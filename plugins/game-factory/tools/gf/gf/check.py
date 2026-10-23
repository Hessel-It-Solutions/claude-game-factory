"""Mechanical continuity checks. They do not interpret semantics."""

from __future__ import annotations

import fnmatch
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import unquote

from .core import IDS, load_config, validate_one
from .schema import MAX_LINE_CHARS, SEE_SHEET

CHARACTER_PREFIXES = ("chr_", "npc_", "en_", "boss_")


def derive_speakers(root: Path) -> dict[str, str]:
    """SPEAKER label -> character id, derived from docs/03-characters/<id>.md.

    chr_hero_young.md answers to HERO and HERO YOUNG. Entries in gf.json
    "speakers" win over the derived ones.
    """
    found: dict[str, str] = {}
    folder = root / "docs/03-characters"
    if folder.is_dir():
        for path in sorted(folder.glob("*.md")):
            stem = path.stem
            prefix = next((p for p in CHARACTER_PREFIXES if stem.startswith(p)), None)
            if not prefix:
                continue
            words = stem[len(prefix):].split("_")
            if not words or not words[0]:
                continue
            found.setdefault(words[0].upper(), stem)
            found.setdefault(" ".join(words).upper(), stem)
    return found


def speakers_map(root: Path) -> dict[str, str]:
    return {**derive_speakers(root), **{k.upper(): v for k, v in load_config(root).get("speakers", {}).items()}}


def braces(pattern: str) -> list[str]:
    match = re.search(r"\{([^{}]+)\}", pattern)
    if not match:
        return [pattern]
    return [*sum((braces(pattern[:match.start()] + part + pattern[match.end():]) for part in match.group(1).split(",")), [])]


def expand_paths(root: Path, pattern: str, base: Path | None = None) -> list[Path]:
    pattern = unquote(pattern.split("#", 1)[0]).strip().strip("`<>")
    if not pattern or pattern.startswith(("http:", "https:", "mailto:")):
        return []
    start = base or root
    values = []
    for variant in braces(pattern):
        p = Path(variant)
        candidate = p if p.is_absolute() else start / p
        if any(ch in variant for ch in "*?["):
            values.extend(x.resolve() for x in candidate.parent.glob(candidate.name) if x.exists())
        elif candidate.exists():
            values.append(candidate.resolve())
    return sorted(set(values))


def path_tokens(line: str) -> list[str]:
    tokens = re.findall(r"(?:!?\[[^]]*\]\()?([^\s)\]>`]+(?:\{[^}]+\}[^\s)\]>`]*)?)(?:\))?", line)
    output = []
    for token in tokens:
        if any(token.startswith(prefix) for prefix in ("art/", "docs/", "production/", "../../art/", "../art/", "../../docs/", "../docs/")):
            output.append(token.rstrip(".,;:"))
    return output


def link_problems(root: Path, files: list[Path]) -> list[str]:
    problems = []
    for path in files:
        if not path.is_file():
            continue
        for number, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
            links = re.findall(r"!?\[[^]]*\]\(([^)]+)\)", line)
            loose = path_tokens(line)
            for raw in links + loose:
                raw = raw.split("#", 1)[0]
                if raw.startswith(("http:", "https:", "mailto:")):
                    continue
                base = path.parent if not raw.startswith(("art/", "docs/", "production/")) else root
                if not expand_paths(root, raw, base):
                    problems.append(f"{path.relative_to(root)}:{number}: {raw}")
    return sorted(set(problems))


def scope_files(root: Path, scope: str | None) -> list[Path]:
    """Script files in scope. No scope means every doc. A name from gf.json
    "scopes" (for example "pilot": "ch01,ch02") expands to its file list."""
    if not scope:
        return sorted((root / "docs").rglob("*.md"))
    scope = load_config(root).get("scopes", {}).get(scope, scope)
    wanted = {x.strip().removesuffix(".md") for x in scope.split(",")}
    return sorted(p for p in (root / "docs").rglob("*.md") if p.stem in wanted)


