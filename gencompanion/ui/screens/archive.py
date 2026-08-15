"""Archive screen: open a .big, browse entries, extract."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from ...formats.big import ArchiveError, BigArchive, open_archive
from ..tokens import Space
from ..widgets import Banner, EmptyState, Screen, human_size

_COLUMNS = ("Name", "Size", "Offset", "Type")


class ArchiveScreen(Screen):
    def __init__(self) -> None:
        super().__init__(
            "Archive",
            "Open a .big archive to browse and extract its contents.",
        )
        self.archive: BigArchive | None = None

        self.add(self._toolbar())

        self.status = Banner("", "info")
        self.status.hide()
        self.add(self.status)

        # Swap between the empty state and the table rather than showing an
        # empty grid, which reads as a fault.
        self.content = QStackedWidget()
        self.content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        self.empty = EmptyState(
            "No archive open",
            "Open a .big file from your Generals folder to list its contents. "
            "Archives are read lazily, so even multi-gigabyte files open "
            "instantly.",
        )
        self.table = self._make_table()

        self.content.addWidget(self.empty)
        self.content.addWidget(self.table)
        self.add(self.content)

    def _toolbar(self) -> QWidget:
        bar = QWidget()
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Space.md)

        open_button = QPushButton("Open archive")
        open_button.setProperty("variant", "primary")
        open_button.clicked.connect(self.open_dialog)

        self.filter_box = QLineEdit()
        self.filter_box.setPlaceholderText("Filter by name or extension")
        self.filter_box.textChanged.connect(self._apply_filter)
        self.filter_box.setClearButtonEnabled(True)
        self.filter_box.setEnabled(False)

        self.extract_button = QPushButton("Extract selected")
        self.extract_button.clicked.connect(self._extract_selected)
        self.extract_button.setEnabled(False)

        layout.addWidget(open_button)
        layout.addWidget(self.filter_box, 1)
        layout.addWidget(self.extract_button)
        return bar

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
        table.setMinimumHeight(360)

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        for col in range(1, len(_COLUMNS)):
            header.setSectionResizeMode(col, QHeaderView.ResizeToContents)
        return table

    # -- actions -------------------------------------------------------

    def open_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open BIG archive", "", "BIG archives (*.big);;All files (*)"
        )
        if path:
            self.load(Path(path))

    def load(self, path: Path) -> None:
        try:
            archive = open_archive(path)
        except ArchiveError as exc:
            self._fail(f"{path.name} - {exc}")
            return
        except OSError as exc:
            self._fail(f"{path.name} - could not read: {exc}")
            return

        self.archive = archive
        self._populate()
        self.content.setCurrentWidget(self.table)

        message = (
            f"{path.name}   {len(archive):,} entries, "
            f"{human_size(archive.total_data_size())}"
        )
        kind = "info"
        if archive.warnings:
            message += f"   -   {len(archive.warnings)} warning(s): "
            message += "; ".join(archive.warnings[:2])
            kind = "warn"
        if archive.read_only:
            message += "   -   read-only, this archive is damaged"
            kind = "warn"

        self.status.set_kind(kind)
        self.status.set_text(message)
        self.status.show()
        self.extract_button.setEnabled(True)
        self.filter_box.setEnabled(True)

    def _fail(self, message: str) -> None:
        self.status.set_kind("error")
        self.status.set_text(message)
        self.status.show()
        self.content.setCurrentWidget(self.empty)
        self.extract_button.setEnabled(False)
        self.filter_box.setEnabled(False)

    def _populate(self) -> None:
        if self.archive is None:
            return

        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(self.archive.entries))

        for row, entry in enumerate(self.archive.entries):
            name = QTableWidgetItem(entry.name)
            name.setData(Qt.UserRole, row)

            size = QTableWidgetItem()
            size.setData(Qt.DisplayRole, entry.size)
            size.setText(human_size(entry.size))
            size.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            offset = QTableWidgetItem()
            offset.setData(Qt.DisplayRole, entry.offset)
            offset.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            kind = QTableWidgetItem(entry.extension or "-")

            self.table.setItem(row, 0, name)
            self.table.setItem(row, 1, size)
            self.table.setItem(row, 2, offset)
            self.table.setItem(row, 3, kind)

        self.table.setSortingEnabled(True)

    def _apply_filter(self, text: str) -> None:
        needle = text.strip().casefold()
        shown = 0
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            visible = not needle or (
                item is not None and needle in item.text().casefold()
            )
            self.table.setRowHidden(row, not visible)
            shown += int(visible)

        if needle and self.archive is not None:
            self.status.set_text(
                f"{shown:,} of {len(self.archive):,} entries match "
                f"'{text.strip()}'"
            )

    def _extract_selected(self) -> None:
        if self.archive is None:
            return

        rows = {index.row() for index in self.table.selectedIndexes()}
        if not rows:
            QMessageBox.information(
                self, "Nothing selected", "Select one or more entries first."
            )
            return

        dest = QFileDialog.getExistingDirectory(self, "Extract to folder")
        if not dest:
            return

        dest_path = Path(dest)
        written = 0
        failed: list[str] = []

        for row in sorted(rows):
            item = self.table.item(row, 0)
            if item is None:
                continue
            entry = self.archive.find(item.text())
            if entry is None:
                continue

            target = dest_path / entry.name.replace("\\", "/")
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                with open(target, "wb") as out:
                    entry.copy_to(out)
                written += 1
            except OSError as exc:
                failed.append(f"{entry.name}: {exc}")

        if failed:
            QMessageBox.warning(
                self,
                "Some entries failed",
                f"Extracted {written}.\n\nFailed:\n" + "\n".join(failed[:10]),
            )
        else:
            self.status.set_kind("info")
            self.status.set_text(f"Extracted {written} entries to {dest_path}")
