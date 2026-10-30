import os
import tempfile
import unittest

from notecat.cli import load_notes


class NotecatTests(unittest.TestCase):
    def test_load_notes_skips_blank_and_comments(self):
        fd, path = tempfile.mkstemp(suffix=".txt")
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write("  one \n\n# comment\ntwo\n")
        try:
            self.assertEqual(load_notes(path), ["one", "two"])
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
