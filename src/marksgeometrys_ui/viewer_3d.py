"""Interactive, driver-independent 3D geometry viewport.

Faces are projected from actual meshes and depth sorted before painting.  Keeping
the renderer in Qt makes the viewport usable on machines without OpenGL drivers,
including remote desktops and the offscreen platform used by the UI tests.
"""

import itertools
import math
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

from PyQt6.QtCore import QEasingCurve, QElapsedTimer, QPointF, QRectF, Qt, QTimer, QVariantAnimation
from PyQt6.QtGui import QBrush, QColor, QFont, QLinearGradient, QPainter, QPen, QPolygonF, QRadialGradient
from PyQt6.QtWidgets import QSizePolicy, QWidget

from .shapes import ShapeConfig
from .symbols import parameter_symbol
from .typography import FONTS, load_fonts

Vector = Tuple[float, float, float]

BLUE = QColor("#2764EF")


def _sub(a: Vector, b: Vector) -> Vector:
    return tuple(x - y for x, y in zip(a, b))


def _cross(a: Vector, b: Vector) -> Vector:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _dot(a: Vector, b: Vector) -> float:
    return sum(x * y for x, y in zip(a, b))


def _normal(v: Vector) -> Vector:
    length = math.sqrt(_dot(v, v))
    return tuple(x / (length or 1.0) for x in v)


@dataclass
class Mesh:
    """A closed polygon mesh, with optional sparse construction lines."""

    vertices: List[Vector]
    faces: List[Tuple[int, ...]]
    curved: bool = False


@dataclass
class DimensionSegment:
    """An actual model-space measurement, independent of the camera."""

    start: Vector
    end: Vector
    symbol: str
    title: str
    dashed: bool = False

    @property
    def length(self) -> float:
        return math.sqrt(_dot(_sub(self.end, self.start), _sub(self.end, self.start)))


def _extrude(bottom: List[Tuple[float, float]], height: float,
             top: Optional[List[Tuple[float, float]]] = None) -> Mesh:
    top = bottom if top is None else top
    count = len(bottom)
    vertices = [(x, -height / 2, z) for x, z in bottom]
    if len(top) == 1:
        vertices.append((top[0][0], height / 2, top[0][1]))
        faces = [tuple(range(count))]
        faces.extend((i, (i + 1) % count, count) for i in range(count))
    else:
        vertices.extend((x, height / 2, z) for x, z in top)
        faces = [tuple(range(count)), tuple(range(count, count * 2))]
        faces.extend((i, (i + 1) % count, (i + 1) % count + count, i + count)
                     for i in range(count))
    return Mesh(vertices, faces)


def _ring(radius: float, count: int, offset: float = math.pi / 4) -> List[Tuple[float, float]]:
    return [(math.cos(offset + i * math.tau / count) * radius,
             math.sin(offset + i * math.tau / count) * radius) for i in range(count)]


def _hull(vertices: List[Vector]) -> Mesh:
    """Find the polygonal faces of the small convex Platonic meshes.

    Coplanar triples are grouped into a single face, preserving pentagons on the
    dodecahedron rather than drawing an arbitrary triangulation of each face.
    """
    face_sets = set()
    for triple in itertools.combinations(range(len(vertices)), 3):
        a, b, c = (vertices[i] for i in triple)
        normal = _cross(_sub(b, a), _sub(c, a))
        if _dot(normal, normal) < 1e-12:
            continue
        distances = [_dot(normal, _sub(v, a)) for v in vertices]
        if min(distances) >= -1e-7 or max(distances) <= 1e-7:
            face_sets.add(frozenset(i for i, d in enumerate(distances) if abs(d) < 1e-7))
    faces = []
    for face_set in sorted(face_sets, key=lambda indices: tuple(sorted(indices))):
        indices = sorted(face_set)
        center = tuple(sum(vertices[i][axis] for i in indices) / len(indices)
                       for axis in range(3))
        normal = _normal(center)
        tangent = _normal(_sub(vertices[indices[0]], center))
        bitangent = _cross(normal, tangent)
        indices.sort(key=lambda i: math.atan2(_dot(_sub(vertices[i], center), bitangent),
                                              _dot(_sub(vertices[i], center), tangent)))
        faces.append(tuple(indices))
    return Mesh(vertices, faces)


