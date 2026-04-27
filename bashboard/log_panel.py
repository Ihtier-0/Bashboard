from datetime import datetime
from typing import Optional

from PySide6.QtCore import QEvent, Qt, QTimer
from PySide6.QtGui import (
    QColor,
    QFont,
    QKeySequence,
    QShortcut,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
)
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

_MATCH_BG = QColor("#ffea7f")
_CURRENT_MATCH_BG = QColor("#ff8f00")
_MATCH_FG = QColor(Qt.black)

from .ansi import AnsiParser
from .i18n import translator, tr
from .script import CLEAR_TOKEN, Script, format_bytes, format_duration


class LogPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.script: Optional[Script] = None
        self._ansi = AnsiParser()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        title_row = QHBoxLayout()
        self.title = QLabel()
        title_font = self.title.font()
        title_font.setBold(True)
        self.title.setFont(title_font)
        title_row.addWidget(self.title)
        title_row.addStretch(1)
        self.clear_btn = QPushButton()
        self.clear_btn.clicked.connect(self._clear)
        title_row.addWidget(self.clear_btn)
        layout.addLayout(title_row)

        self.subtitle = QLabel()
        self.subtitle.setStyleSheet("color: gray;")
        layout.addWidget(self.subtitle)

        self._tick_timer = QTimer(self)
        self._tick_timer.setInterval(1000)
        self._tick_timer.timeout.connect(self._refresh_stats)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(10000)
        mono = QFont("Monospace")
        mono.setStyleHint(QFont.TypeWriter)
        self.log_view.setFont(mono)
        layout.addWidget(self.log_view, 1)

        self.search_bar = QWidget()
        sl = QHBoxLayout(self.search_bar)
        sl.setContentsMargins(0, 4, 0, 0)
        self.search_input = QLineEdit()
        self.search_input.installEventFilter(self)
        self.search_input.textChanged.connect(self._on_search_text_changed)
        sl.addWidget(self.search_input, 1)
        self.search_prev_btn = QToolButton()
        self.search_prev_btn.setText("▲")
        self.search_prev_btn.clicked.connect(self._search_prev)
        sl.addWidget(self.search_prev_btn)
        self.search_next_btn = QToolButton()
        self.search_next_btn.setText("▼")
        self.search_next_btn.clicked.connect(self._search_next)
        sl.addWidget(self.search_next_btn)
        self.search_close_btn = QToolButton()
        self.search_close_btn.setText("✕")
        self.search_close_btn.clicked.connect(self._hide_search)
        sl.addWidget(self.search_close_btn)
        self.search_bar.setVisible(False)
        layout.addWidget(self.search_bar)

        self.find_shortcut = QShortcut(QKeySequence.Find, self)
        self.find_shortcut.activated.connect(self._show_search)

        input_row = QHBoxLayout()
        self.input = QLineEdit()
        self.input.returnPressed.connect(self._send)
        input_row.addWidget(self.input)

        self.send_btn = QPushButton()
        self.send_btn.clicked.connect(self._send)
        input_row.addWidget(self.send_btn)
        layout.addLayout(input_row)

        translator.language_changed.connect(self._retranslate)
        self._retranslate()
        self.attach(None)

    def attach(self, script: Optional[Script]) -> None:
        if self.script is not None:
            try:
                self.script.log_appended.disconnect(self._on_append)
                self.script.state_changed.disconnect(self._update_input_state)
            except (RuntimeError, TypeError):
                pass

        self.script = script
        self.log_view.clear()
        self._ansi.reset()

        self._refresh_title()

        if script is None:
            self._update_input_state()
            return

        if script.log_lines:
            self._append_with_ansi("".join(script.log_lines))

        script.log_appended.connect(self._on_append)
        script.state_changed.connect(self._update_input_state)
        self._update_input_state()

    def refresh_title(self) -> None:
        self._refresh_title()

    def _refresh_title(self) -> None:
        if self.script is None:
            self.title.setText(tr("Logs"))
        else:
            self.title.setText(tr("Logs — {name}").format(name=self.script.name))

    def _retranslate(self) -> None:
        self._refresh_title()
        self.input.setPlaceholderText(
            tr("Send to stdin of the running script (Enter to send)")
        )
        self.send_btn.setText(tr("Send"))
        self.clear_btn.setText(tr("Clear"))
        self.search_input.setPlaceholderText(tr("Find in log…"))
        self.search_prev_btn.setToolTip(tr("Previous match (Shift+Enter)"))
        self.search_next_btn.setToolTip(tr("Next match (Enter)"))
        self.search_close_btn.setToolTip(tr("Close (Esc)"))

    def _on_append(self, chunk: str) -> None:
        if chunk == CLEAR_TOKEN:
            self.log_view.clear()
            self._ansi.reset()
            return
        self._append_with_ansi(chunk)

    def _append_with_ansi(self, chunk: str) -> None:
        cursor = self.log_view.textCursor()
        cursor.movePosition(QTextCursor.End)
        for text, fmt in self._ansi.parse(chunk):
            cursor.insertText(text, fmt)
        self.log_view.setTextCursor(cursor)

    def _update_input_state(self) -> None:
        running = self.script is not None and self.script.is_running
        self.input.setEnabled(running)
        self.send_btn.setEnabled(running)
        self.clear_btn.setEnabled(self.script is not None)
        self._refresh_stats()

    def _refresh_stats(self) -> None:
        s = self.script
        if s is None or s.last_started_at is None:
            self.subtitle.setText("")
            self._tick_timer.stop()
            return
        started = s.last_started_at.strftime("%H:%M:%S")
        sz = format_bytes(s.bytes_received)
        if s.is_running:
            elapsed = (datetime.now() - s.last_started_at).total_seconds()
            self.subtitle.setText(
                tr("▶ started {start} · running {elapsed} · {size} output").format(
                    start=started, elapsed=format_duration(elapsed), size=sz
                )
            )
            if not self._tick_timer.isActive():
                self._tick_timer.start()
        else:
            self._tick_timer.stop()
            duration = (
                (s.last_finished_at - s.last_started_at).total_seconds()
                if s.last_finished_at
                else 0
            )
            sym = "✓" if s.last_exit_code == 0 else "✗"
            self.subtitle.setText(
                tr("{sym} last: {start} · {duration} · exit {code} · {size}").format(
                    sym=sym,
                    start=started,
                    duration=format_duration(duration),
                    code=s.last_exit_code if s.last_exit_code is not None else "?",
                    size=sz,
                )
            )

    def _clear(self) -> None:
        if self.script is not None:
            self.script.clear_log()

    def _send(self) -> None:
        if self.script is None or not self.script.is_running:
            return
        text = self.input.text()
        self.script.send_input(text)
        self.log_view.moveCursor(QTextCursor.End)
        self.log_view.insertPlainText(f"> {text}\n")
        self.log_view.moveCursor(QTextCursor.End)
        self.input.clear()

    # ----- search -----

    def _show_search(self) -> None:
        self.search_bar.setVisible(True)
        self.search_input.setFocus()
        self.search_input.selectAll()
        self._refresh_highlights()

    def _hide_search(self) -> None:
        self.search_bar.setVisible(False)
        self.log_view.setExtraSelections([])
        self.log_view.setFocus()

    def _on_search_text_changed(self, text: str) -> None:
        if not text:
            self.log_view.setExtraSelections([])
            return
        # Move to the first match from the top.
        cursor = self.log_view.textCursor()
        cursor.movePosition(QTextCursor.Start)
        self.log_view.setTextCursor(cursor)
        self.log_view.find(text)
        self._refresh_highlights()

    def _search_next(self) -> None:
        text = self.search_input.text()
        if not text:
            return
        if not self.log_view.find(text):
            cursor = self.log_view.textCursor()
            cursor.movePosition(QTextCursor.Start)
            self.log_view.setTextCursor(cursor)
            self.log_view.find(text)
        self._refresh_highlights()

    def _search_prev(self) -> None:
        text = self.search_input.text()
        if not text:
            return
        if not self.log_view.find(text, QTextDocument.FindBackward):
            cursor = self.log_view.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.log_view.setTextCursor(cursor)
            self.log_view.find(text, QTextDocument.FindBackward)
        self._refresh_highlights()

    def _refresh_highlights(self) -> None:
        text = self.search_input.text() if self.search_bar.isVisible() else ""
        if not text:
            self.log_view.setExtraSelections([])
            return
        cur = self.log_view.textCursor()
        cur_start, cur_end = cur.selectionStart(), cur.selectionEnd()

        selections = []
        doc = self.log_view.document()
        finder = QTextCursor(doc)
        while True:
            finder = doc.find(text, finder)
            if finder.isNull():
                break
            sel = QTextEdit.ExtraSelection()
            sel.cursor = QTextCursor(finder)
            fmt = QTextCharFormat()
            is_current = (
                finder.selectionStart() == cur_start
                and finder.selectionEnd() == cur_end
            )
            fmt.setBackground(_CURRENT_MATCH_BG if is_current else _MATCH_BG)
            fmt.setForeground(_MATCH_FG)
            sel.format = fmt
            selections.append(sel)
        self.log_view.setExtraSelections(selections)

    def eventFilter(self, obj, event) -> bool:
        if obj is self.search_input and event.type() == QEvent.KeyPress:
            key = event.key()
            if key == Qt.Key_Escape:
                self._hide_search()
                return True
            if key in (Qt.Key_Return, Qt.Key_Enter):
                if event.modifiers() & Qt.ShiftModifier:
                    self._search_prev()
                else:
                    self._search_next()
                return True
        return super().eventFilter(obj, event)
