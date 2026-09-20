import unittest

from semver import parse


class ParseTest(unittest.TestCase):
    def test_parses_plain_version(self):
        self.assertEqual(parse("1.2.3"), (1, 2, 3, None))

    def test_parses_prerelease(self):
        self.assertEqual(parse("1.2.3-alpha"), (1, 2, 3, "alpha"))

    def test_invalid_raises(self):
        with self.assertRaises(ValueError):
            parse("1.2")


if __name__ == "__main__":
    unittest.main()
