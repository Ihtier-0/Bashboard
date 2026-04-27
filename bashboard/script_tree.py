from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QDrag, QDragMoveEvent, QPainter, QPixmap
from PySide6.QtWidgets import QAbstractItemView, QTreeWidget


class ScriptTree(QTreeWidget):
    """Tree widget for the script list. Supports drag-drop reorder and a
    custom 'drop script onto another script to create a category' gesture.

    The tree does not perform the drop itself — it emits drop_requested with
    enough info for the parent to mutate the model and rebuild."""

    drop_requested = Signal(
        object, object, object
    )  # source_item, target_item_or_None, DropIndicatorPosition

    def __init__(self):
        super().__init__()
        self.setHeaderHidden(True)
        self.setRootIsDecorated(False)  # hide built-in left chevron
        self.setIndentation(24)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)

    def startDrag(self, supportedActions) -> None:
        # Default Qt drag pixmap is empty for items using setItemWidget — the
        # delegate (which is empty) is rendered, not the widget. Build the
        # pixmap from the actual row widget. For expanded categories, stack
        # the children widgets below the header so the user sees what's being
        # moved as a group.
        item = self.currentItem()
        if item is None:
            return super().startDrag(supportedActions)
        widget = self.itemWidget(item, 0)
        if widget is None:
            return super().startDrag(supportedActions)

        indexes = [self.indexFromItem(item, 0)]
        drag = QDrag(self.viewport())
        drag.setMimeData(self.model().mimeData(indexes))
        pixmap = self._build_drag_pixmap(item, widget)
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(20, min(widget.height() // 2, pixmap.height() // 2)))
        drag.exec(supportedActions, Qt.MoveAction)

    def _build_drag_pixmap(self, item, header_widget) -> QPixmap:
        pixmaps = [header_widget.grab()]
        # Include expanded category children (one level only — categories
        # cannot nest).
        if item.parent() is None and item.isExpanded():
            for i in range(item.childCount()):
                child = item.child(i)
                child_widget = self.itemWidget(child, 0)
                if child_widget is not None:
                    pixmaps.append(child_widget.grab())
        if len(pixmaps) == 1:
            return pixmaps[0]
        width = max(p.width() for p in pixmaps)
        height = sum(p.height() for p in pixmaps)
        combined = QPixmap(width, height)
        combined.fill(Qt.transparent)
        painter = QPainter(combined)
        y = 0
        for p in pixmaps:
            painter.drawPixmap(0, y, p)
            y += p.height()
        painter.end()
        return combined

    def _adjusted_pos(self, pos: QPoint) -> QPoint:
        """If pos is above the first item, snap it just inside the top of the
        first row so Qt computes AboveItem and draws an indicator."""
        first = self.topLevelItem(0)
        if first is None:
            return pos
        rect = self.visualItemRect(first)
        if pos.y() < rect.top():
            return QPoint(pos.x(), rect.top() + 1)
        return pos

    def dragMoveEvent(self, event) -> None:
        pos = event.position().toPoint()
        adjusted = self._adjusted_pos(pos)
        if adjusted != pos:
            new_event = QDragMoveEvent(
                adjusted,
                event.possibleActions(),
                event.mimeData(),
                event.buttons(),
                event.modifiers(),
            )
            super().dragMoveEvent(new_event)
            if new_event.isAccepted():
                event.accept()
            else:
                event.ignore()
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event) -> None:
        pos = event.position().toPoint()
        target_item = self.itemAt(pos)
        position = self.dropIndicatorPosition()

        # When the cursor is in viewport whitespace ABOVE the first item,
        # Qt reports OnViewport which we treat as "append to end". Treat it
        # instead as "above the first item" so the user can drop at the top.
        if target_item is None:
            first = self.topLevelItem(0)
            if first is not None:
                first_rect = self.visualItemRect(first)
                if pos.y() < first_rect.top():
                    target_item = first
                    position = QAbstractItemView.AboveItem

        source_items = self.selectedItems()
        if source_items:
            self.drop_requested.emit(source_items[0], target_item, position)
        # Force IgnoreAction so QAbstractItemView::startDrag() does NOT call
        # clearOrRemove() on its source after this returns. The parent already
        # rebuilt the tree from the updated model; if Qt then also removes
        # rows by stale persistent index, an item gets destroyed twice.
        event.setDropAction(Qt.IgnoreAction)
        event.accept()
