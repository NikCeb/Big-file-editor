# Generals Companion

Desktop tool that makes Command & Conquer: Generals and Zero Hour behave on modern hardware, plus a BIG archive editor.

Windows-only. Python 3.11+ / PySide6.

## What it does

- **Display** — set resolutions the in-game menu never offers (verified working: 2560x1440)
- **Performance** — CPU affinity launcher, Windows compatibility and DPI flags
- **Profiles** — named config sets, switchable
- **Backups** — every write backed up, journalled, restorable
- **Diagnostics** — install health, read-only save browser, crash log reader
- **Archive** — open, extract, and rebuild `.big` files

## What it does not do

- Never patches an executable
- Never writes save files (read-only, by design)
- Nothing affecting multiplayer fairness

## Status

In development. See `specs/` in the ai_companion repo for the spec and plan.
