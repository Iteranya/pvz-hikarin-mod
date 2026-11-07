"""Compile the Druid demo story (linear, 3 play_level calls) with Hikarin Studio."""
import json
import os
import sys

sys.path.insert(0, r"C:/Project/Hermes/hikarin-studio")
from hikarin.compiler import compile_project

# Block shorthand — kinds match hikarin/blocks.py BUILDERS.
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
    say("Druid", "Day 1. The zombies are at the fence. The Pea family said they'd help — if I survive today."),
    label("day1"),
    play("druid_day1", "win1", "retry1"),
    label("win1"),
    setvar("day", 1),
    say("Pea Waifu", "You lived! Repeater and I will carry seeds for you now. Tomorrow the Sunflowers wake up."),
    say("Druid", "Day 2. Sunflowers make sun. I need sun. We need sun."),
    label("day2"),
    play("druid_day2", "win2", "retry2"),
    label("win2"),
    setvar("day", 2),
    say("Sunflower Waifu", "Twin Sunflower sends her thanks. The Shrooms are… shy. They only come out at night."),
    say("Druid", "Day 3. Puff, Scaredy, Fume, Gloom. And something bigger watching from the roof."),
    label("day3"),
    play("druid_day3", "win3", "retry3"),
    label("win3"),
    setvar("day", 3),
    say("Shroom Waifu", "Doom and Ice chose to stay quiet today. They are not like us. You will know them when the roof burns."),
    say("Druid", "Three days survived. 297 to go for the three million. Fine. We feast tonight."),
    end(),
    # Fail branches: linear retry (jump straight back to the play block).
    label("retry1"),
    say("Druid", "The lawn fell. Again. Same day, same zombies — go again."),
    {"kind": "jump", "data": {"target": "day1"}},
    label("retry2"),
    say("Druid", "Again. The Sunflowers believe in us. Probably."),
    {"kind": "jump", "data": {"target": "day2"}},
    label("retry3"),
    say("Druid", "Again. Even the Shrooms are nervous now."),
    {"kind": "jump", "data": {"target": "day3"}},
]}

META = {"character": "druid", "startLabel": "start", "packName": "Druid Demo"}


def main():
    result = compile_project(META, FILES)
    print("compile errors:", result.errors)
    assert not result.errors, result.errors
    out_dir = r"C:/Project/Hermes/pvz-hikarin-mod/examples"
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "druid_story.json"), "w", encoding="utf-8") as f:
        json.dump(result.actions, f, indent=2, ensure_ascii=False)
        f.write("\n")
    with open(os.path.join(out_dir, "druid_story.story.json"), "w", encoding="utf-8") as f:
        json.dump(FILES["main.story"], f, indent=2, ensure_ascii=False)
        f.write("\n")
    levels = [a["level"] for a in result.actions if a.get("type") == "play_level"]
    print("play_level calls:", levels)
    assert levels == ["druid_day1", "druid_day2", "druid_day3"]
    print("wrote examples/druid_story.json + druid_story.story.json")
    print("COMPILE OK")


if __name__ == "__main__":
    main()
