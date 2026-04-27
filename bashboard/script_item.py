from datetime import datetime

from PySide6.QtCore import QEvent, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QWidget,
)

from .i18n import translator, tr
from .script import Script, format_bytes, format_duration


class ScriptItem(QWidget):
    run_clicked = Signal()
    stop_clicked = Signal()
    copy_clicked = Signal()
    edit_clicked = Signal()
    delete_clicked = Signal()

    def __init__(self, script: Script):
        super().__init__()
        self.script = script

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        self.dot = QLabel("●")
        self.dot.setFixedWidth(16)
        # Recompute the dot tooltip just-in-time so the elapsed time is
        # accurate without a per-row tick timer.
        self.dot.installEventFilter(self)
        layout.addWidget(self.dot)

        self.name_label = QLabel(script.name)
        self.name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(self.name_label, 1)

        self.run_btn = self._mk_btn("▶")
        self.run_btn.clicked.connect(self.run_clicked.emit)
        layout.addWidget(self.run_btn)

        self.stop_btn = self._mk_btn("■")
        self.stop_btn.clicked.connect(self.stop_clicked.emit)
        layout.addWidget(self.stop_btn)

        self.copy_btn = self._mk_btn("⎘")
        self.copy_btn.clicked.connect(self.copy_clicked.emit)
        layout.addWidget(self.copy_btn)

        self.edit_btn = self._mk_btn("✎")
        self.edit_btn.clicked.connect(self.edit_clicked.emit)
        layout.addWidget(self.edit_btn)

        self.delete_btn = self._mk_btn("✖")
        self.delete_btn.clicked.connect(self.delete_clicked.emit)
        layout.addWidget(self.delete_btn)

        script.state_changed.connect(self.refresh)
        translator.language_changed.connect(self.refresh)
        self.refresh()

    @staticmethod
    def _mk_btn(text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedWidth(36)
        return btn

    def refresh(self) -> None:
        self.name_label.setText(self.script.name)
        self.run_btn.setToolTip(tr("Run"))
        self.stop_btn.setToolTip(tr("Stop"))
        self.copy_btn.setToolTip(tr("Copy command to clipboard"))
        self.edit_btn.setToolTip(tr("Edit"))
        self.delete_btn.setToolTip(tr("Delete"))

        if self.script.is_running:
            if self.script.waiting_input:
                self.dot.setStyleSheet("color: #f39c12; font-size: 16px;")
            else:
                self.dot.setStyleSheet("color: #2ecc71; font-size: 16px;")
            self.run_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.edit_btn.setEnabled(False)
        else:
            self.dot.setStyleSheet("color: #888; font-size: 16px;")
            self.run_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.edit_btn.setEnabled(True)

        self.dot.setToolTip(self._tooltip())

    def eventFilter(self, obj, event) -> bool:
        if obj is self.dot and event.type() == QEvent.ToolTip:
            self.dot.setToolTip(self._tooltip())
        return super().eventFilter(obj, event)

    def _tooltip(self) -> str:
        s = self.script
        if s.is_running:
            head = (
                tr("Waiting for input on stdin") if s.waiting_input else tr("Running")
            )
            if s.last_started_at is None:
                return head
            elapsed = (datetime.now() - s.last_started_at).total_seconds()
            return tr("{head}\nstarted: {start} · {elapsed} · {size}").format(
                head=head,
                start=s.last_started_at.strftime("%H:%M:%S"),
                elapsed=format_duration(elapsed),
                size=format_bytes(s.bytes_received),
            )
        if s.last_started_at is None:
            return tr("Not running")
        duration = (
            (s.last_finished_at - s.last_started_at).total_seconds()
            if s.last_finished_at
            else 0
        )
        return tr(
            "Not running\nlast: {start} · {duration} · exit {code} · {size}"
        ).format(
            start=s.last_started_at.strftime("%H:%M:%S"),
            duration=format_duration(duration),
            code=s.last_exit_code if s.last_exit_code is not None else "?",
            size=format_bytes(s.bytes_received),
        )
