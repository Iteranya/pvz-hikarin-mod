// HikarinPvZMod.cs — REAL MelonLoader (IL2CPP) mod for Plants vs Zombies: Fusion 4.1.
// v2: Adventure-mode integration. levelN_begin fires when InitBoard
// appears (seed-select, game paused via Time.timeScale=0), levelN_win
// fires when the victory trophy appears (paused at trophy), then the
// game resumes and auto-advances to the next level on its own.
// Current level is read from playerData.json advLevelCompleted.
// F8 remains a manual overlay hide/show override.

using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using MelonLoader;
using UnityEngine;

[assembly: MelonInfo(typeof(HikarinPvZ.HikarinPvZMod), "HikarinPvZ", "0.1.0", "Viel")]
[assembly: MelonGame("LanPiaoPiao", "PlantsVsZombiesRH")]

namespace HikarinPvZ
{
    public sealed class JsonAction
    {
        public string Type = "";
        public string Action = "";
        public string Label = "";
        public string Content = "";
        public string Level = "";
        public string OnComplete = "";
        public string OnFail = "";
        public string Var = "";
        public string Condition = "equal";
        public string ValueRaw = "";
        public int Id;
        public int End = -1;
        public List<(string label, string display)> Choices = new List<(string, string)>();
    }

    public enum PlayerState { Hidden, Dialogue, Choice, PlayLevel, Finished }

    public sealed class StoryPlayer
    {
        private readonly List<JsonAction> _actions;
        private readonly Dictionary<string, int> _labels = new Dictionary<string, int>();
        public readonly Dictionary<string, object> State = new Dictionary<string, object>();
        public readonly List<string> Log = new List<string>();
        public PlayerState Mode = PlayerState.Hidden;
        public JsonAction Current;
        public string Checkpoint;

        public StoryPlayer(List<JsonAction> actions)
        {
            _actions = actions;
            for (int i = 0; i < actions.Count; i++)
                if (actions[i].Type == "label")
                    _labels[actions[i].Label] = i;
        }

        private int Pc;
        private void Jump(string label)
        {
            if (!_labels.TryGetValue(label, out int idx))
                throw new InvalidOperationException("missing label: " + label);
            Pc = idx;
        }

        private static bool Compare(object var, string cond, object value)
        {
            switch (cond)
            {
                case "equal": return Equals(var, value);
                case "not_equal": return !Equals(var, value);
                case "exists": return var != null;
                case "not_exists": return var == null;
                case "day": return true;
                case "night": return false;
                default:
                    try
                    {
                        double a = Convert.ToDouble(var ?? 0), b = Convert.ToDouble(value ?? 0);
                        if (cond == "greater_than") return a > b;
                        if (cond == "less_than") return a < b;
                        if (cond == "greater_or_equal") return a >= b;
                        if (cond == "less_or_equal") return a <= b;
                    }
                    catch { }
                    return false;
            }
        }

        private static object ParseValue(string raw)
        {
            if (raw == "true") return true;
            if (raw == "false") return false;
            if (long.TryParse(raw, out long l)) return l;
            if (double.TryParse(raw, out double d)) return d;
            return raw;
        }

        public void Advance()
        {
            int guard = 0;
            while (Pc < _actions.Count)
            {
                if (++guard > 10000) throw new InvalidOperationException("step loop");
                var a = _actions[Pc++];
                Current = a;
                switch (a.Type)
                {
                    case "meta":
                    case "label":
                    case "show_sprite":
                    case "modify_background":
                    case "clear_background":
                    case "give_item":
                    case "take_item":
                    case "play_music":
                    case "play_sound":
                    case "command":
                        continue;
                    case "dialogue":
                        Mode = PlayerState.Dialogue;
                        return;
                    case "choice":
                    case "night_choice":
                        Mode = PlayerState.Choice;
                        return;
                    case "transition":
                        if (a.Action == "jump") Jump(a.Label);
                        continue;
                    case "conditional":
                    case "conditional_global":
                        {
                            object var = State.TryGetValue(a.Var, out var v) ? v : null;
                            bool pass = Compare(var, a.Condition, ParseValue(a.ValueRaw));
                            if (!pass && a.End >= 0) Pc = a.End;
                            continue;
                        }
                    case "modify_variable":
                    case "modify_global":
                        State[a.Var] = ParseValue(a.ValueRaw);
                        continue;
                    case "next":
                        Checkpoint = a.Label;
                        continue;
                    case "play_level":
                        Mode = PlayerState.PlayLevel;
                        Log.Add("PLAY_LEVEL " + a.Level);
                        return;
                    case "finish_dialogue":
                        Mode = PlayerState.Finished;
                        Log.Add("FINISH");
                        return;
                    default:
                        continue;
                }
            }
            Mode = PlayerState.Finished;
        }

