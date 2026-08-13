# Findings

Evidence gathered from a real Zero Hour installation and from community
documentation. Each finding changed a design decision, so they are recorded
here rather than lost in commit messages.

Method: direct inspection of `%USERPROFILE%\Documents\Command and Conquer
Generals Zero Hour Data\` — its `Options.ini`, 17 save files and two crash
logs — plus published format documentation for the archive layout.

---

## F1 — Resolution injection works, and the format is not obvious

`Options.ini` contained:

```
Resolution = 2560 1440
```

The in-game menu never offers 1440p. The config file accepts it anyway, which
is the entire quality-of-life pitch confirmed in one line.

Note the format: **space-separated, not `x`-separated**. A writer that emits
`2560x1440` produces a value the game silently ignores.

The file held 17 keys. Community documentation lists roughly 30. The missing
ones are graphics settings the user never changed — which is why the tool
treats an absent key as "game default" rather than "unsupported", and only
writes a key the user has actually altered.

## F2 — The FPS key is not where it looks like it should be

`Options.ini` has no framerate key. `Skirmish.ini` does:

```
FPS = 30
```

But `Skirmish.ini` stores last-used skirmish match settings, and this value is
the simulation tick rate rather than a render cap. Editing it changes game
speed, not smoothness.

The real switch is the command-line flag `-nofpslimit`, which does lift the
30 FPS limit. It also makes the game run at roughly double speed, because the
engine ties simulation speed to framerate — units move faster, buildings finish
sooner, animations run fast.

**Consequence:** the switch ships opt-in with an explicit warning, and points
at GenTool for anyone wanting high FPS at correct speed. Advertising it as a
smoothness fix would have been wrong.

## F3 — A UTF-16 string inside an ASCII file

```
UserName = O_00R_00I_00G_00I_00N_00
```

That is `ORIGIN` stored as UTF-16, with interleaved null bytes, inside an
otherwise-ASCII config file.

**Consequence:** `configparser` is unusable here. It discards comments,
reorders keys, and normalises encoding — the last of which would corrupt the
player's profile name. The INI parser keeps every line verbatim and rewrites
only the values that actually changed.

## F4 — Save files are chunked and cheap to identify

First bytes of a save:

```
0f 43 48 55 4e 4b 5f 47 61 6d 65 53 74 61 74 65   .CHUNK_GameState
36 00 00 00 02 00 00 00 ...
   ... 0c 4d 44 5f 55 53 41 30 31 2e 6d 61 70      ..MD_USA01.map
   03 75 73 61                                     .usa
0e 43 48 55 4e 4b 5f 43 61 6d 70 61 69 67 6e      .CHUNK_Campaign
1c 00 00 00 05 03 75 73 61 09 6d 69 73 73 69 6f 6e 30 31
                                                   ...usa.mission01
```

Layout: `[uint8 name_len][ASCII chunk name][uint32 size LE][payload]`.
Chunks observed: `CHUNK_GameState`, `CHUNK_Campaign`, `CHUNK_GameStateMap`.

Map, faction and mission are all readable within the first few kilobytes, so a
3 MB save costs one small read to identify.

Two cases the spec did not anticipate:

- **Generals Challenge saves carry no faction token.** `GC_TankGeneral.map`,
  `GC_AirGeneral.map` and similar return no `usa`/`china`/`gla` match, correctly,
  because it is not there. The opponent has to come from the map filename.
- **Two distinct save kinds.** Saves cluster at either ~200 bytes or 2–6 MB.
  The small ones are campaign progress markers with two chunks; full game states
  have three.

The read-only rule is unchanged by any of this.

## F5 — Crash logs are structured enough to classify

```
Release Crash at Fri Mar 14 14:41:27 2025
; Reason Uncaught exception in Main::WndProc... probably should not happen
Exception is access violation
Error code: EXCEPTION_ACCESS_VIOLATION
Access address:00000000 was read from.
Register dump... Eip/Esp/Ebp/Eax/...
Bytes at CS:EIP (72ECFDC5) : 8B 07 FF 71 20 ...
```

Timestamp, reason, exception type, faulting address, register state and opcode
bytes are all parseable. The sample is a null-pointer read, which is a
classifiable signature.

Not yet built into the tool, but the format supports it.

## F6 — BIG archive format, and the endianness trap

Confirmed against the Thyme project's format documentation:

```c
struct BIGFileHeader {
    uint32_t id;            // "BIGF" (Generals/ZH) or "BIG4" (BFME)
    uint32_t archive_size;  // LITTLE endian
    uint32_t file_count;    // BIG endian
    uint32_t data_start;    // BIG endian
};
struct IndexEntry {
    int32_t file_size;      // BIG endian
    int32_t position;       // BIG endian
    char    file_name[n];   // null-terminated, max 260 chars
};
```

Three consecutive 32-bit integers, and the first is byte-ordered differently
from the other two. Reading `file_count` little-endian turns 1 into
**16,777,216** — same four bytes, reversed — and the tool then tries to read
sixteen million index records from a file holding one.

**Consequence:** the round-trip test (open, write back unedited, compare bytes)
is the acceptance criterion for the whole format layer. It fails immediately if
any field's endianness is wrong.

## F7 — Command-line switches

Verified against C&C Labs and community guides:

| Switch | Effect |
|---|---|
| `-quickstart` | Skips intro movies and the shell map |
| `-noshellmap` | Keeps intros, drops the animated menu backdrop |
| `-nologo` | Skips the EA logo |
| `-win` | Windowed mode |
| `-noshaders` | Legacy compatibility for old ATI hardware |
| `-xres` / `-yres` | Sets resolution without touching `Options.ini` |
| `-mod` | Loads a mod archive |
| `-nofpslimit` | Lifts the FPS cap — see F2 |

`-xres`/`-yres` turned out to be more useful than expected: they set resolution
without writing to disk, so the change is undone by simply launching without
them. This became its own screen, which the original spec did not include.

---

## Still unverified

| Item | Why |
|---|---|
| GenTool overlap behaviour | Not installed on the dev machine |
| Generals Online re-release config paths and archive format | Not installed |
| Generals 1.08 key differences | Data folder exists but its `Options.ini` was not compared |
| Aspect-ratio correction | No corresponding key found in `Options.ini`; may not be INI-addressable |
