"""Compact controls and animated results for the geometry workspace."""

import math
import re
from typing import Dict, Optional

from PyQt6.QtCore import QEasingCurve, QLocale, QPropertyAnimation, Qt, pyqtProperty, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractSpinBox, QButtonGroup, QComboBox, QDoubleSpinBox, QFrame,
    QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy,
    QSpinBox, QVBoxLayout, QWidget,
)

from .shapes import Parameter, ShapeConfig, get_shapes_by_category
from .symbols import parameter_symbol
from .typography import FONTS
from .viewer_2d import ShapeVisualizationWidget
from .viewer_3d import GLVisualizationWidget

__all__ = [
    "GLVisualizationWidget", "PARAMETER_LABELS", "ParameterFormWidget", "ParameterWidget",
    "ResultCard", "ResultsWidget", "SHAPE_NAMES", "ShapeSelectorWidget",
    "ShapeVisualizationWidget",
]

SHAPE_NAMES = {
    "circle": "Circle", "square": "Square", "rectangle": "Rectangle",
    "triangle": "Triangle", "rhombus": "Rhombus", "parallelogram": "Parallelogram",
    "trapezoid": "Trapezoid", "regular_polygon": "Regular polygon", "cube": "Cube",
    "sphere": "Sphere", "cylinder": "Cylinder", "cone": "Cone",
    "cone_trunk": "Cone frustum", "pyramid": "Pyramid",
    "pyramid_trunk": "Pyramid frustum", "tetrahedron": "Tetrahedron",
    "octohedron": "Octahedron", "dodecahedron": "Dodecahedron", "icosahedron": "Icosahedron",
    "rectangular_prism": "Rectangular prism", "quadrangular_prism": "Quadrangular prism",
    "regular_polygon_prism": "Regular polygon prism", "rhomboidal_prism": "Rhombic prism",
    "triangular_prism": "Triangular prism", "trapezoidal_prism": "Trapezoidal prism",
}

PARAMETER_LABELS = {"Side": "Side length", "Base Side 1": "Base width", "Base Side 2": "Base depth"}


class ParameterWidget(QWidget):
    """A labeled full-width input without hard minimum widths."""

    value_changed = pyqtSignal(str, float)

    def __init__(self, parameter: Parameter, parent: Optional[QWidget] = None, shape_name=""):
        super().__init__(parent)
        self.parameter = parameter
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        field_name = PARAMETER_LABELS.get(parameter.label, parameter.label)
        self.label = QLabel(field_name[0].upper() + field_name[1:].lower())
        self.label.setObjectName("ParameterLabel")
        self.label.setWordWrap(True)
        self.label.setStyleSheet(
            f"color: #60718B; font-family: '{FONTS['primary']}'; font-size: 12px; font-weight: 600;"
        )
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.addWidget(self.label)
        header.addStretch()
        self.symbol_label = QLabel(parameter_symbol(shape_name, parameter.name))
        self.symbol_label.setStyleSheet(
            f"color: #2764EF; font-family: '{FONTS['primary']}'; font-size: 11px; "
            "font-weight: 600; background: #EDF3FF; border-radius: 5px; padding: 2px 6px;"
        )
        header.addWidget(self.symbol_label)
        layout.addLayout(header)
        if parameter.name == "sidesnumber":
            self.spinbox = QSpinBox()
            self.spinbox.setRange(int(parameter.min_value), 10000)
            self.spinbox.setSingleStep(max(1, int(parameter.step)))
        else:
            self.spinbox = QDoubleSpinBox()
            self.spinbox.setRange(parameter.min_value, 10000.0)
            self.spinbox.setSingleStep(parameter.step)
            self.spinbox.setDecimals(2)
        self.spinbox.setObjectName("ParameterInput")
        self.spinbox.setLocale(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))
        self.spinbox.setMinimumWidth(0)
        self.spinbox.setMinimumHeight(42)
        self.spinbox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.spinbox.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.spinbox.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self.spinbox.setAccelerated(True)
        self.spinbox.setSuffix(" " + parameter.unit if parameter.unit else "")
        self.spinbox.setToolTip(self.label.text())
        self.spinbox.setAccessibleName(self.label.text())
        self.label.setBuddy(self.spinbox)
        self.set_value(parameter.default if parameter.default is not None else parameter.min_value)
        self.spinbox.valueChanged.connect(
            lambda value: self.value_changed.emit(self.parameter.name, float(value))
        )
        layout.addWidget(self.spinbox)

    def get_value(self) -> float:
        return float(self.spinbox.value())

    def set_value(self, value: float):
        self.spinbox.setValue(int(value) if isinstance(self.spinbox, QSpinBox) else float(value))