        public void Choose(string label) { Jump(label); Advance(); }
        public void CompleteLevel()
        {
            if (!string.IsNullOrEmpty(Current?.OnComplete)) Jump(Current.OnComplete);
            Advance();
        }
        public void FailLevel()
        {
            if (!string.IsNullOrEmpty(Current?.OnFail)) Jump(Current.OnFail);
            else Pc--;
            Advance();
        }
        public void Start(string startLabel = null)
        {
            Pc = 0;
            if (!string.IsNullOrEmpty(startLabel)) Jump(startLabel);
            else if (!string.IsNullOrEmpty(Checkpoint)) Jump(Checkpoint);
            Advance();
        }
    }

    public class HikarinPvZMod : MelonMod
    {
        private StoryPlayer _player;
        private bool _visible;
        private string _storyPath;
        private readonly Dictionary<string, (string name, int number)> _manifest =
            new Dictionary<string, (string, int)>();
        // v2 phase machine: None -> Begin -> Playing -> Win -> (next level)
        private string _phase = "None";
        private int _level = 1;
        private int _frame;
        private bool _pollInitLogged;
        private bool _pauseFailed;

        public override void OnInitializeMelon()
        {
            LoggerInstance.Msg("HikarinPvZ v2 initializing");
            string baseDir = AppDomain.CurrentDomain.BaseDirectory;
            string dir = Path.Combine(baseDir, "Mods", "HikarinPvZ");
            _storyPath = Path.Combine(dir, "adventure_story_v2.json");
            LoadStory();
            _level = ReadSaveLevel();
            LoggerInstance.Msg($"[HikarinPvZ] current Adventure level from save: {_level}");
        }

        public override void OnSceneWasLoaded(int buildIndex, string sceneName)
        {
            LoggerInstance.Msg($"[HikarinPvZ] Scene loaded: idx={buildIndex} name={sceneName}");
            if (sceneName == "Main")
            {
                // Back at the menu: cancel any pending VN, unpause.
                _phase = "None";
                _visible = false;
                SetTimeScale(1f);
            }
        }

        private int ReadSaveLevel()
        {
            try
            {
                string profile = Environment.GetEnvironmentVariable("USERPROFILE");
                string[] candidates =
                {
                    Path.Combine(profile, "AppData", "LocalLow", "LanPiaoPiao",
                        "PlantsVsZombiesRH", "Saves", "Texas", "playerData.json"),
                    Path.Combine(profile, "AppData", "LocalLow", "LanPiaoPiao",
                        "PlantsVsZombiesRH", "playerData.json"),
                };
                foreach (var path in candidates)
                {
                    if (!File.Exists(path)) continue;
                    using var doc = JsonDocument.Parse(File.ReadAllText(path));
                    if (!doc.RootElement.TryGetProperty("advLevelCompleted", out var arr)) continue;
                    int i = 0;
                    foreach (var el in arr.EnumerateArray())
                    {
                        if (el.ValueKind == JsonValueKind.False) return Math.Min(i + 1, 3);
                        i++;
                    }
                    return 3; // all beaten (within demo range)
                }
            }
            catch (Exception ex)
            {
                LoggerInstance.Warning("[HikarinPvZ] ReadSaveLevel failed: " + ex.Message);
            }
            return 1;
        }

        private void SetTimeScale(float s)
        {
            if (_pauseFailed) return;
            try { Time.timeScale = s; }
            catch (Exception ex)
            {
                _pauseFailed = true;
                LoggerInstance.Warning("[HikarinPvZ] Time.timeScale unavailable, continuing unpaused: " + ex.Message);
            }
        }

