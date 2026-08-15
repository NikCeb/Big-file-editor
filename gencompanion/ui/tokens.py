"""Design tokens. The only place colour, spacing, radius, and type live.

Spec rule 6: no hardcoded hex anywhere else in the UI.

Palette is a cool slate with an amber accent, chosen to sit next to the game's
own khaki/olive HUD without imitating it. Surfaces step in even luminance
increments so depth reads without borders doing all the work.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Palette:
    # Surfaces, darkest to lightest.
    bg: str
    surface: str
    surface_raised: str
    surface_inset: str
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
    accent_soft: str
    ok: str
    warn: str
    warn_soft: str
    danger: str
    danger_hover: str
    danger_soft: str

    row_alt: str
    selection: str


DARK = Palette(
    bg="#14161b",
    surface="#1b1e25",
    surface_raised="#22262f",
    surface_inset="#171a20",
    border="#2b303a",
    border_strong="#3a4150",
    text="#e9ebef",
    text_dim="#9aa3b2",
    text_faint="#697182",
    accent="#e0a244",
    accent_hover="#eeb257",
    accent_text="#14161b",
    accent_soft="#2a2419",
    ok="#5fa771",
    warn="#d9a441",
    warn_soft="#2a2419",
    danger="#c9584f",
    danger_hover="#d76a61",
    danger_soft="#2b1d1c",
    row_alt="#1e222a",
    selection="#2c3446",
)

LIGHT = Palette(
    bg="#f2f3f5",
    surface="#ffffff",
    surface_raised="#f7f8fa",
    surface_inset="#eef0f3",
    border="#dfe2e7",
    border_strong="#c2c8d2",
    text="#1a1d24",
    text_dim="#586074",
    text_faint="#878f9e",
    accent="#b3781c",
    accent_hover="#9d6816",
    accent_text="#ffffff",
    accent_soft="#faf3e6",
    ok="#3d7f52",
    warn="#8d6a0f",
    warn_soft="#fbf5e6",
    danger="#a63e37",
    danger_hover="#8f332d",
    danger_soft="#fbeeed",
    row_alt="#f8f9fa",
    selection="#dde5f3",
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
    sm = 4
    md = 6
    lg = 10


class Type:
    family = "Segoe UI Variable Text, Segoe UI, system-ui, sans-serif"
    mono = "Cascadia Mono, Consolas, monospace"

    tiny = 11
    small = 12
    body = 13
    large = 15
    title = 20
    display = 26


def stylesheet(p: Palette) -> str:
    """Qt stylesheet built from a palette. No literals outside this module."""
    return f"""
QWidget {{
    background: transparent;
    color: {p.text};
    font-family: {Type.family};
    font-size: {Type.body}px;
}}
QMainWindow, QScrollArea, QStackedWidget {{
    background: {p.bg};
}}

QLabel {{ background: transparent; }}
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
    font-size: {Type.tiny}px;
    font-weight: 700;
    color: {p.text_faint};
    letter-spacing: 1px;
}}
QLabel[role="mono"] {{
    font-family: {Type.mono};
    font-size: {Type.small}px;
    color: {p.text_dim};
}}
QLabel[role="empty-title"] {{
    font-size: {Type.large}px;
    font-weight: 600;
    color: {p.text_dim};
}}
QLabel[role="empty-body"] {{
    font-size: {Type.body}px;
    color: {p.text_faint};
}}
QLabel[role="metric"] {{
    font-size: {Type.display}px;
    font-weight: 600;
    color: {p.text};
}}

/* Left navigation rail */
QListWidget#rail {{
    background: {p.surface};
    border: none;
    border-right: 1px solid {p.border};
    outline: none;
    padding-top: {Space.md}px;
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
    min-height: 16px;
}}
QPushButton:hover {{ background: {p.selection}; border-color: {p.text_faint}; }}
QPushButton:pressed {{ background: {p.surface_inset}; }}
QPushButton:disabled {{
    color: {p.text_faint};
    border-color: {p.border};
    background: {p.surface_inset};
}}

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
QPushButton[variant="primary"]:disabled {{
    background: {p.surface_inset};
    border-color: {p.border};
    color: {p.text_faint};
}}
QPushButton[variant="danger"] {{
    background: transparent;
    border: 1px solid {p.danger};
    color: {p.danger};
}}
QPushButton[variant="danger"]:hover {{
    background: {p.danger};
    color: #ffffff;
}}
QPushButton[variant="danger"]:disabled {{
    background: {p.surface_inset};
    border-color: {p.border};
    color: {p.text_faint};
}}

