"""Overview screen: what was detected, and how to correct it.

Auto-detection covers the common layouts, but Documents can be redirected,
installs can be portable, and saves can be copied from another machine. Every
detected path is therefore user-correctable, and a manual choice is persisted
and always wins over detection.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...domain.detect import GameInstall
from ...domain.settings import (
    Settings,
    looks_like_install,
    looks_like_user_data,
)
from ..tokens import Space
from ..widgets import Banner, Card, Screen, label, section

_EDITIONS: tuple[tuple[str, str], ...] = (
    ("zerohour", "Zero Hour"),
    ("generals", "Generals"),
)

_SEP = "  -  "


class WelcomeScreen(Screen):
    """Shows detection results with a picker for every path."""

    paths_changed = Signal()

    def __init__(self, installs: list[GameInstall], settings: Settings) -> None:
        super().__init__(
            "Generals Companion",
            "Quality-of-life tooling for Command & Conquer: Generals and Zero Hour.",
        )
        self.settings = settings
        self._by_edition = {i.edition: i for i in installs}

        if not installs:
            self.add(
                Banner(
                    "No Generals installation detected. Use the buttons below "
                    "to point the app at your game folder or your save folder.",
                    "warn",
                )
            )

        # Always render a card per edition, even when nothing was found, so
        # there is somewhere to click to fix it.
        for edition, edition_label in _EDITIONS:
            self.add(self._edition_card(edition, edition_label))

        self.add(
            Banner(
                "Nothing is changed until you press Apply on a screen. "
                "Every write is backed up first.",
                "info",
            )
        )
        self.add_stretch()

    # -- rendering -----------------------------------------------------

    def _edition_card(self, edition: str, edition_label: str) -> Card:
        install = self._by_edition.get(edition)
        card = Card()
        card.add(section(edition_label))

        card.body.addWidget(
            self._path_row(
                "Game folder",
                install.install_path if install else None,
                manual=bool(install and install.manual_install),
                detail=self._install_detail(install),
                on_pick=lambda: self._pick_install(edition),
                on_clear=lambda: self._clear_install(edition),
            )
        )

        card.body.addWidget(
            self._path_row(
                "Save and config folder",
                install.user_data_path if install else None,
                manual=bool(install and install.manual_user_data),
                detail=self._data_detail(install),
                on_pick=lambda: self._pick_user_data(edition),
                on_clear=lambda: self._clear_user_data(edition),
            )
        )

        return card

    def _path_row(
        self,
        name: str,
        path: Path | None,
        *,
        manual: bool,
        detail: str,
        on_pick,
        on_clear,
    ) -> QWidget:
        row = QWidget()
        layout = QVBoxLayout(row)
        layout.setContentsMargins(0, Space.sm, 0, Space.sm)
        layout.setSpacing(Space.xs)

        heading = QWidget()
        heading_layout = QHBoxLayout(heading)
        heading_layout.setContentsMargins(0, 0, 0, 0)
        heading_layout.setSpacing(Space.sm)

        caption = name + ("   (set by you)" if manual else "")
        caption_label = label(caption, "subtitle")
        # Without this the caption wraps mid-phrase when the row is narrow.
        caption_label.setWordWrap(False)
        heading_layout.addWidget(caption_label)
        heading_layout.addStretch(1)

        button = QPushButton("Change..." if path else "Locate...")
        if not path:
            button.setProperty("variant", "primary")
        button.clicked.connect(on_pick)
        heading_layout.addWidget(button)

        if manual:
            reset = QPushButton("Reset")
            reset.setToolTip("Forget this choice and go back to auto-detection")
            reset.clicked.connect(on_clear)
            heading_layout.addWidget(reset)

        layout.addWidget(heading)

        value = label(str(path) if path else "not found", "mono")
        value.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(value)

        if detail:
            layout.addWidget(label(detail, "subtitle"))

        return row

    def _install_detail(self, install: GameInstall | None) -> str:
        if install is None or install.install_path is None:
            return ""
        bits: list[str] = []
        if install.executable:
            bits.append(install.executable.name)
        else:
            bits.append("no executable found, launching is unavailable")
        if install.big_files:
            bits.append(f"{len(install.big_files)} .big archives")
        return _SEP.join(bits)

    def _data_detail(self, install: GameInstall | None) -> str:
        if install is None or install.user_data_path is None:
            return ""
        bits: list[str] = []
        if install.options_ini:
            bits.append("Options.ini")
        if install.save_dir:
            count = len(list(install.save_dir.glob("*.sav")))
            bits.append(f"{count} saves")
        return _SEP.join(bits) if bits else "folder found but empty"

    # -- picking -------------------------------------------------------

    def _pick_install(self, edition: str) -> None:
        current = self.settings.overrides.install_for(edition)
        chosen = QFileDialog.getExistingDirectory(
            self,
            "Select the game folder (contains generals.exe or .big files)",
            str(current) if current else "",
        )
        if not chosen:
            return

        path = Path(chosen)
        ok, reason = looks_like_install(path)
        if not ok and not self._confirm_anyway(path, reason):
            return

        self.settings.overrides.set_install(edition, path)
        self._persist()

    def _pick_user_data(self, edition: str) -> None:
        current = self.settings.overrides.user_data_for(edition)
        chosen = QFileDialog.getExistingDirectory(
            self,
            "Select the save and config folder (contains Options.ini or Save)",
            str(current) if current else "",
        )
        if not chosen:
            return

        path = Path(chosen)
        ok, reason = looks_like_user_data(path)
        if not ok and not self._confirm_anyway(path, reason):
            return

        self.settings.overrides.set_user_data(edition, path)
        self._persist()

    def _confirm_anyway(self, path: Path, reason: str) -> bool:
        """Warn on an unlikely folder, but let the user override us."""
        answer = QMessageBox.question(
            self,
            "That folder does not look right",
            f"{path}\n\n{reason}\n\nUse it anyway?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return answer == QMessageBox.Yes

    def _clear_install(self, edition: str) -> None:
        self.settings.overrides.set_install(edition, None)
        self._persist()

    def _clear_user_data(self, edition: str) -> None:
        self.settings.overrides.set_user_data(edition, None)
        self._persist()

    def _persist(self) -> None:
        try:
            self.settings.save()
        except OSError as exc:
            QMessageBox.warning(
                self,
                "Could not save settings",
                f"Your choice applies for this session but will not be "
                f"remembered.\n\n{exc}",
            )
        self.paths_changed.emit()
