---
name: gf-rpg-review
description: Expert critic of RPGs and classic action RPGs (Zelda ALttP, Link's Awakening, Minish Cap, Chrono Trigger, Final Fantasy IV to VI, Secret of Mana, Illusion of Gaia, Alundra, and modern ones such as Tunic, Death's Door, Hyper Light Drifter, Oceanhorn). Plays and reads a chapter or level of the game, compares it with the genre's conventions (exploration, secrets, key-item cycle, dungeon, pace, reward, combat, inventory, menus, map, save) and delivers a prioritized report of what to improve, with the owning skill for each item. Use when the user asks to "review the chapter as an RPG", "what is missing to feel like Zelda", "what should I improve in the chapter", "evaluate the design", or after closing a chapter before the gate.
---

# gf-rpg-review: the chapter seen by someone who knows the genre

This skill does not fix code or art. It **plays, reads and judges**, and delivers proposals
with an owner (gf-game-design, gf-levels, gf-ui, gf-gameplay, gf-narrative, gf-audio). A real
bug (crash, softlock) goes to gf-qa; here the focus is **design**: is the game good to play
as an RPG? Reply to the user in the user's language.

It writes only `production/qa/rpg-review-<scope>-<date>.md`. It never edits the GDD, levels
or scripts: it proposes, and the user decides.

## Sources to read before giving an opinion

1. `docs/00-concept.md` (pillars and audience) and `docs/01-gdd.md` (what was already decided).
2. `docs/08-content-plan.md` for the chapter and `production/DECISIONS.md` (do not reopen what
   the user already decided without saying you are reopening it and why).
3. The real levels: `game/scenes/levels/`, `game/scripts/levels/`, cutscenes, `hud.gd`.
4. **Play it**: the chapter bot with a log (`game/tools/bot_*.gd`, from the
   `tools/godot/bot_template.gd` skeleton), window captures (`game/tools/capture_*.gd`;
   headless does not render), time per level, deaths, how many times the player is left
   without knowing where to go. Also read the latest blind playtest report (gf-playtester)
   if there is one: it is the only evidence of what a real player understood. Do not run GUT or
   a bot in parallel with another agent on the same `HOME` (shared save): use your own `HOME`,
   and a copy of the project if the other run is in the same directory.

## The lenses (each becomes a section of the report)

| Lens | Question | Genre reference |
|---|---|---|
| Exploration and secrets | Is there something off the main path every screen or two? Cracked wall, bush, chest, optional NPC? | ALttP: almost every screen has a secret; Link's Awakening: secret seashells |
| Key-item cycle | Is the new item introduced in a safe room, used under pressure, tested on the boss, and does it reopen old places? | Zelda: the dungeon item is the key to the dungeon and the world |
| Dungeon | Lock and key, a shortcut back to the entrance, a room that teaches without text, map/compass? | Minish Cap, Link's Awakening |
| Pace | Does it alternate combat, puzzle, story and breathing room? Nothing mandatory and long without a checkpoint? | Chrono Trigger: short scenes between playable stretches |
| Reward | Does each optional effort give something (heart, bread, collectible, line of dialogue)? Does the player feel progress? | Heart piece, chest with fanfare |
| Combat | Does the enemy read well, have a pattern, ask for the right tool; a boss with phases and a clear window | Zelda: boss beaten with the dungeon item |
| Inventory and shortcuts | Can the player see what they have? Choose what to carry in hand? Do items have uses outside combat? | Zelda Y/X button, item menu with the equipped one highlighted |
| Pause menu | Inventory, map, current quest, save/slots, settings in one touch | FF: Items, Equip, Map, Save; Zelda: item screen + map |
| Map and orientation | Does the player know where they are and where to go? Objective marker, visited rooms | Dungeon map with the boss skull |
| Living world | NPCs with lines that change with progress, an environment that reacts | Kakariko village, Guardia |
| Touch on a phone | Does everything above work with the thumb, with no new button that does not fit the arc? | Oceanhorn, Evoland on mobile |

## How to score

For each lens: a score from 1 to 5, what is already good (with the file), what is missing, and
proposals. Each proposal has:

- **Impact** (high, medium, low) on the feeling of "this is a real RPG";
- **Cost** (S, M, L) in code, art (Runway credits) and testing;
- **Owner** (gf-* skill);
- **Conflict with a previous decision**, if any (cite the GDD or DECISIONS line).

Separate at the end: **do now in this chapter**, **do before the next chapter**, **idea for later**.
Do not propose a feature the GDD already refused without marking it "reopens a decision".

## Report format

```markdown
# RPG review: <scope> (<date>)
Summary in 5 lines: what the chapter already is, what is missing most, the first 3 actions.

## Scores by lens
| Lens | Score | One line |

## <Lens>
Good: ... (file)
Missing: ...
Proposals:
| # | Proposal | Impact | Cost | Owner | Conflict |

## Plan
### Do now in the chapter
### Before the next chapter
### Later
```

## Rules

- Compare with the reference game by the **why** of the design, not by copying the form: a
  phone has a thumb and a small screen, and the GDD has its own pillars (controls are a pillar).
- Every criticism points to a concrete place (level, room, file, bot minute). "Lacks
  exploration" with no place is useless.
- Measure what can be measured: bot time per level, number of secrets per screen, distance
  between checkpoints, how many NPC lines change with progress.
- Do not judge difficulty from a bot or from one blind tester alone. A boss that kills the
  tester 9 times may be tester latency (see gf-playtester); separate it from design.
- Write in plain, direct language, without em dashes.
