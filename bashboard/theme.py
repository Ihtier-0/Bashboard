from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QColor, QGuiApplication, QPalette
from PySide6.QtWidgets import QApplication

SUPPORTED_THEMES = ["system", "light", "dark"]
DEFAULT_THEME = "system"


def _dark_palette() -> QPalette:
    p = QPalette()
    p.setColor(QPalette.Window, QColor(53, 53, 53))
    p.setColor(QPalette.WindowText, Qt.white)
    p.setColor(QPalette.Base, QColor(35, 35, 35))
    p.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    p.setColor(QPalette.ToolTipBase, QColor(53, 53, 53))
    p.setColor(QPalette.ToolTipText, Qt.white)
    p.setColor(QPalette.Text, Qt.white)
    p.setColor(QPalette.Button, QColor(53, 53, 53))
    p.setColor(QPalette.ButtonText, Qt.white)
    p.setColor(QPalette.BrightText, Qt.red)
    p.setColor(QPalette.Link, QColor(42, 130, 218))
    p.setColor(QPalette.Highlight, QColor(42, 130, 218))
    p.setColor(QPalette.HighlightedText, Qt.black)
    p.setColor(QPalette.PlaceholderText, QColor(160, 160, 160))
    p.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
    p.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))
    p.setColor(QPalette.Disabled, QPalette.WindowText, QColor(127, 127, 127))
    p.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor(127, 127, 127))
    return p


def _resolve(name: str) -> str:
    if name == "system":
        scheme = QGuiApplication.styleHints().colorScheme()
        if scheme == Qt.ColorScheme.Dark:
            return "dark"
        return "light"
    return name


def _apply_resolved(app: QApplication, resolved: str) -> None:
    app.setStyle("Fusion")
    if resolved == "dark":
        app.setPalette(_dark_palette())
    else:
        app.setPalette(app.style().standardPalette())


class _ThemeManager(QObject):
    theme_changed = Signal()

    def __init__(self):
        super().__init__()
        self._current = DEFAULT_THEME
        self._app: QApplication | None = None

    @property
    def current(self) -> str:
        return self._current

    def install(self, app: QApplication, name: str) -> None:
        self._app = app
        QGuiApplication.styleHints().colorSchemeChanged.connect(self._on_system_changed)
        self.set_theme(name, force=True)

    def set_theme(self, name: str, force: bool = False) -> None:
        if name not in SUPPORTED_THEMES:
            name = DEFAULT_THEME
        if not force and name == self._current:
            return
        self._current = name
        if self._app is not None:
            _apply_resolved(self._app, _resolve(name))
        self.theme_changed.emit()

    def _on_system_changed(self) -> None:
        if self._current == "system" and self._app is not None:
            _apply_resolved(self._app, _resolve("system"))
            self.theme_changed.emit()


theme_manager = _ThemeManager()
