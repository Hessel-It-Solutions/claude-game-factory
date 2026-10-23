---
name: gf-sprites
description: "Animated pixel art sprite production with sprite-gen (github.com/aldegad/sprite-gen) + Codex + Runway. Generates pose strips through the sprite-gen codex provider (ChatGPT subscription) and locomotion videos in Runway from the character's identity base, extracts with chroma and pixel unfake, assembles the atlas, curates, exports Aseprite JSON and delivers into the Godot project. Also makes dialogue portraits and effects. Use from W5 on for characters, enemies, NPCs, bosses and effects, or when the user asks to \"animate the character\", \"make the sprite\", \"make the attack sprite\", \"redo the walk\"."
---

# gf-sprites: animated characters

Produces animated pixel art sprites. It generates pose strips with sprite-gen and Codex (or extracts cycles from Runway video), cleans them with chroma removal and pixel unfake, rescales them consistently, builds the atlas and delivers it to Godot. It also makes dialogue portraits and effects. Part of the [game factory](https://github.com/Hessel-It-Solutions/claude-game-factory), a set of skills that make pixel-art mobile games with Godot 4.

## When to use

- Animating a character, enemy, NPC or boss
- Redoing a walk, attack or idle cycle
- Making dialogue portraits or effect sprites

Produces: `art/characters/<chr_id>/runs/` and atlases in `game/assets/sprites/`.

Works with: gf-characters, gf-runway, gf-gameplay.

---

> **Detail coherence guardrail:** all content follows the same art standard; no character less detailed than the scenery, no scenery more detailed than the characters. Detail is volume (light and shadow in masses, continuous outline on actors, desaturated color from the storyboard), not loose pixels. Character and animal bases are cut out of the storyboard art; the AI only completes directions and animations, anchored on the cutout. Before delivering: a coherence board with the asset at game scale over the real scenery, next to the approved main character and the storyboard cutout. Full rule in `docs/02-art-direction.md` section 0.1.

Prerequisites: G3 approved (except the art direction sprite test, marked draft), approved `art/characters/<chr_id>/base/base.png`, states in the character sheet `docs/03-characters/<chr_id>.md`, scale and palette in `docs/02-art-direction.md`. Read `gf-runway`. Variables: `SG=$SPRITE_GEN_ROOT/.venv/bin/sprite-gen`, `PY=$SPRITE_GEN_ROOT/.venv/bin/python`, `PIX=tools/gf/pixelize.py`.

The sprite-gen docs are in `$SPRITE_GEN_ROOT/docs/` (start with `atlas-workflow.md`, `pixel-unfake.md`, `video-pipeline.md`, `run-contract.md`). When in doubt about a flag, `$SG <command> --help` wins.

## Route split

| State | Route | Why |
|---|---|---|
| idle, attack, jump, hurt, death, cast, talk, interact, effects | **A: pose strip (`gen-set --provider codex`)** | short readable poses, native and stable sprite-gen route, zero Runway cost |
| walk, run, flight, cyclic motion with cape/hair | **B: Runway video then loop** | cyclic locomotion by strip is experimental in sprite-gen |

When in doubt, start with route A (cheap); if the motion QA fails, redo with B.

Who does what: the **identity base** comes from the approved storyboard art (cut out, see gf-characters; Runway only completes what the frame does not show); **pose strips** come from Codex via sprite-gen; the **locomotion video** comes from Runway. Route A' (strip in Runway) is the fallback when Codex fails or the quota runs out.

## Route A: pose strip

```bash
RUN=art/characters/<chr_id>/runs/<chr_id>_a_v1
$SG prepare --out-dir $RUN --character-id <chr_id> \
  --base-image art/characters/<chr_id>/base/base.png \
  --description "<character description: age, clothes, hair, props>" \
  --cell-width <W> --cell-height <H> --chroma-key "#FF00FF" --safe-margin 2 \
  --fit-pixel-unfake --fit-palette-size <N> --fit-align-x foot-centroid --fit-align-y bottom \
  --request-json '{"states":{"idle":{"frames":4,"fps":6,"loop":true,"action":"subtle breathing, one blink"},"attack":{"frames":5,"fps":10,"loop":false,"action":"..."}}}'
```

- `<W>x<H>` and `<N>` come from the art direction. Omitted `logical_height` = 1:1 with the cell (recommended); use `--fit-logical-height` only with an integer divisor of H.
- States, frames, fps and loop come from the character sheet.
- Describe the character with `--description`: the `character` field inside `--request-json` is ignored.
- `--request <file>` takes a file; `--request-json` takes the JSON text.
- `--safe-margin 2`: the default (about 9.4% of the cell) crops a character that fills 75 of 80 px.
- Make the base 8x on magenta with some slack around it, otherwise Codex redraws the character.

Generate all strips through Codex:

```bash
$SG gen-set --run-dir $RUN --provider codex          # all states, 6 in parallel, to raw/<state>.png
$SG gen-set --run-dir $RUN --provider codex --force  # regenerate (or delete raw/<state>.png of the bad state and run without --force)
```

- Always pass `--provider codex`: without it sprite-gen may fall back to another provider you do not have.
- Reports in `$RUN/reports/gen-set/<state>.json` and `table.md`. A failed row = check `codex login status` and quota; if it persists, use route A'.
- sprite-gen calls Codex internally, so it does not run inside a `codex exec` sandbox. Run `gen-set` straight from the terminal (main session).
- Log each state in `art/_prompts/spr_<chr_id>_<state>_vN.md` with `provider: codex` (prompt = `$RUN/prompts/<state>.txt`, Runway credits: 0).
- A new strip for an existing character starts only from the anchor of the base: copy the approved run, `prepare --chroma-key '#FF00FF'` in a temporary directory, then `gen-set --states X`.

### Route A' (fallback): strip in Runway

Same prepared run; for each state:

1. Upload the base, the style tile and the guide `$RUN/references/layout-guides/<state>.png` with `init_upload`, `curl`, `complete_upload` (the base is uploaded once per session and the URL is reused).
2. `generate_image` with the official character model, `referenceImages` = `@base`, `@style`, `@guide`, prompt = the content of `$RUN/prompts/<state>.txt` followed by:
   `@base is the identity reference: same character, same pixel density, same palette. @guide shows slot count and placement: draw exactly <frames> poses in one horizontal row, evenly spaced, same scale, feet on one baseline. Do not draw the guide lines, numbers or boxes. Flat solid #FF00FF background.`
   Ratio: as wide as the model accepts (21:9 or 16:9). The extractor separates poses by connected component, not by fixed slices.
3. Download to `$RUN/raw/<state>.png`. Generate `count: 2` when the state is critical; the second goes to `$RUN/raw/<state>.takes/b.png`.
4. Log in `art/_prompts/spr_<chr_id>_<state>_vN.md`.

Then (A or A'):

```bash
$SG extract --run-dir $RUN            # chroma + pixel unfake to frames/<state>/frame-N.png
$SG inspect --run-dir $RUN            # frame count, identity, motion defects
$SG preview --run-dir $RUN            # GIFs and contact sheet for QA
```

**After extract, always:**

- **Palette**: pixel unfake creates the run's own palette, outside `docs/palette.hex`. Remap every frame: `$PY $PIX frame.png frame.png --pitch 1 --palette docs/palette.hex` (keeps the grid, locks the colors).
- **Grid and height**: each strip can come on a different grid and the character can vary a few px in height between states. Use `--fit-pitch-hint` with the pitch measured on the base and check the height on the contact sheet; a strip out of range (more than 4 px difference) is regenerated.
- **Fixed scales**: each raw strip has the character at its own size. Set `fit.fixed_scales` per state (measured on the raw) and check the head on a board. For fauna and effects, measure the body length in profile and the height in front/back views.
- **Raw strip at the wrong size or touching the top of the cell** (extract refuses it): `$PY tools/gf/strip_rescale.py raw.png out.png --frames N --height H [--cell 80] [--cell-w 112] [--foot 78] [--ref-frame K]` cuts the strip into frames by empty columns and rescales all of them with one factor, measuring the body without thin props (staff, sling) by erosion. For action cells, use `--cell-w`/`--foot` to match the atlas and `--ref-frame` on the standing frame when blending.

`extract-failure.json` in the run = regenerate that state (pose glued to another, extra arm, cropped pose). Do not fix a bad drawing by cropping: generate again.

## Top-down games (4 directions)

For a 3/4 top-down camera, the run is directional. The base is the character **facing the camera (down)**; sprite-gen first generates one idle per direction (which becomes the identity anchor of that direction) and then the actions of each direction from the anchor. Left is a mirror of right at runtime.

`prepare` does not expose `--directions`/`--mirror`: pass directions inside `--request-json`.

```bash
$SG prepare --out-dir $RUN --character-id <chr_id> --base-image art/characters/<chr_id>/base/base.png \
  --description "<description>" --cell-width <W> --cell-height <H> --chroma-key "#FF00FF" \
  --fit-pixel-unfake --fit-palette-size <N> --fit-align-x foot-centroid --fit-align-y bottom \
  --fit-pitch-hint <pitch measured on the base> \
  --request-json '{"directions":{"set":["down","side","up"],"mirror":{"left":"side"}},
                   "states":{"down_idle":{...},"side_idle":{...},"up_idle":{...},"side_walk":{...},"down_attack":{...}}}'
# 1. anchors first, and extracted, otherwise gen-set of the actions fails with "generate and extract the anchor row ... first"
$SG gen-set --run-dir $RUN --provider codex --states down_idle,side_idle,up_idle
$SG extract --run-dir $RUN --states down_idle,side_idle,up_idle
#    review the 3 anchors here (side_idle tends to come out 3/4: ask for "strict side profile" and regenerate)
# 2. actions
$SG gen-set --run-dir $RUN --provider codex
$SG extract --run-dir $RUN
```

`preview` and `inspect` need all anchors of the request extracted.

- States are always `<direction>_<state>`; the generation order is in `$RUN/references/generation-plan.json`.
- Review the 3 anchors (`down_idle`, `side_idle`, `up_idle`) **before** generating actions: a wrong anchor contaminates every action of that direction. Details and gates: `$SPRITE_GEN_ROOT/docs/directional-anchor-workflow.md`.
- `walk` by direction is cyclic locomotion (experimental as a strip): try route A and, if QA fails, use route B per direction.
- In Godot the animations are `down_walk`, `side_walk`, `up_walk`; the actor picks by dominant direction and applies `flip_h` for left.

### Anchor handling

- `gen-set` rebuilds each direction's anchor from `frames/<dir>/idle/frame-0.png` x8 on every round (overwriting what is in `references/anchors`) and may regenerate the `<dir>_idle` row on its own.
- A noisy anchor frame (bad extraction) turns into a "camouflaged" creature in every action. Put the clean strip, reduced by majority color vote, in the idle frames, in the cell, and run `anchor --all` before `gen-set`.
- A row with more frames in the request than in the manifest breaks `gen-set`; the anchor `side_idle` keeps 1 frame. Placeholders in `raw/` and rows in `frames-manifest.json` for states not generated also break it ("corrupt frames manifest").
- A profile anchor cut from a storyboard in a gesture pose (pointing, for example) contaminates walk and idle: ask for an upright posture in the text, or use another pose as the idle. A front view derived from the profile can change age and clothes: describe them in the text (adult, beard, single tunic).
- Never base an effect run on the style tile (it draws the main character); use a neutral base.

### Side scenes (hybrid camera)

A game that alternates top-down with side scenes reuses the `side_*` states in the side scenes. States that only exist in the side view (for example `side_aim`, `side_fall`) go in the same run with the `side_` prefix. Same scale in both modes: never resample a sprite to "zoom", it breaks the grid. For a dramatic close-up, use a portrait or a full-screen illustration (gf-cutscenes).

## Route B: video to loop

```bash
V=art/characters/<chr_id>/runs/<chr_id>_video/<state>
$SG video-canvas --still art/characters/<chr_id>/base/base.png --out $V/canvas.png --state <state> --facing right --key magenta
```

1. Upload `$V/canvas.png` and call `generate_video` with `startFrame` = canvas. Motion-only prompt: `<character> <walking|running> in place, side view, seamless treadmill cycle, camera locked, no zoom, no cut, character stays centered, background stays flat solid magenta, keep the exact pixel art look of the first frame`. Start model `seedance-2`, shortest supported duration. **Video is expensive: it needs the producer/user approval.**
2. Download to `$V/clip.mp4`.

```bash
$SG video-frames --clip $V/clip.mp4 --out-dir $V --key magenta --reference $V/canvas.png
$SG video-loop --frames-dir $V/keyed --out-dir $V/loop --state <state> --name <state> --anchor feet
```

3. The cycle frames (`$V/loop/cycle/`) are still "AI pixel art". Run each through `pixelize.py --height <H> --palette docs/palette.hex` (same H as the cell, to match route A) and reduce to the frame count of the sheet by picking evenly spaced frames.

## Final assembly (A + B in one atlas)

```text
art/characters/<chr_id>/runs/<chr_id>_final/pngs/
  _base/base.png
  idle/1-idle.png 2-idle.png ...        <- copied from $RUN/frames/idle/frame-N.png
  walk/1-walk.png ...                   <- from route B, already pixelized
  meta.json                             <- optional
```

```bash
F=art/characters/<chr_id>/runs/<chr_id>_final
$SG unpack-atlas --pngs-dir $F/pngs --out-dir $F/run --force
$SG curation --run-dir $F/run --lang en      # optional: webview for the user to pick/adjust frames
$SG compose-atlas --run-dir $F/run
$SG export-aseprite --run-dir $F/run          # exports/aseprite.json (frameTags per state)
```

If there is only route A, skip `pngs/` and run `compose-atlas`/`export-aseprite` straight on `$RUN`.

### Config-driven atlas build

For core characters whose atlas is built from several runs (one animation per row, fixed columns, a cell size and a foot row per character, an idle assembled at build time), keep a JSON config in the game repo and run:

```bash
$PY tools/gf/build_sprite_atlas.py <atlas_config.json>
```

The tool reads the strips from `art/`, builds each atlas and writes the PNG plus a JSON in the format of the game's `SpriteFramesLoader`. See the docstring of the tool for the config fields. Rules it relies on:

- One animation per row, so a neighbor is never corrupted. Never insert a new strip by sequential index into an existing atlas (it corrupted neighboring animations once); rebuild from the config.
- Chroma removal is by hue (about 285 to 330 degrees, saturation above 0.6): remapping leaves near-pure magenta and a dark fringe that exact-color equality does not catch.

## Delivery to Godot

```text
game/assets/sprites/<chr_id>/<chr_id>.png        <- sprite-sheet-alpha.png
game/assets/sprites/<chr_id>/<chr_id>.json       <- exports/aseprite.json (meta.image adjusted to <chr_id>.png)
game/assets/sprites/<chr_id>/anim.json           <- {"idle":{"fps":6,"loop":true}, ...} from the sheet
```

The gf-godot-core importer turns this into `SpriteFrames` (`<chr_id>.tres`). Do not create SpriteFrames by hand.

- Centered sprite position: `y = cell_height / 2 - foot_row`. A wrong integration put the sprite far too high and left the feet floating above the collision.
- Never scale a character by a fractional factor in the scene (for example 0.8): it blurs the pixel grid. Resize in the art pipeline to an integer scale, and check that the on-screen height matches the storyboard height.

## Dialogue portraits

Expression sheet generated by gf-characters (`concept/portraits.png`, or generate a new one with the base as `@base`), then:

```bash
$SG slice-sheet --sheet portraits.png --out-dir art/characters/<chr_id>/portraits --chroma-key magenta \
  --grid 3x2 --names neutral,happy,sad,angry,afraid,determined --prefix <chr_id>_
```

Pixelize each portrait at the portrait height from the art direction.

### Animated portrait (the dialogue "GIF")

Each expression becomes two short looping animations, generated by Codex in a portrait run (Runway cost zero):

```bash
P=art/characters/<chr_id>/runs/<chr_id>_portraits_v1
$SG prepare --out-dir $P --character-id <chr_id>_portrait --base-image art/characters/<chr_id>/portraits/<chr_id>_neutral.png \
  --cell-width <PW> --cell-height <PH> --chroma-key "#FF00FF" --fit-pixel-unfake --fit-palette-size <N> --fit-align-y bottom \
  --request-json '{"states":{
    "neutral_idle":{"frames":4,"fps":4,"loop":true,"action":"same pose and framing, only one slow eye blink, nothing else moves"},
    "neutral_talk":{"frames":3,"fps":8,"loop":true,"action":"same pose and framing, mouth closed, half open, open, as if speaking"},
    "afraid_idle":{"frames":4,"fps":4,"loop":true,"action":"afraid expression, same framing, one blink"}, "afraid_talk":{...}}}'
$SG gen-set --run-dir $P --provider codex
$SG extract --run-dir $P && $SG preview --run-dir $P && $SG compose-atlas --run-dir $P && $SG export-aseprite --run-dir $P
```

- Identical framing and background in all frames: only eyes and mouth change. A frame with the head moving = regenerate the state.
- Delivery like a sprite: `game/assets/portraits/<chr_id>/<chr_id>_portrait.png` + `.json` + `anim.json`. The dialogue box plays `<emotion>_talk` while the text runs and `<emotion>_idle` afterwards.
- If QA fails an expression animation, deliver frame 1 static; a dialogue with a static portrait is acceptable, a jittery portrait is not.
- Check the PNG/JSON that the game actually loads, not loose files: a review board built from loose files once approved portraits while the game sheet lacked the expressions.

## Effects (hit, dust, magic)

Route A with `prepare --subject effect`, chroma background, no character base (use `@style` and a palette color). Delivery in `game/assets/sprites/fx/<fx_id>/`.

## Color variations

Repeated enemies and skins: `$SG recolor-palette` and `$SG recolor --spec` generate variants without a new generation (see `docs/recolor.md` in sprite-gen). Cheaper and more consistent than asking Runway for another image.

## Gotchas

- Always `--provider codex`; always run `gen-set` from the terminal, never inside a Codex sandbox.
- `fixed_scales` per state, measured on the raw strip; check the head height on a board. Size drift between states of 4 px or more is a regeneration.
- Anchors: see "Anchor handling". Clean the idle frames and run `anchor --all` before every `gen-set`.
- Cutting a base from storyboard art: do not ask any AI to redraw the character (it comes back with a small head and detail turned into noise). Cut it out (SAM background removal in gf-runway, then close holes, keep the largest component, reduce by majority color vote only when the frame scale is not the game scale). Use AI only to complete directions and animations anchored on the cutout.
- A secondary character generated without its own cutout inherits the main character's colors.
- Pose strips from Codex are not trusted until measured: Codex has handed back "done" assets that were an old capture copied from a cache folder. Check the files yourself.

## QA before delivering

- GIF of each state reviewed at real size and at 4x; feet do not slide (idle, attack); loop without a jump (walk, run).
- All colors inside `docs/palette.hex`.
- Same character size across states (pixel unfake + foot-centroid guarantee it; check anyway).
- Side-by-side board at game scale against the storyboard frame and the main character.
- Asset stays `candidate` until the user or the gate approves; only then `approved` and copied to `game/`.
