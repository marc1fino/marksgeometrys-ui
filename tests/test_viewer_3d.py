"""Regression coverage for the desktop's driver-independent 3D viewport."""

import itertools
import math
import os
import unittest
from unittest.mock import patch
from collections import Counter
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QAbstractAnimation, QPoint, Qt
from PyQt6.QtGui import QFontDatabase, QPainter
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from marksgeometrys_ui.shapes import SHAPES_3D, get_shape_config
from marksgeometrys_ui.viewer_3d import (
    GLVisualizationWidget, build_dimensions, build_mesh, section_layers,
)


class MeshTests(unittest.TestCase):
    def test_dimension_segments_match_model_lengths_and_shared_symbols(self):
        examples = {
            "cube": ({"side": 3.}, {"l": 3.}),
            "sphere": ({"radius": 7.}, {"r": 7.}),
            "cylinder": ({"radius": 2., "height": 9.}, {"r": 2., "h": 9.}),
            "cone": ({"radius": 3., "geometry": 5.}, {"r": 3., "g": 5., "h": 4.}),
            "cone_trunk": ({"sbradius": 2., "lbradius": 4., "height": 5.},
                           {"r": 2., "R": 4., "h": 5., "g": math.sqrt(29)}),
            "regular_polygon_prism": ({"side": 3., "sidesnumber": 6., "height": 9.},
                                      {"l": 3., "h": 9., "a": 3 * math.sqrt(3) / 2}),
            "rectangular_prism": ({"side1": 4., "side2": 3., "side3": 2.},
                                  {"a": 4., "b": 3., "h": 2.}),
            "rhomboidal_prism": ({"largediagonal": 8., "smalldiagonal": 4., "height": 5.},
                                 {"D": 8., "d": 4., "h": 5.}),
        }
        for name, (values, expected) in examples.items():
            with self.subTest(shape=name):
                dimensions = build_dimensions(name, values, build_mesh(name, values))
                self.assertEqual({d.symbol for d in dimensions}, set(expected))
                for dimension in dimensions:
                    self.assertAlmostEqual(dimension.length, expected[dimension.symbol])
                    self.assertNotEqual(dimension.start, dimension.end)

    def test_decimated_polygon_measurements_still_use_requested_edge(self):
        values = {"side": .1, "sidesnumber": 10000., "height": 1.}
        dimensions = build_dimensions("regular_polygon_prism", values,
                                      build_mesh("regular_polygon_prism", values))
        self.assertAlmostEqual(next(d.length for d in dimensions if d.symbol == "l"), .1)

    def test_volume_layers_are_real_sections_inside_every_solid(self):
        for shape in SHAPES_3D:
            with self.subTest(shape=shape.name):
                mesh = build_mesh(shape.name, {p.name: p.default for p in shape.parameters})
                layers = section_layers(mesh)
                self.assertEqual(len(layers), 6)
                self.assertTrue(all(len(layer) >= 3 for layer in layers))
                heights = [layer[0][1] for layer in layers]
                self.assertEqual(heights, sorted(heights))
                self.assertTrue(all(all(abs(p[1] - layer[0][1]) < 1e-9 for p in layer)
                                    for layer in layers))

    def test_every_supported_solid_is_a_closed_mesh(self):
        for shape in SHAPES_3D:
            with self.subTest(shape=shape.name):
                mesh = build_mesh(shape.name, {p.name: p.default for p in shape.parameters})
                edges = Counter()
                for face in mesh.faces:
                    self.assertGreaterEqual(len(face), 3)
                    for start, end in zip(face, face[1:] + face[:1]):
                        self.assertNotEqual(start, end)
                        self.assertLess(max(start, end), len(mesh.vertices))
                        edges[tuple(sorted((start, end)))] += 1
                self.assertTrue(edges)
                self.assertEqual(set(edges.values()), {2})
                self.assertEqual(len(mesh.vertices) - len(edges) + len(mesh.faces), 2)

    def test_platonic_solids_have_their_real_faces(self):
        for name, expected_count, face_size in [
            ("tetrahedron", 4, 3), ("octohedron", 8, 3),
            ("dodecahedron", 12, 5), ("icosahedron", 20, 3),
        ]:
            with self.subTest(shape=name):
                mesh = build_mesh(name, {"side": 3., "height": math.sqrt(6)})
                self.assertEqual(len(mesh.faces), expected_count)
                self.assertEqual({len(face) for face in mesh.faces}, {face_size})

    def test_dimension_changes_preserve_actual_proportions(self):
        mesh = build_mesh("cylinder", {"radius": 2., "height": 9.})
        self.assertAlmostEqual(max(v[1] for v in mesh.vertices) - min(v[1] for v in mesh.vertices), 9.)
        self.assertAlmostEqual(max(v[0] for v in mesh.vertices) - min(v[0] for v in mesh.vertices), 4.)
        cone = build_mesh("cone", {"radius": 3., "geometry": 5.})
        self.assertAlmostEqual(max(v[1] for v in cone.vertices) - min(v[1] for v in cone.vertices), 4.)

    def test_huge_polygon_side_counts_have_bounded_render_cost(self):
        mesh = build_mesh("regular_polygon_prism", {"sidesnumber": 10000., "side": .1, "height": 1.})
        self.assertLessEqual(len(mesh.faces), 98)
        self.assertAlmostEqual(math.hypot(mesh.vertices[0][0], mesh.vertices[0][2]),
                               .1 / (2 * math.sin(math.pi / 10000)))

    def test_regular_solids_derive_geometry_from_independent_dimensions(self):
        side = 3.
        tetrahedron = build_mesh("tetrahedron", {"side": side})
        height = max(v[1] for v in tetrahedron.vertices) - min(v[1] for v in tetrahedron.vertices)
        self.assertAlmostEqual(height, side * math.sqrt(2 / 3))
        for name in ("octohedron", "dodecahedron", "icosahedron"):
            with self.subTest(shape=name):
                mesh = build_mesh(name, {"side": side})
                shortest = min(math.dist(a, b) for a, b in
                               itertools.combinations(mesh.vertices, 2))
                self.assertAlmostEqual(shortest, side)
        sphere = build_mesh("sphere", {"radius": 7.})
        self.assertTrue(all(abs(math.sqrt(sum(x * x for x in vertex)) - 7.) < 1e-10
                            for vertex in sphere.vertices))

    def test_pyramid_prism_and_frustum_heights_use_the_axial_height(self):
        for name, parameters in [
            ("pyramid", {"base": 4., "sidesnumber": 5., "height": 9.}),
            ("pyramid_trunk", {"sbside": 2., "lbside": 4., "sidesnumber": 4., "height": 9.}),
            ("regular_polygon_prism", {"side": 3., "sidesnumber": 6., "height": 9.}),
            ("cone_trunk", {"sbradius": 2., "lbradius": 4., "height": 9.}),
        ]:
            with self.subTest(shape=name):
                mesh = build_mesh(name, parameters)
                height = max(v[1] for v in mesh.vertices) - min(v[1] for v in mesh.vertices)
                self.assertAlmostEqual(height, 9.)


class ViewportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        for name in ("arial.ttf", "arialbd.ttf"):
            path = Path("C:/Windows/Fonts") / name
            if path.exists():
                QFontDatabase.addApplicationFont(str(path))

    def setUp(self):
        self.viewer = GLVisualizationWidget()
        self.viewer.resize(480, 320)
        self.viewer.set_auto_rotate(False)

    def tearDown(self):
        self.viewer.close()
        self.viewer.deleteLater()
        self.app.processEvents()

    def test_all_shapes_render_without_an_opengl_context(self):
        self.viewer.show()
        for shape in SHAPES_3D:
            with self.subTest(shape=shape.name):
                self.viewer.set_shape(shape, {p.name: p.default for p in shape.parameters})
                self.app.processEvents()
                image = self.viewer.grab().toImage()
                self.assertFalse(image.isNull())
                # Blue geometry must be painted; dimension labels may cover its center.
                blue_samples = sum(image.pixelColor(x, y).blue() -
                                   image.pixelColor(x, y).red() > 30
                                   for x in range(120, 360, 4) for y in range(60, 260, 4))
                self.assertGreater(blue_samples, 100)

    def test_all_measurement_modes_render_and_invalid_mode_is_rejected(self):
        self.viewer.show()
        self.viewer.set_animations_enabled(False)
        for shape in SHAPES_3D:
            self.viewer.set_shape(shape, {p.name: p.default for p in shape.parameters})
            for mode in ("dimensions", "area", "volume"):
                with self.subTest(shape=shape.name, mode=mode):
                    self.viewer.set_measurement_mode(mode)
                    self.assertFalse(self.viewer.grab().isNull())
                    self.assertEqual(self.viewer.measurement_mode, mode)
        with self.assertRaises(ValueError):
            self.viewer.set_measurement_mode("unknown")

    def test_wireframe_preference_does_not_suppress_measurement_fills(self):
        self.viewer.show()
        self.viewer.set_animations_enabled(False)
        self.viewer.set_shape(get_shape_config("cube"), {"side": 3.})
        self.viewer.set_wireframe(False)
        for mode in ("area", "volume"):
            with self.subTest(mode=mode):
                self.viewer.set_measurement_mode(mode)
                self.viewer.set_wireframe(False)
                filled = self.viewer.grab().toImage()
                self.viewer.set_wireframe(True)
                with_preference = self.viewer.grab().toImage()
                self.assertEqual(filled, with_preference)
        self.viewer.set_measurement_mode("dimensions")
        wireframe = self.viewer.grab().toImage()
        self.viewer.set_wireframe(False)
        self.assertNotEqual(wireframe, self.viewer.grab().toImage())

    def test_volume_sections_are_lazy_and_follow_the_current_transition_frame(self):
        config = get_shape_config("sphere")
        with patch("marksgeometrys_ui.viewer_3d.section_layers", wraps=section_layers) as sections:
            self.viewer.set_shape(config, {"radius": 3.})
            self.viewer.show()
            self.app.processEvents()
            self.viewer.set_shape(config, {"radius": 4.})
            self.viewer._edit_animation.setCurrentTime(100)
            self.viewer.set_measurement_mode("area")
            self.viewer._edit_animation.setCurrentTime(160)
            sections.assert_not_called()
            self.assertEqual(self.viewer._layers, [])

            self.viewer.set_measurement_mode("volume")
            self.assertEqual(sections.call_count, 1)
            self.assertEqual(self.viewer._layers, section_layers(self.viewer._mesh))
            self.viewer.set_measurement_mode("volume")
            self.assertEqual(sections.call_count, 1)
            self.viewer._edit_animation.setCurrentTime(200)
            self.assertEqual(sections.call_count, 2)
            self.assertEqual(self.viewer._layers, section_layers(self.viewer._mesh))

            self.viewer.set_animations_enabled(False)
            self.assertEqual(self.viewer._displayed_values, {"radius": 4.})
            self.assertEqual(self.viewer._layers, section_layers(self.viewer._mesh))
            self.viewer.set_measurement_mode("dimensions")
            calls = sections.call_count
            self.viewer.set_shape(config, {"radius": 5.})
            self.assertEqual(sections.call_count, calls)
            self.assertEqual(self.viewer._layers, [])
            self.viewer.set_measurement_mode("volume")
            self.assertEqual(sections.call_count, calls + 1)
            self.assertEqual(self.viewer._layers, section_layers(self.viewer._mesh))

    def test_dimension_labels_stay_within_viewport_without_overlap(self):
        self.viewer.show()
        self.viewer.set_animations_enabled(False)
        for size in ((480, 320), (760, 420)):
            self.viewer.resize(*size)
            for shape in SHAPES_3D:
                with self.subTest(size=size, shape=shape.name):
                    self.viewer.set_shape(shape, {p.name: p.default for p in shape.parameters})
                    self.viewer.grab()
                    bounds = self.viewer._label_bounds
                    self.assertGreaterEqual(len(bounds), 1)
                    self.assertTrue(all(self.viewer.rect().contains(b.toRect()) for b in bounds))
                    self.assertFalse(any(a.intersects(b) for a, b in itertools.combinations(bounds, 2)))

    def test_editing_dimensions_keeps_the_camera(self):
        config = get_shape_config("cylinder")
        self.viewer.set_shape(config, {"radius": 3., "height": 5.})
        self.viewer._azimuth = 112.
        self.viewer._elevation = -18.
        self.viewer._zoom = 1.6
        self.viewer.set_shape(config, {"radius": 4., "height": 8.})
        self.assertEqual((self.viewer._azimuth, self.viewer._elevation, self.viewer._zoom),
                         (112., -18., 1.6))
        self.assertEqual(self.viewer.current_values["height"], 8.)

    def test_parameter_transitions_keep_measurements_attached_and_rapid_edits_continuous(self):
        config = get_shape_config("cylinder")
        self.viewer.set_shape(config, {"radius": 3., "height": 5.})
        self.viewer.show()
        self.app.processEvents()
        self.viewer.set_shape(config, {"radius": 4., "height": 9.})
        self.assertEqual(self.viewer.current_values["height"], 9.)
        self.assertEqual(self.viewer._edit_animation.state(), QAbstractAnimation.State.Running)
        self.viewer._edit_animation.setCurrentTime(100)
        displayed = dict(self.viewer._displayed_values)
        self.assertGreater(displayed["height"], 5.)
        self.assertLess(displayed["height"], 9.)
        mesh_height = max(v[1] for v in self.viewer._mesh.vertices) - min(v[1] for v in self.viewer._mesh.vertices)
        self.assertAlmostEqual(mesh_height, displayed["height"])
        height = next(d for d in self.viewer._dimensions if d.title == "height")
        self.assertAlmostEqual(height.length, displayed["height"])
        self.viewer.set_shape(config, {"radius": 2., "height": 11.})
        self.assertEqual(self.viewer._edit_from_values, displayed)
        self.assertEqual(self.viewer._displayed_values, displayed)
        self.viewer.set_animations_enabled(False)
        self.assertEqual(self.viewer._edit_animation.state(), QAbstractAnimation.State.Stopped)
        self.assertEqual(self.viewer._displayed_values, {"radius": 2., "height": 11.})
        self.viewer.set_animations_enabled(True)
        self.viewer.set_shape(config, {"radius": 4., "height": 7.})
        self.viewer.hide()
        self.assertEqual(self.viewer._edit_animation.state(), QAbstractAnimation.State.Stopped)
        self.assertEqual(self.viewer._displayed_values, {"radius": 4., "height": 7.})

    def test_rotation_timer_stops_when_hidden_or_disabled(self):
        self.viewer.set_shape(get_shape_config("cube"), {"side": 3.})
        self.viewer.set_auto_rotate(True)
        self.assertFalse(self.viewer.anim_timer.isActive())
        self.viewer.show()
        self.app.processEvents()
        self.assertTrue(self.viewer.anim_timer.isActive())
        self.viewer.hide()
        self.app.processEvents()
        self.assertFalse(self.viewer.anim_timer.isActive())
        self.viewer.show()
        self.viewer.set_auto_rotate(False)
        self.assertFalse(self.viewer.anim_timer.isActive())

    def test_default_orbit_is_off_and_global_motion_stops_all_animations(self):
        self.viewer.set_shape(get_shape_config("cube"), {"side": 3.})
        self.viewer.show()
        self.app.processEvents()
        self.assertFalse(self.viewer.anim_timer.isActive())
        self.viewer.set_auto_rotate(True)
        self.assertTrue(self.viewer.anim_timer.isActive())
        self.viewer.set_animations_enabled(False)
        self.assertFalse(self.viewer.anim_timer.isActive())
        self.assertEqual(self.viewer._entrance.state(), QAbstractAnimation.State.Stopped)
        self.assertEqual(self.viewer._reveal, 1.)
        self.viewer.set_shape(get_shape_config("sphere"), {"radius": 3.})
        self.assertEqual(self.viewer._entrance.state(), QAbstractAnimation.State.Stopped)
        self.viewer.set_animations_enabled(True)
        self.assertTrue(self.viewer.anim_timer.isActive())

    def test_mouse_orbit_keyboard_reset_and_render_modes(self):
        self.viewer.set_shape(get_shape_config("cube"), {"side": 3.})
        self.viewer.show()
        self.app.processEvents()
        initial = self.viewer._azimuth
        QTest.mousePress(self.viewer, Qt.MouseButton.LeftButton, pos=QPoint(200, 160))
        QTest.mouseMove(self.viewer, QPoint(260, 185))
        QTest.mouseRelease(self.viewer, Qt.MouseButton.LeftButton, pos=QPoint(260, 185))
        self.assertNotEqual(self.viewer._azimuth, initial)
        QTest.keyClick(self.viewer, Qt.Key.Key_R)
        self.assertEqual(self.viewer._azimuth, 35.)
        self.viewer.set_wireframe(True)
        self.viewer.set_grid_visible(False)
        self.viewer.set_dimensions_visible(False)
        self.assertFalse(self.viewer.grab().isNull())

    def test_units_relabel_actual_dimensions_and_measurement_tags(self):
        viewer = self.viewer
        viewer.set_animations_enabled(False)
        config = get_shape_config("cylinder")
        values = {"radius": 3., "height": 5.}
        viewer.set_shape(config, values)
        original_vertices = list(viewer._mesh.vertices)
        texts = []

        class RecordingPainter(QPainter):
            def drawText(self, *args):
                texts.append(str(args[-1]))
                return super().drawText(*args)

        for unit in ("mm", "in", "px"):
            with self.subTest(unit=unit):
                viewer.set_unit(unit)
                viewer.set_shape(config, values)
                texts.clear()
                with patch("marksgeometrys_ui.viewer_3d.QPainter", RecordingPainter):
                    for mode in ("dimensions", "area", "volume"):
                        viewer.set_measurement_mode(mode)
                        viewer.grab()
                self.assertTrue(any(text.startswith("r =") and text.endswith(" " + unit) for text in texts))
                self.assertTrue(any(text.startswith("h =") and text.endswith(" " + unit) for text in texts))
                self.assertIn(f"outer faces · {unit}²", texts)
                self.assertIn(f"interior layers · {unit}³", texts)
                self.assertFalse(any(" cm" in text for text in texts))
                self.assertEqual(viewer._mesh.vertices, original_vertices)
                self.assertEqual(viewer.current_values, values)
                self.assertEqual(viewer.unit, unit)
        for invalid in (None, "", "  "):
            with self.assertRaises(ValueError):
                viewer.set_unit(invalid)

    def test_changing_units_preserves_camera_mesh_layers_and_animation(self):
        viewer = self.viewer
        config = get_shape_config("cylinder")
        viewer.set_shape(config, {"radius": 3., "height": 5.})
        viewer.show()
        self.app.processEvents()
        viewer.set_measurement_mode("volume")
        viewer.set_shape(config, {"radius": 4., "height": 9.})
        viewer._edit_animation.setCurrentTime(100)
        mesh, dimensions, layers = viewer._mesh, viewer._dimensions, viewer._layers
        displayed = dict(viewer._displayed_values)
        elapsed, state = viewer._edit_animation.currentTime(), viewer._edit_animation.state()
        camera = viewer._azimuth, viewer._elevation, viewer._zoom
        timer_active = viewer.anim_timer.isActive()
        with patch.object(viewer, "update") as update:
            viewer.set_unit("ft")
        update.assert_called_once()
        self.assertIs(viewer._mesh, mesh)
        self.assertIs(viewer._dimensions, dimensions)
        self.assertIs(viewer._layers, layers)
        self.assertEqual(viewer._displayed_values, displayed)
        self.assertEqual(viewer._edit_animation.currentTime(), elapsed)
        self.assertEqual(viewer._edit_animation.state(), state)
        self.assertEqual((viewer._azimuth, viewer._elevation, viewer._zoom), camera)
        self.assertEqual(viewer.measurement_mode, "volume")
        self.assertEqual(viewer.anim_timer.isActive(), timer_active)


if __name__ == "__main__":
    unittest.main()
