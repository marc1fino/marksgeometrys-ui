"""Shared dimension symbols for form fields and geometric annotations."""

_PARAMETER_SYMBOLS = {
    "radius": "r", "side": "l", "base": "b", "height": "h",
    "largediagonal": "D", "smalldiagonal": "d", "largebase": "B",
    "smallbase": "b", "sidesnumber": "n", "apothem": "a", "geometry": "g",
    "sbradius": "r", "lbradius": "R", "sbside": "l", "lbside": "L",
    "sbapothem": "a", "lbapothem": "A", "latheight": "g",
    "side1": "a", "side2": "b", "side3": "h", "theight": "t",
    "pheight": "h", "baseheight": "t", "pbase": "b",
}


def parameter_symbol(shape_name: str, parameter_name: str) -> str:
    """Return the symbol used consistently for a shape's input dimension."""
    if parameter_name == "base" and shape_name == "pyramid":
        return "l"
    return _PARAMETER_SYMBOLS.get(parameter_name, parameter_name)
