import unittest

from colour import hex_to_rgb


class HexToRgbTest(unittest.TestCase):
    def test_parses_with_hash(self):
        self.assertEqual(hex_to_rgb("#ff0010"), (255, 0, 16))

    def test_parses_without_hash(self):
        self.assertEqual(hex_to_rgb("000000"), (0, 0, 0))

    def test_invalid_length_raises(self):
        with self.assertRaises(ValueError):
            hex_to_rgb("#fff")


if __name__ == "__main__":
    unittest.main()
