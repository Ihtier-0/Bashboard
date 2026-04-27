from typing import Optional

from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .i18n import translator, tr
from .script import CLEAR_TOKEN, Script


class LogPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.script: Optional[Script] = None

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

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(10000)
        mono = QFont("Monospace")
        mono.setStyleHint(QFont.TypeWriter)
        self.log_view.setFont(mono)
        layout.addWidget(self.log_view, 1)

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

        self._refresh_title()

        if script is None:
            self._update_input_state()
            return

        if script.log_lines:
            self.log_view.setPlainText("".join(script.log_lines))
            self.log_view.moveCursor(QTextCursor.End)

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

    def _on_append(self, chunk: str) -> None:
        if chunk == CLEAR_TOKEN:
            self.log_view.clear()
            return
        self.log_view.moveCursor(QTextCursor.End)
        self.log_view.insertPlainText(chunk)
        self.log_view.moveCursor(QTextCursor.End)

    def _update_input_state(self) -> None:
        running = self.script is not None and self.script.is_running
        self.input.setEnabled(running)
        self.send_btn.setEnabled(running)
        self.clear_btn.setEnabled(self.script is not None)

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
