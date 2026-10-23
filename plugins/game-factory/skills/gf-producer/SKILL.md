---
name: gf-producer
description: "Producer of the pixel art mobile game factory. Owns the shared contracts (folder structure, STATE.md, approval gates, asset registry, Runway budget, file ownership), the wave map and the cost rules. Use whenever you plan, dispatch, consolidate or review a wave of /game-factory, open a new game in the factory, check status or gates, split work between Claude, Codex and Runway, or when any other gf-* skill needs to know where to write something or whether production is unlocked."
---

# gf-producer: factory contracts

Runs the game factory like a small studio. It owns the shared rules every other skill follows: the folder layout, the wave map, the approval gates G0 to G6, who writes which file, the asset registry and the Runway budget. It also decides who does each job: Claude plans and reviews, Codex writes code and sprites, Runway makes art and audio. Part of the [game factory](https://github.com/Hessel-It-Solutions/claude-game-factory), a set of skills that make pixel-art mobile games with Godot 4.

## When to use

- Starting a new game or checking its status
- Planning, dispatching or closing a wave of work
- Asking for approval at a gate before production starts
- Estimating credits and tokens before spending them

Produces: `production/STATE.md`, `DECISIONS.md`, `BUDGET.md`, wave plans and reports.

Works with: every gf-* skill; start with gf-setup.

---

Every `gf-*` skill obeys this file. If a skill contradicts the producer, the producer wins.

## Principle

A game is made like a studio makes one: **pre-production approved before any line of production**. Concept, script, characters, worlds, art direction and storyboard form the **game Bible**. Only after gate G3 (Bible approved by the user) may the production skills run.

Approval always comes from the user, explicit, recorded in `production/STATE.md`. No agent marks a gate as approved on its own.

**Storyboard fidelity:** no skill creates or integrates anything visual that does not follow the concept and art of the storyboard (`art/storyboard/`, `docs/06-storyboard/`) and `docs/02-art-direction.md` (section 0). Every visual delivery ships with a side-by-side board against the storyboard frame at the same scale; below the bar, redo it before integrating. The producer rejects a delivery without the board.

**Detail coherence guardrail:** all generated content follows the same art standard; no character less detailed than the scenery, and no scenery more detailed than the characters (`docs/02-art-direction.md` section 0.1). Character and animal bases are cut out of the storyboard, never redrawn by the AI. Every actor or scenery delivery includes the coherence board (the asset at game size over the real scenery, next to the approved reference character and the storyboard cutout); the producer checks it and rejects the delivery if one side looks more worked than the other.

## Who does what: Claude, Codex, Runway

| Tool | Role |
|---|---|
| **Claude Code** (this session) | Producer and director: plans waves, writes briefs, reviews diffs, measures, integrates, talks to the user. Claude does not do bulk implementation. |
| **Codex CLI** (ChatGPT subscription) | The engine for code (Godot GDScript, tools, tests), sprite pose strips (through sprite-gen with `--provider codex`), image edits, and long blind playtests. |
| **Runway** (MCP) | Identity bases, portraits, key art, storyboard frames, music, SFX, voice, and locomotion video for sprite cycles. |

Working rules for Codex:

- Run `codex exec ... < /dev/null`. Without the redirect it waits on stdin and hangs. Use a quoted heredoc (`<<'EOF'`) for long prompts, because an unquoted one executes backticks in the text.
- Options go before the subcommand (`codex exec -s workspace-write -o out.txt ...`). Pick your Codex coding model explicitly (we used `gpt-reserve` at medium reasoning; any capable coding model works).
- Run batches in isolated APFS clones of the repo (`cp -c -R` on macOS) so parallel jobs do not share `.godot/` or the save in `user://`. Two Godot processes in the same directory corrupt it.
- Give Codex a short list of acceptance criteria, not a long essay. Long code prompts come back as partial deliveries with green tests.
- Never trust a Codex report without measuring. Codex has faked captures, patched the bot so it passed, and written tests that only read the source. Check by reading the diff, running the test yourself, and looking at the result on a device or emulator.
- For visual adjustments (scale, color), do the measurement and the comparison board first, then send Codex only the chosen parameter.
- `sprite-gen` calls Codex internally: do not run it from inside a `codex exec` sandbox. Run `gen-set` from the terminal of the main session.

Cost rules (token cost counts as much as Runway credits):

- **Estimate before every wave**: Runway credits, Claude tokens and Codex tokens, per item (and per group when the wave has groups). Show it to the user and wait for approval before spending. After the wave, show the real numbers (balance via `whoami`).
- **Ask for approval** when the wave is estimated above **300 Runway credits**, or whenever it includes **batch video**.
- **Subagents always get an explicit `model`**. Never omit it (omitting inherits the session model, which may be the most expensive one). Default `sonnet`; see the model table below.
- **Few agents**, at most 1 or 2 at a time for Claude subagents. Each extra agent pays again for the shared context. Continue an existing agent with SendMessage instead of opening a new one.
- **Opus only diagnoses.** When Codex fails the same task three times, one read-only Opus subagent finds the cause (file and line), and Codex implements the fix. Opus is not for implementing Godot code, sprites or art that Codex can do.
- **Mechanical work goes to `tools/gf`**, never to an LLM and never to a throwaway script (see "Tools").
- **Scope on request**: do not review, illustrate or storyboard chapters that are not going to production now. G3 may cover only a pilot.
- **"Stop" or "stop everything" means stop now**: stop all running subagents (TaskStop) and kill only the `codex exec` and `sprite-gen` processes this session started (match the specific PIDs or command lines). Never `pkill -f codex`: it also kills the IDE's ChatGPT extension server and other tools whose path contains `.codex`. Do not resume without an explicit order.
- Runway called from a subagent is sometimes blocked by the permission classifier. Do not work around it: ask the user and generate from the main session. `list_recent` dumps huge URLs into the context; download results by task id (`get_task`) with a cheap Sonnet subagent instead.

## Game structure

Root = the game folder (for example `my_game/`).

```text
production/
  STATE.md            phase, gates, current wave, next step (source of truth)
  DECISIONS.md        locked decisions, with date and reason (append-only)
  ASSETS.md           index of every generated asset (see "Asset registry")
  BUDGET.md           Runway credits: estimated vs spent per wave
  waves/NN-<name>.md  plan + report of each wave
docs/                 the Bible
  BIBLE.md            index and approval status of each document
  00-concept.md       gf-concept
  01-gdd.md           gf-game-design
  02-art-direction.md gf-art-direction (+ palette.hex)
  03-characters/<chr_id>.md          gf-characters
  04-world/<loc_id>.md + world-map.md gf-world
  05-script/outline.md, chNN.md      gf-narrative
  06-storyboard/<seq_id>.md          gf-storyboard
  07-audio-direction.md              gf-audio
  08-content-plan.md  gf-game-design (list of levels/chapters and assets per chapter)
art/
  _refs/              style tiles, moodboards, approved references
  _prompts/<asset_id>.md   full prompt + model + task id of each generation
  characters/<chr_id>/concept|base|runs/
  environments/<loc_id>/keyart|tiles|parallax|props/
  ui/  storyboard/<seq_id>/  marketing/
audio/music  audio/sfx  audio/voice
game/                 Godot 4 project (project.godot)
  tools/              Godot-side tools (copied by gf-setup)
tools/gf/             factory CLI (copied by gf-setup), run with tools/gf/gf.sh
tools/codex/          Codex batch launcher
tools/playtest/       blind playtest kit
tools/sprite-gen/     clone + .venv of sprite-gen (gitignored)
```

### IDs

- character `chr_<name>` (example: `chr_hero`), location `loc_<name>`, sequence `seq_NN_<name>`, chapter `chNN`, level `lvl_chNN_NN`, asset `<type>_<owner>_<name>_vN` (example: `spr_chr_hero_walk_v2`).
- An ID is born in the Bible and does not change. Renaming needs an entry in DECISIONS.md and an update by gf-continuity.

## STATE.md

```markdown
# Production state: <Game name>
Phase: pre-production | production | release
Current wave: W<n> <name> (planned | running | in review | done)
Next step: <one sentence>

## Gates
| Gate | What it approves | Status | Date | User notes |
|---|---|---|---|---|
| G0 | Toolchain ready (gf-setup) | pending | | |
| G1 | Concept | pending | | |
| G2 | Foundation: GDD v1, narrative structure, art direction, audio direction | pending | | |
| G3 | Full Bible: cast, world, script, storyboard (UNLOCKS PRODUCTION) | pending | | |
| G4 | Playable vertical slice on a phone | pending | | |
| G5 | Full content (beta) | pending | | |
| G6 | Release candidate in the stores | pending | | |

## Open items
- ...
```

Gate status: `pending`, `in review`, `approved`, `rejected (reason)`. A rejected gate goes back to the previous wave with the user's notes as input.

## Wave map

| Wave | Phase | Execution | Skills |
|---|---|---|---|
| W0 Setup | pre | main | gf-setup → **G0** |
| W1 Concept | pre | 1a interview (main) · 1b parallel · 1c synthesis (main) | gf-concept (pitches + research), gf-art-direction (style exploration) → **G1** |
| W2 Foundation | pre | parallel | gf-game-design, gf-narrative (structure), gf-art-direction (style guide), gf-audio (direction) → **G2** |
| W3 Cast and world | pre | parallel | gf-characters (few agents, per large group of characters), gf-world, gf-narrative (script), gf-game-design (content plan) |
| W4 Storyboard | pre | parallel + review | gf-storyboard (1 agent per chapter), then gf-continuity → **G3** |
| W5 Slice base | prod | parallel | gf-godot-core, gf-sprites (protagonist), gf-environments (1st scene), gf-ui, gf-audio (production) |
| W6 Slice integration | prod | parallel | gf-gameplay, gf-levels, gf-cutscenes, gf-sprites (slice enemies/NPCs) |
| W7 Slice verification | prod | parallel | gf-qa, gf-mobile (Android debug build) → **G4** |
| W8+ Chapter N | prod | 3 sub-waves: assets → integration → QA | gf-sprites, gf-environments, gf-audio · gf-levels, gf-cutscenes, gf-gameplay · gf-qa, gf-continuity → **G5** on the last |
| WF Release | release | parallel | gf-mobile (store builds, monetization), gf-release (store, trailer, ASO) → **G6** |

Sequence rules:

- A big game can have G3 limited to a pilot (for example the launch chapters). In that case continuity, art and storyboard cover only the pilot; the other chapters go through them when they enter the queue. Do not spend an agent reviewing a chapter that will not be produced now.
- No production skill (`gf-sprites`, `gf-environments`, `gf-ui`, `gf-godot-core`, `gf-gameplay`, `gf-levels`, `gf-cutscenes`, `gf-mobile`, `gf-qa`, `gf-release`, `gf-audio` in production mode) runs while G3 is anything other than `approved`. Single exception: gf-art-direction and gf-characters may generate sprite **tests** in pre-production to validate the style, marked `draft`.
- A wave only starts when the previous one is `done`. Inside a wave, everything that does not depend on something else runs in parallel.
- Pre-production that needs conversation with the user (interview, choosing between options) happens in the main context. A subagent does not talk to the user: it produces options, the main session asks.

## Dispatching subagents

One subagent per task, all of the wave in a single message. Each subagent starts from zero and resends its whole context on every tool call, so unnecessary reading is paid for many times.

Savings rules:

- **Minimal context.** The prompt carries, pasted in, only the decisions and excerpts the task needs (ids, rules, numbers). Never "read the Bible" or the whole DECISIONS file; list the few files in scope and, when possible, the sections or lines.
- **Few agents.** Group by chapter or role, not by sequence or item. Parallel only when the work is big and truly independent.
- **Continue instead of opening.** An adjustment or second round goes by SendMessage to the agent that already read the context.
- **Consolidation and mechanical tasks** (ASSETS.md, slicing, boards, moving files, aligning text to decisions already made) with Sonnet, or in the main context if small.

Prompt template:

```text
You are the <role> of the game factory, working on the game <name> at <absolute root>.
1. Load the skill <skill> with the Skill tool (your craft). From gf-producer only what is summarized here applies.
2. Context (already summarized, do not reread the sources): <pasted decisions and excerpts>. Files you must open: <short list, with section/lines>.
3. Task: <what to deliver, how many options, what scope>.
4. You own ONLY these paths: <list>. Do not edit anything outside them. Need something outside? Write it under "Requests" in the report.
5. Runway budget for this task: up to <N> credits. If you go past the estimate, stop and report.
6. Write the report to production/waves/<NN>-<name>.<skill>.md with: deliverables (paths), decisions made, questions for the user, requests to other skills, credits spent, assets registered.
7. Reply in the user's language. End with a summary of at most 10 lines.
```

### Subagent model

The `model` parameter of Agent picks the model. **Always pass `model`; never omit it.** Default: `sonnet`.

| `sonnet` (default) | `opus` (only where the reasoning pays for the cost) |
|---|---|
| gf-world, gf-characters (sheets from the Bible) | gf-narrative (structure, script, dialogue) |
| gf-storyboard, gf-environments, gf-ui, gf-audio | gf-game-design (GDD v1, systems, economy) |
| gf-sprites, gf-levels, gf-cutscenes, gf-mobile, gf-release | gf-continuity (cross review before a gate, large diff only) |
| gf-concept (market research), gf-art-direction | gf-concept (pitches), gf-godot-core (architecture) |
| aligning docs to decided changes, consolidation, day-to-day gf-qa and gf-gameplay | diagnosing a hard bug when Codex spins (read-only) |

Use `fable` only when the user asks. Record in the wave plan which model each task used. If the user asks for another criterion, follow it.

Code, sprites and art that Codex can produce go to Codex, not to a Claude subagent. Claude subagents are for reading, planning and short consolidation.

### File ownership (who writes where)

| Skill | Owns |
|---|---|
| gf-concept | docs/00-concept.md |
| gf-game-design | docs/01-gdd.md, docs/08-content-plan.md |
| gf-art-direction | docs/02-art-direction.md, docs/palette.hex, art/_refs/ (includes art/_refs/sprite-test/) |
| gf-characters | docs/03-characters/, art/characters/*/concept, art/characters/*/base |
| gf-world | docs/04-world/, art/environments/*/keyart |
| gf-narrative | docs/05-script/, game/data/dialogue/ (source text) |
| gf-storyboard | docs/06-storyboard/, art/storyboard/ |
| gf-audio | docs/07-audio-direction.md, audio/, game/assets/audio/ |
| gf-sprites | art/characters/*/runs, art/characters/*/portraits, game/assets/sprites/, game/assets/portraits/ |
| gf-environments | art/environments/*/tiles,parallax,props, game/assets/environments/ |
| gf-ui | art/ui/, game/assets/ui/, game/scenes/ui/, game/assets/fonts/ |
| gf-godot-core | game/project.godot, game/default_bus_layout.tres, game/autoload/, game/core/, game/addons/, game/scenes/main.tscn |
| gf-gameplay | game/scenes/actors/, game/scripts/gameplay/, game/data/balance/ |
| gf-levels | game/scenes/levels/ (includes tilesets/<loc_id>.tres), game/data/levels/ |
| gf-cutscenes | game/scenes/cutscenes/, game/scripts/dialogue/, game/assets/illustrations/ |
| gf-mobile | game/export_presets.cfg, game/scripts/platform/, builds/ |
| gf-qa | game/tests/, production/qa/ |
| gf-release | store/, art/marketing/ |
| gf-continuity | read-only; writes production/continuity-report.md |
| gf-producer | production/STATE.md, DECISIONS.md, BUDGET.md, docs/BIBLE.md, waves/NN-<name>.md |

ASSETS.md is append-only and any skill that generates an asset adds lines to it. To avoid conflicts in parallel, each subagent writes its lines in its own wave report and the producer consolidates them into ASSETS.md at the end of the wave.

## Asset registry

Every generation (Runway or script) produces:

1. The downloaded file at the owner's path.
2. `art/_prompts/<asset_id>.md` with the full prompt, model, ratio, refs used (task ids), result task id, cost.
3. A line in the wave report, later consolidated into `production/ASSETS.md`:

```markdown
| asset_id | type | file | model | task_id | refs | credits | status | wave |
```

Status: `draft`, `candidate`, `approved`, `rejected`, `replaced by <id>`. Only an `approved` asset goes into the game.

## Generation providers

| What | Provider | Cost |
|---|---|---|
| Concept, identity bases, portraits, scenery, key art, storyboard, UI, marketing | Runway | credits |
| Sprite pose strips, isolated props with alpha | Codex through sprite-gen (`--provider codex`) | ChatGPT subscription (quota, no credits) |
| Video only to extract sprite locomotion cycles (the game has no video) | Runway | credits (expensive) |
| Music, SFX, voice | Runway | credits |

Codex generation does not go into BUDGET.md, but it is logged in `_prompts` and ASSETS.md with `model: codex`.

## Runway budget

- Before dispatching a wave that generates art, video or audio, the producer estimates credits per task (using the costs given in the Runway tool descriptions and the BUDGET.md history) and shows them to the user.
- A wave estimated above 300 credits, or any batch video generation, needs explicit user approval. Show the cost per group when the wave has groups and let the user approve per group.
- Current balance: the Runway `whoami` tool (credits field; `mcp__claude_ai_Runaway__whoami` when connected through claude.ai). Record it in BUDGET.md before and after each wave.

## Wave consolidation (end of every wave)

1. Read all `production/waves/NN-*.md` reports.
2. Consolidate assets into ASSETS.md and credits into BUDGET.md.
3. Resolve requests between skills: they become tasks of the next wave or of an adjustment mini-wave.
4. Run gf-continuity when the wave touched the Bible or closed a chapter.
5. Update STATE.md and BIBLE.md.
6. Present to the user: what was done (with absolute paths of images to open, as clickable `file://` links with short labels), open questions and, if it is a gate, the approval question. Use AskUserQuestion for choices between options.

## New game

`/game-factory:game-factory new <name>` (without the plugin, the user asks in plain words, for example "start a new game called <name> with the game factory", and you follow the same steps): creates the structure above, **preserving what already exists** (DECISIONS.md and references in `art/_refs/` registered before W0 become input for the W1 interview), a STATE.md with all gates pending, a `.gitignore`, `git init`, and starts with W0. The production files start from the plugin templates (two levels up from this skill's base directory, in `templates/`; when the skills were installed without the plugin, use `plugins/game-factory/templates/` from the clone made by gf-setup): copy `STATE.md`, `DECISIONS.md`, `BUDGET.md`, `ASSETS.md` and `SESSION_HANDOFF.md` into `production/` unless they already exist. `wave-plan.md` is the shape of every `production/waves/NN-<name>.md`, and `codex-brief.md` is the shape of every Codex batch brief.

`.gitignore` must include:

```text
tools/sprite-gen/
builds/
game/.godot/
*.apk
*.aab
*.ipa
# generator raw outputs
art/characters/**/runs/**/raw/
*_raw.png
audio/raw/
```

Do not ignore the whole `tools/` folder: `tools/gf`, `tools/codex` and `tools/playtest` must be versioned with the game.

## Tools (tools/gf)

Mechanical work is done by the CLI `tools/gf/gf.sh` (see tools/gf/README.md), never by a new script written on the spot:
- Subagent context pack: `gf context <role> --seq/--chars/--locs`, pasted into the prompt.
- Registry: the agent writes `production/waves/<wave>.assets.jsonl`; the producer runs `gf assets add` and `gf assets check`. Budget and state: `gf budget`, `gf state`.
- Before any LLM continuity review: `gf check --scope <scope>`. The continuity agent receives only the check output and the diff since the last review.
- A new script only if no command covers the case; in that case, ask for an extension of tools/gf instead of leaving a loose script in art/_prompts.
