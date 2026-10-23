# gf

Game factory CLI. It takes the mechanical, repetitive work off the LLM: image post-processing,
sheet cutting, boards, Codex image batches, the asset registry, continuity checks and the
context pack. The executable shortcut is `tools/gf/gf.sh`; the canonical form is
`PYTHONPATH=tools/gf python -m gf`. `gf.sh` uses `tools/sprite-gen/.venv/bin/python` when it
exists and falls back to `python3` (which needs Pillow and numpy).

The repo root is found by walking up to the first directory with `production/STATE.md`.
Exit codes: 0 no problems, 1 problems found, 2 usage error. `--json` is available on every
command that reports something.

```sh
tools/gf/gf.sh post in.png out.png --width 640 --chroma magenta
tools/gf/gf.sh validate art/characters/chr_hero
tools/gf/gf.sh cut sheet.png --grid 3x2 --names neutral,afraid,determined,calm,hurt,tired cells/
tools/gf/gf.sh board art/storyboard/seq_01_fields --labels
tools/gf/gf.sh codex jobs.json --parallel 4 --dry-run
tools/gf/gf.sh assets add production/waves/04.assets.jsonl
tools/gf/gf.sh assets check
tools/gf/gf.sh budget W5 2873 2800 --cap 100 --notes "test"
tools/gf/gf.sh state "Current wave" "W5"
tools/gf/gf.sh check --scope pilot
tools/gf/gf.sh context storyboard --seq seq_01_fields
```

`post` and `validate` use the master palette (`docs/palette.hex`) and the majority-vote logic of
`tools/gf/pixelize.py`, which also runs on its own (see the gf-runway skill). To use another
copy, set "pixelizer" in `gf.json`. `codex --dry-run` never
calls Codex. `assets add`, `budget` and `state` change production files and write a `.bak`
backup when they append to or rewrite a table. No command deletes files.

## Production file contract

The CLI parses these headings and columns. They are defined once, in `gf/schema.py`; the producer
skill and the templates must match them.

| File | What the CLI reads or writes |
|---|---|
| `production/STATE.md` | Lines `Current wave: <value>` and `Next step: <value>` (`gf state`). |
| `production/ASSETS.md` | One table with the columns `asset_id`, `type`, `file`, `model`, `task_id`, `refs`, `credits`, `status`, `wave`, in this order. `gf assets add` takes JSONL with the same keys (`refs` may be omitted). Rows whose status or file contains `planned`, `pending`, `rejected`, `to generate`, `do not generate` or `no generation` skip the file-exists check. A `file` cell may use `{a,b}` braces, globs and ranges written `x.png to y.png`. |
| `production/BUDGET.md` | `gf budget` appends `\| <wave> \| <balance before> \| up to <cap> \| <spent> \| <balance after> \| <notes> \|`. |
| `production/DECISIONS.md`, `docs/08-content-plan.md`, `docs/05-script/ch*.md` | Read by `gf context`. |
| `docs/05-script/ch<NN>.md` | Dialogue lines `SPEAKER [optional note] (expression): text`; sequences declared as `## seq_<id>`. |
| `docs/05-script/expressions.md` | Table with the header `chr_id \| Expression \| Lines \| Description \| Cell`. A cell of `see sheet` sends the lookup to `docs/03-characters/<id>.md`. |
| `docs/03-characters/<id>.md`, `docs/04-world/<id>.md`, `docs/06-storyboard/<seq>.md` | Sheets and storyboards the ID checks look for. |

ID prefixes the continuity check knows: `chr_ npc_ en_ boss_ loc_ seq_ ill_ prop_ plx_ sb_`.

## Configuration: tools/gf/gf.json

- `speakers`: maps the SPEAKER label in dialogue to a character id (`{"HERO": "chr_hero_young"}`).
  Default is empty. Labels are also derived from `docs/03-characters/<id>.md`: `chr_hero_young.md`
  answers to `HERO` and `HERO YOUNG`. Entries in `speakers` win.
- `no_portrait`: character ids that speak without a portrait cell (crowds, extras).
- `scopes`: named scopes for `gf check --scope`, for example `{"pilot": "ch01,ch02"}`. A scope
  not found here is read as a comma list of script file names.
- `final_art`: include and exclude globs for the PNGs `check` validates against the palette.
- `assets`: exclude globs for `assets check` (raw, previews, boards, `_rejected`, `_refs`, `_legacy`).
- `pixelizer`: optional path to `pixelize.py`, relative to the repo root.

`--rules rules.json` (for `post` and `validate`) accepts per-region color rules
(`{"rules": [{"name": "...", "box": [x0, y0, x1, y1], "allowed": ["hex"], "forbidden": ["hex"]}]}`)
and optional cleanup keys for `post`: `remap` (global color replacement), `remap_from_y`
(`{"y": 25, "map": {...}}`, replacement below a row), `remap_regions` and `fringe_colors`
(dark chroma fringe removed next to transparency). No game-specific remap is built in.

## Outside the CLI

- `strip_rescale.py`: cuts a raw sprite-gen strip into frames by its empty columns and rescales all
  of them with one factor, measuring the body without thin props (by erosion) so it matches the
  anchor height. Cells are configurable (`--cell`, `--cell-w`, `--foot`, `--ref-frame`).
  `python tools/gf/strip_rescale.py raw.png out.png --frames 8 --height 75`
- `build_sprite_atlas.py atlas.json`: config-driven atlas builder (strips or frame folders to a
  runtime atlas plus Godot SpriteFrames-compatible JSON). Chroma is removed by hue (285 to 330
  degrees, saturation above 0.6), not by exact value. See `atlas.example.json`.
- `build_collision_polygons.gd`: `godot --headless --path game -s tools/gf/build_collision_polygons.gd -- <mask.png> <out.json> [epsilon] [min_area]`.

## Known limits

`check` validates mechanical relations. It does not read the meaning of continuity, the intent of a
line, the visual composition, or whether a sheet describes a character correctly. Those stay with
the LLM reviewers. `assets check` only flags an `.ogg` with a matching `.mp3` as `awaiting
conversion`; it does not validate audio.

## Tests

`cd tools/gf && python3 -m unittest discover -s tests` (Pillow and numpy required).
