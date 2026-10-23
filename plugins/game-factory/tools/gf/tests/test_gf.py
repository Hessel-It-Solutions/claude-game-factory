import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from helpers import make_project, run_gf


def sheet_image(size, boxes):
    image = Image.new("RGBA", size, (255, 0, 255, 255))
    for box, color in boxes:
        image.paste(color, box)
    return image


class GfTests(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.d = Path(self._td.name)
        self.root = make_project(self.d / "repo")

    def tearDown(self):
        self._td.cleanup()

    def test_post_and_validate_synthetic(self):
        d = self.d
        image = Image.new("RGBA", (8, 8), (255, 0, 255, 255))
        for y in range(2, 6):
            for x in range(2, 6):
                image.putpixel((x, y), (22, 20, 18, 255))
        image.save(d / "in.png")
        p = run_gf(self.root, "post", d / "in.png", d / "out.png", "--width", "4", "--chroma", "magenta")
        self.assertEqual(p.returncode, 0, p.stderr + p.stdout)
        out = Image.open(d / "out.png")
        self.assertEqual(out.size, (4, 4))
        self.assertEqual(out.getpixel((0, 0))[3], 0)
        self.assertEqual(out.getpixel((2, 2))[3], 255)
        v = run_gf(self.root, "validate", d / "out.png", "--json")
        self.assertEqual(v.returncode, 0, v.stderr + v.stdout)

    def test_validate_flags_color_outside_palette(self):
        Image.new("RGBA", (2, 2), (10, 200, 30, 255)).save(self.d / "bad.png")
        v = run_gf(self.root, "validate", self.d / "bad.png")
        self.assertEqual(v.returncode, 1)
        self.assertIn("outside the palette", v.stdout)

    def test_cut_post_chroma_preserves_alpha_with_width(self):
        d = self.d
        sheet_image((8, 8), [((2, 2, 6, 6), (22, 20, 18, 255))]).save(d / "sheet.png")
        out = d / "cells"
        p = run_gf(self.root, "cut", d / "sheet.png", "--grid", "1x1", "--post", "--post-width", "4", "--post-chroma", "magenta", out)
        self.assertEqual(p.returncode, 0, p.stderr + p.stdout)
        result = Image.open(out / "01.png")
        self.assertEqual(result.getpixel((0, 0))[3], 0)
        self.assertEqual(result.getpixel((2, 2))[3], 255)

    def test_cut_grid_and_board(self):
        d = self.d; sheet = d / "sheet.png"
        sheet_image((8, 4), [((0, 0, 4, 4), (22, 20, 18, 255)), ((4, 0, 8, 4), (176, 134, 69, 255))]).save(sheet)
        out = d / "cells"
        p = run_gf(self.root, "cut", sheet, "--grid", "2x1", "--names", "01,02", out)
        self.assertEqual(p.returncode, 0, p.stderr + p.stdout)
        self.assertTrue((out / "01.png").exists())
        b = run_gf(self.root, "board", out, "--labels")
        self.assertEqual(b.returncode, 0, b.stderr + b.stdout)
        self.assertTrue((out / "board.png").exists())

    def test_codex_dry_run_does_not_write_output(self):
        d = self.d; ref = d / "ref.png"; out = d / "out.png"; ref.touch()
        jobs = d / "jobs.json"; jobs.write_text(json.dumps([{"id": "j1", "prompt": "test", "refs": [str(ref)], "out": str(out)}]))
        p = run_gf(self.root, "codex", jobs, "--dry-run")
        self.assertEqual(p.returncode, 0, p.stderr + p.stdout)
        self.assertIn("--provider codex", p.stdout)
        self.assertFalse(out.exists())

    def test_state_and_budget(self):
        s = run_gf(self.root, "state", "Current wave", "W2")
        self.assertEqual(s.returncode, 0, s.stderr + s.stdout)
        self.assertIn("Current wave: W2", (self.root / "production/STATE.md").read_text())
        b = run_gf(self.root, "budget", "W2", "1000", "900", "--cap", "150", "--notes", "test")
        self.assertEqual(b.returncode, 0, b.stderr + b.stdout)
        self.assertIn("| W2 | 1000 | up to 150 | 100 | 900 | test |", (self.root / "production/BUDGET.md").read_text())
        over = run_gf(self.root, "budget", "W3", "1000", "100", "--cap", "150", "--notes", "x")
        self.assertEqual(over.returncode, 2)

    def test_assets_add_and_check(self):
        art = self.root / "art/characters/chr_hero/base"; art.mkdir(parents=True)
        Image.new("RGBA", (2, 2), (22, 20, 18, 255)).save(art / "base.png")
        row = {"asset_id": "chr_hero_base", "type": "image", "file": "art/characters/chr_hero/base/base.png", "model": "m", "task_id": "t", "credits": "5", "status": "approved", "wave": "W3"}
        jsonl = self.root / "production/w3.assets.jsonl"; jsonl.write_text(json.dumps(row) + "\n")
        a = run_gf(self.root, "assets", "add", "production/w3.assets.jsonl")
        self.assertEqual(a.returncode, 0, a.stderr + a.stdout)
        c = run_gf(self.root, "assets", "check")
        self.assertEqual(c.returncode, 0, c.stdout)
        self.assertIn("summary: 1 assets, 0 problems", c.stdout)

    def test_check_on_empty_project(self):
        c = run_gf(self.root, "check")
        self.assertIn("summary:", c.stdout)


if __name__ == "__main__":
    unittest.main()
