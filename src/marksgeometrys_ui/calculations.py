"""Adapt UI dimensions to marksgeometrys without replacing its calculations.

Every area and volume displayed by the app comes from an actual marksgeometrys
method. This module validates inputs, derives dependent lengths, supplies the
library's constructor arguments, and reads its numeric results. Upstream
errors are reported explicitly; there are no local measurement fallbacks.
"""

import math
from importlib.metadata import PackageNotFoundError, version
from typing import Dict, Optional, Tuple, Union

import marksgeometrys

from .shapes import ShapeConfig

try:
    LIBRARY_VERSION = version("marksgeometrys")
except PackageNotFoundError:
    LIBRARY_VERSION = "development"

LIBRARY_LABEL = "marksgeometrys " + LIBRARY_VERSION
Result = Tuple[float, Optional[float]]
ConstructorArguments = Dict[str, Union[float, str]]


class LibraryCalculationError(ValueError):
    """An upstream failure with any successful measurement retained."""

    def __init__(self, message, area=None, volume=None):
        super().__init__(message)
        self.area = area
        self.volume = volume


def _number(raw) -> float:
    """Accept the numeric API from marksgeometrys 0.2 without truncating decimals."""
    if raw is None:
        raise ValueError("returned no value")
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        raise ValueError("returned a non-numeric value; marksgeometrys 0.2 or later is required")
    number = float(raw)
    if not math.isfinite(number) or number < 0:
        raise ValueError("returned a non-finite or negative value")
    return number


def _validate(config: ShapeConfig, values: Dict[str, float]) -> Dict[str, float]:
    dimensions = {}
    for parameter in config.parameters:
        try:
            number = float(values[parameter.name])
        except (KeyError, ValueError, TypeError, OverflowError) as exc:
            raise ValueError("A valid dimension is required: " + parameter.label) from exc
        if parameter.name == "sidesnumber":
            if not math.isfinite(number) or not number.is_integer() or number < 3:
                raise ValueError("The number of sides must be an integer of at least 3.")
        elif not math.isfinite(number) or number <= 0:
            raise ValueError("All dimensions must be positive and finite.")
        dimensions[parameter.name] = number
    if config.name == "cone" and dimensions["geometry"] <= dimensions["radius"]:
        raise ValueError("The slant height must be greater than the cone radius.")
    for shape_names, small, large, description in (
        (("cone_trunk",), "sbradius", "lbradius", "radius"),
        (("pyramid_trunk",), "sbside", "lbside", "base side"),
        (("trapezoid", "trapezoidal_prism"), "smallbase", "largebase", "base"),
    ):
        if config.name in shape_names and dimensions[small] > dimensions[large]:
            raise ValueError("The smaller " + description + " cannot exceed the larger one.")
    return dimensions


def _apothem(side: float, sides: float) -> float:
    """Derive a dependent length, not an area or volume."""
    return side / (2 * math.tan(math.pi / sides))


def _validate_unit(unit: str) -> str:
    """Accept the library's custom unit labels without converting dimensions."""
    if not isinstance(unit, str) or not unit.strip():
        raise ValueError("A non-empty measurement unit is required.")
    return unit.strip()


def _base_area(class_name: str, unit: str, **dimensions) -> float:
    """Obtain required base-area arguments from library primitives as well."""
    try:
        instance = getattr(marksgeometrys, class_name)(unit=unit, **dimensions)
        return _number(instance.area())
    except Exception as exc:
        raise LibraryCalculationError(
            LIBRARY_LABEL + " could not calculate the base area with " + class_name + ": " + str(exc)
        ) from exc


