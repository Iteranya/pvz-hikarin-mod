# PvZ Fusion x Hikarin

Arknights-style VN <-> gameplay loop for **Plants vs Zombies: Fusion**
(植物大战僵尸：融合版, the Unity IL2CPP fan game by 蓝飘飘fly — *not*
the original PopCap PvZ).

You write the story in **Hikarin Studio**. It compiles to a flat JSON
list of actions. This mod is a MelonLoader (IL2CPP) DLL that reads that
JSON inside Fusion and plays it as a VN overlay. When the script hits
`play_level "<name>"`, the mod shows instructions to play that
**Adventure Mode** level (Adventure Mode has no real story of its own —
the mod supplies it), suspends the VN until you press Enter (won) or
F (lost / retry), then resumes at `on_complete` / `on_fail`.

```
VN scene  ->  play_level "adv_day_1"  ->  Adventure Day Level 1
   ^                                               |
   +---------------- on_complete / on_fail --------+
```

Game copy with the mod installed:
`C:/Users/dev-01/Downloads/PvZ-Fusion-4.1-English-PC-Hikarin/`
Launch it with `Launch-Hikarin.bat` in that folder (it sets up the
portable .NET 6 runtime in `runtime6/` for MelonLoader). The VN story
**auto-starts on the Main scene** — no F8 needed; it auto-hides while
you're inside a level scene and F8 stays as a manual hide/show override.
Press **F8** in-game to toggle the VN overlay manually. Adventure Day Levels 1–3 are the
demo loop: Pea/Sunflower intro (L1), Cherry Bomb (L2), Wall-nut (L3),
linear unlock by introduction like the real game.

## What's verified today

- **Real in-game mod, built and loaded.** MelonLoader 0.7.1 installed
  in the Hikarin game copy, .NET SDK 6.0.425 portable, mod compiled
  with `dotnet build` (0 warnings/errors), installed to
  `Mods/HikarinPvZ.dll`. Launch log (`MelonLoader/Latest.log`):
  v2 initializing, story loaded (28 actions), current level from save: 1.
- **v2 Adventure hooks:** `levelN_begin` fires when the game's
  `InitBoard` instance appears (seed-select phase, `Time.timeScale = 0`
  pause), `levelN_win` fires when a `victoryTrophy` object appears
  (paused at trophy), then the game resumes and auto-advances on its
  own. Current level is read from `playerData.json`
  (`advLevelCompleted`, first `false` +1). No fail scenes, no
  play_level — default is continue on win, per design.
- `hikarin_pvz/runtime.py` — Python reference runtime implementing the
  full state machine (pc, labels, conditionals, variables, checkpoint,
  `play_level` complete/fail/fallthrough). Tested headlessly:
  `uv run pytest -q` → 4 passed. This is the same logic the C# mod ports.
- Hikarin Studio now has a **Play Level (PvZ)** block (`playLevel`):
  `level` (name), `on_complete` / `on_fail` (labels). Compiler validates
  both labels and rejects an empty level name. Studio tests: 50 passed.
- Demo story `examples/adventure_story.json` compiles with 0 errors and
  calls `adv_day_1/2/3` (Adventure Day Levels 1–3).

## What's NOT done yet (honest blockers)

1. **Auto-launching / auto-detecting Adventure levels.** The overlay
   shows you which Adventure level to play; you start it manually via
   Adventure Mode > Day, then press Enter (won) / F (lost) back in the
   VN. Auto-launch + win detection needs Fusion's
   LevelManager/CustomLevelData API (`Assembly-CSharp.dll`). The mod
   logs every scene loaded — play Adventure L1 and check the log for
   its scene name, that's the discovery step for wiring it up.
2. **Custom levels are a side path now.** 3 custom levels
   (9001–9003) are installed in the real save
   (`Saves/Texas/LevelData/Levels/`) and playable via Custom Levels,
   but the main loop is Adventure Mode (see above). Delete those JSONs
   if you don't want them.

## Layout

```
hikarin_pvz/runtime.py   Python reference runtime (tested)
tests/test_runtime.py    Arknights loop tests (win / lose / retreat)
mod/                   C# MelonLoader skeleton (needs dotnet + MelonLoader)
examples/              compiled demo story JSON
```

## The data contract

```json
{ "type": "play_level", "action": "play_level",
  "level": "boss_fight_1",
  "on_complete": "after_win",
  "on_fail": "after_lose", "id": 8 }
```

- `level` is a human name. Fusion identifies levels by the internal
  `levelNumber` in each level JSON (`.../LevelData/Levels/`), so the
  runtime must resolve name → `levelNumber` at load time and error
  loudly if it's missing (same "did you mean" idea as Studio jumps).
- Empty `on_complete` = fall through to the next block.
- Empty `on_fail` = retry the level (re-run this action).
- Save the checkpoint (`next`) *before* `play_level`, so a crash
  mid-level resumes the VN instead of restarting the scene.
