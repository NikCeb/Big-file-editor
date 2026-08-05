"""Welcome screen: what was detected on this machine."""

from __future__ import annotations

from PySide6.QtWidgets import QGridLayout, QLabel

from ...domain.detect import GameInstall
from ..tokens import Space
from ..widgets import Banner, Card, Screen, label, section


class WelcomeScreen(Screen):
    def __init__(self, installs: list[GameInstall]) -> None:
        super().__init__(
            "Generals Companion",
            "Quality-of-life tooling for Command & Conquer: Generals and Zero Hour.",
        )

        if not installs:
            self.add(
                Banner(
                    "No Generals or Zero Hour installation found. You can still "
                    "open .big archives manually from the Archive screen.",
                    "warn",
                )
            )
            self.add_stretch()
            return

        for install in installs:
            self.add(self._install_card(install))

        self.add(
            Banner(
                "Nothing is changed until you press Apply on a screen. Every "
                "write is backed up first.",
                "info",
            )
        )
        self.add_stretch()

    def _install_card(self, install: GameInstall) -> Card:
        card = Card()
        card.add(section(install.label))

        grid = QGridLayout()
        grid.setColumnStretch(1, 1)
        grid.setHorizontalSpacing(Space.lg)
        grid.setVerticalSpacing(Space.sm)

        rows: list[tuple[str, str]] = []
        rows.append(
            ("Install", str(install.install_path) if install.install_path else "not found")
        )
        rows.append(
            (
                "Config",
                str(install.user_data_path) if install.user_data_path else "not found",
            )
        )

        if install.save_dir:
            count = len(list(install.save_dir.glob("*.sav")))
            rows.append(("Saves", f"{count} in {install.save_dir.name}\\"))

        if install.big_files:
            rows.append(("Archives", f"{len(install.big_files)} .big files"))

        for row, (name, value) in enumerate(rows):
            key = label(name, "subtitle")
            val = label(value, "mono")
            val.setTextInteractionFlags(
                val.textInteractionFlags() | _selectable()
            )
            grid.addWidget(key, row, 0)
            grid.addWidget(val, row, 1)

        card.body.addLayout(grid)
        return card


def _selectable():
    from PySide6.QtCore import Qt

    return Qt.TextSelectableByMouse
