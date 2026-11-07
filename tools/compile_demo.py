"""Compile a playLevel story with Hikarin Studio, save it, run it headless."""
import json
import os
import sys

sys.path.insert(0, r"C:/Project/Hermes/hikarin-studio")
sys.path.insert(0, r"C:/Project/Hermes/pvz-hikarin-mod")

from hikarin.compiler import compile_project
from hikarin_pvz import Hooks, run_story

meta = {"character": "cupa", "startLabel": "start", "packName": "Demo"}
files = {"main.story": [
    {"kind": "label", "data": {"name": "start"}},
    {"kind": "say", "data": {"label": "Cupa", "content": "VN time."}},
    {"kind": "playLevel", "data": {"level": "boss_fight_1", "on_complete": "win", "on_fail": "lose"}},
    {"kind": "label", "data": {"name": "win"}},
    {"kind": "say", "data": {"label": "Cupa", "content": "Back from the level!"}},
    {"kind": "end", "data": {}},
    {"kind": "label", "data": {"name": "lose"}},
    {"kind": "say", "data": {"label": "Cupa", "content": "Lost... retry?"}},
    {"kind": "end", "data": {}},
]}

result = compile_project(meta, files)
print("compile errors:", result.errors)
assert not result.errors, result.errors

out = r"C:/Project/Hermes/pvz-hikarin-mod/examples/demo_story.json"
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w", encoding="utf-8") as f:
    json.dump(result.actions, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", out)

played = []
hooks = Hooks(play_level=lambda level, a, s: played.append(level) or "complete")
events = run_story(result.actions, hooks)
print("played:", played)
print("events:", [(e["event"], e.get("content", e.get("level", ""))) for e in events])
assert played == ["boss_fight_1"]
assert any(e.get("content") == "Back from the level!" for e in events)
print("INTEGRATION OK")
