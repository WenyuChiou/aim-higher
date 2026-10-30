import contextlib
import io
import os
import tempfile
import unittest

from logstat.cli import main
from logstat.grep import grep_lines
from logstat.reader import read_all
from logstat.tail import tail_lines

LINES = [
    "2026-01-01T00:00:00 INFO service started",
    "2026-01-01T00:00:01 INFO listening on port 80",
    "2026-01-01T00:00:02 WARN slow request",
    "2026-01-01T00:00:03 ERROR upstream failed",
    "2026-01-01T00:00:04 INFO done",
]


class LogstatTests(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".log")
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(LINES) + "\n")

    def tearDown(self):
        os.remove(self.path)

    def run_cli(self, *argv):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = main(list(argv))
        self.assertEqual(code, 0)
        return buf.getvalue().splitlines()

    def test_read_all(self):
        self.assertEqual(list(read_all(self.path)), LINES)

    def test_summary(self):
        self.assertEqual(
            self.run_cli("summary", self.path), ["INFO 3", "WARN 1", "ERROR 1"]
        )

    def test_tail(self):
        self.assertEqual(tail_lines(self.path, 2), LINES[-2:])
        self.assertEqual(self.run_cli("tail", self.path, "2"), LINES[-2:])
        self.assertEqual(tail_lines(self.path, 0), [])
        self.assertEqual(tail_lines(self.path, 99), LINES)

    def test_grep(self):
        self.assertEqual(
            self.run_cli("grep", self.path, "ERROR"), ["4: " + LINES[3]]
        )
        self.assertEqual(list(grep_lines(self.path, "INFO"))[0], (1, LINES[0]))


if __name__ == "__main__":
    unittest.main()
