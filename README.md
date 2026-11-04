# MarksGeometrys UI

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/PyQt6-6.6+-green.svg" alt="PyQt6 Version">
  <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License">
  <img src="https://img.shields.io/badge/status-active-brightgreen.svg" alt="Status">
</p>

A beautiful, interactive desktop application for calculating areas and volumes of geometric shapes. Built on top of the [`marksgeometrys`](https://pypi.org/project/marksgeometrys/) Python library with a modern PyQt6 interface.

## ✨ Features

- **25 Geometric Shapes** — 8 two-dimensional and 17 three-dimensional shapes
- **Real-time Visualization** — See a visual representation of each shape as you adjust parameters
- **Instant Calculations** — Compute area and volume with a single click
- **Parameter Validation** — Input constraints prevent invalid geometries
- **Modern UI** — Clean, responsive interface built with PyQt6
- **Cross-platform** — Runs on Windows, macOS, and Linux

## 📐 Supported Shapes

### 2D Shapes (Area)
| Shape | Parameters |
|-------|------------|
| Circle | Radius |
| Square | Side |
| Rectangle | Base, Height |
| Triangle | Base, Height |
| Rhombus | Large Diagonal, Small Diagonal |
| Parallelogram | Base, Height |
| Trapezoid | Large Base, Small Base, Height |
| Regular Polygon | Side, Number of Sides, Apothem |

### 3D Shapes (Area + Volume)
| Shape | Parameters |
|-------|------------|
| Cube | Side |
| Sphere | Radius |
| Cylinder | Radius, Height |
| Cone | Radius, Slant Height |
| Cone Trunk (Frustum) | Small/Large Radius, Height, Slant Height |
| Pyramid | Base Side, Sides, Apothem, Slant Height, Height |
| Pyramid Trunk | Small/Large Base Sides, Apothems, Lateral Height, Height |
| Tetrahedron | Edge, Height |
| Octahedron | Edge |
| Dodecahedron | Edge, Face Apothem |
| Icosahedron | Edge |
| Rectangular Prism | Length, Width, Depth, Height |
| Quadrangular Prism | Two Base Sides, Height, Base Area |
| Regular Polygon Prism | Side, Apothem, Sides, Height, Base Area |
| Rhomboidal Prism | Diagonals, Height, Base Area |
| Triangular Prism | Triangle Base, Triangle Height, Prism Height |
| Trapezoidal Prism | Large/Small Base, Base Height, Prism Height, Prism Base |

## 🚀 Installation

### From PyPI (Recommended)
```bash
pip install marksgeometrys-ui
```

### From Source
```bash
git clone https://github.com/marc1fino/marksgeometrys-ui.git
cd marksgeometrys-ui
pip install -e .
```

### Development Install
```bash
git clone https://github.com/marc1fino/marksgeometrys-ui.git
cd marksgeometrys-ui
pip install -e ".[dev]"
```

## 🎮 Usage

### Launch the Application
```bash
marksgeometrys-ui
```

Or use the short alias:
```bash
mgui
```

### Running from Source
```bash
python -m marksgeometrys_ui
```

## 🖥️ Interface Overview

```
┌─────────────────────────────────────────────────────────────┐
│  MarksGeometrys - Geometry Calculator                        │
├─────────────────────┬───────────────────────────────────────┤
│  Category: [2D ▼]   │        Shape Visualization            │
│  Shape:   [Circle ▼]│                                       │
│                     │           ○○○○○                       │
│  Description:       │         ○○○○○○○○○                     │
│  A perfectly round  │        ○○○○○○○○○○○○                   │
│  2D shape where     │         ○○○○○○○○○○○                   │
│  all points are     │           ○○○○○○○○○                     │
│  equidistant from   │             ○○○○○                       │
│  the center.        │                                       │
├─────────────────────┤                                       │
│  Parameters:        ├───────────────────────────────────────┤
│  Radius: 5.00 cm    │            Results                    │
│                     │  ┌─────────────┐  ┌─────────────┐    │
│  [Calculate]        │  │    Area     │  │   Volume    │    │
│                     │  │  78.54 cm²  │  │     —       │    │
│                     │  └─────────────┘  └─────────────┘    │
└─────────────────────┴───────────────────────────────────────┘
```

## 🏗️ Project Structure

```
marksgeometrys-ui/
├── src/
│   └── marksgeometrys_ui/
│       ├── __init__.py          # Package initialization
│       ├── __main__.py          # Entry point
│       ├── main_window.py       # Main application window
│       ├── shapes.py            # Shape configurations & parameters
│       └── widgets.py           # Custom UI widgets
├── pyproject.toml               # Project configuration
├── README.md                    # This file
├── LICENSE                      # MIT License
└── .gitignore                   # Git ignore rules
```

## 🛠️ Development

### Requirements
- Python 3.8+
- PyQt6 6.6+
- marksgeometrys 0.1.1+

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black src/
ruff check src/
```

### Type Checking
```bash
mypy src/
```

## 📦 Building Distribution

```bash
pip install build
python -m build
```

This creates `dist/marksgeometrys_ui-0.1.0.tar.gz` and `dist/marksgeometrys_ui-0.1.0-py3-none-any.whl`

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m '✨ Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[marksgeometrys](https://pypi.org/project/marksgeometrys/)** — My geometry calculation library
- **[PyQt6](https://www.qt.io/)** — The GUI framework
- **Icons** — [Feather Icons](https://feathericons.com/)

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/marc1fino/marksgeometrys-ui/issues)
- **Discussions**: [GitHub Discussions](https://github.com/marc1fino/marksgeometrys-ui/discussions)