class ShapeSelectorWidget(QWidget):
    """Segmented dimension selector and keyboard-accessible shape picker."""

    shape_changed = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setMinimumWidth(0)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        segments = QFrame()
        segments.setObjectName("CategorySegments")
        segments.setStyleSheet(
            "QFrame#CategorySegments { background: #F0F4FC; border: 1px solid #E3EAF6; border-radius: 12px; }"
            "QPushButton { color: #8290A7; background: transparent; border: 1px solid transparent; "
            f"border-radius: 8px; padding: 9px 5px; font-family: '{FONTS['primary']}'; "
            "font-size: 12px; font-weight: 600; }"
            "QPushButton:hover { color: #2764EF; background: #E7EFFD; }"
            "QPushButton:checked { color: #2764EF; background: #FFFFFF; border-color: #D6E3FC; }"
        )
        segment_layout = QHBoxLayout(segments)
        segment_layout.setContentsMargins(4, 4, 4, 4)
        segment_layout.setSpacing(4)
        self.category_buttons = []
        self.category_group = QButtonGroup(self)
        self.category_group.setExclusive(True)
        for index, title in enumerate(("2D shapes", "3D solids")):
            button = QPushButton(title)
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setAccessibleName("Shapes " + ("2D" if index == 0 else "3D"))
            button.setMinimumWidth(0)
            self.category_group.addButton(button, index)
            button.clicked.connect(lambda checked=False, category=index: self.set_category(category))
            self.category_buttons.append(button)
            segment_layout.addWidget(button, 1)
        layout.addWidget(segments)
        self.category_combo = QComboBox(self)
        self.category_combo.addItems(["2D Shapes", "3D Shapes"])
        self.category_combo.hide()
        self.category_combo.currentIndexChanged.connect(self._on_category_changed)
        label = QLabel("Shape")
        label.setObjectName("Eyebrow")
        layout.addWidget(label)
        self.shape_combo = QComboBox()
        self.shape_combo.setObjectName("ShapePicker")
        self.shape_combo.setMinimumWidth(0)
        self.shape_combo.setMinimumHeight(44)
        self.shape_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.shape_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.shape_combo.setMinimumContentsLength(1)
        self.shape_combo.setMaxVisibleItems(12)
        self.shape_combo.setAccessibleName("Select a shape")
        self.shape_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.shape_combo.currentIndexChanged.connect(self._on_shape_changed)
        layout.addWidget(self.shape_combo)
        self._populate_shapes(0, emit=False)

    def set_category(self, index: int):
        index = 1 if index == 1 else 0
        if self.category_combo.currentIndex() == index:
            self.category_buttons[index].setChecked(True)
            return
        self.category_combo.setCurrentIndex(index)

    def _on_category_changed(self, index):
        self._populate_shapes(index)

    def _populate_shapes(self, category, emit=True):
        index = 1 if category in (1, "3D", "3D Shapes") else 0
        self.category_buttons[index].setChecked(True)
        self.shape_combo.blockSignals(True)
        self.shape_combo.clear()
        for shape in get_shapes_by_category("3D" if index else "2D"):
            self.shape_combo.addItem(SHAPE_NAMES.get(shape.name, shape.display_name), shape.name)
        self.shape_combo.blockSignals(False)
        if emit and self.shape_combo.count():
            self.shape_changed.emit(self.get_current_shape_name())

    def _on_shape_changed(self, index):
        if index >= 0:
            self.shape_changed.emit(self.get_current_shape_name())

    def get_current_shape_name(self) -> str:
        return self.shape_combo.currentData() or ""


