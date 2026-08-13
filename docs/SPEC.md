# Spec: Generals Companion

Status: **implemented**. This document records the decisions the build was made
from. Where the build diverged from the original plan, the divergence is noted
below rather than edited out, because the reasoning is the useful part.

Stack: Python 3.13 / PySide6 (Qt 6), Windows-only, `psutil` permitted
Targets: Zero Hour 1.04 verified, Generals 1.08 supported. GenTool and the
Generals Online re-release remain untested.

## What changed during the build

| # | Decision | Outcome |
|---|---|---|
| D2 | Verify GenTool and Generals Online before planning | **Partially done.** Neither is installed on the dev machine, so both stay untested. Zero Hour 1.04 was verified directly. |
| D16 | Framerate control | **Dropped, then reinstated with a warning.** `Skirmish.ini` holds `FPS = 30`, but that is the simulation tick, not a render cap. Research found `-nofpslimit`, which does lift the cap but also doubles game speed because the engine ties simulation to framerate. It ships opt-in behind an explicit warning rather than as a quality-of-life default. |
| D7 | Degraded `SaveInfo` acceptable | **Not needed.** Map, faction and mission all proved cheap to extract. Two cases the spec did not anticipate were added: Generals Challenge saves carry no faction token, and saves under ~100 KB are progress markers rather than full game states. |
| — | Aspect-ratio correction | **Cut.** No corresponding key exists in `Options.ini`, so it is not INI-addressable. |
| — | Launch options screen | **Added.** Not in the original spec. Command-line switches turned out to be the safest way to change resolution and skip intros, since they write nothing to disk. |

Everything else in this document was built as written. See `FINDINGS.md` for the
evidence behind these calls.

---

## Summary

A desktop tool that makes Command & Conquer: Generals and Zero Hour behave correctly on modern hardware, plus a BIG archive editor for modding. The game was built in 2003 against assumptions that no longer hold — 4:3 monitors, single-core CPUs, a 30 FPS ceiling, no DPI scaling. This tool fixes those assumptions by editing config files the game already reads.

It never patches an executable. It never edits save data. It changes nothing that affects another player. Every change it makes is backed up and reversible.

## Users

One user type: a player or modder on Windows who owns the game. No accounts, no server, no permissions model. Runs locally against files on disk.

What they do:
- Make the game run at their monitor's resolution and refresh rate
- Stop the stutter and audio desync caused by high-core-count CPUs
- Keep config profiles and roll back a change that made things worse
- Diagnose a save that will not load, or a crash they do not understand
- Open a `.big`, look inside, pull files out, put files back in

## Design boundary

The rule that decides what belongs in this tool:

> **Fix the machine's assumptions, not the game's rules.**

| Belongs | Does not belong |
|---|---|
| Resolution, framerate, aspect ratio | Unit stats, costs, build times |
| CPU affinity, DPI flags, compatibility | Money, power, tech level |
| Config backup, profiles, diagnostics | Anything editing save state |
| Reading a save to explain why it broke | Writing a save |

Save files are **read-only, always**. The tool parses them to diagnose problems and to tell you which mission a save belongs to. There is no write path, no field editor, and no plan to add one. Editing save values is a trainer, and this is not that.

Any setting that would affect another player in multiplayer is out of scope. Where a setting is single-player only, the tool says so.

## Scope

### In

**Hardware fixes**
- Resolution injection, including modes the in-game menu never lists
- Framerate cap adjustment
- Aspect ratio correction for widescreen displays
- CPU affinity launcher for high-core-count processors
- Windows compatibility and DPI-awareness flags

**Config quality of life**
- Timestamped backup before every write, with one-click restore
- Named config profiles, switchable
- Install detection and health check
- Read-only save browser with mission, faction, timestamp, validity
- Crash log reader that explains the likely cause in plain English
- Restore-to-stock that undoes everything the tool ever did

**BIG archive editor**
- Read BIGF-format archives (also accept BIG4)
- Extract single entries, selections, or whole archives
- Add, replace, rename, delete entries; write a valid rebuilt archive
- Create a new empty archive
- Inline preview of text and INI entries, hex fallback for binary

### Out

- Any modification of `game.dat`, `generals.exe`, or any executable
- Binary patching of hardcoded engine limits
- Writing save files, or editing any value inside one
- Mod management — enabling, disabling, load order, merging
- HUD or UI repositioning for ultrawide
- Map (`.map`) editing
- Texture, model, or audio conversion
- Any change affecting multiplayer balance or fairness
- Networking of any kind
- Distribution of any copyrighted game asset

## User Stories

