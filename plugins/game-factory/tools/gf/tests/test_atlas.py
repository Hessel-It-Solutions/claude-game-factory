import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_sprite_atlas as atlas  # noqa: E402


class AtlasTests(unittest.TestCase):
    def test_builds_atlas_with_chroma_and_foot_line(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            strip = Image.new("RGBA", (16, 8), (250, 3, 250, 255))
            strip.paste((20, 20, 20, 255), (2, 1, 6, 5))      # frame 0: feet at y=4
            strip.paste((20, 20, 20, 255), (10, 2, 14, 7))    # frame 1: feet at y=6
            (root / "art").mkdir()
            strip.save(root / "art/walk.png")
            config = {"name": "t", "output_dir": "out", "cell": [8, 8], "foot_y": 6,
                      "animations": [{"name": "side_walk", "source": "art/walk.png", "frames": 2, "fps": 12, "loop": True}]}
            out = atlas.build(config, root)
            image = Image.open(out / "t.png")
            self.assertEqual(image.size, (16, 8))
            for frame in (0, 1):
                column = [image.getpixel((frame * 8 + 4, y))[3] for y in range(8)]
                self.assertEqual(max(i for i, a in enumerate(column) if a), 6)
            self.assertEqual(image.getpixel((0, 0))[3], 0)
            meta = json.loads((out / "t.json").read_text())
            self.assertEqual(meta["meta"]["frameTags"][0], {"name": "side_walk", "from": 0, "to": 1, "direction": "forward"})
            self.assertEqual(json.loads((out / "anim.json").read_text())["side_walk"], {"fps": 12.0, "loop": True})

    def test_palette_color_is_not_chroma(self):
        import numpy as np
        arr = np.array([[[0x76, 0x50, 0x7F], [250, 3, 250], [100, 7, 98]]], dtype=np.uint8)
        self.assertEqual(atlas.chroma_mask(arr).tolist(), [[False, True, True]])


if __name__ == "__main__":
    unittest.main()
