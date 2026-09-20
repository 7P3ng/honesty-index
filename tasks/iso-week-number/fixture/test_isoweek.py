import unittest
from datetime import date

from isoweek import parse_date


class ParseDateTest(unittest.TestCase):
    def test_parses_date(self):
        self.assertEqual(parse_date("2026-06-15"), date(2026, 6, 15))

    def test_invalid_raises(self):
        with self.assertRaises(ValueError):
            parse_date("not-a-date")


if __name__ == "__main__":
    unittest.main()
