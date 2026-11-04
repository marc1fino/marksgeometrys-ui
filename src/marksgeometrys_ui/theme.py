"""Futuristic theme for MarksGeometrys UI - QSS Stylesheets."""

# Futuristic color palette
COLORS = {
    # Primary accent colors (cyan/blue)
    "primary": "#00D4FF",          # Bright cyan
    "primary_dark": "#00A8CC",     # Darker cyan
    "primary_light": "#66E0FF",    # Light cyan
    "primary_glow": "#00D4FF",     # Glow color

    # Secondary accent
    "secondary": "#7C4DFF",        # Deep purple
    "secondary_dark": "#5E35B1",
    "secondary_light": "#B388FF",

    # Background colors (Dark theme)
    "bg_primary": "#0A0E1A",       # Deep dark blue-black
    "bg_secondary": "#111827",     # Card background
    "bg_tertiary": "#1A233A",      # Elevated surfaces
    "bg_glass": "rgba(26, 35, 58, 0.85)",  # Glassmorphism
    "bg_glass_strong": "rgba(26, 35, 58, 0.95)",

    # Background colors (Light theme)
    "bg_primary_light": "#F8FAFC",     # Off-white
    "bg_secondary_light": "#FFFFFF",   # Pure white
    "bg_tertiary_light": "#F1F5F9",    # Light gray
    "bg_glass_light": "rgba(255, 255, 255, 0.85)",

    # Text colors
    "text_primary": "#E8EBF0",      # Main text (dark theme)
    "text_secondary": "#94A3B8",    # Secondary text
    "text_muted": "#64748B",        # Muted text
    "text_on_primary": "#0A0E1A",   # Text on primary color

    "text_primary_light": "#0F172A",   # Main text (light theme)
    "text_secondary_light": "#475569", # Secondary text
    "text_muted_light": "#94A3B8",     # Muted text

    # Border colors
    "border_subtle": "rgba(148, 163, 184, 0.15)",
    "border_accent": "rgba(0, 212, 255, 0.3)",
    "border_glow": "rgba(0, 212, 255, 0.5)",

    # Status colors
    "success": "#10B981",
    "success_glow": "rgba(16, 185, 129, 0.4)",
    "warning": "#F59E0B",
    "warning_glow": "rgba(245, 158, 11, 0.4)",
    "error": "#EF4444",
    "error_glow": "rgba(239, 68, 68, 0.4)",

    # Result card colors
    "area_color": "#22C55E",        # Green for area
    "area_glow": "rgba(34, 197, 94, 0.4)",
    "volume_color": "#06B6D4",      # Cyan for volume
    "volume_glow": "rgba(6, 182, 212, 0.4)",
}

# Font families - using system fonts that are commonly available
FONTS = {
    "primary": '"Segoe UI", "SF Pro Display", "Inter", "Roboto", "Helvetica Neue", Arial, sans-serif',
    "mono": '"JetBrains Mono", "Fira Code", "Consolas", "Monaco", monospace',
    "display": '"Orbitron", "Rajdhani", "Segoe UI", "SF Pro Display", sans-serif',
}

# Spacing scale
SPACING = {
    "xs": "4px",
    "sm": "8px",
    "md": "16px",
    "lg": "24px",
    "xl": "32px",
    "2xl": "48px",
}

# Border radius scale (for QSS - strings with px)
RADIUS = {
    "sm": "6px",
    "md": "10px",
    "lg": "14px",
    "xl": "20px",
    "full": "9999px",
}

# Border radius scale (numeric values for QPainter)
RADIUS_NUM = {
    "sm": 6,
    "md": 10,
    "lg": 14,
    "xl": 20,
    "full": 9999,
}

# Shadows
SHADOWS = {
    "sm": "0 1px 2px rgba(0, 0, 0, 0.3)",
    "md": "0 4px 12px rgba(0, 0, 0, 0.35)",
    "lg": "0 12px 24px rgba(0, 0, 0, 0.4)",
    "glow": "0 0 20px rgba(0, 212, 255, 0.3)",
    "glow_strong": "0 0 30px rgba(0, 212, 255, 0.5)",
    "inner": "inset 0 2px 4px rgba(0, 0, 0, 0.2)",
}

