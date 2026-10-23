import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from gf.assets import references
from gf.check import braces, check, derive_speakers
from helpers import make_project


def run_check(root: Path, scope="pilot"):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        code = check(SimpleNamespace(scope=scope, json=False), root)
    return code, output.getvalue()


class ContinuityFixtures(unittest.TestCase):
    def test_check_fixture_covers_orphan_long_link_and_braces(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_project(Path(td), palette="000000\n", speakers={"HERO": "chr_hero"})
            (root / "docs/05-script/ch01.md").write_text(
                "## seq_01_fields\nCast: chr_missing\n\n"
                "HERO (neutral): " + "x " * 45 + "\n"
                "HERO (ecstatic): Short line\n"
                "Link [broken](../art/missing_{a,b}.png)\n"
            )
            (root / "docs/05-script/ch02.md").write_text("")
            (root / "docs/05-script/expressions.md").write_text(
                "| chr_id | Expression | Lines | Description | Cell |\n"
                "|---|---|---|---|---|\n| chr_hero | neutral | 1 | x | neutral |\n"
            )
            (root / "docs/06-storyboard/seq_01_fields.md").write_text(
                "Character cited only in the storyboard: chr_ghost_kid\n"
                "![x](../../art/storyboard/seq_01_fields/01.png)\n"
            )
            code, text = run_check(root, scope="ch01,ch02")
            self.assertEqual(code, 1)
            self.assertIn("ids without sheet", text)
            self.assertIn("chr_ghost_kid: sheet missing", text)
            self.assertIn("lines > 80", text)
            self.assertIn("chr_hero+ecstatic: not in expressions.md", text)
            self.assertIn("portrait without cell: chr_hero+ecstatic", text)
            self.assertIn("paths", text)
            self.assertIn("summary:", text)
            self.assertEqual(braces("x_{a,b}.png"), ["x_a.png", "x_b.png"])

    def test_named_scope_from_config(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_project(Path(td))
            import json
            cfg = root / "tools/gf/gf.json"
            data = json.loads(cfg.read_text()); data["scopes"] = {"pilot": "ch01,ch02"}; cfg.write_text(json.dumps(data))
            (root / "docs/05-script/ch01.md").write_text("## seq_a\nchr_nobody\n")
            code, text = run_check(root, scope="pilot")
            self.assertEqual(code, 1)
            self.assertIn("chr_nobody: sheet missing", text)

    def test_speakers_derived_from_character_sheets(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_project(Path(td))
            (root / "docs/03-characters/chr_hero_young.md").write_text("# hero\n")
            speakers = derive_speakers(root)
            self.assertEqual(speakers["HERO"], "chr_hero_young")
            self.assertEqual(speakers["HERO YOUNG"], "chr_hero_young")

    def test_default_config_has_no_speakers(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_project(Path(td))
            (root / "docs/05-script/ch01.md").write_text("## seq_a\nSOMEONE (neutral): hi\n")
            (root / "docs/05-script/expressions.md").write_text("# Expressions\n")
            code, text = run_check(root, scope="ch01")
            self.assertNotIn("expressions:", text)

    def test_check_summary_counts_only_nonempty_types(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_project(Path(td))
            (root / "docs/05-script/ch01.md").write_text("")
            (root / "docs/05-script/ch02.md").write_text("")
            (root / "docs/05-script/expressions.md").write_text("# Expressions\n")
            code, text = run_check(root, scope="ch01,ch02")
            self.assertEqual(code, 0)
            self.assertIn("summary: 0 problems in 0 types", text)

    def test_assets_resolves_relative_glob_and_status(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); folder = root / "art/characters/npc_sheep/base"; folder.mkdir(parents=True)
            (folder / "base_light_front.png").touch()
            row = {"asset_id": "npc_sheep_base", "file": "art/characters/npc_sheep/base/base_{light,dark}_{front,side}.png"}
            found = {p.name for _, p in references(row["file"], root, row) if p}
            self.assertIn("base_light_front.png", found)


if __name__ == "__main__":
    unittest.main()