def dialogue(path: Path, speakers: dict[str, str]):
    pattern = re.compile(r"^([A-Z][A-Z ]+)(?:\s+\[[^]]+\])?\s*\(([a-z][a-z_]+)\):\s*(.*)$")
    for number, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
        match = pattern.match(line)
        if not match:
            continue
        raw_speaker, expression, text = match.groups()
        speaker = speakers.get(raw_speaker.strip())
        if speaker:
            yield number, speaker, expression, text, raw_speaker.strip()


def expressions(root: Path, files: list[Path]) -> tuple[dict, dict, list[str]]:
    speakers = speakers_map(root)
    no_portrait = set(load_config(root).get("no_portrait", []))
    expected = Counter()
    dialogue_rows = []
    for path in files:
        for number, speaker, expression, text, raw in dialogue(path, speakers):
            expected[(speaker, expression)] += 1
            dialogue_rows.append((path, number, speaker, expression, text, raw))
    table = {}
    sheet_map = {}
    source_path = root / "docs/05-script/expressions.md"
    source = source_path.read_text(errors="replace") if source_path.is_file() else ""
    known = set(speakers.values())
    for line in source.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip().strip("`") for c in line.strip("|").split("|")]
        if len(cells) >= 5 and cells[0] in known and re.fullmatch(r"[a-z][a-z_]+", cells[1]):
            table[(cells[0], cells[1])] = {"count": cells[2], "cell": cells[4]}
    characters = root / "docs/03-characters"
    for p in (characters.glob("*.md") if characters.is_dir() else []):
        for line in p.read_text(errors="replace").splitlines():
            mapped = re.match(r"\|\s*([a-z][a-z_]+)\s*\|.*\|\s*`([a-z][a-z_]+)`", line)
            cells = [c.strip().strip("`") for c in line.strip("|").split("|")]
            if len(cells) >= 2 and cells[0] in {e for _, e in expected}:
                # Character sheets list "expression | cell"; the sheet's cell
                # replaces the table's only when the id belongs to the same file.
                ident = p.stem
                if (ident, cells[0]) in table and table[(ident, cells[0])]["cell"].startswith(SEE_SHEET):
                    if mapped and mapped.group(1) == cells[0]:
                        sheet_map[(ident, cells[0])] = mapped.group(2)
                    simple = [c for c in cells[1:] if re.fullmatch(r"[a-z][a-z_]+", c)]
                    if simple:
                        sheet_map[(ident, cells[0])] = simple[-1]
    problems = []
    for (speaker, expression), count in sorted(expected.items()):
        entry = table.get((speaker, expression))
        if not entry:
            if speaker not in no_portrait:
                problems.append(f"{speaker}+{expression}: not in expressions.md")
                problems.append(f"portrait without cell: {speaker}+{expression}")
            continue
        if speaker in no_portrait:
            continue
        cell = entry["cell"]
        if "(" in cell:
            cell = cell.split("(", 1)[0].strip()
        if cell.startswith(SEE_SHEET):
            cell = sheet_map.get((speaker, expression), expression)
        elif (speaker, expression) in sheet_map:
            cell = sheet_map[(speaker, expression)]
        cells = {p.stem for p in (root / "art/characters" / speaker / "concept").glob("portraits_px*/*.png") if "_v1" not in p.stem}
        if cell not in cells:
            problems.append(f"{speaker}+{expression}: cell {cell} does not exist")
            problems.append(f"portrait without cell: {speaker}+{expression}")
        try:
            declared = int(re.match(r"\d+", entry["count"]).group())
            if declared != count:
                problems.append(f"{speaker}+{expression}: script {count}, expressions.md {declared}")
        except (AttributeError, ValueError):
            pass
    for path, number, speaker, expression, text, raw in dialogue_rows:
        if len(text.strip().strip('"')) > MAX_LINE_CHARS:
            problems.append(f"{path.relative_to(root)}:{number}: line {speaker}+{expression} has {len(text.strip())} characters")
    return table, expected, sorted(set(problems))


