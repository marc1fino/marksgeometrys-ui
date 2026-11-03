"""Custom widgets for the MarksGeometry UI."""

import math
from typing import Dict, List, Optional, Callable, Tuple
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QDoubleSpinBox, QSpinBox, QComboBox, QPushButton, QGroupBox,
    QScrollArea, QFrame, QSizePolicy, QMessageBox, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRectF, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import (
    QFont, QPixmap, QPainter, QColor, QPen, QBrush,
    QLinearGradient, QRadialGradient, QConicalGradient,
    QPainterPath, QPolygonF, QFontMetrics, QTransform
)

from .shapes import ShapeConfig, Parameter, get_shape_config
from .theme import COLORS, FONTS, RADIUS, SHADOWS, SPACING


class ParameterWidget(QWidget):
    """Widget for a single parameter input."""

    value_changed = pyqtSignal(str, float)

    def __init__(self, parameter: Parameter, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.parameter = parameter
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(12)

        # Label with tooltip
        label = QLabel(self.parameter.label)
        label.setToolTip(self.parameter.tooltip)
        label.setMinimumWidth(150)
        label.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 12px;
            font-weight: 500;
            padding-right: 8px;
        """)
        layout.addWidget(label)

        # Spin box based on parameter type
        if isinstance(self.parameter.default, int) or self.parameter.step >= 1:
            self.spinbox = QSpinBox()
            self.spinbox.setMinimum(int(self.parameter.min_value))
            self.spinbox.setMaximum(10000)
            self.spinbox.setSingleStep(int(self.parameter.step))
            if self.parameter.default is not None:
                self.spinbox.setValue(int(self.parameter.default))
        else:
            self.spinbox = QDoubleSpinBox()
            self.spinbox.setMinimum(self.parameter.min_value)
            self.spinbox.setMaximum(10000.0)
            self.spinbox.setSingleStep(self.parameter.step)
            self.spinbox.setDecimals(2)
            if self.parameter.default is not None:
                self.spinbox.setValue(self.parameter.default)

        self.spinbox.setSuffix(f" {self.parameter.unit}")
        self.spinbox.setToolTip(self.parameter.tooltip)
        self.spinbox.setStyleSheet(f"""
            QSpinBox, QDoubleSpinBox {{
                font-family: {FONTS['mono']};
                font-size: 14px;
                font-weight: 500;
                color: {COLORS['text_primary']};
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: {RADIUS['md']};
                padding: 10px 12px;
                min-height: 22px;
                min-width: 100px;
                selection-background-color: {COLORS['primary']};
                selection-color: {COLORS['text_on_primary']};
            }}
            QSpinBox:hover, QDoubleSpinBox:hover {{
                border-color: {COLORS['border_accent']};
                background-color: {COLORS['bg_glass']};
            }}
            QSpinBox:focus, QDoubleSpinBox:focus {{
                border: 2px solid {COLORS['primary']};
                background-color: {COLORS['bg_glass_strong']};
            }}
            QSpinBox::up-button, QDoubleSpinBox::up-button {{
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 28px;
                border: none;
                border-top-right-radius: {RADIUS['md']};
                background: transparent;
            }}
            QSpinBox::down-button, QDoubleSpinBox::down-button {{
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 28px;
                border: none;
                border-bottom-right-radius: {RADIUS['md']};
                background: transparent;
            }}
            QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 5px solid {COLORS['text_secondary']};
            }}
            QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {COLORS['text_secondary']};
            }}
            QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
            QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
                background: rgba(0, 212, 255, 0.15);
            }}
        """)
        self.spinbox.valueChanged.connect(
            lambda v: self.value_changed.emit(self.parameter.name, float(v))
        )
        layout.addWidget(self.spinbox, 1)

    def get_value(self) -> float:
        """Get the current parameter value."""
        return float(self.spinbox.value())

    def set_value(self, value: float):
        """Set the parameter value."""
        self.spinbox.setValue(value)


class ShapeSelectorWidget(QWidget):
    """Widget for selecting a shape category and specific shape."""

    shape_changed = pyqtSignal(str)  # Emits shape name

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Category selector
        cat_layout = QHBoxLayout()
        cat_layout.setSpacing(10)

        cat_label = QLabel("Category")
        cat_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;")
        cat_layout.addWidget(cat_label)

        self.category_combo = QComboBox()
        self.category_combo.addItems(["2D Shapes", "3D Shapes"])
        self.category_combo.currentTextChanged.connect(self._on_category_changed)
        self.category_combo.setStyleSheet(f"""
            QComboBox {{
                font-family: {FONTS['primary']};
                font-size: 13px;
                color: {COLORS['text_primary']};
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: {RADIUS['md']};
                padding: 10px 16px;
                min-height: 22px;
                min-width: 180px;
            }}
            QComboBox:hover {{
                border-color: {COLORS['border_accent']};
                background-color: {COLORS['bg_glass']};
            }}
            QComboBox:focus {{
                border: 2px solid {COLORS['primary']};
                background-color: {COLORS['bg_glass_strong']};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 32px;
                border: none;
                border-top-right-radius: {RADIUS['md']};
                border-bottom-right-radius: {RADIUS['md']};
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {COLORS['text_secondary']};
                margin-right: 10px;
            }}
            QComboBox:hover::down-arrow {{
                border-top-color: {COLORS['primary']};
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border_accent']};
                border-radius: {RADIUS['md']};
                selection-background-color: {COLORS['primary']};
                selection-color: {COLORS['text_on_primary']};
                outline: none;
                padding: 4px;
            }}
        """)
        cat_layout.addWidget(self.category_combo)
        cat_layout.addStretch()
        layout.addLayout(cat_layout)

        # Shape selector
        shape_layout = QHBoxLayout()
        shape_layout.setSpacing(10)

        shape_label = QLabel("Shape")
        shape_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;")
        shape_layout.addWidget(shape_label)

        self.shape_combo = QComboBox()
        self.shape_combo.currentTextChanged.connect(self._on_shape_changed)
        self.shape_combo.setStyleSheet(f"""
            QComboBox {{
                font-family: {FONTS['primary']};
                font-size: 13px;
                color: {COLORS['text_primary']};
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: {RADIUS['md']};
                padding: 10px 16px;
                min-height: 22px;
                min-width: 180px;
            }}
            QComboBox:hover {{
                border-color: {COLORS['border_accent']};
                background-color: {COLORS['bg_glass']};
            }}
            QComboBox:focus {{
                border: 2px solid {COLORS['primary']};
                background-color: {COLORS['bg_glass_strong']};
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 32px;
                border: none;
                border-top-right-radius: {RADIUS['md']};
                border-bottom-right-radius: {RADIUS['md']};
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {COLORS['text_secondary']};
                margin-right: 10px;
            }}
            QComboBox:hover::down-arrow {{
                border-top-color: {COLORS['primary']};
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border_accent']};
                border-radius: {RADIUS['md']};
                selection-background-color: {COLORS['primary']};
                selection-color: {COLORS['text_on_primary']};
                outline: none;
                padding: 4px;
            }}
        """)
        shape_layout.addWidget(self.shape_combo)
        shape_layout.addStretch()
        layout.addLayout(shape_layout)

        # Populate initial shapes
        self._populate_shapes("2D Shapes")

    def _populate_shapes(self, category_text: str):
        """Populate shape combo based on category."""
        self.shape_combo.blockSignals(True)
        self.shape_combo.clear()

        category = "2D" if "2D" in category_text else "3D"
        from .shapes import get_shapes_by_category
        shapes = get_shapes_by_category(category)

        for shape in shapes:
            self.shape_combo.addItem(shape.display_name, shape.name)

        self.shape_combo.blockSignals(False)

        # Emit signal for first shape
        if shapes:
            self.shape_changed.emit(shapes[0].name)

    def _on_category_changed(self, text: str):
        self._populate_shapes(text)

    def _on_shape_changed(self, text: str):
        shape_name = self.shape_combo.currentData()
        if shape_name:
            self.shape_changed.emit(shape_name)

    def get_current_shape_name(self) -> str:
        """Get the currently selected shape name."""
        return self.shape_combo.currentData() or ""


class ParameterFormWidget(QWidget):
    """Dynamic form for shape parameters."""

    values_changed = pyqtSignal(dict)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.parameter_widgets: List[ParameterWidget] = []
        self._setup_ui()

    def _setup_ui(self):
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: {COLORS['bg_secondary']};
                width: 8px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLORS['primary']}, stop:1 {COLORS['secondary']});
                border-radius: 4px;
                min-height: 30px;
                margin: 2px;
            }}
        """)

        self.form_container = QWidget()
        self.form_layout = QFormLayout(self.form_container)
        self.form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.form_layout.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        self.form_layout.setHorizontalSpacing(12)
        self.form_layout.setVerticalSpacing(10)

        self.scroll.setWidget(self.form_container)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.scroll)

    def set_shape(self, shape_config: ShapeConfig):
        """Update form for a new shape."""
        # Clear existing widgets
        for widget in self.parameter_widgets:
            widget.value_changed.disconnect()
            widget.setParent(None)
            widget.deleteLater()
        self.parameter_widgets.clear()

        # Clear layout
        while self.form_layout.rowCount() > 0:
            self.form_layout.removeRow(0)

        # Add new parameter widgets
        for param in shape_config.parameters:
            widget = ParameterWidget(param)
            widget.value_changed.connect(self._on_value_changed)
            self.parameter_widgets.append(widget)
            self.form_layout.addRow(widget)

        # Emit initial values
        self._on_value_changed()

    def _on_value_changed(self, name: str = "", value: float = 0):
        """Emit all current values."""
        values = {}
        for widget in self.parameter_widgets:
            values[widget.parameter.name] = widget.get_value()
        self.values_changed.emit(values)

    def get_values(self) -> Dict[str, float]:
        """Get all current parameter values."""
        return {w.parameter.name: w.get_value() for w in self.parameter_widgets}


