import tempfile
import unittest
from pathlib import Path

from helpers import run_gf


class CommandCoverage(unittest.TestCase):
    def test_every_command_has_entrypoint(self):
        commands = ["post", "validate", "cut", "board", "codex", "assets", "budget", "state", "check", "context"]
        with tempfile.TemporaryDirectory() as td:
            for command in commands:
                result = run_gf(Path(td), command, "--help")
                self.assertEqual(result.returncode, 0, command)
                self.assertIn("usage:", result.stdout.lower(), command)


if __name__ == "__main__":
    unittest.main()
