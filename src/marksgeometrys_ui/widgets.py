"""Custom widgets for the MarksGeometry UI."""

from typing import Dict, List, Optional, Callable
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QDoubleSpinBox, QSpinBox, QComboBox, QPushButton, QGroupBox,
    QScrollArea, QFrame, QSizePolicy, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor, QPen, QBrush

from .shapes import ShapeConfig, Parameter, get_shape_config


class ParameterWidget(QWidget):
    """Widget for a single parameter input."""

    value_changed = pyqtSignal(str, float)

    def __init__(self, parameter: Parameter, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.parameter = parameter
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Label with tooltip
        label = QLabel(f"{self.parameter.label}:")
        label.setToolTip(self.parameter.tooltip)
        label.setMinimumWidth(140)
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
        self.spinbox.valueChanged.connect(
            lambda v: self.value_changed.emit(self.parameter.name, float(v))
        )
        layout.addWidget(self.spinbox)

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

        # Category selector
        cat_layout = QHBoxLayout()
        cat_layout.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(["2D Shapes", "3D Shapes"])
        self.category_combo.currentTextChanged.connect(self._on_category_changed)
        cat_layout.addWidget(self.category_combo)
        cat_layout.addStretch()
        layout.addLayout(cat_layout)

        # Shape selector
        shape_layout = QHBoxLayout()
        shape_layout.addWidget(QLabel("Shape:"))
        self.shape_combo = QComboBox()
        self.shape_combo.currentTextChanged.connect(self._on_shape_changed)
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

        self.form_container = QWidget()
        self.form_layout = QFormLayout(self.form_container)
        self.form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.form_layout.setFormAlignment(Qt.AlignmentFlag.AlignTop)

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
    """Widget for displaying a simple visualization of the selected shape."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.current_shape: Optional[ShapeConfig] = None
        self.current_values: Dict[str, float] = {}
        self.setMinimumSize(300, 300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_shape(self, shape_config: ShapeConfig, values: Dict[str, float]):
        """Update the visualization for a new shape."""
        self.current_shape = shape_config
        self.current_values = values
        self.update()

    def paintEvent(self, event):
        """Paint a simple representation of the shape."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        painter.fillRect(self.rect(), QColor(245, 245, 250))

        if not self.current_shape:
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Select a shape to visualize")
            return

        # Draw shape name
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(50, 50, 50))
        painter.drawText(10, 30, self.current_shape.display_name)

        # Draw parameters
        font.setPointSize(10)
        font.setBold(False)
        painter.setFont(font)
        y = 55
        for name, value in self.current_values.items():
            param = next((p for p in self.current_shape.parameters if p.name == name), None)
            if param:
                label = f"{param.label}: {value:.2f} {param.unit}"
                painter.drawText(10, y, label)
                y += 22

        # Draw simple geometric representation
        self._draw_shape_representation(painter)

    def _draw_shape_representation(self, painter: QPainter):
        """Draw a simple 2D representation of the shape."""
        if not self.current_shape:
            return

        w = self.width()
        h = self.height()
        center_x = w // 2
        center_y = h // 2 + 30
        size = min(w, h) // 3

        painter.setPen(QPen(QColor(70, 130, 180), 2))
        painter.setBrush(QBrush(QColor(70, 130, 180, 50)))

        shape_name = self.current_shape.name

        # 2D Shapes
        if shape_name == "circle":
            r = size
            painter.drawEllipse(center_x - r, center_y - r, 2 * r, 2 * r)

        elif shape_name == "square":
            s = size * 1.5
            painter.drawRect(center_x - s//2, center_y - s//2, s, s)

        elif shape_name == "rectangle":
            bw = size * 2
            bh = size
            painter.drawRect(center_x - bw//2, center_y - bh//2, bw, bh)

        elif shape_name == "triangle":
            # Equilateral-ish triangle
            points = [
                (center_x, center_y - size),
                (center_x - size, center_y + size//2),
                (center_x + size, center_y + size//2),
            ]
            painter.drawPolygon(*[QPointF(x, y) for x, y in points])

        elif shape_name == "rhombus":
            points = [
                (center_x, center_y - size),
                (center_x + size, center_y),
                (center_x, center_y + size),
                (center_x - size, center_y),
            ]
            painter.drawPolygon(*[QPointF(x, y) for x, y in points])

        elif shape_name == "parallelogram":
            offset = size // 2
            points = [
                (center_x - size + offset, center_y - size//2),
                (center_x + size + offset, center_y - size//2),
                (center_x + size - offset, center_y + size//2),
                (center_x - size - offset, center_y + size//2),
            ]
            painter.drawPolygon(*[QPointF(x, y) for x, y in points])

        elif shape_name == "trapezoid":
            top = size // 2
            bottom = size
            points = [
                (center_x - top, center_y - size//2),
                (center_x + top, center_y - size//2),
                (center_x + bottom, center_y + size//2),
                (center_x - bottom, center_y + size//2),
            ]
            painter.drawPolygon(*[QPointF(x, y) for x, y in points])

        elif shape_name == "regular_polygon":
            import math
            sides = int(self.current_values.get("sidesnumber", 6))
            radius = size
            points = []
            for i in range(sides):
                angle = 2 * math.pi * i / sides - math.pi / 2
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                points.append((x, y))
            painter.drawPolygon(*[QPointF(x, y) for x, y in points])

        # 3D Shapes - draw wireframe-ish representations
        elif shape_name == "cube":
            # Isometric cube
            offset = size // 3
            # Front face
            painter.drawRect(center_x - size, center_y - size, 2*size, 2*size)
            # Top face
            points = [
                (center_x - size, center_y - size),
                (center_x - size + offset, center_y - size - offset),
                (center_x + size + offset, center_y - size - offset),
                (center_x + size, center_y - size),
            ]
            painter.drawPolygon(*[QPointF(x, y) for x, y in points])
            # Side face
            points = [
                (center_x + size, center_y - size),
                (center_x + size + offset, center_y - size - offset),
                (center_x + size + offset, center_y + size - offset),
                (center_x + size, center_y + size),
            ]
            painter.drawPolygon(*[QPointF(x, y) for x, y in points])

        elif shape_name == "sphere":
            r = size
            painter.drawEllipse(center_x - r, center_y - r, 2*r, 2*r)
            # Add a simple shading line
            painter.setPen(QPen(QColor(70, 130, 180, 100), 1))
            for i in range(-r, r, r//4):
                painter.drawLine(center_x - r, center_y + i, center_x + r, center_y + i)

        elif shape_name == "cylinder":
            r = size
            h = size * 2
            # Top ellipse
            painter.drawEllipse(center_x - r, center_y - h//2, 2*r, r//2)
            # Bottom ellipse
            painter.drawEllipse(center_x - r, center_y + h//2, 2*r, r//2)
            # Sides
            painter.drawLine(center_x - r, center_y - h//2, center_x - r, center_y + h//2)
            painter.drawLine(center_x + r, center_y - h//2, center_x + r, center_y + h//2)

        elif shape_name == "cone":
            r = size
            h = size * 2
            # Base ellipse
            painter.drawEllipse(center_x - r, center_y + h//2, 2*r, r//2)
            # Sides to apex
            painter.drawLine(center_x - r, center_y + h//2, center_x, center_y - h//2)
            painter.drawLine(center_x + r, center_y + h//2, center_x, center_y - h//2)

        elif shape_name == "cone_trunk":
            r1 = size // 2
            r2 = size
            h = size * 2
            # Top ellipse
            painter.drawEllipse(center_x - r1, center_y - h//2, 2*r1, r1//2)
            # Bottom ellipse
            painter.drawEllipse(center_x - r2, center_y + h//2, 2*r2, r2//2)
            # Sides
            painter.drawLine(center_x - r1, center_y - h//2, center_x - r2, center_y + h//2)
            painter.drawLine(center_x + r1, center_y - h//2, center_x + r2, center_y + h//2)

        elif shape_name in ("pyramid", "tetrahedron"):
            # Simple pyramid
            base_size = size * 1.5
            h = size * 1.5
            points = [
                (center_x - base_size//2, center_y + h//2),
                (center_x + base_size//2, center_y + h//2),
                (center_x, center_y - h//2),
            ]
            painter.drawPolygon(*[QPointF(x, y) for x, y in points])

        elif shape_name == "octohedron":
            # Two pyramids base-to-base
            s = size
            points = [
                (center_x, center_y - s),
                (center_x - s, center_y),
                (center_x, center_y + s),
                (center_x + s, center_y),
            ]
            painter.drawPolygon(*[QPointF(x, y) for x, y in points])

        elif shape_name in ("dodecahedron", "icosahedron"):
            # Draw as circle with label
            painter.drawEllipse(center_x - size, center_y - size, 2*size, 2*size)
            painter.drawText(center_x - 30, center_y + 5, "≈")

        elif shape_name.endswith("_prism"):
            # Generic prism representation
            bw = size * 1.5
            bh = size
            h = size
            offset = size // 3
            # Front face
            painter.drawRect(center_x - bw//2, center_y - bh//2, bw, bh)
            # Top face
            points = [
                (center_x - bw//2, center_y - bh//2),
                (center_x - bw//2 + offset, center_y - bh//2 - offset),
                (center_x + bw//2 + offset, center_y - bh//2 - offset),
                (center_x + bw//2, center_y - bh//2),
            ]
            painter.drawPolygon(*[QPointF(x, y) for x, y in points])
            # Side face
            points = [
                (center_x + bw//2, center_y - bh//2),
                (center_x + bw//2 + offset, center_y - bh//2 - offset),
                (center_x + bw//2 + offset, center_y + bh//2 - offset),
                (center_x + bw//2, center_y + bh//2),
            ]
            painter.drawPolygon(*[QPointF(x, y) for x, y in points])

        else:
            # Default: draw a rounded rect
            painter.drawRoundedRect(center_x - size, center_y - size, 2*size, 2*size, 10, 10)


class ResultsWidget(QWidget):
    """Widget for displaying calculation results."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Area result
        self.area_group = QGroupBox("Area")
        area_layout = QVBoxLayout(self.area_group)
        self.area_label = QLabel("—")
        self.area_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        self.area_label.setFont(font)
        self.area_label.setStyleSheet("color: #2E7D32;")
        area_layout.addWidget(self.area_label)
        self.area_unit_label = QLabel("cm²")
        self.area_unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        area_layout.addWidget(self.area_unit_label)
        layout.addWidget(self.area_group)

        # Volume result
        self.volume_group = QGroupBox("Volume")
        volume_layout = QVBoxLayout(self.volume_group)
        self.volume_label = QLabel("—")
        self.volume_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.volume_label.setFont(font)
        self.volume_label.setStyleSheet("color: #1565C0;")
        volume_layout.addWidget(self.volume_label)
        self.volume_unit_label = QLabel("cm³")
        self.volume_unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        volume_layout.addWidget(self.volume_unit_label)
        layout.addWidget(self.volume_group)

        # Initially hide volume for 2D shapes
        self.volume_group.setVisible(False)

    def set_results(self, area: Optional[float], volume: Optional[float], is_3d: bool):
        """Update the displayed results."""
        if area is not None:
            self.area_label.setText(f"{area:,.2f}")
        else:
            self.area_label.setText("—")

        if volume is not None:
            self.volume_label.setText(f"{volume:,.2f}")
            self.volume_group.setVisible(True)
        else:
            self.volume_label.setText("—")
            self.volume_group.setVisible(is_3d)


# Need to import QPointF for polygon drawing
from PyQt6.QtCore import QPointF