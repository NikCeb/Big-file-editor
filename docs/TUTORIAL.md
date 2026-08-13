# How to use Generals Companion

A walkthrough of every screen, in the order you will actually need them.

Nothing in this tool changes a file until you press **Apply**. Everything it does
change is backed up first, and can be undone from the Backups screen.

**Contents**

1. [First run](#1-first-run)
2. [Fixing the resolution](#2-fixing-the-resolution)
3. [Faster launches](#3-faster-launches)
4. [About the FPS cap](#4-about-the-fps-cap)
5. [Browsing your saves](#5-browsing-your-saves)
6. [Opening a .big archive](#6-opening-a-big-archive)
7. [Undoing a change](#7-undoing-a-change)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. First run

Open `GeneralsCompanion.exe`. The Overview screen shows what it found.

![Overview screen](images/overview.png)

The tool looks for two things per edition:

- **Game folder** &mdash; where `generals.exe` and the `.big` archives live
- **Save and config folder** &mdash; usually under Documents, holding `Options.ini` and your saves

These are separate because they usually are on disk. You can have one without the
other, and the tool still works with whichever it finds.

### If a path says "not found"

Press **Locate...** and pick the folder. The tool checks the folder looks right and
tells you what it expected if it does not &mdash; but you can override that and use it
anyway.

Your choice is remembered, and beats auto-detection from then on. Press **Reset** to
go back to automatic.

> **Where are these folders?**
> Save and config is normally
> `Documents\Command and Conquer Generals Zero Hour Data`.
> If your Documents folder is redirected to OneDrive, the tool checks there too.

---

## 2. Fixing the resolution

This is the main event. The in-game options menu only offers a handful of old 4:3
resolutions, but the config file accepts anything your monitor supports.

![Display screen](images/display.png)

1. Open **Display**.
2. Pick a preset from the dropdown, or type a custom width and height.
3. Press **Apply changes**.
4. Launch the game. Your resolution is now active.

The status line confirms what was written and reminds you a backup was taken.

### The detail settings

Everything under **Detail** comes from the same file. Settings showing
**(game default)** are not in your config at all &mdash; the game is using its built-in
default, and the tool will only write a value if you deliberately change one.

Leave them alone unless you have a reason. They are there for when you are chasing
performance on old hardware.

---

## 3. Faster launches

Command-line switches. These change **nothing on disk** &mdash; they only apply to the
launch you start from here, so they are undone by launching the game normally.

![Launch options screen](images/launch-options.png)

The one worth using every time is **Skip intro movies and shell map**. It boots
straight to the menu instead of playing logos and an animated battle you have seen
a thousand times.

Tick what you want, then:

- **Copy command line** puts the full command on your clipboard. Paste it into a
  desktop shortcut's Target field to make it permanent.
- **Launch game** starts the game with those switches immediately.

The preview line at the bottom always shows exactly what will be passed.

### Setting resolution here instead

The **Resolution** dropdown on this screen passes `-xres` and `-yres` rather than
editing `Options.ini`. Use this if you want to try a resolution without committing
to it &mdash; launch without the switch and you are back to normal.

---

## 4. About the FPS cap

Generals runs at 30 FPS. There is a switch that removes that limit, and it is on
the Launch options screen &mdash; but it does not do what most people expect.

**The engine ties game speed to framerate.** Removing the cap does not give you a
smoother game at the same speed. It gives you a game running at roughly **double
speed**: units move faster, buildings finish sooner, animations run fast.

The tool shows a warning the moment you tick it, for exactly this reason.

If you want high FPS at correct game speed, use
[GenTool](https://www.gentool.net/). It caps frames independently of game logic,
which is the thing this tool deliberately does not attempt.

---

## 5. Browsing your saves

The Saves screen lists every save it can find, newest first.

![Saves screen](images/saves.png)

| Column | Meaning |
|---|---|
| **Kind** | `campaign`, `challenge`, or `progress` |
| **Description** | Faction and mission, or the Challenge general |
| **Map** | The map file the save refers to |
| **Size** | Full saves are megabytes; progress markers are a few hundred bytes |

**Progress** entries are small campaign-progress markers rather than full game
states &mdash; that is why some rows are 200 bytes and others are 6 MB. Both are
normal.

**This screen is read-only.** The tool never writes to a save file. It is here so
you can find the save you want and spot a corrupt one before the game chokes on it.

Use **Browse another folder...** to inspect saves copied from another machine.

---

## 6. Opening a .big archive

`.big` files are how Generals stores its assets. The Archive screen opens them.

![Archive screen](images/archive.png)

1. Press **Open archive** and pick a `.big` file from your game folder.
   `INI.big` is a good first one.
2. The entry list appears. Use the filter box to narrow by name or extension &mdash;
   typing `.ini` shows only INI files.
3. Select one or more rows and press **Extract selected**, then pick a destination.

Internal folder structure is preserved when extracting.

Large archives open instantly because entries are read on demand rather than loaded
up front. Extracting one small file from a two-gigabyte archive reads only that
file.

### If an archive is damaged

It still opens. Unreadable entries are skipped, a warning appears, and the archive
is marked read-only so the damage cannot be written back out.

---

## 7. Undoing a change

Every write is backed up first. The Backups screen is where you undo things.

- **Restore selected** &mdash; picks one backup and puts that file back to that point.
- **Restore everything to stock** &mdash; returns every file the tool has touched to how
  it was *before this tool ever ran*. Not the previous change; the original state.

Only files this tool changed are ever affected. If you hand-edited a config file
yourself, restore leaves it alone.

Backups are capped at 50, and the very first backup of each file is kept
permanently so restore-to-stock always has something to return to.

---

## 8. Troubleshooting

**The app says no installation found.**
Use **Locate...** on the Overview screen. You only need the save and config folder
for Display and Saves to work; the game folder is only needed to launch the game or
open its archives.

**My resolution change did nothing.**
Check the game is fully closed before applying, then relaunch. If the game is
running when you press Apply, it may overwrite `Options.ini` on exit.

**The game runs too fast.**
You have `-nofpslimit` enabled. Untick it &mdash; see
[section 4](#4-about-the-fps-cap).

**I want everything back to normal.**
Backups screen &rarr; **Restore everything to stock**.

**Where is my data stored?**
`%LOCALAPPDATA%\GeneralsCompanion\` holds settings, backups and the change journal.
Deleting that folder resets the tool but does not touch your game.

**Can I use this with GenTool?**
Untested. GenTool already handles some display work, so the two may overlap. If you
use GenTool, prefer its settings for display and use this tool for archives, saves
and backups.
