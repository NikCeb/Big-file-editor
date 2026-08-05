"""Design tokens. The only place colour, spacing, radius, and type live.

Spec rule 6: no hardcoded hex anywhere else in the UI.

Palette is a warm desaturated slate with a amber accent, chosen to sit next to
the game's own khaki/olive HUD without imitating it.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Palette:
    # Surfaces, darkest to lightest.
    bg: str
    surface: str
    surface_raised: str
    border: str
    border_strong: str

    # Text.
    text: str
    text_dim: str
    text_faint: str

    # Accent and status.
    accent: str
    accent_hover: str
    accent_text: str
    ok: str
    warn: str
    danger: str
    danger_hover: str

    # Row striping in tables.
    row_alt: str
    selection: str


DARK = Palette(
    bg="#16181d",
    surface="#1c1f26",
    surface_raised="#232730",
    border="#2e333d",
    border_strong="#3d434f",
    text="#e8eaed",
    text_dim="#a2a9b6",
    text_faint="#6f7784",
    accent="#d99b3f",
    accent_hover="#e8ab4f",
    accent_text="#16181d",
    ok="#5fa771",
    warn="#d9a441",
    danger="#c3574f",
    danger_hover="#d4675f",
    row_alt="#1a1d24",
    selection="#31374a",
)

LIGHT = Palette(
    bg="#f4f5f7",
    surface="#ffffff",
    surface_raised="#fafbfc",
    border="#dde0e5",
    border_strong="#c3c8d0",
    text="#1c1f26",
    text_dim="#5a626f",
    text_faint="#8b939f",
    accent="#b87a1e",
    accent_hover="#a66d16",
    accent_text="#ffffff",
    ok="#3d7f52",
    warn="#96700f",
    danger="#a83f38",
    danger_hover="#93342e",
    row_alt="#f7f8f9",
    selection="#dfe5f2",
)


class Space:
    """4px base scale."""

    xs = 4
    sm = 8
    md = 12
    lg = 16
    xl = 24
    xxl = 32


class Radius:
    sm = 3
    md = 5
    lg = 8


class Type:
    family = "Segoe UI, system-ui, sans-serif"
    mono = "Cascadia Mono, Consolas, monospace"

    tiny = 11
    small = 12
    body = 13
    large = 15
    title = 19
    display = 25


def stylesheet(p: Palette) -> str:
    """Qt stylesheet built from a palette. No literals outside this module."""
    return f"""
QWidget {{
    background: {p.bg};
    color: {p.text};
    font-family: {Type.family};
    font-size: {Type.body}px;
}}

QLabel[role="title"] {{
    font-size: {Type.title}px;
    font-weight: 600;
    color: {p.text};
}}
QLabel[role="subtitle"] {{
    font-size: {Type.body}px;
    color: {p.text_dim};
}}
QLabel[role="section"] {{
    font-size: {Type.small}px;
    font-weight: 600;
    color: {p.text_faint};
    text-transform: uppercase;
    letter-spacing: 1px;
}}
QLabel[role="mono"] {{
    font-family: {Type.mono};
    color: {p.text_dim};
}}

/* Left navigation rail */
QListWidget#rail {{
    background: {p.surface};
    border: none;
    border-right: 1px solid {p.border};
    outline: none;
    padding-top: {Space.sm}px;
}}
QListWidget#rail::item {{
    padding: {Space.md}px {Space.lg}px;
    margin: 1px {Space.sm}px;
    border-radius: {Radius.md}px;
    color: {p.text_dim};
}}
QListWidget#rail::item:hover {{
    background: {p.surface_raised};
    color: {p.text};
}}
QListWidget#rail::item:selected {{
    background: {p.selection};
    color: {p.text};
    font-weight: 600;
}}

QPushButton {{
    background: {p.surface_raised};
    border: 1px solid {p.border_strong};
    border-radius: {Radius.md}px;
    padding: {Space.sm}px {Space.lg}px;
    color: {p.text};
}}
QPushButton:hover {{ background: {p.selection}; }}
QPushButton:disabled {{ color: {p.text_faint}; border-color: {p.border}; }}

QPushButton[variant="primary"] {{
    background: {p.accent};
    border: 1px solid {p.accent};
    color: {p.accent_text};
    font-weight: 600;
}}
QPushButton[variant="primary"]:hover {{
    background: {p.accent_hover};
    border-color: {p.accent_hover};
}}
QPushButton[variant="danger"] {{
    background: {p.danger};
    border: 1px solid {p.danger};
    color: #ffffff;
}}
QPushButton[variant="danger"]:hover {{ background: {p.danger_hover}; }}