@lru_cache(maxsize=4)
def _platonic(name: str) -> Mesh:
    phi = (1 + math.sqrt(5)) / 2
    if name == "tetrahedron":
        vertices = [(1., 1., 1.), (1., -1., -1.), (-1., 1., -1.), (-1., -1., 1.)]
    elif name == "octohedron":
        vertices = [(1., 0., 0.), (-1., 0., 0.), (0., 1., 0.),
                    (0., -1., 0.), (0., 0., 1.), (0., 0., -1.)]
    elif name == "icosahedron":
        vertices = []
        for a, b in itertools.product((-1, 1), repeat=2):
            vertices.extend([(0., a, b * phi), (a, b * phi, 0.), (b * phi, 0., a)])
    else:
        vertices = list(itertools.product((-1., 1.), repeat=3))
        for a, b in itertools.product((-1, 1), repeat=2):
            vertices.extend([(0., a / phi, b * phi),
                             (a / phi, b * phi, 0.), (b * phi, 0., a / phi)])
    return _hull(vertices)


def build_mesh(name: str, values: Dict[str, float]) -> Mesh:
    """Build every supported solid, preserving its dimension proportions."""
    def value(key: str, default: float = 1.0) -> float:
        number = float(values.get(key, default))
        return max(0.001, number) if math.isfinite(number) else default

    if name == "tetrahedron":
        edge = value("side")
        return _extrude(_ring(edge / math.sqrt(3), 3, math.pi / 6),
                        edge * math.sqrt(2 / 3), [(0., 0.)])
    if name in ("octohedron", "dodecahedron", "icosahedron"):
        mesh = _platonic(name)
        edge = min(math.sqrt(_dot(_sub(a, b), _sub(a, b)))
                   for a, b in itertools.combinations(mesh.vertices, 2))
        factor = value("side") / edge
        return Mesh([tuple(coordinate * factor for coordinate in vertex)
                     for vertex in mesh.vertices], mesh.faces)
    if name == "sphere":
        segments, latitudes = 40, 24
        vertices = [(0., -1., 0.)]
        for latitude in range(1, latitudes):
            angle = -math.pi / 2 + math.pi * latitude / latitudes
            vertices.extend((math.cos(angle) * math.cos(i * math.tau / segments),
                             math.sin(angle),
                             math.cos(angle) * math.sin(i * math.tau / segments))
                            for i in range(segments))
        vertices.append((0., 1., 0.))
        faces = [(0, 1 + (i + 1) % segments, 1 + i) for i in range(segments)]
        for latitude in range(latitudes - 2):
            start = 1 + latitude * segments
            faces.extend((start + i, start + (i + 1) % segments,
                          start + (i + 1) % segments + segments, start + i + segments)
                         for i in range(segments))
        start = 1 + (latitudes - 2) * segments
        faces.extend((start + i, start + (i + 1) % segments, len(vertices) - 1)
                     for i in range(segments))
        radius = value("radius")
        return Mesh([tuple(coordinate * radius for coordinate in vertex)
                     for vertex in vertices], faces, curved=True)
    if name in ("cylinder", "cone", "cone_trunk"):
        bottom_radius = value("lbradius") if name == "cone_trunk" else value("radius")
        height = value("height", 2.)
        if name == "cone":
            # The library takes the generatrix, so derive the axial height.
            height = math.sqrt(max(0.001, value("geometry") ** 2 - bottom_radius ** 2))
            top = [(0., 0.)]
        elif name == "cone_trunk":
            top = _ring(value("sbradius"), 48)
        else:
            top = None
        mesh = _extrude(_ring(bottom_radius, 48), height, top)
        mesh.curved = True
        return mesh
    if name in ("pyramid", "pyramid_trunk", "regular_polygon_prism"):
        # Very large side counts become visually circular; bound paint cost.
        requested_count = max(3, int(value("sidesnumber", 4)))
        count = min(96, requested_count)
        bottom_side = value("lbside") if name == "pyramid_trunk" else value(
            "base" if name == "pyramid" else "side")
        radius = bottom_side / (2 * math.sin(math.pi / requested_count))
        if name == "pyramid":
            top = [(0., 0.)]
        elif name == "pyramid_trunk":
            top = _ring(value("sbside") / (2 * math.sin(math.pi / requested_count)), count)
        else:
            top = None
        return _extrude(_ring(radius, count), value("height"), top)
    if name == "rhomboidal_prism":
        x, z = value("largediagonal") / 2, value("smalldiagonal") / 2
        return _extrude([(-x, 0.), (0., z), (x, 0.), (0., -z)], value("height"))
    if name == "triangular_prism":
        x, z = value("base") / 2, value("theight") / 2
        return _extrude([(-x, -z), (x, -z), (0., z)], value("pheight"))
    if name == "trapezoidal_prism":
        bottom, top, z = value("largebase") / 2, value("smallbase") / 2, value("baseheight") / 2
        return _extrude([(-bottom, -z), (bottom, -z), (top, z), (-top, z)], value("pheight"))
    if name == "cube":
        x = z = value("side") / 2
        height = value("side")
    else:
        x, z = value("side1") / 2, value("side2") / 2
        height = value("side3") if name == "rectangular_prism" else value("height")
    return _extrude([(-x, -z), (x, -z), (x, z), (-x, z)], height)


