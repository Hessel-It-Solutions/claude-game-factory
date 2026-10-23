"""Asset registry and audit."""

from __future__ import annotations

import fnmatch
import json
import re
import shutil
from collections import Counter
from pathlib import Path

from .check import braces
from .core import UsageError, load_config, parse_assets
from .schema import ASSET_HEADERS, SKIP_STATUS_WORDS

ROOT_DIRS = ("art/", "audio/", "docs/", "game/", "production/")


def status_skips(status: str, row: dict) -> bool:
    value = (status + " " + row.get("file", "")).lower()
    return any(word in value for word in SKIP_STATUS_WORDS)


def references(value: str, root: Path, row: dict) -> list[tuple[str, Path | None]]:
    value = re.sub(r"\([^)]*\)", "", value)
    tokens = [t.rstrip(".,;:") for t in re.findall(r"(?:art|audio|docs|game|production)/[^\s|)`]+|[A-Za-z0-9_./*{},-]+\.(?:png|jpg|jpeg|ogg|mp3|wav|gif)", value)]
    expanded_tokens = [variant for token in tokens for variant in braces(token)]
    explicit_dirs = [root / token.rsplit("/", 1)[0] for token in expanded_tokens if "/" in token and (root / token).parent.exists()]
    if not explicit_dirs:
        aid = row["asset_id"]
        if aid.startswith(("chr_", "npc_", "en_", "boss_")):
            explicit_dirs = [root / "art/characters" / aid.split("_v", 1)[0]]
        elif aid.startswith("loc_"):
            explicit_dirs = [root / "art/environments" / aid.split("_v", 1)[0]]
    out = []
    for token in tokens:
        for variant in braces(token):
            if "/" in variant and variant.startswith(ROOT_DIRS):
                candidates = [root / variant]
            else:
                candidates = [directory / variant for directory in explicit_dirs]
                if not candidates:
                    candidates = list((root / "art").rglob(variant))
            matches = []
            for candidate in candidates:
                if any(ch in str(candidate) for ch in "*?["):
                    matches.extend(candidate.parent.glob(candidate.name))
                elif candidate.exists():
                    matches.append(candidate)
            existing = [p for p in matches if p.exists()]
            out.extend((token, p) for p in existing) if existing else out.append((token, None))
    # An ASSETS row can register a range, for example
    # ``01_splash.png to 14_thanks.png``. The folder is then the registered
    # unit, because the table describes a set generated together.
    if " to " in value and len(tokens) >= 2:
        first = next((t for t in tokens if "/" in t), None)
        if first:
            directory = (root / first).parent
            out.extend((str(p.relative_to(root)), p) for p in directory.glob("*.png"))
    return out


def assets_add(args, root: Path) -> int:
    source = Path(args.jsonl) if Path(args.jsonl).is_absolute() else root / args.jsonl
    rows = []
    for number, line in enumerate(source.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise UsageError(f"JSONL line {number}: {exc}") from exc
        row.setdefault("refs", "")  # text-only generation (audio, for example) has no reference
        missing = set(ASSET_HEADERS) - row.keys()
        if missing:
            raise UsageError(f"JSONL line {number}: missing columns {sorted(missing)}")
        rows.append({key: str(row[key]) for key in ASSET_HEADERS})
    existing = {row["asset_id"] for _, row in parse_assets(root)}
    problems = []
    ids = [row["asset_id"] for row in rows]
    problems.extend(f"duplicate id: {ident}" for ident, count in Counter(ids).items() if count > 1)
    problems.extend(f"id already registered: {ident}" for ident in ids if ident in existing)
    for row in rows:
        if status_skips(row["status"], row):
            continue
        matches = [match for _, match in references(row["file"], root, row) if match]
        if not matches:
            problems.append(f"{row['asset_id']}: file does not exist: {row['file']}")
    if problems:
        for problem in problems:
            print(problem)
        return 1
    target = root / "production/ASSETS.md"
    shutil.copy2(target, target.with_suffix(target.suffix + ".bak"))
    with target.open("a") as handle:
        for row in rows:
            handle.write("| " + " | ".join(row[key] for key in ASSET_HEADERS) + " |\n")
    print(f"assets add: {len(rows)} rows appended; backup {target.name}.bak")
    return 0


def assets_check(args, root: Path) -> int:
    rows = parse_assets(root)
    problems = []
    ids = [row["asset_id"] for _, row in rows]
    for ident in sorted({x for x in ids if ids.count(x) > 1}):
        problems.append(("duplicate id", f"production/ASSETS.md: {ident}"))
    registered = set()
    for number, row in rows:
        if status_skips(row["status"], row):
            continue
        for raw, match in references(row["file"], root, row):
            if match:
                registered.add(str(match.relative_to(root)))
                continue
            if raw.endswith(".ogg") and (root / (raw[:-4] + ".mp3")).exists():
                problems.append(("awaiting conversion", f"production/ASSETS.md:{number}: {raw} (mp3 exists)"))
            else:
                problems.append(("missing file", f"production/ASSETS.md:{number}: {raw}"))
    excludes = load_config(root)["assets"]["exclude"]
    for path in sorted((root / "art").rglob("*.png")):
        rel = str(path.relative_to(root))
        if any(fnmatch.fnmatch(rel, p) for p in excludes):
            continue
        if rel not in registered:
            problems.append(("PNG not registered", rel))
    for kind, item in problems:
        print(json.dumps({"type": kind, "problem": item}, ensure_ascii=False) if args.json else f"{kind}: {item}")
    print(json.dumps({"assets": len(rows), "problems": len(problems)}, ensure_ascii=False) if args.json else f"summary: {len(rows)} assets, {len(problems)} problems")
    return 1 if problems else 0
