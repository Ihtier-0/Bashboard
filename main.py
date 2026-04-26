import sys

from PySide6.QtWidgets import QApplication

from bashboard import settings
from bashboard.i18n import DEFAULT_LANGUAGE, translator
from bashboard.main_window import MainWindow
from bashboard.theme import DEFAULT_THEME, theme_manager


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Bashboard")
    app.setOrganizationName("Bashboard")

    cfg = settings.load()
    translator.set_language(cfg.get("language", DEFAULT_LANGUAGE))
    theme_manager.install(app, cfg.get("theme", DEFAULT_THEME))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
