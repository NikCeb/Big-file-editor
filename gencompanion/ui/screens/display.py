"""Display screen: edit Options.ini resolution and quality settings.

Changes are staged locally and only written when Apply is pressed, so one
backup covers one deliberate action rather than one per keystroke.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QWidget,
)

from ...domain.detect import GameInstall
from ...domain.display import (
    apply_display_changes,
    common_resolutions,
    read_display_config,
)
from ..tokens import Space
from ..widgets import Banner, Card, Screen, label, section

_DEFAULT_CHOICE = "(game default)"


class DisplayScreen(Screen):
    def __init__(self, install: GameInstall | None) -> None:
        super().__init__(
            "Display",
            "Resolution and detail settings from Options.ini. "
            "The game accepts resolutions its menu never lists.",
        )
        self.install = install
        self._quality_boxes: dict[str, QComboBox] = {}
        self._config = None

        options_ini = install.options_ini if install else None
        if options_ini is None:
            self.add(
                Banner(
                    "No Options.ini found. Use Overview to locate your save "
                    "and config folder first.",
                    "warn",
                )
            )
            self.add_stretch()
            return

        try:
            self._config = read_display_config(options_ini)
        except OSError as exc:
            self.add(Banner(f"Could not read {options_ini}: {exc}", "error"))
            self.add_stretch()
            return

        self.add(self._resolution_card())
        self.add(self._quality_card())

        self.status = Banner(
            f"Reading {self._config.path}  ({self._config.raw_keys} keys)",
            "info",
        )
        self.add(self.status)
        self.add(self._actions())
        self.add_stretch()

    # -- cards ---------------------------------------------------------

    def _resolution_card(self) -> Card:
        card = Card()
        card.add(section("Resolution"))
        card.add(
            label(
                f"Currently {self._config.resolution_text}. "
                "Pick a preset or set a custom size.",
                "subtitle",
            )
        )

        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Space.md)

        self.preset = QComboBox()
        self.preset.addItem("Custom", None)
        for width, height in common_resolutions():
            self.preset.addItem(f"{width} x {height}", (width, height))
        self.preset.currentIndexChanged.connect(self._on_preset)

        self.width_box = QSpinBox()
        self.width_box.setRange(640, 7680)
        self.width_box.setSingleStep(10)

        self.height_box = QSpinBox()
        self.height_box.setRange(480, 4320)
        self.height_box.setSingleStep(10)

        self._syncing = False
        self.width_box.valueChanged.connect(self._on_size_typed)
        self.height_box.valueChanged.connect(self._on_size_typed)

        current = self._config.resolution or (1024, 768)
        self.width_box.setValue(current[0])
        self.height_box.setValue(current[1])

        # findData compares by identity for tuples, so match explicitly.
        for i in range(self.preset.count()):
            if self.preset.itemData(i) == current:
                self.preset.setCurrentIndex(i)
                break

        layout.addWidget(self.preset)
        layout.addWidget(label("width", "subtitle"))
        layout.addWidget(self.width_box)
        layout.addWidget(label("height", "subtitle"))
        layout.addWidget(self.height_box)
        layout.addStretch(1)

        card.body.addWidget(row)
        return card

    def _quality_card(self) -> Card:
        card = Card()
        card.add(section("Detail"))
        card.add(
            label(
                "Settings absent from Options.ini use the game default and "
                "are only written if you change them.",
                "subtitle",
            )
        )

        grid = QGridLayout()
        grid.setHorizontalSpacing(Space.lg)
        grid.setVerticalSpacing(Space.sm)
        grid.setColumnStretch(1, 1)

        for row, setting in enumerate(self._config.quality):
            grid.addWidget(label(setting.label, "subtitle"), row, 0)

            box = QComboBox()
            box.addItem(_DEFAULT_CHOICE, None)
            for choice in setting.choices:
                box.addItem(choice, choice)

            if setting.current is not None:
                index = box.findData(setting.current)
                if index < 0:
                    box.addItem(setting.current, setting.current)
                    index = box.count() - 1
                box.setCurrentIndex(index)

            self._quality_boxes[setting.key] = box
            grid.addWidget(box, row, 1)

        card.body.addLayout(grid)
        return card

    def _actions(self) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Space.md)

        apply_button = QPushButton("Apply changes")
        apply_button.setProperty("variant", "primary")
        apply_button.clicked.connect(self._apply)

        layout.addWidget(apply_button)
        layout.addStretch(1)
        return row

    # -- behaviour -----------------------------------------------------

    def _on_preset(self, index: int) -> None:
        value = self.preset.itemData(index)
        if value is None:
            return
        self._syncing = True
        self.width_box.setValue(value[0])
        self.height_box.setValue(value[1])
        self._syncing = False

    def _on_size_typed(self) -> None:
        # Typing a size that is not a preset should say so, rather than
        # leaving a stale preset name selected.
        if getattr(self, "_syncing", False):
            return
        current = (self.width_box.value(), self.height_box.value())
        for i in range(self.preset.count()):
            if self.preset.itemData(i) == current:
                self.preset.setCurrentIndex(i)
                return
        self.preset.setCurrentIndex(0)

    def _apply(self) -> None:
        if self._config is None:
            return

        resolution = (self.width_box.value(), self.height_box.value())
        quality: dict[str, str] = {}
        for setting in self._config.quality:
            chosen = self._quality_boxes[setting.key].currentData()
            if chosen is not None and chosen != setting.current:
                quality[setting.key] = chosen

        try:
            path, changed = apply_display_changes(
                self._config.path,
                resolution=resolution,
                quality=quality,
            )
        except OSError as exc:
            QMessageBox.warning(
                self, "Could not write settings", f"{self._config.path}\n\n{exc}"
            )
            return

        if not changed:
            self.status.set_text("No changes to apply.")
            return

        self.status.set_text(
            f"Wrote {', '.join(changed)} to {path.name}. "
            "A backup was taken first, see the Backups screen."
        )
        self._config = read_display_config(path)