**Hardware fixes**
- As a player, I can set a resolution my monitor supports but the game does not list, so the game is not stretched or blurry.
- As a player, I can raise the 30 FPS cap, so the game feels responsive on a modern display.
- As a player, I can correct the aspect ratio so 16:9 widens my view instead of stretching it.
- As a player on a 16-core CPU, I can launch with limited affinity, so the game stops stuttering and the audio stays in sync.
- As a player on Windows 11, I can apply DPI and fullscreen flags, so the game is not scaled into a blurry mess.

**Config quality of life**
- As a player, I can revert any change the tool made, because it backed up the file first.
- As a player, I can keep a "4K single-player" profile and a "1080p competitive" profile and switch between them.
- As a player, I can check my install is intact and see exactly which files are missing or corrupt.
- As a player, I can browse my saves and see which one is which, and which one is broken, without loading the game.
- As a player, I can paste a crash log and get a plain-English likely cause.
- As a cautious player, I can press one button and put everything back to stock.

**BIG editor**
- As a modder, I can open a `.big` and see every entry with path, size, and offset.
- As a modder, I can filter a 10,000-entry archive by name or extension.
- As a modder, I can extract entries preserving internal directory structure.
- As a modder, I can drag files in from Explorer and add them at a chosen internal path.
- As a modder, I can replace an entry, save, and have the game still load the archive.

## Screens / UI

Single main window, left rail navigation. Dark theme default, light available.

| Screen | Shows | User can |
|---|---|---|
| **Welcome** | Detected installs, health summary, recent files, primary actions | Jump to a fix, open an archive, run health check |
| **Display** | Resolution list incl. injected modes, framerate cap, aspect ratio, current monitor caps | Change values, add a resolution, preview the effect, apply |
| **Performance** | Detected CPU topology, affinity recommendation, compatibility and DPI flags | Apply affinity, create launch shortcut, toggle flags |
| **Profiles** | Named config sets with a diff against current state | Save, load, rename, delete, compare |
| **Backups** | Timestamped backups with source file and size | Restore, open folder, delete, restore-to-stock |
| **Diagnostics** | Install health, file integrity, save browser, crash log reader | Run checks, browse saves read-only, paste a log, export a report |
| **Archive** | Split view: folder tree left, entry table right | Filter, sort, multi-select, extract, add, replace, rename, delete, preview |
| **Entry preview** | Text/INI viewer with syntax highlight, hex fallback | Read, copy, edit text entries in place |

UI rules:
1. Long operations run off the UI thread with a progress bar and a working cancel. The window never freezes.
2. Destructive actions confirm once, naming the exact file affected.
3. Errors appear as an inline banner with the file and the reason. No bare stack traces, no silent failures.
4. Every table value is selectable and copyable.
5. Keyboard first: Ctrl+O open, Ctrl+S save, Ctrl+F filter, Del delete, F2 rename.
6. Spacing, colour, radius come from a token module. No hardcoded hex in widget code.
7. Every setting shows its current value, its stock default, and whether it is single-player only.

## Data

### Game install

`GameInstall { path, version, edition, options_ini_path, save_dir, big_paths[] }`
`IniSetting { section, key, value, stock_default, type, allowed_range, multiplayer_safe }`

`stock_default` and `multiplayer_safe` are populated from a **shipped per-version reference table** (D1), not from the user's files. The table is a curated data asset keyed by detected version, versioned alongside the app.
`VersionProfile { version, ini_paths, settings: dict[key, IniSetting], verified: bool }`
`DisplayMode { width, height, refresh, aspect, injected: bool }`
`CpuTopology { physical_cores, logical_cores, recommended_mask }`

### BIG archive

| Field | Type | Notes |
|---|---|---|
| `magic` | 4 bytes | `BIGF`, also accept `BIG4` |
| `archive_size` | uint32 LE | Total file size |
| `entry_count` | uint32 **BE** | Big-endian — the classic parsing trap |
| `index_size` | uint32 BE | Header + index block size |
| `entries[]` | list | Repeated index records |

Per entry:

| Field | Type | Notes |
|---|---|---|
| `offset` | uint32 BE | Absolute offset of entry data |
| `size` | uint32 BE | Entry length |
| `name` | cstring | Null-terminated, backslash separators |

`BigArchive { path, format, entries[], dirty }`
`BigEntry { name, offset, size, source }` — `source` is a region of the original file or a pending disk file. Data is read lazily; a multi-GB archive is never loaded whole.

### Save file (read-only)

`SaveInfo { path, filename, timestamp, size, valid, problem, mission?, faction?, difficulty? }`

Parsed only far enough to identify and validate. No field model, no write path, no offsets recorded for mutation.
Per D7: `filename`, `timestamp`, `size`, `valid` are the required floor. `mission`, `faction`, `difficulty` are best-effort and may be absent.

### Profiles, backups, journal

