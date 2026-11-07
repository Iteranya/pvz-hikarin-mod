"""Generate 3 playable PvZ Fusion custom levels from a real template.

The template is a real custom-level JSON (Pond Level 1, from
Tproplay/Pvz-Fusion-Custom-Levels). We keep its scene/board shape and
only change the *variables* — sun, zombie multipliers, wave timing,
name and the unique levelNumber — exactly the on-the-fly knobs the
Super Custom node system exposes. Install target is the user's real
save: .../Saves/Texas/LevelData/Levels/
"""
import copy
import json
import os

TEMPLATE = r"C:/Project/Hermes/pvz-hikarin-mod/examples/_pond_level1_template.json"
OUT_DIR = r"C:/Project/Hermes/pvz-hikarin-mod/examples/levels"
GAME_LEVELS = (
    r"C:/Users/dev-01/AppData/LocalLow/LanPiaoPiao/PlantsVsZombiesRH"
    r"/Saves/Texas/LevelData/Levels"
)

# Linear progression: each day is harder, sun scales too.
DAYS = [
    dict(name="Druid Day 1", level_name="druid_day1", levelNumber=9001,
         startSun=500, maxWave=10, health=1.0, speed=1.0,
         waveInterval=30.0, firstWave=15.0),
    dict(name="Druid Day 2", level_name="druid_day2", levelNumber=9002,
         startSun=650, maxWave=15, health=1.5, speed=1.1,
         waveInterval=25.0, firstWave=12.0),
    dict(name="Druid Day 3", level_name="druid_day3", levelNumber=9003,
         startSun=800, maxWave=20, health=2.0, speed=1.25,
         waveInterval=20.0, firstWave=10.0),
]

MANIFEST = {}


def main():
    with open(TEMPLATE, encoding="utf-8") as f:
        template = json.load(f)
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(GAME_LEVELS, exist_ok=True)

    for d in DAYS:
        lvl = copy.deepcopy(template)
        lvl["name"] = d["name"]
        lvl["levelNumber"] = d["levelNumber"]
        lvl["startSun"] = d["startSun"]
        lvl["maxWave"] = d["maxWave"]
        cfg = lvl["boardConfig"]
        cfg["zombieHealthMultiplier"] = d["health"]
        cfg["zombieSpeedMultiplier"] = d["speed"]
        cfg["waveInterval"] = d["waveInterval"]
        cfg["firstWaveArrivedTimer"] = d["firstWave"]
        # Validity check: this is the shape the game actually loads.
        assert isinstance(lvl["levelNumber"], int)
        assert lvl["SpawnZombies"], "zombie pool must not be empty"
        assert lvl["boardConfig"]["zombieHealthMultiplier"] == d["health"]

        fname = f"{d['levelNumber']} - {d['name']}.json"
        for folder in (OUT_DIR, GAME_LEVELS):
            with open(os.path.join(folder, fname), "w", encoding="utf-8") as f:
                json.dump(lvl, f, indent=2)
        MANIFEST[d["level_name"]] = {
            "name": d["name"], "levelNumber": d["levelNumber"], "file": fname,
        }
        print(f"wrote {fname}  sun={d['startSun']} health=x{d['health']} waves={d['maxWave']}")

    manifest_path = os.path.join(OUT_DIR, "levels_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(MANIFEST, f, indent=2)
    print("manifest:", json.dumps(MANIFEST, indent=2))


if __name__ == "__main__":
    main()
