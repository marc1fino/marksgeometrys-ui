"""Main application window for MarksGeometry UI."""

import marksgeometrys
from typing import Dict, Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QPushButton, QMessageBox, QStatusBar, QMenuBar,
    QMenu, QToolBar, QApplication, QGroupBox, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QAction, QIcon, QFont, QFontDatabase

from .widgets import (
    ShapeSelectorWidget, ParameterFormWidget,
    ShapeVisualizationWidget, ResultsWidget
)
from .shapes import ShapeConfig, get_shape_config, ALL_SHAPES
from .theme import get_dark_theme_stylesheet, FONTS


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.current_shape_config: Optional[ShapeConfig] = None
        self.current_values: Dict[str, float] = {}
        self._calculation_in_progress = False

        # Apply futuristic theme
        self.setStyleSheet(get_dark_theme_stylesheet())

        self._setup_ui()
        self._setup_menu()
        self._setup_statusbar()
        self._connect_signals()

        # Set initial shape
        self.shape_selector.shape_changed.emit("circle")

    def _setup_ui(self):
        """Set up the main UI layout."""
        self.setWindowTitle("MarksGeometry - Geometry Calculator")
        self.setMinimumSize(1100, 750)
        self.resize(1300, 850)

        # Central widget with splitter
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(3)
        main_layout.addWidget(splitter)

        # Left panel - Controls
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)

        # Right panel - Visualization and Results
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)

        # Set initial splitter sizes (35% left, 65% right)
        splitter.setSizes([450, 850])

    def _create_left_panel(self) -> QWidget:
        """Create the left control panel."""
        panel = QWidget()
        panel.setMaximumWidth(480)
        panel.setMinimumWidth(400)
        layout = QVBoxLayout(panel)
        layout.setSpacing(20)
        layout.setContentsMargins(0, 0, 0, 0)

        # Title with futuristic styling
        title = QLabel("MarksGeometry")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setProperty("title", True)
        title.setStyleSheet(f"""
            font-family: {FONTS['display']};
            font-size: 32px;
            font-weight: 800;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00D4FF, stop:1 #7C4DFF);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            padding: 10px 0;
        """)
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Geometry Calculator")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setProperty("subtitle", True)
        subtitle.setStyleSheet("color: #94A3B8; font-size: 14px; margin-bottom: 8px;")
        layout.addWidget(subtitle)

        # Shape selector
        self.shape_selector = ShapeSelectorWidget()
        layout.addWidget(self.shape_selector)

        # Description card
        self.description_label = QLabel()
        self.description_label.setWordWrap(True)
        self.description_label.setStyleSheet("""
            QLabel {
                color: #94A3B8;
                padding: 16px;
                background: rgba(26, 35, 58, 0.8);
                border: 1px solid rgba(148, 163, 184, 0.15);
                border-radius: 10px;
                font-size: 13px;
                line-height: 1.5;
            }
        """)
        layout.addWidget(self.description_label)

        # Parameter form
        params_group = QGroupBox("Parameters")
        params_layout = QVBoxLayout(params_group)
        params_layout.setContentsMargins(16, 24, 16, 16)
        self.param_form = ParameterFormWidget()
        params_layout.addWidget(self.param_form)
        layout.addWidget(params_group)

        # Calculate button with enhanced styling
        self.calc_button = QPushButton("Calculate Area / Volume")
        self.calc_button.setMinimumHeight(52)
        font = QFont(FONTS["display"])
        font.setPointSize(14)
        font.setWeight(QFont.Weight.DemiBold)
        self.calc_button.setFont(font)
        self.calc_button.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.calc_button)

        # Loading progress bar (hidden by default)
        self.loading_bar = QProgressBar()
        self.loading_bar.setProperty("loading", True)
        self.loading_bar.setRange(0, 0)  # Indeterminate
        self.loading_bar.setFixedHeight(4)
        self.loading_bar.setTextVisible(False)
        self.loading_bar.setVisible(False)
        self.loading_bar.setStyleSheet("""
            QProgressBar {
                background: rgba(26, 35, 58, 0.5);
                border: none;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00D4FF, stop:1 #7C4DFF);
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.loading_bar)

        # Info label
        info = QLabel("Enter parameters and click Calculate to compute area and volume.")
        info.setWordWrap(True)
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setProperty("caption", True)
        info.setStyleSheet("color: #64748B; font-size: 11px; margin-top: 8px;")
        layout.addWidget(info)

        layout.addStretch()
        return panel

    def _create_right_panel(self) -> QWidget:
        """Create the right visualization and results panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)

        # Visualization
        viz_group = QGroupBox("Shape Visualization")
        viz_layout = QVBoxLayout(viz_group)
        viz_layout.setContentsMargins(16, 24, 16, 16)
        self.viz_widget = ShapeVisualizationWidget()
        self.viz_widget.setMinimumHeight(400)
        viz_layout.addWidget(self.viz_widget)
        layout.addWidget(viz_group, stretch=2)

        # Results
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout(results_group)
        results_layout.setContentsMargins(16, 24, 16, 16)
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
        """Set up the status bar with animated indicators."""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        # Main status message
        self.status_message = QLabel("Ready - Select a shape and enter parameters")
        self.status_message.setProperty("caption", True)
        self.status_message.setStyleSheet("color: #94A3B8; padding: 4px 12px;")
        self.statusbar.addWidget(self.status_message, 1)

        # Status indicator dot
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("color: #00D4FF; font-size: 10px; padding-right: 12px;")
        self.status_indicator.setProperty("status", "active")
        self.statusbar.addPermanentWidget(self.status_indicator)

        # Shape info label
        self.shape_info_label = QLabel("")
        self.shape_info_label.setProperty("caption", True)
        self.shape_info_label.setStyleSheet("color: #64748B; padding-right: 16px;")
        self.statusbar.addPermanentWidget(self.shape_info_label)

        # Start pulse animation for status indicator
        self._start_status_pulse()

    def _connect_signals(self):
        """Connect widget signals."""
        self.shape_selector.shape_changed.connect(self._on_shape_changed)
        self.param_form.values_changed.connect(self._on_values_changed)
        self.calc_button.clicked.connect(self._calculate)

    def _start_status_pulse(self):
        """Start the pulsing animation for the status indicator."""
        self._pulse_timer = QTimer()
        self._pulse_timer.timeout.connect(self._pulse_status_indicator)
        self._pulse_timer.start(1000)  # Pulse every second
        self._pulse_state = True

    def _pulse_status_indicator(self):
        """Pulse the status indicator."""
        if hasattr(self, 'status_indicator'):
            if self._pulse_state:
                self.status_indicator.setStyleSheet("color: #00D4FF; font-size: 10px; padding-right: 12px;")
            else:
                self.status_indicator.setStyleSheet("color: rgba(0, 212, 255, 0.4); font-size: 10px; padding-right: 12px;")
            self._pulse_state = not self._pulse_state

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
        self.results_widget.set_results(None, None, self.current_shape_config.category == "3D", self.current_shape_config.name)

        # Update status
        self.status_message.setText(f"Selected: {self.current_shape_config.display_name}")
        self.shape_info_label.setText(f"{self.current_shape_config.category} Shape")

    def _on_values_changed(self, values: Dict[str, float]):
        """Handle parameter value changes."""
        self.current_values = values
        if self.current_shape_config:
            self.viz_widget.set_shape(self.current_shape_config, values)
            # Update status with current parameter preview
            param_str = ", ".join([f"{k}={v:.1f}" for k, v in values.items()])
            self.status_message.setText(f"Parameters: {param_str}")

    def _calculate(self):
        """Calculate area and/or volume for the current shape."""
        if not self.current_shape_config:
            QMessageBox.warning(self, "No Shape", "Please select a shape first.")
            return

        # Show loading state
        self._set_calculating(True)

        # Use a timer to allow UI to update before calculation
        QTimer.singleShot(50, self._perform_calculation)

    def _perform_calculation(self):
        """Perform the actual calculation (called after UI updates)."""
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
            self.results_widget.set_results(area, volume, self.current_shape_config.category == "3D", self.current_shape_config.name)

            # Update status - parse values to handle string results from marksgeometrys
            def parse_val(v):
                if v is None:
                    return None
                if isinstance(v, (int, float)):
                    return float(v)
                if isinstance(v, str):
                    import re
                    match = re.match(r'^([\d.]+)', v.strip())
                    if match:
                        return float(match.group(1))
                return None

            area_val = parse_val(area)
            volume_val = parse_val(volume)

            # Build status message with clear labels
            parts = []
            if area_val is not None:
                parts.append(f"Area = {area_val:,.2f} cm²")
            if volume_val is not None:
                parts.append(f"Volume = {volume_val:,.2f} cm³")

            if parts:
                msg = "Calculated: " + ", ".join(parts)
            else:
                msg = "Calculated"

            self.status_message.setText(msg)
            self.status_indicator.setProperty("status", "success")
            self.status_indicator.setStyleSheet("color: #10B981; font-size: 10px; padding-right: 12px;")
            self.shape_info_label.setText(f"{self.current_shape_config.display_name}")

        except Exception as e:
            QMessageBox.critical(self, "Calculation Error", f"Error calculating: {str(e)}")
            self.status_message.setText("Calculation failed")
            self.status_indicator.setProperty("status", "error")
            self.status_indicator.setStyleSheet("color: #EF4444; font-size: 10px; padding-right: 12px;")

        finally:
            self._set_calculating(False)

    def _set_calculating(self, calculating: bool):
        """Set the calculating state with loading animation."""
        self._calculation_in_progress = calculating
        self.calc_button.setEnabled(not calculating)
        self.loading_bar.setVisible(calculating)

        if calculating:
            self.calc_button.setText("Calculating...")
            self.status_message.setText("Calculating...")
            self.status_indicator.setProperty("status", "warning")
            self.status_indicator.setStyleSheet("color: #F59E0B; font-size: 10px; padding-right: 12px;")
        else:
            self.calc_button.setText("Calculate Area / Volume")

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
            self.status_message.setText("Parameters reset to defaults")
            self.status_indicator.setProperty("status", "active")
            self.status_indicator.setStyleSheet("color: #00D4FF; font-size: 10px; padding-right: 12px;")

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
    font = QFont(FONTS["primary"])
    font.setPointSize(10)
    app.setFont(font)

    # Set application-wide style (already applied per-window in MainWindow.__init__)
    # This ensures any dialogs also get the theme
    app.setStyleSheet(get_dark_theme_stylesheet())

    window = MainWindow()
    window.show()

    sys.exit(app.exec())