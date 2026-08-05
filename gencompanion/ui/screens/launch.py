"""Launch options screen.

Builds a command line from verified switches. The -nofpslimit caution is
shown the moment it is ticked, because the engine ties simulation speed to
framerate and users reasonably expect "remove FPS cap" to mean "smoother".
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ...domain.detect import GameInstall
from ...domain.launch import SWITCHES, LaunchConfig, Severity
from ..tokens import Space
from ..widgets import Banner, Card, Screen, label, section

_COMMON_RESOLUTIONS: tuple[tuple[int, int], ...] = (
    (1280, 720),
    (1600, 900),
    (1920, 1080),
    (2560, 1440),
    (3440, 1440),
    (3840, 2160),
)


class LaunchScreen(Screen):
    def __init__(self, install: GameInstall | None) -> None:
        super().__init__(
            "Launch options",
            "Command-line switches applied when the game starts. "
            "These change nothing on disk.",
        )
        self.install = install
        self.config = LaunchConfig()
        self._checkboxes: dict[str, QCheckBox] = {}

        self.add(self._switch_card())
        self.add(self._resolution_card())

        self.warning_banner = Banner("", "warn")
        self.warning_banner.hide()
        self.add(self.warning_banner)

        self.preview = Banner("", "info")
        self.add(self.preview)

        self.add(self._actions())
        self.add_stretch()
        self._refresh()

    def _switch_card(self) -> Card:
        card = Card()
        card.add(section("Switches"))

        for index, switch in enumerate(SWITCHES):
            row = QWidget()
            layout = QVBoxLayout(row)
            top = Space.sm if index else 0
            layout.setContentsMargins(0, top, 0, Space.sm)
            layout.setSpacing(Space.xs)

            box = QCheckBox(switch.label)
            box.toggled.connect(
                lambda checked, flag=switch.flag: self._on_toggle(flag, checked)
            )
            self._checkboxes[switch.flag] = box
            layout.addWidget(box)

            # Indent descriptions to align under the checkbox label, not its box.
            indent = Space.xl + Space.xs

            desc = label(switch.description, "subtitle")
            desc.setContentsMargins(indent, 0, 0, 0)
            desc.setWordWrap(True)
            layout.addWidget(desc)

            if switch.severity is Severity.CAUTION:
                flag_note = label(f"{switch.flag} — see warning below", "mono")
                flag_note.setContentsMargins(indent, 0, 0, 0)
                layout.addWidget(flag_note)

            # Let the row grow to whatever its contents need; without this the
            # last row clips against the card edge.
            row.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
            row.adjustSize()
            card.body.addWidget(row)

        return card

    def _resolution_card(self) -> Card:
        card = Card()
        card.add(section("Resolution"))
        card.add(
            label(
                "Passed as -xres / -yres. Does not modify Options.ini, so it is "
                "easy to undo — just launch without the switch.",
                "subtitle",
            )
        )

        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Space.md)

        self.res_combo = QComboBox()
        self.res_combo.addItem("Use game setting", None)
        for width, height in _COMMON_RESOLUTIONS:
            self.res_combo.addItem(f"{width} x {height}", (width, height))
        self.res_combo.currentIndexChanged.connect(self._on_resolution)

        layout.addWidget(self.res_combo)
        layout.addStretch(1)
        card.body.addWidget(row)
        return card

    def _actions(self) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Space.md)

        self.copy_button = QPushButton("Copy command line")
        self.copy_button.clicked.connect(self._copy)

        self.launch_button = QPushButton("Launch game")
        self.launch_button.setProperty("variant", "primary")
        self.launch_button.clicked.connect(self._launch)
        self.launch_button.setEnabled(
            self.install is not None and self.install.is_playable
        )
        if self.install is None or not self.install.is_playable:
            self.launch_button.setToolTip(
                "No game executable found. Copy the command line instead."
            )

        layout.addWidget(self.copy_button)
        layout.addWidget(self.launch_button)
        layout.addStretch(1)
        return row

    # -- behaviour -----------------------------------------------------

    def _on_toggle(self, flag: str, checked: bool) -> None:
        self.config.toggle(flag, checked)
        self._refresh()

    def _on_resolution(self, index: int) -> None:
        value = self.res_combo.itemData(index)
        if value is None:
            self.config.set_resolution(None, None)
        else:
            self.config.set_resolution(*value)
        self._refresh()

    def _refresh(self) -> None:
        warnings = self.config.warnings()
        if warnings:
            self.warning_banner.set_text("\n\n".join(warnings))
            self.warning_banner.show()
        else:
            self.warning_banner.hide()

        self.preview.set_text(self.config.describe())

    def _copy(self) -> None:
        from PySide6.QtWidgets import QApplication

        if self.install and self.install.executable:
            text = self.config.command_line(self.install.executable)
        else:
            text = " ".join(self.config.arguments())
        QApplication.clipboard().setText(text)
        self.copy_button.setText("Copied")
        from PySide6.QtCore import QTimer

        QTimer.singleShot(
            1500, lambda: self.copy_button.setText("Copy command line")
        )

    def _launch(self) -> None:
        import subprocess

        from PySide6.QtWidgets import QMessageBox

        if not (self.install and self.install.executable):
            return

        try:
            subprocess.Popen(
                [str(self.install.executable), *self.config.arguments()],
                cwd=str(self.install.executable.parent),
            )
        except OSError as exc:
            QMessageBox.warning(
                self,
                "Could not launch",
                f"{self.install.executable}\n\n{exc}",
            )