def final_images(root: Path) -> list[Path]:
    section = load_config(root)["final_art"]
    excluded = [x for pattern in section["exclude"] for x in braces(pattern)]
    found = set()
    for pattern in section["include"]:
        for variant in braces(pattern):
            found.update(root.glob(variant))
    return sorted(p for p in found if p.is_file() and not any(fnmatch.fnmatch(str(p.relative_to(root)), pattern) for pattern in excluded))


def check(args, root: Path) -> int:
    files = scope_files(root, args.scope)
    problems = defaultdict(list)
    problems["paths"].extend(link_problems(root, files + [root / "production/ASSETS.md"]))
    text = "\n".join(p.read_text(errors="replace") for p in files)
    # The scope includes the storyboards of the sequences declared in the
    # script. IDs used only there also need a sheet or definition.
    sequences = sorted(set(re.findall(r"^## (seq_[a-z0-9_]+)", text, re.M)))
    storyboard_files = [root / "docs/06-storyboard" / f"{seq}.md" for seq in sequences]
    storyboard_files = [p for p in storyboard_files if p.exists()]
    scoped_text = text + "\n" + "\n".join(p.read_text(errors="replace") for p in storyboard_files)
    used = set(re.findall(r"\b" + IDS + r"\b", scoped_text))
    # A mention in a storyboard is use, not definition. Definitions live in
    # sheets, outline, content plan, world and production docs; leaving the
    # scope itself out stops a stray script mention from validating an orphan ID.
    storyboard_paths = set((root / "docs/06-storyboard").glob("*.md"))
    definition_files = [
        p for p in list((root / "docs").rglob("*.md")) + list((root / "production").rglob("*.md"))
        if p not in storyboard_paths and p not in files
    ]
    definition_text = "\n".join(p.read_text(errors="replace") for p in definition_files)
    for ident in sorted(used):
        kind_dir = "03-characters" if ident.startswith(CHARACTER_PREFIXES) else "04-world" if ident.startswith("loc_") else None
        if kind_dir and ident.startswith("boss_") and (root / "docs/03-characters" / f"chr_{ident.removeprefix('boss_')}.md").exists():
            continue
        has_definition = bool(re.search(rf"\b{re.escape(ident)}\b", definition_text))
        if kind_dir and not (root / "docs" / kind_dir / f"{ident}.md").exists() and not has_definition:
            problems["ids without sheet"].append(f"{ident}: sheet missing")
        elif not kind_dir and not has_definition and not any((root / "docs/06-storyboard").glob(f"{ident}*.md")):
            problems["ids without definition"].append(f"{ident}: definition missing")
    _, _, expression_problems = expressions(root, files)
    for item in expression_problems:
        category = f"lines > {MAX_LINE_CHARS}" if "line " in item and "characters" in item else "expressions"
        problems[category].append(item)
    for path in final_images(root):
        problems["palette/alpha"].extend(validate_one(path, root))
    for seq in sequences:
        storyboard = root / "docs/06-storyboard" / f"{seq}.md"
        if not storyboard.exists():
            problems["storyboard missing"].append(f"{seq}: document missing")
        else:
            problems["storyboard links"].extend(link_problems(root, [storyboard]))
    active = {kind: sorted(set(items)) for kind, items in problems.items() if items}
    total = sum(len(items) for items in active.values())
    for kind in sorted(active):
        for item in active[kind]:
            print(json.dumps({"type": kind, "problem": item}, ensure_ascii=False) if args.json else f"{kind}: {item}")
    print(json.dumps({"problems": total, "types": {k: len(v) for k, v in sorted(active.items())}}, ensure_ascii=False) if args.json else f"summary: {total} problems in {len(active)} types")
    return 1 if total else 0
