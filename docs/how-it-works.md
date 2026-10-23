# How the factory works

The factory treats a game like a small studio would. There is a producer, there are specialists, there is a bible, and nothing goes into production until the bible is approved. The producer is Claude Code running the `/game-factory:game-factory` command. The specialists are the 25 `gf-*` skills. You are the director: every gate needs your explicit approval.

## Waves and gates

Work happens in waves. Inside a wave, independent tasks run in parallel; between waves there is a gate.

| Wave | Phase | What happens | Gate |
|---|---|---|---|
| W0 Setup | pre-production | Toolchain: Godot 4, export templates, Python, sprite-gen, ffmpeg, Android SDK, Codex CLI, Runway access | G0 |
| W1 Concept | pre-production | Interview, three pitches, market research, three style tiles. You pick or combine. | G1 |
| W2 Foundation | pre-production | GDD v1, narrative structure, style guide and palette, audio direction | G2 |
| W3 Cast and world | pre-production | Character sheets and identity bases, locations and key art, full script, content plan | |
| W4 Storyboard | pre-production | Storyboard per chapter, then a continuity review | G3 (unlocks production) |
| W5 Slice base | production | Godot core, hero sprites, first environment, UI kit, audio | |
| W6 Slice integration | production | Gameplay, level, cutscenes, enemy and NPC sprites | |
| W7 Slice check | production | QA, Android debug build | G4 (vertical slice on a phone) |
| W8+ Chapter N | production | Assets, then integration, then QA, per chapter | G5 on the last chapter |
| WF Release | release | Store builds, store listing, screenshots, trailer | G6 |

Rules the producer enforces:

- No production skill runs before G3 is approved. The only exception is style tests (draft sprites) during pre-production.
- A wave only starts when the previous one is done.
- Anything that needs a conversation with you (interviews, choosing between options) runs in the main session. Subagents produce options; the main session asks.
- A big game can restrict G3 to a pilot (the launch chapters). Chapters outside the pilot are not storyboarded or reviewed until they enter the queue.

After G4, most of the work is the chapter loop: produce assets, integrate, run the tests and the bot, run a blind playtest, triage, fix in Codex batches, repeat. *David: Rise of a King* went through 17 of these UX rounds on chapter 1.

## The bible

Pre-production produces the bible, a set of documents in `docs/`, each owned by one skill:

```text
docs/
  BIBLE.md                index and approval status
  00-concept.md           gf-concept
  01-gdd.md               gf-game-design
  02-art-direction.md     gf-art-direction (+ palette.hex)
  03-characters/          gf-characters
  04-world/               gf-world
  05-script/              gf-narrative
  06-storyboard/          gf-storyboard
  07-audio-direction.md   gf-audio
  08-content-plan.md      gf-game-design
```

IDs are born in the bible and never change: `chr_<name>`, `loc_<name>`, `seq_NN_<name>`, `chNN`, `lvl_chNN_NN`, `<type>_<owner>_<name>_vN`. Renaming needs a decision entry and a continuity pass.

## Production files

`production/` is the source of truth for the state of the project:

| File | What it holds |
|---|---|
| `STATE.md` | Phase, gates, current wave, next step |
| `DECISIONS.md` | Every locked decision with date and reason. Append-only. |
| `ASSETS.md` | Index of every generated asset: model, task id, references, cost, status |
| `BUDGET.md` | Runway credits per wave: balance before, estimate, spent, balance after |
| `waves/NN-<name>.md` | Plan and report of each wave |
| `SESSION_HANDOFF.md` | Where the last session stopped, so a fresh session can continue |

Templates for these files are in [`plugins/game-factory/templates/`](../plugins/game-factory/templates).

## File ownership

Each skill owns specific paths and writes only there. When a skill needs something outside its paths, it writes a request in its wave report and the producer turns it into a task. This is what lets several agents (Claude subagents or Codex batches) work in parallel without stepping on each other. The full table is in the `gf-producer` skill.

## The skills

| Group | Skills |
|---|---|
| Producer | `gf-producer` (the contract), `gf-setup` |
| Pre-production | `gf-concept`, `gf-game-design`, `gf-narrative`, `gf-world`, `gf-characters`, `gf-art-direction`, `gf-storyboard` |
| Art and audio | `gf-runway`, `gf-sprites`, `gf-environments`, `gf-ui`, `gf-audio` |
| Godot | `gf-godot-core`, `gf-gameplay`, `gf-levels`, `gf-cutscenes`, `gf-mobile` |
| Quality | `gf-autotest`, `gf-qa`, `gf-playtester`, `gf-rpg-review`, `gf-continuity` |
| Release | `gf-release` |

Each skill has a description with trigger phrases, so you can also call one directly without the producer: "make the walk cycle for the hero", "run a blind playtest of chapter 1", "review the chapter as an RPG".

## Tools

The plugin ships tools that `gf-setup` copies into your game repo at W0:

| Path in your game | What it does |
|---|---|
| `tools/gf/` | The `gf` CLI: post-process and validate pixel art against the palette, cut sheets, build review boards, build subagent context packs, register assets, log budget, update state, run mechanical continuity checks. Also `strip_rescale.py` and the config-driven `build_sprite_atlas.py`. |
| `tools/codex/` | `batch_launch.sh` runs a Codex batch in an isolated clone of the project; README with the brief template and the trust checklist. |
| `tools/playtest/` | Blind playtest kit: `cap.sh` (screenshot), `in.sh` (input bursts), the tester prompt and the journal format. |
| `game/tools/` | Godot scripts: `dump_collision.gd` (collision of a level as a PNG), `capture_scene.gd` (windowed capture of any scene), `bot_template.gd` (input-only scenario bot with invariants). |

Mechanical work goes through these tools, not through an LLM. If a tool is missing, extend `tools/gf` instead of leaving a one-off script somewhere.