`Profile { name, created, display: dict, affinity: dict, compat_flags: dict, source_install, requires_relaunch: bool }`
`Backup { id, path, source_target, timestamp, size, reason, tool_version, is_baseline: bool }`
`JournalEntry { id, target, target_type, timestamp, backup_id, tool_version, applied: bool }`

`target_type` is one of `file`, `registry`, `shortcut`. The journal (D6) is the sole authority for restore.
Retention (D11): entries where `is_baseline` is true are never evicted; others cap at 50, oldest first.

## API / Actions

Core library is pure Python, no Qt import, so it stays testable and scriptable.

| Action | Input | Output |
|---|---|---|
| `detect_installs()` | — | list of `GameInstall` from registry and common paths |
| `read_settings(install)` | install | list of `IniSetting` |
| `write_settings(install, settings)` | install, settings | written path, after backup |
| `enumerate_display_modes()` | — | monitor-supported modes |
| `inject_display_mode(install, mode)` | install, mode | updated INI |
| `recommend_affinity()` | — | `CpuTopology` with suggested mask |
| `create_launch_shortcut(install, mask)` | install, affinity mask | shortcut path |
| `apply_compat_flags(install, flags)` | install, flags | per-user registry write, reversible |
| `check_health(install)` | install | report of missing/corrupt/modified files |
| `list_saves(install)` | install | list of `SaveInfo`, read-only |
| `parse_crash_log(text)` | log text | likely cause, plain English |
| `save_profile(name, install)` / `load_profile(name, install)` | name, install | profile / applied settings |
| `backup(path, reason)` | path, reason | backup path |
| `restore(backup)` / `restore_to_stock(install)` | backup / install | restored paths |
| `open_archive(path)` | path | `BigArchive` or `ArchiveError` |
| `extract(archive, names, dest)` | archive, names, folder | count written |
| `add_entry` / `replace_entry` / `delete_entries` | archive, names, paths | updated archive |
| `write_archive(archive, dest)` | archive, path | written path; rebuilds header, index, every offset |

Write model: write to a temp file in the destination folder, verify it parses back, then atomically replace. A crash mid-write never leaves a corrupt file in place.

## Auth & Permissions

None. Local desktop tool, single user, no network calls. Compatibility flags write to per-user registry keys only, never machine-wide.

## Error States

| Condition | Behaviour |
|---|---|
| No game install detected | Ask for a manual folder pick |
| Install detected but files missing | Health report names each file; block writes to a broken install |
| Chosen resolution unsupported by monitor | Warn before applying, offer nearest supported |
| Framerate INI key differs on this version | Detect version first; if unknown, refuse and explain |
| Setting affects multiplayer | Flag it, require explicit confirmation |
| Game running during a write | Detect, name the process, refuse until closed |
| File is not a BIG archive | Named error, no partial state, offer hex view |
| Header claims more entries than the file holds | Load what fits, warn, mark archive read-only |
| Entry offset/size past end of file | Skip, list in warnings panel, keep rest usable |
| Entry name not valid UTF-8 | Decode latin-1, flag it, preserve original bytes on write |
| Archive would exceed 4 GB after edits | Block write, explain the uint32 offset limit |
| Save unreadable | Report as invalid in the browser. Never attempt repair. |
| Disk full during write | Temp file discarded, original untouched, error shown |

## Acceptance Criteria

**Hardware fixes** (automated)
- [ ] A resolution absent from the in-game menu appears there after injection
- [ ] Framerate change is written to the correct per-version INI key and reads back
- [ ] Affinity shortcut is created with the correct mask and launches the game
- [ ] Compatibility flags apply per-user and are fully reversible

**Manual QA checklist** (D15 — not machine-verifiable)
- [ ] Framerate change is visible in-game on a frame counter
- [ ] 16:9 correction widens the field of view rather than stretching the image
- [ ] Affinity shortcut measurably reduces stutter on a 12+ core CPU
- [ ] Crash log reader identifies a known crash class correctly

**Config quality of life**
- [ ] Every write produces a restorable backup and a journal entry
- [ ] Restore-to-stock returns every journalled target to its original state
- [ ] Restore-to-stock leaves un-journalled files untouched, including hand-edited ones
- [ ] A saved profile reapplies identically on a clean install
- [ ] Health check correctly identifies a deliberately corrupted archive
- [ ] Save browser lists saves with correct filename, timestamp and valid flag
- [ ] Save browser has no code path that opens a save for writing
- [ ] Backup retention evicts at 50 and never evicts the baseline
- [ ] A failed multi-target apply rolls back every completed write in that apply

**BIG editor**
- [ ] Stock Zero Hour archive lists correct entry count; names match a reference tool
- [ ] Extract-all is byte-identical to a reference extractor
- [ ] Open → write with no edits is byte-identical
- [ ] Archive with one replaced INI loads in-game and values take effect
- [ ] 2 GB+ archive opens in under 3 seconds, under 300 MB memory

