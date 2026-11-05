"""Verify that marksgeometrys is the sole source of calculated measurements."""

import math
import unittest
from unittest.mock import patch

import marksgeometrys

from marksgeometrys_ui.calculations import calculate_shape, library_parameters
from marksgeometrys_ui.shapes import ALL_SHAPES, get_shape_config


def defaults(config):
    return {parameter.name: parameter.default for parameter in config.parameters}


class LibraryCalculationTests(unittest.TestCase):
    def test_selected_unit_reaches_every_shape_constructor(self):
        for unit in ("mm", "m", "in", "px", "µm"):
            for config in ALL_SHAPES:
                with self.subTest(unit=unit, shape=config.name):
                    constructor = getattr(marksgeometrys, config.class_name)
                    expected_instance = constructor(**library_parameters(config, defaults(config), unit))
                    expected = (
                        expected_instance.area(),
                        expected_instance.volume() if config.has_volume else None,
                    )
                    with patch.object(marksgeometrys, config.class_name, wraps=constructor) as wrapped:
                        result = calculate_shape(config, defaults(config), unit)
                    self.assertEqual(wrapped.call_args.kwargs["unit"], unit)
                    self.assertEqual(result, expected)

    def test_selected_unit_reaches_required_base_area_primitives(self):
        for name, primitive in (
            ("quadrangular_prism", "Rectangle"),
            ("regular_polygon_prism", "RegularPolygon"),
            ("rhomboidal_prism", "Rhombus"),
        ):
            for unit in ("mm", "m", "in", "px"):
                with self.subTest(shape=name, unit=unit):
                    config = get_shape_config(name)
                    constructor = getattr(marksgeometrys, primitive)
                    with patch.object(marksgeometrys, primitive, wraps=constructor) as wrapped:
                        calculate_shape(config, defaults(config), unit)
                    self.assertEqual(wrapped.call_args.kwargs["unit"], unit)

    def test_unit_selection_labels_values_without_automatic_conversion(self):
        config = get_shape_config("cube")
        values = {"side": 2.5}
        for unit in ("mm", "cm", "m", "in", "px"):
            with self.subTest(unit=unit):
                arguments = library_parameters(config, values, unit)
                self.assertEqual(arguments["side"], 2.5)
                cube = marksgeometrys.Cube(**arguments)
                self.assertEqual(cube.unit, unit)
                self.assertTrue(cube.area_formatted().endswith(unit + "²"))
                self.assertTrue(cube.volume_formatted().endswith(unit + "³"))
                self.assertEqual(calculate_shape(config, values, unit), (37.5, 15.625))

    def test_unit_defaults_to_centimeters_and_trims_outer_whitespace(self):
        config = get_shape_config("circle")
        self.assertEqual(library_parameters(config, defaults(config))["unit"], "cm")
        self.assertEqual(library_parameters(config, defaults(config), "  mm  ")["unit"], "mm")

    def test_invalid_units_are_rejected_before_calling_the_library(self):
        config = get_shape_config("circle")
        with patch.object(marksgeometrys, "Circle") as constructor:
            for unit in (None, "", "  ", 0, False, []):
                with self.subTest(unit=unit):
                    with self.assertRaisesRegex(ValueError, "measurement unit"):
                        calculate_shape(config, defaults(config), unit)
        constructor.assert_not_called()

    def test_every_shape_obtains_its_results_from_the_library_methods(self):
        for config in ALL_SHAPES:
            with self.subTest(shape=config.name):
                # Wrap the genuine constructor so prerequisite library calls remain real.
                constructor = getattr(marksgeometrys, config.class_name)
                instance = constructor(**self._complete_parameters(config))
                with patch.object(instance, "area", return_value=123.456) as area:
                    if config.has_volume:
                        with patch.object(instance, "volume", return_value=987.654) as volume:
                            with patch.object(marksgeometrys, config.class_name, return_value=instance):
                                result = calculate_shape(config, defaults(config))
                        volume.assert_called_once_with()
                        self.assertEqual(result, (123.456, 987.654))
                    else:
                        with patch.object(marksgeometrys, config.class_name, return_value=instance):
                            result = calculate_shape(config, defaults(config))
                        self.assertEqual(result, (123.456, None))
                area.assert_called_once_with()

    @staticmethod
    def _complete_parameters(config):
        # The public preparation API exposes the exact library call for debugging.
        from marksgeometrys_ui.calculations import library_parameters

        return library_parameters(config, defaults(config))

    def test_successful_real_results_are_unchanged_library_outputs(self):
        for config in ALL_SHAPES:
            with self.subTest(shape=config.name):
                instance = getattr(marksgeometrys, config.class_name)(
                    **self._complete_parameters(config)
                )
                raw_area = instance.area()
                raw_volume = instance.volume() if config.has_volume else None
                self.assertIsInstance(raw_area, (int, float))
                self.assertGreater(raw_area, 0)
                if config.has_volume:
                    self.assertIsInstance(raw_volume, (int, float))
                    self.assertGreater(raw_volume, 0)
                area, volume = calculate_shape(config, defaults(config))
                self.assertEqual(area, raw_area)
                self.assertEqual(volume, raw_volume)

    def test_required_base_areas_also_come_from_library_methods(self):
        for name, primitive in (
            ("quadrangular_prism", "Rectangle"),
            ("regular_polygon_prism", "RegularPolygon"),
            ("rhomboidal_prism", "Rhombus"),
        ):
            with self.subTest(shape=name):
                config = get_shape_config(name)
                from marksgeometrys_ui.calculations import library_parameters

                with patch.object(getattr(marksgeometrys, primitive), "area", return_value=314.25) as area:
                    arguments = library_parameters(config, defaults(config))
                self.assertEqual(arguments["base"], 314.25)
                area.assert_called_once_with()

    def test_missing_upstream_result_is_reported_without_a_fallback(self):
        from marksgeometrys_ui.calculations import LibraryCalculationError

        config = get_shape_config("cube")
        with patch.object(marksgeometrys.Cube, "area", return_value=None):
            with self.assertRaisesRegex(LibraryCalculationError, "marksgeometrys.*area") as caught:
                calculate_shape(config, defaults(config))
        self.assertIsNone(caught.exception.area)
        self.assertEqual(caught.exception.volume, 27)

    def test_valid_area_survives_an_upstream_volume_failure(self):
        from marksgeometrys_ui.calculations import LibraryCalculationError

        config = get_shape_config("cube")
        with patch.object(marksgeometrys.Cube, "volume", side_effect=RuntimeError("upstream")):
            with self.assertRaisesRegex(LibraryCalculationError, "marksgeometrys.*volume") as caught:
                calculate_shape(config, defaults(config))
        self.assertEqual(caught.exception.area, 54)
        self.assertIsNone(caught.exception.volume)

    def test_constructor_errors_name_the_library(self):
        from marksgeometrys_ui.calculations import LibraryCalculationError

        config = get_shape_config("cube")
        with patch.object(marksgeometrys, "Cube", side_effect=RuntimeError("constructor failure")):
            with self.assertRaisesRegex(LibraryCalculationError, "marksgeometrys.*constructor"):
                calculate_shape(config, defaults(config))

    def test_integer_float_and_small_numeric_outputs_keep_their_values(self):
        config = get_shape_config("circle")
        for raw, expected in ((12, 12.0), (12.5, 12.5), (1.25e-3, 0.00125), (0.5, 0.5)):
            with self.subTest(raw=raw):
                with patch.object(marksgeometrys.Circle, "area", return_value=raw):
                    self.assertEqual(calculate_shape(config, defaults(config)), (expected, None))

    def test_invalid_library_outputs_are_reported(self):
        from marksgeometrys_ui.calculations import LibraryCalculationError

        config = get_shape_config("circle")
        for value in (None, "not a result", "NaN", "12.5cm²", "12.5", True, math.nan, math.inf, -5):
            with self.subTest(value=value):
                with patch.object(marksgeometrys.Circle, "area", return_value=value):
                    with self.assertRaises(LibraryCalculationError):
                        calculate_shape(config, defaults(config))

    def test_octahedron_now_calculates_through_the_library_numeric_api(self):
        config = get_shape_config("octohedron")
        area, volume = calculate_shape(config, defaults(config))
        solid = marksgeometrys.Octohedron(side=3)
        self.assertEqual(area, solid.area())
        self.assertEqual(volume, solid.volume())
        self.assertGreater(area, 0)
        self.assertGreater(volume, 0)

    def test_sphere_calls_volume_and_never_formatted_measurement_methods(self):
        config = get_shape_config("sphere")
        with patch.object(marksgeometrys.Sphere, "area", return_value=50.25) as area:
            with patch.object(marksgeometrys.Sphere, "volume", return_value=33.75) as volume:
                with patch.object(marksgeometrys.Sphere, "area_formatted") as formatted_area:
                    with patch.object(marksgeometrys.Sphere, "volume_formatted") as formatted_volume:
                        self.assertEqual(calculate_shape(config, defaults(config)), (50.25, 33.75))
        area.assert_called_once_with()
        volume.assert_called_once_with()
        formatted_area.assert_not_called()
        formatted_volume.assert_not_called()

    def test_nonpositive_nonfinite_or_missing_inputs_never_reach_the_library(self):
        config = get_shape_config("circle")
        with patch.object(marksgeometrys, "Circle") as constructor:
            for value in (0, -1, math.nan, math.inf, "bad", None):
                with self.subTest(value=value):
                    with self.assertRaises(ValueError):
                        calculate_shape(config, {"radius": value})
            with self.assertRaises(ValueError):
                calculate_shape(config, {})
        constructor.assert_not_called()

    def test_polygon_side_count_is_an_integer_at_least_three(self):
        config = get_shape_config("regular_polygon")
        for sides in (0, 2, 3.5):
            with self.subTest(sides=sides):
                with self.assertRaisesRegex(ValueError, "number of sides"):
                    calculate_shape(config, {"side": 2, "sidesnumber": sides})

    def test_impossible_cones_and_reversed_bases_are_rejected(self):
        for slant in (2, 3):
            with self.assertRaisesRegex(ValueError, "slant height"):
                calculate_shape(get_shape_config("cone"), {"radius": 3, "geometry": slant})
        for name, values in {
            "cone_trunk": {"sbradius": 4, "lbradius": 2, "height": 3},
            "pyramid_trunk": {"sbside": 4, "lbside": 2, "sidesnumber": 4, "height": 3},
            "trapezoid": {"largebase": 2, "smallbase": 4, "height": 3},
            "trapezoidal_prism": {"largebase": 2, "smallbase": 4, "baseheight": 3, "pheight": 2},
        }.items():
            with self.subTest(shape=name):
                with self.assertRaises(ValueError):
                    calculate_shape(get_shape_config(name), values)


if __name__ == "__main__":
    unittest.main()
