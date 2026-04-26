import os
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QProcess
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QWidget,
)

from .i18n import tr


class EditDialog(QDialog):
    def __init__(
        self,
        parent=None,
        name: str = "",
        path: str = "",
        args: str = "",
        cwd: str = "",
        base_dir: Optional[str] = None,
    ):
        super().__init__(parent)
        self.setWindowTitle(tr("Script"))
        self.resize(720, 540)
        self._base_dir = base_dir

        form = QFormLayout(self)

        self.name_edit = QLineEdit(name)
        self.name_edit.setPlaceholderText(tr("e.g. Backup DB"))
        form.addRow(tr("Name:"), self.name_edit)

        self.path_edit = QLineEdit(path)
        self.path_edit.setPlaceholderText("/path/to/script.sh")
        self.path_edit.textChanged.connect(self._update_external_button)
        self.path_edit.editingFinished.connect(self._on_path_changed)
        self._last_loaded_path = path
        path_browse = QPushButton(tr("Browse…"))
        path_browse.clicked.connect(self._browse_path)
        form.addRow(tr("File:"), self._row(self.path_edit, path_browse))

        self.cwd_edit = QLineEdit(cwd)
        self.cwd_edit.setPlaceholderText(tr("(default: directory of the script)"))
        cwd_browse = QPushButton(tr("Browse…"))
        cwd_browse.clicked.connect(self._browse_cwd)
        form.addRow(tr("Working dir:"), self._row(self.cwd_edit, cwd_browse))

        self.args_edit = QLineEdit(args)
        self.args_edit.setPlaceholderText("--days 30 --dry-run")
        form.addRow(tr("Arguments:"), self.args_edit)

        content_header = QHBoxLayout()
        content_header.addWidget(QLabel(tr("Content:")))
        content_header.addStretch(1)
        self.external_btn = QPushButton(tr("Open in external editor"))
        self.external_btn.clicked.connect(self._open_external)
        content_header.addWidget(self.external_btn)
        form.addRow(content_header)

        self.content_edit = QPlainTextEdit()
        mono = QFont("Monospace")
        mono.setStyleHint(QFont.TypeWriter)
        self.content_edit.setFont(mono)
        self.content_edit.setTabChangesFocus(False)
        form.addRow(self.content_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

        self._load_content(path)
        self._update_external_button()

    @staticmethod
    def _row(*widgets) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        for w in widgets:
            layout.addWidget(w)
        return row

    def _browse_path(self) -> None:
        if self._content_dirty():
            confirm = QMessageBox.question(
                self,
                tr("Unsaved changes"),
                tr("Discard typed content and load the picked file?"),
            )
            if confirm != QMessageBox.Yes:
                return
        path, _ = QFileDialog.getOpenFileName(
            self,
            tr("Select bash script"),
            self.path_edit.text() or str(Path.home()),
            "Bash scripts (*.sh);;All files (*)",
        )
        if not path:
            return
        self.path_edit.setText(path)
        if not self.name_edit.text().strip():
            self.name_edit.setText(Path(path).stem)
        self._load_content(path)
        self._last_loaded_path = path
        self._update_external_button()

    def _on_path_changed(self) -> None:
        new_path = self.path_edit.text().strip()
        if new_path == self._last_loaded_path:
            return
        self._last_loaded_path = new_path
        if not new_path:
            return
        if not Path(self._resolve(new_path)).is_file():
            # Non-existent path: user is specifying where to save; keep content.
            return
        if self._content_dirty():
            confirm = QMessageBox.question(
                self,
                tr("Unsaved changes"),
                tr("Discard typed content and load the picked file?"),
            )
            if confirm != QMessageBox.Yes:
                return
        self._load_content(new_path)

    def _content_dirty(self) -> bool:
        return (
            self.content_edit.document().isModified()
            and self.content_edit.toPlainText() != ""
        )

    def _browse_cwd(self) -> None:
        start = (
            self.cwd_edit.text()
            or os.path.dirname(self.path_edit.text())
            or str(Path.home())
        )
        directory = QFileDialog.getExistingDirectory(
            self, tr("Select working directory"), start
        )
        if directory:
            self.cwd_edit.setText(directory)

    def _resolve(self, path: str) -> str:
        if not path or os.path.isabs(path) or not self._base_dir:
            return path
        return os.path.join(self._base_dir, path)

    def _load_content(self, path: str) -> None:
        resolved = self._resolve(path)
        if resolved and Path(resolved).is_file():
            try:
                text = Path(resolved).read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                text = ""
            self.content_edit.setPlainText(text)
        else:
            self.content_edit.setPlainText("")
        # setPlainText flips the modified flag; reset so isModified() truly
        # reflects whether the user typed anything.
        self.content_edit.document().setModified(False)

    def _update_external_button(self) -> None:
        resolved = self._resolve(self.path_edit.text().strip())
        self.external_btn.setEnabled(bool(resolved) and Path(resolved).is_file())

    def _open_external(self) -> None:
        resolved = self._resolve(self.path_edit.text().strip())
        if not resolved or not Path(resolved).is_file():
            return
        if self.content_edit.document().isModified():
            confirm = QMessageBox.question(
                self,
                tr("Unsaved changes"),
                tr("Discard inline changes and open in external editor?"),
            )
            if confirm != QMessageBox.Yes:
                return
        editor = os.environ.get("VISUAL") or os.environ.get("EDITOR")
        if editor:
            QProcess.startDetached(editor, [resolved])
        else:
            QProcess.startDetached("xdg-open", [resolved])
        self.reject()

    def values(self) -> tuple[str, str, str, str, Optional[str]]:
        """Returns (name, path, args, cwd, content_or_None).
        content is None if the editor was not modified — caller should leave
        the file untouched in that case."""
        content = (
            self.content_edit.toPlainText()
            if self.content_edit.document().isModified()
            else None
        )
        return (
            self.name_edit.text().strip(),
            self.path_edit.text().strip(),
            self.args_edit.text().strip(),
            self.cwd_edit.text().strip(),
            content,
        )