QLineEdit, QComboBox, QSpinBox {{
    background: {p.surface_inset};
    border: 1px solid {p.border_strong};
    border-radius: {Radius.md}px;
    padding: {Space.sm}px {Space.md}px;
    color: {p.text};
    selection-background-color: {p.accent};
    selection-color: {p.accent_text};
    min-height: 16px;
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
    border-color: {p.accent};
    background: {p.surface};
}}
QLineEdit:hover, QComboBox:hover, QSpinBox:hover {{
    border-color: {p.text_faint};
}}
QComboBox::drop-down {{ border: none; width: {Space.xl}px; }}
QComboBox QAbstractItemView {{
    background: {p.surface_raised};
    border: 1px solid {p.border_strong};
    border-radius: {Radius.md}px;
    selection-background-color: {p.selection};
    padding: {Space.xs}px;
    outline: none;
}}

QTableWidget {{
    background: {p.surface};
    alternate-background-color: {p.row_alt};
    border: 1px solid {p.border};
    border-radius: {Radius.md}px;
    gridline-color: transparent;
    outline: none;
}}
QTableWidget::item {{
    padding: {Space.sm}px {Space.md}px;
    border: none;
    border-bottom: 1px solid {p.border};
}}
QTableWidget::item:selected {{
    background: {p.selection};
    color: {p.text};
}}
QHeaderView {{ background: transparent; }}
QHeaderView::section {{
    background: {p.surface_raised};
    color: {p.text_faint};
    padding: {Space.sm}px {Space.md}px;
    border: none;
    border-bottom: 1px solid {p.border_strong};
    font-weight: 600;
    font-size: {Type.tiny}px;
    letter-spacing: 0.5px;
}}
QTableCornerButton::section {{
    background: {p.surface_raised};
    border: none;
}}

QFrame[role="card"] {{
    background: {p.surface};
    border: 1px solid {p.border};
    border-radius: {Radius.lg}px;
}}
QFrame[role="empty"] {{
    background: {p.surface_inset};
    border: 1px dashed {p.border_strong};
    border-radius: {Radius.lg}px;
}}
QFrame[role="divider"] {{
    background: {p.border};
    border: none;
    max-height: 1px;
}}

QFrame[role="banner-info"],
QFrame[role="banner-warn"],
QFrame[role="banner-error"] {{
    border-radius: {Radius.md}px;
}}
QFrame[role="banner-info"] {{
    background: {p.surface_raised};
    border: 1px solid {p.border};
    border-left: 3px solid {p.border_strong};
}}
QFrame[role="banner-warn"] {{
    background: {p.warn_soft};
    border: 1px solid {p.warn};
    border-left: 3px solid {p.warn};
}}
QFrame[role="banner-error"] {{
    background: {p.danger_soft};
    border: 1px solid {p.danger};
    border-left: 3px solid {p.danger};
}}

QTextEdit, QPlainTextEdit {{
    background: {p.surface_inset};
    border: 1px solid {p.border};
    border-radius: {Radius.md}px;
    font-family: {Type.mono};
    font-size: {Type.small}px;
    selection-background-color: {p.accent};
    selection-color: {p.accent_text};
}}

QProgressBar {{
    background: {p.surface_inset};
    border: none;
    border-radius: {Radius.sm}px;
    height: 6px;
    text-align: center;
}}
QProgressBar::chunk {{
    background: {p.accent};
    border-radius: {Radius.sm}px;
}}

QScrollBar:vertical {{
    background: transparent; width: 10px; margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {p.border_strong};
    border-radius: 5px;
    min-height: {Space.xl}px;
}}
QScrollBar::handle:vertical:hover {{ background: {p.text_faint}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
QScrollBar:horizontal {{
    background: transparent; height: 10px; margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: {p.border_strong};
    border-radius: 5px;
    min-width: {Space.xl}px;
}}

QCheckBox {{
    spacing: {Space.sm}px;
    padding: 2px 0;
    background: transparent;
}}
QCheckBox::indicator {{
    width: 15px;
    height: 15px;
    border: 1px solid {p.border_strong};
    border-radius: {Radius.sm}px;
    background: {p.surface_inset};
}}
QCheckBox::indicator:hover {{ border-color: {p.accent}; }}
QCheckBox::indicator:checked {{
    background: {p.accent};
    border-color: {p.accent};
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
    border-radius: {Radius.sm}px;
    padding: {Space.xs}px {Space.sm}px;
}}
"""
