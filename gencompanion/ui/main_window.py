"""Main window: left rail, stacked screens."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

from ..domain.detect import detect_installs
from .screens.archive import ArchiveScreen
from .screens.launch import LaunchScreen
from .screens.saves import SavesScreen
from .screens.welcome import WelcomeScreen
from .tokens import DARK, LIGHT, stylesheet

_RAIL_WIDTH = 188


class MainWindow(QMainWindow):
    def __init__(self, dark: bool = True) -> None:
        super().__init__()
        self.setWindowTitle("Generals Companion")
        self.resize(1180, 760)
        self.setMinimumSize(QSize(880, 560))

        self.setStyleSheet(stylesheet(DARK if dark else LIGHT))

        installs = detect_installs()
        primary = next(
            (i for i in installs if i.edition == "zerohour"),
            installs[0] if installs else None,
        )

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.rail = QListWidget()
        self.rail.setObjectName("rail")
        self.rail.setFixedWidth(_RAIL_WIDTH)
        self.rail.setFocusPolicy(Qt.NoFocus)

        self.stack = QStackedWidget()

        self._add_screen("Overview", WelcomeScreen(installs))
        self._add_screen("Launch options", LaunchScreen(primary))
        self._add_screen("Saves", SavesScreen(installs))
        self._add_screen("Archive", ArchiveScreen())

        self.rail.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.rail.setCurrentRow(0)

        layout.addWidget(self.rail)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(central)

    def _add_screen(self, name: str, widget: QWidget) -> None:
        item = QListWidgetItem(name)
        item.setSizeHint(QSize(0, 40))
        self.rail.addItem(item)
        self.stack.addWidget(widget)
