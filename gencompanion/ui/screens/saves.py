"""Save browser. Read-only, by design — see the spec's design boundary.

Nothing on this screen writes to a save file. There is no edit control and no
code path that opens a save for writing.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
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

        save_dirs = [
            (install.label, install.save_dir)
            for install in installs
            if install.save_dir is not None
        ]

        if not save_dirs:
            self.add(Banner("No save folders found.", "warn"))
            self.add_stretch()
            return

        self.table = QTableWidget(0, len(_COLUMNS))
        self.table.setHorizontalHeaderLabels(_COLUMNS)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        for col in (0, 1, 3, 4, 5):
            header.setSectionResizeMode(col, QHeaderView.ResizeToContents)

        total = 0
        problems = 0
        rows: list[tuple[str, object]] = []

        for _label, save_dir in save_dirs:
            for info in list_saves(save_dir):
                rows.append((_label, info))
                total += 1
                if not info.valid:
                    problems += 1

        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for row, (_label, info) in enumerate(rows):
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

        summary = f"{total} saves"
        if problems:
            summary += f"  ·  {problems} unreadable"
        self.add(Banner(summary, "warn" if problems else "info"))
        self.table.setMinimumHeight(420)
        self.add(self.table, stretch=1)