def build_dimensions(name: str, values: Dict[str, float], mesh: Mesh) -> List[DimensionSegment]:
    """Locate measurements on the same vertices and planes used by the solid."""
    vertices = mesh.vertices
    low_y, high_y = min(v[1] for v in vertices), max(v[1] for v in vertices)
    bottom_center, top_center = (0., low_y, 0.), (0., high_y, 0.)
    dimensions = []

    def add(start, end, key, title, dashed=False, symbol=None):
        dimensions.append(DimensionSegment(start, end,
            symbol or parameter_symbol(name, key), title, dashed))

    def midpoint(a, b):
        return tuple((x + y) / 2 for x, y in zip(a, b))

    if name == "sphere":
        add((0., 0., 0.), (float(values["radius"]), 0., 0.), "radius", "radius")
    elif name in ("cylinder", "cone", "cone_trunk"):
        radius = float(values["lbradius"] if name == "cone_trunk" else values["radius"])
        add(bottom_center, (radius, low_y, 0.),
            "lbradius" if name == "cone_trunk" else "radius",
            "lower radius" if name == "cone_trunk" else "radius")
        if name == "cone_trunk":
            small = float(values["sbradius"])
            add(top_center, (small, high_y, 0.), "sbradius", "upper radius")
            add((radius, low_y, 0.), (small, high_y, 0.), "geometry", "slant height")
        elif name == "cone":
            add((radius, low_y, 0.), top_center, "geometry", "slant height")
        if name == "cylinder":
            add((radius, low_y, 0.), (radius, high_y, 0.), "height", "height")
        else:
            add(bottom_center, top_center, "height", "height", True)
    elif name in ("pyramid", "pyramid_trunk", "regular_polygon_prism"):
        count = len(vertices) - 1 if name == "pyramid" else len(vertices) // 2
        key = "lbside" if name == "pyramid_trunk" else "base" if name == "pyramid" else "side"
        sides = max(3, int(values["sidesnumber"]))
        radius = float(values[key]) / (2 * math.sin(math.pi / sides))
        # Decimated display meshes must not change the requested edge measurement.
        angle = math.pi / 4 + math.tau / sides
        bottom_end = (radius * math.cos(angle), low_y, radius * math.sin(angle))
        bottom_mid = midpoint(vertices[0], bottom_end)
        add(vertices[0], bottom_end, key, "base edge")
        if name == "pyramid_trunk":
            small_radius = float(values["sbside"]) / (2 * math.sin(math.pi / sides))
            top_end = (small_radius * math.cos(angle), high_y, small_radius * math.sin(angle))
            add(vertices[count], top_end, "sbside", "upper edge")
            add(bottom_mid, midpoint(vertices[count], top_end),
                "geometry", "slant height")
        elif name == "pyramid":
            add(bottom_mid, vertices[-1], "geometry", "slant height")
        else:
            add(bottom_center, bottom_mid, "apothem", "base apothem", True)
        add(bottom_center, top_center, "height", "height", True)
    elif name in ("tetrahedron", "octohedron", "dodecahedron", "icosahedron"):
        first = mesh.faces[0]
        add(vertices[first[0]], vertices[first[1]], "side", "edge length")
    elif name == "cube":
        add(vertices[0], vertices[1], "side", "edge length")
    elif name in ("rectangular_prism", "quadrangular_prism"):
        add(vertices[0], vertices[1], "side1", "length")
        add(vertices[1], vertices[2], "side2", "width")
        add(vertices[2], vertices[6], "side3" if name == "rectangular_prism" else "height", "height")
    elif name == "rhomboidal_prism":
        add(vertices[0], vertices[2], "largediagonal", "major diagonal", True)
        add(vertices[1], vertices[3], "smalldiagonal", "minor diagonal", True)
        add(vertices[2], vertices[6], "height", "height")
    elif name == "triangular_prism":
        add(vertices[0], vertices[1], "base", "triangle base")
        add(midpoint(vertices[0], vertices[1]), vertices[2], "theight", "triangle height", True)
        add(vertices[1], vertices[4], "pheight", "prism height")
    elif name == "trapezoidal_prism":
        add(vertices[0], vertices[1], "largebase", "lower base")
        add(vertices[2], vertices[3], "smallbase", "upper base")
        add(midpoint(vertices[0], vertices[1]), midpoint(vertices[2], vertices[3]),
            "baseheight", "base height", True)
        add(vertices[1], vertices[5], "pheight", "prism height")
    return dimensions