class ShapeVisualizationWidget(QWidget):
    """Widget for displaying a visualization of the selected shape with dimension labels."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.current_shape: Optional[ShapeConfig] = None
        self.current_values: Dict[str, float] = {}
        self.setMinimumSize(400, 400)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet(f"""
            QWidget {{
                background: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: {RADIUS['lg']};
            }}
        """)

    def set_shape(self, shape_config: ShapeConfig, values: Dict[str, float]):
        """Update the visualization for a new shape."""
        self.current_shape = shape_config
        self.current_values = values
        self.update()

    def paintEvent(self, event):
        """Paint a representation of the shape with dimension labels."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background with subtle gradient
        rect = self.rect()
        gradient = QLinearGradient(0, 0, 0, rect.height())
        gradient.setColorAt(0, QColor(COLORS['bg_secondary']))
        gradient.setColorAt(1, QColor(COLORS['bg_tertiary']))
        painter.fillRect(rect, gradient)

        # Subtle grid pattern
        self._draw_grid(painter, rect)

        if not self.current_shape:
            self._draw_placeholder(painter, rect)
            return

        # Draw shape name
        font = QFont(FONTS["display"])
        font.setPointSize(16)
        font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(font)
        painter.setPen(QColor(COLORS['text_primary']))
        painter.drawText(20, 35, self.current_shape.display_name)

        # Draw category badge
        cat_font = QFont(FONTS["primary"])
        cat_font.setPointSize(9)
        cat_font.setWeight(QFont.Weight.Medium)
        painter.setFont(cat_font)
        cat_color = COLORS['primary'] if self.current_shape.category == "2D" else COLORS['secondary']
        painter.setPen(QColor(cat_color))
        painter.drawText(20, 55, f"{self.current_shape.category} Shape")

        # Draw parameters panel on the right
        self._draw_parameters_panel(painter, rect)

        # Draw the shape representation
        self._draw_shape_representation(painter, rect)

    def _draw_grid(self, painter: QPainter, rect: QRectF):
        """Draw a subtle grid pattern."""
        painter.setPen(QPen(QColor(COLORS['border_subtle']), 1, Qt.PenStyle.DotLine))
        grid_size = 30
        for x in range(0, rect.width(), grid_size):
            painter.drawLine(x, 0, x, rect.height())
        for y in range(0, rect.height(), grid_size):
            painter.drawLine(0, y, rect.width(), y)

    def _draw_placeholder(self, painter: QPainter, rect: QRectF):
        """Draw placeholder when no shape is selected."""
        font = QFont(FONTS["primary"])
        font.setPointSize(14)
        painter.setFont(font)
        painter.setPen(QColor(COLORS['text_muted']))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "Select a shape to visualize")

    def _draw_parameters_panel(self, painter: QPainter, rect: QRectF):
        """Draw the parameters panel on the right side."""
        if not self.current_shape:
            return

        panel_x = rect.width() - 220
        panel_y = 80
        panel_width = 200
        line_height = 26

        # Panel background
        painter.setBrush(QBrush(QColor(COLORS['bg_glass_strong'])))
        painter.setPen(QPen(QColor(COLORS['border_subtle']), 1))
        painter.drawRoundedRect(panel_x - 10, panel_y - 10, panel_width, len(self.current_shape.parameters) * line_height + 20, RADIUS['md'], RADIUS['md'])

        # Title
        font = QFont(FONTS["display"])
        font.setPointSize(10)
        font.setWeight(QFont.Weight.Medium)
        painter.setFont(font)
        painter.setPen(QColor(COLORS['primary']))
        painter.drawText(panel_x, panel_y + 5, "Dimensions")

        # Parameters
        font = QFont(FONTS["mono"])
        font.setPointSize(11)
        painter.setFont(font)
        y = panel_y + 30

        for param in self.current_shape.parameters:
            value = self.current_values.get(param.name, param.default or 0)
            # Parameter name
            painter.setPen(QColor(COLORS['text_secondary']))
            painter.drawText(panel_x, y, param.label)
            # Value
            painter.setPen(QColor(COLORS['text_primary']))
            value_text = f"{value:.2f} {param.unit}" if param.unit else f"{value:.2f}"
            # Right align value
            metrics = QFontMetrics(font)
            value_width = metrics.horizontalAdvance(value_text)
            painter.drawText(panel_x + panel_width - value_width, y, value_text)
            y += line_height

    def _draw_shape_representation(self, painter: QPainter, rect: QRectF):
        """Draw a 2D/3D representation of the shape with dimension lines."""
        if not self.current_shape:
            return

        w = rect.width() - 250  # Leave space for parameters panel
        h = rect.height() - 100
        center_x = w // 2
        center_y = h // 2 + 50
        size = min(w, h) // 3

        # Set up drawing style
        primary_color = QColor(COLORS['primary'])
        secondary_color = QColor(COLORS['secondary'])
        accent_pen = QPen(primary_color, 2.5)
        dim_pen = QPen(QColor(COLORS['text_secondary']), 1, Qt.PenStyle.DashLine)
        dim_font = QFont(FONTS["mono"])
        dim_font.setPointSize(9)

        painter.setPen(accent_pen)
        painter.setBrush(QBrush(QColor(COLORS['primary'] + "33")))  # 20% opacity

        shape_name = self.current_shape.name

        # 2D Shapes
        if shape_name == "circle":
            r = size
            cx, cy = center_x, center_y
            painter.drawEllipse(cx - r, cy - r, 2 * r, 2 * r)
            # Draw radius line
            painter.setPen(dim_pen)
            painter.drawLine(cx, cy, cx + r, cy)
            # Radius label
            painter.setFont(dim_font)
            painter.setPen(QColor(COLORS['primary']))
            radius_val = self.current_values.get("radius", 0)
            painter.drawText(cx + r//2 - 15, cy - 10, f"r = {radius_val:.1f}")

        elif shape_name == "square":
            s = size * 1.5
            cx, cy = center_x, center_y
            painter.drawRect(cx - s//2, cy - s//2, s, s)
            # Side dimension
            painter.setPen(dim_pen)
            painter.drawLine(cx - s//2, cy + s//2 + 10, cx + s//2, cy + s//2 + 10)
            painter.drawLine(cx - s//2, cy + s//2 + 5, cx - s//2, cy + s//2 + 15)
            painter.drawLine(cx + s//2, cy + s//2 + 5, cx + s//2, cy + s//2 + 15)
            painter.setFont(dim_font)
            painter.setPen(QColor(COLORS['primary']))
            side_val = self.current_values.get("side", 0)
            painter.drawText(cx - 20, cy + s//2 + 30, f"side = {side_val:.1f}")

        elif shape_name == "rectangle":
            bw = size * 2
            bh = size
            cx, cy = center_x, center_y
            painter.drawRect(cx - bw//2, cy - bh//2, bw, bh)
            # Base dimension
            painter.setPen(dim_pen)
            painter.drawLine(cx - bw//2, cy + bh//2 + 10, cx + bw//2, cy + bh//2 + 10)
            painter.setFont(dim_font)
            painter.setPen(QColor(COLORS['primary']))
            base_val = self.current_values.get("base", 0)
            painter.drawText(cx - 25, cy + bh//2 + 30, f"base = {base_val:.1f}")
            # Height dimension
            painter.setPen(dim_pen)
            painter.drawLine(cx + bw//2 + 10, cy - bh//2, cx + bw//2 + 10, cy + bh//2)
            painter.setFont(dim_font)
            painter.setPen(QColor(COLORS['primary']))
            height_val = self.current_values.get("height", 0)
            painter.drawText(cx + bw//2 + 15, cy + 5, f"h = {height_val:.1f}")

        elif shape_name == "triangle":
            cx, cy = center_x, center_y
            base_val = self.current_values.get("base", 1)
            height_val = self.current_values.get("height", 1)
            scale = min(size * 2 / max(base_val, 1), size * 2 / max(height_val, 1))
            bw = base_val * scale
            bh = height_val * scale
            points = [
                (cx, cy - bh//2),
                (cx - bw//2, cy + bh//2),
                (cx + bw//2, cy + bh//2),
            ]
            painter.drawPolygon(*[QPointF(x, y) for x, y in points])
            # Base
            painter.setPen(dim_pen)
            painter.drawLine(cx - bw//2, cy + bh//2 + 10, cx + bw//2, cy + bh//2 + 10)
            painter.setFont(dim_font)
            painter.setPen(QColor(COLORS['primary']))
            painter.drawText(cx - 20, cy + bh//2 + 30, f"base = {base_val:.1f}")
            # Height
            painter.setPen(dim_pen)
            painter.drawLine(cx + 10, cy - bh//2, cx + 10, cy + bh//2)
            painter.setFont(dim_font)
            painter.setPen(QColor(COLORS['primary']))
            painter.drawText(cx + 15, cy, f"h = {height_val:.1f}")

        elif shape_name == "rhombus":
            cx, cy = center_x, center_y
            d1 = self.current_values.get("largediagonal", 1)
            d2 = self.current_values.get("smalldiagonal", 1)
            scale = min(size * 2 / max(d1, 1), size * 2 / max(d2, 1))
            r1 = d1 * scale / 2
            r2 = d2 * scale / 2
            points = [
                (cx, cy - r1),
                (cx + r2, cy),
                (cx, cy + r1),
                (cx - r2, cy),
            ]
            painter.drawPolygon(*[QPointF(x, y) for x, y in points])
            # Large diagonal
            painter.setPen(dim_pen)
            painter.drawLine(cx, cy - r1, cx, cy + r1)
            painter.setFont(dim_font)
            painter.setPen(QColor(COLORS['primary']))
            painter.drawText(cx + 5, cy, f"d₁ = {d1:.1f}")
            # Small diagonal
            painter.setPen(dim_pen)
            painter.drawLine(cx - r2, cy, cx + r2, cy)
            painter.setFont(dim_font)
            painter.setPen(QColor(COLORS['primary']))
            painter.drawText(cx - 30, cy - 10, f"d₂ = {d2:.1f}")

        elif shape_name == "parallelogram":
            cx, cy = center_x, center_y
            base_val = self.current_values.get("base", 1)
            height_val = self.current_values.get("height", 1)
            scale = min(size * 2 / max(base_val, 1), size * 2 / max(height_val, 1))
            bw = base_val * scale
            bh = height_val * scale
            offset = bw * 0.3
            points = [
                (cx - bw//2 + offset, cy - bh//2),
                (cx + bw//2 + offset, cy - bh//2),
                (cx + bw//2 - offset, cy + bh//2),
                (cx - bw//2 - offset, cy + bh//2),
            ]
            painter.drawPolygon(*[QPointF(x, y) for x, y in points])
            # Base
            painter.setPen(dim_pen)
            painter.drawLine(cx - bw//2 - offset, cy + bh//2 + 10, cx + bw//2 - offset, cy + bh//2 + 10)
            painter.setFont(dim_font)
            painter.setPen(QColor(COLORS['primary']))
            painter.drawText(cx - 20, cy + bh//2 + 30, f"base = {base_val:.1f}")
            # Height
            painter.setPen(dim_pen)
            painter.drawLine(cx + bw//2 - offset + 10, cy - bh//2, cx + bw//2 - offset + 10, cy + bh//2)
            painter.setFont(dim_font)
            painter.setPen(QColor(COLORS['primary']))
            painter.drawText(cx + bw//2 - offset + 15, cy, f"h = {height_val:.1f}")

        elif shape_name == "trapezoid":
            cx, cy = center_x, center_y
            b1 = self.current_values.get("largebase", 1)
            b2 = self.current_values.get("smallbase", 1)
            h = self.current_values.get("height", 1)
            scale = min(size * 2 / max(b1, 1), size * 2 / max(h, 1))
            bw1 = b1 * scale
            bw2 = b2 * scale
            bh = h * scale
            points = [
                (cx - bw2//2, cy - bh//2),
                (cx + bw2//2, cy - bh//2),
                (cx + bw1//2, cy + bh//2),
                (cx - bw1//2, cy + bh//2),
            ]
            painter.drawPolygon(*[QPointF(x, y) for x, y in points])
            # Large base
            painter.setPen(dim_pen)
            painter.drawLine(cx - bw1//2, cy + bh//2 + 10, cx + bw1//2, cy + bh//2 + 10)
            painter.setFont(dim_font)
            painter.setPen(QColor(COLORS['primary']))
            painter.drawText(cx - 30, cy + bh//2 + 30, f"base₁ = {b1:.1f}")
            # Small base
            painter.setPen(dim_pen)
            painter.drawLine(cx - bw2//2, cy - bh//2 - 10, cx + bw2//2, cy - bh//2 - 10)
            painter.setFont(dim_font)
            painter.setPen(QColor(COLORS['primary']))
            painter.drawText(cx - 30, cy - bh//2 - 15, f"base₂ = {b2:.1f}")
            # Height
            painter.setPen(dim_pen)
            painter.drawLine(cx + bw1//2 + 10, cy - bh//2, cx + bw1//2 + 10, cy + bh//2)
            painter.setFont(dim_font)
            painter.setPen(QColor(COLORS['primary']))
            painter.drawText(cx + bw1//2 + 15, cy, f"h = {h:.1f}")

        elif shape_name == "regular_polygon":
            cx, cy = center_x, center_y
            side_val = self.current_values.get("side", 1)
            sides = int(self.current_values.get("sidesnumber", 6))
            apothem_val = self.current_values.get("apothem", 1)
            # Calculate radius from side and sides
            import math
            radius = side_val / (2 * math.sin(math.pi / sides))
            scale = size / radius
            r = radius * scale
            points = []
            for i in range(sides):
                angle = 2 * math.pi * i / sides - math.pi / 2
                x = cx + r * math.cos(angle)
                y = cy + r * math.sin(angle)
                points.append((x, y))
            painter.drawPolygon(*[QPointF(x, y) for x, y in points])
            # Apothem line
            painter.setPen(dim_pen)
            painter.drawLine(cx, cy, cx, cy - r)
            painter.setFont(dim_font)
            painter.setPen(QColor(COLORS['primary']))
            painter.drawText(cx + 5, cy - r//2, f"a = {apothem_val:.1f}")
            # Side indicator
            if points:
                x1, y1 = points[0]
                x2, y2 = points[1]
                mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                painter.setPen(dim_pen)
                painter.drawLine(mx - 10, my - 10, mx + 10, my + 10)
                painter.setFont(dim_font)
                painter.setPen(QColor(COLORS['primary']))
                painter.drawText(mx + 15, my, f"s = {side_val:.1f}")

        # 3D Shapes - draw isometric representations with dimensions
        elif shape_name == "cube":
            cx, cy = center_x, center_y
            s = size
            side_val = self.current_values.get("side", 1)
            offset = s // 3
            # Front face
            painter.drawRect(cx - s, cy - s, 2*s, 2*s)
            # Top face
            points = [
                (cx - s, cy - s),
                (cx - s + offset, cy - s - offset),
                (cx + s + offset, cy - s - offset),
                (cx + s, cy - s),
            ]
            painter.drawPolygon(*[QPointF(x, y) for x, y in points])
            # Side face
            points = [
                (cx + s, cy - s),
                (cx + s + offset, cy - s - offset),
                (cx + s + offset, cy + s - offset),
                (cx + s, cy + s),
            ]
            painter.drawPolygon(*[QPointF(x, y) for x, y in points])
            # Side dimension
            painter.setPen(dim_pen)
            painter.drawLine(cx + s + 15, cy - s, cx + s + 15, cy + s)
            painter.setFont(dim_font)
            painter.setPen(QColor(COLORS['primary']))
            painter.drawText(cx + s + 20, cy, f"side = {side_val:.1f}")

        elif shape_name == "sphere":
            cx, cy = center_x, center_y
            r = size
            radius_val = self.current_values.get("radius", 1)
            # Draw sphere as circle with shading
            gradient = QRadialGradient(cx - r//3, cy - r//3, r)
            gradient.setColorAt(0, QColor(COLORS['primary'] + "80"))
            gradient.setColorAt(0.5, QColor(COLORS['primary'] + "40"))
            gradient.setColorAt(1, QColor(COLORS['primary'] + "10"))
            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(primary_color, 2))
            painter.drawEllipse(cx - r, cy - r, 2*r, 2*r)
            # Radius line
            painter.setPen(dim_pen)
            painter.drawLine(cx, cy, cx + r, cy)
            painter.setFont(dim_font)
            painter.setPen(QColor(COLORS['primary']))
            painter.drawText(cx + r//2 - 15, cy - 10, f"r = {radius_val:.1f}")
            # Wireframe lines for 3D effect
            painter.setPen(QPen(QColor(COLORS['primary'] + "60"), 1))
            for i in range(-r, r, r//3):
                y_offset = int((r**2 - i**2)**0.5) if abs(i) < r else 0
                painter.drawLine(cx - y_offset, cy + i, cx + y_offset, cy + i)

        elif shape_name == "cylinder":
            cx, cy = center_x, center_y
            r = size
            h = size * 2
            radius_val = self.current_values.get("radius", 1)
            height_val = self.current_values.get("height", 1)
            # Top ellipse
            painter.drawEllipse(cx - r, cy - h//2, 2*r, r//2)
            # Bottom ellipse
            painter.drawEllipse(cx - r, cy + h//2, 2*r, r//2)
            # Sides
            painter.drawLine(cx - r, cy - h//2, cx - r, cy + h//2)
            painter.drawLine(cx + r, cy - h//2, cx + r, cy + h//2)
            # Radius
            painter.setPen(dim_pen)
            painter.drawLine(cx, cy + h//2, cx + r, cy + h//2)
            painter.setFont(dim_font)
            painter.setPen(QColor(COLORS['primary']))
            painter.drawText(cx + r//2 - 10, cy + h//2 + 20, f"r = {radius_val:.1f}")
            # Height
            painter.setPen(dim_pen)
            painter.drawLine(cx + r + 10, cy - h//2, cx + r + 10, cy + h//2)
            painter.setFont(dim_font)
            painter.setPen(QColor(COLORS['primary']))
            painter.drawText(cx + r + 15, cy, f"h = {height_val:.1f}")

        elif shape_name == "cone":
            cx, cy = center_x, center_y
            r = size
            h = size * 2
            radius_val = self.current_values.get("radius", 1)
            slant_val = self.current_values.get("geometry", 1)
            # Base ellipse
            painter.drawEllipse(cx - r, cy + h//2, 2*r, r//2)
            # Sides to apex
            painter.drawLine(cx - r, cy + h//2, cx, cy - h//2)
            painter.drawLine(cx + r, cy + h//2, cx, cy - h//2)
            # Radius
            painter.setPen(dim_pen)
            painter.drawLine(cx, cy + h//2, cx + r, cy + h//2)
            painter.setFont(dim_font)
            painter.setPen(QColor(COLORS['primary']))
            painter.drawText(cx + r//2 - 10, cy + h//2 + 20, f"r = {radius_val:.1f}")
            # Height
            painter.setPen(dim_pen)
            painter.drawLine(cx + 10, cy - h//2, cx + 10, cy + h//2)
            painter.setFont(dim_font)
            painter.setPen(QColor(COLORS['primary']))
            painter.drawText(cx + 15, cy, f"h = {height_val:.1f}" if (height_val := self.current_values.get("height")) else f"l = {slant_val:.1f}")

        elif shape_name == "cone_trunk":
            cx, cy = center_x, center_y
            r1 = self.current_values.get("sbradius", 1)
            r2 = self.current_values.get("lbradius", 1)
            h = self.current_values.get("height", 1)
            slant = self.current_values.get("geometry", 1)
            scale = min(size * 2 / max(r2 * 2, 1), size * 2 / max(h, 1))
            sr1 = r1 * scale
            sr2 = r2 * scale
            sh = h * scale
            # Top ellipse
            painter.drawEllipse(cx - sr1, cy - sh//2, 2*sr1, sr1//2)
            # Bottom ellipse
            painter.drawEllipse(cx - sr2, cy + sh//2, 2*sr2, sr2//2)
            # Sides
            painter.drawLine(cx - sr1, cy - sh//2, cx - sr2, cy + sh//2)
            painter.drawLine(cx + sr1, cy - sh//2, cx + sr2, cy + sh//2)
            # Radii
            painter.setPen(dim_pen)
            painter.drawLine(cx, cy - sh//2, cx + sr1, cy - sh//2)
            painter.setFont(dim_font)
            painter.setPen(QColor(COLORS['primary']))
            painter.drawText(cx + sr1//2 - 15, cy - sh//2 - 10, f"r₁ = {r1:.1f}")
            painter.setPen(dim_pen)
            painter.drawLine(cx, cy + sh//2, cx + sr2, cy + sh//2)
            painter.setFont(dim_font)
            painter.setPen(QColor(COLORS['primary']))
            painter.drawText(cx + sr2//2 - 15, cy + sh//2 + 20, f"r₂ = {r2:.1f}")
            # Height
            painter.setPen(dim_pen)
            painter.drawLine(cx + sr2 + 10, cy - sh//2, cx + sr2 + 10, cy + sh//2)
            painter.setFont(dim_font)
            painter.setPen(QColor(COLORS['primary']))
            painter.drawText(cx + sr2 + 15, cy, f"h = {h:.1f}")

        elif shape_name in ("pyramid", "tetrahedron"):
            cx, cy = center_x, center_y
            base_val = self.current_values.get("base", 1)
            height_val = self.current_values.get("height", 1)
            slant_val = self.current_values.get("side", 1)  # slant height
            scale = min(size * 2 / max(base_val, 1), size * 2 / max(height_val, 1))
            bw = base_val * scale
            bh = height_val * scale
            points = [
                (cx - bw//2, cy + bh//2),
                (cx + bw//2, cy + bh//2),
                (cx, cy - bh//2),
            ]
            painter.drawPolygon(*[QPointF(x, y) for x, y in points])
            # Base
            painter.setPen(dim_pen)
            painter.drawLine(cx - bw//2, cy + bh//2 + 10, cx + bw//2, cy + bh//2 + 10)
            painter.setFont(dim_font)
            painter.setPen(QColor(COLORS['primary']))
            painter.drawText(cx - 20, cy + bh//2 + 30, f"base = {base_val:.1f}")
            # Height
            painter.setPen(dim_pen)
            painter.drawLine(cx + 10, cy - bh//2, cx + 10, cy + bh//2)
            painter.setFont(dim_font)
            painter.setPen(QColor(COLORS['primary']))
            painter.drawText(cx + 15, cy, f"h = {height_val:.1f}")

        elif shape_name == "octohedron":
            cx, cy = center_x, center_y
            s = size
            side_val = self.current_values.get("side", 1)
            points = [
                (cx, cy - s),
                (cx - s, cy),
                (cx, cy + s),
                (cx + s, cy),
            ]
            painter.drawPolygon(*[QPointF(x, y) for x, y in points])
            # Side dimension
            painter.setPen(dim_pen)
            painter.drawLine(cx - s, cy, cx, cy - s)
            painter.setFont(dim_font)
            painter.setPen(QColor(COLORS['primary']))
            painter.drawText(cx - s//2 - 10, cy - s//2 - 10, f"side = {side_val:.1f}")

        elif shape_name in ("dodecahedron", "icosahedron"):
            cx, cy = center_x, center_y
            side_val = self.current_values.get("side", 1)
            r = size
            painter.drawEllipse(cx - r, cy - r, 2*r, 2*r)
            painter.setFont(dim_font)
            painter.setPen(QColor(COLORS['primary']))
            painter.drawText(cx - 20, cy - 10, f"≈ {shape_name.capitalize()}")
            painter.drawText(cx - 20, cy + 10, f"side = {side_val:.1f}")

        elif shape_name.endswith("_prism"):
            cx, cy = center_x, center_y
            bw = size * 1.5
            bh = size
            h = size
            offset = size // 3
            # Front face
            painter.drawRect(cx - bw//2, cy - bh//2, bw, bh)
            # Top face
            points = [
                (cx - bw//2, cy - bh//2),
                (cx - bw//2 + offset, cy - bh//2 - offset),
                (cx + bw//2 + offset, cy - bh//2 - offset),
                (cx + bw//2, cy - bh//2),
            ]
            painter.drawPolygon(*[QPointF(x, y) for x, y in points])
            # Side face
            points = [
                (cx + bw//2, cy - bh//2),
                (cx + bw//2 + offset, cy - bh//2 - offset),
                (cx + bw//2 + offset, cy + bh//2 - offset),
                (cx + bw//2, cy + bh//2),
            ]
            painter.drawPolygon(*[QPointF(x, y) for x, y in points])
            # Height/depth
            painter.setPen(dim_pen)
            painter.drawLine(cx + bw//2 + offset + 10, cy - bh//2 - offset, cx + bw//2 + offset + 10, cy + bh//2 - offset)
            painter.setFont(dim_font)
            painter.setPen(QColor(COLORS['primary']))
            height_val = self.current_values.get("height", 0)
            painter.drawText(cx + bw//2 + offset + 15, cy, f"h = {height_val:.1f}")

        else:
            # Default: draw a rounded rect
            painter.drawRoundedRect(center_x - size, center_y - size, 2*size, 2*size, 10, 10)


class ResultCard(QWidget):
    """A card widget for displaying a single calculation result (Area or Volume)."""

    def __init__(
        self,
        title: str,
        icon_color: str,
        unit: str,
        formula: str = "",
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.title = title
        self.icon_color = icon_color
        self.unit = unit
        self.formula = formula
        self._value: Optional[float] = None
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("ResultCard")
        self.setProperty("area", "true" if "Area" in self.title else "false")
        self.setProperty("volume", "true" if "Volume" in self.title else "false")
        self.setStyleSheet(f"""
            #ResultCard {{
                background-color: {COLORS['bg_glass_strong']};
                border: 1px solid {COLORS['border_subtle']};
                border-left: 4px solid {self.icon_color};
                border-radius: {RADIUS['xl']};
                padding: {SPACING['lg']};
            }}
            #ResultCard:hover {{
                border-color: {COLORS['border_accent']};
                background-color: {COLORS['bg_glass']};
                box-shadow: {SHADOWS['lg']};
            }}
            #ResultCard[area="true"] {{
                border-left-color: {COLORS['area_color']};
            }}
            #ResultCard[volume="true"] {{
                border-left-color: {COLORS['volume_color']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 20, 24, 20)

        # Header with icon and title
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        # Icon circle with glow
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(40, 40)
        self.icon_label.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {self.icon_color}, stop:1 {self._darken_color(self.icon_color)});
            border-radius: 20px;
        """)
        # Add glow effect
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(20)
        glow.setColor(QColor(self.icon_color + "80"))
        glow.setOffset(0, 0)
        self.icon_label.setGraphicsEffect(glow)
        header_layout.addWidget(self.icon_label)

        # Title
        title_label = QLabel(self.title)
        title_font = QFont(FONTS["display"])
        title_font.setPointSize(15)
        title_font.setWeight(QFont.Weight.DemiBold)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {self.icon_color};")
        header_layout.addWidget(title_label)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Value display
        self.value_label = QLabel("—")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_font = QFont(FONTS["mono"])
        value_font.setPointSize(36)
        value_font.setWeight(QFont.Weight.Bold)
        self.value_label.setFont(value_font)
        self.value_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(self.value_label)

        # Unit label
        self.unit_label = QLabel(self.unit)
        self.unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        unit_font = QFont(FONTS["primary"])
        unit_font.setPointSize(11)
        unit_font.setWeight(QFont.Weight.Medium)
        self.unit_label.setFont(unit_font)
        self.unit_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(self.unit_label)

        # Formula (optional) - will be added dynamically
        self.formula_label = None

    def _darken_color(self, hex_color: str) -> str:
        """Darken a hex color by 20%."""
        try:
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            r = max(0, int(r * 0.8))
            g = max(0, int(g * 0.8))
            b = max(0, int(b * 0.8))
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return hex_color

    def set_value(self, value: Optional[float | str]):
        """Update the displayed value."""
        parsed = self._parse_value(value)
        if parsed is not None:
            self._value = parsed
            self.value_label.setText(f"{parsed:,.2f}")
        else:
            self._value = None
            self.value_label.setText("—")

    @staticmethod
    def _parse_value(value: Optional[float | str]) -> Optional[float]:
        """Extract numeric value from string or pass through float."""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            import re
            match = re.match(r'^([\d.]+)', value.strip())
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    return None
        return None

    def set_formula(self, formula: str):
        """Set or update the formula display."""
        if formula:
            if self.formula_label is None:
                self.formula_label = QLabel()
                self.formula_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.formula_label.setWordWrap(True)
                formula_font = QFont(FONTS["primary"])
                formula_font.setPointSize(9)
                formula_font.setItalic(True)
                self.formula_label.setFont(formula_font)
                self.formula_label.setStyleSheet(f"""
                    color: {COLORS['text_muted']};
                    background-color: {COLORS['bg_tertiary']};
                    padding: 8px 12px;
                    border-radius: {RADIUS['sm']};
                    border: 1px solid {COLORS['border_subtle']};
                """)
                self.layout().addWidget(self.formula_label)
            self.formula_label.setText(f"Formula: {formula}")
            self.formula_label.setVisible(True)
        elif self.formula_label:
            self.formula_label.setVisible(False)


class ResultsWidget(QWidget):
    """Widget for displaying calculation results with separate Area and Volume cards."""

    # Formulas for different shapes (can be extended)
    # Using ASCII-compatible characters for better cross-platform rendering
    SHAPE_FORMULAS: Dict[str, Dict[str, str]] = {
        # 2D shapes
        "circle": {"area": "pi * r^2"},
        "square": {"area": "side^2"},
        "rectangle": {"area": "base * height"},
        "triangle": {"area": "1/2 * base * height"},
        "rhombus": {"area": "1/2 * d1 * d2"},
        "parallelogram": {"area": "base * height"},
        "trapezoid": {"area": "1/2 * (base1 + base2) * height"},
        "regular_polygon": {"area": "1/2 * perimeter * apothem"},
        # 3D shapes
        "cube": {"area": "6 * side^2", "volume": "side^3"},
        "sphere": {"area": "4 * pi * r^2", "volume": "4/3 * pi * r^3"},
        "cylinder": {"area": "2 * pi * r * (r + h)", "volume": "pi * r^2 * h"},
        "cone": {"area": "pi * r * (r + l)", "volume": "1/3 * pi * r^2 * h"},
        "cone_trunk": {"area": "pi * (r1 + r2) * l + pi * r1^2 + pi * r2^2", "volume": "1/3 * pi * h * (r1^2 + r1*r2 + r2^2)"},
        "pyramid": {"area": "base_area + 1/2 * perimeter * slant_height", "volume": "1/3 * base_area * height"},
        "pyramid_trunk": {"area": "base1 + base2 + 1/2 * (perimeter1 + perimeter2) * slant_height", "volume": "1/3 * h * (base1 + base2 + sqrt(base1*base2))"},
        "tetrahedron": {"area": "sqrt(3) * side^2", "volume": "side^3 / (6*sqrt(2))"},
        "octohedron": {"area": "2*sqrt(3) * side^2", "volume": "sqrt(2)/3 * side^3"},
        "dodecahedron": {"area": "3*sqrt(25+10*sqrt(5)) * side^2", "volume": "(15+7*sqrt(5))/4 * side^3"},
        "icosahedron": {"area": "5*sqrt(3) * side^2", "volume": "5*(3+sqrt(5))/12 * side^3"},
        "rectangular_prism": {"area": "2 * (lw + lh + wh)", "volume": "l * w * h"},
        "quadrangular_prism": {"area": "2 * base_area + perimeter * height", "volume": "base_area * height"},
        "regular_polygon_prism": {"area": "2 * base_area + perimeter * height", "volume": "base_area * height"},
        "rhomboidal_prism": {"area": "2 * base_area + perimeter * height", "volume": "base_area * height"},
        "triangular_prism": {"area": "2 * triangle_area + perimeter * height", "volume": "triangle_area * height"},
        "trapezoidal_prism": {"area": "2 * trapezoid_area + perimeter * height", "volume": "trapezoid_area * height"},
    }

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.current_shape_name: str = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)

        # Area Card
        self.area_card = ResultCard(
            title="Area",
            icon_color=COLORS["area_color"],
            unit="cm²",
            formula=""
        )
        layout.addWidget(self.area_card)

        # Volume Card
        self.volume_card = ResultCard(
            title="Volume",
            icon_color=COLORS["volume_color"],
            unit="cm³",
            formula=""
        )
        self.volume_card.setVisible(False)  # Hidden by default for 2D shapes
        layout.addWidget(self.volume_card)

        layout.addStretch()

    def set_results(self, area: Optional[float | str], volume: Optional[float | str], is_3d: bool, shape_name: str = ""):
        """Update the displayed results."""
        self.current_shape_name = shape_name

        # Update area card
        self.area_card.set_value(area)

        # Update formula for area
        if shape_name and shape_name in self.SHAPE_FORMULAS:
            area_formula = self.SHAPE_FORMULAS[shape_name].get("area", "")
            if area_formula:
                self.area_card.set_formula(area_formula)

        # Update volume card visibility and value
        if is_3d:
            self.volume_card.setVisible(True)
            self.volume_card.set_value(volume)

            # Update formula for volume
            if shape_name and shape_name in self.SHAPE_FORMULAS:
                volume_formula = self.SHAPE_FORMULAS[shape_name].get("volume", "")
                if volume_formula:
                    self.volume_card.set_formula(volume_formula)
        else:
            self.volume_card.setVisible(False)
            self.volume_card.set_formula("")