        private void BeginScene()
        {
            _level = ReadSaveLevel();
            _phase = "Begin";
            _visible = true;
            SetTimeScale(0f);
            _player.Start($"level{_level}_begin");
            LoggerInstance.Msg($"[HikarinPvZ] BEGIN level {_level} (paused, seed-select hook)");
        }

        private void WinScene()
        {
            _phase = "Win";
            _visible = true;
            SetTimeScale(0f);
            _player.Start($"level{_level}_win");
            LoggerInstance.Msg($"[HikarinPvZ] WIN level {_level} (paused at trophy)");
        }

        private void ResumeGame()
        {
            SetTimeScale(1f);
            _visible = false;
            if (_phase == "Win") _level = Math.Min(_level + 1, 3);
            _phase = "Playing";
            LoggerInstance.Msg("[HikarinPvZ] resumed game, next level will begin-hook at " + _level);
        }

        private bool InitBoardPresent()
        {
            try
            {
                var ib = Il2Cpp.InitBoard.Instance;
                return ib != null;
            }
            catch { return false; }
        }

        private bool TrophyPresent()
        {
            try
            {
                var go = GameObject.Find("victoryTrophy");
                return go != null;
            }
            catch { return false; }
        }

        private void LoadManifest(string path)
        {
            if (!File.Exists(path)) { LoggerInstance.Warning("manifest not found: " + path); return; }
            using var doc = JsonDocument.Parse(File.ReadAllText(path));
            foreach (var prop in doc.RootElement.EnumerateObject())
            {
                string name = prop.Value.GetProperty("name").GetString();
                int num = prop.Value.GetProperty("levelNumber").GetInt32();
                _manifest[prop.Name] = (name, num);
            }
            LoggerInstance.Msg($"HikarinPvZ manifest: {_manifest.Count} levels");
        }

        private void LoadStory()
        {
            if (!File.Exists(_storyPath))
            {
                LoggerInstance.Error("story not found: " + _storyPath);
                return;
            }
            var actions = new List<JsonAction>();
            using var doc = JsonDocument.Parse(File.ReadAllText(_storyPath));
            foreach (var el in doc.RootElement.EnumerateArray())
            {
                var a = new JsonAction
                {
                    Type = el.TryGetProperty("type", out var t) ? t.GetString() ?? "" : "",
                    Action = el.TryGetProperty("action", out var ac) ? ac.GetString() ?? "" : "",
                    Label = el.TryGetProperty("label", out var l) ? l.GetString() ?? "" : "",
                    Content = el.TryGetProperty("content", out var c) ? c.GetString() ?? "" : "",
                    Level = el.TryGetProperty("level", out var lv) ? lv.GetString() ?? "" : "",
                    OnComplete = el.TryGetProperty("on_complete", out var oc) ? oc.GetString() ?? "" : "",
                    OnFail = el.TryGetProperty("on_fail", out var of) ? of.GetString() ?? "" : "",
                    Var = el.TryGetProperty("var", out var vr) ? vr.GetString() ?? "" : "",
                    Condition = el.TryGetProperty("condition", out var cd) ? cd.GetString() ?? "equal" : "equal",
                };
                if (el.TryGetProperty("id", out var id)) a.Id = id.GetInt32();
                if (el.TryGetProperty("end", out var en) && en.ValueKind == JsonValueKind.Number) a.End = en.GetInt32();
                if (el.TryGetProperty("value", out var val))
                    a.ValueRaw = val.ValueKind == JsonValueKind.String ? val.GetString() ?? "" : val.GetRawText();
                if (el.TryGetProperty("choice", out var ch))
                    foreach (var o in ch.EnumerateArray())
                        a.Choices.Add((o.GetProperty("label").GetString() ?? "",
                                       o.GetProperty("display").GetString() ?? ""));
                actions.Add(a);
            }
            _player = new StoryPlayer(actions);
            LoggerInstance.Msg($"HikarinPvZ story loaded: {actions.Count} actions from {_storyPath}");
        }