QLineEdit, QComboBox, QSpinBox {{
    background: {p.surface};
    border: 1px solid {p.border_strong};
    border-radius: {Radius.md}px;
    padding: {Space.sm}px {Space.md}px;
    selection-background-color: {p.accent};
    selection-color: {p.accent_text};
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
    border-color: {p.accent};
}}
QComboBox::drop-down {{ border: none; width: {Space.xl}px; }}
QComboBox QAbstractItemView {{
    background: {p.surface_raised};
    border: 1px solid {p.border_strong};
    selection-background-color: {p.selection};
    outline: none;
}}

QTableWidget, QTreeWidget {{
    background: {p.surface};
    alternate-background-color: {p.row_alt};
    border: 1px solid {p.border};
    border-radius: {Radius.md}px;
    gridline-color: {p.border};
    outline: none;
}}
QTableWidget::item, QTreeWidget::item {{
    padding: {Space.xs}px {Space.sm}px;
    border: none;
}}
QTableWidget::item:selected, QTreeWidget::item:selected {{
    background: {p.selection};
    color: {p.text};
}}
QHeaderView::section {{
    background: {p.surface_raised};
    color: {p.text_dim};
    padding: {Space.sm}px;
    border: none;
    border-bottom: 1px solid {p.border_strong};
    border-right: 1px solid {p.border};
    font-weight: 600;
    font-size: {Type.small}px;
}}

QFrame[role="card"] {{
    background: {p.surface};
    border: 1px solid {p.border};
    border-radius: {Radius.lg}px;
}}

QFrame[role="banner-info"],
QFrame[role="banner-warn"],
QFrame[role="banner-error"] {{
    border-radius: {Radius.md}px;
    padding: {Space.md}px;
}}
QFrame[role="banner-info"]  {{ background: {p.surface_raised}; border: 1px solid {p.border_strong}; }}
QFrame[role="banner-warn"]  {{ background: {p.surface_raised}; border: 1px solid {p.warn}; }}
QFrame[role="banner-error"] {{ background: {p.surface_raised}; border: 1px solid {p.danger}; }}

QTextEdit, QPlainTextEdit {{
    background: {p.surface};
    border: 1px solid {p.border};
    border-radius: {Radius.md}px;
    font-family: {Type.mono};
    font-size: {Type.small}px;
    selection-background-color: {p.accent};
    selection-color: {p.accent_text};
}}

QProgressBar {{
    background: {p.surface};
    border: 1px solid {p.border};
    border-radius: {Radius.sm}px;
    height: {Space.sm}px;
    text-align: center;
}}
QProgressBar::chunk {{
    background: {p.accent};
    border-radius: {Radius.sm}px;
}}

QScrollBar:vertical {{
    background: transparent; width: 11px; margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {p.border_strong};
    border-radius: 5px;
    min-height: {Space.xl}px;
}}
QScrollBar::handle:vertical:hover {{ background: {p.text_faint}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar:horizontal {{
    background: transparent; height: 11px; margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: {p.border_strong};
    border-radius: 5px;
    min-width: {Space.xl}px;
}}

QCheckBox {{
    spacing: {Space.sm}px;
    padding: 2px 0;
}}
QCheckBox::indicator {{
    width: 15px;
    height: 15px;
    border: 1px solid {p.border_strong};
    border-radius: {Radius.sm}px;
    background: {p.surface};
}}
QCheckBox::indicator:hover {{ border-color: {p.accent}; }}
QCheckBox::indicator:checked {{
    background: {p.accent};
    border-color: {p.accent};
    /* Inline SVG tick so no asset file is needed. */
    image: url("data:image/svg+xml;utf8,\
<svg xmlns='http://www.w3.org/2000/svg' width='11' height='11' viewBox='0 0 11 11'>\
<path d='M2 5.6 L4.3 8 L9 3' fill='none' stroke='{p.accent_text}' \
stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/></svg>");
}}

QSplitter::handle {{ background: {p.border}; }}
QToolTip {{
    background: {p.surface_raised};
    color: {p.text};
    border: 1px solid {p.border_strong};
    padding: {Space.xs}px {Space.sm}px;
}}
"""
