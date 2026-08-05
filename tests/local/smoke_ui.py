"""Headless UI smoke test: build every screen, render once, screenshot.

Uses the offscreen Qt platform so it runs without a visible desktop session.

    python tests/local/smoke_ui.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from PySide6.QtWidgets import QApplication  # noqa: E402

from gencompanion.ui.main_window import MainWindow  # noqa: E402


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1180, 760)
    window.show()
    app.processEvents()

    out_dir = Path(__file__).parent / "screenshots"
    out_dir.mkdir(exist_ok=True)

    for row in range(window.rail.count()):
        window.rail.setCurrentRow(row)
        app.processEvents()

        name = window.rail.item(row).text()
        screen = window.stack.currentWidget()
        print(f"  screen {row}: {name:<16} -> {type(screen).__name__}")

        target = out_dir / f"{row}_{name.replace(' ', '_').lower()}.png"
        window.grab().save(str(target))

    print(f"\nScreenshots written to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