class ParameterFormWidget(QWidget):
    """Scrollable parameter stack, including the seven-field frustum form."""

    values_changed = pyqtSignal(dict)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.parameter_widgets = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("ParameterScroll")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setMinimumWidth(0)
        self.scroll_area.setMinimumHeight(78)
        self.scroll_area.setStyleSheet("QScrollArea#ParameterScroll { background: transparent; border: none; }")
        self.form_container = QWidget()
        self.form_container.setObjectName("ParameterContainer")
        self.form_layout = QVBoxLayout(self.form_container)
        self.form_layout.setContentsMargins(0, 0, 10, 0)
        self.form_layout.setSpacing(14)
        self.form_layout.addStretch()
        self.scroll_area.setWidget(self.form_container)
        layout.addWidget(self.scroll_area)

    def set_shape(self, shape_config: ShapeConfig):
        # Defaults are populated before connections, so no partial form is emitted.
        self.setUpdatesEnabled(False)
        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
        self.parameter_widgets = []
        for parameter in shape_config.parameters:
            widget = ParameterWidget(parameter, shape_name=shape_config.name)
            widget.value_changed.connect(self._on_value_changed)
            self.parameter_widgets.append(widget)
            self.form_layout.addWidget(widget)
        self.form_layout.addStretch(1)
        self.scroll_area.verticalScrollBar().setValue(0)
        self.setUpdatesEnabled(True)

    def _on_value_changed(self, name="", value=0):
        self.values_changed.emit(self.get_values())

    def get_values(self) -> Dict[str, float]:
        return {widget.parameter.name: widget.get_value() for widget in self.parameter_widgets}


