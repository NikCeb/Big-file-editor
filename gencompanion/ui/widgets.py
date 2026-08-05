"""Small shared widgets. Styling comes from tokens; no literals here."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .tokens import Space


def label(text: str, role: str = "") -> QLabel:
    widget = QLabel(text)
    if role:
        widget.setProperty("role", role)
    widget.setWordWrap(True)
    return widget


def title(text: str) -> QLabel:
    return label(text, "title")


def subtitle(text: str) -> QLabel:
    return label(text, "subtitle")


def section(text: str) -> QLabel:
    return label(text, "section")


class Banner(QFrame):
    """Inline message. Spec rule 3: errors name the file and the reason."""

    def __init__(self, text: str, kind: str = "info") -> None:
        super().__init__()
        self.setProperty("role", f"banner-{kind}")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(Space.md, Space.md, Space.md, Space.md)
        self._label = label(text)
        self._label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self._label)

    def set_text(self, text: str) -> None:
        self._label.setText(text)


class Card(QFrame):
    """A bordered panel with a vertical layout."""

    def __init__(self, spacing: int = Space.md) -> None:
        super().__init__()
        self.setProperty("role", "card")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(Space.lg, Space.lg, Space.lg, Space.lg)
        self.body.setSpacing(spacing)

    def add(self, widget: QWidget) -> QWidget:
        self.body.addWidget(widget)
        return widget


class Screen(QWidget):
    """Base for every screen: title, optional subtitle, scrollable content.

    Content scrolls vertically so a small window never clips a card, and never
    scrolls horizontally — the spec forbids the body scrolling sideways.
    """

    def __init__(self, heading: str, description: str = "") -> None:
        super().__init__()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        outer.addWidget(scroll)

        body = QWidget()
        scroll.setWidget(body)

        self.root = QVBoxLayout(body)
        self.root.setContentsMargins(Space.xxl, Space.xl, Space.xxl, Space.xl)
        self.root.setSpacing(Space.lg)

        self.root.addWidget(title(heading))
        if description:
            self.root.addWidget(subtitle(description))

    def add(self, widget: QWidget, stretch: int = 0) -> QWidget:
        self.root.addWidget(widget, stretch)
        return widget

    def add_stretch(self) -> None:
        self.root.addStretch(1)


def spacer() -> QWidget:
    widget = QWidget()
    widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    return widget


def human_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:,.0f} {unit}" if unit == "B" else f"{size:,.1f} {unit}"
        size /= 1024
    return f"{size:,.1f} GB"
