from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QWidget,
)

from .i18n import tr


class EditDialog(QDialog):
    def __init__(self, parent=None, name: str = "", path: str = "", args: str = ""):
        super().__init__(parent)
        self.setWindowTitle(tr("Script"))
        self.resize(560, 0)

        form = QFormLayout(self)

        self.name_edit = QLineEdit(name)
        self.name_edit.setPlaceholderText(tr("e.g. Backup DB"))
        form.addRow(tr("Name:"), self.name_edit)

        path_row = QWidget()
        path_layout = QHBoxLayout(path_row)
        path_layout.setContentsMargins(0, 0, 0, 0)
        self.path_edit = QLineEdit(path)
        self.path_edit.setPlaceholderText("/path/to/script.sh")
        path_layout.addWidget(self.path_edit)
        browse_btn = QPushButton(tr("Browse…"))
        browse_btn.clicked.connect(self._browse)
        path_layout.addWidget(browse_btn)
        form.addRow(tr("File:"), path_row)

        self.args_edit = QLineEdit(args)
        self.args_edit.setPlaceholderText("--days 30 --dry-run")
        form.addRow(tr("Arguments:"), self.args_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _browse(self) -> None:
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

    def values(self) -> tuple[str, str, str]:
        return (
            self.name_edit.text().strip(),
            self.path_edit.text().strip(),
            self.args_edit.text().strip(),
        )
