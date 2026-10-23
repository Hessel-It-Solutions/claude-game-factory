#!/usr/bin/env python3
"""Convert an AI-generated image into clean-grid pixel art.

Measures the size of the generated "pixel" block, downsamples by majority color
vote inside each block (keeps 1px outlines better than average/lanczos),
snaps the colors to the master palette and optionally turns the chroma
background into alpha.

Usage:
  pixelize.py in.png out.png --pitch auto --palette docs/palette.hex --chroma magenta --preview 4
  pixelize.py in.png out.png --width 320 --colors 32
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

CHROMA = {"magenta": (255, 0, 255), "green": (0, 255, 0)}


def load_palette(path):
    colors = []
    for line in Path(path).read_text().splitlines():
        line = line.strip().lstrip("#")
        if not line or line.startswith(("GIMP", "Name", "Columns", ";")):
            continue
        parts = line.split()
        if len(parts) >= 3 and all(p.isdigit() for p in parts[:3]):
            colors.append(tuple(int(p) for p in parts[:3]))  # .gpl format
        elif len(parts[0]) == 6:
            colors.append(tuple(int(parts[0][i:i + 2], 16) for i in (0, 2, 4)))
    if not colors:
        sys.exit(f"empty or unreadable palette: {path}")
    return np.array(colors, dtype=np.int32)


def chroma_mask(rgb, key, tol):
    dist = np.abs(rgb.astype(np.int32) - np.array(key)).sum(axis=2)
    return dist <= tol


def estimate_pitch(idx, max_pitch=32):
    """Block size from how well color edges align to a grid.

    Works on the palette index map (compression noise already removed).
    For each step p, finds the phase that concentrates the most edges and
    discounts chance (1/p). The true grid beats its sub-harmonics because the
    discount is smaller.
    """
    hist = []
    for axis in (1, 0):
        edges = np.diff(idx, axis=axis) != 0
        hist.append(edges.sum(axis=0 if axis == 1 else 1).astype(np.float64))
    best_p, best_score = 1, 0.0
    for p in range(2, max_pitch + 1):
        score = 0.0
        for h in hist:
            total = h.sum()
            if total == 0 or len(h) < 2 * p:
                continue
            hits = max(h[ph::p].sum() for ph in range(p)) / total
            score += hits - 1.0 / p
        if score > best_score:
            best_p, best_score = p, score
    return best_p


def nearest_index(rgb, palette):
    px = rgb.reshape(-1, 3).astype(np.int32)
    out = np.empty(len(px), dtype=np.int32)
    step = 65536  # chunked to avoid blowing up memory on large images
    for i in range(0, len(px), step):
        d = ((px[i:i + step, None, :] - palette[None, :, :]) ** 2).sum(axis=2)
        out[i:i + step] = d.argmin(axis=1)
    return out.reshape(rgb.shape[:2])


def block_mode(idx, alpha, bw, bh, n):
    h, w = idx.shape
    gh, gw = h // bh, w // bw
    idx = idx[: gh * bh, : gw * bw].reshape(gh, bh, gw, bw).transpose(0, 2, 1, 3).reshape(gh, gw, -1)
    a = alpha[: gh * bh, : gw * bw].reshape(gh, bh, gw, bw).transpose(0, 2, 1, 3).reshape(gh, gw, -1)
    # alpha and voting: transparent pixels do not vote on color
    opaque = a >= 128
    flat_idx = idx.reshape(-1, idx.shape[2])
    flat_op = opaque.reshape(-1, opaque.shape[2])
    rows = np.repeat(np.arange(flat_idx.shape[0]), flat_idx.shape[1])
    votes = np.zeros((flat_idx.shape[0], n), dtype=np.int32)
    np.add.at(votes, (rows, flat_idx.ravel()), flat_op.ravel().astype(np.int32))
    out_idx = votes.argmax(axis=1).reshape(gh, gw)
    out_a = (opaque.mean(axis=2) >= 0.5).astype(np.uint8) * 255
    return out_idx, out_a


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--pitch", default="auto", help="block size in px, or 'auto'")
    ap.add_argument("--width", type=int, help="final logical width (ignores --pitch)")
    ap.add_argument("--height", type=int, help="final logical height (ignores --pitch)")
    ap.add_argument("--palette", help=".hex file (one RRGGBB per line) or .gpl")
    ap.add_argument("--colors", type=int, default=32, help="number of colors when there is no --palette")
    ap.add_argument("--exclude", help="palette colors forbidden for this asset: comma-separated RRGGBB, "
                    "or a .hex file (e.g. UI colors and a hero-only color ramp)")
    ap.add_argument("--chroma", choices=CHROMA, help="chroma background becomes transparent")
    ap.add_argument("--chroma-tol", type=int, default=120)
    ap.add_argument("--preview", type=int, default=0, help="also write <out>.preview.png enlarged N× (nearest)")
    args = ap.parse_args()

    img = Image.open(args.input).convert("RGBA")
    arr = np.array(img)
    rgb, alpha = arr[:, :, :3], arr[:, :, 3].copy()
    if args.chroma:
        alpha[chroma_mask(rgb, CHROMA[args.chroma], args.chroma_tol)] = 0

    if args.palette:
        palette = load_palette(args.palette)
        if args.exclude:
            ex = load_palette(args.exclude) if Path(args.exclude).exists() else np.array(
                [tuple(int(h.strip().lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)) for h in args.exclude.split(",")])
            keep = ~(palette[:, None, :] == ex[None, :, :]).all(axis=2).any(axis=1)
            palette = palette[keep]
    else:
        opaque_px = Image.fromarray(rgb[alpha >= 128].reshape(-1, 1, 3))
        q = opaque_px.quantize(colors=args.colors, method=Image.Quantize.MEDIANCUT)
        palette = np.array(q.getpalette()[: args.colors * 3], dtype=np.int32).reshape(-1, 3)
    idx = nearest_index(rgb, palette)

    h, w = alpha.shape
    if args.width or args.height:
        # Exact final size: resample the input to an integer multiple of the target
        # before the block vote (otherwise block rounding is off by a few px).
        tw = args.width or max(1, round(w * args.height / h))
        th = args.height or max(1, round(h * args.width / w))
        bw = bh = max(1, min(w // tw, h // th, 8)) if min(w // tw, h // th) >= 1 else 1
        big = Image.fromarray(np.dstack([rgb, alpha]), "RGBA").resize((tw * bw, th * bh), Image.LANCZOS)
        arr = np.array(big)
        rgb, alpha = arr[:, :, :3], np.where(arr[:, :, 3] >= 128, 255, 0).astype(np.uint8)
        idx = nearest_index(rgb, palette)
    else:
        p = estimate_pitch(idx) if args.pitch == "auto" else int(args.pitch)
        bw = bh = max(1, p)

    out_idx, out_a = block_mode(idx, alpha, bw, bh, len(palette))
    out = np.dstack([palette[out_idx].astype(np.uint8), out_a])
    result = Image.fromarray(out, "RGBA")
    result.save(args.output)
    print(f"block {bw}x{bh}px -> {result.width}x{result.height} logical, {len(palette)} colors: {args.output}")
    if args.preview:
        prev = result.resize((result.width * args.preview, result.height * args.preview), Image.NEAREST)
        prev_path = Path(args.output).with_suffix(".preview.png")
        prev.save(prev_path)
        print(f"preview: {prev_path}")


if __name__ == "__main__":
    main()
