"""Minimal ANSI SGR (Select Graphic Rendition) parser for the log view.

Handles colors (8/16, 256, truecolor), bold, italic, underline. Strips other
escape sequences (cursor movement, clear screen, etc.) so they don't pollute
the output. Stateful: the current QTextCharFormat persists across parse()
calls so a multi-chunk stream renders correctly."""

import re
from typing import Iterator

from PySide6.QtGui import QColor, QFont, QTextCharFormat

_SGR_RE = re.compile(r"\x1b\[([\d;]*)([a-zA-Z])")

# Standard 8 + bright 8. Picked to be readable on both light and dark
# backgrounds (close to common terminal palettes).
_BASE_COLORS = {
    30: "#000000",
    31: "#cd3131",
    32: "#0dbc79",
    33: "#cd9900",
    34: "#2472c8",
    35: "#bc3fbc",
    36: "#11a8cd",
    37: "#cccccc",
    90: "#666666",
    91: "#f14c4c",
    92: "#23d18b",
    93: "#f5f543",
    94: "#3b8eea",
    95: "#d670d6",
    96: "#29b8db",
    97: "#ffffff",
}


def _xterm_256(idx: int) -> QColor:
    """xterm 256-color palette: 0-15 base, 16-231 6×6×6 cube, 232-255 grayscale."""
    if idx < 16:
        # Map back to base palette via FG codes (0-7 -> 30-37, 8-15 -> 90-97).
        code = (30 + idx) if idx < 8 else (90 + idx - 8)
        return QColor(_BASE_COLORS[code])
    if idx < 232:
        n = idx - 16
        r = n // 36
        g = (n // 6) % 6
        b = n % 6
        levels = [0, 95, 135, 175, 215, 255]
        return QColor(levels[r], levels[g], levels[b])
    gray = 8 + (idx - 232) * 10
    return QColor(gray, gray, gray)


class AnsiParser:
    def __init__(self):
        self._fmt = QTextCharFormat()

    def reset(self) -> None:
        self._fmt = QTextCharFormat()

    def _apply_codes(self, codes: list[int]) -> None:
        i = 0
        while i < len(codes):
            c = codes[i]
            if c == 0:
                self._fmt = QTextCharFormat()
            elif c == 1:
                self._fmt.setFontWeight(QFont.Bold)
            elif c == 22:
                self._fmt.setFontWeight(QFont.Normal)
            elif c == 3:
                self._fmt.setFontItalic(True)
            elif c == 23:
                self._fmt.setFontItalic(False)
            elif c == 4:
                self._fmt.setFontUnderline(True)
            elif c == 24:
                self._fmt.setFontUnderline(False)
            elif c in _BASE_COLORS:
                self._fmt.setForeground(QColor(_BASE_COLORS[c]))
            elif c == 39:
                self._fmt.clearForeground()
            elif 40 <= c <= 47:
                self._fmt.setBackground(QColor(_BASE_COLORS[c - 10]))
            elif 100 <= c <= 107:
                self._fmt.setBackground(QColor(_BASE_COLORS[c - 10]))
            elif c == 49:
                self._fmt.clearBackground()
            elif c == 38 and i + 2 < len(codes) and codes[i + 1] == 5:
                self._fmt.setForeground(_xterm_256(codes[i + 2]))
                i += 2
            elif c == 38 and i + 4 < len(codes) and codes[i + 1] == 2:
                self._fmt.setForeground(
                    QColor(codes[i + 2], codes[i + 3], codes[i + 4])
                )
                i += 4
            elif c == 48 and i + 2 < len(codes) and codes[i + 1] == 5:
                self._fmt.setBackground(_xterm_256(codes[i + 2]))
                i += 2
            elif c == 48 and i + 4 < len(codes) and codes[i + 1] == 2:
                self._fmt.setBackground(
                    QColor(codes[i + 2], codes[i + 3], codes[i + 4])
                )
                i += 4
            i += 1

    def parse(self, text: str) -> Iterator[tuple[str, QTextCharFormat]]:
        """Yield (chunk, format) pairs. Non-SGR escapes (cursor movement,
        screen clear, etc.) are dropped silently."""
        pos = 0
        for m in _SGR_RE.finditer(text):
            if m.start() > pos:
                yield text[pos : m.start()], QTextCharFormat(self._fmt)
            params, terminator = m.group(1), m.group(2)
            if terminator == "m":
                codes = [int(x) for x in params.split(";") if x] or [0]
                self._apply_codes(codes)
            pos = m.end()
        if pos < len(text):
            yield text[pos:], QTextCharFormat(self._fmt)
