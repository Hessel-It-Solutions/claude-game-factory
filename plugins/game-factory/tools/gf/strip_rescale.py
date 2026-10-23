"""Cut a raw sprite-gen strip (raw/<dir>/<state>.png, magenta background) into N frames and
rescale all of them with ONE factor per strip, so the tallest body matches the anchor height.

Why it exists: the generator sometimes draws the character at a different pixel block than the
anchor (a walk cycle coming out 61 px tall instead of 75) or touches the top of the cell, and
`extract` refuses it. Here each frame is isolated by the empty columns of the strip, centered on
the torso (top 60%), pixelized to the master palette and pasted into cells (80x80 by default)
with the foot at y=78. A single factor per strip keeps the up and down bob of the cycle. The
reference height is the BODY height: thin parts (a staff, a sling, a tail) are erased by erosion
before measuring, otherwise a strike with the staff above the head would shrink the character.

Usage:
  python tools/gf/strip_rescale.py <raw.png> <out.png> --frames N --height H [--cell 80] [--cell-w 112] [--foot 78] [--ref-frame K]
"""
import argparse
import os
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PIXELIZE_CANDIDATES = [
    os.path.join(HERE, "pixelize.py"),
]


def pixelize_path() -> str:
    for path in PIXELIZE_CANDIDATES:
        if os.path.isfile(path):
            return path
    raise SystemExit("ERROR: pixelize.py not found (copy it to tools/gf/pixelize.py)")


PAD = 200
BORDER = 15  # the strip sometimes carries a guide line on its border


def segments(mask: np.ndarray) -> list[tuple[int, int]]:
    cols = mask.any(0)
    out, start = [], None
    for x, filled in enumerate(cols):
        if filled and start is None:
            start = x
        elif not filled and start is not None:
            out.append((start, x))
            start = None
    if start is not None:
        out.append((start, len(cols)))
    return out


def erode(mask: np.ndarray, r: int) -> np.ndarray:
    """Binary erosion with a (2r+1)^2 box, via integral image: removes anything thinner than ~2r."""
    k = 2 * r + 1
    ii = np.pad(mask.astype(np.int32), ((1, 0), (1, 0))).cumsum(0).cumsum(1)
    h, w = mask.shape
    out = np.zeros_like(mask)
    box = ii[k:, k:] - ii[:-k, k:] - ii[k:, :-k] + ii[:-k, :-k]
    out[r:h - r, r:w - r] = box == k * k
    return out


def split_to(segs: list[tuple[int, int]], mask: np.ndarray, n: int) -> list[tuple[int, int]]:
    """Touching frames: cut the widest segment at the emptiest column of its middle."""
    segs = list(segs)
    while len(segs) < n:
        i = max(range(len(segs)), key=lambda j: segs[j][1] - segs[j][0])
        a, b = segs[i]
        lo, hi = a + (b - a) // 4, b - (b - a) // 4
        cut = lo + int(np.argmin(mask[:, lo:hi].sum(0)))
        segs[i:i + 1] = [(a, cut), (cut, b)]
    return segs


def merge_to(segs: list[tuple[int, int]], n: int) -> list[tuple[int, int]]:
    """Merge the narrowest gaps until N frames remain (a prop detached from the body)."""
    segs = list(segs)
    while len(segs) > n:
        gaps = [segs[i + 1][0] - segs[i][1] for i in range(len(segs) - 1)]
        i = gaps.index(min(gaps))
        segs[i:i + 2] = [(segs[i][0], segs[i + 1][1])]
    return segs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("raw")
    ap.add_argument("out")
    ap.add_argument("--frames", type=int, required=True)
    ap.add_argument("--height", type=int, required=True)
    ap.add_argument("--cell", type=int, default=80)
    ap.add_argument("--cell-w", type=int, default=0, help="cell width (0 = same as the height)")
    ap.add_argument("--foot", type=int, default=78)
    ap.add_argument("--palette", default="docs/palette.hex")
    ap.add_argument("--ref-frame", type=int, default=-1,
                    help="standing frame used as the ruler (for example the last frame of a throw); -1 = the tallest body")
    args = ap.parse_args()

    im = np.array(Image.open(args.raw).convert("RGB")).astype(int)
    im[:, :BORDER] = (255, 0, 255)
    im[:, -BORDER:] = (255, 0, 255)
    im = np.pad(im, ((0, 0), (PAD, PAD), (0, 0)))
    im[:, :PAD] = (255, 0, 255)
    im[:, -PAD:] = (255, 0, 255)
    mask = ~((abs(im[..., 0] - 255) < 70) & (im[..., 1] < 90) & (abs(im[..., 2] - 255) < 70))

    segs = [s for s in segments(mask) if mask[:, s[0]:s[1]].sum() > 400]  # drop dust
    if not segs:
        print("ERROR: empty strip", file=sys.stderr)
        return 2
    segs = merge_to(segs, args.frames) if len(segs) > args.frames else split_to(segs, mask, args.frames)

    rows = [np.where(mask[:, a:b].any(1))[0] for a, b in segs]
    top = min(r[0] for r in rows)
    bot = max(r[-1] for r in rows) + 1
    radius = max(4, round(max(r[-1] - r[0] + 1 for r in rows) / 75 * 1.8))
    body = erode(mask, radius)
    body_h = []
    for a, b in segs:
        ys = np.where(body[:, a:b].any(1))[0]
        body_h.append(ys[-1] - ys[0] + 1 + 2 * radius if len(ys) else 0)
    width = max(b - a for a, b in segs) + 40
    ref = body_h[args.ref_frame] if args.ref_frame >= 0 else max(body_h)
    target = round(args.height * (bot - top) / ref)
    cw = args.cell_w or args.cell

    strip = Image.new("RGBA", (cw * args.frames, args.cell), (0, 0, 0, 0))
    heights = []
    clipped = []
    with tempfile.TemporaryDirectory() as tmp:
        for i, (a, b) in enumerate(segs):
            iso = np.zeros_like(im)
            iso[..., 0] = 255
            iso[..., 2] = 255
            iso[:, a:b] = im[:, a:b]
            ys, xs = np.nonzero(mask[top:top + int((bot - top) * 0.6), a:b])
            cx = a + int(xs.mean()) if len(xs) else (a + b) // 2
            crop = Image.fromarray(iso.astype("uint8")).crop((cx - width // 2, top, cx + width // 2, bot))
            src, dst = os.path.join(tmp, f"{i}_src.png"), os.path.join(tmp, f"{i}.png")
            crop.save(src)
            subprocess.run([sys.executable, pixelize_path(), src, dst, "--height", str(target),
                            "--palette", args.palette, "--chroma", "magenta"], check=True, capture_output=True)
            frame = Image.open(dst).convert("RGBA")
            bbox = frame.getbbox()
            heights.append(bbox[3] - bbox[1])
            cell = Image.new("RGBA", (cw, args.cell), (0, 0, 0, 0))
            cell.paste(frame, (cw // 2 - frame.width // 2, args.foot - frame.height), frame)
            # A wide strike can overflow the cell: report how many pixels were cut.
            lost = frame.getchannel("A").point(lambda v: 255 if v else 0).histogram()[255] - \
                cell.getchannel("A").point(lambda v: 255 if v else 0).histogram()[255]
            if lost > 0:
                clipped.append((i, lost))
            strip.alpha_composite(cell, (cw * i, 0))
    strip.save(args.out)
    print(f"{os.path.basename(args.out)} frames={args.frames} heights={heights} max_width={width} clipped={clipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
