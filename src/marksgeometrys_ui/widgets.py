"""Custom widgets for the MarksGeometrys UI."""

import math
from typing import Dict, List, Optional, Callable, Tuple
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QDoubleSpinBox, QSpinBox, QComboBox, QPushButton, QGroupBox,
    QScrollArea, QFrame, QSizePolicy, QMessageBox, QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, QPointF, QRectF, QTimer, QPropertyAnimation,
    QEasingCurve, QParallelAnimationGroup, QSequentialAnimationGroup,
    QAbstractAnimation, pyqtProperty, QRect, QEasingCurve
)
from PyQt6.QtGui import (
    QFont, QPixmap, QPainter, QColor, QPen, QBrush,
    QLinearGradient, QRadialGradient, QConicalGradient,
    QPainterPath, QPolygonF, QFontMetrics, QTransform,
    QPolygon, QOpenGLContext, QSurfaceFormat
)

# OpenGL imports
try:
    from OpenGL import GL as gl
    from OpenGL import GLU as glu
    from OpenGL.arrays import vbo
    OPENGL_AVAILABLE = True
except ImportError:
    OPENGL_AVAILABLE = False
    gl = None
    glu = None
    vbo = None

from .shapes import ShapeConfig, Parameter, get_shape_config
from .theme import COLORS, FONTS, RADIUS, RADIUS_NUM, SHADOWS, SPACING


