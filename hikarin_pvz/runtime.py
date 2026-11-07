"""PvZ Fusion x Hikarin runtime (reference / headless prototype).

This mirrors the C# MelonLoader mod in ``mod/``. It proves the data
contract works in Python (testable on this laptop with no Unity):

  VN script (Hikarin JSON)  ->  dialogue / choice / conditionals
                            ->  play_level "<name>"  (hooks.play_level)
                            ->  resume at on_complete / on_fail / fallthrough

The Unity mod replaces the hooks with real UI + level loading; the
state machine (pc, labels, variables, conditional semantics) is shared.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


class HookError(RuntimeError):
    pass


@dataclass
class Hooks:
    """Callbacks the host (Unity mod / headless test) provides."""

    dialogue: Callable[[dict, dict], None] = lambda a, s: None
    choice: Callable[[dict, dict], str] = lambda a, s: (a["choice"][0]["label"] if a.get("choice") else "")
    play_level: Callable[[str, dict, dict], str] = lambda level, a, s: "complete"
    show_sprite: Callable[[dict, dict], None] = lambda a, s: None
    background: Callable[[dict, dict], None] = lambda a, s: None
    item: Callable[[dict, dict], None] = lambda a, s: None
    audio: Callable[[dict, dict], None] = lambda a, s: None


def _compare(var: Any, condition: str, value: Any, state: dict) -> bool:
    """Hikarin conditional semantics: True = continue, False = jump to `end`."""
    if condition == "equal":
        return var == value
    if condition == "not_equal":
        return var != value
    if condition == "greater_than":
        return var > value
    if condition == "less_than":
        return var < value
    if condition == "greater_or_equal":
        return var >= value
    if condition == "less_or_equal":
        return var <= value
    if condition == "exists":
        return var is not None
    if condition == "not_exists":
        return var is None
    if condition == "day":
        return bool(state.get("isDay", True))
    if condition == "night":
        return bool(state.get("isNight", False))
    raise HookError(f"unknown condition {condition!r}")


class Runtime:
    def __init__(self, actions: list[dict], hooks: Hooks | None = None):
        self.actions = actions
        self.hooks = hooks or Hooks()
        self.state: dict[str, Any] = {"isDay": True, "isNight": False}
        self.events: list[dict] = []
        self.labels: dict[str, int] = {}
        for i, a in enumerate(actions):
            if a.get("type") == "label":
                name = a.get("label")
                if name in self.labels:
                    raise HookError(f"duplicate label {name!r}")
                self.labels[name] = i
        self.pc = 0
        self.checkpoint: str | None = None

    def _jump(self, label: str):
        if label not in self.labels:
            raise HookError(f"jump to missing label {label!r}")
        self.pc = self.labels[label]

    def run(self, start_label: str | None = None, max_steps: int = 10000) -> list[dict]:
        if start_label:
            self._jump(start_label)
        elif self.checkpoint:
            self._jump(self.checkpoint)
        steps = 0
        while self.pc < len(self.actions):
            steps += 1
            if steps > max_steps:
                raise HookError("step limit exceeded (infinite loop?)")
            a = self.actions[self.pc]
            t = a.get("type")
            self.pc += 1  # default: fall through; jumps overwrite pc

            if t in ("meta", "label"):
                continue
            if t == "dialogue":
                self.events.append({"event": "dialogue", **a})
                self.hooks.dialogue(a, self.state)
            elif t in ("choice", "night_choice"):
                if t == "night_choice" and not self.state.get("isNight"):
                    continue
                picked = self.hooks.choice(a, self.state)
                self.events.append({"event": "choice", "picked": picked})
                if picked:
                    self._jump(picked)
            elif t == "transition" and a.get("action") == "jump":
                self._jump(a.get("label", ""))
            elif t in ("conditional", "conditional_global"):
                var = self.state.get(a.get("var"))
                if not _compare(var, a.get("condition", "equal"), a.get("value"), self.state):
                    end = a.get("end")
                    if isinstance(end, int) and 0 <= end < len(self.actions):
                        self.pc = end
                    elif isinstance(end, str) and end:
                        self._jump(end)
                    # else: fall through (compiler normally resolves end to an id)
            elif t in ("modify_variable", "modify_global"):
                var, op, val = a.get("var"), a.get("action", "set"), a.get("value")
                if op == "set":
                    self.state[var] = val
                elif op == "increment_var":
                    self.state[var] = (self.state.get(var) or 0) + (val or 0)
                elif op == "subtract_var":
                    self.state[var] = (self.state.get(var) or 0) - (val or 0)
                self.events.append({"event": "set_var", "var": var, "value": self.state.get(var)})
            elif t == "play_level":
                level = a.get("level") or ""
                if not level:
                    raise HookError("play_level has no level name")
                self.events.append({"event": "play_level", "level": level})
                result = self.hooks.play_level(level, a, self.state)
                if result == "complete":
                    target = a.get("on_complete")
                    if target:
                        self._jump(target)
                elif result == "fail":
                    target = a.get("on_fail")
                    if target:
                        self._jump(target)
                    else:
                        # Default (documented): retry — re-run this action.
                        self.pc -= 1
                else:
                    raise HookError(f"play_level hook returned {result!r}, want complete/fail")
            elif t == "next":
                self.checkpoint = a.get("label") or self.checkpoint
                self.events.append({"event": "checkpoint", "label": self.checkpoint})
            elif t == "finish_dialogue":
                self.events.append({"event": "finish"})
                break
            elif t == "show_sprite":
                self.events.append({"event": "show_sprite", **a})
                self.hooks.show_sprite(a, self.state)
            elif t in ("modify_background", "clear_background"):
                self.events.append({"event": "background", **a})
                self.hooks.background(a, self.state)
            elif t in ("give_item", "take_item"):
                self.events.append({"event": "item", **a})
                self.hooks.item(a, self.state)
            elif t in ("play_music", "play_sound", "command", "unlock_dialogues", "idle_chat", "remove_sprite"):
                self.events.append({"event": t, **a})
                self.hooks.audio(a, self.state)
            else:
                self.events.append({"event": "unknown", "type": t})
        return self.events


def run_story(actions: list[dict], hooks: Hooks | None = None, **kw) -> list[dict]:
    """Convenience: build a Runtime and run it to completion."""
    return Runtime(actions, hooks).run(**kw)
