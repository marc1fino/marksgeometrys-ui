"""A restrained desktop workspace for the marksgeometrys Python library."""

import sys
from typing import Dict, Optional

from PyQt6.QtCore import QEasingCurve, QPoint, QPointF, QPropertyAnimation, QRectF, Qt, QTimer
from PyQt6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPalette, QPen, QPixmap, QPolygonF
from PyQt6.QtWidgets import (
    QApplication, QComboBox, QFrame, QHBoxLayout, QLabel, QMainWindow, QMenu,
    QMessageBox, QPushButton, QScrollArea, QSizePolicy, QSplitter, QStackedWidget,
    QStatusBar, QVBoxLayout, QWidget,
)

from .calculations import LIBRARY_LABEL, LibraryCalculationError, calculate_shape
from .shapes import ShapeConfig, get_shape_config
from .theme import FONTS, get_light_theme_stylesheet
from .widgets import (
    GLVisualizationWidget, ParameterFormWidget, ResultsWidget, SHAPE_NAMES,
    ShapeSelectorWidget, ShapeVisualizationWidget,
)


def label(text: str, role: str) -> QLabel:
    widget = QLabel(text)
    widget.setObjectName(role)
    return widget


class BrandMark(QWidget):
    """A small folded-square wordmark, drawn as resolution-independent linework."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(36, 36)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor("#2028FF"), 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPolygon(QPolygonF([
            QPointF(3, 3), QPointF(32, 3), QPointF(32, 32),
            QPointF(8, 32), QPointF(3, 27),
        ]))
        painter.drawPolyline(QPolygonF([QPointF(3, 27), QPointF(8, 27), QPointF(8, 32)]))
        font = QFont("Arial")
        font.setPixelSize(17)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(QRectF(3, 2, 29, 29), Qt.AlignmentFlag.AlignCenter, "M")


class MainWindow(QMainWindow):
    """Keep calculations in the library and visual exploration in the viewports."""

    def __init__(self):
        super().__init__()
        self.current_shape_config: Optional[ShapeConfig] = None
        self.current_values: Dict[str, float] = {}
        self._calculation_in_progress = False
        self._motion_enabled = True
        self.setWindowTitle("MarksGeometrys")
        self.setMinimumSize(760, 580)
        self.resize(1220, 820)
        self.setStyleSheet(get_light_theme_stylesheet())
        self._setup_ui()
        self._setup_actions()
        self._connect_signals()
        self._on_shape_changed("circle")
        self._toggle_grid(False)
        QTimer.singleShot(0, self._animate_entrance)

    def _setup_ui(self):
        central = QWidget()
        central.setObjectName("Workspace")
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._create_topbar())
        content = QWidget()
        self.body_layout = QVBoxLayout(content)
        self.body_layout.setContentsMargins(40, 32, 40, 18)
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setChildrenCollapsible(False)
        self.main_splitter.setHandleWidth(36)
        self.controls_panel = self._create_left_panel()
        self.main_splitter.addWidget(self.controls_panel)
        self.main_splitter.addWidget(self._create_right_panel())
        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 1)
        self.main_splitter.setSizes([254, 850])
        self.body_layout.addWidget(self.main_splitter)
        outer.addWidget(content, 1)
        self.statusbar = QStatusBar()
        self.statusbar.setSizeGripEnabled(True)
        self.setStatusBar(self.statusbar)
        self.status_message = label("Ready", "Muted")
        self.statusbar.addWidget(self.status_message, 1)
        self.shape_info_label = label("cm  /  cm²  /  cm³", "Muted")
        self.statusbar.addPermanentWidget(self.shape_info_label)

    def _create_topbar(self):
        bar = QFrame()
        bar.setObjectName("TopBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(40, 18, 40, 18)
        layout.setSpacing(12)
        layout.addWidget(BrandMark())
        layout.addWidget(label("MarksGeometrys", "Brand"))
        layout.addStretch()
        layout.addWidget(label("Workspace", "ActiveNavigation"))
        layout.addSpacing(20)
        for title, callback in (("Guide", self._show_docs), ("About", self._show_about)):
            button = QPushButton(title)
            button.setObjectName("Navigation")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(callback)
            layout.addWidget(button)
            layout.addSpacing(12)
        self.preferences_menu = QMenu(self)
        self.preferences_button = QPushButton("Preferences")
        self.preferences_button.setObjectName("Navigation")
        self.preferences_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.preferences_button.clicked.connect(self._show_preferences)
        layout.addWidget(self.preferences_button)
        return bar

    def _create_left_panel(self):
        panel = QFrame()
        panel.setObjectName("Card")
        panel.setMinimumWidth(228)
        panel.setMaximumWidth(300)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        self.controls_scroll = QScrollArea()
        self.controls_scroll.setWidgetResizable(True)
        self.controls_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_content = QWidget()
        fields_layout = QVBoxLayout(scroll_content)
        fields_layout.setContentsMargins(0, 0, 6, 8)
        fields_layout.setSpacing(18)
        self.shape_selector = ShapeSelectorWidget()
        fields_layout.addWidget(self.shape_selector)
        self.description_label = label("", "Description")
        self.description_label.setWordWrap(True)
        fields_layout.addWidget(self.description_label)
        self.parameter_heading = label("Parameters", "SectionLabel")
        fields_layout.addWidget(self.parameter_heading)
        self.param_form = ParameterFormWidget()
        self.param_form.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.param_form.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        fields_layout.addWidget(self.param_form)
        self.error_label = label("", "Error")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        fields_layout.addWidget(self.error_label)
        fields_layout.addStretch(1)
        self.controls_scroll.setWidget(scroll_content)
        layout.addWidget(self.controls_scroll, 1)
        self.calc_button = QPushButton("Calculate")
        self.calc_button.setObjectName("PrimaryButton")
        self.calc_button.setMinimumHeight(44)
        self.calc_button.setToolTip("Calculate with marksgeometrys (Ctrl+Enter)")
        self.calc_button.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.calc_button)
        self.reset_button = QPushButton("Reset parameters")
        self.reset_button.setObjectName("GhostButton")
        self.reset_button.setToolTip("Restore the initial dimensions (Ctrl+R)")
        self.reset_button.clicked.connect(self._reset_parameters)
        layout.addWidget(self.reset_button)
        return panel

    def _create_right_panel(self):
        panel = QWidget()
        panel.setObjectName("PanelContent")
        panel.setMinimumWidth(380)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(22)
        self.viewer_card = QFrame()
        self.viewer_card.setObjectName("ViewerCard")
        viewer_layout = QVBoxLayout(self.viewer_card)
        viewer_layout.setContentsMargins(0, 0, 0, 0)
        viewer_layout.setSpacing(12)
        title_row = QHBoxLayout()
        title_row.setSpacing(10)
        self.viewer_title = label("Circle", "Heading")
        self.viewer_title.setWordWrap(True)
        self.viewer_title.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        title_row.addWidget(self.viewer_title, 1)
        self.dimension_badge = label("2D", "DimensionBadge")
        title_row.addWidget(self.dimension_badge)
        title_row.addSpacing(16)
        self.measurement_combo = QComboBox()
        self.measurement_combo.setObjectName("MeasurementPicker")
        self.measurement_combo.setAccessibleName("Measurement view")
        self.measurement_combo.setToolTip("Show dimensions, highlight area, or explore volume")
        for title, mode in (("Dimensions", "dimensions"), ("Area", "area"), ("Volume", "volume")):
            self.measurement_combo.addItem(title, mode)
        self.measurement_combo.setMinimumContentsLength(10)
        title_row.addWidget(self.measurement_combo)
        viewer_layout.addLayout(title_row)
        self.viz_stack = QStackedWidget()
        self.viz_stack.setMinimumHeight(200)
        self.viz_stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.viz_2d_widget = ShapeVisualizationWidget()
        self.viz_3d_widget = GLVisualizationWidget()
        self.viz_stack.addWidget(self.viz_2d_widget)
        self.viz_stack.addWidget(self.viz_3d_widget)
        viewer_layout.addWidget(self.viz_stack, 1)
        self.measurement_help = label("", "Description")
        self.measurement_help.setWordWrap(True)
        self.measurement_help.setMinimumHeight(30)
        viewer_layout.addWidget(self.measurement_help)
        self.viewer_toolbar = QWidget()
        tools = QHBoxLayout(self.viewer_toolbar)
        tools.setContentsMargins(0, 0, 0, 0)
        tools.setSpacing(5)
        self.viewer_hint = label("Drag to pan · Scroll to zoom", "Muted")
        self.viewer_hint.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        tools.addWidget(self.viewer_hint, 1)
        self.grid_button = self._tool("Grid", "Show the construction grid", True)
        self.grid_button.toggled.connect(self._toggle_grid)
        tools.addWidget(self.grid_button)
        self.rotate_button = self._tool("Rotate", "Rotate the 3D model automatically", True)
        self.rotate_button.toggled.connect(self._toggle_rotation)
        tools.addWidget(self.rotate_button)
        self.reset_view_button = self._tool("Reset view", "Reset the camera (Ctrl+0)")
        self.reset_view_button.clicked.connect(self._reset_view)
        tools.addWidget(self.reset_view_button)
        viewer_layout.addWidget(self.viewer_toolbar)
        layout.addWidget(self.viewer_card, 1)
        self.results_widget = ResultsWidget()
        layout.addWidget(self.results_widget)
        return panel

    def _tool(self, text, tooltip, checkable=False):
        button = QPushButton(text)
        button.setObjectName("ToolButton")
        button.setToolTip(tooltip)
        button.setAccessibleName(tooltip)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setCheckable(checkable)
        return button

    def _setup_actions(self):
        for text, shortcut, callback in (
            ("Calculate", "Ctrl+Return", self._calculate),
            ("Reset parameters", "Ctrl+R", self._reset_parameters),
            ("Reset view", "Ctrl+0", self._reset_view),
            ("Guide", "F1", self._show_docs),
            ("Close", "Ctrl+Q", self.close),
        ):
            action = QAction(text, self)
            action.setShortcut(shortcut)
            action.triggered.connect(callback)
            self.addAction(action)
        self.motion_button = QAction("Animations", self)
        self.motion_button.setCheckable(True)
        self.motion_button.setChecked(True)
        self.motion_button.toggled.connect(self._set_motion_enabled)
        self.preferences_menu.addAction(self.motion_button)
        self.dimensions_button = QAction("Dimension labels", self)
        self.dimensions_button.setCheckable(True)
        self.dimensions_button.setChecked(True)
        self.dimensions_button.toggled.connect(self._toggle_dimensions)
        self.preferences_menu.addAction(self.dimensions_button)
        self.wireframe_button = QAction("Wireframe", self)
        self.wireframe_button.setCheckable(True)
        self.wireframe_button.toggled.connect(self.viz_3d_widget.set_wireframe)
        self.preferences_menu.addAction(self.wireframe_button)

    def _connect_signals(self):
        self.shape_selector.shape_changed.connect(self._on_shape_changed)
        self.param_form.values_changed.connect(self._on_values_changed)
        self.calc_button.clicked.connect(self._calculate)
        self.measurement_combo.currentIndexChanged.connect(self._on_measurement_mode_changed)

    def _on_shape_changed(self, shape_name):
        config = get_shape_config(shape_name)
        if config is None:
            return
        self.current_shape_config = config
        self.param_form.blockSignals(True)
        self.param_form.set_shape(config)
        self.param_form.blockSignals(False)
        form_height = sum(field.sizeHint().height() for field in self.param_form.parameter_widgets)
        form_height += max(0, len(config.parameters) - 1) * 14 + 8
        self.param_form.setFixedHeight(max(78, form_height))
        self.controls_scroll.verticalScrollBar().setValue(0)
        self.current_values = self.param_form.get_values()
        self.description_label.setText(config.description)
        self.viewer_title.setText(SHAPE_NAMES.get(config.name, config.display_name))
        is_3d = config.category == "3D"
        self.viz_stack.setCurrentIndex(int(is_3d))
        self._active_viewer().set_shape(config, self.current_values)
        self.rotate_button.setVisible(is_3d)
        self.wireframe_button.setVisible(is_3d)
        self.dimension_badge.setText(config.category)
        self.viewer_hint.setText("Drag to orbit · Scroll to zoom" if is_3d else "Drag to pan · Scroll to zoom")
        self._on_measurement_mode_changed()
        self._clear_results()
        self.status_message.setText("Ready")

    def _on_values_changed(self, values):
        self.current_values = values.copy()
        if self.current_shape_config:
            self._active_viewer().set_shape(self.current_shape_config, values)
            self._clear_results()
            self.status_message.setText("Dimensions changed")

    def _on_measurement_mode_changed(self, index=None):
        mode = self.measurement_combo.currentData()
        for viewer in (self.viz_2d_widget, self.viz_3d_widget):
            viewer.set_measurement_mode(mode)
        is_3d = self.current_shape_config is not None and self.current_shape_config.category == "3D"
        self.wireframe_button.setEnabled(is_3d and mode == "dimensions")
        if mode == "area":
            explanation = ("A · Surface area covers all the outside faces of the solid. Measured in cm²."
                           if is_3d else "A · Area counts square units across the enclosed surface, measured in cm².")
        elif mode == "volume":
            explanation = ("V · Volume is the space inside the solid. The layers reveal its interior. Measured in cm³."
                           if is_3d else "A plane figure has no volume. A 1 cm × 1 cm × 1 cm cube represents 1 cm³.")
        else:
            explanation = ""
        self.measurement_help.setText(explanation)
        self.measurement_help.setVisible(bool(explanation))

    def _clear_results(self):
        if self.current_shape_config:
            self.results_widget.set_results(None, None,
                self.current_shape_config.category == "3D", self.current_shape_config.name)
        self.error_label.hide()

    def _active_viewer(self):
        return self.viz_stack.currentWidget()

    def _calculate(self):
        if self.current_shape_config is None or self._calculation_in_progress:
            return
        self._calculation_in_progress = True
        self.calc_button.setEnabled(False)
        self.error_label.hide()
        config = self.current_shape_config
        try:
            for field in self.param_form.parameter_widgets:
                field.spinbox.interpretText()
            self.current_values = self.param_form.get_values()
            area, volume = calculate_shape(config, self.current_values)
            self.results_widget.set_results(area, volume, config.category == "3D", config.name)
            self.status_message.setText("Calculated by " + LIBRARY_LABEL)
        except LibraryCalculationError as exc:
            self.results_widget.set_results(exc.area, exc.volume, config.category == "3D", config.name)
            self.error_label.setText(str(exc))
            self.error_label.show()
            self.controls_scroll.ensureWidgetVisible(self.error_label)
            self.status_message.setText("Calculation unavailable in " + LIBRARY_LABEL)
        except Exception as exc:
            self.results_widget.set_results(None, None, config.category == "3D", config.name)
            self.error_label.setText("Check the parameters: " + str(exc))
            self.error_label.show()
            self.controls_scroll.ensureWidgetVisible(self.error_label)
            self.status_message.setText("Calculation could not be completed")
        finally:
            self._calculation_in_progress = False
            self.calc_button.setEnabled(True)

    def _reset_parameters(self):
        if self.current_shape_config:
            self._on_shape_changed(self.current_shape_config.name)
            self._reset_view()

    def _reset_view(self):
        self._active_viewer().reset_view()

    def _toggle_grid(self, visible):
        for viewer in (self.viz_2d_widget, self.viz_3d_widget):
            viewer.set_grid_visible(visible)

    def _toggle_dimensions(self, visible):
        for viewer in (self.viz_2d_widget, self.viz_3d_widget):
            viewer.set_dimensions_visible(visible)

    def _toggle_rotation(self, enabled):
        self.viz_3d_widget.set_auto_rotate(enabled and self._motion_enabled)

    def _set_motion_enabled(self, enabled):
        self._motion_enabled = enabled
        if not enabled and hasattr(self, "_entrance"):
            self._entrance.stop()
            self.setWindowOpacity(1.0)
        for viewer in (self.viz_2d_widget, self.viz_3d_widget):
            viewer.set_animations_enabled(enabled)
        self.results_widget.set_animations_enabled(enabled)
        self._toggle_rotation(self.rotate_button.isChecked())

    def _animate_entrance(self):
        if self._motion_enabled and self.isVisible():
            self._entrance = QPropertyAnimation(self, b"windowOpacity", self)
            self._entrance.setDuration(340)
            self._entrance.setStartValue(0.0)
            self._entrance.setEndValue(1.0)
            self._entrance.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._entrance.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "body_layout"):
            compact = self.width() < 1000
            margin = 22 if compact else 40
            self.body_layout.setContentsMargins(margin, 22 if compact else 32, margin, 12)
            self.main_splitter.setHandleWidth(24 if compact else 36)
            self.viewer_hint.setVisible(self.width() >= 900)
            for viewer in (self.viz_stack, self.viz_2d_widget, self.viz_3d_widget):
                viewer.setMinimumHeight(140 if self.height() < 700 else 200)

    def _show_preferences(self):
        self.preferences_menu.popup(self.preferences_button.mapToGlobal(QPoint(0, self.preferences_button.height())))

    def _show_docs(self):
        QMessageBox.information(self, "Guide",
            "Choose a 2D or 3D shape, adjust its dimensions, then select Calculate.\n\n"
            "The Dimensions view labels each length directly on the figure.\n"
            "Area highlights the enclosed surface or the outside faces.\n"
            "Volume reveals interior layers; plane figures have no volume.\n\n"
            "Drag to pan in 2D or orbit in 3D. Scroll to zoom.\n"
            "Preferences includes animations, dimension labels and wireframe.\n\n"
            "Ctrl+Enter: calculate · Ctrl+R: reset parameters\n"
            "Ctrl+0: reset view · Ctrl+Q: close\n\n"
            "All area and volume results come directly from " + LIBRARY_LABEL + ".")

    def _show_about(self):
        QMessageBox.information(self, "About MarksGeometrys",
            "MarksGeometrys\n\nA visual interface for the marksgeometrys Python library.\n\n"
            "Calculation engine: " + LIBRARY_LABEL + "\n"
            "The interface displays the library's outputs without replacement formulas.\n\n"
            "Lengths: cm · Areas: cm² · Volumes: cm³")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("MarksGeometrys")
    app.setOrganizationName("MarksGeometrys")
    app.setStyle("Fusion")
    # Native popup frames also need a light palette when Windows uses dark mode.
    palette = app.palette()
    for role, color in (
        (QPalette.ColorRole.Window, "#FFFFFF"),
        (QPalette.ColorRole.Base, "#FFFFFF"),
        (QPalette.ColorRole.Button, "#FFFFFF"),
        (QPalette.ColorRole.WindowText, "#242434"),
        (QPalette.ColorRole.Text, "#242434"),
        (QPalette.ColorRole.ButtonText, "#242434"),
        (QPalette.ColorRole.Highlight, "#E8E9FF"),
        (QPalette.ColorRole.HighlightedText, "#2028FF"),
    ):
        palette.setColor(role, QColor(color))
    app.setPalette(palette)
    app.setFont(QFont(FONTS["primary"], 10))
    app.setStyleSheet(get_light_theme_stylesheet())
    mark = BrandMark()
    icon = QPixmap(36, 36)
    icon.fill(Qt.GlobalColor.transparent)
    mark.render(icon)
    app.setWindowIcon(QIcon(icon))
    window = MainWindow()
    screen = app.primaryScreen()
    if screen:
        available = screen.availableGeometry()
        window.resize(min(1220, available.width() - 32), min(820, available.height() - 48))
        window.move(available.center() - window.rect().center())
    window.show()
    sys.exit(app.exec())
