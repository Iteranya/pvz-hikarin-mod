"""Compile v2 story: per-level begin/win scenes (no fail, no play_level).

Hook plan (mod): begin fires when InitBoard appears (seed-select phase,
game paused), win fires when the victory trophy appears (game paused),
then the game auto-advances to the next Adventure level on its own.
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

def setvar(var, value):
    return {"kind": "setVar",
            "data": {"scope": "", "var": var, "operation": "set", "value": str(value)}}

def end():
    return {"kind": "end", "data": {}}


FILES = {"main.story": [
    # ── Level 1 (Adventure Day 1: Sunflower + Peashooter tutorial) ──
    label("level1_begin"),
    say("Druid", "Day 1, before the first seeds are even chosen. The Pea family is already judging my card picks."),
    say("Pea Waifu", "Sunflower first, druid. ALWAYS Sunflower first. Then me. Then we fuse and become Sunshooter."),
    end(),
    label("level1_win"),
    setvar("day", 1),
    say("Sunflower Waifu", "Trophy! You picked up the trophy and you still came back to gloat. Twin Sunflower approves."),
    say("Druid", "Level 2 tomorrow. Something red is coming."),
    end(),
    # ── Level 2 (Cherry Bomb introduced) ──
    label("level2_begin"),
    say("Druid", "Day 2. The Cherry Bomb is awake. She is a one-use plant. She does NOT do encores."),
    say("Cherry Waifu", "I am a single, perfect explosion. Point me at the biggest crowd you have."),
    end(),
    label("level2_win"),
    setvar("day", 2),
    say("Cherry Waifu", "Level clear. I exploded beautifully and I would like a nap now."),
    say("Druid", "Level 3 tomorrow. Wall-nut's shift."),
    end(),
    # ── Level 3 (Wall-nut introduced) ──
    label("level3_begin"),
    say("Druid", "Day 3. Wall-nut has volunteered to be the front row. Forever. He has no choice, he is a wall."),
    say("Wall Waifu", "I will hold the line. Probably. Do not think about my health bar."),
    end(),
    label("level3_win"),
    setvar("day", 3),
    say("Wall Waifu", "We survived! The Shrooms are next — they only come out at night, and Doom and Ice are watching from the roof."),
    say("Druid", "Three Adventure levels down. The druid story continues in the fog."),
    end(),
]}

META = {"character": "druid", "startLabel": "level1_begin", "packName": "Druid Adventure v2"}


def main():
    result = compile_project(META, FILES)
    print("compile errors:", result.errors)
    assert not result.errors, result.errors
    out_dir = r"C:/Project/Hermes/pvz-hikarin-mod/examples"
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "adventure_story_v2.json"), "w", encoding="utf-8") as f:
        json.dump(result.actions, f, indent=2, ensure_ascii=False)
        f.write("\n")
    with open(os.path.join(out_dir, "adventure_story_v2.story.json"), "w", encoding="utf-8") as f:
        json.dump(FILES["main.story"], f, indent=2, ensure_ascii=False)
        f.write("\n")
    labels = [a["label"] for a in result.actions if a.get("type") == "label"]
    print("labels:", labels)
    assert labels == ["level1_begin", "level1_win", "level2_begin", "level2_win", "level3_begin", "level3_win"]
    print("COMPILE OK -> examples/adventure_story_v2.json")


if __name__ == "__main__":
    main()
