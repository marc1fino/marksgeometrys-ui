"""Bundled geometric typefaces for the interface and large display headings."""

from pathlib import Path

from PyQt6.QtGui import QFontDatabase, QGuiApplication


FONTS = {
    "primary": "Manrope",
    "display": "Space Grotesk",
    "mono": "Manrope",
}

_FONT_FILES = (
    ("Manrope[wght].ttf", "Manrope"),
    ("SpaceGrotesk[wght].ttf", "Space Grotesk"),
)
_font_ids = []


def load_fonts() -> None:
    """Register the packaged fonts once, after the GUI application is created.

    Fonts are private to this process. A missing or invalid resource raises an
    explicit error instead of quietly falling back to a different typeface.
    """
    if not isinstance(QGuiApplication.instance(), QGuiApplication):
        raise RuntimeError("Create QApplication before loading the bundled fonts.")
    if _font_ids:
        return

    directory = Path(__file__).parent / "assets" / "fonts"
    registered = []
    try:
        for filename, family in _FONT_FILES:
            font_id = QFontDatabase.addApplicationFont(str(directory / filename))
            if font_id == -1 or family not in QFontDatabase.applicationFontFamilies(font_id):
                if font_id != -1:
                    QFontDatabase.removeApplicationFont(font_id)
                raise RuntimeError("Could not load the bundled " + family + " typeface.")
            registered.append(font_id)
    except Exception:
        for font_id in registered:
            QFontDatabase.removeApplicationFont(font_id)
        raise
    _font_ids.extend(registered)
