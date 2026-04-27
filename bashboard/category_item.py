from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QToolButton,
    QWidget,
)

from .manager import Category


class CategoryItem(QWidget):
    """Row widget shown for a category in the tree. Visually a section header:
    bold larger label on the left, disclosure chevron on the right (Qt's
    default decoration on the left is hidden)."""

    toggle_clicked = Signal()

    def __init__(self, category: Category):
        super().__init__()
        self.category = category

        # Tinted background so categories clearly read as section headers.
        # In dark themes lighten the base; in light themes a slight darken
        # gives just enough contrast against scripts below.
        # WA_StyledBackground is required so the stylesheet bg actually paints
        # over the QTreeWidget's own item background.
        self.setAttribute(Qt.WA_StyledBackground, True)
        bg = self.palette().color(QPalette.Base)
        bg = bg.lighter(150) if bg.lightness() < 128 else bg.darker(108)
        self.setStyleSheet(f"background-color: {bg.name()};")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 6, 6)
        layout.setSpacing(8)

        self.name_label = QLabel(category.name)
        font = self.name_label.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 1)
        self.name_label.setFont(font)
        self.name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(self.name_label, 1)

        self.chevron = QToolButton()
        self.chevron.setAutoRaise(True)
        self.chevron.setText("▼")
        self.chevron.setFixedWidth(28)
        self.chevron.clicked.connect(self.toggle_clicked.emit)
        layout.addWidget(self.chevron)

    def set_name(self, name: str) -> None:
        self.category.name = name
        self.name_label.setText(name)

    def set_expanded(self, expanded: bool) -> None:
        self.chevron.setText("▼" if expanded else "▶")
