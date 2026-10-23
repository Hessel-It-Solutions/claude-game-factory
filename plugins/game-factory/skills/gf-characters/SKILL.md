---
name: gf-characters
description: "Character creation for the game: character sheet (bible) with personality, arc, silhouette, palette and lists of animations and expressions; concept art, turnaround and the pixel art identity base image made in Runway, which becomes the anchor of all sprites. Use in W3 of /game-factory (one agent per group of characters), or when the user asks to create, redesign or detail a character, enemy, boss or NPC, \"design the hero\", \"make the character sheet\"."
---

# gf-characters: cast

> **Detail coherence guardrail:** all content follows the same art standard; no character less detailed than the scenery, and no scenery more detailed than the characters. Detail is volume (light and shadow in masses, continuous outline on actors, desaturated storyboard color), not loose pixels. Character and animal bases are cut out of the storyboard art; the AI only completes directions and animations, anchored on the cutout. Before delivering: a coherence board with the asset at game size over the real scenery, next to the approved reference character and the storyboard cutout. Full rule in `docs/02-art-direction.md` section 0.1.

Inputs: `docs/05-script/outline.md` (cast and arcs), `docs/01-gdd.md` (mechanics and enemies), `docs/02-art-direction.md` (scale, palette, prompt blocks). Load `gf-runway` before generating.

## Sheet: `docs/03-characters/<chr_id>.md`

```markdown
# <Name> (<chr_id>)
Role: protagonist | ally | antagonist | enemy | boss | NPC
Chapters: ch01, ch02

## Essence (1 sentence)
## Personality and voice (3 traits, how they speak, catchphrase if any)
## Arc
## Appearance
   age, build, proportion (heads tall), hair, clothes, accessories, weapon
   silhouette: what makes them recognizable at 64px (must read in flat black)
## Palette (master palette colors used, per region)
## Variations (ages, outfits per chapter) with ids: chr_hero_young, chr_hero_king
## Animations (for gf-sprites)
   state | directions | suggested frames | loop | fps | note
   idle | down, side, up | 4 | yes | 6 | breathing, sling swaying
   sling_aim | side (side scenes only) | 4 | no | 8 | ...
## Portrait expressions (for dialogue)
   neutral, determined, afraid, ... (taken from the script: emotions used in the lines)
## Audio (for gf-audio): footsteps, grunts, voice
## Images
   concept, turnaround, base, portraits (paths)
```

## Images (Runway)

Order, each step logged in `art/_prompts/`:

1. **Concept** (`art/characters/<chr_id>/concept/`): 2 to 4 variations (`count`), freer and more illustrated style, to decide the design. With `@style`.
2. **Choice**: the agent picks the best by the sheet and the silhouette rule, but leaves the others as `candidate` and notes it in the report for the user to confirm at the gate.
3. **Turnaround** (`concept/turnaround.png`): front, side, back in the same image, same height, chroma background. Reference: the chosen concept.
4. **Identity base** (`art/characters/<chr_id>/base/base.png`): idle pose, full body, **front-facing (down) in a top-down game** or side view in a side-scroller; in a hybrid camera, front-facing (the side view comes out as the `side_idle` anchor in gf-sprites), feet visible, chroma background, at the game's **logical resolution**. This image is the identity contract for sprite-gen: it needs a measurable pixel grid. Run it through `pixelize.py --height <cell height>` with the palette and check the 4x preview.
   - When a storyboard exists, the base is **cut out of the approved storyboard frame** (hand mask; majority-vote reduction only if the frame scale differs from the game scale). Do not ask the AI (Runway or Codex) to redraw the character: it comes back with a small head and detail turning into noise. The AI only completes what the frame does not show (other directions, animations), always anchored on the cutout. A secondary character generated without the storyboard cutout inherits the colors of the protagonist.
5. **Portraits** (`concept/portraits.png`): sheet with the expressions in a grid (for example 3x2), chroma background, for `$SG slice-sheet` in production.

Characters of the same group (family, army) come out with each other's bases as extra references, to keep proportion coherent. Family proportion rule: the same head-to-body ratio for all humans of the group.

## Rules

- Reading at real size: show the base at 1x and 4x. If the character cannot be recognized at 1x, simplify.
- Common enemies: economical design (few states, colors that contrast with the scenery where they appear).
- Bosses: large silhouette, attack telegraphed in the design (the arm that will strike is visible).
- Historical or religious character: research period clothing and objects, record the sources in the sheet and avoid stereotypes.

## Done criteria

Complete sheet, base approved by the agent with a 4x preview, list of animations and expressions that matches the GDD and the script.

## Tools

Cutting portrait sheets: `tools/gf/gf.sh cut <sheet> --auto --names ... --post`. Post-processing and palette: `tools/gf/gf.sh post` and `tools/gf/gf.sh validate`. Codex batch of concept/turnaround: `tools/gf/gf.sh codex jobs.json`. Do not write cutting, cleaning or validation scripts.