        public override void OnUpdate()
        {
            if (Input.GetKeyDown(KeyCode.F8))
            {
                _visible = !_visible;
                LoggerInstance.Msg("HikarinPvZ overlay visible=" + _visible);
            }

            // Dialogue advance (works in Begin/Win phases, game paused).
            if (_visible && _player != null &&
                (_phase == "Begin" || _phase == "Win"))
            {
                if (_player.Mode == PlayerState.Dialogue &&
                    (Input.GetMouseButtonDown(0) || Input.GetKeyDown(KeyCode.Space)))
                {
                    _player.Advance();
                }
                if (_player.Mode == PlayerState.Choice)
                {
                    // Choices are rendered as buttons in OnGUI.
                }
                if (_player.Mode == PlayerState.Finished)
                {
                    ResumeGame();
                }
            }

            // Throttled hook polling (~every 15 frames).
            if (++_frame % 15 != 0) return;
            try
            {
                if (_phase == "None" || _phase == "Playing")
                {
                    bool present = InitBoardPresent();
                    if (present && !_pollInitLogged)
                    {
                        _pollInitLogged = true;
                        LoggerInstance.Msg("[HikarinPvZ] InitBoard detected");
                    }
                    if (_phase == "None" && present)
                    {
                        BeginScene();
                    }
                    else if (_phase == "Playing" && !present)
                    {
                        // Level scene unloaded without a win (quit/lose):
                        // re-arm so the next InitBoard replays the begin.
                        _phase = "None";
                        _pollInitLogged = false;
                        LoggerInstance.Msg("[HikarinPvZ] level scene gone, re-armed begin hook");
                    }
                }
                if (_phase == "Playing" && TrophyPresent())
                {
                    WinScene();
                }
            }
            catch (Exception ex)
            {
                LoggerInstance.Warning("[HikarinPvZ] poll failed: " + ex.Message);
            }
            foreach (var entry in _player.Log) { LoggerInstance.Msg("[HikarinPvZ] " + entry); _player.Log.Clear(); break; }
        }

        public override void OnGUI()
        {
            if (!_visible || _player == null) return;
            try { RenderOverlay(); }
            catch (Exception ex)
            {
                // e.g. an IMGUI method stripped from this IL2CPP build:
                // log once, hide, don't spam the log every frame.
                LoggerInstance.Error("[HikarinPvZ] OnGUI failed, hiding overlay: " + ex.GetType().Name + " " + ex.Message);
                _visible = false;
            }
        }

        private void RenderOverlay()
        {
            // NOTE: GUILayout.BeginArea is stripped from Fusion's IL2CPP
            // build ("Method unstripping failed"), so the overlay is drawn
            // with plain GUI.Label/GUI.Box at fixed rects instead.
            var boxRect = new Rect(40, Screen.height - 190, Screen.width - 80, 160);
            GUI.Box(boxRect, "");
            switch (_player.Mode)
            {
                case PlayerState.Dialogue:
                    GUI.Label(new Rect(60, Screen.height - 170, Screen.width - 120, 30), _player.Current.Label);
                    GUI.Label(new Rect(60, Screen.height - 140, Screen.width - 120, 60), _player.Current.Content);
                    GUI.Label(new Rect(60, Screen.height - 60, Screen.width - 120, 30), "Click / Space to continue - F8 hide");
                    break;
                case PlayerState.Choice:
                    GUI.Label(new Rect(60, Screen.height - 170, Screen.width - 120, 30), "Choose:");
                    int i = 0;
                    foreach (var (label, display) in _player.Current.Choices)
                    {
                        if (GUI.Button(new Rect(60, Screen.height - 140 + i * 30, 300, 28), display))
                            _player.Choose(label);
                        i++;
                    }
                    break;
                case PlayerState.PlayLevel:
                    {
                        string lv = _player.Current.Level;
                        string pretty = _manifest.TryGetValue(lv, out var m) ? $"{m.name} (#{m.number})" : lv;
                        GUI.Label(new Rect(60, Screen.height - 170, Screen.width - 120, 30), "PLAY LEVEL: " + pretty);
                        GUI.Label(new Rect(60, Screen.height - 140, Screen.width - 120, 60), "In game: Adventure Mode > Day > that level. Beat it, then come back here.");
                        GUI.Label(new Rect(60, Screen.height - 60, Screen.width - 120, 30), "ENTER = won   F = lost / retry");
                        break;
                    }
                case PlayerState.Finished:
                    GUI.Label(new Rect(60, Screen.height - 170, Screen.width - 120, 30), "- End of demo story -  F8 hide, F9 restart");
                    if (Input.GetKeyDown(KeyCode.F9)) _player.Start();
                    break;
            }
        }
    }
}
