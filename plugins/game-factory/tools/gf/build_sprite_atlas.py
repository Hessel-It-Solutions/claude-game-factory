#!/usr/bin/env python3
"""Config-driven sprite atlas builder.

Usage:
  python tools/gf/build_sprite_atlas.py atlas.json [--root DIR]

Reads animation strips (or directories of frame-N.png files) from art/, removes the
magenta chroma by hue, aligns every frame to a common foot line inside a fixed cell, and
writes a runtime atlas plus Aseprite-style JSON that a Godot SpriteFrames loader can read:

  <output_dir>/<name>.png    atlas, one row per animation, frames left to right
  <output_dir>/<name>.json   {"frames": [...], "meta": {"frameTags": [...]}}
  <output_dir>/anim.json     {"<animation>": {"fps": f, "loop": bool}}

The source art is only read. See atlas.example.json for the config format.

Config keys:
  name         atlas base name (file names and tag prefix source)
  output_dir   where the three files are written (relative to --root)
  cell         [width, height] of one atlas cell
  foot_y       row inside the cell where the lowest opaque pixel of each frame lands
  animations   list of:
    name       animation name, becomes the frame tag (for example "side_walk")
    source     PNG strip (frames side by side) or a directory with frame-N.png files
    frames     number of frames in the strip (required for a PNG strip)
    fps        playback speed
    loop       true or false
    align      "foot" (default: crop to the opaque box, center horizontally, put the
               lowest opaque row on foot_y) or "none" (paste the frame as is, top left)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

# Chroma by hue, not by exact value: palette remapping leaves near-pure magenta
# (250,3,250) and a darkened fringe (100,7,98). No color in a normal master palette is a
# saturated magenta, so a hue window is safe and catches the fringe too.
HUE_MIN, HUE_MAX = 285.0, 330.0
MIN_SATURATION = 0.6
MIN_VALUE = 0.3


def chroma_mask(rgb: np.ndarray) -> np.ndarray:
    """True where the pixel is magenta chroma (hue 285..330, saturation > 0.6)."""
    x = rgb.astype(np.float64) / 255.0
    r, g, b = x[..., 0], x[..., 1], x[..., 2]
    mx = x.max(axis=-1)
    mn = x.min(axis=-1)
    delta = mx - mn
    safe = np.where(delta == 0, 1.0, delta)
    hue = np.where(mx == r, ((g - b) / safe) % 6.0,
                   np.where(mx == g, (b - r) / safe + 2.0, (r - g) / safe + 4.0)) * 60.0
    hue = np.where(delta == 0, 0.0, hue)
    sat = np.where(mx == 0, 0.0, delta / np.where(mx == 0, 1.0, mx))
    return (HUE_MIN <= hue) & (hue <= HUE_MAX) & (sat > MIN_SATURATION) & (mx > MIN_VALUE)


def remove_chroma(im: Image.Image) -> Image.Image:
    arr = np.array(im.convert("RGBA"))
    arr[chroma_mask(arr[..., :3]) & (arr[..., 3] > 0), 3] = 0
    return Image.fromarray(arr, "RGBA")


def split_strip(path: Path, count: int) -> list[Image.Image]:
    strip = remove_chroma(Image.open(path))
    if count < 1 or strip.width % count:
        raise ValueError(f"{path}: width {strip.width} is not divisible by {count} frames")
    width = strip.width // count
    return [strip.crop((i * width, 0, (i + 1) * width, strip.height)) for i in range(count)]


def read_frames(path: Path, count: int | None) -> list[Image.Image]:
    if path.is_dir():
        files = sorted(
            (p for p in path.glob("frame-*.png") if not p.name.endswith(".plain.png")),
            key=lambda p: int(p.stem.split("-")[-1]),
        )
        if not files:
            raise FileNotFoundError(f"no frame-N.png files in {path}")
        return [remove_chroma(Image.open(p)) for p in files]
    if not path.is_file():
        raise FileNotFoundError(path)
    if not count:
        raise ValueError(f"{path}: 'frames' is required for a PNG strip")
    return split_strip(path, count)


def align_to_foot(im: Image.Image, cell: tuple[int, int], foot_y: int) -> Image.Image:
    """Crop to the opaque box, center horizontally, put the lowest opaque row on foot_y.

    The lowest opaque row of each frame is the measured foot anchor; using the real row
    per frame avoids assuming that every generated frame has identical feet."""
    out = Image.new("RGBA", cell)
    bbox = im.getbbox()
    if bbox is None:
        return out
    x0, y0, x1, y1 = bbox
    foot = y1 - 1
    x = (cell[0] - (x1 - x0)) // 2
    y = foot_y - foot + y0
    out.alpha_composite(im.crop(bbox), (x, y))
    return out


def paste_plain(im: Image.Image, cell: tuple[int, int]) -> Image.Image:
    out = Image.new("RGBA", cell)
    out.alpha_composite(im.crop((0, 0, cell[0], cell[1])))
    return out


def write_atlas(out: Path, basename: str, animations, cell: tuple[int, int]) -> None:
    """animations: list of (name, frames, fps, loop). Writes png, <name>.json, anim.json."""
    w, h = cell
    width = max(len(frames) for _, frames, _, _ in animations) * w
    atlas = Image.new("RGBA", (width, len(animations) * h))
    frames_meta = []
    tags = []
    timings = {}
    for row, (name, frames, fps, loop) in enumerate(animations):
        first = len(frames_meta)
        for i, frame in enumerate(frames):
            atlas.alpha_composite(frame, (i * w, row * h))
            frames_meta.append({"filename": f"{name}_{i}", "frame": {"x": i * w, "y": row * h, "w": w, "h": h}, "duration": 0.0})
        tags.append({"name": name, "from": first, "to": len(frames_meta) - 1, "direction": "forward"})
        timings[name] = {"fps": fps, "loop": loop}
    out.mkdir(parents=True, exist_ok=True)
    atlas.save(out / f"{basename}.png")
    (out / f"{basename}.json").write_text(json.dumps({"frames": frames_meta, "meta": {"frameTags": tags}}, indent=2), encoding="utf-8")
    (out / "anim.json").write_text(json.dumps(timings, indent=2), encoding="utf-8")


def build(config: dict, root: Path) -> Path:
    for key in ("name", "output_dir", "cell", "animations"):
        if key not in config:
            raise ValueError(f"config is missing '{key}'")
    cell = (int(config["cell"][0]), int(config["cell"][1]))
    foot_y = int(config.get("foot_y", cell[1] - 2))
    animations = []
    for entry in config["animations"]:
        frames = read_frames(root / entry["source"], entry.get("frames"))
        if entry.get("align", "foot") == "foot":
            frames = [align_to_foot(f, cell, foot_y) for f in frames]
        else:
            frames = [paste_plain(f, cell) for f in frames]
        animations.append((entry["name"], frames, float(entry.get("fps", 10)), bool(entry.get("loop", True))))
    out = root / config["output_dir"]
    write_atlas(out, config["name"], animations, cell)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("config", help="atlas JSON config")
    ap.add_argument("--root", default=".", help="repo root that source and output paths are relative to")
    args = ap.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    try:
        out = build(config, Path(args.root).resolve())
    except (OSError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"atlas written to {out}: {len(config['animations'])} animations")
    return 0


if __name__ == "__main__":
    sys.exit(main())
