"""Arknights loop: VN -> play_level -> VN, with a fail branch."""

from hikarin_pvz import Hooks, run_story

# Hand-written to match Hikarin Studio's compiled output (see FORMAT.md).
# ids are sequential; conditional `end` is an action id; play_level keeps
# human-readable level names + resume labels.
STORY = [
    {"type": "meta", "action": "start", "id": 0},
    {"type": "label", "action": "label", "label": "start", "id": 1},
    {"type": "dialogue", "action": "say", "label": "Cupa", "content": "Zombies ahead. Ready?", "id": 2},
    {"type": "choice", "action": "choice", "choice": [
        {"label": "fight", "display": "Fight"},
        {"label": "retreat", "display": "Retreat"},
    ], "id": 3},
    {"type": "label", "action": "label", "label": "retreat", "id": 4},
    {"type": "dialogue", "action": "say", "label": "Cupa", "content": "Coward.", "id": 5},
    {"type": "finish_dialogue", "action": "finish_dialogue", "id": 6},
    {"type": "label", "action": "label", "label": "fight", "id": 7},
    {"type": "play_level", "action": "play_level", "level": "boss_fight_1",
     "on_complete": "after_win", "on_fail": "after_lose", "id": 8},
    {"type": "label", "action": "label", "label": "after_win", "id": 9},
    {"type": "modify_variable", "action": "set", "var": "won_boss", "value": True, "id": 10},
    {"type": "dialogue", "action": "say", "label": "Cupa", "content": "We won?!", "id": 11},
    {"type": "finish_dialogue", "action": "finish_dialogue", "id": 12},
    {"type": "label", "action": "label", "label": "after_lose", "id": 13},
    {"type": "dialogue", "action": "say", "label": "Cupa", "content": "We lost...", "id": 14},
    {"type": "finish_dialogue", "action": "finish_dialogue", "id": 15},
]


def test_win_path_plays_level_and_resumes_on_complete():
    played = []
    hooks = Hooks(
        choice=lambda a, s: "fight",
        play_level=lambda level, a, s: played.append(level) or "complete",
    )
    events = run_story(STORY, hooks)
    assert played == ["boss_fight_1"]
    kinds = [e["event"] for e in events]
    assert kinds.index("play_level") < kinds.index("dialogue", kinds.index("play_level"))
    # won_boss was set and the win dialogue ran
    assert any(e["event"] == "set_var" and e.get("var") == "won_boss" for e in events)
    assert any(e.get("content") == "We won?!" for e in events)


def test_lose_path_resumes_on_fail():
    hooks = Hooks(
        choice=lambda a, s: "fight",
        play_level=lambda level, a, s: "fail",
    )
    events = run_story(STORY, hooks)
    assert any(e.get("content") == "We lost..." for e in events)
    assert not any(e.get("content") == "We won?!" for e in events)


def test_retreat_never_plays_a_level():
    played = []
    hooks = Hooks(
        choice=lambda a, s: "retreat",
        play_level=lambda level, a, s: played.append(level) or "complete",
    )
    events = run_story(STORY, hooks)
    assert played == []
    assert any(e.get("content") == "Coward." for e in events)


def test_play_level_without_level_name_is_an_error():
    bad = [
        {"type": "meta", "action": "start", "id": 0},
        {"type": "label", "action": "label", "label": "start", "id": 1},
        {"type": "play_level", "action": "play_level", "level": "", "id": 2},
    ]
    try:
        run_story(bad)
    except Exception as e:  # HookError
        assert "level name" in str(e)
    else:
        raise AssertionError("expected HookError for empty level")
