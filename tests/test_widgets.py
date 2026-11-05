"""Checks for English labels, dimension symbols and direct library provenance."""

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QAbstractAnimation
from PyQt6.QtWidgets import QApplication

from marksgeometrys_ui.shapes import ALL_SHAPES, Parameter, get_shape_config
from marksgeometrys_ui.symbols import parameter_symbol
from marksgeometrys_ui.widgets import (
    ParameterFormWidget, ParameterWidget, ResultsWidget, ShapeSelectorWidget,
)


class ControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_form_labels_match_the_viewer_symbols_for_every_shape(self):
        form = ParameterFormWidget()
        for shape in ALL_SHAPES:
            with self.subTest(shape=shape.name):
                form.set_shape(shape)
                self.assertEqual(set(form.get_values()), {p.name for p in shape.parameters})
                for field in form.parameter_widgets:
                    self.assertEqual(field.symbol_label.text(),
                                     parameter_symbol(shape.name, field.parameter.name))
                    self.assertEqual(field.spinbox.locale().name(), "en_US")
        form.close()

    def test_selector_uses_english_shape_names_and_stable_category_signals(self):
        selector = ShapeSelectorWidget()
        selected = []
        selector.shape_changed.connect(selected.append)
        self.assertEqual(selector.shape_combo.currentText(), "Circle")
        selector.set_category(1)
        self.assertEqual(selector.shape_combo.currentText(), "Cube")
        selector.set_category(0)
        self.assertEqual(selected, ["cube", "circle"])
        selector.close()

    def test_results_identify_actual_library_methods(self):
        results = ResultsWidget()
        results.set_results(12.5, 7.2, True, "sphere")
        self.assertEqual(results.area_card.title_label.text(), "Area")
        self.assertEqual(results.volume_card.title_label.text(), "Volume")
        self.assertEqual(results.area_card.formula_label.text(), "marksgeometrys · area()")
        self.assertEqual(results.volume_card.formula_label.text(), "marksgeometrys · volume()")
        results.set_results(9, None, False, "square")
        self.assertIn("plane figure", results.volume_card.formula_label.text())
        self.assertIsNone(results.volume_card._value)
        results.close()

    def test_reduced_motion_keeps_exact_result_values(self):
        results = ResultsWidget()
        results.show()
        self.app.processEvents()
        results.set_results(123.45, 678.9, True, "cube")
        results.set_animations_enabled(False)
        self.assertEqual(results.area_card._animation.state(), QAbstractAnimation.State.Stopped)
        self.assertEqual(results.area_card.display_value, 123.45)
        self.assertEqual(results.volume_card.display_value, 678.9)
        results.close()

    def test_repeated_targets_do_not_restart_an_ongoing_number_animation(self):
        results = ResultsWidget()
        results.show()
        self.app.processEvents()
        results.set_results(123.45, 678.9, True, "cube")
        card = results.area_card
        card._animation.setCurrentTime(120)
        displayed = card.display_value
        elapsed = card._animation.currentTime()
        results.set_results(123.45, 678.9, True, "cube")
        self.assertGreaterEqual(card._animation.currentTime(), elapsed)
        self.assertEqual(card.display_value, displayed)
        results.set_results(250.75, 678.9, True, "cube")
        self.assertEqual(card._animation.startValue(), displayed)
        results.set_animations_enabled(False)
        self.assertEqual(card.display_value, 250.75)
        results.close()

    def test_unit_changes_preserve_dimensions_counts_and_edit_signals(self):
        form = ParameterFormWidget()
        form.set_shape(get_shape_config("regular_polygon_prism"))
        form.parameter_widgets[0].set_value(2.75)
        changes = []
        form.values_changed.connect(changes.append)
        expected = form.get_values()
        for unit in ("mm", "m", "in", "px"):
            with self.subTest(unit=unit):
                form.set_unit(unit)
                self.assertEqual(form.get_values(), expected)
                self.assertEqual(changes, [])
                for field in form.parameter_widgets:
                    self.assertEqual(field.spinbox.suffix(),
                                     " " + unit if field.parameter.unit else "")
        form.close()

    def test_unit_selection_survives_shape_changes(self):
        form = ParameterFormWidget()
        form.set_unit("ft")
        for name in ("circle", "regular_polygon", "cube"):
            form.set_shape(get_shape_config(name))
            self.assertEqual(form.current_unit, "ft")
            for field in form.parameter_widgets:
                self.assertEqual(field.spinbox.suffix(), " ft" if field.parameter.unit else "")
        form.close()

    def test_parameter_unit_power_and_signal_blocking_are_preserved(self):
        field = ParameterWidget(Parameter(name="base", label="Base area", unit="cm²",
                                          default=2.5))
        changes = []
        field.value_changed.connect(lambda *args: changes.append(args))
        field.spinbox.blockSignals(True)
        field.set_unit("mm")
        self.assertTrue(field.spinbox.signalsBlocked())
        self.assertEqual(field.spinbox.suffix(), " mm²")
        self.assertEqual(field.get_value(), 2.5)
        self.assertEqual(changes, [])
        field.close()

    def test_result_unit_changes_update_labels_and_tooltips_without_restarting(self):
        results = ResultsWidget()
        results.show()
        self.app.processEvents()
        results.set_results(12.5, 7.25, True, "cube")
        results.area_card._animation.setCurrentTime(120)
        elapsed = results.area_card._animation.currentTime()
        displayed = results.area_card.display_value
        animation_state = results.area_card._animation.state()
        for unit in ("mm", "m", "in", "px"):
            with self.subTest(unit=unit):
                results.set_unit(unit)
                self.assertEqual(results.area_card.unit_label.text(), unit + "²")
                self.assertEqual(results.volume_card.unit_label.text(), unit + "³")
                self.assertEqual(results.area_card.unit, unit + "²")
                self.assertEqual(results.volume_card.unit, unit + "³")
                self.assertEqual(results.area_card.value_label.toolTip(), "12.5 " + unit + "²")
                self.assertEqual(results.volume_card.value_label.toolTip(), "7.25 " + unit + "³")
                self.assertEqual(results.area_card._value, 12.5)
                self.assertEqual(results.volume_card._value, 7.25)
                self.assertGreaterEqual(results.area_card._animation.currentTime(), elapsed)
                self.assertEqual(results.area_card._animation.state(), animation_state)
                self.assertEqual(results.area_card.display_value, displayed)
        results.set_results(9.5, None, False, "square")
        self.assertEqual(results.area_card.unit_label.text(), "px²")
        self.assertEqual(results.volume_card.unit_label.text(), "px³")
        self.assertEqual(results.area_card.value_label.toolTip(), "9.5 px²")
        results.close()


if __name__ == "__main__":
    unittest.main()
