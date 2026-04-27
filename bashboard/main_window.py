import os
import re
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QActionGroup, QCloseEvent, QGuiApplication
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from . import settings as settings_module
from .category_item import CategoryItem
from .edit_dialog import EditDialog
from .i18n import SUPPORTED_LANGUAGES, translator, tr
from .log_panel import LogPanel
from .manager import Category, Manager
from .script import Script
from .script_item import ScriptItem
from .script_tree import ScriptTree
from .theme import SUPPORTED_THEMES, theme_manager

LANGUAGE_NAMES = {"en": "English", "ru": "Русский"}
THEME_LABELS = {"system": "System", "light": "Light", "dark": "Dark"}


class MainWindow(QMainWindow):
    def __init__(self, config_path=None):
        super().__init__()
        self.setWindowTitle("Bashboard")
        self.resize(1100, 650)

        self.manager = Manager(config_path)
        self.manager.load()

        # Maps stable ints (stored in tree items as Qt.UserRole) to Script /
        # Category instances. We can't store Python QObjects on items
        # directly because Qt tries to pickle them for drag-drop mime data.
        self._next_id = 0
        self._objects: dict = {}

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

        self.tree = ScriptTree()
        self.tree.currentItemChanged.connect(self._on_current_changed)
        self.tree.itemExpanded.connect(self._on_expanded)
        self.tree.itemCollapsed.connect(self._on_collapsed)
        self.tree.itemDoubleClicked.connect(self._on_double_clicked)
        self.tree.drop_requested.connect(self._on_drop)
        left_layout.addWidget(self.tree, 1)

        splitter.addWidget(left)

        self.log_panel = LogPanel()
        splitter.addWidget(self.log_panel)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([420, 680])

        self._populate_tree()

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

    # ----- tree population -----

    def _data(self, item) -> Optional[object]:
        if item is None:
            return None
        oid = item.data(0, Qt.UserRole)
        return self._objects.get(oid) if oid is not None else None

    def _set_data(self, item, obj) -> None:
        self._next_id += 1
        self._objects[self._next_id] = obj
        item.setData(0, Qt.UserRole, self._next_id)

    def _populate_tree(self) -> None:
        """Rebuild the entire tree from manager.items. Called after every
        structural change. Preserves current selection by Script identity."""
        current_script = self._current_script()
        self._objects.clear()
        self._next_id = 0
        self.tree.blockSignals(True)
        self.tree.clear()
        for item in self.manager.items:
            if isinstance(item, Script):
                self._add_script_row(item, parent=None)
            else:
                self._add_category_row(item)
        self.tree.blockSignals(False)
        if current_script is not None:
            self._select_script(current_script)

    def _add_script_row(
        self, script: Script, parent: Optional[QTreeWidgetItem]
    ) -> QTreeWidgetItem:
        item = QTreeWidgetItem(parent or self.tree.invisibleRootItem())
        self._set_data(item, script)
        # Drop must be enabled even for scripts so that dropIndicatorPosition()
        # can return OnItem (needed for the "drop A onto B → create category"
        # gesture). Our dropEvent override controls what actually happens.
        item.setFlags(item.flags() | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)
        widget = ScriptItem(script)
        widget.run_clicked.connect(lambda s=script: self._run(s))
        widget.stop_clicked.connect(lambda s=script: self._stop(s))
        widget.copy_clicked.connect(lambda s=script: self._copy(s))
        widget.edit_clicked.connect(lambda s=script: self._edit(s))
        widget.delete_clicked.connect(lambda s=script: self._delete(s))
        item.setSizeHint(0, widget.sizeHint())
        self.tree.setItemWidget(item, 0, widget)
        return item

    def _add_category_row(self, category: Category) -> QTreeWidgetItem:
        item = QTreeWidgetItem(self.tree.invisibleRootItem())
        self._set_data(item, category)
        item.setFlags(item.flags() | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)
        widget = CategoryItem(category)
        widget.toggle_clicked.connect(lambda i=item: i.setExpanded(not i.isExpanded()))
        item.setSizeHint(0, widget.sizeHint())
        self.tree.setItemWidget(item, 0, widget)
        for s in category.scripts:
            self._add_script_row(s, parent=item)
        item.setExpanded(getattr(category, "_expanded", True))
        widget.set_expanded(item.isExpanded())
        return item

    # ----- selection / log panel sync -----

    def _current_script(self) -> Optional[Script]:
        data = self._data(self.tree.currentItem())
        return data if isinstance(data, Script) else None

    def _on_current_changed(
        self,
        current: Optional[QTreeWidgetItem],
        _previous: Optional[QTreeWidgetItem],
    ) -> None:
        if current is None:
            self.log_panel.attach(None)
            return
        data = self._data(current)
        self.log_panel.attach(data if isinstance(data, Script) else None)

    def _select_script(self, script: Script) -> None:
        for item in self._iter_items():
            if self._data(item) is script:
                self.tree.setCurrentItem(item)
                return

    def _iter_items(self):
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            top = root.child(i)
            yield top
            for j in range(top.childCount()):
                yield top.child(j)

    def _on_expanded(self, item: QTreeWidgetItem) -> None:
        data = self._data(item)
        if isinstance(data, Category):
            data._expanded = True
            widget = self.tree.itemWidget(item, 0)
            if isinstance(widget, CategoryItem):
                widget.set_expanded(True)

    def _on_collapsed(self, item: QTreeWidgetItem) -> None:
        data = self._data(item)
        if isinstance(data, Category):
            data._expanded = False
            widget = self.tree.itemWidget(item, 0)
            if isinstance(widget, CategoryItem):
                widget.set_expanded(False)

    def _on_double_clicked(self, item: QTreeWidgetItem, _column: int) -> None:
        data = self._data(item)
        if isinstance(data, Category):
            self._rename_category(data)

    # ----- drag-drop handling -----

    def _on_drop(
        self,
        source_item: QTreeWidgetItem,
        target_item: Optional[QTreeWidgetItem],
        position,
    ) -> None:
        source = self._data(source_item)
        target = self._data(target_item) if target_item else None

        if source is target:
            return

        target_in_category = (
            target_item is not None and target_item.parent() is not None
        )

        # Validation: categories cannot be nested.
        if isinstance(source, Category):
            if target_in_category:
                return
            if position == QAbstractItemView.OnItem and isinstance(target, Category):
                return

        # Special gesture: drop one top-level script onto another → category.
        if (
            isinstance(source, Script)
            and isinstance(target, Script)
            and target_item is not None
            and target_item.parent() is None
            and position == QAbstractItemView.OnItem
        ):
            if not self._make_category(source, target):
                return
            self._populate_tree()
            self._select_script(source)
            return

        # Regular reorder / move.
        self._move(source, target, target_item, position)
        self._populate_tree()
        if isinstance(source, Script):
            self._select_script(source)

    def _make_category(self, dragged: Script, drop_target: Script) -> bool:
        name = self._default_category_name()
        items = self.manager.items
        self._remove_from(items, dragged)
        target_idx = items.index(drop_target)
        items.pop(target_idx)
        items.insert(target_idx, Category(name, [drop_target, dragged]))
        self.manager._auto_flatten()
        self.manager.save()
        return True

    def _default_category_name(self) -> str:
        base = tr("New category")
        existing = {it.name for it in self.manager.items if isinstance(it, Category)}
        if base not in existing:
            return base
        n = 2
        while f"{base} {n}" in existing:
            n += 1
        return f"{base} {n}"

    def _rename_category(self, category: Category) -> None:
        name, ok = QInputDialog.getText(
            self,
            tr("Rename category"),
            tr("Category name:"),
            text=category.name,
        )
        if not ok or not name.strip() or name.strip() == category.name:
            return
        category.name = name.strip()
        self.manager.save()
        self._populate_tree()

    def _move(
        self,
        source,
        target,
        target_item: Optional[QTreeWidgetItem],
        position,
    ) -> None:
        items = self.manager.items
        self._remove_from(items, source)

        if target is None:
            items.append(source)
        elif (
            position == QAbstractItemView.OnItem
            and isinstance(target, Category)
            and isinstance(source, Script)
        ):
            target.scripts.append(source)
        elif target_item is not None and target_item.parent() is not None:
            parent_cat = self._data(target_item.parent())
            idx = parent_cat.scripts.index(target)
            if position == QAbstractItemView.BelowItem:
                idx += 1
            parent_cat.scripts.insert(idx, source)
        else:
            idx = items.index(target)
            if position == QAbstractItemView.BelowItem:
                idx += 1
            items.insert(idx, source)

        self.manager._auto_flatten()
        self.manager.save()

    @staticmethod
    def _remove_from(items: list, target) -> None:
        if target in items:
            items.remove(target)
            return
        for it in items:
            if isinstance(it, Category) and target in it.scripts:
                it.scripts.remove(target)
                return

    # ----- file system / dialog helpers -----

    def _resolve_path(self, path: str) -> str:
        if not path or os.path.isabs(path):
            return path
        return os.path.join(str(self.manager.config_path.parent), path)

    def _auto_path(self, name: str) -> str:
        """Pick a unique relative path under <config_dir>/scripts/ from the
        script name. Returned path is relative to config_path.parent."""
        scripts_dir = self.manager.config_path.parent / "scripts"
        safe = re.sub(r"[^a-zA-Z0-9._-]+", "_", name).strip("_") or "script"
        if not safe.endswith(".sh"):
            safe += ".sh"
        candidate = safe
        n = 1
        while (scripts_dir / candidate).exists():
            n += 1
            candidate = f"{safe[:-3]}-{n}.sh"
        return f"scripts/{candidate}"

    def _write_content(self, path: str, content: Optional[str]) -> bool:
        """Write inline editor content to the script file. Returns False if the
        write failed (after showing an error). content=None means the user did
        not touch the editor — leave the file untouched. Creates the file if
        it does not exist and makes it executable."""
        resolved = self._resolve_path(path)
        p = Path(resolved)
        creating = not p.exists()
        if content is None and not creating:
            return True
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content or "", encoding="utf-8")
            if creating or not os.access(resolved, os.X_OK):
                os.chmod(resolved, 0o755)
        except OSError as e:
            QMessageBox.warning(self, tr("Error"), str(e))
            return False
        return True

    # ----- script actions -----

    def _add(self) -> None:
        dlg = EditDialog(self, base_dir=str(self.manager.config_path.parent))
        if dlg.exec() != EditDialog.Accepted:
            return
        name, path, args, cwd, content = dlg.values()
        if not name:
            QMessageBox.warning(self, tr("Error"), tr("Specify a name."))
            return
        if not path:
            if not content:
                QMessageBox.warning(
                    self,
                    tr("Error"),
                    tr("Specify a file path or type the script content."),
                )
                return
            path = self._auto_path(name)
        if not self._write_content(path, content):
            return
        script = Script(name, path, args, cwd)
        self.manager.add(script)
        self._populate_tree()
        self._select_script(script)

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

    def _edit(self, script: Script) -> None:
        if script.is_running:
            QMessageBox.information(
                self,
                tr("Script is running"),
                tr("Stop the script before editing."),
            )
            return
        dlg = EditDialog(
            self,
            script.name,
            script.path,
            script.args,
            script.cwd,
            base_dir=str(self.manager.config_path.parent),
        )
        if dlg.exec() != EditDialog.Accepted:
            return
        name, path, args, cwd, content = dlg.values()
        if not name:
            QMessageBox.warning(self, tr("Error"), tr("Specify a name."))
            return
        if not path:
            if not content:
                QMessageBox.warning(
                    self,
                    tr("Error"),
                    tr("Specify a file path or type the script content."),
                )
                return
            path = self._auto_path(name)
        if not self._write_content(path, content):
            return
        script.name = name
        script.path = path
        script.args = args
        script.cwd = cwd
        self.manager.save()
        self._populate_tree()
        self._select_script(script)

    def _delete(self, script: Script) -> None:
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
        self._populate_tree()
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
