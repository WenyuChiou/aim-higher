import contextlib
import io
import unittest

from tidepool import __version__
from tidepool.cli import build_parser, main


class HelpTests(unittest.TestCase):
    def test_help_shows_tagline(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            with self.assertRaises(SystemExit):
                main(["--help"])
        self.assertIn("A tiny log viewer for your terminal", out.getvalue())

    def test_version(self):
        self.assertIn(__version__, build_parser().format_usage() + "tidepool " + __version__)


if __name__ == "__main__":
    unittest.main()