def section_layers(mesh: Mesh, count: int = 6) -> List[List[Vector]]:
    """Intersect a convex solid with parallel planes to illustrate occupied space."""
    low, high = min(v[1] for v in mesh.vertices), max(v[1] for v in mesh.vertices)
    edges = {tuple(sorted((a, b))) for face in mesh.faces
             for a, b in zip(face, face[1:] + face[:1])}
    sections = []
    tolerance = max(1e-10, (high - low) * 1e-9)
    for layer in range(count):
        height = low + (high - low) * (layer + .5) / count
        points = []
        for a_index, b_index in edges:
            a, b = mesh.vertices[a_index], mesh.vertices[b_index]
            candidates = [point for point in (a, b) if abs(point[1] - height) <= tolerance]
            if (a[1] < height < b[1]) or (b[1] < height < a[1]):
                progress = (height - a[1]) / (b[1] - a[1])
                candidates.append(tuple(a[axis] + progress * (b[axis] - a[axis]) for axis in range(3)))
            for point in candidates:
                if not any(sum((point[i] - existing[i]) ** 2 for i in range(3)) < tolerance ** 2
                           for existing in points):
                    points.append(point)
        if len(points) >= 3:
            cx = sum(p[0] for p in points) / len(points)
            cz = sum(p[2] for p in points) / len(points)
            points.sort(key=lambda p: math.atan2(p[2] - cz, p[0] - cx))
            sections.append(points)
    return sections


