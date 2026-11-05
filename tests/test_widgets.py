"""Checks for English labels, dimension symbols and direct library provenance."""

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QAbstractAnimation
from PyQt6.QtWidgets import QApplication

from marksgeometrys_ui.shapes import ALL_SHAPES, get_shape_config
from marksgeometrys_ui.symbols import parameter_symbol
from marksgeometrys_ui.widgets import ParameterFormWidget, ResultsWidget, ShapeSelectorWidget


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
        self.assertEqual(results.volume_card.formula_label.text(), "marksgeometrys · volum()")
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


if __name__ == "__main__":
    unittest.main()
