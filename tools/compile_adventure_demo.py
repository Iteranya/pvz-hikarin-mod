"""Compile the Adventure-mode demo story: VN scene -> Adventure Day L1/L2/L3 -> VN.

Linear, matching Fusion's own Adventure unlock order (wiki.gg Adventure):
  L1 tutorial: Sunflower + Peashooter (Sunshooter / Gatling Pea fusions taught)
  L2: Cherry Bomb introduced
  L3: Wall-nut introduced
Plant-waifu families unlock by introduction, like the real game.
"""
import json
import os
import sys

sys.path.insert(0, r"C:/Project/Hermes/hikarin-studio")
from hikarin.compiler import compile_project


def say(speaker, text):
    return {"kind": "say", "data": {"label": speaker, "content": text}}

def label(name):
    return {"kind": "label", "data": {"name": name}}

def play(level, on_complete, on_fail):
    return {"kind": "playLevel",
            "data": {"level": level, "on_complete": on_complete, "on_fail": on_fail}}

def setvar(var, value):
    return {"kind": "setVar",
            "data": {"scope": "", "var": var, "operation": "set", "value": str(value)}}

def end():
    return {"kind": "end", "data": {}}


FILES = {"main.story": [
    label("start"),
    say("Druid", "Adventure Day, Level 1. The Pea family and the Sunflowers are already arguing over who gets the front row."),
    say("Pea Waifu", "Plant me first. I shoot, she makes sun, we fuse — Sunshooter. That's the whole tutorial, druid."),
    label("day1"),
    play("adv_day_1", "win1", "retry1"),
    label("win1"),
    setvar("day", 1),
    say("Sunflower Waifu", "Level clear! Twin Sunflower says hi. Tomorrow something red and loud shows up."),
    label("day2"),
    play("adv_day_2", "win2", "retry2"),
    label("win2"),
    setvar("day", 2),
    say("Druid", "Cherry Bomb introduced today — she's a one-use plant, she does NOT do encores. Wall-nut tomorrow."),
    say("Cherry Waifu", "I am a single, perfect explosion. Do not ask me to do it again."),
    label("day3"),
    play("adv_day_3", "win3", "retry3"),
    label("win3"),
    setvar("day", 3),
    say("Druid", "Three Adventure levels survived. The Shrooms, Doom and Ice are still out there past the fog — later, druid's honor."),
    say("Pea Waifu", "Same time tomorrow. Bring fertilizer."),
    end(),
    label("retry1"),
    say("Druid", "Level 1 again. The lawn fell. Again."),
    {"kind": "jump", "data": {"target": "day1"}},
    label("retry2"),
    say("Druid", "Level 2 again. Cherry says she meant that. Go again."),
    {"kind": "jump", "data": {"target": "day2"}},
    label("retry3"),
    say("Druid", "Level 3 again. Wall-nut believes in us. He is a wall, he has no choice."),
    {"kind": "jump", "data": {"target": "day3"}},
]}

META = {"character": "druid", "startLabel": "start", "packName": "Druid Adventure Demo"}


def main():
    result = compile_project(META, FILES)
    print("compile errors:", result.errors)
    assert not result.errors, result.errors
    out_dir = r"C:/Project/Hermes/pvz-hikarin-mod/examples"
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "adventure_story.json"), "w", encoding="utf-8") as f:
        json.dump(result.actions, f, indent=2, ensure_ascii=False)
        f.write("\n")
    with open(os.path.join(out_dir, "adventure_story.story.json"), "w", encoding="utf-8") as f:
        json.dump(FILES["main.story"], f, indent=2, ensure_ascii=False)
        f.write("\n")
    manifest = {
        "adv_day_1": {"name": "Adventure Day Level 1", "levelNumber": 1, "file": "Adventure Mode > Day > Level 1"},
        "adv_day_2": {"name": "Adventure Day Level 2", "levelNumber": 2, "file": "Adventure Mode > Day > Level 2"},
        "adv_day_3": {"name": "Adventure Day Level 3", "levelNumber": 3, "file": "Adventure Mode > Day > Level 3"},
    }
    with open(os.path.join(out_dir, "adventure_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    levels = [a["level"] for a in result.actions if a.get("type") == "play_level"]
    print("play_level calls:", levels)
    assert levels == ["adv_day_1", "adv_day_2", "adv_day_3"]
    print("COMPILE OK -> examples/adventure_story.json")


if __name__ == "__main__":
    main()
