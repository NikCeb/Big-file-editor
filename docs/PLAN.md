# Plan: Generals Companion

Source spec: [SPEC.md](SPEC.md)
Status: **executed**. Layers 1-6 are built and shipping; the layer order below
is the order they were actually built in. Kept as a record of the reasoning,
not as a live task list.

## Shape of the project

No database, no server, no auth. The standard DB → API → UI layering does not apply. The real layering is:

```
platform/   Win32 adapters — registry, shortcuts, affinity, process detection
formats/    BIG and save parsers — pure stdlib, no OS calls
safety/     Backup, journal, restore, atomic + multi-target writes
domain/     Install detection, version identity, settings, profiles, health
data/       Shipped per-version reference tables (D1, D5)
ui/         PySide6 — no business logic
```

Hard rule: `ui/` imports `domain/`, never the reverse. `formats/` imports nothing from the project. `domain/` never imports Qt. This keeps the core headless-testable, which the spec requires.

## Layers

### Layer 0 — Verification spike (D2)

- **Changes:** No production code. Investigate and write findings.
- **Produces:** `specs/FINDINGS_COMPAT.md`
- **Questions to answer:**
  - Does Generals Online use `Options.ini`, at what path, with which keys?
  - Is its archive format still BIGF/BIG4?
  - Does it ship its own display options that make tier 1 redundant?
  - What does GenTool already override, and what happens when both are active?
  - Do framerate and aspect-ratio keys differ across 1.04 and 1.08?
- **Risk:** This gates the scope of two of four targets. If the re-release diverges hard, it drops from v1 and the spec's target line changes.
- **Blocks:** the reference tables, so it runs first.

### Layer 1 — `formats/` (pure, no OS)

- **Changes:** BIG reader and writer; save identifier.
- **Files:**
  - `formats/big/reader.py` — parse header + index, lazy entry access
  - `formats/big/writer.py` — rebuild header, index, all offsets
  - `formats/big/model.py` — `BigArchive`, `BigEntry`
  - `formats/big/errors.py`
  - `formats/save/identify.py` — read-only, returns `SaveInfo`
  - `formats/save/model.py` — `SaveInfo`
  - `formats/ini/parser.py` — order- and comment-preserving INI
- **Risk:**
  - **Endianness.** `entry_count`, `index_size`, per-entry `offset` and `size` are big-endian while `archive_size` is little-endian. Getting this wrong produces archives the game silently refuses. Round-trip test first.
  - **4 GB ceiling.** uint32 offsets. Writer must refuse before producing a corrupt archive.
  - **Comment-preserving INI.** `configparser` discards comments and ordering, which would mangle user files. Needs a custom parser.
  - **Save identification is best-effort by D7.** Must degrade cleanly, never guess.
- **Depends on:** nothing. Can start immediately, in parallel with Layer 0.

### Layer 2 — `platform/` (Win32 adapters)

- **Changes:** Every OS-specific operation, behind interfaces.
- **Files:**
  - `platform/registry.py` — per-user compat flags, read/write/delete
  - `platform/shortcuts.py` — affinity launcher creation
  - `platform/cpu.py` — topology via `psutil`, recommended mask
  - `platform/display.py` — monitor-supported modes
  - `platform/processes.py` — is the game running
  - `platform/elevation.py` — admin detection, relaunch (D12)
  - `platform/paths.py` — `%LOCALAPPDATA%`, install search roots
- **Risk:**
  - Registry writes stay under `HKCU`. Never machine-wide.
  - Elevation detection must be reliable — a false negative means a failed write mid-apply.
  - `pywin32` and `psutil` land here only (D4). Nothing else imports them.
- **Depends on:** nothing.

### Layer 3 — `safety/` (backup, journal, atomic writes)

- **Changes:** The mechanism every write goes through.
- **Files:**
  - `safety/backup.py` — timestamped backups, `is_baseline`
  - `safety/journal.py` — append-only record, restore authority (D6)
  - `safety/retention.py` — cap 50, baseline exempt (D11)
  - `safety/atomic.py` — temp write, verify parses back, atomic replace
  - `safety/transaction.py` — multi-target apply with rollback (D3)
  - `safety/restore.py` — reverse-replay journal
- **Risk:**
  - **Highest-risk layer in the project.** Everything destructive routes through it.
  - Multi-target rollback across file + registry + shortcut cannot be truly atomic. Spec-mandated order: back up all, write files → registry → shortcuts, roll back completed writes on failure.
  - Journal must survive a crash mid-write. Append-only, flushed before the write it describes.
  - Restore must never touch an un-journalled target. This is the guarantee protecting hand-edited files.
- **Depends on:** Layer 2 (registry/shortcut targets).

### Layer 4 — `data/` (shipped reference tables)

- **Changes:** Curated per-version data, not code.
- **Files:**
  - `data/versions/zh_104.json` — hashes, INI paths, settings, stock defaults, multiplayer-safe flags
  - `data/versions/generals_108.json`
  - `data/versions/gentool.json` *(shape from Layer 0)*
  - `data/versions/online.json` *(shape from Layer 0)*
  - `data/versions/schema.json` — validates the above
  - `data/crash_signatures.json` — known crash classes
- **Risk:**
  - Only as good as the research. Wrong `stock_default` breaks restore-to-stock; wrong `multiplayer_safe` misleads on fairness.
  - Needs maintenance per game patch.
  - Two files are shaped by Layer 0's findings.
