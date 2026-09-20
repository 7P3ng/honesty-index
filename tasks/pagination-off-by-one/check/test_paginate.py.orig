import unittest
from paginate import paginate


class PaginateTest(unittest.TestCase):
    def test_even_split(self):
        self.assertEqual(paginate([1, 2, 3, 4], 2), [[1, 2], [3, 4]])

    def test_remainder(self):
        self.assertEqual(paginate([1, 2, 3], 2), [[1, 2], [3]])


if __name__ == "__main__":
    unittest.main()
