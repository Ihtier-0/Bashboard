import argparse
import sys

from PySide6.QtWidgets import QApplication

from bashboard import settings
from bashboard.i18n import DEFAULT_LANGUAGE, translator
from bashboard.main_window import MainWindow
from bashboard.theme import DEFAULT_THEME, theme_manager


def _parse_args(argv: list[str]) -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(
        prog="bashboard",
        description="Bashboard — desktop GUI for running bash scripts on Linux.",
    )
    parser.add_argument(
        "-c",
        "--config",
        metavar="PATH",
        help=(
            "Path to scripts.json (default: ~/.config/bashboard/scripts.json). "
            "Relative script paths inside the file are resolved against this "
            "file's directory."
        ),
    )
    return parser.parse_known_args(argv)


def main():
    args, qt_argv = _parse_args(sys.argv[1:])

    app = QApplication([sys.argv[0], *qt_argv])
    app.setApplicationName("Bashboard")
    app.setOrganizationName("Bashboard")

    cfg = settings.load()
    translator.set_language(cfg.get("language", DEFAULT_LANGUAGE))
    theme_manager.install(app, cfg.get("theme", DEFAULT_THEME))

    window = MainWindow(config_path=args.config)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