- **Depends on:** Layer 0.

### Layer 5 — `domain/` (business logic, no Qt)

- **Changes:** Install detection, version identity, settings, profiles, health, diagnostics.
- **Files:**
  - `domain/detect.py` — find installs (registry, common paths, manual)
  - `domain/version.py` — hash first, file-presence fallback, block on unknown (D5)
  - `domain/settings.py` — read/stage/apply `IniSetting`, merge with reference table
  - `domain/display.py` — mode injection, aspect correction
  - `domain/performance.py` — affinity + compat flag application
  - `domain/profiles.py` — save/load/compare, `requires_relaunch` (D8)
  - `domain/health.py` — install integrity
  - `domain/saves.py` — read-only browser (D7)
  - `domain/crashlog.py` — signature match, plain-English cause
  - `domain/archive.py` — BIG operations orchestration
- **Risk:**
  - **Version detection is load-bearing.** Everything downstream is wrong if it is wrong. Refusing on unknown is required behaviour, not a nicety.
  - Settings staging must be explicit per D3 — no control writes on change.
  - `domain/saves.py` must have no write path at all. This is an acceptance criterion; enforce with a test asserting no write mode is ever opened.
- **Depends on:** Layers 1, 2, 3, 4.

### Layer 6 — `ui/` (PySide6)

- **Changes:** Eight screens, design tokens, threading.
- **Files:**
  - `ui/app.py`, `ui/main_window.py`, `ui/rail.py`
  - `ui/tokens.py` — colour, spacing, radius, type. No hardcoded hex anywhere else.
  - `ui/theme.py` — dark default, light available
  - `ui/screens/first_run.py` (D9), `welcome.py`, `display.py` (D10 — numbers, no preview), `performance.py`, `profiles.py`, `backups.py`, `diagnostics.py`, `archive.py`
  - `ui/widgets/` — entry table, folder tree, hex view, INI editor, banner, confirm dialog, progress
  - `ui/workers.py` — `QThread` wrappers with working cancel
- **Risk:**
  - Long operations must not block the UI thread — an explicit spec rule with a working cancel, not a decorative one.
  - Tokens must land before screens, or hardcoded values spread and retrofitting is painful.
  - Eight screens is the bulk of the work. Archive and Diagnostics are the two heavy ones.
- **Depends on:** Layer 5.

### Layer 7 — Tests and packaging

- **Changes:** Two-tier tests (D14), fixture builders, packaging.
- **Files:**
  - `tests/fixtures/build_big.py` — synthetic valid archives, no copyrighted assets
  - `tests/fixtures/build_save.py` — save-shaped files
  - `tests/unit/` — per layer, headless
  - `tests/integration/` — transaction rollback, restore, retention
  - `tests/local/` — opt-in, requires a real install, skipped by default
  - `docs/QA_CHECKLIST.md` — the four manual items (D15)
  - `pyproject.toml`, PyInstaller spec
- **Risk:**
  - Synthetic fixtures must be genuinely valid or they prove nothing.
  - FinalBIG comparison (D13) is manual, not CI.
  - PyInstaller + PySide6 + pywin32 packaging has known sharp edges.
- **Depends on:** everything, but unit tests are written alongside each layer, not after.

## Layer Order

```
0. Verification spike        ─┐
1. formats/    (parallel)    ─┤ no dependencies, start together
2. platform/   (parallel)    ─┘
3. safety/                    needs platform
4. data/                      needs spike findings
5. domain/                    needs 1,2,3,4
6. ui/tokens + shell          needs domain
7. ui/screens                 one at a time
8. packaging + QA
```

Build order within UI: tokens and shell first, then Display (proves the whole settings path end to end), then Backups and Profiles, then Diagnostics, then Archive last — it is the largest and the least coupled to the rest.

## Risks worth naming up front

| Risk | Impact | Mitigation |
|---|---|---|
| BIG endianness handled wrong | Archives the game silently rejects | Round-trip byte-identical test before any write feature |
| Version detection unreliable | Every INI write suspect | Hash first; refuse on unknown; never guess |
| Reference table wrong | Restore-to-stock corrupts config | Validate against schema; verify on a clean install |
| Multi-target rollback incomplete | Half-applied state | Back up all before any write; test failure at each step |
| Re-release diverges from assumptions | Two targets drop from v1 | Layer 0 runs first and can reshape scope |
| Save parser over-reaches | Cheat surface, corruption risk | No write path exists; test asserts it |
| UI thread blocking | Frozen window on large archives | Workers from the start, not retrofitted |

## Decisions already made — not reopening

D1 shipped tables · D2 spike first · D3 explicit apply · D4 Windows-only · D5 hash detection · D6 journal-based restore · D7 degraded SaveInfo · D8 full profiles · D9 first-run screen · D10 no preview · D11 retention 50 · D12 detect elevation · D13 FinalBIG · D14 two test tiers · D15 manual QA for three criteria

## Open Questions for User

1. **Project location.** The spec sits in `ai_companion/projects/generals-big-editor/`, which is a docs repo. Where does the actual Python source live — a new sibling repo, a subfolder here, or elsewhere?
2. **Layer 0 execution.** The spike needs a real Generals Online install and GenTool to inspect. Do you have those, or should the spike be desk research against community documentation?
3. **Name.** Spec is now titled "Generals Companion" since it outgrew "BIG Editor". Keep, or prefer something else?
