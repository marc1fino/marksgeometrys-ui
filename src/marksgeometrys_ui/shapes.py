"""Shape definitions and parameter configurations for marksgeometrys UI."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class Parameter:
    """Represents a parameter for a shape."""
    name: str
    label: str
    unit: str = "cm"
    default: Optional[float] = None
    min_value: float = 0.0
    step: float = 0.1
    tooltip: str = ""


@dataclass
class ShapeConfig:
    """Configuration for a geometric shape."""
    name: str
    display_name: str
    category: str  # "2D" or "3D"
    class_name: str  # Class name in marksgeometrys
    parameters: List[Parameter]
    has_area: bool = True
    has_volume: bool = False
    description: str = ""


# 2D Shapes
SHAPES_2D = [
    ShapeConfig(
        name="circle",
        display_name="Circle",
        category="2D",
        class_name="Circle",
        parameters=[
            Parameter(name="radius", label="Radius", unit="cm", default=5.0, min_value=0.1, tooltip="Radius of the circle"),
        ],
        has_area=True,
        has_volume=False,
        description="A perfectly round 2D shape where all points are equidistant from the center.",
    ),
    ShapeConfig(
        name="square",
        display_name="Square",
        category="2D",
        class_name="Square",
        parameters=[
            Parameter(name="side", label="Side", unit="cm", default=5.0, min_value=0.1, tooltip="Length of one side"),
        ],
        has_area=True,
        has_volume=False,
        description="A quadrilateral with four equal sides and four right angles.",
    ),
    ShapeConfig(
        name="rectangle",
        display_name="Rectangle",
        category="2D",
        class_name="Rectangle",
        parameters=[
            Parameter(name="base", label="Base", unit="cm", default=5.0, min_value=0.1, tooltip="Length of the base"),
            Parameter(name="height", label="Height", unit="cm", default=3.0, min_value=0.1, tooltip="Height of the rectangle"),
        ],
        has_area=True,
        has_volume=False,
        description="A quadrilateral with four right angles and opposite sides equal.",
    ),
    ShapeConfig(
        name="triangle",
        display_name="Triangle",
        category="2D",
        class_name="Triangle",
        parameters=[
            Parameter(name="base", label="Base", unit="cm", default=5.0, min_value=0.1, tooltip="Length of the base"),
            Parameter(name="height", label="Height", unit="cm", default=4.0, min_value=0.1, tooltip="Height from base to opposite vertex"),
        ],
        has_area=True,
        has_volume=False,
        description="A polygon with three edges and three vertices.",
    ),
    ShapeConfig(
        name="rhombus",
        display_name="Rhombus",
        category="2D",
        class_name="Rhombus",
        parameters=[
            Parameter(name="largediagonal", label="Large Diagonal", unit="cm", default=8.0, min_value=0.1, tooltip="Length of the longer diagonal"),
            Parameter(name="smalldiagonal", label="Small Diagonal", unit="cm", default=4.0, min_value=0.1, tooltip="Length of the shorter diagonal"),
        ],
        has_area=True,
        has_volume=False,
        description="A quadrilateral with all four sides of equal length.",
    ),
    ShapeConfig(
        name="parallelogram",
        display_name="Parallelogram",
        category="2D",
        class_name="Parallelogram",
        parameters=[
            Parameter(name="base", label="Base", unit="cm", default=5.0, min_value=0.1, tooltip="Length of the base"),
            Parameter(name="height", label="Height", unit="cm", default=3.0, min_value=0.1, tooltip="Perpendicular height"),
        ],
        has_area=True,
        has_volume=False,
        description="A quadrilateral with opposite sides parallel and equal.",
    ),
    ShapeConfig(
        name="trapezoid",
        display_name="Trapezoid",
        category="2D",
        class_name="Trapezoid",
        parameters=[
            Parameter(name="largebase", label="Large Base", unit="cm", default=8.0, min_value=0.1, tooltip="Length of the longer parallel side"),
            Parameter(name="smallbase", label="Small Base", unit="cm", default=4.0, min_value=0.1, tooltip="Length of the shorter parallel side"),
            Parameter(name="height", label="Height", unit="cm", default=3.0, min_value=0.1, tooltip="Perpendicular distance between bases"),
        ],
        has_area=True,
        has_volume=False,
        description="A quadrilateral with at least one pair of parallel sides.",
    ),
    ShapeConfig(
        name="regular_polygon",
        display_name="Regular Polygon",
        category="2D",
        class_name="RegularPolygon",
        parameters=[
            Parameter(name="side", label="Side Length", unit="cm", default=3.0, min_value=0.1, tooltip="Length of one side"),
            Parameter(name="sidesnumber", label="Number of Sides", unit="", default=6, min_value=3, step=1, tooltip="Number of sides (3+)"),
            Parameter(name="apothem", label="Apothem", unit="cm", default=2.6, min_value=0.1, tooltip="Distance from center to midpoint of side"),
        ],
        has_area=True,
        has_volume=False,
        description="A polygon with all sides and angles equal.",
    ),
]

# 3D Shapes
SHAPES_3D = [
    ShapeConfig(
        name="cube",
        display_name="Cube",
        category="3D",
        class_name="Cube",
        parameters=[
            Parameter(name="side", label="Side", unit="cm", default=3.0, min_value=0.1, tooltip="Length of one edge"),
        ],
        has_area=True,
        has_volume=True,
        description="A 3D solid with six equal square faces.",
    ),
    ShapeConfig(
        name="sphere",
        display_name="Sphere",
        category="3D",
        class_name="Sphere",
        parameters=[
            Parameter(name="radius", label="Radius", unit="cm", default=2.0, min_value=0.1, tooltip="Distance from center to surface"),
        ],
        has_area=True,
        has_volume=True,
        description="A perfectly round 3D object where all surface points are equidistant from the center.",
    ),
    ShapeConfig(
        name="cylinder",
        display_name="Cylinder",
        category="3D",
        class_name="Cylinder",
        parameters=[
            Parameter(name="radius", label="Radius", unit="cm", default=3.0, min_value=0.1, tooltip="Radius of the circular base"),
            Parameter(name="height", label="Height", unit="cm", default=5.0, min_value=0.1, tooltip="Height of the cylinder"),
        ],
        has_area=True,
        has_volume=True,
        description="A 3D solid with two parallel circular bases connected by a curved surface.",
    ),
    ShapeConfig(
        name="cone",
        display_name="Cone",
        category="3D",
        class_name="Cone",
        parameters=[
            Parameter(name="radius", label="Base Radius", unit="cm", default=3.0, min_value=0.1, tooltip="Radius of the circular base"),
            Parameter(name="geometry", label="Slant Height", unit="cm", default=5.0, min_value=0.1, tooltip="Slant height (generatrix)"),
        ],
        has_area=True,
        has_volume=True,
        description="A 3D solid with a circular base tapering to a point (apex).",
    ),
    ShapeConfig(
        name="cone_trunk",
        display_name="Cone Trunk (Frustum)",
        category="3D",
        class_name="ConeTrunk",
        parameters=[
            Parameter(name="sbradius", label="Small Base Radius", unit="cm", default=2.0, min_value=0.1, tooltip="Radius of the top base"),
            Parameter(name="lbradius", label="Large Base Radius", unit="cm", default=4.0, min_value=0.1, tooltip="Radius of the bottom base"),
            Parameter(name="height", label="Height", unit="cm", default=5.0, min_value=0.1, tooltip="Perpendicular height"),
            Parameter(name="geometry", label="Slant Height", unit="cm", default=5.4, min_value=0.1, tooltip="Slant height of the frustum"),
        ],
        has_area=True,
        has_volume=True,
        description="A cone with the top cut off parallel to the base.",
    ),
    ShapeConfig(
        name="pyramid",
        display_name="Pyramid",
        category="3D",
        class_name="Pyramid",
        parameters=[
            Parameter(name="base", label="Base Side", unit="cm", default=4.0, min_value=0.1, tooltip="Side length of base polygon"),
            Parameter(name="sidesnumber", label="Number of Base Sides", unit="", default=4, min_value=3, step=1, tooltip="Number of sides of base polygon"),
            Parameter(name="apothem", label="Base Apothem", unit="cm", default=2.0, min_value=0.1, tooltip="Apothem of base polygon"),
            Parameter(name="side", label="Slant Height", unit="cm", default=5.0, min_value=0.1, tooltip="Slant height of triangular faces"),
            Parameter(name="height", label="Height", unit="cm", default=4.0, min_value=0.1, tooltip="Perpendicular height from base to apex"),
        ],
        has_area=True,
        has_volume=True,
        description="A polyhedron with a polygonal base and triangular faces meeting at an apex.",
    ),
    ShapeConfig(
        name="pyramid_trunk",
        display_name="Pyramid Trunk (Frustum)",
        category="3D",
        class_name="PyramidTrunk",
        parameters=[
            Parameter(name="sbside", label="Small Base Side", unit="cm", default=2.0, min_value=0.1, tooltip="Side of top base polygon"),
            Parameter(name="sidesnumber", label="Number of Base Sides", unit="", default=4, min_value=3, step=1, tooltip="Number of sides of base polygon"),
            Parameter(name="sbapothem", label="Small Base Apothem", unit="cm", default=1.0, min_value=0.1, tooltip="Apothem of top base"),
            Parameter(name="lbside", label="Large Base Side", unit="cm", default=4.0, min_value=0.1, tooltip="Side of bottom base polygon"),
            Parameter(name="lbapothem", label="Large Base Apothem", unit="cm", default=2.0, min_value=0.1, tooltip="Apothem of bottom base"),
            Parameter(name="latheight", label="Lateral Height", unit="cm", default=3.0, min_value=0.1, tooltip="Slant height of trapezoidal faces"),
            Parameter(name="height", label="Height", unit="cm", default=4.0, min_value=0.1, tooltip="Perpendicular height"),
        ],
        has_area=True,
        has_volume=True,
        description="A pyramid with the top cut off parallel to the base.",
    ),
    ShapeConfig(
        name="tetrahedron",
        display_name="Tetrahedron",
        category="3D",
        class_name="Tetrahedron",
        parameters=[
            Parameter(name="side", label="Edge Length", unit="cm", default=3.0, min_value=0.1, tooltip="Length of each edge"),
            Parameter(name="height", label="Height", unit="cm", default=2.45, min_value=0.1, tooltip="Height from base to opposite vertex"),
        ],
        has_area=True,
        has_volume=True,
        description="A polyhedron with four triangular faces (regular tetrahedron has equilateral triangles).",
    ),
    ShapeConfig(
        name="octohedron",
        display_name="Octahedron",
        category="3D",
        class_name="Octohedron",
        parameters=[
            Parameter(name="side", label="Edge Length", unit="cm", default=3.0, min_value=0.1, tooltip="Length of each edge"),
        ],
        has_area=True,
        has_volume=True,
        description="A polyhedron with eight equilateral triangle faces.",
    ),
    ShapeConfig(
        name="dodecahedron",
        display_name="Dodecahedron",
        category="3D",
        class_name="Dodecahedron",
        parameters=[
            Parameter(name="side", label="Edge Length", unit="cm", default=2.0, min_value=0.1, tooltip="Length of each edge"),
            Parameter(name="apothem", label="Face Apothem", unit="cm", default=1.38, min_value=0.1, tooltip="Apothem of pentagonal face"),
        ],
        has_area=True,
        has_volume=True,
        description="A polyhedron with twelve regular pentagon faces.",
    ),
    ShapeConfig(
        name="icosahedron",
        display_name="Icosahedron",
        category="3D",
        class_name="Icosahedron",
        parameters=[
            Parameter(name="side", label="Edge Length", unit="cm", default=2.0, min_value=0.1, tooltip="Length of each edge"),
        ],
        has_area=True,
        has_volume=True,
        description="A polyhedron with twenty equilateral triangle faces.",
    ),
    ShapeConfig(
        name="rectangular_prism",
        display_name="Rectangular Prism",
        category="3D",
        class_name="RectangularPrism",
        parameters=[
            Parameter(name="side1", label="Length", unit="cm", default=4.0, min_value=0.1, tooltip="Length of the prism"),
            Parameter(name="side2", label="Width", unit="cm", default=3.0, min_value=0.1, tooltip="Width of the prism"),
            Parameter(name="side3", label="Depth", unit="cm", default=2.0, min_value=0.1, tooltip="Depth of the prism"),
            Parameter(name="height", label="Height", unit="cm", default=5.0, min_value=0.1, tooltip="Height (alternative to side3)"),
        ],
        has_area=True,
        has_volume=True,
        description="A 3D solid with six rectangular faces (box shape).",
    ),
    ShapeConfig(
        name="quadrangular_prism",
        display_name="Quadrangular Prism",
        category="3D",
        class_name="QuadrangularPrism",
        parameters=[
            Parameter(name="side1", label="Base Side 1", unit="cm", default=4.0, min_value=0.1, tooltip="First side of quadrilateral base"),
            Parameter(name="side2", label="Base Side 2", unit="cm", default=3.0, min_value=0.1, tooltip="Second side of quadrilateral base"),
            Parameter(name="height", label="Height", unit="cm", default=5.0, min_value=0.1, tooltip="Height of the prism"),
            Parameter(name="base", label="Base Area", unit="cm²", default=12.0, min_value=0.1, tooltip="Area of the quadrilateral base"),
        ],
        has_area=True,
        has_volume=True,
        description="A prism with a quadrilateral base.",
    ),
    ShapeConfig(
        name="regular_polygon_prism",
        display_name="Regular Polygon Prism",
        category="3D",
        class_name="RegularPolygonPrism",
        parameters=[
            Parameter(name="side", label="Base Side", unit="cm", default=3.0, min_value=0.1, tooltip="Side length of regular polygon base"),
            Parameter(name="apothem", label="Base Apothem", unit="cm", default=2.6, min_value=0.1, tooltip="Apothem of base polygon"),
            Parameter(name="sidesnumber", label="Number of Sides", unit="", default=6, min_value=3, step=1, tooltip="Number of sides of base polygon"),
            Parameter(name="height", label="Height", unit="cm", default=5.0, min_value=0.1, tooltip="Height of the prism"),
            Parameter(name="base", label="Base Area", unit="cm²", default=23.4, min_value=0.1, tooltip="Area of base polygon"),
        ],
        has_area=True,
        has_volume=True,
        description="A prism with a regular polygon base.",
    ),
    ShapeConfig(
        name="rhomboidal_prism",
        display_name="Rhomboidal Prism",
        category="3D",
        class_name="RhomboidalPrism",
        parameters=[
            Parameter(name="largediagonal", label="Large Diagonal", unit="cm", default=8.0, min_value=0.1, tooltip="Longer diagonal of rhombus base"),
            Parameter(name="smalldiagonal", label="Small Diagonal", unit="cm", default=4.0, min_value=0.1, tooltip="Shorter diagonal of rhombus base"),
            Parameter(name="height", label="Height", unit="cm", default=5.0, min_value=0.1, tooltip="Height of the prism"),
            Parameter(name="base", label="Base Area", unit="cm²", default=16.0, min_value=0.1, tooltip="Area of rhombus base"),
        ],
        has_area=True,
        has_volume=True,
        description="A prism with a rhombus base.",
    ),
    ShapeConfig(
        name="triangular_prism",
        display_name="Triangular Prism",
        category="3D",
        class_name="TriangularPrism",
        parameters=[
            Parameter(name="base", label="Triangle Base", unit="cm", default=4.0, min_value=0.1, tooltip="Base of triangular face"),
            Parameter(name="theight", label="Triangle Height", unit="cm", default=3.0, min_value=0.1, tooltip="Height of triangular face"),
            Parameter(name="pheight", label="Prism Height", unit="cm", default=5.0, min_value=0.1, tooltip="Height/length of the prism"),
        ],
        has_area=True,
        has_volume=True,
        description="A prism with triangular bases.",
    ),
    ShapeConfig(
        name="trapezoidal_prism",
        display_name="Trapezoidal Prism",
        category="3D",
        class_name="TrapezoidalPrism",
        parameters=[
            Parameter(name="largebase", label="Large Base", unit="cm", default=8.0, min_value=0.1, tooltip="Longer parallel side of trapezoid"),
            Parameter(name="smallbase", label="Small Base", unit="cm", default=4.0, min_value=0.1, tooltip="Shorter parallel side of trapezoid"),
            Parameter(name="baseheight", label="Trapezoid Height", unit="cm", default=3.0, min_value=0.1, tooltip="Height of trapezoidal face"),
            Parameter(name="pheight", label="Prism Height", unit="cm", default=5.0, min_value=0.1, tooltip="Height/length of the prism"),
            Parameter(name="pbase", label="Prism Base", unit="cm", default=6.0, min_value=0.1, tooltip="Base dimension of prism"),
        ],
        has_area=True,
        has_volume=True,
        description="A prism with trapezoidal bases.",
    ),
]

# All shapes combined
ALL_SHAPES = SHAPES_2D + SHAPES_3D

# Shape lookup by name
SHAPE_LOOKUP = {shape.name: shape for shape in ALL_SHAPES}


def get_shape_config(name: str) -> Optional[ShapeConfig]:
    """Get shape configuration by name."""
    return SHAPE_LOOKUP.get(name)


def get_shapes_by_category(category: str) -> List[ShapeConfig]:
    """Get all shapes of a specific category (2D or 3D)."""
    return [s for s in ALL_SHAPES if s.category == category]