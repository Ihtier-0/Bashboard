import argparse
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication

from bashboard import settings
from bashboard.i18n import DEFAULT_LANGUAGE, translator
from bashboard.main_window import MainWindow
from bashboard.theme import DEFAULT_THEME, theme_manager


def _load_svg_icon(path: Path) -> QIcon:
    """Render the SVG into a QIcon with multiple raster sizes. QIcon(path)
    alone leaves availableSizes() empty, which X11 window managers don't
    always pick up — they want concrete pixmaps for _NET_WM_ICON."""
    renderer = QSvgRenderer(str(path))
    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256, 512):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        icon.addPixmap(pixmap)
    return icon


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


def main() -> None:
    args, qt_argv = _parse_args(sys.argv[1:])

    app = QApplication([sys.argv[0], *qt_argv])
    app.setApplicationName("Bashboard")
    app.setOrganizationName("Bashboard")
    app.setDesktopFileName("bashboard")
    icon_path = Path(__file__).resolve().parent.parent / "icons" / "bashboard.svg"
    if not icon_path.is_file():
        # Installed via pip: icons are in the package data directory.
        icon_path = Path(__file__).resolve().parent / "icons" / "bashboard.svg"
    if icon_path.is_file():
        app.setWindowIcon(_load_svg_icon(icon_path))

    cfg = settings.load()
    translator.set_language(cfg.get("language", DEFAULT_LANGUAGE))
    theme_manager.install(app, cfg.get("theme", DEFAULT_THEME))

    window = MainWindow(config_path=args.config)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
