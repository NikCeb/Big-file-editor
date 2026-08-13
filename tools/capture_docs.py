"""Capture the documentation screenshots at 2x, then downscale to 1180px wide.

Run from the repo root:  python tools/capture_docs.py

Writes straight into docs/images/, so the docs and the app never drift apart.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ["QT_SCALE_FACTOR"] = "2"

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "images"
WIDTH = 1180

sys.path.insert(0, str(ROOT))

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from gencompanion.ui.main_window import MainWindow  # noqa: E402

# Rail index -> output filename.
SHOTS = {
    0: "overview.png",
    1: "display.png",
    3: "saves.png",
    4: "archive.png",
    5: "backups.png",
}


def save_scaled(window, target: Path) -> None:
    """Grab the window and scale to WIDTH so files stay a sane size."""
    pixmap = window.grab()
    scaled = pixmap.scaledToWidth(WIDTH, Qt.SmoothTransformation)
    scaled.save(str(target))


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1180, 800)
    window.show()
    for _ in range(6):
        app.processEvents()

    OUT.mkdir(parents=True, exist_ok=True)

    for row, filename in SHOTS.items():
        window.rail.setCurrentRow(row)
        for _ in range(4):
            app.processEvents()
        save_scaled(window, OUT / filename)
        print(f"  {filename}")

    # Launch options is captured with the FPS caution showing, because the
    # warning is the point of that screen.
    window.rail.setCurrentRow(2)
    for _ in range(3):
        app.processEvents()

    screen = window.stack.currentWidget()
    box = getattr(screen, "_checkboxes", {}).get("-nofpslimit")
    if box is not None:
        box.setChecked(True)
        for _ in range(4):
            app.processEvents()
    save_scaled(window, OUT / "launch-options.png")
    print("  launch-options.png")

    print(f"\nwrote {len(SHOTS) + 1} screenshots to {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
