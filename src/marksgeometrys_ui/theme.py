"""A quiet white workspace with typography and blue linework as its identity."""

from pathlib import Path

from .typography import FONTS

COLORS = {
    "primary": "#2028FF", "primary_dark": "#1119DB", "primary_light": "#F1F2FF",
    "secondary": "#2028FF", "bg_primary": "#FFFFFF", "bg_secondary": "#FFFFFF",
    "bg_tertiary": "#FAFAFC", "text_primary": "#242434", "text_secondary": "#686873",
    "text_muted": "#909099", "text_on_primary": "#FFFFFF", "border_subtle": "#E5E5EB",
    "border_accent": "#BABDFF", "success": "#2028FF", "warning": "#926319",
    "error": "#A73745", "area_color": "#2028FF", "volume_color": "#2028FF",
}
SPACING = {"xs": "4px", "sm": "8px", "md": "16px", "lg": "24px", "xl": "32px"}
RADIUS_NUM = {"sm": 2, "md": 3, "lg": 4, "xl": 4}
RADIUS = {name: f"{value}px" for name, value in RADIUS_NUM.items()}


def get_theme_stylesheet(dark: bool = False) -> str:
    """Return Qt-supported styling; the legacy argument is accepted."""
    assets = (Path(__file__).parent / "assets").as_posix()
    return """
    QWidget {
        color: #242434; font-family: '@PRIMARY@'; font-size: 13px;
        selection-background-color: #E8E9FF; selection-color: #2028FF;
    }
    QMainWindow, QWidget#Workspace { background: white; }
    QLabel { background: transparent; border: none; }
    QFrame#TopBar { background: white; border-bottom: 1px solid #EBEBF0; }
    QFrame#Card, QFrame#ViewerCard, QWidget#PanelContent { background: white; border: none; }
    QLabel#Brand { color: #2028FF; font-family: '@DISPLAY@'; font-size: 20px; font-weight: 700; }
    QLabel#Heading { color: #2028FF; font-family: '@DISPLAY@'; font-size: 42px; font-weight: 700; letter-spacing: -1px; }
    QLabel#Heading[compact="true"] { font-size: 28px; letter-spacing: 0px; }
    QLabel#SectionLabel { color: #60606D; font-size: 13px; font-weight: 400; }
    QLabel#Description, QLabel#Muted { color: #85858F; font-size: 12px; }
    QLabel#DimensionBadge { color: #9797A0; font-size: 12px; }
    QLabel#ActiveNavigation { color: #2028FF; font-size: 14px; }
    QLabel#Error {
        color: #A73745; background: #FCF5F6; border: none;
        border-radius: 3px; padding: 10px; font-size: 12px;
    }
    QFrame#Divider { background: #EBEBF0; border: none; max-height: 1px; }
    QPushButton {
        background: white; color: #686873; border: 1px solid #DEDEE7;
        border-radius: 3px; padding: 8px 12px; font-weight: 400;
    }
    QPushButton:hover { color: #2028FF; border-color: #BABDFF; background: #FAFAFF; }
    QPushButton:pressed { background: #EFEFFF; }
    QPushButton:focus { border-color: #2028FF; }
    QPushButton:disabled { color: #B0B0BA; background: #FAFAFC; }
    QPushButton#PrimaryButton {
        background: #2028FF; color: white; border: 1px solid #2028FF;
        padding: 11px 16px; border-radius: 3px; font-size: 14px;
    }
    QPushButton#PrimaryButton:hover { background: #1119DB; border-color: #1119DB; }
    QPushButton#PrimaryButton:pressed { background: #0D13AF; }
    QPushButton#PrimaryButton:disabled { background: #ABAEF1; border-color: #ABAEF1; }
    QPushButton#GhostButton, QPushButton#ToolButton {
        background: transparent; border: none; color: #888893; font-size: 12px;
        padding: 6px 9px; border-radius: 2px;
    }
    QPushButton#GhostButton:hover, QPushButton#ToolButton:hover {
        color: #2028FF; background: #F6F6FF;
    }
    QPushButton#ToolButton:checked { color: #2028FF; background: #F1F2FF; }
    QPushButton#Navigation {
        background: transparent; color: #2028FF; font-size: 14px;
        border: none; padding: 8px 6px;
    }
    QPushButton#Navigation:hover { background: #F8F8FF; }
    QComboBox, QSpinBox, QDoubleSpinBox {
        background: white; color: #343441; border: 1px solid #DEDEE7;
        border-radius: 3px; padding: 9px 11px; min-height: 20px;
    }
    QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover { border-color: #B7BAE5; }
    QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus { border-color: #2028FF; }
    QComboBox { padding-right: 28px; }
    QComboBox::drop-down { border: none; width: 25px; }
    QComboBox#MeasurementPicker { border: none; padding: 6px 26px 6px 10px; color: #2028FF; }
    QSpinBox::up-button, QDoubleSpinBox::up-button {
        subcontrol-origin: border; subcontrol-position: top right;
        width: 22px; border: none; background: #FAFAFD;
    }
    QSpinBox::down-button, QDoubleSpinBox::down-button {
        subcontrol-origin: border; subcontrol-position: bottom right;
        width: 22px; border: none; background: #FAFAFD;
    }
    QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
        image: url('@ASSETS@/chevron-up.svg'); width: 10px; height: 7px;
    }
    QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
        image: url('@ASSETS@/chevron-down.svg'); width: 10px; height: 7px;
    }
    QComboBox::down-arrow {
        image: url('@ASSETS@/chevron-down.svg'); width: 12px; height: 8px;
    }
    QComboBox QAbstractItemView, QMenu {
        background: white; color: #343441; border: 1px solid #DEDEE7;
        selection-background-color: #F0F0FF; selection-color: #2028FF;
        padding: 5px; outline: none;
    }
    QMenu::item { padding: 8px 24px; }
    QMenu::item:selected { color: #2028FF; background: #F1F2FF; }
    QMenu::separator { height: 1px; background: #E9E9EF; margin: 4px 8px; }
    QAbstractItemView::item { min-height: 28px; }
    QScrollArea { background: transparent; border: none; }
    QScrollArea > QWidget > QWidget { background: transparent; }
    QScrollBar:vertical { width: 5px; background: transparent; margin: 2px; }
    QScrollBar::handle:vertical { background: #DCDCE5; border-radius: 2px; min-height: 24px; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
    QSplitter::handle { background: transparent; }
    QSplitter::handle:hover { background: #F5F5FC; }
    QStatusBar { background: white; color: #9A9AA4; border: none; font-size: 11px; }
    QStatusBar::item { border: none; }
    QToolTip { background: white; color: #434351; border: 1px solid #DEDEE7; padding: 7px; }
    QDialog, QMessageBox { background: white; }
    """.replace("@ASSETS@", assets).replace("@PRIMARY@", FONTS["primary"]).replace("@DISPLAY@", FONTS["display"])


def get_light_theme_stylesheet() -> str:
    return get_theme_stylesheet()


def get_dark_theme_stylesheet() -> str:
    """Compatibility alias for the application's white theme."""
    return get_theme_stylesheet()