def library_parameters(
    config: ShapeConfig, values: Dict[str, float], unit: str = "cm"
) -> ConstructorArguments:
    """Return the exact constructor arguments passed to marksgeometrys.

    Several constructors require redundant dimensions. Base-area inputs are
    obtained from its own 2D classes; geometric lengths use the displayed shape.
    The Pyramid constructor has two rectangular base sides, supplied as the
    selected base edge. The app does not reinterpret them to correct its volume
    formula for other side counts. The selected unit labels the entered values;
    changing the unit does not convert their magnitudes.
    """
    unit = _validate_unit(unit)
    dimensions = _validate(config, values)
    name = config.name
    if name in ("regular_polygon", "regular_polygon_prism"):
        dimensions["apothem"] = _apothem(dimensions["side"], dimensions["sidesnumber"])
        if name == "regular_polygon_prism":
            dimensions["base"] = _base_area(
                "RegularPolygon", unit, side=dimensions["side"],
                sidesnumber=dimensions["sidesnumber"], apothem=dimensions["apothem"],
            )
    elif name == "cone_trunk":
        dimensions["geometry"] = math.hypot(
            dimensions["height"], dimensions["lbradius"] - dimensions["sbradius"]
        )
    elif name == "pyramid":
        dimensions["apothem"] = _apothem(dimensions["base"], dimensions["sidesnumber"])
        dimensions["side"] = math.hypot(dimensions["height"], dimensions["apothem"])
        dimensions["side1"] = dimensions["base"]
        dimensions["side2"] = dimensions["base"]
    elif name == "pyramid_trunk":
        dimensions["sbapothem"] = _apothem(dimensions["sbside"], dimensions["sidesnumber"])
        dimensions["lbapothem"] = _apothem(dimensions["lbside"], dimensions["sidesnumber"])
        dimensions["latlargebase"] = dimensions["lbside"]
        dimensions["latsmallbase"] = dimensions["sbside"]
        dimensions["latheight"] = math.hypot(
            dimensions["height"], dimensions["lbapothem"] - dimensions["sbapothem"]
        )
    elif name == "tetrahedron":
        dimensions["height"] = math.sqrt(2 / 3) * dimensions["side"]
    elif name == "dodecahedron":
        dimensions["apothem"] = _apothem(dimensions["side"], 5)
    elif name == "rectangular_prism":
        dimensions["height"] = dimensions["side3"]
    elif name == "quadrangular_prism":
        dimensions["base"] = _base_area(
            "Rectangle", unit, base=dimensions["side1"], height=dimensions["side2"]
        )
    elif name == "rhomboidal_prism":
        dimensions["base"] = _base_area(
            "Rhombus", unit, largediagonal=dimensions["largediagonal"],
            smalldiagonal=dimensions["smalldiagonal"],
        )
    elif name == "trapezoidal_prism":
        # This is the legacy constructor's prism-base length, not its area.
        dimensions["pbase"] = (dimensions["largebase"] + dimensions["smallbase"]) / 2
    arguments: ConstructorArguments = dict(dimensions)
    arguments["unit"] = unit
    return arguments


def calculate_shape(
    config: ShapeConfig, values: Dict[str, float], unit: str = "cm"
) -> Result:
    """Call the library's area/volume methods and preserve their numeric outputs."""
    dimensions = library_parameters(config, values, unit)
    try:
        instance = getattr(marksgeometrys, config.class_name)(**dimensions)
    except Exception as exc:
        raise LibraryCalculationError(
            LIBRARY_LABEL + " constructor for " + config.class_name + " failed: " + str(exc)
        ) from exc

    area, volume = None, None
    failures = []
    if config.has_area:
        try:
            area = _number(instance.area())
        except Exception as exc:
            failures.append("area: " + str(exc))
    if config.has_volume:
        try:
            method = getattr(instance, "volume", None)
            if not callable(method):
                raise ValueError("no volume method is available")
            volume = _number(method())
        except Exception as exc:
            failures.append("volume: " + str(exc))
    if failures:
        raise LibraryCalculationError(
            LIBRARY_LABEL + " could not calculate " + config.class_name + " ("
            + "; ".join(failures) + ").", area=area, volume=volume,
        )
    return area, volume