class ParameterWidget(QWidget):
    """Widget for a single parameter input with hover animation."""

    value_changed = pyqtSignal(str, float)

    def __init__(self, parameter: Parameter, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.parameter = parameter
        self._hover_animation = None
        self._setup_ui()
        self._setup_animations()

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

    def _setup_animations(self):
        """Setup hover animations for the spinbox."""
        # Create opacity effect for smooth hover transition
        self._hover_effect = QGraphicsOpacityEffect(self.spinbox)
        self._hover_effect.setOpacity(1.0)
        self.spinbox.setGraphicsEffect(self._hover_effect)

        self._hover_animation = QPropertyAnimation(self._hover_effect, b"opacity")
        self._hover_animation.setDuration(150)
        self._hover_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Install event filter for hover detection
        self.spinbox.installEventFilter(self)

    def eventFilter(self, obj, event):
        """Handle hover events for smooth animations."""
        if obj == self.spinbox:
            if event.type() == event.Type.Enter:
                self._hover_animation.stop()
                self._hover_animation.setStartValue(self._hover_effect.opacity())
                self._hover_animation.setEndValue(1.0)
                self._hover_animation.start()
            elif event.type() == event.Type.Leave:
                self._hover_animation.stop()
                self._hover_animation.setStartValue(self._hover_effect.opacity())
                self._hover_animation.setEndValue(1.0)
                self._hover_animation.start()
        return super().eventFilter(obj, event)

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
        painter.drawRoundedRect(panel_x - 10, panel_y - 10, panel_width, len(self.current_shape.parameters) * line_height + 20, RADIUS_NUM['md'], RADIUS_NUM['md'])

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

        # Shape fill with subtle gradient
        shape_brush = QBrush(QColor(COLORS['primary'] + "33"))  # 20% opacity

        painter.setPen(accent_pen)
        painter.setBrush(shape_brush)

        shape_name = self.current_shape.name

        # Dimension colors from theme
        CYAN = QColor(COLORS['primary'])       # #00D4FF - radius, primary dimensions
        GREEN = QColor(COLORS['success'])      # #10B981 - height
        ORANGE = QColor(COLORS['warning'])     # #F59E0B - base
        PURPLE = QColor(COLORS['secondary'])   # #7C4DFF - diagonals, apothem

        # Area/Volume visualization colors
        AREA_COLOR = QColor(COLORS['area_color'])     # Green for area
        AREA_FILL = QColor(COLORS['area_color'] + "40")  # Semi-transparent green
        VOLUME_COLOR = QColor(COLORS['volume_color'])   # Cyan for volume
        VOLUME_FILL = QColor(COLORS['volume_color'] + "30")  # Semi-transparent cyan

        # 2D Shapes
        if shape_name == "circle":
            r = size
            cx, cy = center_x, center_y
            # Draw AREA fill (green semi-transparent)
            painter.setBrush(QBrush(AREA_FILL))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(cx - r, cy - r, 2 * r, 2 * r)
            # Draw outline
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(accent_pen)
            painter.drawEllipse(cx - r, cy - r, 2 * r, 2 * r)
            # Draw "AREA" label in center
            self._draw_area_label(painter, cx, cy, "AREA", AREA_COLOR)
            # Radius dimension line with arrows
            radius_val = self.current_values.get("radius", 0)
            self._draw_dimension_line(
                painter, cx, cy, cx + r, cy,
                f"r = {radius_val:.1f} cm", CYAN,
                offset=0, above=True
            )

        elif shape_name == "square":
            s = size * 1.5
            cx, cy = center_x, center_y
            # Draw AREA fill
            painter.setBrush(QBrush(AREA_FILL))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(cx - s//2, cy - s//2, s, s)
            # Draw outline
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(accent_pen)
            painter.drawRect(cx - s//2, cy - s//2, s, s)
            # Draw "AREA" label
            self._draw_area_label(painter, cx, cy, "AREA", AREA_COLOR)
            # Side dimension
            side_val = self.current_values.get("side", 0)
            self._draw_dimension_line(
                painter, cx - s//2, cy + s//2, cx + s//2, cy + s//2,
                f"side = {side_val:.1f} cm", ORANGE,
                offset=15, above=False
            )

        elif shape_name == "rectangle":
            bw = size * 2
            bh = size
            cx, cy = center_x, center_y
            # Draw AREA fill
            painter.setBrush(QBrush(AREA_FILL))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(cx - bw//2, cy - bh//2, bw, bh)
            # Draw outline
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(accent_pen)
            painter.drawRect(cx - bw//2, cy - bh//2, bw, bh)
            # Draw "AREA" label
            self._draw_area_label(painter, cx, cy, "AREA", AREA_COLOR)
            # Base dimension (bottom)
            base_val = self.current_values.get("base", 0)
            self._draw_dimension_line(
                painter, cx - bw//2, cy + bh//2, cx + bw//2, cy + bh//2,
                f"base = {base_val:.1f} cm", ORANGE,
                offset=15, above=False
            )
            # Height dimension (right side)
            height_val = self.current_values.get("height", 0)
            self._draw_dimension_line(
                painter, cx + bw//2, cy - bh//2, cx + bw//2, cy + bh//2,
                f"h = {height_val:.1f} cm", GREEN,
                offset=15, above=False
            )

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
            # Draw AREA fill
            painter.setBrush(QBrush(AREA_FILL))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPolygon(*[QPointF(x, y) for x, y in points])
            # Draw outline
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(accent_pen)
            painter.drawPolygon(*[QPointF(x, y) for x, y in points])
            # Draw "AREA" label (centroid of triangle)
            centroid_x = cx
            centroid_y = cy + bh//6  # Centroid is at 1/3 height from base
            self._draw_area_label(painter, centroid_x, centroid_y, "AREA", AREA_COLOR)
            # Base dimension
            self._draw_dimension_line(
                painter, cx - bw//2, cy + bh//2, cx + bw//2, cy + bh//2,
                f"base = {base_val:.1f} cm", ORANGE,
                offset=15, above=False
            )
            # Height dimension (dashed line from base midpoint to apex)
            self._draw_dimension_line(
                painter, cx, cy + bh//2, cx, cy - bh//2,
                f"h = {height_val:.1f} cm", GREEN,
                offset=15, above=False, dashed=True
            )

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
            # Draw AREA fill
            painter.setBrush(QBrush(AREA_FILL))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPolygon(*[QPointF(x, y) for x, y in points])
            # Draw outline
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(accent_pen)
            painter.drawPolygon(*[QPointF(x, y) for x, y in points])
            # Draw "AREA" label
            self._draw_area_label(painter, cx, cy, "AREA", AREA_COLOR)
            # Large diagonal (vertical)
            self._draw_dimension_line(
                painter, cx, cy - r1, cx, cy + r1,
                f"D = {d1:.1f} cm", PURPLE,
                offset=10, above=False
            )
            # Small diagonal (horizontal)
            self._draw_dimension_line(
                painter, cx - r2, cy, cx + r2, cy,
                f"d = {d2:.1f} cm", PURPLE,
                offset=10, above=True
            )

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
            # Draw AREA fill
            painter.setBrush(QBrush(AREA_FILL))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPolygon(*[QPointF(x, y) for x, y in points])
            # Draw outline
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(accent_pen)
            painter.drawPolygon(*[QPointF(x, y) for x, y in points])
            # Draw "AREA" label
            self._draw_area_label(painter, cx, cy, "AREA", AREA_COLOR)
            # Base dimension (bottom edge)
            self._draw_dimension_line(
                painter, cx - bw//2 - offset, cy + bh//2, cx + bw//2 - offset, cy + bh//2,
                f"base = {base_val:.1f} cm", ORANGE,
                offset=15, above=False
            )
            # Height dimension (vertical on right side)
            self._draw_dimension_line(
                painter, cx + bw//2 - offset, cy - bh//2, cx + bw//2 - offset, cy + bh//2,
                f"h = {height_val:.1f} cm", GREEN,
                offset=15, above=False
            )

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
            # Draw AREA fill
            painter.setBrush(QBrush(AREA_FILL))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPolygon(*[QPointF(x, y) for x, y in points])
            # Draw outline
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(accent_pen)
            painter.drawPolygon(*[QPointF(x, y) for x, y in points])
            # Draw "AREA" label
            self._draw_area_label(painter, cx, cy, "AREA", AREA_COLOR)
            # Large base (bottom)
            self._draw_dimension_line(
                painter, cx - bw1//2, cy + bh//2, cx + bw1//2, cy + bh//2,
                f"base₁ = {b1:.1f} cm", ORANGE,
                offset=15, above=False
            )
            # Small base (top)
            self._draw_dimension_line(
                painter, cx - bw2//2, cy - bh//2, cx + bw2//2, cy - bh//2,
                f"base₂ = {b2:.1f} cm", ORANGE,
                offset=10, above=True
            )
            # Height (right side)
            self._draw_dimension_line(
                painter, cx + bw1//2, cy - bh//2, cx + bw1//2, cy + bh//2,
                f"h = {h:.1f} cm", GREEN,
                offset=15, above=False
            )

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
            # Draw AREA fill
            painter.setBrush(QBrush(AREA_FILL))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPolygon(*[QPointF(x, y) for x, y in points])
            # Draw outline
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(accent_pen)
            painter.drawPolygon(*[QPointF(x, y) for x, y in points])
            # Draw "AREA" label
            self._draw_area_label(painter, cx, cy, "AREA", AREA_COLOR)
            # Radius (circumradius) line
            R = radius * scale
            self._draw_dimension_line(
                painter, cx, cy, cx, cy - R,
                f"R = {R/scale:.1f} cm", CYAN,
                offset=10, above=True
            )
            # Apothem line (to midpoint of first side)
            if points:
                x1, y1 = points[0]
                x2, y2 = points[1]
                mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                self._draw_dimension_line(
                    painter, cx, cy, mx, my,
                    f"a = {apothem_val:.1f} cm", PURPLE,
                    offset=10, above=False
                )
                # Side length indicator
                self._draw_dimension_line(
                    painter, x1, y1, x2, y2,
                    f"s = {side_val:.1f} cm", GREEN,
                    offset=8, above=True, inline=True
                )

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
            # Side dimension (right edge)
            self._draw_dimension_line(
                painter, cx + s, cy - s, cx + s, cy + s,
                f"side = {side_val:.1f} cm", CYAN,
                offset=15, above=False
            )

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
            self._draw_dimension_line(
                painter, cx, cy, cx + r, cy,
                f"r = {radius_val:.1f} cm", CYAN,
                offset=0, above=True
            )
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
            # Radius (on bottom ellipse)
            self._draw_dimension_line(
                painter, cx, cy + h//2, cx + r, cy + h//2,
                f"r = {radius_val:.1f} cm", CYAN,
                offset=0, above=False
            )
            # Height (right side)
            self._draw_dimension_line(
                painter, cx + r, cy - h//2, cx + r, cy + h//2,
                f"h = {height_val:.1f} cm", GREEN,
                offset=15, above=False
            )

        elif shape_name == "cone":
            cx, cy = center_x, center_y
            r = size
            h = size * 2
            radius_val = self.current_values.get("radius", 1)
            height_val = self.current_values.get("height", 1)
            # Base ellipse
            painter.drawEllipse(cx - r, cy + h//2, 2*r, r//2)
            # Sides to apex
            painter.drawLine(cx - r, cy + h//2, cx, cy - h//2)
            painter.drawLine(cx + r, cy + h//2, cx, cy - h//2)
            # Radius (on base)
            self._draw_dimension_line(
                painter, cx, cy + h//2, cx + r, cy + h//2,
                f"r = {radius_val:.1f} cm", CYAN,
                offset=0, above=False
            )
            # Height (center line)
            self._draw_dimension_line(
                painter, cx, cy - h//2, cx, cy + h//2,
                f"h = {height_val:.1f} cm", GREEN,
                offset=15, above=False, dashed=True
            )

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
            # Top radius
            self._draw_dimension_line(
                painter, cx, cy - sh//2, cx + sr1, cy - sh//2,
                f"r₁ = {r1:.1f} cm", CYAN,
                offset=0, above=True
            )
            # Bottom radius
            self._draw_dimension_line(
                painter, cx, cy + sh//2, cx + sr2, cy + sh//2,
                f"r₂ = {r2:.1f} cm", CYAN,
                offset=0, above=False
            )
            # Height
            self._draw_dimension_line(
                painter, cx + sr2, cy - sh//2, cx + sr2, cy + sh//2,
                f"h = {h:.1f} cm", GREEN,
                offset=15, above=False
            )

        elif shape_name in ("pyramid", "tetrahedron"):
            cx, cy = center_x, center_y
            base_val = self.current_values.get("base", 1)
            height_val = self.current_values.get("height", 1)
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
            self._draw_dimension_line(
                painter, cx - bw//2, cy + bh//2, cx + bw//2, cy + bh//2,
                f"base = {base_val:.1f} cm", ORANGE,
                offset=15, above=False
            )
            # Height
            self._draw_dimension_line(
                painter, cx, cy - bh//2, cx, cy + bh//2,
                f"h = {height_val:.1f} cm", GREEN,
                offset=15, above=False, dashed=True
            )

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
            self._draw_dimension_line(
                painter, cx - s, cy, cx, cy - s,
                f"side = {side_val:.1f} cm", CYAN,
                offset=10, above=True
            )

        elif shape_name in ("dodecahedron", "icosahedron"):
            cx, cy = center_x, center_y
            side_val = self.current_values.get("side", 1)
            r = size
            painter.drawEllipse(cx - r, cy - r, 2*r, 2*r)
            # Approximation label
            dim_font = QFont(FONTS["mono"])
            dim_font.setPointSize(9)
            painter.setFont(dim_font)
            painter.setPen(QColor(COLORS['primary']))
            painter.drawText(cx - 20, cy - 10, f"≈ {shape_name.capitalize()}")
            painter.drawText(cx - 20, cy + 10, f"side = {side_val:.1f} cm")

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
            # Height/depth (right edge)
            height_val = self.current_values.get("height", 0)
            self._draw_dimension_line(
                painter, cx + bw//2 + offset, cy - bh//2 - offset, cx + bw//2 + offset, cy + bh//2 - offset,
                f"h = {height_val:.1f} cm", GREEN,
                offset=15, above=False
            )

        else:
            # Default: draw a rounded rect
            painter.drawRoundedRect(center_x - size, center_y - size, 2*size, 2*size, 10, 10)

    def _draw_dimension_line(self, painter: QPainter, x1: float, y1: float, x2: float, y2: float,
                              label: str, color: QColor, offset: float = 10,
                              above: bool = True, dashed: bool = False, inline: bool = False):
        """Draw a dimension line with arrows and label.

        Args:
            painter: QPainter instance
            x1, y1: Start point of dimension line
            x2, y2: End point of dimension line
            label: Text label to display
            color: Color for the dimension line and label
            offset: Distance from shape to dimension line
            above: If True, label is placed above/outside the line; if False, below/inside
            dashed: If True, draw dashed line for height/apothem
            inline: If True, draw label along the line (for side lengths)
        """
        # Calculate angle and perpendicular direction
        dx = x2 - x1
        dy = y2 - y1
        length = math.hypot(dx, dy)

        if length == 0:
            return

        # Unit vectors
        ux = dx / length
        uy = dy / length
        # Perpendicular (rotated 90 degrees CCW)
        px = -uy
        py = ux

        # Arrow head size
        arrow_size = 8

        # Offset the dimension line from the shape
        ox = px * offset
        oy = py * offset

        # Dimension line start/end points (offset from shape)
        dim_x1 = x1 + ox
        dim_y1 = y1 + oy
        dim_x2 = x2 + ox
        dim_y2 = y2 + oy

        # Extension lines (from shape to dimension line)
        ext_len = 5
        ext_x1 = x1 - ux * ext_len
        ext_y1 = y1 - uy * ext_len
        ext_x2 = x2 + ux * ext_len
        ext_y2 = y2 + uy * ext_len

        # Set up pens
        dim_pen = QPen(color, 2)
        dim_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        if dashed:
            dim_pen.setStyle(Qt.PenStyle.DashLine)
            dim_pen.setDashPattern([4, 4])

        ext_pen = QPen(color, 1)
        ext_pen.setStyle(Qt.PenStyle.DashLine)
        ext_pen.setDashPattern([3, 3])

        arrow_pen = QPen(color, 2)
        arrow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        arrow_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)

        # Draw extension lines
        painter.setPen(ext_pen)
        painter.drawLine(int(x1), int(y1), int(ext_x1), int(ext_y1))
        painter.drawLine(int(x2), int(y2), int(ext_x2), int(ext_y2))

        # Draw dimension line
        painter.setPen(dim_pen)
        painter.drawLine(int(dim_x1), int(dim_y1), int(dim_x2), int(dim_y2))

        # Draw arrow heads at both ends
        # Arrow at start (pointing towards line)
        ax1 = dim_x1 - ux * arrow_size + py * arrow_size * 0.5
        ay1 = dim_y1 - uy * arrow_size + px * arrow_size * 0.5
        ax2 = dim_x1 - ux * arrow_size - py * arrow_size * 0.5
        ay2 = dim_y1 - uy * arrow_size - px * arrow_size * 0.5

        painter.setPen(arrow_pen)
        painter.drawLine(int(dim_x1), int(dim_y1), int(ax1), int(ay1))
        painter.drawLine(int(dim_x1), int(dim_y1), int(ax2), int(ay2))

        # Arrow at end (pointing towards line)
        bx1 = dim_x2 + ux * arrow_size + py * arrow_size * 0.5
        by1 = dim_y2 + uy * arrow_size + px * arrow_size * 0.5
        bx2 = dim_x2 + ux * arrow_size - py * arrow_size * 0.5
        by2 = dim_y2 + uy * arrow_size - px * arrow_size * 0.5

        painter.drawLine(int(dim_x2), int(dim_y2), int(bx1), int(by1))
        painter.drawLine(int(dim_x2), int(dim_y2), int(bx2), int(by2))

        # Draw label with background
        if inline:
            # Label along the line (for side lengths)
            mid_x = (dim_x1 + dim_x2) / 2
            mid_y = (dim_y1 + dim_y2) / 2
            self._draw_dimension_label(painter, mid_x, mid_y, label, color, angle=math.degrees(math.atan2(dy, dx)))
        else:
            # Label perpendicular to line
            mid_x = (dim_x1 + dim_x2) / 2
            mid_y = (dim_y1 + dim_y2) / 2

            # Determine label position (above or below the dimension line)
            label_offset = 20 if above else -20
            label_x = mid_x + px * label_offset
            label_y = mid_y + py * label_offset

            self._draw_dimension_label(painter, label_x, label_y, label, color)

    def _draw_dimension_label(self, painter: QPainter, x: float, y: float, text: str,
                               color: QColor, angle: float = 0):
        """Draw a dimension label with semi-transparent background."""
        font = QFont(FONTS["mono"])
        font.setPointSize(10)
        font.setWeight(QFont.Weight.Medium)
        painter.setFont(font)

        metrics = QFontMetrics(font)
        text_rect = metrics.boundingRect(text)
        text_width = text_rect.width()
        text_height = text_rect.height()

        # Padding around text
        padding_x = 8
        padding_y = 4

        # Background rect
        bg_rect = QRectF(
            x - text_width / 2 - padding_x,
            y - text_height / 2 - padding_y,
            text_width + 2 * padding_x,
            text_height + 2 * padding_y
        )

        # Draw background with glow effect
        bg_color = QColor(color)
        bg_color.setAlpha(180)  # Semi-transparent

        # Create gradient for glow effect
        gradient = QRadialGradient(x, y, max(text_width, text_height))
        gradient.setColorAt(0, QColor(color.red(), color.green(), color.blue(), 60))
        gradient.setColorAt(0.5, QColor(color.red(), color.green(), color.blue(), 30))
        gradient.setColorAt(1, QColor(0, 0, 0, 0))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(bg_rect.adjusted(-10, -10, 10, 10), 6, 6)

        # Draw solid background
        painter.setBrush(QBrush(QColor(COLORS['bg_tertiary'] + "E0")))  # Dark background with alpha
        painter.setPen(QPen(color, 1))
        painter.drawRoundedRect(bg_rect, 4, 4)

        # Draw text
        painter.setPen(QPen(QColor(COLORS['text_primary']), 1))
        if angle != 0:
            painter.save()
            painter.translate(x, y)
            painter.rotate(angle)
            painter.drawText(-text_width / 2, text_height / 2 - 1, text)
            painter.restore()
        else:
            painter.drawText(int(x - text_width / 2), int(y + text_height / 2 - 1), text)

    def _draw_area_label(self, painter: QPainter, x: float, y: float, text: str, color: QColor):
        """Draw an 'AREA' or 'VOLUME' label at the center of a shape with prominent styling."""
        font = QFont(FONTS["display"])
        font.setPointSize(14)
        font.setWeight(QFont.Weight.Bold)
        painter.setFont(font)

        metrics = QFontMetrics(font)
        text_rect = metrics.boundingRect(text)
        text_width = text_rect.width()
        text_height = text_rect.height()

        # Larger padding for area/volume labels
        padding_x = 16
        padding_y = 8

        # Background rect
        bg_rect = QRectF(
            x - text_width / 2 - padding_x,
            y - text_height / 2 - padding_y,
            text_width + 2 * padding_x,
            text_height + 2 * padding_y
        )

        # Draw outer glow
        glow_color = QColor(color)
        glow_color.setAlpha(80)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(glow_color))
        painter.drawRoundedRect(bg_rect.adjusted(-8, -8, 8, 8), 12, 12)

        # Draw solid background with gradient
        gradient = QLinearGradient(
            bg_rect.topLeft().x(), bg_rect.topLeft().y(),
            bg_rect.bottomRight().x(), bg_rect.bottomRight().y()
        )
        gradient.setColorAt(0, QColor(color.red(), color.green(), color.blue(), 200))
        gradient.setColorAt(1, QColor(color.red(), color.green(), color.blue(), 150))
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(color, 2))
        painter.drawRoundedRect(bg_rect, 8, 8)

        # Draw text with outline for better readability
        painter.setPen(QPen(QColor(0, 0, 0, 180), 2))
        painter.drawText(int(x - text_width / 2), int(y + text_height / 2 - 1), text)
        painter.setPen(QPen(QColor(COLORS['text_on_primary']), 1))
        painter.drawText(int(x - text_width / 2), int(y + text_height / 2 - 1), text)

    def _draw_volume_label(self, painter: QPainter, x: float, y: float, text: str, color: QColor):
        """Draw a 'VOLUME' label for 3D shapes (isometric view)."""
        font = QFont(FONTS["display"])
        font.setPointSize(12)
        font.setWeight(QFont.Weight.Bold)
        painter.setFont(font)

        metrics = QFontMetrics(font)
        text_rect = metrics.boundingRect(text)
        text_width = text_rect.width()
        text_height = text_rect.height()

        padding_x = 14
        padding_y = 7

        bg_rect = QRectF(
            x - text_width / 2 - padding_x,
            y - text_height / 2 - padding_y,
            text_width + 2 * padding_x,
            text_height + 2 * padding_y
        )

        # Outer glow
        glow_color = QColor(color)
        glow_color.setAlpha(80)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(glow_color))
        painter.drawRoundedRect(bg_rect.adjusted(-6, -6, 6, 6), 10, 10)

        # Solid background
        gradient = QLinearGradient(
            bg_rect.topLeft().x(), bg_rect.topLeft().y(),
            bg_rect.bottomRight().x(), bg_rect.bottomRight().y()
        )
        gradient.setColorAt(0, QColor(color.red(), color.green(), color.blue(), 200))
        gradient.setColorAt(1, QColor(color.red(), color.green(), color.blue(), 150))
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(color, 2))
        painter.drawRoundedRect(bg_rect, 6, 6)

        # Text with outline
        painter.setPen(QPen(QColor(0, 0, 0, 180), 2))
        painter.drawText(int(x - text_width / 2), int(y + text_height / 2 - 1), text)
        painter.setPen(QPen(QColor(COLORS['text_on_primary']), 1))
        painter.drawText(int(x - text_width / 2), int(y + text_height / 2 - 1), text)


class ResultCard(QWidget):
    """A card widget for displaying a single calculation result (Area or Volume) with fade animations."""

    def __init__(
        self,
        title: str,
        icon_color: str,
        unit: str,
        formula: str = "",
        is_area: bool = True,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.title = title
        self.icon_color = icon_color
        self.unit = unit
        self.formula = formula
        self.is_area = is_area
        self._value: Optional[float] = None
        self._fade_animation = None
        self._slide_animation = None
        self._setup_ui()
        self._setup_animations()

    def _setup_ui(self):
        self.setObjectName("ResultCard")
        self.setProperty("area", "true" if self.is_area else "false")
        self.setProperty("volume", "true" if not self.is_area else "false")

        # Different background tints for area vs volume
        if self.is_area:
            bg_tint = "rgba(34, 197, 94, 0.06)"  # Subtle green tint
            border_glow = COLORS['area_glow']
        else:
            bg_tint = "rgba(6, 182, 212, 0.06)"  # Subtle cyan tint
            border_glow = COLORS['volume_glow']

        self.setStyleSheet(f"""
            #ResultCard {{
                background-color: {bg_tint};
                border: 2px solid {COLORS['border_subtle']};
                border-left: 6px solid {self.icon_color};
                border-radius: {RADIUS['xl']};
                padding: {SPACING['lg']};
            }}
            #ResultCard:hover {{
                border-color: {border_glow};
                background-color: {bg_tint.replace("0.06", "0.10")};
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
        layout.setSpacing(14)
        layout.setContentsMargins(28, 22, 28, 22)

        # Header with icon and title
        header_layout = QHBoxLayout()
        header_layout.setSpacing(14)

        # Icon circle with glow - different icons for area/volume
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(48, 48)
        # Add an icon character based on type
        icon_char = "▢" if self.is_area else "⬢"  # Square for area, Hexagon for volume
        self.icon_label.setText(icon_char)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_font = QFont(FONTS["display"])
        icon_font.setPointSize(20)
        self.icon_label.setFont(icon_font)
        self.icon_label.setStyleSheet(f"""
            color: {self.icon_color};
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {self.icon_color}33, stop:1 {self._darken_color(self.icon_color)}33);
            border-radius: 24px;
            border: 2px solid {self.icon_color}66;
        """)
        # Add glow effect
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(24)
        glow.setColor(QColor(self.icon_color + "80"))
        glow.setOffset(0, 0)
        self.icon_label.setGraphicsEffect(glow)
        header_layout.addWidget(self.icon_label)

        # Title - Spanish labels
        title_label = QLabel(self.title)
        title_font = QFont(FONTS["display"])
        title_font.setPointSize(16)
        title_font.setWeight(QFont.Weight.DemiBold)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {self.icon_color}; letter-spacing: 1px;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Value display
        self.value_label = QLabel("—")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_font = QFont(FONTS["mono"])
        value_font.setPointSize(42)
        value_font.setWeight(QFont.Weight.Bold)
        self.value_label.setFont(value_font)
        self.value_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(self.value_label)

        # Unit label - more prominent
        self.unit_label = QLabel(self.unit)
        self.unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        unit_font = QFont(FONTS["display"])
        unit_font.setPointSize(14)
        unit_font.setWeight(QFont.Weight.Medium)
        self.unit_label.setFont(unit_font)
        self.unit_label.setStyleSheet(f"""
            color: {self.icon_color};
            background-color: {self.icon_color}22;
            padding: 6px 16px;
            border-radius: {RADIUS['full']};
            border: 1px solid {self.icon_color}44;
        """)
        layout.addWidget(self.unit_label)

        # Formula (optional) - will be added dynamically
        self.formula_label = None

    def _setup_animations(self):
        """Setup fade and slide animations."""
        # Opacity effect for fade animation
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity_effect)

        self._fade_animation = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_animation.setDuration(300)
        self._fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Slide animation using geometry
        self._slide_animation = QPropertyAnimation(self, b"geometry")
        self._slide_animation.setDuration(300)
        self._slide_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def fade_in(self, duration: int = 300):
        """Fade in the card with slide up animation."""
        # Start from transparent and slightly below
        start_rect = self.geometry()
        end_rect = start_rect
        start_rect.moveTop(start_rect.top() + 20)

        self._opacity_effect.setOpacity(0.0)
        self.setGeometry(start_rect)
        self.show()

        self._fade_animation.stop()
        self._fade_animation.setDuration(duration)
        self._fade_animation.setStartValue(0.0)
        self._fade_animation.setEndValue(1.0)

        self._slide_animation.stop()
        self._slide_animation.setDuration(duration)
        self._slide_animation.setStartValue(start_rect)
        self._slide_animation.setEndValue(end_rect)

        # Run both animations in parallel
        self._animation_group = QParallelAnimationGroup()
        self._animation_group.addAnimation(self._fade_animation)
        self._animation_group.addAnimation(self._slide_animation)
        self._animation_group.start()

    def fade_out(self, duration: int = 200, on_finished: Optional[Callable] = None):
        """Fade out the card with slide down animation."""
        start_rect = self.geometry()
        end_rect = start_rect
        end_rect.moveTop(end_rect.top() + 20)

        self._fade_animation.stop()
        self._fade_animation.setDuration(duration)
        self._fade_animation.setStartValue(self._opacity_effect.opacity())
        self._fade_animation.setEndValue(0.0)

        self._slide_animation.stop()
        self._slide_animation.setDuration(duration)
        self._slide_animation.setStartValue(start_rect)
        self._slide_animation.setEndValue(end_rect)

        self._animation_group = QParallelAnimationGroup()
        self._animation_group.addAnimation(self._fade_animation)
        self._animation_group.addAnimation(self._slide_animation)

        if on_finished:
            self._animation_group.finished.connect(on_finished)

        self._animation_group.start()

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
        """Update the displayed value with a subtle pulse animation."""
        parsed = self._parse_value(value)
        if parsed is not None:
            self._value = parsed
            # Pulse animation on value change
            self._pulse_value()
            self.value_label.setText(f"{parsed:,.2f}")
        else:
            self._value = None
            self.value_label.setText("—")

    def _pulse_value(self):
        """Create a subtle pulse animation on the value label."""
        pulse_anim = QPropertyAnimation(self.value_label, b"geometry")
        pulse_anim.setDuration(150)
        pulse_anim.setEasingCurve(QEasingCurve.Type.OutQuad)

        start_rect = self.value_label.geometry()
        # Slightly scale up
        pulse_anim.setStartValue(start_rect)
        pulse_anim.setEndValue(QRect(
            start_rect.x() - 2, start_rect.y() - 2,
            start_rect.width() + 4, start_rect.height() + 4
        ))

        # Return to normal
        return_anim = QPropertyAnimation(self.value_label, b"geometry")
        return_anim.setDuration(150)
        return_anim.setEasingCurve(QEasingCurve.Type.OutBounce)
        return_anim.setStartValue(QRect(
            start_rect.x() - 2, start_rect.y() - 2,
            start_rect.width() + 4, start_rect.height() + 4
        ))
        return_anim.setEndValue(start_rect)

        seq = QSequentialAnimationGroup()
        seq.addAnimation(pulse_anim)
        seq.addAnimation(return_anim)
        seq.start()
        self._pulse_seq = seq  # Keep reference

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
        self._volume_visible = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Area Card
        self.area_card = ResultCard(
            title="AREA",
            icon_color=COLORS["area_color"],
            unit="cm²",
            formula="",
            is_area=True
        )
        layout.addWidget(self.area_card)

        # Visual separator between cards - gradient line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Plain)
        separator.setFixedHeight(3)
        separator.setStyleSheet(f"""
            QFrame {{
                border: none;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['area_color']},
                    stop:0.5 {COLORS['primary']},
                    stop:1 {COLORS['volume_color']}
                );
                margin: 10px 20px;
                border-radius: 1.5px;
            }}
        """)
        layout.addWidget(separator)

        # Volume Card
        self.volume_card = ResultCard(
            title="VOLUME",
            icon_color=COLORS["volume_color"],
            unit="cm³",
            formula="",
            is_area=False
        )
        self.volume_card.setVisible(False)  # Hidden by default for 2D shapes
        layout.addWidget(self.volume_card)

        layout.addStretch()

    def set_results(self, area: Optional[float | str], volume: Optional[float | str], is_3d: bool, shape_name: str = ""):
        """Update the displayed results with animations."""
        self.current_shape_name = shape_name

        # Update area card with fade in if first time
        if not self.area_card.isVisible():
            self.area_card.fade_in()
        self.area_card.set_value(area)

        # Update formula for area
        if shape_name and shape_name in self.SHAPE_FORMULAS:
            area_formula = self.SHAPE_FORMULAS[shape_name].get("area", "")
            if area_formula:
                self.area_card.set_formula(area_formula)

        # Update volume card visibility and value with animation
        if is_3d and not self._volume_visible:
            # Show volume card with animation
            self._volume_visible = True
            self.volume_card.fade_in()
            self.volume_card.set_value(volume)

            # Update formula for volume
            if shape_name and shape_name in self.SHAPE_FORMULAS:
                volume_formula = self.SHAPE_FORMULAS[shape_name].get("volume", "")
                if volume_formula:
                    self.volume_card.set_formula(volume_formula)
        elif not is_3d and self._volume_visible:
            # Hide volume card with animation
            self._volume_visible = False
            self.volume_card.fade_out(on_finished=lambda: self.volume_card.setVisible(False))
            self.volume_card.set_formula("")
        elif is_3d and self._volume_visible:
            # Just update value
            self.volume_card.set_value(volume)

            # Update formula for volume
            if shape_name and shape_name in self.SHAPE_FORMULAS:
                volume_formula = self.SHAPE_FORMULAS[shape_name].get("volume", "")
                if volume_formula:
                    self.volume_card.set_formula(volume_formula)
        else:
            self.volume_card.setVisible(False)
            self.volume_card.set_formula("")


# ============================================================================
# OpenGL 3D Visualization Widget
# ============================================================================

try:
    from OpenGL import GL as gl
    from OpenGL import GLU as glu
    OPENGL_AVAILABLE = True
except ImportError:
    OPENGL_AVAILABLE = False


class GLVisualizationWidget(QWidget):
    """
    OpenGL-based 3D visualization widget with mouse interaction.
    Supports rotation, zoom, pan, and rendering of all 3D geometric shapes.
    Includes smooth camera animations using QPropertyAnimation.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.current_shape: Optional[ShapeConfig] = None
        self.current_values: Dict[str, float] = {}
        self.setMinimumSize(400, 400)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Camera state (animated properties)
        self._camera_distance = 5.0
        self._camera_elevation = 30.0  # degrees
        self._camera_azimuth = 45.0    # degrees
        self._camera_target = [0.0, 0.0, 0.0]

        # Camera animation
        self._camera_anim_group: Optional[QParallelAnimationGroup] = None
        self._animating_camera = False

        # Mouse interaction
        self.last_mouse_pos = None
        self.mouse_mode = None  # 'rotate', 'pan', 'zoom'

        # Rendering options
        self.wireframe_mode = False
        self.show_axes = True
        self.show_grid = True

        # Animation timer for smooth rendering
        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self.update)
        self.anim_timer.start(16)  # ~60 FPS

        # OpenGL widget container
        self.gl_widget = None
        self._setup_gl_widget()

        # Set style
        self.setStyleSheet(f"""
            QWidget {{
                background: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: {RADIUS['lg']};
            }}
        """)

    # Camera properties for QPropertyAnimation
    @pyqtProperty(float)
    def camera_distance(self) -> float:
        return self._camera_distance

    @camera_distance.setter
    def camera_distance(self, value: float):
        self._camera_distance = max(1.0, min(30.0, value))
        if self.gl_widget:
            self.gl_widget.update()

    @pyqtProperty(float)
    def camera_elevation(self) -> float:
        return self._camera_elevation

    @camera_elevation.setter
    def camera_elevation(self, value: float):
        self._camera_elevation = max(-85.0, min(85.0, value))
        if self.gl_widget:
            self.gl_widget.update()

    @pyqtProperty(float)
    def camera_azimuth(self) -> float:
        return self._camera_azimuth

    @camera_azimuth.setter
    def camera_azimuth(self, value: float):
        self._camera_azimuth = value % 360.0
        if self.gl_widget:
            self.gl_widget.update()

    def _setup_gl_widget(self):
        """Create the OpenGL widget."""
        if not OPENGL_AVAILABLE:
            return

        # We'll use a QOpenGLWidget embedded in this widget
        from PyQt6.QtOpenGLWidgets import QOpenGLWidget
        from PyQt6.QtGui import QSurfaceFormat

        # Configure OpenGL surface format
        # Use CompatibilityProfile for better driver compatibility
        # CoreProfile causes crashes when subclassing QOpenGLWidget on some systems
        fmt = QSurfaceFormat()
        fmt.setVersion(3, 3)
        fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CompatibilityProfile)
        fmt.setDepthBufferSize(24)
        fmt.setStencilBufferSize(8)
        fmt.setSamples(4)  # MSAA
        fmt.setSwapBehavior(QSurfaceFormat.SwapBehavior.DoubleBuffer)
        QSurfaceFormat.setDefaultFormat(fmt)

        class GLWidget(QOpenGLWidget):
            def __init__(self, parent_widget):
                super().__init__(parent_widget)
                self.parent_vis = parent_widget
                self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

            def initializeGL(self):
                """Initialize OpenGL context."""
                gl.glClearColor(
                    int(COLORS['bg_secondary'][1:3], 16) / 255.0,
                    int(COLORS['bg_secondary'][3:5], 16) / 255.0,
                    int(COLORS['bg_secondary'][5:7], 16) / 255.0,
                    1.0
                )
                gl.glEnable(gl.GL_DEPTH_TEST)
                gl.glEnable(gl.GL_CULL_FACE)
                gl.glCullFace(gl.GL_BACK)
                gl.glEnable(gl.GL_MULTISAMPLE)
                gl.glEnable(gl.GL_BLEND)
                gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

                # Lighting
                gl.glEnable(gl.GL_LIGHTING)
                gl.glEnable(gl.GL_LIGHT0)
                gl.glLightfv(gl.GL_LIGHT0, gl.GL_POSITION, [5.0, 10.0, 5.0, 1.0])
                gl.glLightfv(gl.GL_LIGHT0, gl.GL_AMBIENT, [0.3, 0.3, 0.3, 1.0])
                gl.glLightfv(gl.GL_LIGHT0, gl.GL_DIFFUSE, [0.8, 0.8, 0.8, 1.0])
                gl.glLightfv(gl.GL_LIGHT0, gl.GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])

                gl.glEnable(gl.GL_COLOR_MATERIAL)
                gl.glColorMaterial(gl.GL_FRONT_AND_BACK, gl.GL_AMBIENT_AND_DIFFUSE)

                # Material properties
                gl.glMaterialfv(gl.GL_FRONT_AND_BACK, gl.GL_SPECULAR, [0.5, 0.5, 0.5, 1.0])
                gl.glMaterialf(gl.GL_FRONT_AND_BACK, gl.GL_SHININESS, 32.0)

                # Fog for depth perception
                gl.glEnable(gl.GL_FOG)
                gl.glFogi(gl.GL_FOG_MODE, gl.GL_LINEAR)
                gl.glFogfv(gl.GL_FOG_COLOR, [
                    int(COLORS['bg_secondary'][1:3], 16) / 255.0,
                    int(COLORS['bg_secondary'][3:5], 16) / 255.0,
                    int(COLORS['bg_secondary'][5:7], 16) / 255.0,
                    1.0
                ])
                gl.glFogf(gl.GL_FOG_START, 2.0)
                gl.glFogf(gl.GL_FOG_END, 20.0)

            def resizeGL(self, w, h):
                """Handle resize."""
                gl.glViewport(0, 0, w, h)
                gl.glMatrixMode(gl.GL_PROJECTION)
                gl.glLoadIdentity()
                aspect = w / h if h > 0 else 1.0
                glu.gluPerspective(45.0, aspect, 0.1, 50.0)
                gl.glMatrixMode(gl.GL_MODELVIEW)

            def paintGL(self):
                """Render the 3D scene."""
                gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
                gl.glLoadIdentity()

                # Calculate camera position from spherical coordinates
                import math
                elev_rad = math.radians(self.parent_vis.camera_elevation)
                azim_rad = math.radians(self.parent_vis.camera_azimuth)
                dist = self.parent_vis.camera_distance

                eye_x = dist * math.cos(elev_rad) * math.sin(azim_rad)
                eye_y = dist * math.sin(elev_rad)
                eye_z = dist * math.cos(elev_rad) * math.cos(azim_rad)

                glu.gluLookAt(
                    eye_x, eye_y, eye_z,
                    self.parent_vis.camera_target[0],
                    self.parent_vis.camera_target[1],
                    self.parent_vis.camera_target[2],
                    0.0, 1.0, 0.0
                )

                # Draw grid
                if self.parent_vis.show_grid:
                    self._draw_grid()

                # Draw axes
                if self.parent_vis.show_axes:
                    self._draw_axes()

                # Set polygon mode
                if self.parent_vis.wireframe_mode:
                    gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)
                else:
                    gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)

                # Draw the shape
                self.parent_vis._draw_3d_shape()

                # Render dimension labels overlay using QPainter
                self._render_dimension_labels_overlay()

            def _render_dimension_labels_overlay(self):
                """Render dimension labels as 2D overlay using QPainter."""
                if not hasattr(self.parent_vis, '_dimension_labels') or not self.parent_vis._dimension_labels:
                    return

                # Use QPainter for text rendering on top of OpenGL
                painter = QPainter(self)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

                # Get font from theme
                from .theme import FONTS, COLORS

                for label_info in self.parent_vis._dimension_labels:
                    x = label_info['x']
                    y = label_info['y']
                    text = label_info['text']
                    color = label_info['color']
                    font_size = label_info['font_size']

                    # Set up font
                    font = QFont(FONTS["mono"])
                    font.setPointSize(font_size)
                    font.setWeight(QFont.Weight.Medium)
                    painter.setFont(font)

                    # Measure text
                    metrics = QFontMetrics(font)
                    text_rect = metrics.boundingRect(text)
                    text_width = text_rect.width()
                    text_height = text_rect.height()

                    # Padding
                    padding_x = 8
                    padding_y = 4

                    # Background rect (centered on label position)
                    bg_rect = QRectF(
                        x - text_width / 2 - padding_x,
                        y - text_height / 2 - padding_y,
                        text_width + 2 * padding_x,
                        text_height + 2 * padding_y
                    )

                    # Convert color tuple to QColor
                    qcolor = QColor(int(color[0] * 255), int(color[1] * 255), int(color[2] * 255))

                    # Draw background with glow effect
                    # Outer glow
                    glow_color = QColor(qcolor)
                    glow_color.setAlpha(60)
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(QBrush(glow_color))
                    painter.drawRoundedRect(bg_rect.adjusted(-8, -8, 8, 8), 8, 8)

                    # Solid background
                    bg_color = QColor(COLORS['bg_tertiary'])
                    bg_color.setAlpha(230)
                    painter.setBrush(QBrush(bg_color))
                    painter.setPen(QPen(qcolor, 1.5))
                    painter.drawRoundedRect(bg_rect, 5, 5)

                    # Draw text
                    painter.setPen(QPen(QColor(COLORS['text_primary']), 1))
                    painter.drawText(
                        int(x - text_width / 2),
                        int(y + text_height / 2 - 1),
                        text
                    )

                painter.end()

                # Clear labels for next frame
                self.parent_vis._dimension_labels.clear()

            def _draw_grid(self):
                """Draw ground grid."""
                gl.glDisable(gl.GL_LIGHTING)
                gl.glLineWidth(1.0)
                gl.glColor4f(0.3, 0.3, 0.4, 0.5)
                gl.glBegin(gl.GL_LINES)
                grid_size = 10
                step = 1.0
                for i in range(-grid_size, grid_size + 1):
                    x = i * step
                    gl.glVertex3f(x, 0, -grid_size * step)
                    gl.glVertex3f(x, 0, grid_size * step)
                    gl.glVertex3f(-grid_size * step, 0, x)
                    gl.glVertex3f(grid_size * step, 0, x)
                gl.glEnd()
                gl.glEnable(gl.GL_LIGHTING)

            def _draw_axes(self):
                """Draw coordinate axes."""
                gl.glDisable(gl.GL_LIGHTING)
                gl.glLineWidth(3.0)
                gl.glBegin(gl.GL_LINES)
                # X axis - Red
                gl.glColor3f(1.0, 0.2, 0.2)
                gl.glVertex3f(0, 0, 0)
                gl.glVertex3f(3, 0, 0)
                # Y axis - Green
                gl.glColor3f(0.2, 1.0, 0.2)
                gl.glVertex3f(0, 0, 0)
                gl.glVertex3f(0, 3, 0)
                # Z axis - Blue
                gl.glColor3f(0.2, 0.2, 1.0)
                gl.glVertex3f(0, 0, 0)
                gl.glVertex3f(0, 0, 3)
                gl.glEnd()
                gl.glEnable(gl.GL_LIGHTING)

            def mousePressEvent(self, event):
                """Handle mouse press."""
                self.parent_vis.last_mouse_pos = event.position()
                if event.button() == Qt.MouseButton.LeftButton:
                    self.parent_vis.mouse_mode = 'rotate'
                elif event.button() == Qt.MouseButton.RightButton:
                    self.parent_vis.mouse_mode = 'pan'
                elif event.button() == Qt.MouseButton.MiddleButton:
                    self.parent_vis.mouse_mode = 'zoom'
                event.accept()

            def mouseMoveEvent(self, event):
                """Handle mouse move for camera control."""
                if self.parent_vis.last_mouse_pos is None:
                    return

                current_pos = event.position()
                dx = current_pos.x() - self.parent_vis.last_mouse_pos.x()
                dy = current_pos.y() - self.parent_vis.last_mouse_pos.y()

                if self.parent_vis.mouse_mode == 'rotate':
                    self.parent_vis.camera_azimuth += dx * 0.5
                    self.parent_vis.camera_elevation = max(-85, min(85, self.parent_vis.camera_elevation - dy * 0.5))
                elif self.parent_vis.mouse_mode == 'pan':
                    # Pan in camera-relative coordinates
                    import math
                    azim_rad = math.radians(self.parent_vis.camera_azimuth)
                    elev_rad = math.radians(self.parent_vis.camera_elevation)
                    right_x = math.cos(azim_rad)
                    right_z = -math.sin(azim_rad)
                    up_x = math.sin(elev_rad) * math.sin(azim_rad)
                    up_y = math.cos(elev_rad)
                    up_z = math.sin(elev_rad) * math.cos(azim_rad)

                    pan_speed = 0.005 * self.parent_vis.camera_distance
                    self.parent_vis.camera_target[0] += dx * pan_speed * right_x + dy * pan_speed * up_x
                    self.parent_vis.camera_target[1] -= dy * pan_speed * up_y
                    self.parent_vis.camera_target[2] += dx * pan_speed * right_z + dy * pan_speed * up_z
                elif self.parent_vis.mouse_mode == 'zoom':
                    self.parent_vis.camera_distance = max(1.0, min(30.0, self.parent_vis.camera_distance + dy * 0.05))

                self.parent_vis.last_mouse_pos = current_pos
                self.update()

            def mouseReleaseEvent(self, event):
                """Handle mouse release."""
                self.parent_vis.last_mouse_pos = None
                self.parent_vis.mouse_mode = None
                event.accept()

            def wheelEvent(self, event):
                """Handle wheel for zoom."""
                delta = event.angleDelta().y()
                self.parent_vis.camera_distance = max(1.0, min(30.0, self.parent_vis.camera_distance - delta * 0.01))
                self.update()

            def keyPressEvent(self, event):
                """Handle keyboard shortcuts."""
                if event.key() == Qt.Key.Key_W:
                    self.parent_vis.wireframe_mode = not self.parent_vis.wireframe_mode
                    self.update()
                elif event.key() == Qt.Key.Key_R:
                    self.parent_vis._reset_camera()
                    self.update()
                elif event.key() == Qt.Key.Key_G:
                    self.parent_vis.show_grid = not self.parent_vis.show_grid
                    self.update()
                elif event.key() == Qt.Key.Key_A:
                    self.parent_vis.show_axes = not self.parent_vis.show_axes
                    self.update()
                event.accept()

        self.gl_widget = GLWidget(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.gl_widget)

    def _reset_camera(self, animated: bool = True):
        """Reset camera to default position with smooth animation."""
        self._animate_camera_to(
            distance=5.0,
            elevation=30.0,
            azimuth=45.0,
            target=[0.0, 0.0, 0.0],
            duration=800 if animated else 0
        )

    def _animate_camera_to(self, distance: float, elevation: float, azimuth: float,
                           target: list, duration: int = 800):
        """Smoothly animate camera to new position using QPropertyAnimation."""
        if duration <= 0:
            self._camera_distance = distance
            self._camera_elevation = elevation
            self._camera_azimuth = azimuth
            self._camera_target = target
            if self.gl_widget:
                self.gl_widget.update()
            return

        # Stop any existing animation
        if self._camera_anim_group:
            self._camera_anim_group.stop()
            self._camera_anim_group.deleteLater()

        self._animating_camera = True

        # Create animations for each camera property
        anim_distance = QPropertyAnimation(self, b"camera_distance")
        anim_distance.setDuration(duration)
        anim_distance.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim_distance.setStartValue(self._camera_distance)
        anim_distance.setEndValue(distance)

        anim_elevation = QPropertyAnimation(self, b"camera_elevation")
        anim_elevation.setDuration(duration)
        anim_elevation.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim_elevation.setStartValue(self._camera_elevation)
        anim_elevation.setEndValue(elevation)

        anim_azimuth = QPropertyAnimation(self, b"camera_azimuth")
        anim_azimuth.setDuration(duration)
        anim_azimuth.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim_azimuth.setStartValue(self._camera_azimuth)
        anim_azimuth.setEndValue(azimuth)

        # Group animations to run in parallel
        self._camera_anim_group = QParallelAnimationGroup()
        self._camera_anim_group.addAnimation(anim_distance)
        self._camera_anim_group.addAnimation(anim_elevation)
        self._camera_anim_group.addAnimation(anim_azimuth)

        def on_finished():
            self._animating_camera = False
            self._camera_target = target
            if self.gl_widget:
                self.gl_widget.update()

        self._camera_anim_group.finished.connect(on_finished)
        self._camera_anim_group.start()

    def set_shape(self, shape_config: ShapeConfig, values: Dict[str, float]):
        """Update the visualization for a new shape with smooth camera transition."""
        self.current_shape = shape_config
        self.current_values = values
        self._reset_camera(animated=True)
        self.update()

    def _draw_3d_shape(self):
        """Draw the current 3D shape using OpenGL."""
        if not self.current_shape:
            return

        # Get color from theme
        primary_r = int(COLORS['primary'][1:3], 16) / 255.0
        primary_g = int(COLORS['primary'][3:5], 16) / 255.0
        primary_b = int(COLORS['primary'][5:7], 16) / 255.0

        secondary_r = int(COLORS['secondary'][1:3], 16) / 255.0
        secondary_g = int(COLORS['secondary'][3:5], 16) / 255.0
        secondary_b = int(COLORS['secondary'][5:7], 16) / 255.0

        gl.glColor4f(primary_r, primary_g, primary_b, 0.8)

        shape_name = self.current_shape.name

        # Draw different 3D shapes
        if shape_name == "cube":
            self._draw_cube()
        elif shape_name == "sphere":
            self._draw_sphere()
        elif shape_name == "cylinder":
            self._draw_cylinder()
        elif shape_name == "cone":
            self._draw_cone()
        elif shape_name == "cone_trunk":
            self._draw_cone_trunk()
        elif shape_name == "pyramid":
            self._draw_pyramid()
        elif shape_name == "pyramid_trunk":
            self._draw_pyramid_trunk()
        elif shape_name == "tetrahedron":
            self._draw_tetrahedron()
        elif shape_name == "octohedron":
            self._draw_octohedron()
        elif shape_name == "dodecahedron":
            self._draw_dodecahedron()
        elif shape_name == "icosahedron":
            self._draw_icosahedron()
        elif shape_name == "rectangular_prism":
            self._draw_rectangular_prism()
        elif shape_name in ("quadrangular_prism", "regular_polygon_prism",
                            "rhomboidal_prism", "triangular_prism", "trapezoidal_prism"):
            self._draw_generic_prism(shape_name)

        # Draw area/volume visual indicators
        self._draw_area_volume_indicators_3d()

        # Draw dimension labels after the shape
        self._draw_dimension_labels_3d()

    def _draw_dimension_labels_3d(self):
        """Draw 3D dimension lines with billboarded text labels for the current shape."""
        if not self.current_shape:
            return

        # Disable lighting for dimension lines
        gl.glDisable(gl.GL_LIGHTING)
        gl.glDisable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glLineWidth(2.0)

        shape_name = self.current_shape.name

        # Color definitions (as RGB 0-1)
        CYAN = (0.0, 0.83, 1.0)     # #00D4FF - radius, primary dimensions
        GREEN = (0.06, 0.73, 0.51)  # #10B981 - height
        ORANGE = (0.96, 0.62, 0.04) # #F59E0B - base
        PURPLE = (0.49, 0.30, 1.0)  # #7C4DFF - diagonals, apothem, slant

        if shape_name == "cube":
            side = self.current_values.get("side", 1.0)
            half = side / 2.0
            # Side length on front-bottom edge
            self._draw_3d_dimension_line(
                half, -half, -half, -half, -half, -half,
                f"side = {side:.1f} cm", ORANGE
            )
        elif shape_name == "sphere":
            radius = self.current_values.get("radius", 1.0)
            # Radius from center to surface on X axis
            self._draw_3d_dimension_line(
                0, 0, 0, radius, 0, 0,
                f"r = {radius:.1f} cm", CYAN
            )
        elif shape_name == "cylinder":
            radius = self.current_values.get("radius", 1.0)
            height = self.current_values.get("height", 2.0)
            half_h = height / 2.0
            # Radius on bottom face
            self._draw_3d_dimension_line(
                0, 0, -half_h, radius, 0, -half_h,
                f"r = {radius:.1f} cm", CYAN
            )
            # Height on right side
            self._draw_3d_dimension_line(
                radius, 0, -half_h, radius, 0, half_h,
                f"h = {height:.1f} cm", GREEN
            )
        elif shape_name == "cone":
            radius = self.current_values.get("radius", 1.0)
            height = self.current_values.get("height", 2.0)
            slant = self.current_values.get("geometry", math.sqrt(radius*radius + height*height))
            half_h = height / 2.0
            # Radius on base
            self._draw_3d_dimension_line(
                0, 0, half_h, radius, 0, half_h,
                f"r = {radius:.1f} cm", CYAN
            )
            # Height from apex to base center
            self._draw_3d_dimension_line(
                0, 0, -half_h, 0, 0, half_h,
                f"h = {height:.1f} cm", GREEN
            )
            # Slant height
            self._draw_3d_dimension_line(
                0, 0, -half_h, radius, 0, half_h,
                f"l = {slant:.1f} cm", PURPLE
            )
        elif shape_name == "cone_trunk":
            r1 = self.current_values.get("sbradius", 0.5)
            r2 = self.current_values.get("lbradius", 1.0)
            height = self.current_values.get("height", 1.5)
            slant = self.current_values.get("geometry", math.sqrt((r2-r1)**2 + height**2))
            half_h = height / 2.0
            # Top radius
            self._draw_3d_dimension_line(
                0, 0, -half_h, r1, 0, -half_h,
                f"r₁ = {r1:.1f} cm", CYAN
            )
            # Bottom radius
            self._draw_3d_dimension_line(
                0, 0, half_h, r2, 0, half_h,
                f"r₂ = {r2:.1f} cm", CYAN
            )
            # Height
            self._draw_3d_dimension_line(
                r2, 0, -half_h, r2, 0, half_h,
                f"h = {height:.1f} cm", GREEN
            )
            # Slant height
            self._draw_3d_dimension_line(
                r1, 0, -half_h, r2, 0, half_h,
                f"l = {slant:.1f} cm", PURPLE
            )
        elif shape_name == "pyramid":
            base = self.current_values.get("base", 1.0)
            height = self.current_values.get("height", 1.5)
            sides = int(self.current_values.get("sidesnumber", 4))
            slant = self.current_values.get("side", math.sqrt((base/2)**2 + height**2))
            half_h = height / 2.0
            apothem = self.current_values.get("apothem", base / (2 * math.tan(math.pi / sides)) if sides > 2 else base / 2)
            # Base side (on front edge of base)
            self._draw_3d_dimension_line(
                -apothem, 0, half_h, apothem, 0, half_h,
                f"base = {base:.1f} cm", ORANGE
            )
            # Height
            self._draw_3d_dimension_line(
                0, 0, -half_h, 0, 0, half_h,
                f"h = {height:.1f} cm", GREEN
            )
            # Slant height
            self._draw_3d_dimension_line(
                0, 0, -half_h, apothem, 0, half_h,
                f"l = {slant:.1f} cm", PURPLE
            )
        elif shape_name == "pyramid_trunk":
            sbside = self.current_values.get("sbside", 1.0)
            lbside = self.current_values.get("lbside", 2.0)
            height = self.current_values.get("height", 1.5)
            latheight = self.current_values.get("latheight", 2.0)
            half_h = height / 2.0
            sb_apothem = self.current_values.get("sbapothem", sbside / (2 * math.tan(math.pi / 4)))
            lb_apothem = self.current_values.get("lbapothem", lbside / (2 * math.tan(math.pi / 4)))
            # Top base side
            self._draw_3d_dimension_line(
                -sb_apothem, 0, -half_h, sb_apothem, 0, -half_h,
                f"base₁ = {sbside:.1f} cm", ORANGE
            )
            # Bottom base side
            self._draw_3d_dimension_line(
                -lb_apothem, 0, half_h, lb_apothem, 0, half_h,
                f"base₂ = {lbside:.1f} cm", ORANGE
            )
            # Height
            self._draw_3d_dimension_line(
                lb_apothem, 0, -half_h, lb_apothem, 0, half_h,
                f"h = {height:.1f} cm", GREEN
            )
            # Lateral height
            self._draw_3d_dimension_line(
                sb_apothem, 0, -half_h, lb_apothem, 0, half_h,
                f"l = {latheight:.1f} cm", PURPLE
            )
        elif shape_name == "tetrahedron":
            side = self.current_values.get("side", 1.0)
            height = self.current_values.get("height", side * math.sqrt(2/3))
            # Edge length
            h = side * math.sqrt(2/3)
            r = side / math.sqrt(3)
            self._draw_3d_dimension_line(
                0, 0, h * 3/4, r, 0, -h/4,
                f"edge = {side:.1f} cm", ORANGE
            )
            # Height
            self._draw_3d_dimension_line(
                0, 0, -h/4, 0, 0, h * 3/4,
                f"h = {height:.1f} cm", GREEN
            )
        elif shape_name == "octohedron":
            side = self.current_values.get("side", 1.0)
            r = side / math.sqrt(2)
            # Edge length
            self._draw_3d_dimension_line(
                0, 0, r, r, 0, 0,
                f"edge = {side:.1f} cm", ORANGE
            )
        elif shape_name in ("dodecahedron", "icosahedron"):
            side = self.current_values.get("side", 1.0)
            # Just show edge length on a representative edge
            radius = side * 1.5  # approximate
            self._draw_3d_dimension_line(
                0, 0, radius, side, 0, radius,
                f"edge = {side:.1f} cm", ORANGE
            )
        elif shape_name == "rectangular_prism":
            side1 = self.current_values.get("side1", 1.0)
            side2 = self.current_values.get("side2", 1.0)
            side3 = self.current_values.get("side3", 1.0)
            hx, hy, hz = side1/2, side2/2, side3/2
            # Length (side1) - front bottom edge
            self._draw_3d_dimension_line(
                -hx, -hy, -hz, hx, -hy, -hz,
                f"length = {side1:.1f} cm", ORANGE
            )
            # Width (side2) - front left edge
            self._draw_3d_dimension_line(
                -hx, -hy, -hz, -hx, hy, -hz,
                f"width = {side2:.1f} cm", ORANGE
            )
            # Depth/Height (side3) - front right edge
            self._draw_3d_dimension_line(
                hx, -hy, -hz, hx, -hy, hz,
                f"depth = {side3:.1f} cm", GREEN
            )
        elif shape_name in ("quadrangular_prism", "regular_polygon_prism",
                            "rhomboidal_prism", "triangular_prism", "trapezoidal_prism"):
            # Generic prism dimensions
            height = self.current_values.get("height", 1.0)
            base = self.current_values.get("base", 1.0)
            # Height
            self._draw_3d_dimension_line(
                1.5, 0, -height/2, 1.5, 0, height/2,
                f"h = {height:.1f} cm", GREEN
            )
            # Base dimension (approximate)
            self._draw_3d_dimension_line(
                0, 0, -height/2, math.sqrt(base) if base > 0 else 1.5, 0, -height/2,
                f"base ≈ {math.sqrt(base):.1f} cm", ORANGE
            )

        # Re-enable depth test and lighting
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_LIGHTING)
        gl.glDisable(gl.GL_BLEND)

    def _draw_3d_dimension_line(self, x1: float, y1: float, z1: float,
                                 x2: float, y2: float, z2: float,
                                 label: str, color: tuple):
        """Draw a 3D dimension line with arrow heads and billboarded label.

        Args:
            x1, y1, z1: Start point
            x2, y2, z2: End point
            label: Text label
            color: (r, g, b) tuple with values 0-1
        """
        # Calculate line vector and length
        dx = x2 - x1
        dy = y2 - y1
        dz = z2 - z1
        length = math.sqrt(dx*dx + dy*dy + dz*dz)

        if length == 0:
            return

        # Unit direction vector
        ux = dx / length
        uy = dy / length
        uz = dz / length

        # Arrow head size (relative to line length)
        arrow_size = min(0.15, length * 0.15)
        # Offset for dimension line (slightly away from shape)
        offset_dist = 0.1

        # For dimension line offset, we need a perpendicular vector
        # Use camera view direction to determine perpendicular
        # Camera position
        import math
        elev_rad = math.radians(self.camera_elevation)
        azim_rad = math.radians(self.camera_azimuth)
        cam_x = math.cos(elev_rad) * math.sin(azim_rad)
        cam_y = math.sin(elev_rad)
        cam_z = math.cos(elev_rad) * math.cos(azim_rad)

        # Perpendicular to both line and camera view
        px = uy * cam_z - uz * cam_y
        py = uz * cam_x - ux * cam_z
        pz = ux * cam_y - uy * cam_x
        plen = math.sqrt(px*px + py*py + pz*pz)
        if plen > 0:
            px, py, pz = px/plen, py/plen, pz/plen

        # Offset points
        ox1, oy1, oz1 = x1 + px * offset_dist, y1 + py * offset_dist, z1 + pz * offset_dist
        ox2, oy2, oz2 = x2 + px * offset_dist, y2 + py * offset_dist, z2 + pz * offset_dist

        # Extension lines (from shape to dimension line)
        ext_len = 0.05
        ex1, ey1, ez1 = x1 - ux * ext_len, y1 - uy * ext_len, z1 - uz * ext_len
        ex2, ey2, ez2 = x2 + ux * ext_len, y2 + uy * ext_len, z2 + uz * ext_len

        # Set color
        gl.glColor4f(color[0], color[1], color[2], 0.9)

        # Draw extension lines (dashed)
        gl.glEnable(gl.GL_LINE_STIPPLE)
        gl.glLineStipple(1, 0xAAAA)
        gl.glBegin(gl.GL_LINES)
        gl.glVertex3f(x1, y1, z1)
        gl.glVertex3f(ex1, ey1, ez1)
        gl.glVertex3f(x2, y2, z2)
        gl.glVertex3f(ex2, ey2, ez2)
        gl.glEnd()
        gl.glDisable(gl.GL_LINE_STIPPLE)

        # Draw dimension line
        gl.glBegin(gl.GL_LINES)
        gl.glVertex3f(ox1, oy1, oz1)
        gl.glVertex3f(ox2, oy2, oz2)
        gl.glEnd()

        # Draw arrow heads
        # Arrow at start
        ax1 = ox1 - ux * arrow_size + px * arrow_size * 0.5
        ay1 = oy1 - uy * arrow_size + py * arrow_size * 0.5
        az1 = oz1 - uz * arrow_size + pz * arrow_size * 0.5
        ax2 = ox1 - ux * arrow_size - px * arrow_size * 0.5
        ay2 = oy1 - uy * arrow_size - py * arrow_size * 0.5
        az2 = oz1 - uz * arrow_size - pz * arrow_size * 0.5

        gl.glBegin(gl.GL_LINES)
        gl.glVertex3f(ox1, oy1, oz1)
        gl.glVertex3f(ax1, ay1, az1)
        gl.glVertex3f(ox1, oy1, oz1)
        gl.glVertex3f(ax2, ay2, az2)
        gl.glEnd()

        # Arrow at end
        bx1 = ox2 + ux * arrow_size + px * arrow_size * 0.5
        by1 = oy2 + uy * arrow_size + py * arrow_size * 0.5
        bz1 = oz2 + uz * arrow_size + pz * arrow_size * 0.5
        bx2 = ox2 + ux * arrow_size - px * arrow_size * 0.5
        by2 = oy2 + uy * arrow_size - py * arrow_size * 0.5
        bz2 = oz2 + uz * arrow_size - pz * arrow_size * 0.5

        gl.glBegin(gl.GL_LINES)
        gl.glVertex3f(ox2, oy2, oz2)
        gl.glVertex3f(bx1, by1, bz1)
        gl.glVertex3f(ox2, oy2, oz2)
        gl.glVertex3f(bx2, by2, bz2)
        gl.glEnd()

        # Draw billboarded label at midpoint
        mid_x = (ox1 + ox2) / 2
        mid_y = (oy1 + oy2) / 2
        mid_z = (oz1 + oz2) / 2

        # Offset label perpendicular to line
        label_offset = 0.15
        label_x = mid_x + px * label_offset
        label_y = mid_y + py * label_offset
        label_z = mid_z + pz * label_offset

        self._draw_billboarded_text(label_x, label_y, label_z, label, color)

    def _draw_billboarded_text(self, x: float, y: float, z: float, text: str, color: tuple):
        """Draw billboarded text that always faces the camera.

        Uses gluProject to convert 3D coordinates to 2D screen coordinates
        for overlay rendering with QPainter.
        """
        # Get current modelview and projection matrices (before any modifications)
        modelview = gl.glGetDoublev(gl.GL_MODELVIEW_MATRIX)
        projection = gl.glGetDoublev(gl.GL_PROJECTION_MATRIX)
        viewport = gl.glGetIntegerv(gl.GL_VIEWPORT)

        # Project 3D point to screen coordinates
        try:
            screen_x, screen_y, screen_z = glu.gluProject(
                x, y, z, modelview, projection, viewport
            )
        except:
            return

        # Convert to widget coordinates (origin at top-left)
        # gluProject returns coordinates with origin at bottom-left
        widget_w = self.gl_widget.width() if self.gl_widget else 400
        widget_h = self.gl_widget.height() if self.gl_widget else 400
        screen_y = widget_h - screen_y  # Flip Y

        # Scale factor based on camera distance for readable text at different zoom levels
        # Base size at camera_distance=5.0
        base_font_size = 11
        scale_factor = 5.0 / max(self.camera_distance, 1.0)
        font_size = max(8, min(18, int(base_font_size * scale_factor)))

        # Store for later rendering in paintGL overlay
        if not hasattr(self, '_dimension_labels'):
            self._dimension_labels = []
        self._dimension_labels.append({
            'x': screen_x,
            'y': screen_y,
            'text': text,
            'color': color,
            'font_size': font_size
        })

    def _draw_area_volume_indicators_3d(self):
        """Draw 3D visual indicators for AREA (surface) and VOLUME (interior)."""
        if not self.current_shape:
            return

        # Color definitions for area/volume
        AREA_COLOR = (0.13, 0.77, 0.37)   # #22C55E - green for area
        VOLUME_COLOR = (0.02, 0.71, 0.83)  # #06B6D4 - cyan for volume

        # Disable lighting for overlay
        gl.glDisable(gl.GL_LIGHTING)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glDisable(gl.GL_DEPTH_TEST)

        shape_name = self.current_shape.name

        if shape_name == "cube":
            side = self.current_values.get("side", 1.0)
            half = side / 2.0
            # Draw VOLUME label at center
            self._draw_billboarded_text(0, 0, 0, "VOLUME", VOLUME_COLOR)
            # Draw AREA labels on face centers (visible faces)
            # Front face
            self._draw_billboarded_text(0, 0, half + 0.15, "AREA", AREA_COLOR)
            # Top face
            self._draw_billboarded_text(0, half + 0.15, 0, "AREA", AREA_COLOR)
            # Right face
            self._draw_billboarded_text(half + 0.15, 0, 0, "AREA", AREA_COLOR)

        elif shape_name == "sphere":
            radius = self.current_values.get("radius", 1.0)
            # VOLUME at center
            self._draw_billboarded_text(0, 0, 0, "VOLUME", VOLUME_COLOR)
            # AREA on surface (front)
            self._draw_billboarded_text(radius + 0.15, 0, 0, "AREA", AREA_COLOR)

        elif shape_name == "cylinder":
            radius = self.current_values.get("radius", 1.0)
            height = self.current_values.get("height", 2.0)
            half_h = height / 2.0
            # VOLUME at center
            self._draw_billboarded_text(0, 0, 0, "VOLUME", VOLUME_COLOR)
            # AREA - curved surface
            self._draw_billboarded_text(radius + 0.15, 0, 0, "AREA", AREA_COLOR)
            # AREA - top face
            self._draw_billboarded_text(0, 0, half_h + 0.15, "AREA", AREA_COLOR)
            # AREA - bottom face
            self._draw_billboarded_text(0, 0, -half_h - 0.15, "AREA", AREA_COLOR)

        elif shape_name == "cone":
            radius = self.current_values.get("radius", 1.0)
            height = self.current_values.get("height", 2.0)
            half_h = height / 2.0
            # VOLUME at centroid (1/4 height from base)
            self._draw_billboarded_text(0, 0, -half_h / 2, "VOLUME", VOLUME_COLOR)
            # AREA - base
            self._draw_billboarded_text(0, 0, half_h + 0.15, "AREA", AREA_COLOR)
            # AREA - lateral surface (side)
            self._draw_billboarded_text(radius + 0.15, 0, 0, "AREA", AREA_COLOR)

        elif shape_name == "cone_trunk":
            r1 = self.current_values.get("sbradius", 0.5)
            r2 = self.current_values.get("lbradius", 1.0)
            height = self.current_values.get("height", 1.5)
            half_h = height / 2.0
            # VOLUME at approximate centroid
            self._draw_billboarded_text(0, 0, 0, "VOLUME", VOLUME_COLOR)
            # AREA - top face
            self._draw_billboarded_text(0, 0, -half_h - 0.15, "AREA", AREA_COLOR)
            # AREA - bottom face
            self._draw_billboarded_text(0, 0, half_h + 0.15, "AREA", AREA_COLOR)
            # AREA - lateral surface
            self._draw_billboarded_text(r2 + 0.15, 0, 0, "AREA", AREA_COLOR)

        elif shape_name in ("pyramid", "pyramid_trunk"):
            height = self.current_values.get("height", 1.5)
            half_h = height / 2.0
            # VOLUME at centroid (1/4 height from base for pyramid)
            self._draw_billboarded_text(0, 0, -half_h / 2, "VOLUME", VOLUME_COLOR)
            # AREA - base
            self._draw_billboarded_text(0, 0, half_h + 0.15, "AREA", AREA_COLOR)
            # AREA - lateral faces
            self._draw_billboarded_text(0, half_h / 2, 0, "AREA", AREA_COLOR)

        elif shape_name == "tetrahedron":
            side = self.current_values.get("side", 1.0)
            h = side * math.sqrt(2/3)
            # VOLUME at centroid
            self._draw_billboarded_text(0, 0, h / 4, "VOLUME", VOLUME_COLOR)
            # AREA on one face
            self._draw_billboarded_text(0, 0, -h / 4 + 0.15, "AREA", AREA_COLOR)

        elif shape_name == "octohedron":
            side = self.current_values.get("side", 1.0)
            r = side / math.sqrt(2)
            # VOLUME at center
            self._draw_billboarded_text(0, 0, 0, "VOLUME", VOLUME_COLOR)
            # AREA on one face
            self._draw_billboarded_text(r / 2, r / 2, r / 2, "AREA", AREA_COLOR)

        elif shape_name in ("dodecahedron", "icosahedron"):
            side = self.current_values.get("side", 1.0)
            radius = side * 1.5
            # VOLUME at center
            self._draw_billboarded_text(0, 0, 0, "VOLUME", VOLUME_COLOR)
            # AREA on surface
            self._draw_billboarded_text(radius + 0.15, 0, 0, "AREA", AREA_COLOR)

        elif shape_name == "rectangular_prism":
            side1 = self.current_values.get("side1", 1.0)
            side2 = self.current_values.get("side2", 1.0)
            side3 = self.current_values.get("side3", 1.0)
            hx, hy, hz = side1/2, side2/2, side3/2
            # VOLUME at center
            self._draw_billboarded_text(0, 0, 0, "VOLUME", VOLUME_COLOR)
            # AREA on three visible faces
            self._draw_billboarded_text(0, 0, hz + 0.15, "AREA", AREA_COLOR)  # front
            self._draw_billboarded_text(0, hy + 0.15, 0, "AREA", AREA_COLOR)  # top
            self._draw_billboarded_text(hx + 0.15, 0, 0, "AREA", AREA_COLOR)  # right

        elif shape_name in ("quadrangular_prism", "regular_polygon_prism",
                            "rhomboidal_prism", "triangular_prism", "trapezoidal_prism"):
            height = self.current_values.get("height", 1.0)
            half_h = height / 2.0
            # VOLUME at center
            self._draw_billboarded_text(0, 0, 0, "VOLUME", VOLUME_COLOR)
            # AREA - top/bottom faces
            self._draw_billboarded_text(0, 0, half_h + 0.15, "AREA", AREA_COLOR)
            self._draw_billboarded_text(0, 0, -half_h - 0.15, "AREA", AREA_COLOR)
            # AREA - lateral surface
            self._draw_billboarded_text(1.5, 0, 0, "AREA", AREA_COLOR)

        # Re-enable depth test and lighting
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_LIGHTING)
        gl.glDisable(gl.GL_BLEND)

    def _draw_cube(self):
        """Draw a cube."""
        side = self.current_values.get("side", 1.0)
        half = side / 2.0
        # 8 vertices of a cube
        vertices = [
            [-half, -half, -half], [half, -half, -half], [half, half, -half], [-half, half, -half],
            [-half, -half, half], [half, -half, half], [half, half, half], [-half, half, half]
        ]
        # 6 faces (each with 4 vertices)
        faces = [
            [0, 1, 2, 3],  # back
            [4, 7, 6, 5],  # front
            [0, 4, 5, 1],  # bottom
            [2, 3, 7, 6],  # top
            [0, 3, 7, 4],  # left
            [1, 2, 6, 5],  # right
        ]
        gl.glBegin(gl.GL_QUADS)
        for face in faces:
            # Calculate face normal
            v0 = vertices[face[0]]
            v1 = vertices[face[1]]
            v2 = vertices[face[2]]
            nx = (v1[1] - v0[1]) * (v2[2] - v0[2]) - (v1[2] - v0[2]) * (v2[1] - v0[1])
            ny = (v1[2] - v0[2]) * (v2[0] - v0[0]) - (v1[0] - v0[0]) * (v2[2] - v0[2])
            nz = (v1[0] - v0[0]) * (v2[1] - v0[1]) - (v1[1] - v0[1]) * (v2[0] - v0[0])
            length = math.sqrt(nx*nx + ny*ny + nz*nz)
            if length > 0:
                nx, ny, nz = nx/length, ny/length, nz/length
            gl.glNormal3f(nx, ny, nz)
            for idx in face:
                gl.glVertex3fv(vertices[idx])
        gl.glEnd()

    def _draw_sphere(self):
        """Draw a sphere using quadric."""
        radius = self.current_values.get("radius", 1.0)
        quadric = glu.gluNewQuadric()
        glu.gluQuadricNormals(quadric, glu.GLU_SMOOTH)
        glu.gluQuadricTexture(quadric, gl.GL_TRUE)
        glu.gluSphere(quadric, radius, 32, 32)
        glu.gluDeleteQuadric(quadric)

    def _draw_cylinder(self):
        """Draw a cylinder."""
        radius = self.current_values.get("radius", 1.0)
        height = self.current_values.get("height", 2.0)
        half_h = height / 2.0
        quadric = glu.gluNewQuadric()
        glu.gluQuadricNormals(quadric, glu.GLU_SMOOTH)
        # Draw cylinder body
        glu.gluCylinder(quadric, radius, radius, height, 32, 4)
        # Draw top cap
        gl.glPushMatrix()
        gl.glTranslatef(0, 0, half_h)
        glu.gluDisk(quadric, 0, radius, 32, 1)
        gl.glPopMatrix()
        # Draw bottom cap
        gl.glPushMatrix()
        gl.glTranslatef(0, 0, -half_h)
        gl.glRotatef(180, 1, 0, 0)
        glu.gluDisk(quadric, 0, radius, 32, 1)
        gl.glPopMatrix()
        glu.gluDeleteQuadric(quadric)

    def _draw_cone(self):
        """Draw a cone."""
        radius = self.current_values.get("radius", 1.0)
        height = self.current_values.get("height", 2.0)
        # Try to get slant height, otherwise calculate
        slant = self.current_values.get("geometry", math.sqrt(radius*radius + height*height))
        half_h = height / 2.0
        quadric = glu.gluNewQuadric()
        glu.gluQuadricNormals(quadric, glu.GLU_SMOOTH)
        # Draw cone body
        gl.glPushMatrix()
        gl.glTranslatef(0, 0, -half_h)
        glu.gluCylinder(quadric, radius, 0, height, 32, 4)
        # Draw base cap
        gl.glPushMatrix()
        gl.glTranslatef(0, 0, height)
        gl.glRotatef(180, 1, 0, 0)
        glu.gluDisk(quadric, 0, radius, 32, 1)
        gl.glPopMatrix()
        gl.glPopMatrix()
        glu.gluDeleteQuadric(quadric)

    def _draw_cone_trunk(self):
        """Draw a cone frustum (truncated cone)."""
        r1 = self.current_values.get("sbradius", 0.5)
        r2 = self.current_values.get("lbradius", 1.0)
        height = self.current_values.get("height", 1.5)
        half_h = height / 2.0
        quadric = glu.gluNewQuadric()
        glu.gluQuadricNormals(quadric, glu.GLU_SMOOTH)
        # Draw frustum body
        gl.glPushMatrix()
        gl.glTranslatef(0, 0, -half_h)
        glu.gluCylinder(quadric, r2, r1, height, 32, 4)
        # Draw bottom cap
        gl.glPushMatrix()
        gl.glTranslatef(0, 0, height)
        gl.glRotatef(180, 1, 0, 0)
        glu.gluDisk(quadric, 0, r2, 32, 1)
        gl.glPopMatrix()
        # Draw top cap
        gl.glPushMatrix()
        gl.glTranslatef(0, 0, 0)
        glu.gluDisk(quadric, 0, r1, 32, 1)
        gl.glPopMatrix()
        gl.glPopMatrix()
        glu.gluDeleteQuadric(quadric)

    def _draw_pyramid(self):
        """Draw a regular pyramid."""
        base = self.current_values.get("base", 1.0)
        height = self.current_values.get("height", 1.5)
        sides = int(self.current_values.get("sidesnumber", 4))
        half_h = height / 2.0
        apothem = self.current_values.get("apothem", base / (2 * math.tan(math.pi / sides)) if sides > 2 else base / 2)

        # Draw base
        gl.glBegin(gl.GL_POLYGON)
        gl.glNormal3f(0, 0, -1)
        for i in range(sides):
            angle = 2 * math.pi * i / sides
            x = apothem * math.cos(angle)
            y = apothem * math.sin(angle)
            gl.glVertex3f(x, y, -half_h)
        gl.glEnd()

        # Draw side faces
        gl.glBegin(gl.GL_TRIANGLES)
        for i in range(sides):
            angle1 = 2 * math.pi * i / sides
            angle2 = 2 * math.pi * (i + 1) / sides
            x1 = apothem * math.cos(angle1)
            y1 = apothem * math.sin(angle1)
            x2 = apothem * math.cos(angle2)
            y2 = apothem * math.sin(angle2)

            # Normal for this face
            v1 = [x1, y1, -half_h]
            v2 = [x2, y2, -half_h]
            v3 = [0, 0, half_h]
            # Calculate normal
            ux = v2[0] - v1[0]; uy = v2[1] - v1[1]; uz = v2[2] - v1[2]
            vx = v3[0] - v1[0]; vy = v3[1] - v1[1]; vz = v3[2] - v1[2]
            nx = uy * vz - uz * vy
            ny = uz * vx - ux * vz
            nz = ux * vy - uy * vx
            length = math.sqrt(nx*nx + ny*ny + nz*nz)
            if length > 0:
                nx, ny, nz = nx/length, ny/length, nz/length

            gl.glNormal3f(nx, ny, nz)
            gl.glVertex3f(x1, y1, -half_h)
            gl.glVertex3f(x2, y2, -half_h)
            gl.glVertex3f(0, 0, half_h)
        gl.glEnd()

    def _draw_pyramid_trunk(self):
        """Draw a pyramid frustum."""
        # Simplified - draw as two pyramids
        self._draw_pyramid()

    def _draw_tetrahedron(self):
        """Draw a regular tetrahedron."""
        side = self.current_values.get("side", 1.0)
        # Vertices of a regular tetrahedron
        h = side * math.sqrt(2/3)
        r = side / math.sqrt(3)
        vertices = [
            [0, 0, h * 3/4],
            [r, 0, -h/4],
            [-r/2, r*math.sqrt(3)/2, -h/4],
            [-r/2, -r*math.sqrt(3)/2, -h/4]
        ]
        faces = [[0, 1, 2], [0, 2, 3], [0, 3, 1], [1, 3, 2]]
        gl.glBegin(gl.GL_TRIANGLES)
        for face in faces:
            v0 = vertices[face[0]]
            v1 = vertices[face[1]]
            v2 = vertices[face[2]]
            # Normal
            ux = v1[0] - v0[0]; uy = v1[1] - v0[1]; uz = v1[2] - v0[2]
            vx = v2[0] - v0[0]; vy = v2[1] - v0[1]; vz = v2[2] - v0[2]
            nx = uy * vz - uz * vy
            ny = uz * vx - ux * vz
            nz = ux * vy - uy * vx
            length = math.sqrt(nx*nx + ny*ny + nz*nz)
            if length > 0:
                nx, ny, nz = nx/length, ny/length, nz/length
            gl.glNormal3f(nx, ny, nz)
            gl.glVertex3fv(v0)
            gl.glVertex3fv(v1)
            gl.glVertex3fv(v2)
        gl.glEnd()

    def _draw_octohedron(self):
        """Draw a regular octahedron."""
        side = self.current_values.get("side", 1.0)
        r = side / math.sqrt(2)
        vertices = [
            [0, 0, r], [0, 0, -r],
            [r, 0, 0], [-r, 0, 0],
            [0, r, 0], [0, -r, 0]
        ]
        faces = [
            [0, 2, 4], [0, 4, 3], [0, 3, 5], [0, 5, 2],
            [1, 4, 2], [1, 3, 4], [1, 5, 3], [1, 2, 5]
        ]
        gl.glBegin(gl.GL_TRIANGLES)
        for face in faces:
            v0 = vertices[face[0]]
            v1 = vertices[face[1]]
            v2 = vertices[face[2]]
            ux = v1[0] - v0[0]; uy = v1[1] - v0[1]; uz = v1[2] - v0[2]
            vx = v2[0] - v0[0]; vy = v2[1] - v0[1]; vz = v2[2] - v0[2]
            nx = uy * vz - uz * vy
            ny = uz * vx - ux * vz
            nz = ux * vy - uy * vx
            length = math.sqrt(nx*nx + ny*ny + nz*nz)
            if length > 0:
                nx, ny, nz = nx/length, ny/length, nz/length
            gl.glNormal3f(nx, ny, nz)
            gl.glVertex3fv(v0)
            gl.glVertex3fv(v1)
            gl.glVertex3fv(v2)
        gl.glEnd()

    def _draw_dodecahedron(self):
        """Draw a regular dodecahedron."""
        # Simplified - draw as sphere
        self._draw_sphere()

    def _draw_icosahedron(self):
        """Draw a regular icosahedron."""
        # Simplified - draw as sphere
        self._draw_sphere()

    def _draw_rectangular_prism(self):
        """Draw a rectangular prism (box)."""
        side1 = self.current_values.get("side1", 1.0)
        side2 = self.current_values.get("side2", 1.0)
        side3 = self.current_values.get("side3", 1.0)
        hx, hy, hz = side1/2, side2/2, side3/2
        # Similar to cube but with different dimensions
        vertices = [
            [-hx, -hy, -hz], [hx, -hy, -hz], [hx, hy, -hz], [-hx, hy, -hz],
            [-hx, -hy, hz], [hx, -hy, hz], [hx, hy, hz], [-hx, hy, hz]
        ]
        faces = [
            [0, 1, 2, 3], [4, 7, 6, 5], [0, 4, 5, 1],
            [2, 3, 7, 6], [0, 3, 7, 4], [1, 2, 6, 5]
        ]
        gl.glBegin(gl.GL_QUADS)
        for face in faces:
            v0 = vertices[face[0]]
            v1 = vertices[face[1]]
            v2 = vertices[face[2]]
            nx = (v1[1] - v0[1]) * (v2[2] - v0[2]) - (v1[2] - v0[2]) * (v2[1] - v0[1])
            ny = (v1[2] - v0[2]) * (v2[0] - v0[0]) - (v1[0] - v0[0]) * (v2[2] - v0[2])
            nz = (v1[0] - v0[0]) * (v2[1] - v0[1]) - (v1[1] - v0[1]) * (v2[0] - v0[0])
            length = math.sqrt(nx*nx + ny*ny + nz*nz)
            if length > 0:
                nx, ny, nz = nx/length, ny/length, nz/length
            gl.glNormal3f(nx, ny, nz)
            for idx in face:
                gl.glVertex3fv(vertices[idx])
        gl.glEnd()

    def _draw_generic_prism(self, shape_name: str):
        """Draw a generic prism (simplified as cylinder)."""
        self._draw_cylinder()


