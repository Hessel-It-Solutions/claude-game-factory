from __future__ import annotations

import json
import re
import shlex
import shutil
import subprocess
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from .schema import ASSET_HEADERS, BUDGET_CAP_PREFIX, ID_PREFIXES, STATE_FIELDS

IDS = r"(?:" + "|".join(re.escape(p) for p in ID_PREFIXES) + r")[A-Za-z0-9_]+"
CHROMA = {"magenta": (255, 0, 255), "green": (0, 255, 0)}
PACKAGE_DIR = Path(__file__).resolve().parent
TOOL_DIR = PACKAGE_DIR.parent


class UsageError(Exception):
    pass


def find_root(start: Path | None = None) -> Path:
    p = (start or Path.cwd()).resolve()
    for candidate in (p, *p.parents):
        if (candidate / "production" / "STATE.md").is_file():
            return candidate
    raise UsageError("repo root not found (looked for production/STATE.md in the current directory and its parents)")


def load_config(root: Path) -> dict:
    """gf.json from the game repo (tools/gf/gf.json), else the one next to the package."""
    for path in (root / "tools/gf/gf.json", TOOL_DIR / "gf.json"):
        if path.is_file():
            return json.loads(path.read_text())
    raise UsageError("gf.json not found")


def load_pixelizer(root: Path):
    """Find the official pixelize.py: gf.json "pixelizer", the game repo, or the plugin."""
    candidates = []
    try:
        configured = load_config(root).get("pixelizer")
    except UsageError:
        configured = None
    if configured:
        candidates.append(root / configured)
    candidates += [
        root / "tools/gf/pixelize.py",
        # next to the gf package, wherever the CLI runs from
        PACKAGE_DIR.parent / "pixelize.py",
    ]
    path = next((c for c in candidates if c.is_file()), None)
    if path is None:
        raise UsageError("pixelize.py not found; set \"pixelizer\" in gf.json or copy it to tools/gf/pixelize.py")
    spec = spec_from_file_location("gf_official_pixelize", path)
    if not spec or not spec.loader:
        raise UsageError(f"could not load {path}")
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def palette(root: Path) -> set[str]:
    vals = set()
    for line in (root / "docs/palette.hex").read_text().splitlines():
        value = line.strip().lstrip("#").lower()
        if re.fullmatch(r"[0-9a-f]{6}", value):
            vals.add(value)
    return vals


def image_paths(items: list[str], root: Path) -> list[Path]:
    found: list[Path] = []
    for raw in items:
        p = (Path(raw) if Path(raw).is_absolute() else root / raw).resolve()
        if p.is_dir():
            found.extend(sorted(x for x in p.rglob("*.png") if x.is_file()))
        elif p.suffix.lower() == ".png":
            found.append(p)
        else:
            raise UsageError(f"PNG not found: {raw}")
    return found


