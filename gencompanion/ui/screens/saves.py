"""Save browser. Read-only, by design — see the spec's design boundary.

Nothing on this screen writes to a save file. There is no edit control and no
code path that opens a save for writing.

A folder can also be browsed directly, so saves copied from another machine
can be inspected without configuring anything.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from ...domain.detect import GameInstall
from ...formats.save import list_saves
from ..widgets import Banner, Screen, human_size

_COLUMNS = ("File", "Kind", "Description", "Map", "Size", "Modified")


class SavesScreen(Screen):
    def __init__(self, installs: list[GameInstall]) -> None:
        super().__init__(
            "Saves",
            "Read-only. This tool never modifies save files.",
        )

        self._save_dirs: list[tuple[str, Path]] = [
            (install.label, install.save_dir)
            for install in installs
            if install.save_dir is not None
        ]

        self.status = Banner("", "info")
        self.add(self.status)

        # Secondary action: keep it to its own width rather than spanning
        # the page like a primary call to action.
        bar = QWidget()
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(0, 0, 0, 0)
        self.browse_button = QPushButton("Browse another folder…")
        self.browse_button.clicked.connect(self._browse)
        bar_layout.addWidget(self.browse_button)
        bar_layout.addStretch(1)
        self.add(bar)

        self.table = self._make_table()
        self.table.setMinimumHeight(420)
        self.add(self.table, stretch=1)

        if self._save_dirs:
            self._reload()
        else:
            self.browse_button.setText("Browse a save folder…")
            self.browse_button.setProperty("variant", "primary")
            self.status.setProperty("role", "banner-warn")
            self.status.set_text(
                "No save folders found. Use Overview to locate your save and "
                "config folder, or browse a folder directly."
            )

    # -- table ---------------------------------------------------------

    def _make_table(self) -> QTableWidget:
        table = QTableWidget(0, len(_COLUMNS))
        table.setHorizontalHeaderLabels(_COLUMNS)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSortingEnabled(True)
        table.setShowGrid(False)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(30)

        header = table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        for col in (0, 1, 3, 4, 5):
            header.setSectionResizeMode(col, QHeaderView.ResizeToContents)
        return table

    def _reload(self) -> None:
        rows = []
        problems = 0

        for _label, save_dir in self._save_dirs:
            for info in list_saves(save_dir):
                rows.append(info)
                if not info.valid:
                    problems += 1

        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))

        for row, info in enumerate(rows):
            self.table.setItem(row, 0, QTableWidgetItem(info.filename))
            self.table.setItem(row, 1, QTableWidgetItem(info.kind))
            self.table.setItem(row, 2, QTableWidgetItem(info.display_name))
            self.table.setItem(row, 3, QTableWidgetItem(info.map_name or "—"))

            size_item = QTableWidgetItem()
            size_item.setData(Qt.DisplayRole, info.size)
            size_item.setText(human_size(info.size))
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 4, size_item)

            self.table.setItem(
                row,
                5,
                QTableWidgetItem(info.timestamp.strftime("%Y-%m-%d %H:%M")),
            )

        self.table.setSortingEnabled(True)

        summary = f"{len(rows)} saves"
        if len(self._save_dirs) > 1:
            summary += f" across {len(self._save_dirs)} folders"
        if problems:
            summary += f"  ·  {problems} unreadable"
        self.status.set_text(summary)

    def _browse(self) -> None:
        chosen = QFileDialog.getExistingDirectory(
            self, "Select a folder containing .sav files"
        )
        if not chosen:
            return

        path = Path(chosen)
        found = list_saves(path)
        if not found:
            self.status.set_text(f"No .sav files found in {path}")
            return

        self._save_dirs = [(path.name, path)]
        self.browse_button.setText("Browse another folder…")
        self._reload()
