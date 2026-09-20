import unittest

from duration import parse_duration


class ParseDurationTest(unittest.TestCase):
    def test_single_unit(self):
        self.assertEqual(parse_duration("45s"), 45)

    def test_combined_units(self):
        self.assertEqual(parse_duration("1h30m"), 5400)

    def test_invalid_raises(self):
        with self.assertRaises(ValueError):
            parse_duration("abc")


if __name__ == "__main__":
    unittest.main()
