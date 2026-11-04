"""Main application window for MarksGeometrys UI."""

import marksgeometrys
from typing import Dict, Optional
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QPushButton, QMessageBox, QStatusBar, QMenuBar,
    QMenu, QToolBar, QApplication, QGroupBox, QProgressBar,
    QSizePolicy, QStackedWidget, QGraphicsOpacityEffect
)
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, QPoint,
    QParallelAnimationGroup, QSequentialAnimationGroup,
    QAbstractAnimation, pyqtProperty
)
from PyQt6.QtGui import QAction, QIcon, QFont, QFontDatabase

from .widgets import (
    ShapeSelectorWidget, ParameterFormWidget,
    ShapeVisualizationWidget, GLVisualizationWidget, ResultsWidget
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
        self.setWindowTitle("MarksGeometrys - Geometry Calculator")
        self.setMinimumSize(800, 500)  # Smaller minimum for better fit on small screens
        self.resize(1100, 700)

        # Central widget with splitter
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)  # Smaller margins
        main_layout.setSpacing(8)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(3)
        splitter.setChildrenCollapsible(False)
        main_layout.addWidget(splitter)

        # Left panel - Controls
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)

        # Right panel - Visualization and Results
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)

        # Set initial splitter sizes (28% left, 72% right) - more space for visualization
        splitter.setSizes([300, 800])

        # Store splitter reference for resize handling
        self.main_splitter = splitter

        # Add entrance animation
        self._animate_entrance()

    def _create_left_panel(self) -> QWidget:
        """Create the left control panel."""
        panel = QWidget()
        panel.setMinimumWidth(280)  # Smaller minimum for better responsiveness
        panel.setMaximumWidth(380)  # Prevent panel from getting too wide
        panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(panel)
        layout.setSpacing(12)  # More compact spacing
        layout.setContentsMargins(0, 0, 0, 0)

        # Title with futuristic styling
        title = QLabel("MarksGeometrys")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setProperty("title", True)
        title.setStyleSheet(f"""
            font-family: {FONTS['display']};
            font-size: 24px;
            font-weight: 800;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00D4FF, stop:1 #7C4DFF);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            padding: 6px 0;
        """)
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Geometry Calculator")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setProperty("subtitle", True)
        subtitle.setStyleSheet("color: #94A3B8; font-size: 12px; margin-bottom: 2px;")
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
                padding: 12px;
                background: rgba(26, 35, 58, 0.8);
                border: 1px solid rgba(148, 163, 184, 0.15);
                border-radius: 8px;
                font-size: 12px;
                line-height: 1.5;
            }
        """)
        layout.addWidget(self.description_label)

        # Parameter form
        params_group = QGroupBox("Parameters")
        params_layout = QVBoxLayout(params_group)
        params_layout.setContentsMargins(10, 18, 10, 10)
        self.param_form = ParameterFormWidget()
        params_layout.addWidget(self.param_form)
        layout.addWidget(params_group, stretch=1)  # Allow form to expand

        # Calculate button with enhanced styling
        self.calc_button = QPushButton("Calculate Area / Volume")
        self.calc_button.setMinimumHeight(44)
        font = QFont(FONTS["display"])
        font.setPointSize(12)
        font.setWeight(QFont.Weight.DemiBold)
        self.calc_button.setFont(font)
        self.calc_button.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.calc_button)

        # Loading progress bar (hidden by default)
        self.loading_bar = QProgressBar()
        self.loading_bar.setProperty("loading", True)
        self.loading_bar.setRange(0, 0)  # Indeterminate
        self.loading_bar.setFixedHeight(3)
        self.loading_bar.setTextVisible(False)
        self.loading_bar.setVisible(False)
        self.loading_bar.setStyleSheet("""
            QProgressBar {
                background: rgba(26, 35, 58, 0.5);
                border: none;
                border-radius: 1.5px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00D4FF, stop:1 #7C4DFF);
                border-radius: 1.5px;
            }
        """)
        layout.addWidget(self.loading_bar)

        # Info label
        info = QLabel("Enter parameters and click Calculate to compute area and volume.")
        info.setWordWrap(True)
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setProperty("caption", True)
        info.setStyleSheet("color: #64748B; font-size: 10px; margin-top: 4px;")
        layout.addWidget(info)

        layout.addStretch()
        return panel

    def _create_right_panel(self) -> QWidget:
        """Create the right visualization and results panel."""
        panel = QWidget()
        panel.setMinimumWidth(400)  # Ensure right panel has enough space
        panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(panel)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        # Visualization - use stacked widget with smooth transitions
        viz_group = QGroupBox("Visualization")
        viz_layout = QVBoxLayout(viz_group)
        viz_layout.setContentsMargins(10, 18, 10, 10)

        # Custom animated stacked widget
        self.viz_stack = AnimatedStackedWidget()
        self.viz_stack.setMinimumHeight(300)
        self.viz_stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # 2D visualization widget (QPainter-based)
        self.viz_2d_widget = ShapeVisualizationWidget()
        self.viz_2d_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.viz_stack.addWidget(self.viz_2d_widget)

        # 3D visualization widget (OpenGL-based)
        self.viz_3d_widget = GLVisualizationWidget()
        self.viz_3d_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.viz_stack.addWidget(self.viz_3d_widget)

        # Default to 2D
        self.viz_stack.setCurrentIndex(0)

        viz_layout.addWidget(self.viz_stack)
        layout.addWidget(viz_group, stretch=3)  # More stretch for visualization

        # Results
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout(results_group)
        results_layout.setContentsMargins(10, 18, 10, 10)
        self.results_widget = ResultsWidget()
        self.results_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
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

    def _animate_entrance(self):
        """Animate the entrance of the main window elements."""
        # Fade in the main window
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity_effect)

        self._entrance_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._entrance_anim.setDuration(500)
        self._entrance_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._entrance_anim.setStartValue(0.0)
        self._entrance_anim.setEndValue(1.0)
        self._entrance_anim.start()

        # Remove effect after animation
        def cleanup():
            self.setGraphicsEffect(None)
        QTimer.singleShot(500, cleanup)

    def _connect_signals(self):
        """Connect widget signals."""
        self.shape_selector.shape_changed.connect(self._on_shape_changed)
        self.param_form.values_changed.connect(self._on_values_changed)
        self.calc_button.clicked.connect(self._calculate)

    def _start_status_pulse(self):
        """Start the pulsing animation for the status indicator using QPropertyAnimation."""
        # Create opacity effect for smooth pulse
        self._status_opacity_effect = QGraphicsOpacityEffect(self.status_indicator)
        self._status_opacity_effect.setOpacity(1.0)
        self.status_indicator.setGraphicsEffect(self._status_opacity_effect)

        # Create the pulse animation (fade in/out)
        self._pulse_animation = QPropertyAnimation(self._status_opacity_effect, b"opacity")
        self._pulse_animation.setDuration(1000)
        self._pulse_animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._pulse_animation.setStartValue(1.0)
        self._pulse_animation.setEndValue(0.3)
        self._pulse_animation.setLoopCount(-1)  # Infinite loop

        # Create a sequential group for continuous pulsing
        self._pulse_group = QSequentialAnimationGroup()
        self._pulse_group.addAnimation(self._pulse_animation)

        # Return animation
        pulse_back = QPropertyAnimation(self._status_opacity_effect, b"opacity")
        pulse_back.setDuration(1000)
        pulse_back.setEasingCurve(QEasingCurve.Type.InOutSine)
        pulse_back.setStartValue(0.3)
        pulse_back.setEndValue(1.0)
        self._pulse_group.addAnimation(pulse_back)

        self._pulse_group.setLoopCount(-1)
        self._pulse_group.start()

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

        # Switch between 2D and 3D visualization based on shape category
        is_3d = self.current_shape_config.category == "3D"
        if is_3d:
            self.viz_stack.setCurrentIndex(1)  # 3D widget
            self.viz_3d_widget.set_shape(self.current_shape_config, default_values)
        else:
            self.viz_stack.setCurrentIndex(0)  # 2D widget
            self.viz_2d_widget.set_shape(self.current_shape_config, default_values)

        # Clear results
        self.results_widget.set_results(None, None, is_3d, self.current_shape_config.name)

        # Update status
        self.status_message.setText(f"Selected: {self.current_shape_config.display_name}")
        self.shape_info_label.setText(f"{self.current_shape_config.category} Shape")

    def _on_values_changed(self, values: Dict[str, float]):
        """Handle parameter value changes."""
        self.current_values = values
        if self.current_shape_config:
            is_3d = self.current_shape_config.category == "3D"
            if is_3d:
                self.viz_3d_widget.set_shape(self.current_shape_config, values)
            else:
                self.viz_2d_widget.set_shape(self.current_shape_config, values)
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

            # Start button pulse animation
            self._start_button_pulse()
        else:
            self.calc_button.setText("Calculate Area / Volume")
            self._stop_button_pulse()

            # Restore pulse animation
            if hasattr(self, '_pulse_group'):
                self._pulse_group.start()

    def _start_button_pulse(self):
        """Start pulse animation on calculate button during calculation."""
        # Create color animation for button
        self._button_pulse_anim = QPropertyAnimation(self.calc_button, b"styleSheet")
        self._button_pulse_anim.setDuration(800)
        self._button_pulse_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._button_pulse_anim.setLoopCount(-1)

        # We'll use a simpler approach - animate the loading bar
        self._loading_anim = QPropertyAnimation(self.loading_bar, b"maximum")
        self._loading_anim.setDuration(1000)
        self._loading_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._loading_anim.setStartValue(0)
        self._loading_anim.setEndValue(100)
        self._loading_anim.setLoopCount(-1)
        self._loading_anim.start()

    def _stop_button_pulse(self):
        """Stop pulse animation on calculate button."""
        if hasattr(self, '_loading_anim') and self._loading_anim:
            self._loading_anim.stop()
            self._loading_anim = None
        if hasattr(self, '_button_pulse_anim') and self._button_pulse_anim:
            self._button_pulse_anim.stop()
            self._button_pulse_anim = None
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
            is_3d = self.current_shape_config.category == "3D"
            if is_3d:
                self.viz_3d_widget.set_shape(self.current_shape_config, default_values)
            else:
                self.viz_2d_widget.set_shape(self.current_shape_config, default_values)
            self.status_message.setText("Parameters reset to defaults")
            self.status_indicator.setProperty("status", "active")
            self.status_indicator.setStyleSheet("color: #00D4FF; font-size: 10px; padding-right: 12px;")

    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(self, "About MarksGeometrys UI",
            "<h3>MarksGeometrys UI</h3>"
            "<p>Visual interface for the <b>marksgeometrys</b> Python library.</p>"
            "<p>Calculate areas and volumes of 2D and 3D geometric shapes.</p>"
            "<p>Version 0.1.0</p>"
            "<p>Built with PyQt6</p>"
        )

    def _show_docs(self):
        """Show documentation/help."""
        QMessageBox.information(self, "Documentation",
            "MarksGeometrys UI uses the marksgeometrys library.\n\n"
            "1. Select a shape category (2D or 3D)\n"
            "2. Choose a specific shape\n"
            "3. Adjust the parameters\n"
            "4. Click 'Calculate Area / Volume'\n\n"
            "All measurements are in centimeters (cm).\n"
            "Areas are in cm², volumes in cm³."
        )


class AnimatedStackedWidget(QStackedWidget):
    """QStackedWidget with smooth fade/slide transitions between pages."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._animation = None
        self._current_widget = None
        self._next_widget = None
        self._animation_direction = 1  # 1 for forward, -1 for backward

    def setCurrentIndex(self, index: int):
        """Switch to the given index with smooth animation."""
        if index == self.currentIndex() or index < 0 or index >= self.count():
            super().setCurrentIndex(index)
            return

        # Stop any ongoing animation
        if self._animation and self._animation.state() == QAbstractAnimation.State.Running:
            self._animation.stop()

        current = self.currentWidget()
        next_widget = self.widget(index)

        # Prepare widgets for animation
        current_pos = current.pos()
        next_widget.setGeometry(self.rect())
        next_widget.show()
        next_widget.raise_()

        # Create opacity effects
        current_effect = QGraphicsOpacityEffect(current)
        current.setGraphicsEffect(current_effect)
        current_effect.setOpacity(1.0)

        next_effect = QGraphicsOpacityEffect(next_widget)
        next_widget.setGraphicsEffect(next_effect)
        next_effect.setOpacity(0.0)

        # Slide offset
        offset = 30 * self._animation_direction

        # Animation group for parallel animations
        self._animation = QParallelAnimationGroup()

        # Fade out current
        fade_out = QPropertyAnimation(current_effect, b"opacity")
        fade_out.setDuration(250)
        fade_out.setEasingCurve(QEasingCurve.Type.OutCubic)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)

        # Fade in next
        fade_in = QPropertyAnimation(next_effect, b"opacity")
        fade_in.setDuration(250)
        fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)

        # Slide current
        slide_out = QPropertyAnimation(current, b"pos")
        slide_out.setDuration(250)
        slide_out.setEasingCurve(QEasingCurve.Type.OutCubic)
        slide_out.setStartValue(current_pos)
        slide_out.setEndValue(QPoint(current_pos.x() - offset, current_pos.y()))

        # Slide next
        next_widget.move(current_pos.x() + offset, current_pos.y())
        slide_in = QPropertyAnimation(next_widget, b"pos")
        slide_in.setDuration(250)
        slide_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        slide_in.setStartValue(QPoint(current_pos.x() + offset, current_pos.y()))
        slide_in.setEndValue(current_pos)

        self._animation.addAnimation(fade_out)
        self._animation.addAnimation(fade_in)
        self._animation.addAnimation(slide_out)
        self._animation.addAnimation(slide_in)

        def on_finished():
            current.setGraphicsEffect(None)
            next_widget.setGraphicsEffect(None)
            current.hide()
            super(AnimatedStackedWidget, self).setCurrentIndex(index)
            self._animation = None

        self._animation.finished.connect(on_finished)
        self._animation.start()

        # Toggle direction for next transition
        self._animation_direction *= -1


def main():
    """Entry point for the application."""
    import sys
    app = QApplication(sys.argv)
    app.setApplicationName("MarksGeometrys UI")
    app.setOrganizationName("MarksGeometrys")

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