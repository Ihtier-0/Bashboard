import sys

from PySide6.QtWidgets import QApplication

from bashboard import settings
from bashboard.i18n import DEFAULT_LANGUAGE, translator
from bashboard.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Bashboard")
    app.setOrganizationName("Bashboard")

    cfg = settings.load()
    translator.set_language(cfg.get("language", DEFAULT_LANGUAGE))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
