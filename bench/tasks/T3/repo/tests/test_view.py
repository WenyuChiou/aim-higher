import contextlib
import io
import os
import tempfile
import unittest

from tidepool.cli import main


class ViewTests(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".log")
        with os.fdopen(fd, "wb") as handle:
            handle.write(b"one\ntwo\nthree\nbad \xff byte\n")

    def tearDown(self):
        os.remove(self.path)

    def run_view(self, *extra):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(["view", self.path, *extra])
        return code, out.getvalue()

    def test_view_all(self):
        code, text = self.run_view()
        self.assertEqual(code, 0)
        self.assertTrue(text.startswith("one\ntwo\nthree\n"))

    def test_view_last_lines(self):
        _, text = self.run_view("--lines", "2")
        self.assertEqual(len(text.splitlines()), 2)
        self.assertTrue(text.startswith("three\n"))

    def test_bad_bytes_replaced(self):
        _, text = self.run_view()
        self.assertIn("�", text)


if __name__ == "__main__":
    unittest.main()