**General**
- [ ] Core library has no Qt import; test suite passes headless
- [ ] All four target versions detected and opened without format error
- [ ] Killing the process mid-write leaves the original intact and valid

## Out of Scope (explicit)

- **Executable patching.** INI editing covers framerate and resolution, is reversible, and does not risk anti-cheat or the re-release's integrity checks.
- **Save writing.** Deliberate. Read-only inspection gives the diagnostic value with none of the cheat surface or corruption risk.
- **Mod management.** Removed by decision. The BIG editor stays; managing which mods load does not.
- **Ultrawide HUD rescaling.** Needs per-resolution asset work; its own spec if wanted.
- **Anything affecting multiplayer fairness.**

## Decisions (resolved in `/speckit.clarify`)

| # | Decision | Consequence |
|---|---|---|
| D1 | **Stock defaults and multiplayer-safety come from a shipped per-version table.** | A curated data file per version is a build artifact. Needs research up front and maintenance per patch. Makes restore-to-stock trustworthy regardless of the user's prior edits. |
| D2 | **Generals Online and GenTool are verified before planning.** | A spike task precedes `/speckit.plan`: probe the re-release's config paths and archive format, and determine GenTool's overlap behaviour. Scope for those two targets is set by what the spike finds. |
| D3 | **Explicit Apply per screen; one backup per apply.** | Controls stage changes locally. Apply takes one backup, then commits all writes for that screen as a unit. Backup history stays readable and every apply is a rollback point. |
| D4 | **Windows-only. `pywin32` and `psutil` permitted.** | Core library stays Qt-free but not OS-free. No Wine/Proton support commitment. Registry, shortcut, and affinity work use proper Win32 APIs. |

### D3 detail — multi-target apply

A single Apply may write across file, registry, and shortcut. These cannot be made atomic together. Required behaviour:

1. Back up every target that will be touched, before any write.
2. Write in order: files, then registry, then shortcuts.
3. On any failure, stop and roll back completed writes from the backups taken in step 1.
4. Report which targets were reverted and which failed.

## Decisions (round 2 — remaining 11 resolved)

| # | Decision | Consequence |
|---|---|---|
| D5 | **Version detection: hash the executable first, fall back to file-presence heuristics.** Unknown result blocks all writes. | Needs a known-hash table per version, shipped with D1's reference table. A wrong-version write is silently ineffective, so refusing on unknown is mandatory, not defensive. |
| D6 | **Restore-to-stock reverts only what the tool changed.** | Requires a durable change journal recording every write. Never destroys the user's own prior edits. "Stock" means "before this tool touched it". |
| D7 | **Degraded `SaveInfo` is acceptable.** Filename, timestamp, size and valid flag are the v1 floor; mission, faction and difficulty are best-effort. | Save browser ships even if deep parsing fails. The valid/invalid flag carries the diagnostic value. |
| D8 | **Profiles contain everything** — display, affinity, compat flags. | Settings needing a relaunch are marked in the model and the UI. Profile apply reuses the D3 multi-target write path. |
| D9 | **First-run is a short one-time screen**: detect installs, run health check, take the baseline backup. | The baseline backup is what makes D6 possible, so it must be visible and must not be skippable. |
| D10 | **"Preview the effect" is cut.** | Display screen shows current vs. pending values as numbers only. A fake preview is worse than none. |
| D11 | **Backup retention: baseline kept permanently, other backups capped at 50, oldest evicted.** | Retention runs after each apply. The first-run baseline is exempt and never evicted. |
| D12 | **Elevation: detect and warn up front, offer relaunch-as-admin.** | No elevation demanded at startup. Installs outside `Program Files` never see a prompt. Write path must check permission before staging. |
| D13 | **Reference tool is FinalBIG** for byte-identical extract and round-trip criteria. | Community standard. Comparison is manual or scripted against a local FinalBIG output; not a CI dependency. |
| D14 | **Two test tiers.** Synthetic fixtures for CI; an opt-in suite run locally against a real install. | CI ships no copyrighted asset. Fixture builders must generate valid BIG archives and save-shaped files from scratch. |
| D15 | **Three criteria downgraded to manual QA**: stutter reduction, FOV widening, crash-class identification. | Moved out of automated acceptance into a QA checklist. Frame-time measurement is out of scope. |

### D6 detail — change journal

Restore-to-stock is only as good as the record of what changed. Required:

- Every write appends a journal entry: target path or registry key, timestamp, backup reference, tool version.
- The journal is the authority for restore, not directory scanning.
- Restore replays the journal in reverse, restoring from the referenced backups.
- A target the tool never wrote is never touched by restore.
