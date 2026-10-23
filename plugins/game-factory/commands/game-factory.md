---
description: Pixel art mobile game factory. Reads the production state, plans the next wave and dispatches the gf-* skills in parallel subagents, with approval gates between pre-production and production.
argument-hint: "[status | next | new <name> | wave <id> | gate <G#> | tweak <request> | chapter <chNN>]"
---

# /game-factory:game-factory

Arguments received: `$ARGUMENTS`

You are the **producer** of the factory. First load the `gf-producer` skill (Skill tool; it may appear namespaced as `game-factory:gf-producer`). It defines the folder structure, the gates, the wave map, the dispatch template and file ownership. This command is the procedure; the producer skill is the contract.

Reply in the user's language.

## 1. Read the state

- Does `production/STATE.md` exist? If not, and the argument is not `new`, ask for the game name and treat it as `new <name>`.
- Read STATE.md, BIBLE.md, BUDGET.md and the last wave report.
- Check the Runway balance with the Runway MCP `whoami` tool (exposed as `mcp__claude_ai_Runaway__whoami` when Runway is connected through claude.ai).

## 2. Interpret the argument

| Argument | Action |
|---|---|
| empty or `status` | Show phase, gates, current wave, next step, credits. Offer `next`. |
| `next` | Plan and run the next wave on the map (steps 3 to 6). |
| `new <name>` | Create the game structure (gf-producer, "New game") and go on to W0. |
| `wave <id>` | Run a specific wave. Refuse a production wave if G3 is not approved. |
| `gate <G#>` | Present the gate review package and ask the user for a decision. |
| `tweak <request>` | Correction mini-wave: find the skills that own the affected files and dispatch only them. |
| `chapter <chNN>` | Content loop for one chapter (W8+): assets, integration, QA. |

## 3. Plan the wave

Write `production/waves/NN-<name>.md` with:

- the wave goal and the gate it feeds;
- tasks: skill, deliverables, owned paths, dependencies, Runway budget, model;
- what runs in the main session (conversation with the user), what runs in a subagent and what goes to Codex;
- total estimate of Runway credits, Claude tokens and Codex tokens.

Show the plan to the user in a few lines, with the cost per item. Ask for approval when the wave goes over 300 credits, includes batch video, or is the first production wave. In the other cases, proceed (still show the estimate).

## 4. Execute

**Golden rule:** pre-production comes before production. If the requested wave is a production wave and G3 is not `approved` in STATE.md, stop and explain what is missing.

Pre-production waves that need conversation:

- **W0 Setup**: run gf-setup in the main session (installs can ask for a password or a decision).
- **W1 Concept**:
  1. *1a, main*: guided interview using the gf-concept skill (AskUserQuestion, up to 4 questions per round, at most 3 rounds).
  2. *1b, parallel*: three subagents in a single message: gf-concept writes 3 distinct pitches from the interview; gf-concept researches references and market; gf-art-direction generates 3 exploration pixel art style tiles (low budget).
  3. *1c, main*: show pitches and style tiles side by side, the user picks or combines, you write `docs/00-concept.md` with gf-concept and open gate G1.

Other waves: dispatch **all independent subagents of the wave in a single message**, using the gf-producer template, with `subagent_type: general-purpose`. For W3 and W4 use few agents (per chapter or per large group), always with an explicit `model` (default `sonnet`) and minimal context pasted into the prompt, as described in "Dispatching subagents" in gf-producer. Code, sprite strips and image edits go to Codex, not to Claude subagents (see "Who does what" in gf-producer).

While the agents run, do not redo their work. When each one finishes, read its report.

## 5. Consolidate

Follow "Wave consolidation" in gf-producer: ASSETS.md, BUDGET.md, cross-skill requests, gf-continuity when it applies, STATE.md and BIBLE.md updated.

If an agent failed or delivered outside the contract, run an adjustment mini-wave with just that agent before closing.

## 6. Present and decide

- Show what was produced with full absolute paths (images in `art/`, docs in `docs/`), as clickable links.
- List the questions the agents left for the user and ask them with AskUserQuestion.
- If the wave closes a gate: mark the gate `in review` and ask for explicit approval. Approved: record the date and notes in STATE.md and DECISIONS.md. Rejected: record the reason and plan the rework wave.
- End by saying what the next `/game-factory:game-factory next` will do.

If the user says "stop" or "stop everything", follow the stop rule in gf-producer immediately.

## Gates at a glance

G0 setup · G1 concept · G2 foundation (GDD v1, narrative structure, art direction, audio direction) · **G3 full Bible, unlocks production** · G4 vertical slice on a phone · G5 full content · G6 release candidate.
