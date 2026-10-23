# Getting started

This guide takes you from nothing to the first approved gate of your own game. It assumes macOS (the first game was made on an M1 Pro). Linux works with small changes, noted where they matter. Windows has not been tested.

## 1. What you need

| Requirement | Why | Required? |
|---|---|---|
| [Claude Code](https://claude.com/claude-code) | Runs the producer and the skills | Yes |
| [Godot 4](https://godotengine.org) with export templates | The game engine (we used 4.7) | Yes |
| Python 3.11 or newer | The `gf` CLI and sprite-gen | Yes |
| [Codex CLI](https://github.com/openai/codex) logged in with a ChatGPT plan | Writes code and generates sprite strips without spending Claude tokens | Strongly recommended |
| [sprite-gen](https://github.com/aldegad/sprite-gen) | Pose strips and animation for sprites | Recommended (installed by `gf-setup`) |
| Runway account with the Runway MCP connected to Claude Code | Identity art, key art, music, SFX, voice | Recommended |
| ffmpeg | Audio conversion, GIFs, video frames | Yes |
| Android SDK, JDK 17 and an emulator (AVD) | Builds and playtests on Android | For W7 and later |
| Xcode | iOS builds | Only for iOS |

You can start without Runway or Codex. The producer will tell you which steps need them, and pre-production up to G2 mostly needs only Claude.

## 2. Install the plugin

Inside Claude Code:

```text
/plugin marketplace add Hessel-It-Solutions/claude-game-factory
/plugin install game-factory@hessel
```

Restart Claude Code if it asks. Check that it loaded:

```text
/game-factory:game-factory status
```

To hack on the plugin itself, clone this repo and add it as a local marketplace instead:

```text
/plugin marketplace add /path/to/claude-game-factory
```

### Without Claude Code

The skills also work in other agents that support the Agent Skills format. Install them from [skills.sh](https://skills.sh/Hessel-It-Solutions/claude-game-factory):

```sh
npx skills add Hessel-It-Solutions/claude-game-factory
```

Use `-a <agent>` to pick the agent and `-s <skill>` to install only some skills. You get the skills without the plugin extras: there is no `/game-factory` command (ask in plain words, "start a new game called my_game with the game factory"), and `gf-setup` clones this repository to get the tools and templates. Subagents, parallel waves and the Runway MCP depend on what your agent supports.

## 3. Connect Runway (optional but recommended)

Connect Runway as an MCP server, either through the claude.ai connectors (it then shows up in Claude Code as `mcp__claude_ai_Runaway__*` tools, the connector name is spelled that way) or through your own MCP config. Ask Claude "what is my Runway balance?" to confirm it works. The producer checks the balance before and after every wave.

## 4. Start a game

Create an empty folder for the game, open Claude Code in it and run:

```text
/game-factory:game-factory new my_game
```

The producer creates the folder structure, `production/STATE.md` with every gate pending, a `.gitignore`, runs `git init` and starts W0.

### W0: setup

`gf-setup` checks and installs the toolchain, then copies the factory tools into your repo (`tools/gf`, `tools/codex`, `tools/playtest`, and the Godot scripts into `game/tools/`). Some steps may ask for your password or a decision. When everything is green you approve G0.

### W1: concept

The producer interviews you (a few rounds of questions about genre, platform, references, scope, monetization). Then, in parallel, it writes three distinct pitches, does market research and generates three style tiles. You pick one or combine them, it writes `docs/00-concept.md`, and you approve G1.

### Next

```text
/game-factory:game-factory next
```

`next` plans the next wave, shows you the plan with the estimated cost (Runway credits, Claude tokens, Codex tokens), waits for your approval when it is above the threshold, runs it, consolidates and tells you what to approve. Repeat until G3, when production starts.

## 5. Commands

| Command | What it does |
|---|---|
| `/game-factory:game-factory` or `status` | Phase, gates, current wave, next step, credits |
| `next` | Plan and run the next wave |
| `new <name>` | Create a new game and start W0 |
| `wave <id>` | Run a specific wave (production waves are refused before G3) |
| `gate <G#>` | Present the review package of a gate and ask for your decision |
| `tweak <request>` | Small fix wave: only the skills that own the affected files run |
| `chapter <chNN>` | Chapter loop: assets, integration, QA |

You can also talk to the skills directly. "Make the attack animation for the hero", "the jackal feels unfair, check the damage pacing", "run a blind playtest of chapter 1 from the den save", "review the chapter as an RPG". The skill descriptions carry these triggers.

## 6. Day to day after the vertical slice

The loop that took *David: Rise of a King* through 17 UX rounds:

1. Blind playtest on the emulator (`gf-playtester`). The tester gets only screenshots and taps.
2. Triage the report against the code. Each friction point becomes a fix with measurable acceptance criteria, or is marked as tester latency.
3. Write Codex briefs and launch them in parallel clones (`tools/codex/batch_launch.sh`).
4. Merge, run the full GUT suite and the scenario bot on main, look at the captures yourself.
5. Export the APK, install it on the emulator, play it.
6. Commit, then the next round with a fresh tester.

## 7. Keep a session handoff

Long sessions get summarized. Before you stop, ask Claude to update `production/SESSION_HANDOFF.md` and `production/STATE.md`. The next session starts with `/game-factory:game-factory status` and continues from there.