class GLVisualizationWidget(QWidget):
    """Orbitable 3D viewport rendered with Qt instead of a driver context.

    The historical class name is retained for callers.  Drag to orbit, use the
    wheel to zoom, double-click to reset; W toggles edges and R resets the camera.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        load_fonts()
        self.current_shape: Optional[ShapeConfig] = None
        self.current_values: Dict[str, float] = {}
        self._mesh: Optional[Mesh] = None
        self._vertices: List[Vector] = []
        self._dimensions: List[DimensionSegment] = []
        self._layers: List[List[Vector]] = []
        self._model_center: Vector = (0., 0., 0.)
        self._model_radius = 1.
        self.measurement_mode = "dimensions"
        self._label_bounds: List[QRectF] = []
        self._azimuth = 35.
        self._elevation = 24.
        self._zoom = 1.
        self._reveal = 1.
        self._last_pos = None
        self._auto_rotate = False
        self._animations_enabled = True
        self.wireframe_mode = False
        self.show_grid = True
        self.show_axes = True
        self._show_dimensions = True
        self._clock = QElapsedTimer()
        self.anim_timer = QTimer(self)
        self.anim_timer.setInterval(33)
        self.anim_timer.timeout.connect(self._tick)
        self._entrance = QVariantAnimation(self)
        self._entrance.setDuration(420)
        self._entrance.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._entrance.valueChanged.connect(self._set_reveal)
        self.setMinimumSize(240, 200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setAccessibleName("Interactive 3D viewer")
        self.setToolTip("Drag to orbit · Scroll to zoom · Double-click to reset")

    def _set_reveal(self, value):
        self._reveal = float(value)
        self.update()

    def _sync_timer(self):
        if (self.isVisible() and self._auto_rotate and self._animations_enabled
                and self.current_shape):
            if not self.anim_timer.isActive():
                self._clock.start()
                self.anim_timer.start()
        else:
            self.anim_timer.stop()

    def _tick(self):
        elapsed = min(self._clock.restart(), 100) / 1000
        if self._last_pos is None:
            self._azimuth = (self._azimuth + elapsed * 9.) % 360
            self.update()

    def showEvent(self, event):
        super().showEvent(event)
        self._sync_timer()

    def hideEvent(self, event):
        self.anim_timer.stop()
        self._entrance.stop()
        self._reveal = 1.
        self._last_pos = None
        super().hideEvent(event)

    def set_shape(self, shape_config: ShapeConfig, values: Dict[str, float]):
        changed = not self.current_shape or self.current_shape.name != shape_config.name
        self.current_shape = shape_config
        self.current_values = dict(values)
        self._mesh = build_mesh(shape_config.name, values)
        self._dimensions = build_dimensions(shape_config.name, values, self._mesh)
        self._layers = section_layers(self._mesh)
        vertices = self._mesh.vertices
        low = [min(v[i] for v in vertices) for i in range(3)]
        high = [max(v[i] for v in vertices) for i in range(3)]
        center = tuple((low[i] + high[i]) / 2 for i in range(3))
        radius = max(math.sqrt(sum((v[i] - center[i]) ** 2 for i in range(3))) for v in vertices)
        self._model_center, self._model_radius = center, radius or 1.
        self._vertices = [tuple((v[i] - center[i]) / (radius or 1.) for i in range(3))
                          for v in vertices]
        if changed:
            self._zoom = 1.
            self._entrance.stop()
            self._entrance.setStartValue(.82)
            self._entrance.setEndValue(1.)
            if self.isVisible() and self._animations_enabled:
                self._entrance.start()
            else:
                self._reveal = 1.
        self._sync_timer()
        self.update()

    def reset_view(self):
        self._azimuth, self._elevation, self._zoom = 35., 24., 1.
        self.update()

    def _reset_camera(self, animated=True):
        self.reset_view()

    def set_auto_rotate(self, enabled: bool):
        self._auto_rotate = enabled
        self._sync_timer()

    def set_animations_enabled(self, enabled: bool):
        """Apply the global motion preference to entry and orbit animations."""
        self._animations_enabled = bool(enabled)
        if not self._animations_enabled:
            self._entrance.stop()
            self._reveal = 1.
        self._sync_timer()
        self.update()

    def set_wireframe(self, enabled: bool):
        self.wireframe_mode = enabled
        self.update()

    def set_grid_visible(self, enabled: bool):
        self.show_grid = enabled
        self.update()

    def set_dimensions_visible(self, enabled: bool):
        self._show_dimensions = enabled
        self.update()

    def set_measurement_mode(self, mode: str):
        """Select geometric dimensions, external area or interior volume."""
        if mode not in ("dimensions", "area", "volume"):
            raise ValueError("Measurement mode must be dimensions, area or volume.")
        self.measurement_mode = mode
        self.update()

    def zoom_in(self):
        self._zoom = min(2.5, self._zoom * 1.15)
        self.update()

    def zoom_out(self):
        self._zoom = max(.4, self._zoom / 1.15)
        self.update()

    def _rotate(self, vertex: Vector) -> Vector:
        yaw, pitch = math.radians(self._azimuth), math.radians(self._elevation)
        x, y, z = vertex
        rx, rz = x * math.cos(yaw) - z * math.sin(yaw), x * math.sin(yaw) + z * math.cos(yaw)
        return (rx, y * math.cos(pitch) - rz * math.sin(pitch),
                y * math.sin(pitch) + rz * math.cos(pitch))

    def _project(self, vertex: Vector, scale: float, center: QPointF) -> QPointF:
        depth = 4.8 / (4.8 - vertex[2])
        return QPointF(center.x() + vertex[0] * scale * depth,
                       center.y() - vertex[1] * scale * depth)

    def _project_world(self, point: Vector, scale: float, center: QPointF) -> QPointF:
        normalized = tuple((point[i] - self._model_center[i]) / self._model_radius
                           for i in range(3))
        return self._project(self._rotate(normalized), scale, center)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)
        rect = QRectF(self.rect())
        background = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        background.setColorAt(0, QColor("#FFFFFF"))
        background.setColorAt(.12, QColor("#FFFFFF"))
        background.setColorAt(1, QColor("#F4F8FF"))
        painter.fillRect(rect, background)
        center = QPointF(rect.center().x(), rect.center().y() - 5)
        scale = min(rect.width() * .30, rect.height() * .32) * self._zoom * self._reveal
        halo = QRadialGradient(center, max(rect.width(), rect.height()) * .42)
        halo.setColorAt(0, QColor(220, 237, 255, 115))
        halo.setColorAt(.55, QColor(242, 248, 255, 65))
        halo.setColorAt(1, QColor(255, 255, 255, 0))
        painter.fillRect(rect, QBrush(halo))
        self._paint_backdrop(painter, rect, center, scale)
        if not self._mesh:
            painter.setPen(QColor("#777777"))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "Select a 3D shape")
            return

        rotated = [self._rotate(v) for v in self._vertices]
        projected = [self._project(v, scale, center) for v in rotated]
        self._paint_ground_shadow(painter, center, scale)
        faces = sorted(self._mesh.faces, key=lambda f: sum(rotated[i][2] for i in f) / len(f))
        light = _normal((-.6, .8, 1.))
        for face in faces:
            vertices = [rotated[i] for i in face]
            normal = _normal(_cross(_sub(vertices[1], vertices[0]), _sub(vertices[2], vertices[0])))
            face_center = tuple(sum(v[axis] for v in vertices) / len(vertices) for axis in range(3))
            if _dot(normal, face_center) < 0:
                normal = tuple(-v for v in normal)
            visible = normal[2] > -.03
            polygon = QPolygonF([projected[i] for i in face])
            if self.wireframe_mode and self.measurement_mode == "dimensions":
                painter.setBrush(Qt.BrushStyle.NoBrush)
                pen = QPen(BLUE if visible else QColor("#D1D2E8"), 1.15 if visible else .7)
                if not visible:
                    pen.setStyle(Qt.PenStyle.DashLine)
                painter.setPen(pen)
            else:
                if not visible:
                    continue
                illumination = max(0., _dot(normal, light))
                if self.measurement_mode == "area":
                    color = QColor.fromRgbF(.12 + illumination * .22,
                                            .36 + illumination * .32, .96, .96)
                else:
                    color = QColor.fromRgbF(.16 + illumination * .28,
                                            .39 + illumination * .32, .95,
                                            .12 if self.measurement_mode == "volume" else 1.)
                painter.setBrush(color)
                # Subpixel fill outlines prevent cracks between curved faces.
                if self._mesh.curved:
                    painter.setPen(QPen(color, .65))
                else:
                    painter.setPen(QPen(QColor(32, 40, 255, 85)
                                        if self.measurement_mode == "volume" else BLUE, 1.1))
            painter.drawPolygon(polygon)

        if self.measurement_mode == "volume":
            self._paint_volume_layers(painter, scale, center)

        if self.show_axes:
            self._paint_axes(painter, rect)
        self._label_bounds = []
        if self._show_dimensions and self.measurement_mode == "dimensions":
            self._paint_dimensions(painter, rect, scale, center)
        elif self.measurement_mode in ("area", "volume"):
            self._paint_measurement_tag(painter, rect, scale, center)
        painter.end()

    def _paint_backdrop(self, painter, rect, center, scale):
        if self.show_grid:
            painter.setPen(QPen(QColor("#DFE8F6"), 1.3, Qt.PenStyle.SolidLine,
                                Qt.PenCapStyle.RoundCap))
            for x in range(24, int(rect.width()), 28):
                for y in range(24, int(rect.height()), 28):
                    painter.drawPoint(QPointF(x, y))

    @staticmethod
    def _paint_ground_shadow(painter, center, scale):
        painter.save()
        painter.translate(center + QPointF(0, scale * .9))
        painter.scale(1, .20)
        radius = max(1., scale * .92)
        shadow = QRadialGradient(0, 0, radius)
        shadow.setColorAt(0, QColor(86, 125, 195, 48))
        shadow.setColorAt(.45, QColor(123, 157, 214, 22))
        shadow.setColorAt(1, QColor(160, 190, 235, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(shadow))
        painter.drawEllipse(QRectF(-radius, -radius, radius * 2, radius * 2))
        painter.restore()

    def _paint_axes(self, painter, rect):
        origin = QPointF(rect.right() - 52, rect.bottom() - 48)
        painter.setFont(QFont(FONTS["primary"], 8))
        for axis, label, color in [((1., 0., 0.), "x", "#999999"),
                                   ((0., 1., 0.), "y", "#777777"),
                                   ((0., 0., 1.), "z", "#2028FF")]:
            point = self._project(self._rotate(axis), 23, origin)
            painter.setPen(QPen(QColor(color), 1.8))
            painter.drawLine(origin, point)
            painter.setPen(QColor(color))
            painter.drawText(QRectF(point.x() - 7, point.y() - 15, 14, 14),
                             Qt.AlignmentFlag.AlignCenter, label)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#7687A4"))
        painter.drawEllipse(origin, 2.5, 2.5)

    def _paint_dimensions(self, painter, rect, scale, center):
        for dimension in self._dimensions:
            start = self._project_world(dimension.start, scale, center)
            end = self._project_world(dimension.end, scale, center)
            delta = end - start
            length = math.hypot(delta.x(), delta.y())
            if length < 4:
                continue
            tangent = delta / length
            normal = QPointF(-tangent.y(), tangent.x())
            midpoint = (start + end) / 2
            outward = midpoint - center
            if normal.x() * outward.x() + normal.y() * outward.y() < 0:
                normal = -normal
            offset = 0. if dimension.dashed else 17.
            a, b = start + normal * offset, end + normal * offset
            painter.setPen(QPen(QColor("#ADB0E7"), .8))
            if offset:
                painter.drawLine(start, a + normal * 4)
                painter.drawLine(end, b + normal * 4)
            pen = QPen(BLUE, 1.)
            if dimension.dashed:
                pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.drawLine(a, b)
            painter.setPen(QPen(BLUE, 1.))
            for point, direction in ((a, tangent), (b, -tangent)):
                painter.drawLine(point, point + direction * 5 + normal * 2.2)
                painter.drawLine(point, point + direction * 5 - normal * 2.2)
            value = (f"{dimension.length:.2f}".rstrip("0").rstrip(".")
                     if .01 <= dimension.length < 10000 else f"{dimension.length:.3g}")
            text = "{} = {} cm".format(dimension.symbol, value)
            label_center = midpoint + normal * (offset + 27)
            bounds = self._paint_label(painter, rect, label_center, text,
                                       dimension.title, normal, tangent)
            # A leader makes displaced labels unambiguous at awkward camera angles.
            if not bounds.contains(midpoint + normal * (offset + 14)):
                painter.setPen(QPen(QColor("#8A8EE8"), .7))
                painter.drawLine(midpoint + normal * offset, bounds.center())
                painter.fillRect(bounds, QColor("#FFFFFF"))
                self._paint_label_text(painter, bounds, text, dimension.title)
        if "sidesnumber" in self.current_values:
            base_height = min(vertex[1] for vertex in self._mesh.vertices)
            anchor = self._project_world((0., base_height, 0.), scale, center)
            target = center + QPointF(-scale - 45, scale * .65)
            bounds = self._paint_label(painter, rect, target,
                "n = {:g}".format(self.current_values["sidesnumber"]), "base sides")
            painter.setPen(QPen(BLUE, .8))
            painter.drawLine(anchor, QPointF(bounds.right(), bounds.center().y()))
            painter.setBrush(BLUE)
            painter.drawEllipse(anchor, 2.1, 2.1)

    def _paint_label(self, painter, viewport, center, text, subtitle,
                     normal=QPointF(0, -1), tangent=QPointF(1, 0)):
        font = QFont(FONTS["primary"])
        font.setPixelSize(11 if viewport.height() < 240 else 12)
        painter.setFont(font)
        metrics = painter.fontMetrics()
        width = min(viewport.width() - 12,
                    max(metrics.horizontalAdvance(text), metrics.horizontalAdvance(subtitle)) + 12)
        height = 35.
        positions = [center + normal * distance + tangent * lateral
                     for distance, lateral in ((0, 0), (22, 0), (0, 45), (0, -45),
                                                (40, 30), (40, -30), (-26, 0))]
        bounds = None
        for position in positions:
            x = max(5., min(viewport.right() - width - 5, position.x() - width / 2))
            y = max(5., min(viewport.bottom() - height - 5, position.y() - height / 2))
            candidate = QRectF(x, y, width, height)
            if not any(candidate.adjusted(-3, -3, 3, 3).intersects(existing)
                       for existing in self._label_bounds):
                bounds = candidate
                break
        if bounds is None:
            # Fall back to an unused edge row when dimensions nearly align on screen.
            for y in range(5, max(6, int(viewport.height() - height)), int(height + 5)):
                for x in (5., viewport.right() - width - 5):
                    candidate = QRectF(x, y, width, height)
                    if not any(candidate.adjusted(-2, -2, 2, 2).intersects(existing)
                               for existing in self._label_bounds):
                        bounds = candidate
                        break
                if bounds is not None:
                    break
        bounds = bounds or candidate
        self._label_bounds.append(bounds)
        painter.fillRect(bounds, QColor("#FFFFFF"))
        self._paint_label_text(painter, bounds, text, subtitle)
        return bounds

    @staticmethod
    def _paint_label_text(painter, bounds, text, subtitle):
        font = QFont(FONTS["primary"])
        font.setPixelSize(12)
        painter.setFont(font)
        painter.setPen(BLUE)
        painter.drawText(bounds.adjusted(5, 0, -5, -15), Qt.AlignmentFlag.AlignCenter, text)
        font.setPixelSize(10)
        painter.setFont(font)
        painter.setPen(QColor("#777777"))
        painter.drawText(bounds.adjusted(5, 17, -5, 0), Qt.AlignmentFlag.AlignCenter, subtitle)

    def _paint_volume_layers(self, painter, scale, center):
        layers = sorted(self._layers, key=lambda section:
            sum(self._rotate(tuple((p[i] - self._model_center[i]) / self._model_radius
                                   for i in range(3)))[2] for p in section) / len(section))
        for section in layers:
            polygon = QPolygonF([self._project_world(point, scale, center) for point in section])
            painter.setPen(QPen(QColor(32, 40, 255, 140), 1.1))
            painter.setBrush(QColor(32, 40, 255, 21))
            painter.drawPolygon(polygon)

    def _paint_measurement_tag(self, painter, rect, scale, center):
        is_area = self.measurement_mode == "area"
        anchor = center + QPointF(scale * .4, -scale * .2)
        target = QPointF(center.x() + scale + 40, center.y() - scale * .4)
        bounds = self._paint_label(painter, rect, target,
            "A · surface area" if is_area else "V · volume",
            "outer faces · cm²" if is_area else "interior layers · cm³")
        painter.setPen(QPen(BLUE, .8))
        painter.drawLine(anchor, QPointF(bounds.left(), bounds.center().y()))
        painter.setBrush(BLUE)
        painter.drawEllipse(anchor, 2.3, 2.3)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._last_pos = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self.setFocus()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._last_pos is None:
            return
        delta = event.position() - self._last_pos
        self._azimuth = (self._azimuth + delta.x() * .5) % 360
        self._elevation = max(-85., min(85., self._elevation + delta.y() * .5))
        self._last_pos = event.position()
        self.update()
        event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._last_pos = None
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        self._zoom = max(.4, min(2.5, self._zoom * math.pow(1.12, event.angleDelta().y() / 120)))
        self.update()
        event.accept()

    def mouseDoubleClickEvent(self, event):
        self.reset_view()
        event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_R:
            self.reset_view()
        elif event.key() == Qt.Key.Key_W:
            self.set_wireframe(not self.wireframe_mode)
        elif event.key() == Qt.Key.Key_G:
            self.set_grid_visible(not self.show_grid)
        elif event.key() in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
            self.zoom_in()
        elif event.key() == Qt.Key.Key_Minus:
            self.zoom_out()
        else:
            super().keyPressEvent(event)
            return
        event.accept()
