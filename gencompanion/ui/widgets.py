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
    # Labels must not paint their own background, or they show as a dark bar
    # against the card they sit on.
    widget.setAttribute(Qt.WA_TranslucentBackground, True)
    widget.setAutoFillBackground(False)
    return widget


def title(text: str) -> QLabel:
    return label(text, "title")


def subtitle(text: str) -> QLabel:
    return label(text, "subtitle")


def section(text: str) -> QLabel:
    return label(text.upper(), "section")


class Banner(QFrame):
    """Inline message. Spec rule 3: errors name the file and the reason."""

    def __init__(self, text: str, kind: str = "info") -> None:
        super().__init__()
        self._kind = kind
        self.setProperty("role", f"banner-{kind}")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(Space.lg, Space.md, Space.lg, Space.md)
        self._label = label(text)
        self._label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self._label)

    def set_text(self, text: str) -> None:
        self._label.setText(text)

    def set_kind(self, kind: str) -> None:
        """Change severity and force a restyle, which Qt does not do alone."""
        if kind == self._kind:
            return
        self._kind = kind
        self.setProperty("role", f"banner-{kind}")
        self.style().unpolish(self)
        self.style().polish(self)


class Card(QFrame):
    """A bordered panel with a vertical layout."""

    def __init__(self, spacing: int = Space.md) -> None:
        super().__init__()
        self.setProperty("role", "card")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(Space.xl, Space.lg, Space.xl, Space.lg)
        self.body.setSpacing(spacing)

    def add(self, widget: QWidget) -> QWidget:
        self.body.addWidget(widget)
        return widget


class EmptyState(QFrame):
    """Explains why a view is empty and what to do about it.

    A bare table with headers and no rows reads as a fault. This gives the
    space a purpose instead.
    """

    def __init__(self, heading: str, body: str = "") -> None:
        super().__init__()
        self.setProperty("role", "empty")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Space.xl, Space.xxl, Space.xl, Space.xxl)
        layout.setSpacing(Space.sm)
        layout.setAlignment(Qt.AlignCenter)
        # Cap the height so the panel stays proportional to its text rather
        # than stretching to fill the page, which reads as a layout fault.
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(200)

        heading_label = label(heading, "empty-title")
        heading_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(heading_label)

        if body:
            body_label = label(body, "empty-body")
            body_label.setAlignment(Qt.AlignCenter)
            body_label.setMaximumWidth(460)
            layout.addWidget(body_label, alignment=Qt.AlignCenter)


def divider() -> QFrame:
    line = QFrame()
    line.setProperty("role", "divider")
    line.setFixedHeight(1)
    return line


class Screen(QWidget):
    """Base for every screen: title, optional subtitle, scrollable content.

    Content scrolls vertically so a small window never clips a card, and never
    scrolls horizontally, which the spec forbids for the page body.
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
        self.root.setContentsMargins(Space.xxl, Space.xl, Space.xxl, Space.xxl)
        self.root.setSpacing(Space.lg)

        header = QVBoxLayout()
        header.setSpacing(Space.xs)
        header.addWidget(title(heading))
        if description:
            header.addWidget(subtitle(description))
        self.root.addLayout(header)

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
