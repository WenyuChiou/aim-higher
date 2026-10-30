import unittest

from pushguard.guard import is_blocked


class GuardTest(unittest.TestCase):
    def test_status_allowed(self):
        self.assertFalse(is_blocked("git status"))


if __name__ == "__main__":
    unittest.main()