def rules_data(path: str | None, root: Path) -> dict:
    if not path:
        return {}
    p = Path(path) if Path(path).is_absolute() else root / path
    try:
        data = json.loads(p.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise UsageError(f"invalid rules file: {exc}") from exc
    if not isinstance(data, dict):
        raise UsageError("rules must be a JSON object")
    return data


def color_set(arr: np.ndarray) -> tuple[set[str], int]:
    opaque = arr[..., 3] > 0
    colors = {"%02x%02x%02x" % tuple(c) for c in arr[opaque, :3]}
    semi = int(((arr[..., 3] > 0) & (arr[..., 3] < 255)).sum())
    return colors, semi


def validate_one(path: Path, root: Path, expected: tuple[int, int] | None = None, rules: dict | None = None) -> list[str]:
    problems = []
    try:
        image = Image.open(path).convert("RGBA")
        arr = None
    except Exception as exc:
        label = path.relative_to(root) if path.is_relative_to(root) else path
        return [f"{label}: unreadable PNG ({exc})"]
    # Counting with Pillow avoids materializing a whole NumPy array. That
    # matters for the repo check, which walks large storyboard images.
    rgb_image = image.convert("RGB")
    if image.getchannel("A").getextrema()[0] == 0:
        arr = np.array(image)
        opaque = arr[..., 3] > 0
        colors = {"%02x%02x%02x" % tuple(value) for value in arr[..., :3][opaque]}
        color_counts = None
    else:
        color_counts = rgb_image.getcolors(maxcolors=10_000_000) or []
    alpha_counts = image.getchannel("A").getcolors(maxcolors=10_000_000) or []
    # getcolors returns (count, value) pairs.
    if color_counts is not None:
        colors = {"%02x%02x%02x" % tuple(value) for _, value in color_counts}
    semi = sum(n for n, value in alpha_counts if 0 < value < 255)
    outside = colors - palette(root)
    rel = path.relative_to(root) if path.is_relative_to(root) else path
    if outside:
        problems.append(f"{rel}: {len(outside)} colors outside the palette ({', '.join(sorted(outside)[:8])})")
    if semi:
        problems.append(f"{rel}: {semi} pixels with partial alpha")
    if expected and image.size != expected:
        problems.append(f"{rel}: size {image.width}x{image.height}, expected {expected[0]}x{expected[1]}")
    for rule in (rules or {}).get("rules", []):
        if not isinstance(rule, dict):
            continue
        box = rule.get("box") or rule.get("region")
        if not box or len(box) != 4:
            continue
        x0, y0, x1, y1 = map(int, box)
        if arr is None:
            arr = np.array(image)
        region = arr[max(0, y0):min(arr.shape[0], y1 + 1), max(0, x0):min(arr.shape[1], x1 + 1)]
        got, _ = color_set(region)
        allowed = {str(c).lower().lstrip("#") for c in rule.get("allowed", [])}
        forbidden = {str(c).lower().lstrip("#") for c in rule.get("forbidden", [])}
        bad = (got - allowed) if allowed else (got & forbidden)
        if bad:
            problems.append(f"{rel}: rule {rule.get('name', 'region')} violated ({', '.join(sorted(bad)[:8])})")
    return problems


def post(args, root: Path) -> int:
    pix = load_pixelizer(root)
    source = Path(args.input) if Path(args.input).is_absolute() else root / args.input
    dest = Path(args.output) if Path(args.output).is_absolute() else root / args.output
    if not source.is_file():
        raise UsageError(f"input does not exist: {args.input}")
    if dest.resolve() == source.resolve():
        raise UsageError("input and output must differ")
    img = Image.open(source).convert("RGBA")
    arr = np.array(img)
    rgb, alpha = arr[..., :3], arr[..., 3].copy()
    if args.chroma != "none":
        mask = pix.chroma_mask(rgb, CHROMA[args.chroma], 120)
        alpha[mask] = 0
    pal = pix.load_palette(root / "docs/palette.hex")
    idx = pix.nearest_index(rgb, pal)
    if args.width:
        tw, th = args.width, max(1, round(img.height * args.width / img.width))
        bw = bh = max(1, min(img.width // tw, img.height // th, 8)) if img.width >= tw and img.height >= th else 1
        size = (tw * bw, th * bh)
        # The chroma is already removed from alpha above. Resizing ``img``
        # here would bring back the source alpha and make the background opaque.
        rgb = np.array(Image.fromarray(rgb).resize(size, Image.Resampling.LANCZOS))
        alpha = np.where(
            np.array(Image.fromarray(alpha).resize(size, Image.Resampling.LANCZOS)) >= 128,
            255,
            0,
        ).astype(np.uint8)
        idx = pix.nearest_index(rgb, pal)
    elif args.pitch == "auto":
        bw = bh = max(1, pix.estimate_pitch(idx))
    else:
        bw = bh = int(args.pitch)
        if bw < 1:
            raise UsageError("--pitch must be positive")
    oi, oa = pix.block_mode(idx, alpha, bw, bh, len(pal))
    out = Image.fromarray(np.dstack([pal[oi].astype(np.uint8), oa]), "RGBA")
    rules = rules_data(args.rules, root)
    out = clean_image(out, rules, args.chroma)
    dest.parent.mkdir(parents=True, exist_ok=True)
    out.save(dest)
    if args.preview:
        out.resize((out.width * args.preview, out.height * args.preview), Image.Resampling.NEAREST).save(dest.with_suffix(".preview.png"))
    problems = validate_one(dest, root, rules=rules)
    for p in problems:
        print(p)
    print(f"size {out.width}x{out.height}, {len(color_set(np.array(out))[0])} colors, colors outside palette {sum('outside the palette' in p for p in problems)}, partial alpha {sum('partial alpha' in p for p in problems)}")
    return 1 if problems else 0


def _hex(value: str) -> tuple[int, int, int]:
    return tuple(bytes.fromhex(str(value).lower().lstrip("#")))  # type: ignore[return-value]


def clean_image(image: Image.Image, rules: dict, chroma: str) -> Image.Image:
    """Optional per-game color cleanup, driven by the rules file.

    Supported keys (all optional):
      "remap": {"3a1210": "4a2820"}            global color replacement
      "remap_regions": [{"box": [x0,y0,x1,y1], "from": ["615749"], "to": "61391f"}]
      "remap_from_y": {"y": 25, "map": {...}}   replacement only below row y
      "fringe_colors": ["561318", "8b2125"]     dark chroma fringe removed next to transparency
    """
    a = np.array(image.convert("RGBA"))
    h, w = a.shape[:2]
    remap = {k.lower().lstrip("#"): v for k, v in (rules.get("remap") or {}).items()}
    below = rules.get("remap_from_y") or {}
    below_y = int(below.get("y", 0)) if below else 0
    below_map = {k.lower().lstrip("#"): v for k, v in (below.get("map") or {}).items()}
    regions = []
    for region in rules.get("remap_regions") or []:
        box = tuple(map(int, region["box"]))
        regions.append((box, {c.lower().lstrip("#") for c in region["from"]}, region["to"]))
    if remap or below_map or regions:
        for y in range(h):
            for x in range(w):
                if not a[y, x, 3]:
                    continue
                c = "%02x%02x%02x" % tuple(a[y, x, :3])
                if c in remap:
                    a[y, x, :3] = _hex(remap[c])
                elif c in below_map and y > below_y:
                    a[y, x, :3] = _hex(below_map[c])
                for box, sources, target in regions:
                    if box[0] <= x <= box[2] and box[1] <= y <= box[3] and c in sources:
                        a[y, x, :3] = _hex(target)
    fringe = {_hex(c) for c in rules.get("fringe_colors") or []}
    if chroma in CHROMA and fringe:
        transparent = a[..., 3] == 0
        for _ in range(2):
            near = np.zeros_like(transparent)
            near[1:] |= transparent[:-1]; near[:-1] |= transparent[1:]
            near[:, 1:] |= transparent[:, :-1]; near[:, :-1] |= transparent[:, 1:]
            for y, x in zip(*np.where(near & ~transparent)):
                if tuple(int(v) for v in a[y, x, :3]) in fringe:
                    a[y, x, 3] = 0
            transparent = a[..., 3] == 0
    return Image.fromarray(a, "RGBA")


def parse_size(text: str) -> tuple[int, int]:
    m = re.fullmatch(r"(\d+)x(\d+)", text.lower())
    if not m:
        raise UsageError(f"invalid size: {text}")
    return int(m.group(1)), int(m.group(2))


def validate(args, root: Path) -> int:
    paths = image_paths(args.paths, root)
    expected = parse_size(args.size) if args.size else None
    rules = rules_data(args.rules, root)
    problems = []
    for p in paths:
        problems.extend(validate_one(p, root, expected, rules))
    for p in problems:
        print(json.dumps({"problem": p}, ensure_ascii=False) if args.json else p)
    print(json.dumps({"files": len(paths), "problems": len(problems)}, ensure_ascii=False) if args.json else f"summary: {len(paths)} files, {len(problems)} problems")
    return 1 if problems else 0


def flood_background(arr: np.ndarray) -> np.ndarray:
    h, w = arr.shape[:2]
    rgb = arr[..., :3].astype(int)
    seed = np.zeros((h, w), bool); q = deque()
    for y, x in [(0, x) for x in range(w)] + [(h - 1, x) for x in range(w)] + [(y, 0) for y in range(h)] + [(y, w - 1) for y in range(h)]:
        q.append((y, x))
    def bg(y, x):
        r, g, b = rgb[y, x]
        return (r > 180 and g < 140 and b > 180) or (r > 180 and g > 180 and b > 180) or (max(rgb[y, x]) - min(rgb[y, x]) < 8 and r > 180)
    while q:
        y, x = q.popleft()
        if seed[y, x] or not bg(y, x): continue
        seed[y, x] = True
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and not seed[ny, nx]: q.append((ny, nx))
    return seed


def cut(args, root: Path) -> int:
    sheet = Path(args.sheet) if Path(args.sheet).is_absolute() else root / args.sheet
    outdir = Path(args.outdir) if Path(args.outdir).is_absolute() else root / args.outdir
    if not sheet.is_file(): raise UsageError(f"sheet does not exist: {args.sheet}")
    im = Image.open(sheet).convert("RGBA")
    names = [x.strip() for x in args.names.split(",")] if args.names else []
    if args.grid:
        cols, rows = map(int, args.grid.lower().split("x")); cw, ch = im.width // cols, im.height // rows
        cells = [(c * cw, r * ch, (c + 1) * cw, (r + 1) * ch) for r in range(rows) for c in range(cols)]
    else:
        if args.cell:
            cw_in, ch_in = parse_size(args.cell)
            cols, rows = im.width // cw_in, im.height // ch_in
            if not cols or not rows:
                raise UsageError("--cell does not fit in the sheet for --auto")
            cells = [(c * cw_in, r * ch_in, (c + 1) * cw_in, (r + 1) * ch_in) for r in range(rows) for c in range(cols)]
        else:
            mask = flood_background(np.array(im))
            # Split the connected foreground into columns and rows using projections.
            fg = ~mask
            xs = np.where(fg.any(axis=0))[0]; ys = np.where(fg.any(axis=1))[0]
            if not len(xs) or not len(ys): raise UsageError("--auto found no cells")
            # Auto sheets are regular: infer runs of occupied columns and rows.
            def runs(vals):
                out = []; start = prev = int(vals[0])
                for n in vals[1:]:
                    n = int(n)
                    if n > prev + 1: out.append((start, prev + 1)); start = n
                    prev = n
                out.append((start, prev + 1)); return out
            xr, yr = runs(xs), runs(ys)
            if len(xr) == 1 and len(yr) > 1: xr = [(0, im.width)]
            if len(yr) == 1 and len(xr) > 1: yr = [(0, im.height)]
            cells = [(x0, y0, x1, y1) for y0, y1 in yr for x0, x1 in xr]
    if args.cell:
        cw, ch = parse_size(args.cell)
    else:
        cw = ch = None
    outdir.mkdir(parents=True, exist_ok=True)
    for i, box in enumerate(cells):
        cell = im.crop(box)
        if args.margin:
            cell = cell.crop((args.margin, args.margin, max(args.margin, cell.width - args.margin), max(args.margin, cell.height - args.margin)))
        if cw and ch: cell = cell.resize((cw, ch), Image.Resampling.NEAREST)
        name = names[i] if i < len(names) else f"{i + 1:02d}"
        cell.save(outdir / f"{name}.png")
        if args.post:
            post_args = type("Post", (), {"input": str(outdir / f"{name}.png"), "output": str(outdir / f"{name}.png"), "width": args.post_width, "pitch": "auto", "chroma": args.post_chroma, "preview": 0, "rules": None})
            tmp = outdir / f".{name}.post.png"; post_args.output = str(tmp); post(post_args, root); tmp.replace(outdir / f"{name}.png")
    print(f"cut {len(cells)} cells into {outdir.relative_to(root) if outdir.is_relative_to(root) else outdir}")
    return 0


def board(args, root: Path) -> int:
    folder = Path(args.folder) if Path(args.folder).is_absolute() else root / args.folder
    files = sorted(folder.glob("[0-9][0-9].png"))
    if not files: raise UsageError("no NN.png files in the folder")
    cols = args.cols or (2 if len(files) <= 4 else 3); scale = args.scale or 1
    thumbs = [Image.open(f).convert("RGB").resize((Image.open(f).width * scale, Image.open(f).height * scale), Image.Resampling.NEAREST) for f in files]
    w, h = max(x.width for x in thumbs), max(x.height for x in thumbs); pad, cap = 16, 24 if args.labels else 0
    rows = (len(files) + cols - 1) // cols; out = Image.new("RGB", (cols * w + (cols + 1) * pad, rows * (h + cap) + (rows + 1) * pad), (24, 20, 18)); draw = ImageDraw.Draw(out)
    for i, (f, thumb) in enumerate(zip(files, thumbs)):
        r, c = divmod(i, cols); x, y = pad + c * (w + pad), pad + r * (h + cap + pad)
        if args.labels: draw.text((x, y + 3), f.stem, fill=(242, 212, 126))
        out.paste(thumb, (x, y + cap))
    dest = Path(args.out) if args.out else folder / "board.png"; dest = dest if dest.is_absolute() else root / dest; out.save(dest)
    print(f"board {dest.relative_to(root) if dest.is_relative_to(root) else dest}: {len(files)} frames")
    return 0


def sprite_gen_binary(root: Path) -> str:
    local = root / "tools/sprite-gen/.venv/bin/sprite-gen"
    return str(local) if local.exists() else (shutil.which("sprite-gen") or "sprite-gen")


def codex_one(job: dict, root: Path, dry: bool) -> tuple[str, str]:
    jid = str(job.get("id", "")); prompt = job.get("prompt"); refs = job.get("refs", []); out = job.get("out")
    if not jid or not isinstance(prompt, str) or not isinstance(refs, list) or not isinstance(out, str): return jid or "?", "invalid"
    if len(refs) > 5: return jid, "refs > 5"
    ref_paths = [str((root / r).resolve() if not Path(r).is_absolute() else Path(r)) for r in refs]
    if any(not Path(r).is_file() for r in ref_paths): return jid, "missing reference"
    output = (root / out).resolve() if not Path(out).is_absolute() else Path(out)
    report = output.with_suffix(output.suffix + ".report.json")
    cmd = [sprite_gen_binary(root), "gen", "--provider", "codex", "--prompt", prompt]
    for ref in ref_paths: cmd += ["--ref", ref]
    cmd += ["--out", str(output), "--report", str(report)]
    started = time.monotonic()
    if dry: return jid, shlex.join(cmd)
    output.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    status = "ok" if proc.returncode == 0 else f"error ({proc.returncode})"
    if status == "ok" and job.get("post"):
        pc = job["post"]; pa = type("Post", (), {"input": str(output), "output": str(output), "width": pc.get("width"), "pitch": "auto", "chroma": pc.get("chroma", "none"), "preview": 0, "rules": None})
        status = "ok" if post(pa, root) == 0 else "post invalid"
    report.write_text(json.dumps({"prompt": prompt, "refs": refs, "command": shlex.join(cmd), "duration": round(time.monotonic() - started, 3), "status": status}, ensure_ascii=False, indent=2) + "\n")
    return jid, status


def codex(args, root: Path) -> int:
    path = Path(args.jobs) if Path(args.jobs).is_absolute() else root / args.jobs
    try: jobs = json.loads(path.read_text())
    except Exception as exc: raise UsageError(f"invalid jobs.json: {exc}") from exc
    if not isinstance(jobs, list): raise UsageError("jobs.json must be a list")
    if args.dry_run:
        for job in jobs: print(f"{job.get('id', '?')}: {codex_one(job, root, True)[1]}")
        print(f"summary: {len(jobs)} jobs, dry-run")
        return 0 if all(codex_one(j, root, True)[1] not in {"invalid", "refs > 5", "missing reference"} for j in jobs) else 1
    results = []
    with ThreadPoolExecutor(max_workers=max(1, args.parallel)) as pool:
        futures = [pool.submit(codex_one, j, root, False) for j in jobs]
        for f in as_completed(futures): results.append(f.result())
    results.sort(); bad = 0
    for jid, status in results: print(f"{jid}: {status}"); bad += status not in {"ok"}
    print(f"summary: {len(results)} jobs, {bad} problems")
    return 1 if bad else 0


def parse_assets(root: Path):
    rows = []; path = root / "production/ASSETS.md"
    for no, line in enumerate(path.read_text().splitlines(), 1):
        if line.startswith("|") and not line.startswith("|---"):
            cells = [x.strip() for x in line.strip("|").split("|")]
            if cells and cells[0] != "asset_id" and len(cells) >= len(ASSET_HEADERS): rows.append((no, dict(zip(ASSET_HEADERS, cells))))
    return rows


def budget(args, root: Path) -> int:
    before, after, cap = int(args.before), int(args.after), int(args.cap); spent = before - after
    if spent < 0 or spent > cap: raise UsageError("invalid balance or spend above the cap")
    path = root / "production/BUDGET.md"; backup = path.with_suffix(path.suffix + ".bak"); shutil.copy2(path, backup)
    with path.open("a") as f: f.write(f"| {args.wave} | {before} | {BUDGET_CAP_PREFIX} {cap} | {spent} | {after} | {args.notes} |\n")
    print(f"budget: spent {spent}, balance {after}; backup {backup.name}"); return 0


def state(args, root: Path) -> int:
    if args.field not in STATE_FIELDS: raise UsageError("field must be one of: " + ", ".join(repr(f) for f in STATE_FIELDS))
    path = root / "production/STATE.md"; lines = path.read_text().splitlines(True); found = False
    for i, line in enumerate(lines):
        if line.startswith(args.field + ":"):
            lines[i] = args.field + ": " + args.value + "\n"; found = True
    if not found: raise UsageError(f"field not found: {args.field}")
    path.write_text("".join(lines)); print(f"state: {args.field} updated"); return 0


def context(args, root: Path) -> int:
    terms = set(filter(None, (args.seq or "").split(",") + (args.chars or "").split(",") + (args.locs or "").split(",")))
    files = [root / "production/DECISIONS.md", root / "docs/08-content-plan.md"] + sorted((root / "docs/05-script").glob("ch*.md"))
    chunks = []
    for p in files:
        if not p.is_file(): continue
        lines = p.read_text(errors="replace").splitlines()
        selected = [f"{p.relative_to(root)}:{i + 1}: {line}" for i, line in enumerate(lines) if not terms or any(t in line for t in terms)]
        if selected: chunks.append("\n".join(selected))
    for ident in terms:
        for p in sorted((root / "docs").rglob(f"{ident}.md")):
            chunks.append(f"{p.relative_to(root)}:\n" + p.read_text(errors="replace"))
    for p in sorted((root / "art").rglob("*.png")):
        if not terms or any(t in str(p) for t in terms): chunks.append(str(p.relative_to(root)))
    result = "\n\n".join(chunks); chars = len(result); tokens = chars // 4
    if tokens > 8000: raise UsageError(f"context exceeds 8k estimated tokens: {tokens}")
    out = Path(args.out) if args.out else None
    if out: (out if out.is_absolute() else root / out).write_text(result + "\n")
    else: print(result)
    print(f"context: {tokens} estimated tokens ({chars} characters)")
    return 0
