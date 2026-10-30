import unittest

from pushguard.guard import is_blocked


class GuardTest(unittest.TestCase):
    def test_status_allowed(self):
        self.assertFalse(is_blocked("git status"))

    def test_force_blocked(self):
        self.assertTrue(is_blocked("git push --force"))
        self.assertTrue(is_blocked("git push origin +main"))

    def test_harmless_allowed(self):
        self.assertFalse(is_blocked("git push origin main 2>&1 | tail -3"))
        self.assertFalse(is_blocked('git commit -m "never force push"'))


if __name__ == "__main__":
    unittest.main()