class ResultCard(QFrame):
    """A stable-size result card with interruptible numeric interpolation."""

    def __init__(self, title, icon_color, unit, formula="", is_area=True, parent=None):
        super().__init__(parent)
        self.title, self.icon_color, self.unit = title, icon_color, unit
        self.formula, self.is_area = formula, is_area
        self._value = None
        self._display_value = 0.0
        self._animations_enabled = True
        self.setObjectName("ResultCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMinimumWidth(0)
        self.setMinimumHeight(122)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setStyleSheet(
            "QFrame#ResultCard { background: #FFFFFF; border: 1px solid #E0E8F4; "
            "border-radius: 16px; border-top: 2px solid " + icon_color + "; }"
            "QFrame#ResultCard:hover { border-color: " + icon_color + "; }"
            "QLabel { background: transparent; border: none; }"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(5)
        header = QHBoxLayout()
        header.setSpacing(8)
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(
            f"color: #60718B; font-family: '{FONTS['primary']}'; font-size: 12px; font-weight: 600;"
        )
        header.addWidget(self.title_label)
        header.addStretch(1)
        self.unit_label = QLabel(unit)
        self.unit_label.setStyleSheet(
            f"color: {icon_color}; font-family: '{FONTS['primary']}'; font-size: 11px; "
            "background: #F3F7FE; border-radius: 5px; padding: 3px 7px;"
        )
        header.addWidget(self.unit_label)
        layout.addLayout(header)
        self.value_label = QLabel("—")
        self.value_label.setObjectName("ResultValue")
        self.value_label.setMinimumWidth(0)
        self.value_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.value_label.setStyleSheet(
            f"color: #182944; font-family: '{FONTS['display']}'; font-size: 34px; font-weight: 600;"
        )
        layout.addWidget(self.value_label)
        self.formula_label = QLabel(formula)
        self.formula_label.setStyleSheet(
            f"color: #8B99AE; font-family: '{FONTS['primary']}'; font-size: 10px;"
        )
        self.formula_label.setWordWrap(True)
        self.formula_label.setMinimumWidth(0)
        self.formula_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.formula_label)
        self._animation = QPropertyAnimation(self, b"display_value", self)
        self._animation.setDuration(420)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._animation.finished.connect(self._finish_animation)

    @staticmethod
    def _parse_value(value):
        if value is None:
            return None
        try:
            if isinstance(value, str):
                match = re.match(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", value.strip())
                if match is None:
                    return None
                value = match.group()
            number = float(value)
            return number if math.isfinite(number) else None
        except (TypeError, ValueError, OverflowError):
            return None

    @staticmethod
    def _format_value(value):
        if value != 0 and (abs(value) < 0.01 or abs(value) >= 1_000_000):
            return f"{value:.6g}"
        return f"{value:,.2f}"

    @pyqtProperty(float)
    def display_value(self):
        return self._display_value

    @display_value.setter
    def display_value(self, value):
        self._display_value = value
        text = self._format_value(value)
        self.value_label.setText(text)
        self.value_label.setStyleSheet(
            f"color: #182944; font-family: '{FONTS['display']}'; font-size: "
            + ("34" if len(text) <= 11 else "28") + "px; font-weight: 600;"
        )

    def _finish_animation(self):
        if self._value is not None:
            self.display_value = self._value

    def set_value(self, value):
        self._animation.stop()
        self._value = self._parse_value(value)
        if self._value is None:
            self.value_label.setText("—")
            self.value_label.setToolTip("Calculate to see the result from marksgeometrys")
            self._display_value = 0.0
            return
        self.value_label.setToolTip(f"{self._value:.12g} {self.unit}")
        if not self.isVisible() or not self._animations_enabled:
            self.display_value = self._value
            return
        self._animation.setStartValue(self._display_value)
        self._animation.setEndValue(self._value)
        self._animation.start()

    def set_formula(self, formula):
        self.formula = formula
        self.formula_label.setText(formula)
        self.formula_label.setToolTip(formula)

    def set_animations_enabled(self, enabled):
        self._animations_enabled = bool(enabled)
        if not enabled:
            self._animation.stop()
            self._finish_animation()


class ResultsWidget(QWidget):
    """Aligned area and volume cards with explicit empty states."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.current_shape_name = ""
        self._is_3d = False
        self.setMinimumWidth(0)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        self.area_card = ResultCard("Area", "#2764EF", "cm²")
        self.volume_card = ResultCard("Volume", "#04AFC2", "cm³", is_area=False)
        layout.addWidget(self.area_card, 1)
        layout.addWidget(self.volume_card, 1)
        self.set_results(None, None)

    def set_results(self, area, volume, is_3d=False, shape_name=""):
        self.current_shape_name = shape_name
        self._is_3d = is_3d
        self.area_card.set_formula("marksgeometrys · area()")
        volume_method = "volum()" if shape_name == "sphere" else "volume()"
        self.volume_card.set_formula(
            "marksgeometrys · " + volume_method if is_3d else "Not defined for a plane figure"
        )
        self.area_card.set_value(area)
        self.volume_card.set_value(volume if is_3d else None)
        self.volume_card.title_label.setStyleSheet(
            "color: " + ("#60718B" if is_3d else "#A5B0C0")
            + f"; font-family: '{FONTS['primary']}'; font-size: 12px; font-weight: 600;"
        )

    def clear(self, is_3d=None, shape_name=None):
        self.set_results(
            None, None, self._is_3d if is_3d is None else is_3d,
            self.current_shape_name if shape_name is None else shape_name,
        )

    def mark_stale(self):
        self.clear()

    def set_animations_enabled(self, enabled):
        self.area_card.set_animations_enabled(enabled)
        self.volume_card.set_animations_enabled(enabled)