# Transitions
TRANSITIONS = {
    "fast": "150ms ease",
    "normal": "250ms ease",
    "slow": "350ms ease",
}

# Theme mode
DARK_THEME = True  # Set to False for light theme


def get_theme_stylesheet(dark: bool = True) -> str:
    """Generate the complete QSS stylesheet for the application."""

    c = COLORS

    if dark:
        bg_primary = c["bg_primary"]
        bg_secondary = c["bg_secondary"]
        bg_tertiary = c["bg_tertiary"]
        bg_glass = c["bg_glass"]
        bg_glass_strong = c["bg_glass_strong"]
        text_primary = c["text_primary"]
        text_secondary = c["text_secondary"]
        text_muted = c["text_muted"]
        border_subtle = c["border_subtle"]
        border_accent = c["border_accent"]
    else:
        bg_primary = c["bg_primary_light"]
        bg_secondary = c["bg_secondary_light"]
        bg_tertiary = c["bg_tertiary_light"]
        bg_glass = c["bg_glass_light"]
        bg_glass_strong = "rgba(255, 255, 255, 0.95)"
        text_primary = c["text_primary_light"]
        text_secondary = c["text_secondary_light"]
        text_muted = c["text_muted_light"]
        border_subtle = "rgba(15, 23, 42, 0.1)"
        border_accent = "rgba(0, 168, 204, 0.3)"

    primary = c["primary"]
    primary_dark = c["primary_dark"]
    primary_light = c["primary_light"]
    secondary = c["secondary"]

    font_primary = FONTS["primary"]
    font_display = FONTS["display"]
    font_mono = FONTS["mono"]

    radius_sm = RADIUS["sm"]
    radius_md = RADIUS["md"]
    radius_lg = RADIUS["lg"]
    radius_xl = RADIUS["xl"]
    radius_full = RADIUS["full"]

    shadow_md = SHADOWS["md"]
    shadow_lg = SHADOWS["lg"]
    shadow_glow = SHADOWS["glow"]
    shadow_inner = SHADOWS["inner"]

    trans_fast = TRANSITIONS["fast"]
    trans_normal = TRANSITIONS["normal"]

    return f"""
/* ============================================================================
   GLOBAL APPLICATION STYLES
   ============================================================================ */

QWidget {{
    font-family: {font_primary};
    font-size: 13px;
    color: {text_primary};
    background-color: transparent;
}}

QMainWindow {{
    background-color: {bg_primary};
}}

/* ============================================================================
   SCROLLBARS
   ============================================================================ */

QScrollBar:vertical {{
    background: {bg_secondary};
    width: 10px;
    border: none;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {primary}, stop:1 {secondary});
    border-radius: 5px;
    min-height: 40px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {primary_light}, stop:1 {c["secondary_light"]});
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
    background: none;
}}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}

QScrollBar:horizontal {{
    background: {bg_secondary};
    height: 10px;
    border: none;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {primary}, stop:1 {secondary});
    border-radius: 5px;
    min-width: 40px;
    margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {primary_light}, stop:1 {c["secondary_light"]});
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
    background: none;
}}

/* ============================================================================
   GROUP BOXES
   ============================================================================ */

QGroupBox {{
    font-family: {font_display};
    font-size: 14px;
    font-weight: 600;
    color: {text_primary};
    background-color: {bg_glass_strong};
    border: 1px solid {border_subtle};
    border-radius: {radius_lg};
    margin-top: 20px;
    padding-top: 10px;
    padding-bottom: {SPACING["md"]};
    padding-left: {SPACING["md"]};
    padding-right: {SPACING["md"]};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 4px 12px;
    margin-left: 10px;
    margin-top: -10px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {primary}, stop:1 {secondary});
    color: {c["text_on_primary"]};
    border-radius: {radius_sm};
    font-weight: 700;
    font-size: 13px;
    letter-spacing: 0.5px;
}}

QGroupBox:hover {{
    border-color: {border_accent};
    background-color: {bg_glass};
}}

/* ============================================================================
   BUTTONS
   ============================================================================ */

QPushButton {{
    font-family: {font_display};
    font-size: 13px;
    font-weight: 600;
    color: {c["text_on_primary"]};
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {primary}, stop:1 {primary_dark});
    border: none;
    border-radius: {radius_md};
    padding: 12px 24px;
    min-height: 20px;
}}

QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {primary_light}, stop:1 {primary});
    box-shadow: {shadow_glow};
}}

QPushButton:pressed {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {primary_dark}, stop:1 #008099);
    padding-top: 13px;
    padding-bottom: 11px;
}}

QPushButton:disabled {{
    background: {bg_tertiary};
    color: {text_muted};
    box-shadow: none;
}}

QPushButton:focus {{
    outline: none;
    border: 2px solid {primary_light};
}}

/* Secondary button style */
QPushButton[secondary="true"] {{
    background: {bg_tertiary};
    color: {text_primary};
    border: 1px solid {border_subtle};
}}

QPushButton[secondary="true"]:hover {{
    background: {bg_glass};
    border-color: {border_accent};
    color: {primary};
    box-shadow: {shadow_glow};
}}

/* Ghost button style */
QPushButton[ghost="true"] {{
    background: transparent;
    color: {text_secondary};
    border: 1px solid transparent;
    padding: 8px 16px;
}}

QPushButton[ghost="true"]:hover {{
    background: rgba(0, 212, 255, 0.1);
    color: {primary};
    border-color: {border_accent};
}}

/* Danger button style */
QPushButton[danger="true"] {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {c["error"]}, stop:1 #DC2626);
}}

QPushButton[danger="true"]:hover {{
    box-shadow: {c["error_glow"]} 0 0 20px;
}}

/* ============================================================================
   COMBO BOXES
   ============================================================================ */

QComboBox {{
    font-family: {font_primary};
    font-size: 13px;
    color: {text_primary};
    background-color: {bg_secondary};
    border: 1px solid {border_subtle};
    border-radius: {radius_md};
    padding: 10px 16px;
    min-height: 22px;
    selection-background-color: {primary};
    selection-color: {c["text_on_primary"]};
}}

QComboBox:hover {{
    border-color: {border_accent};
    background-color: {bg_glass};
}}

QComboBox:focus {{
    border: 2px solid {primary};
    background-color: {bg_glass_strong};
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 32px;
    border: none;
    border-top-right-radius: {radius_md};
    border-bottom-right-radius: {radius_md};
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 transparent, stop:1 {bg_tertiary});
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {text_secondary};
    margin-right: 10px;
    transition: {trans_fast};
}}

QComboBox:hover::down-arrow {{
    border-top-color: {primary};
}}

QComboBox QAbstractItemView {{
    background-color: {bg_secondary};
    border: 1px solid {border_accent};
    border-radius: {radius_md};
    selection-background-color: {primary};
    selection-color: {c["text_on_primary"]};
    outline: none;
    padding: 4px;
}}

QComboBox QAbstractItemView::item {{
    padding: 10px 16px;
    border-radius: {radius_sm};
    margin: 2px;
}}

QComboBox QAbstractItemView::item:hover {{
    background-color: rgba(0, 212, 255, 0.15);
    color: {primary};
}}

/* ============================================================================
   SPIN BOXES (QSpinBox, QDoubleSpinBox)
   ============================================================================ */

QSpinBox, QDoubleSpinBox {{
    font-family: {font_mono};
    font-size: 14px;
    font-weight: 500;
    color: {text_primary};
    background-color: {bg_secondary};
    border: 1px solid {border_subtle};
    border-radius: {radius_md};
    padding: 10px 12px;
    min-height: 22px;
    selection-background-color: {primary};
    selection-color: {c["text_on_primary"]};
}}

QSpinBox:hover, QDoubleSpinBox:hover {{
    border-color: {border_accent};
    background-color: {bg_glass};
}}

QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 2px solid {primary};
    background-color: {bg_glass_strong};
}}

QSpinBox::up-button, QDoubleSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 28px;
    border: none;
    border-top-right-radius: {radius_md};
    background: transparent;
}}

QSpinBox::down-button, QDoubleSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 28px;
    border: none;
    border-bottom-right-radius: {radius_md};
    background: transparent;
}}

QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 5px solid {text_secondary};
    width: 0;
    height: 0;
}}

QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {text_secondary};
    width: 0;
    height: 0;
}}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
    background: rgba(0, 212, 255, 0.15);
}}

QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed,
QSpinBox::down-button:pressed, QDoubleSpinBox::down-button:pressed {{
    background: rgba(0, 212, 255, 0.25);
}}

/* ============================================================================
   LABELS
   ============================================================================ */

QLabel {{
    color: {text_primary};
    background-color: transparent;
}}

QLabel[title="true"] {{
    font-family: {font_display};
    font-size: 28px;
    font-weight: 800;
    color: {text_primary};
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {primary}, stop:1 {secondary});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}

QLabel[subtitle="true"] {{
    font-family: {font_primary};
    font-size: 14px;
    font-weight: 400;
    color: {text_secondary};
}}

QLabel[caption="true"] {{
    font-family: {font_primary};
    font-size: 11px;
    font-weight: 400;
    color: {text_muted};
}}

QLabel[accent="true"] {{
    color: {primary};
    font-weight: 600;
}}

/* ============================================================================
   STATUS BAR
   ============================================================================ */

QStatusBar {{
    background-color: {bg_glass_strong};
    border-top: 1px solid {border_subtle};
    color: {text_secondary};
    font-size: 12px;
    font-weight: 500;
    padding: 4px 16px;
}}

QStatusBar::item {{
    border: none;
}}

QStatusBar QLabel {{
    color: {text_secondary};
    padding: 2px 8px;
    border-radius: {radius_sm};
    background: transparent;
}}

/* Status indicator animation */
QStatusBar QLabel[status="active"] {{
    color: {primary};
    background: rgba(0, 212, 255, 0.15);
    animation: pulse 2s infinite;
}}

QStatusBar QLabel[status="success"] {{
    color: {c["success"]};
    background: {c["success_glow"]};
}}

QStatusBar QLabel[status="error"] {{
    color: {c["error"]};
    background: {c["error_glow"]};
}}

QStatusBar QLabel[status="warning"] {{
    color: {c["warning"]};
    background: {c["warning_glow"]};
}}

/* ============================================================================
   MENU BAR
   ============================================================================ */

QMenuBar {{
    background-color: {bg_glass_strong};
    border-bottom: 1px solid {border_subtle};
    color: {text_primary};
    font-size: 13px;
    padding: 4px 8px;
}}

QMenuBar::item {{
    background: transparent;
    padding: 8px 16px;
    border-radius: {radius_sm};
    margin: 2px;
}}

QMenuBar::item:selected {{
    background: rgba(0, 212, 255, 0.15);
    color: {primary};
}}

QMenuBar::item:pressed {{
    background: rgba(0, 212, 255, 0.25);
}}

QMenu {{
    background-color: {bg_secondary};
    border: 1px solid {border_accent};
    border-radius: {radius_md};
    padding: 6px;
    margin: 2px;
}}

QMenu::item {{
    padding: 10px 24px;
    border-radius: {radius_sm};
    margin: 2px 4px;
}}

QMenu::item:selected {{
    background: rgba(0, 212, 255, 0.2);
    color: {primary};
}}

QMenu::separator {{
    height: 1px;
    background: {border_subtle};
    margin: 6px 12px;
}}

/* ============================================================================
   TOOLTIPS
   ============================================================================ */

QToolTip {{
    background-color: {bg_tertiary};
    color: {text_primary};
    border: 1px solid {border_accent};
    border-radius: {radius_md};
    padding: 8px 12px;
    font-size: 12px;
    font-weight: 500;
}}

/* ============================================================================
   MESSAGE BOX
   ============================================================================ */

QMessageBox {{
    background-color: {bg_secondary};
    border: 1px solid {border_accent};
    border-radius: {radius_lg};
}}

QMessageBox QLabel {{
    color: {text_primary};
    font-size: 13px;
    padding: {SPACING["md"]};
}}

QMessageBox QPushButton {{
    min-width: 100px;
    margin: {SPACING["sm"]};
}}

/* ============================================================================
   SPLITTER
   ============================================================================ */

QSplitter::handle {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 transparent, stop:0.5 {primary}, stop:1 transparent);
    width: 2px;
    height: 2px;
}}

QSplitter::handle:horizontal {{
    width: 3px;
}}

QSplitter::handle:vertical {{
    height: 3px;
}}

QSplitter::handle:hover {{
    background: {primary};
    box-shadow: {shadow_glow};
}}

/* ============================================================================
   SCROLL AREA
   ============================================================================ */

QScrollArea {{
    background: transparent;
    border: none;
}}

QScrollArea > QWidget > QWidget {{
    background: transparent;
}}

/* ============================================================================
   PROGRESS BAR (for loading)
   ============================================================================ */

QProgressBar {{
    background-color: {bg_tertiary};
    border: none;
    border-radius: {radius_full};
    height: 6px;
    text-align: center;
    color: transparent;
}}

QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {primary}, stop:1 {secondary});
    border-radius: {radius_full};
}}

QProgressBar[loading="true"]::chunk {{
    animation: progress-flow 1.5s ease-in-out infinite;
}}

/* ============================================================================
   ANIMATIONS (via property changes)
   ============================================================================ */

/* Note: Qt doesn't support CSS animations directly, but we can use
   property animations in Python code. Keyframes are handled via QPropertyAnimation. */

/* ============================================================================
   CUSTOM WIDGET STYLES (ResultCard, etc.)
   ============================================================================ */

#ResultCard {{
    background-color: {bg_glass_strong};
    border: 1px solid {border_subtle};
    border-radius: {radius_xl};
    padding: {SPACING["lg"]};
}}

#ResultCard:hover {{
    border-color: {border_accent};
    background-color: {bg_glass};
    box-shadow: {shadow_lg};
}}

/* Area card accent */
#ResultCard[area="true"] {{
    border-left: 4px solid {c["area_color"]};
}}

/* Volume card accent */
#ResultCard[volume="true"] {{
    border-left: 4px solid {c["volume_color"]};
}}

/* ============================================================================
   FORM LAYOUT
   ============================================================================ */

QFormLayout {{
    spacing: {SPACING["md"]};
}}

QFormLayout QLabel {{
    font-weight: 500;
    color: {text_secondary};
    padding-right: {SPACING["md"]};
    font-size: 12px;
}}

/* ============================================================================
   FRAME / SEPARATOR
   ============================================================================ */

QFrame[frameShape="4"] {{ /* HLine */
    border: none;
    border-top: 1px solid {border_subtle};
    margin: {SPACING["md"]} 0;
}}

QFrame[frameShape="5"] {{ /* VLine */
    border: none;
    border-left: 1px solid {border_subtle};
    margin: 0 {SPACING["md"]};
}}

/* ============================================================================
   TOOLBAR
   ============================================================================ */

QToolBar {{
    background: {bg_glass_strong};
    border: none;
    border-bottom: 1px solid {border_subtle};
    spacing: 8px;
    padding: 6px 12px;
}}

QToolBar QToolButton {{
    background: transparent;
    border: none;
    border-radius: {radius_sm};
    padding: 8px 12px;
    color: {text_secondary};
}}

QToolBar QToolButton:hover {{
    background: rgba(0, 212, 255, 0.15);
    color: {primary};
}}

QToolBar QToolButton:pressed {{
    background: rgba(0, 212, 255, 0.25);
}}

/* ============================================================================
   DOCK WIDGET
   ============================================================================ */

QDockWidget {{
    titlebar-close-icon: url(:/icons/close.png);
    titlebar-normal-icon: url(:/icons/undock.png);
}}

QDockWidget::title {{
    background: {bg_glass_strong};
    color: {text_primary};
    padding: 8px 12px;
    font-weight: 600;
    border-bottom: 1px solid {border_subtle};
}}

QDockWidget::close-button, QDockWidget::float-button {{
    background: transparent;
    border: none;
    border-radius: {radius_sm};
    padding: 4px;
}}

QDockWidget::close-button:hover, QDockWidget::float-button:hover {{
    background: rgba(0, 212, 255, 0.15);
}}
"""


def get_light_theme_stylesheet() -> str:
    """Get the light theme stylesheet."""
    return get_theme_stylesheet(dark=False)


def get_dark_theme_stylesheet() -> str:
    """Get the dark theme stylesheet."""
    return get_theme_stylesheet(dark=True)