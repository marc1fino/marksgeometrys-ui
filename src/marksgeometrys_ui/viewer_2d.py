"""A responsive, animated drafting canvas for the eight plane figures."""

import math
from typing import Dict, Optional

from PyQt6.QtCore import QEasingCurve, QPointF, QPropertyAnimation, QRectF, Qt, pyqtProperty
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPolygonF,
    QRadialGradient,
)
from PyQt6.QtWidgets import QSizePolicy, QWidget

from .shapes import ShapeConfig
from .typography import FONTS, load_fonts


BLUE = QColor("#2764ef")
CYAN = QColor("#00afc8")
INK = QColor("#60718b")


class ShapeVisualizationWidget(QWidget):
    """Crisp vector geometry with dimensions, animated edits and a pan/zoom camera."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        load_fonts()
        self.current_shape: Optional[ShapeConfig] = None
        self.current_values: Dict[str, float] = {}
        self.unit = "cm"
        self._from_values: Dict[str, float] = {}
        self._transition = 1.0
        self._zoom = 1.0
        self._pan = QPointF()
        self._drag_position = None
        self._grid_visible = True
        self._dimensions_visible = True
        self._animations_enabled = True
        self._appearance = False
        self._measurement_mode = "dimensions"
        self._animation = QPropertyAnimation(self, b"transition", self)
        self._animation.setDuration(360)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.setMinimumSize(240, 200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setToolTip("Drag to pan · Scroll to zoom · Double-click to fit")

    def _get_transition(self):
        return self._transition

    def _set_transition(self, value):
        self._transition = float(value)
        self.update()

    transition = pyqtProperty(float, _get_transition, _set_transition)

    def _display_values(self):
        return {
            name: self._from_values.get(name, value)
            + (value - self._from_values.get(name, value)) * self._transition
            for name, value in self.current_values.items()
        }

    def set_shape(self, shape_config: ShapeConfig, values: Dict[str, float]):
        """Update a figure without restarting the camera during parameter edits."""
        same_shape = self.current_shape is not None and self.current_shape.name == shape_config.name
        if same_shape and values == self.current_values:
            return
        self._from_values = self._display_values() if same_shape else dict(values)
        self._animation.stop()
        self.current_shape = shape_config
        self.current_values = dict(values)
        self._appearance = not same_shape
        if not same_shape:
            self._zoom = 1.0
            self._pan = QPointF()
        if self.isVisible() and self._animations_enabled:
            self._animation.setStartValue(0.0)
            self._animation.setEndValue(1.0)
            self._animation.start()
        else:
            self._transition = 1.0
        self.update()

    def reset_view(self):
        self._zoom = 1.0
        self._pan = QPointF()
        self.update()

    def zoom_in(self):
        self._zoom = min(4.0, self._zoom * 1.15)
        self.update()

    def zoom_out(self):
        self._zoom = max(0.3, self._zoom / 1.15)
        self.update()

    def set_grid_visible(self, visible: bool):
        self._grid_visible = bool(visible)
        self.update()

    def set_dimensions_visible(self, visible: bool):
        self._dimensions_visible = bool(visible)
        self.update()

    def set_unit(self, unit: str):
        """Relabel the existing geometry without converting or resetting it."""
        if not isinstance(unit, str) or not unit.strip():
            raise ValueError("A non-empty measurement unit is required.")
        self.unit = unit.strip()
        self.update()

    def set_measurement_mode(self, mode: str):
        """Switch between dimension annotations and visual measurement examples."""
        if mode not in ("dimensions", "area", "volume"):
            raise ValueError("Unknown measurement mode: " + mode)
        self._measurement_mode = mode
        self.update()

    @property
    def measurement_mode(self) -> str:
        """The active measurement overlay, shared with the 3D viewer API."""
        return self._measurement_mode

    def set_animations_enabled(self, enabled: bool):
        """Finish any transition immediately when reduced motion is requested."""
        self._animations_enabled = bool(enabled)
        if not self._animations_enabled:
            self._animation.stop()
            self._transition = 1.0
            self.update()

    def wheelEvent(self, event):
        if event.angleDelta().y():
            factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
            self._zoom = max(0.3, min(4.0, self._zoom * factor))
            self.update()
            event.accept()
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_position = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_position is not None:
            self._pan += event.position() - self._drag_position
            self._drag_position = event.position()
            self.update()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_position = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.reset_view()
        event.accept()

    def hideEvent(self, event):
        self._animation.stop()
        self._transition = 1.0
        self._drag_position = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().hideEvent(event)

    @staticmethod
    def _font(size, mono=False):
        font = QFont(FONTS["primary"])
        font.setPixelSize(size)
        return font

    def _geometry(self, values):
        """Return world coordinates; physical aspect ratios survive viewport resizing."""
        name = self.current_shape.name
        get = lambda key, default=1.0: max(0.001, float(values.get(key, default)))
        if name == "circle":
            radius = get("radius")
            return [], QRectF(-radius, -radius, 2 * radius, 2 * radius)
        if name in ("square", "rectangle"):
            width = get("side") if name == "square" else get("base")
            height = width if name == "square" else get("height")
            points = [(-width / 2, -height / 2), (width / 2, -height / 2),
                      (width / 2, height / 2), (-width / 2, height / 2)]
        elif name == "triangle":
            width, height = get("base"), get("height")
            points = [(0.0, -height / 2), (width / 2, height / 2),
                      (-width / 2, height / 2)]
        elif name == "rhombus":
            width, height = get("largediagonal"), get("smalldiagonal")
            points = [(0.0, -height / 2), (width / 2, 0.0),
                      (0.0, height / 2), (-width / 2, 0.0)]
        elif name == "parallelogram":
            width, height = get("base"), get("height")
            skew = width * 0.25
            points = [(-width / 2 + skew, -height / 2),
                      (width / 2 + skew, -height / 2),
                      (width / 2 - skew, height / 2),
                      (-width / 2 - skew, height / 2)]
        elif name == "trapezoid":
            lower, upper, height = get("largebase"), get("smallbase"), get("height")
            points = [(-upper / 2, -height / 2), (upper / 2, -height / 2),
                      (lower / 2, height / 2), (-lower / 2, height / 2)]
        else:
            sides = max(3, round(get("sidesnumber", 6)))
            radius = get("side") / (2 * math.sin(math.pi / sides))
            # Above 512 sides the outline is visually indistinguishable at screen resolution.
            samples = min(sides, 512)
            angle_offset = math.pi / 2 + math.pi / sides
            points = [(radius * math.cos(angle_offset + i * math.tau / samples),
                       radius * math.sin(angle_offset + i * math.tau / samples))
                      for i in range(samples)]
        polygon = [QPointF(x, y) for x, y in points]
        return polygon, QPolygonF(polygon).boundingRect()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)
        background = QLinearGradient(0, 0, 0, self.height())
        background.setColorAt(0, QColor("#ffffff"))
        background.setColorAt(.12, QColor("#ffffff"))
        background.setColorAt(1, QColor("#f4f8ff"))
        painter.fillRect(self.rect(), background)
        center = QPointF(self.width() / 2, self.height() / 2 - 4) + self._pan
        halo = QRadialGradient(center, max(self.width(), self.height()) * .42)
        halo.setColorAt(0, QColor(220, 237, 255, 115))
        halo.setColorAt(.55, QColor(242, 248, 255, 65))
        halo.setColorAt(1, QColor(255, 255, 255, 0))
        painter.fillRect(self.rect(), QBrush(halo))
        if self._grid_visible:
            self._draw_grid(painter, center)
        if self.current_shape is None:
            painter.setFont(self._font(13))
            painter.setPen(INK)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Select a shape")
            painter.end()
            return

        values = self._display_values()
        points, world_bounds = self._geometry(values)
        margin_x = 104 if self.width() > 420 else 70
        if self.current_shape.name == "circle":
            margin_y = 40 if self.height() > 300 else 36
        elif self.current_shape.name == "regular_polygon":
            margin_y = 64
        else:
            margin_y = 80 if self.height() > 300 else 64
        available_w = max(32.0, self.width() - 2 * margin_x)
        available_h = max(32.0, self.height() - 2 * margin_y)
        scale = min(available_w / max(world_bounds.width(), 0.001),
                    available_h / max(world_bounds.height(), 0.001)) * self._zoom
        if self._appearance:
            scale *= 0.9 + 0.1 * self._transition
        world_center = world_bounds.center()

        def project(point):
            return center + (point - world_center) * scale

        path = QPainterPath()
        if self.current_shape.name == "circle":
            radius = world_bounds.width() * scale / 2
            shape_bounds = QRectF(center.x() - radius, center.y() - radius, 2 * radius, 2 * radius)
            path.addEllipse(shape_bounds)
            screen_points = []
        else:
            screen_points = [project(point) for point in points]
            path.addPolygon(QPolygonF(screen_points))
            path.closeSubpath()
            shape_bounds = path.boundingRect()

        painter.save()
        if self._appearance:
            painter.setOpacity(0.5 + 0.5 * self._transition)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for width, alpha in ((10, 3), (6, 7)):
            painter.setPen(QPen(QColor(39, 100, 239, alpha), width))
            painter.drawPath(path)
        fill = QLinearGradient(shape_bounds.topLeft(), shape_bounds.bottomRight())
        fill.setColorAt(0, QColor(65, 115, 255, 55 if self._measurement_mode == "area" else 38))
        fill.setColorAt(.5, QColor(105, 164, 255, 32 if self._measurement_mode == "area" else 22))
        fill.setColorAt(1, QColor(0, 184, 205, 50 if self._measurement_mode == "area" else 34))
        painter.setBrush(QBrush(fill))
        painter.setPen(QPen(BLUE, 2.1, Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.drawPath(path)
        if self._measurement_mode == "area":
            self._draw_area(painter, path, shape_bounds, project(QPointF()), scale)
        painter.setBrush(QColor("#ffffff"))
        painter.setPen(QPen(BLUE, 1.6))
        if len(screen_points) <= 24 and self._measurement_mode == "dimensions":
            for point in screen_points:
                painter.drawEllipse(point, 3.3, 3.3)
        if self._dimensions_visible and self._measurement_mode == "dimensions":
            dimension_center = project(QPointF()) if self.current_shape.name == "regular_polygon" else center
            self._draw_dimensions(painter, values, shape_bounds, dimension_center, screen_points, scale)
        painter.restore()
        if self._measurement_mode == "volume":
            self._draw_volume_example(painter)
        painter.end()

    def _draw_grid(self, painter, center):
        spacing = max(12.0, min(54.0, 26.0 * self._zoom))
        painter.setPen(QPen(QColor("#dfe8f6"), 1.3, Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap))
        start_x = center.x() % spacing
        start_y = center.y() % spacing
        x = start_x
        while x < self.width():
            y = start_y
            while y < self.height():
                painter.drawPoint(QPointF(x, y))
                y += spacing
            x += spacing

    def _draw_area(self, painter, path, bounds, origin, scale):
        """A clipped unit grid shows surface coverage without calculating its area."""
        step = max(1, math.ceil(16 / max(scale, 0.001)))
        spacing = step * scale
        painter.save()
        painter.setClipPath(path)
        painter.setPen(QPen(QColor(32, 40, 255, 70), 0.7))
        start_x = origin.x() + math.floor((bounds.left() - origin.x()) / spacing) * spacing
        start_y = origin.y() + math.floor((bounds.top() - origin.y()) / spacing) * spacing
        for index in range(min(256, math.ceil(bounds.width() / spacing) + 2)):
            x = start_x + index * spacing
            painter.drawLine(QPointF(x, bounds.top()), QPointF(x, bounds.bottom()))
        for index in range(min(256, math.ceil(bounds.height() / spacing) + 2)):
            y = start_y + index * spacing
            painter.drawLine(QPointF(bounds.left(), y), QPointF(bounds.right(), y))
        painter.restore()
        self._pill(painter, bounds.center(), "A", BLUE)
        painter.setFont(self._font(11))
        painter.setPen(INK)
        painter.drawText(QRectF(12, self.height() - 26, self.width() - 24, 18),
                         Qt.AlignmentFlag.AlignCenter, f"Grid: {step} {self.unit} × {step} {self.unit}")

    def _draw_volume_example(self, painter):
        """A unit cube illustrates the third dimension absent from a plane figure."""
        size = min(42.0, self.height() * 0.18)
        offset = size * 0.4
        origin = QPointF(self.width() - size - offset - 28, self.height() - size - 42)
        a = origin
        b = a + QPointF(size, 0)
        c = a + QPointF(size, size)
        d = a + QPointF(0, size)
        depth = QPointF(offset, -offset)
        painter.setPen(QPen(BLUE, 1.0))
        painter.setBrush(QColor(32, 40, 255, 13))
        painter.drawPolygon(QPolygonF([a, b, b + depth, a + depth]))
        painter.setBrush(QColor(32, 40, 255, 28))
        painter.drawPolygon(QPolygonF([b, c, c + depth, b + depth]))
        painter.setBrush(QColor(32, 40, 255, 7))
        painter.drawPolygon(QPolygonF([a, b, c, d]))
        painter.setPen(QPen(QColor(32, 40, 255, 80), 0.6))
        for index in (1, 2):
            y = size * index / 3
            painter.drawLine(a + QPointF(0, y), b + QPointF(0, y))
            painter.drawLine(b + QPointF(0, y), b + depth + QPointF(0, y))
        painter.setFont(self._font(11))
        painter.setPen(BLUE)
        painter.drawText(QRectF(origin.x() - 8, origin.y() + size + 6, size + offset + 16, 18),
                         Qt.AlignmentFlag.AlignCenter, f"1 {self.unit}³")
        painter.setPen(INK)
        painter.drawText(QPointF(18, self.height() - 16), "2D · no volume")

    @staticmethod
    def _number(value):
        return f"{value:,.2f}".rstrip("0").rstrip(".")

    def _draw_dimensions(self, painter, values, bounds, center, points, scale):
        name = self.current_shape.name
        value = lambda key: float(values.get(key, 1.0))
        text = lambda prefix, key: f"{prefix} {self._number(value(key))} {self.unit}"
        left, right = bounds.left(), bounds.right()
        top, bottom = bounds.top(), bounds.bottom()
        if name == "circle":
            radius = bounds.width() / 2
            end = center + QPointF(radius * 0.866, -radius * 0.5)
            self._measure(painter, center, end, text("r =", "radius"), 0, BLUE)
            painter.setPen(QPen(BLUE, 1.2))
            painter.setBrush(QColor("#ffffff"))
            painter.drawEllipse(center, 3, 3)
        elif name == "square":
            self._measure(painter, QPointF(left, bottom), QPointF(right, bottom),
                          text("l =", "side"), 29, BLUE)
        elif name in ("rectangle", "triangle", "parallelogram", "trapezoid"):
            if name == "parallelogram":
                base_left, base_right = points[3], points[2]
            else:
                base_left, base_right = QPointF(left, bottom), QPointF(right, bottom)
            base_key = "largebase" if name == "trapezoid" else "base"
            self._measure(painter, base_left, base_right,
                          text("B =" if name == "trapezoid" else "b =", base_key), 29, BLUE)
            self._measure(painter, QPointF(right, top), QPointF(right, bottom),
                          text("h =", "height"), -27, CYAN)
            if name == "triangle":
                self._construction(painter, points[0], QPointF(points[0].x(), bottom))
            elif name == "trapezoid":
                self._measure(painter, points[0], points[1], text("b =", "smallbase"), -27, CYAN)
        elif name == "rhombus":
            self._construction(painter, QPointF(left, center.y()), QPointF(right, center.y()))
            self._construction(painter, QPointF(center.x(), top), QPointF(center.x(), bottom))
            self._measure(painter, QPointF(left, bottom), QPointF(right, bottom),
                          text("D =", "largediagonal"), 29, BLUE)
            self._measure(painter, QPointF(right, top), QPointF(right, bottom),
                          text("d =", "smalldiagonal"), -27, CYAN)
        elif name == "regular_polygon":
            # A base edge supplies an uncluttered, physically accurate apothem.
            sides = max(3, round(value("sidesnumber")))
            apothem = value("side") / (2 * math.tan(math.pi / sides))
            edge = max(((a, b) for a, b in zip(points, points[1:] + points[:1])),
                       key=lambda pair: (pair[0].y() + pair[1].y()) / 2)
            midpoint = (edge[0] + edge[1]) / 2
            self._construction(painter, center, midpoint)
            self._pill(painter, (center + midpoint) / 2 + QPointF(22, 0),
                       f"a = {self._number(apothem)} {self.unit}", CYAN)
            self._measure(painter, edge[1], edge[0], text("l =", "side"), 26, BLUE)

    def _construction(self, painter, start, end):
        pen = QPen(QColor(9, 168, 197, 140), 1.1, Qt.PenStyle.DashLine)
        pen.setDashPattern([4, 4])
        painter.setPen(pen)
        painter.drawLine(start, end)

    def _measure(self, painter, start, end, label, offset, color):
        delta = end - start
        length = math.hypot(delta.x(), delta.y())
        if length < 1:
            return
        direction = delta / length
        normal = QPointF(-direction.y(), direction.x())
        shift = normal * offset
        a, b = start + shift, end + shift
        if abs(offset) > 0.1:
            painter.setPen(QPen(QColor(151, 171, 204, 140), 0.8))
            painter.drawLine(start + normal * (4 if offset > 0 else -4),
                             a + normal * (5 if offset > 0 else -5))
            painter.drawLine(end + normal * (4 if offset > 0 else -4),
                             b + normal * (5 if offset > 0 else -5))
        painter.setPen(QPen(color, 1.0))
        painter.drawLine(a, b)
        # Small inward arrowheads remain crisp even at compact viewport sizes.
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        size = min(5.5, length / 5)
        for point, sign in [(a, 1), (b, -1)]:
            back = point + direction * size * sign
            painter.drawPolygon(QPolygonF([point, back + normal * 2.5, back - normal * 2.5]))
        label_center = (a + b) / 2
        if abs(delta.y()) > abs(delta.x()) * 2:
            label_center += normal * (-27 if offset < 0 else 27)
        elif offset < 0:
            label_center += normal * -15
        else:
            label_center += normal * 15
        self._pill(painter, label_center, label, color)

    def _pill(self, painter, center, text, color):
        painter.setFont(self._font(11, mono=True))
        metrics = painter.fontMetrics()
        width = min(self.width() - 16, metrics.horizontalAdvance(text) + 18)
        height = 24
        # Labels stay legible when a zoomed figure extends beyond the canvas.
        x = max(8.0, min(self.width() - width - 8.0, center.x() - width / 2))
        y = max(32.0, min(self.height() - height - 14.0, center.y() - height / 2))
        rect = QRectF(x, y, width, height)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 242))
        painter.drawRoundedRect(rect, 6, 6)
        painter.setPen(color)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
