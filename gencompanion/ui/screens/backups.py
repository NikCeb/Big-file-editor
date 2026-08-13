"""Backups screen: every write this app made, and how to undo it."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from ...safety.backup import Journal, restore, restore_to_stock
from ..tokens import Space
from ..widgets import Banner, Screen, human_size

_COLUMNS = ("When", "File", "Reason", "Size", "Kind")


class BackupsScreen(Screen):
    def __init__(self) -> None:
        super().__init__(
            "Backups",
            "Every file this app changed, with a copy of how it was before.",
        )
        self.journal = Journal.load()

        self.status = Banner("", "info")
        self.add(self.status)
        self.add(self._actions())

        self.table = QTableWidget(0, len(_COLUMNS))
        self.table.setHorizontalHeaderLabels(_COLUMNS)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        for col in (0, 1, 3, 4):
            header.setSectionResizeMode(col, QHeaderView.ResizeToContents)

        self.table.setMinimumHeight(360)
        self.add(self.table, stretch=1)
        self._reload()

    def _actions(self) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Space.md)

        self.restore_button = QPushButton("Restore selected")
        self.restore_button.clicked.connect(self._restore_selected)

        self.stock_button = QPushButton("Restore everything to stock")
        self.stock_button.setProperty("variant", "danger")
        self.stock_button.clicked.connect(self._restore_stock)

        layout.addWidget(self.restore_button)
        layout.addWidget(self.stock_button)
        layout.addStretch(1)
        return row

    def _reload(self) -> None:
        self.journal = Journal.load()
        entries = self.journal.restorable()

        self.table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            self.table.setItem(
                row, 0, QTableWidgetItem(entry.when.strftime("%Y-%m-%d %H:%M:%S"))
            )

            name_item = QTableWidgetItem(entry.target_path.name)
            name_item.setToolTip(entry.target)
            name_item.setData(Qt.UserRole, entry.id)
            self.table.setItem(row, 1, name_item)

            self.table.setItem(row, 2, QTableWidgetItem(entry.reason))

            backup = entry.backup_path
            size = backup.stat().st_size if backup and backup.is_file() else 0
            size_item = QTableWidgetItem(human_size(size))
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 3, size_item)

            self.table.setItem(
                row,
                4,
                QTableWidgetItem("baseline" if entry.is_baseline else "change"),
            )

        has_any = bool(entries)
        self.restore_button.setEnabled(has_any)
        self.stock_button.setEnabled(has_any)

        if has_any:
            self.status.set_text(
                f"{len(entries)} restorable backups. "
                "Restoring only affects files this app changed."
            )
        else:
            self.status.set_text(
                "No backups yet. One is taken automatically before any change."
            )

    def _selected_entry(self):
        rows = {i.row() for i in self.table.selectedIndexes()}
        if not rows:
            return None
        item = self.table.item(next(iter(rows)), 1)
        if item is None:
            return None
        entry_id = item.data(Qt.UserRole)
        return next((e for e in self.journal.entries if e.id == entry_id), None)

    def _restore_selected(self) -> None:
        entry = self._selected_entry()
        if entry is None:
            QMessageBox.information(
                self, "Nothing selected", "Select a backup to restore."
            )
            return

        answer = QMessageBox.question(
            self,
            "Restore this file?",
            f"{entry.target}\n\nwill be replaced with the copy taken at "
            f"{entry.when:%Y-%m-%d %H:%M:%S}.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        try:
            restore(entry, self.journal)
        except (OSError, FileNotFoundError) as exc:
            QMessageBox.warning(self, "Could not restore", str(exc))
            return

        self.status.set_text(f"Restored {entry.target_path.name}")
        self._reload()

    def _restore_stock(self) -> None:
        targets = self.journal.targets()
        if not targets:
            return

        listing = "\n".join(f"  {t}" for t in targets[:10])
        if len(targets) > 10:
            listing += f"\n  ... and {len(targets) - 10} more"

        answer = QMessageBox.question(
            self,
            "Restore everything to stock?",
            f"These files will go back to how they were before this app "
            f"first touched them:\n\n{listing}\n\n"
            f"Files this app never changed are not affected.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        restored = restore_to_stock(self.journal)
        self.status.set_text(f"Restored {len(restored)} files to stock.")
        self._reload()
