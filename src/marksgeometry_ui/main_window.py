"""Main application window for MarksGeometry UI."""

import marksgeometrys
from typing import Dict, Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QPushButton, QMessageBox, QStatusBar, QMenuBar,
    QMenu, QToolBar, QApplication
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QIcon, QFont

from .widgets import (
    ShapeSelectorWidget, ParameterFormWidget,
    ShapeVisualizationWidget, ResultsWidget
)
from .shapes import ShapeConfig, get_shape_config, ALL_SHAPES


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.current_shape_config: Optional[ShapeConfig] = None
        self.current_values: Dict[str, float] = {}
        self._setup_ui()
        self._setup_menu()
        self._setup_statusbar()
        self._connect_signals()

        # Set initial shape
        self.shape_selector.shape_changed.emit("circle")

    def _setup_ui(self):
        """Set up the main UI layout."""
        self.setWindowTitle("MarksGeometry - Geometry Calculator")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)

        # Central widget with splitter
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Left panel - Controls
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)

        # Right panel - Visualization and Results
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)

        # Set initial splitter sizes (40% left, 60% right)
        splitter.setSizes([450, 750])

    def _create_left_panel(self) -> QWidget:
        """Create the left control panel."""
        panel = QWidget()
        panel.setMaximumWidth(500)
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)

        # Title
        title = QLabel("Geometry Calculator")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        title.setFont(font)
        title.setStyleSheet("color: #1A237E; margin: 10px;")
        layout.addWidget(title)

        # Shape selector
        self.shape_selector = ShapeSelectorWidget()
        layout.addWidget(self.shape_selector)

        # Description
        self.description_label = QLabel()
        self.description_label.setWordWrap(True)
        self.description_label.setStyleSheet("color: #555; padding: 10px; background: #F5F5F5; border-radius: 5px;")
        layout.addWidget(self.description_label)

        # Parameter form
        params_group = QGroupBox("Parameters")
        params_layout = QVBoxLayout(params_group)
        self.param_form = ParameterFormWidget()
        params_layout.addWidget(self.param_form)
        layout.addWidget(params_group)

        # Calculate button
        self.calc_button = QPushButton("Calculate Area / Volume")
        self.calc_button.setMinimumHeight(45)
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.calc_button.setFont(font)
        self.calc_button.setStyleSheet("""
            QPushButton {
                background-color: #1A237E;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #283593;
            }
            QPushButton:pressed {
                background-color: #0D1B5E;
            }
        """)
        layout.addWidget(self.calc_button)

        # Info label
        info = QLabel("Enter parameters and click Calculate to compute area and volume.")
        info.setWordWrap(True)
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(info)

        layout.addStretch()
        return panel

    def _create_right_panel(self) -> QWidget:
        """Create the right visualization and results panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)

        # Visualization
        viz_group = QGroupBox("Shape Visualization")
        viz_layout = QVBoxLayout(viz_group)
        self.viz_widget = ShapeVisualizationWidget()
        self.viz_widget.setMinimumHeight(350)
        viz_layout.addWidget(self.viz_widget)
        layout.addWidget(viz_group, stretch=2)

        # Results
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout(results_group)
        self.results_widget = ResultsWidget()
        results_layout.addWidget(self.results_widget)
        layout.addWidget(results_group, stretch=1)

        return panel

    def _setup_menu(self):
        """Set up the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        reset_action = QAction("&Reset Parameters", self)
        reset_action.setShortcut("Ctrl+R")
        reset_action.triggered.connect(self._reset_parameters)
        view_menu.addAction(reset_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

        docs_action = QAction("&Documentation", self)
        docs_action.triggered.connect(self._show_docs)
        help_menu.addAction(docs_action)

    def _setup_statusbar(self):
        """Set up the status bar."""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Ready - Select a shape and enter parameters")

    def _connect_signals(self):
        """Connect widget signals."""
        self.shape_selector.shape_changed.connect(self._on_shape_changed)
        self.param_form.values_changed.connect(self._on_values_changed)
        self.calc_button.clicked.connect(self._calculate)

    def _on_shape_changed(self, shape_name: str):
        """Handle shape selection change."""
        self.current_shape_config = get_shape_config(shape_name)
        if not self.current_shape_config:
            return

        # Update description
        self.description_label.setText(self.current_shape_config.description)

        # Update parameter form
        self.param_form.set_shape(self.current_shape_config)

        # Update visualization with default values
        default_values = {p.name: p.default or 0 for p in self.current_shape_config.parameters}
        self.current_values = default_values
        self.viz_widget.set_shape(self.current_shape_config, default_values)

        # Clear results
        self.results_widget.set_results(None, None, self.current_shape_config.category == "3D")

        # Update status
        self.statusbar.showMessage(f"Selected: {self.current_shape_config.display_name}")

    def _on_values_changed(self, values: Dict[str, float]):
        """Handle parameter value changes."""
        self.current_values = values
        if self.current_shape_config:
            self.viz_widget.set_shape(self.current_shape_config, values)

    def _calculate(self):
        """Calculate area and/or volume for the current shape."""
        if not self.current_shape_config:
            QMessageBox.warning(self, "No Shape", "Please select a shape first.")
            return

        try:
            # Get the class from marksgeometrys
            cls = getattr(marksgeometrys, self.current_shape_config.class_name)

            # Create instance with current values
            instance = cls(**self.current_values)

            # Calculate area
            area = None
            if self.current_shape_config.has_area:
                area = instance.area()

            # Calculate volume (note: Sphere uses 'volum' not 'volume')
            volume = None
            if self.current_shape_config.has_volume:
                if hasattr(instance, 'volume'):
                    volume = instance.volume()
                elif hasattr(instance, 'volum'):
                    volume = instance.volum()

            # Update results
            self.results_widget.set_results(area, volume, self.current_shape_config.category == "3D")

            # Update status
            msg = f"Calculated: Area = {area:,.2f} cm²" if area is not None else "Calculated"
            if volume is not None:
                msg += f", Volume = {volume:,.2f} cm³"
            self.statusbar.showMessage(msg)

        except Exception as e:
            QMessageBox.critical(self, "Calculation Error", f"Error calculating: {str(e)}")
            self.statusbar.showMessage("Calculation failed")

    def _reset_parameters(self):
        """Reset parameters to defaults."""
        if self.current_shape_config:
            default_values = {p.name: p.default or 0 for p in self.current_shape_config.parameters}
            for name, value in default_values.items():
                # Find and update the corresponding widget
                for widget in self.param_form.parameter_widgets:
                    if widget.parameter.name == name:
                        widget.set_value(value)
            self.current_values = default_values
            self.viz_widget.set_shape(self.current_shape_config, default_values)
            self.statusbar.showMessage("Parameters reset to defaults")

    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(self, "About MarksGeometry UI",
            "<h3>MarksGeometry UI</h3>"
            "<p>Visual interface for the <b>marksgeometrys</b> Python library.</p>"
            "<p>Calculate areas and volumes of 2D and 3D geometric shapes.</p>"
            "<p>Version 0.1.0</p>"
            "<p>Built with PyQt6</p>"
        )

    def _show_docs(self):
        """Show documentation/help."""
        QMessageBox.information(self, "Documentation",
            "MarksGeometry UI uses the marksgeometrys library.\n\n"
            "1. Select a shape category (2D or 3D)\n"
            "2. Choose a specific shape\n"
            "3. Adjust the parameters\n"
            "4. Click 'Calculate Area / Volume'\n\n"
            "All measurements are in centimeters (cm).\n"
            "Areas are in cm², volumes in cm³."
        )


def main():
    """Entry point for the application."""
    import sys
    app = QApplication(sys.argv)
    app.setApplicationName("MarksGeometry UI")
    app.setOrganizationName("MarksGeometry")

    # Set application font
    font = QFont("Segoe UI", 9)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())