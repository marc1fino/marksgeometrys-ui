"""Integration regressions for real selectors, calculations and compact layouts."""

import os
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QAbstractAnimation
from PyQt6.QtGui import QFontDatabase
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from marksgeometrys_ui.main_window import MainWindow
from marksgeometrys_ui.calculations import LibraryCalculationError, calculate_shape
from marksgeometrys_ui.shapes import ALL_SHAPES, get_shape_config


class WorkspaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyle("Fusion")
        for name in ("arial.ttf", "arialbd.ttf", "ariali.ttf"):
            font = Path("C:/Windows/Fonts") / name
            if font.exists():
                QFontDatabase.addApplicationFont(str(font))

    def setUp(self):
        self.window = MainWindow()
        self.window.motion_button.setChecked(False)
        self.window.show()
        QTest.qWait(1)

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()

    def select(self, name):
        config = get_shape_config(name)
        selector = self.window.shape_selector
        selector.set_category(1 if config.category == "3D" else 0)
        selector.shape_combo.setCurrentIndex(selector.shape_combo.findData(name))
        self.app.processEvents()

    def test_all_25_shapes_render_and_display_the_library_result_or_error(self):
        for config in ALL_SHAPES:
            with self.subTest(shape=config.name):
                self.select(config.name)
                self.assertEqual(self.window.current_shape_config.name, config.name)
                self.assertEqual(set(self.window.current_values), {p.name for p in config.parameters})
                self.assertEqual(self.window.viz_stack.currentIndex(), int(config.category == "3D"))
                try:
                    expected = calculate_shape(config, self.window.current_values)
                    library_error = None
                except LibraryCalculationError as exc:
                    expected = exc.area, exc.volume
                    library_error = str(exc)
                self.window._calculate()
                self.assertEqual(self.window.results_widget.area_card._value, expected[0])
                self.assertEqual(self.window.results_widget.volume_card._value, expected[1])
                self.assertEqual(self.window.error_label.isVisible(), library_error is not None)
                if library_error:
                    self.assertEqual(self.window.error_label.text(), library_error)
                self.assertFalse(self.window._active_viewer().grab().isNull())

    def test_small_windows_keep_viewport_toolbar_and_footer_separate(self):
        for width, height in ((760, 580), (800, 600), (1024, 768), (1440, 900)):
            for name in ("circle", "regular_polygon_prism", "pyramid_trunk"):
                with self.subTest(size=(width, height), shape=name):
                    self.select(name)
                    self.window.resize(width, height)
                    self.app.processEvents()
                    canvas = self.window.viz_stack.geometry()
                    toolbar = self.window.viewer_toolbar.geometry()
                    self.assertLess(canvas.bottom(), toolbar.top())
                    self.assertGreaterEqual(canvas.height(), 140)
                    footer = self.window.calc_button.geometry()
                    scroll = self.window.controls_scroll.geometry()
                    self.assertLess(scroll.bottom(), footer.top())
                    self.assertTrue(self.window.controls_panel.rect().contains(footer))

    def test_edits_clear_results_and_reset_restores_defaults(self):
        self.select("cube")
        self.window._calculate()
        self.assertEqual(self.window.results_widget.volume_card._value, 27)
        self.window.param_form.parameter_widgets[0].spinbox.setValue(7)
        self.assertIsNone(self.window.results_widget.area_card._value)
        self.assertIsNone(self.window.results_widget.volume_card._value)
        self.assertEqual(self.window.viz_3d_widget.current_values["side"], 7)
        self.window._calculate()
        self.assertEqual(self.window.results_widget.volume_card._value, 343)
        self.window._reset_parameters()
        self.assertEqual(self.window.current_values["side"], 3)
        self.assertIsNone(self.window.results_widget.volume_card._value)

    def test_rapid_2d_3d_switches_never_leave_blank_or_stale_page(self):
        for _ in range(12):
            self.select("cube")
            self.select("circle")
        self.assertEqual(self.window.viz_stack.currentIndex(), 0)
        self.assertTrue(self.window.viz_2d_widget.isVisible())
        self.assertFalse(self.window.viz_3d_widget.isVisible())
        self.assertEqual(self.window.viewer_title.text(), "Circle")

    def test_reduced_motion_stops_all_result_and_view_animations(self):
        self.window.motion_button.setChecked(True)
        self.window._calculate()
        self.window.motion_button.setChecked(False)
        stopped = QAbstractAnimation.State.Stopped
        self.assertEqual(self.window.results_widget.area_card._animation.state(), stopped)
        self.assertEqual(self.window.viz_2d_widget._animation.state(), stopped)
        self.assertEqual(self.window.results_widget.area_card.display_value,
                         self.window.results_widget.area_card._value)

    def test_invalid_cone_reports_inline_error_and_clears_results(self):
        self.select("cone")
        self.window._calculate()
        fields = {field.parameter.name: field for field in self.window.param_form.parameter_widgets}
        fields["radius"].spinbox.setValue(6)
        fields["geometry"].spinbox.setValue(3)
        self.window._calculate()
        self.assertTrue(self.window.error_label.isVisible())
        self.assertIsNone(self.window.results_widget.area_card._value)
        self.assertTrue(self.window.calc_button.isEnabled())

    def test_missing_library_output_is_reported_instead_of_replaced(self):
        self.select("cube")
        self.window._calculate()
        with patch("marksgeometrys.Cube") as library_class:
            library_class.return_value.area.return_value = None
            library_class.return_value.volume.return_value = "123.45 cm³"
            self.window._calculate()
        self.assertTrue(self.window.error_label.isVisible())
        self.assertIn("marksgeometrys", self.window.error_label.text())
        self.assertIsNone(self.window.results_widget.area_card._value)
        self.assertEqual(self.window.results_widget.volume_card._value, 123.45)

    def test_measurement_selector_explains_area_and_volume_in_both_categories(self):
        for name in ("circle", "cube"):
            self.select(name)
            for index, mode in enumerate(("dimensions", "area", "volume")):
                self.window.measurement_combo.setCurrentIndex(index)
                self.app.processEvents()
                self.assertEqual(self.window._active_viewer().measurement_mode, mode)
                self.assertEqual(self.window.measurement_help.isVisible(), mode != "dimensions")
                if name == "circle" and mode == "volume":
                    self.assertIn("no volume", self.window.measurement_help.text())

    def test_reference_design_omits_promotional_headings(self):
        from PyQt6.QtWidgets import QLabel
        texts = [widget.text() for widget in self.window.findChildren(QLabel)]
        self.assertNotIn("GEOMETRY LAB", texts)
        self.assertNotIn("25 FIGURES", texts)
        self.assertEqual(self.window.windowTitle(), "MarksGeometrys")

    def test_measurement_views_keep_wireframe_as_a_dimensions_preference(self):
        self.select("cube")
        self.window.wireframe_button.setChecked(True)
        self.window.measurement_combo.setCurrentIndex(1)
        self.assertFalse(self.window.wireframe_button.isEnabled())
        self.window.measurement_combo.setCurrentIndex(2)
        self.assertFalse(self.window.wireframe_button.isEnabled())
        self.window.measurement_combo.setCurrentIndex(0)
        self.assertTrue(self.window.wireframe_button.isEnabled())
        self.assertTrue(self.window.wireframe_button.isChecked())


if __name__ == "__main__":
    unittest.main()
