import unittest

from dedup import unique_lines


class UniqueLinesTest(unittest.TestCase):
    def test_removes_exact_duplicates(self):
        self.assertEqual(unique_lines("a\na\nb\na"), ["a", "b"])

    def test_keeps_distinct_whitespace_by_default(self):
        self.assertEqual(unique_lines("a \na"), ["a ", "a"])


if __name__ == "__main__":
    unittest.main()
