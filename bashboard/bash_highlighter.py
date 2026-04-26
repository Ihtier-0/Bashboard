from pygments import lex
from pygments.lexers.shell import BashLexer
from pygments.token import Token

from PySide6.QtGui import (
    QColor,
    QFont,
    QGuiApplication,
    QPalette,
    QSyntaxHighlighter,
    QTextCharFormat,
)

from .theme import theme_manager

# Color schemes loosely follow GitHub light / dark for familiar feel.
_LIGHT = {
    Token.Comment: ("#6a737d", False, True),
    Token.Keyword: ("#d73a49", True, False),
    Token.Operator.Word: ("#d73a49", True, False),
    Token.Name.Builtin: ("#005cc5", False, False),
    Token.Name.Variable: ("#e36209", False, False),
    Token.Name.Function: ("#6f42c1", False, False),
    Token.String: ("#032f62", False, False),
    Token.String.Backtick: ("#22863a", False, False),
    Token.Number: ("#005cc5", False, False),
    Token.Operator: ("#005cc5", False, False),
}

_DARK = {
    Token.Comment: ("#8b949e", False, True),
    Token.Keyword: ("#ff7b72", True, False),
    Token.Operator.Word: ("#ff7b72", True, False),
    Token.Name.Builtin: ("#79c0ff", False, False),
    Token.Name.Variable: ("#ffa657", False, False),
    Token.Name.Function: ("#d2a8ff", False, False),
    Token.String: ("#a5d6ff", False, False),
    Token.String.Backtick: ("#7ee787", False, False),
    Token.Number: ("#79c0ff", False, False),
    Token.Operator: ("#79c0ff", False, False),
}


def _build_formats(scheme: dict) -> dict:
    formats = {}
    for token, (color, bold, italic) in scheme.items():
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(QFont.Bold)
        if italic:
            fmt.setFontItalic(True)
        formats[token] = fmt
    return formats


def _is_dark_palette() -> bool:
    bg = QGuiApplication.palette().color(QPalette.Base)
    # Standard luminance check.
    return bg.lightness() < 128


class BashHighlighter(QSyntaxHighlighter):
    """Bash syntax highlighting via pygments. Re-applies on theme changes."""

    def __init__(self, document):
        super().__init__(document)
        self._lexer = BashLexer()
        self._formats: dict = {}
        self._reload_formats()
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _reload_formats(self) -> None:
        self._formats = _build_formats(_DARK if _is_dark_palette() else _LIGHT)

    def _on_theme_changed(self) -> None:
        self._reload_formats()
        self.rehighlight()

    def _format_for(self, token):
        # Walk the token type hierarchy until we find a registered format.
        while token is not None:
            if token in self._formats:
                return self._formats[token]
            token = token.parent
        return None

    def highlightBlock(self, text: str) -> None:
        pos = 0
        for token, value in lex(text, self._lexer):
            length = len(value)
            fmt = self._format_for(token)
            if fmt is not None:
                self.setFormat(pos, length, fmt)
            pos += length
