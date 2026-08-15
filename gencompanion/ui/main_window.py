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
from ..domain.settings import Settings
from .screens.archive import ArchiveScreen
from .screens.backups import BackupsScreen
from .screens.display import DisplayScreen
from .screens.launch import LaunchScreen
from .screens.saves import SavesScreen
from .screens.welcome import WelcomeScreen
from .tokens import DARK, LIGHT, stylesheet

_RAIL_WIDTH = 188
_SCREENS = (
    "Overview",
    "Display",
    "Launch options",
    "Saves",
    "Archive",
    "Backups",
)


class MainWindow(QMainWindow):
    def __init__(self, dark: bool = True) -> None:
        super().__init__()
        self.setWindowTitle("Generals Companion")
        self.resize(1180, 760)
        self.setMinimumSize(QSize(880, 560))
        self.setStyleSheet(stylesheet(DARK if dark else LIGHT))

        self.settings = Settings.load()

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.rail = QListWidget()
        self.rail.setObjectName("rail")
        self.rail.setFixedWidth(_RAIL_WIDTH)
        self.rail.setFocusPolicy(Qt.NoFocus)
        for name in _SCREENS:
            item = QListWidgetItem(name)
            item.setSizeHint(QSize(0, 40))
            self.rail.addItem(item)

        self.stack = QStackedWidget()
        self.rail.currentRowChanged.connect(self.stack.setCurrentIndex)

        layout.addWidget(self.rail)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(central)

        self._build_screens()
        self.rail.setCurrentRow(0)

    def _build_screens(self) -> None:
        """(Re)create every screen from current settings.

        Called on startup and again whenever the user changes a path, so a
        newly located save folder shows up immediately rather than needing a
        restart.
        """
        current_row = self.rail.currentRow()

        while self.stack.count():
            widget = self.stack.widget(0)
            self.stack.removeWidget(widget)
            widget.deleteLater()

        installs = detect_installs(self.settings.overrides)
        primary = next(
            (i for i in installs if i.edition == "zerohour"),
            installs[0] if installs else None,
        )

        welcome = WelcomeScreen(installs, self.settings)
        welcome.paths_changed.connect(self._build_screens)

        self.stack.addWidget(welcome)
        self.stack.addWidget(DisplayScreen(primary))
        self.stack.addWidget(LaunchScreen(primary))
        self.stack.addWidget(SavesScreen(installs))
        self.stack.addWidget(ArchiveScreen())
        self.stack.addWidget(BackupsScreen())

        if 0 <= current_row < self.stack.count():
            self.stack.setCurrentIndex(current_row)
