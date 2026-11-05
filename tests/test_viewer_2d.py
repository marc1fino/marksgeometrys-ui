"""Regression checks for small viewports and safe native painter rendering."""

import math
import sys
import unittest
from unittest.mock import patch

from PyQt6.QtCore import QPoint, QPointF, Qt
from PyQt6.QtGui import QPainter
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from marksgeometrys_ui.shapes import SHAPES_2D, get_shape_config
from marksgeometrys_ui.viewer_2d import ShapeVisualizationWidget


class PlaneViewerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.viewer = ShapeVisualizationWidget()
        self.errors = []
        self.original_hook = sys.excepthook
        sys.excepthook = lambda kind, error, trace: self.errors.append(error)

    def tearDown(self):
        self.viewer.close()
        self.viewer.deleteLater()
        self.app.processEvents()
        sys.excepthook = self.original_hook
        self.assertEqual(self.errors, [])

    def test_every_plane_figure_renders_in_small_and_large_viewports(self):
        for width, height in [(240, 200), (340, 240), (960, 540)]:
            self.viewer.resize(width, height)
            for shape in SHAPES_2D:
                with self.subTest(size=(width, height), shape=shape.name):
                    self.viewer.set_shape(shape, {p.name: p.default for p in shape.parameters})
                    image = self.viewer.grab().toImage()
                    blue_pixels = sum(
                        1
                        for x in range(20, image.width() - 20, 2)
                        for y in range(32, image.height() - 32, 2)
                        if image.pixelColor(x, y).blue() > image.pixelColor(x, y).red() * 1.2
                        and image.pixelColor(x, y).blue() > image.pixelColor(x, y).green() * 1.1
                    )
                    self.assertGreater(blue_pixels, 20)

    def test_rectangle_keeps_physical_aspect_ratio(self):
        shape = get_shape_config("rectangle")
        self.viewer.resize(800, 500)
        self.viewer.set_dimensions_visible(False)
        self.viewer.set_grid_visible(False)
        self.viewer.set_shape(shape, {"base": 8.0, "height": 2.0})
        image = self.viewer.grab().toImage()
        outline = [
            (x, y)
            for x in range(20, image.width() - 20)
            for y in range(32, image.height() - 32)
            if image.pixelColor(x, y).blue() > 200
            and image.pixelColor(x, y).red() < 100
            and image.pixelColor(x, y).green() < 150
        ]
        self.assertTrue(outline)
        # Isolate the shape outline from the labels, which use the same accent.
        center_y = image.height() // 2 - 4
        midline = [x for x, y in outline if abs(y - center_y) <= 2]
        span = max(midline) - min(midline)
        center_x = image.width() // 2
        vertical = [y for x, y in outline if abs(x - center_x) <= 2]
        top = min(vertical)
        self.assertAlmostEqual(span / (2 * (center_y - top)), 4.0, delta=0.25)

    def test_view_controls_and_hidden_animation(self):
        shape = get_shape_config("circle")
        self.viewer.set_shape(shape, {"radius": 5.0})
        self.viewer.show()
        self.app.processEvents()
        self.viewer.zoom_in()
        self.viewer.zoom_out()
        self.viewer.set_dimensions_visible(False)
        self.viewer.set_grid_visible(False)
        QTest.mousePress(self.viewer, Qt.MouseButton.LeftButton, pos=QPoint(100, 90))
        QTest.mouseMove(self.viewer, QPoint(130, 110))
        QTest.mouseRelease(self.viewer, Qt.MouseButton.LeftButton, pos=QPoint(130, 110))
        self.viewer.reset_view()
        self.viewer.set_shape(shape, {"radius": 7.0})
        self.viewer.hide()
        self.assertEqual(self.viewer._animation.state().name, "Stopped")
        self.assertEqual(self.viewer.current_values["radius"], 7.0)
        self.viewer.grab()

    def test_reduced_motion_finishes_and_suppresses_transitions(self):
        shape = get_shape_config("triangle")
        self.viewer.set_shape(shape, {"base": 5.0, "height": 4.0})
        self.viewer.show()
        self.app.processEvents()
        self.viewer.set_shape(shape, {"base": 7.0, "height": 2.0})
        self.assertEqual(self.viewer._animation.state().name, "Running")
        self.viewer.set_animations_enabled(False)
        self.assertEqual(self.viewer._animation.state().name, "Stopped")
        self.assertEqual(self.viewer._display_values(), {"base": 7.0, "height": 2.0})
        self.viewer.set_shape(shape, {"base": 8.0, "height": 3.0})
        self.assertEqual(self.viewer._animation.state().name, "Stopped")
        self.assertEqual(self.viewer._display_values(), {"base": 8.0, "height": 3.0})
        self.viewer.set_animations_enabled(True)
        self.viewer.set_shape(shape, {"base": 6.0, "height": 4.0})
        self.assertEqual(self.viewer._animation.state().name, "Running")

    def test_rapid_edits_continue_from_the_displayed_geometry(self):
        shape = get_shape_config("rectangle")
        self.viewer.set_shape(shape, {"base": 5., "height": 3.})
        self.viewer.show()
        self.app.processEvents()
        self.viewer.set_shape(shape, {"base": 9., "height": 6.})
        self.viewer._animation.setCurrentTime(120)
        displayed = self.viewer._display_values()
        self.viewer.set_shape(shape, {"base": 12., "height": 4.})
        self.assertEqual(self.viewer._from_values, displayed)
        self.assertEqual(self.viewer._display_values(), displayed)
        self.viewer._animation.setCurrentTime(80)
        elapsed = self.viewer._animation.currentTime()
        self.viewer.set_shape(shape, {"base": 12., "height": 4.})
        self.assertEqual(self.viewer._animation.currentTime(), elapsed)
        self.viewer._animation.setCurrentTime(self.viewer._animation.duration())
        self.assertEqual(self.viewer._display_values(), {"base": 12., "height": 4.})

    def test_polygon_apothem_and_side_dimensions_match_the_outline(self):
        self.viewer.resize(800, 500)
        shape = get_shape_config("regular_polygon")
        for sides in (3, 5, 6, 8):
            with self.subTest(sides=sides):
                self.viewer.set_shape(shape, {"side": 3.0, "sidesnumber": sides})
                with patch.object(self.viewer, "_construction") as construction, \
                     patch.object(self.viewer, "_measure") as measure, \
                     patch.object(self.viewer, "_pill") as pill:
                    self.viewer.grab()
                origin, midpoint = construction.call_args.args[1:3]
                edge_start, edge_end = measure.call_args.args[1:3]
                apothem_pixels = math.hypot(midpoint.x() - origin.x(), midpoint.y() - origin.y())
                edge_pixels = math.hypot(edge_end.x() - edge_start.x(), edge_end.y() - edge_start.y())
                ratio = 1 / (2 * math.tan(math.pi / sides))
                self.assertAlmostEqual(apothem_pixels / edge_pixels, ratio)
                self.assertEqual(pill.call_args.args[2], f"a = {3.0 * ratio:.2f}".rstrip("0").rstrip(".") + " cm")

    def test_measurement_modes_keep_the_figure_and_show_distinct_overlays(self):
        self.viewer.resize(720, 460)
        self.viewer.set_animations_enabled(False)
        self.viewer.set_grid_visible(False)
        images = {}
        for shape in SHAPES_2D:
            self.viewer.set_shape(shape, {p.name: p.default for p in shape.parameters})
            for mode in ("dimensions", "area", "volume"):
                with self.subTest(shape=shape.name, mode=mode):
                    self.viewer.set_measurement_mode(mode)
                    image = self.viewer.grab().toImage()
                    self.assertFalse(image.isNull())
                    images[mode] = image
            self.assertNotEqual(images["dimensions"], images["area"])
            self.assertNotEqual(images["area"], images["volume"])

    def test_area_grid_is_clipped_to_the_actual_shape(self):
        shape = get_shape_config("circle")
        self.viewer.resize(500, 340)
        self.viewer.set_grid_visible(False)
        self.viewer.set_shape(shape, {"radius": 5.0})
        self.viewer.set_measurement_mode("area")
        image = self.viewer.grab().toImage()
        self.assertEqual(image.pixelColor(24, 24).name(), "#ffffff")
        self.assertNotEqual(image.pixelColor(250, 115).name(), "#ffffff")
        with self.assertRaises(ValueError):
            self.viewer.set_measurement_mode("unrecognized")

    def test_units_relabel_dimensions_grid_and_cube_without_converting_geometry(self):
        viewer = self.viewer
        viewer.resize(720, 460)
        viewer.set_animations_enabled(False)
        config = get_shape_config("regular_polygon")
        values = {"side": 3., "sidesnumber": 6.}
        viewer.set_shape(config, values)
        geometry = viewer._geometry(values)
        texts = []

        class RecordingPainter(QPainter):
            def drawText(self, *args):
                texts.append(str(args[-1]))
                return super().drawText(*args)

        for unit in ("mm", "in", "px"):
            with self.subTest(unit=unit):
                viewer.set_unit(unit)
                viewer.set_shape(config, values)  # Same-value fast path must not hide unit changes.
                texts.clear()
                with patch("marksgeometrys_ui.viewer_2d.QPainter", RecordingPainter):
                    for mode in ("dimensions", "area", "volume"):
                        viewer.set_measurement_mode(mode)
                        viewer.grab()
                self.assertTrue(any(text.startswith("l =") and text.endswith(" " + unit) for text in texts))
                self.assertTrue(any(text.startswith("a =") and text.endswith(" " + unit) for text in texts))
                self.assertTrue(any(text.startswith("Grid:") and f"{unit} ×" in text for text in texts))
                self.assertIn(f"1 {unit}³", texts)
                self.assertFalse(any(" cm" in text for text in texts))
                self.assertEqual(viewer.current_values, values)
                self.assertEqual(viewer._geometry(values), geometry)
                self.assertEqual(viewer.unit, unit)
        for invalid in (None, "", "  "):
            with self.assertRaises(ValueError):
                viewer.set_unit(invalid)

    def test_changing_units_keeps_an_in_progress_parameter_transition(self):
        viewer = self.viewer
        config = get_shape_config("rectangle")
        viewer.set_shape(config, {"base": 5., "height": 3.})
        viewer.show()
        self.app.processEvents()
        viewer.set_shape(config, {"base": 9., "height": 6.})
        viewer._animation.setCurrentTime(120)
        displayed = viewer._display_values()
        elapsed, state = viewer._animation.currentTime(), viewer._animation.state()
        viewer._pan = QPointF(7, 11)
        viewer._zoom = 1.5
        with patch.object(viewer, "update") as update:
            viewer.set_unit("m")
        update.assert_called_once()
        self.assertEqual(viewer._animation.currentTime(), elapsed)
        self.assertEqual(viewer._animation.state(), state)
        self.assertEqual(viewer._display_values(), displayed)
        self.assertEqual(viewer._pan, QPointF(7, 11))
        self.assertEqual(viewer._zoom, 1.5)


if __name__ == "__main__":
    unittest.main()
