from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QActionGroup, QCloseEvent, QGuiApplication
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from . import settings as settings_module
from .edit_dialog import EditDialog
from .i18n import SUPPORTED_LANGUAGES, translator, tr
from .log_panel import LogPanel
from .manager import Manager
from .script import Script
from .script_item import ScriptItem
from .theme import SUPPORTED_THEMES, theme_manager

LANGUAGE_NAMES = {"en": "English", "ru": "Русский"}
THEME_LABELS = {"system": "System", "light": "Light", "dark": "Dark"}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bashboard")
        self.resize(1100, 650)

        self.manager = Manager()
        self.manager.load()

        self._build_menu()

        splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(splitter)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(8, 8, 8, 8)

        header = QHBoxLayout()
        self.scripts_label = QLabel()
        header.addWidget(self.scripts_label)
        header.addStretch(1)
        self.add_btn = QPushButton()
        self.add_btn.clicked.connect(self._add)
        header.addWidget(self.add_btn)
        left_layout.addLayout(header)

        self.list_widget = QListWidget()
        self.list_widget.currentItemChanged.connect(self._on_current_changed)
        left_layout.addWidget(self.list_widget, 1)

        splitter.addWidget(left)

        self.log_panel = LogPanel()
        splitter.addWidget(self.log_panel)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([420, 680])

        for script in self.manager.scripts:
            self._add_item(script)

        translator.language_changed.connect(self._retranslate)
        self._retranslate()

    def _build_menu(self) -> None:
        menubar = self.menuBar()

        self.file_menu = menubar.addMenu("")
        self.add_action = QAction(self)
        self.add_action.triggered.connect(self._add)
        self.file_menu.addAction(self.add_action)
        self.file_menu.addSeparator()
        self.quit_action = QAction(self)
        self.quit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.quit_action)

        self.settings_menu = menubar.addMenu("")
        self.language_menu = self.settings_menu.addMenu("")

        self.lang_group = QActionGroup(self)
        self.lang_group.setExclusive(True)
        self.lang_actions: dict[str, QAction] = {}
        for code in SUPPORTED_LANGUAGES:
            action = QAction(LANGUAGE_NAMES[code], self)
            action.setCheckable(True)
            action.setChecked(code == translator.current)
            action.triggered.connect(
                lambda _checked=False, c=code: self._switch_language(c)
            )
            self.lang_group.addAction(action)
            self.language_menu.addAction(action)
            self.lang_actions[code] = action

        self.theme_menu = self.settings_menu.addMenu("")
        self.theme_group = QActionGroup(self)
        self.theme_group.setExclusive(True)
        self.theme_actions: dict[str, QAction] = {}
        for code in SUPPORTED_THEMES:
            action = QAction(self)
            action.setCheckable(True)
            action.setChecked(code == theme_manager.current)
            action.triggered.connect(
                lambda _checked=False, c=code: self._switch_theme(c)
            )
            self.theme_group.addAction(action)
            self.theme_menu.addAction(action)
            self.theme_actions[code] = action

    def _switch_language(self, code: str) -> None:
        cfg = settings_module.load()
        cfg["language"] = code
        settings_module.save(cfg)
        translator.set_language(code)

    def _switch_theme(self, code: str) -> None:
        cfg = settings_module.load()
        cfg["theme"] = code
        settings_module.save(cfg)
        theme_manager.set_theme(code)

    def _retranslate(self) -> None:
        self.file_menu.setTitle(tr("File"))
        self.settings_menu.setTitle(tr("Settings"))
        self.language_menu.setTitle(tr("Language"))
        self.theme_menu.setTitle(tr("Theme"))
        self.add_action.setText(tr("Add script…"))
        self.quit_action.setText(tr("Quit"))
        self.scripts_label.setText(f"<b>{tr('Scripts')}</b>")
        self.add_btn.setText(tr("+ Add"))
        for code, action in self.lang_actions.items():
            action.setChecked(code == translator.current)
        for code, action in self.theme_actions.items():
            action.setText(tr(THEME_LABELS[code]))
            action.setChecked(code == theme_manager.current)

    def _add_item(self, script: Script) -> QListWidgetItem:
        item = QListWidgetItem(self.list_widget)
        widget = ScriptItem(script)
        widget.run_clicked.connect(lambda s=script: self._run(s))
        widget.stop_clicked.connect(lambda s=script: self._stop(s))
        widget.copy_clicked.connect(lambda s=script: self._copy(s))
        widget.edit_clicked.connect(lambda s=script, w=widget: self._edit(s, w))
        widget.delete_clicked.connect(lambda s=script, i=item: self._delete(s, i))
        item.setData(Qt.UserRole, script)
        item.setSizeHint(widget.sizeHint())
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, widget)
        return item

    def _on_current_changed(self, current: QListWidgetItem, _previous) -> None:
        if current is None:
            self.log_panel.attach(None)
            return
        script = current.data(Qt.UserRole)
        self.log_panel.attach(script)

    def _select_script(self, script: Script) -> None:
        for i in range(self.list_widget.count()):
            if self.list_widget.item(i).data(Qt.UserRole) is script:
                self.list_widget.setCurrentRow(i)
                return

    def _add(self) -> None:
        dlg = EditDialog(self)
        if dlg.exec() != EditDialog.Accepted:
            return
        name, path, args = dlg.values()
        if not name or not path:
            QMessageBox.warning(self, tr("Error"), tr("Specify name and path."))
            return
        script = Script(name, path, args)
        self.manager.add(script)
        self._add_item(script)

    def _run(self, script: Script) -> None:
        if script.is_running:
            return
        script.start()
        self._select_script(script)

    def _stop(self, script: Script) -> None:
        if not script.is_running:
            return
        script.stop()

    def _copy(self, script: Script) -> None:
        cmd = script.command()
        QGuiApplication.clipboard().setText(cmd)
        self.statusBar().showMessage(tr("Copied: {cmd}").format(cmd=cmd), 3000)

    def _edit(self, script: Script, widget: ScriptItem) -> None:
        if script.is_running:
            QMessageBox.information(
                self,
                tr("Script is running"),
                tr("Stop the script before editing."),
            )
            return
        dlg = EditDialog(self, script.name, script.path, script.args)
        if dlg.exec() != EditDialog.Accepted:
            return
        name, path, args = dlg.values()
        if not name or not path:
            QMessageBox.warning(self, tr("Error"), tr("Specify name and path."))
            return
        script.name = name
        script.path = path
        script.args = args
        self.manager.save()
        widget.refresh()
        if self.log_panel.script is script:
            self.log_panel.refresh_title()

    def _delete(self, script: Script, item: QListWidgetItem) -> None:
        confirm = QMessageBox.question(
            self,
            tr("Delete"),
            tr(
                "Delete '{name}' from the list?\n(The script file on disk will remain.)"
            ).format(name=script.name),
        )
        if confirm != QMessageBox.Yes:
            return
        if script.is_running:
            script.stop()
        self.manager.remove(script)
        row = self.list_widget.row(item)
        self.list_widget.takeItem(row)
        if self.log_panel.script is script:
            self.log_panel.attach(None)

    def closeEvent(self, event: QCloseEvent) -> None:
        running = [s for s in self.manager.scripts if s.is_running]
        if running:
            confirm = QMessageBox.question(
                self,
                tr("Close Bashboard"),
                tr("{count} script(s) running. Stop them and exit?").format(
                    count=len(running)
                ),
            )
            if confirm != QMessageBox.Yes:
                event.ignore()
                return
            for script in running:
                script.stop()
        event.accept()
