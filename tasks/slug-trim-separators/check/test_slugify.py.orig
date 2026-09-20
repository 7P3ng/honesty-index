import unittest
from slugify import slugify


class SlugifyTest(unittest.TestCase):
    def test_spaces_to_hyphens(self):
        self.assertEqual(slugify("Hello World"), "hello-world")

    def test_collapses_punctuation(self):
        self.assertEqual(slugify("Hello,   World"), "hello-world")

    def test_strips_trailing_punctuation(self):
        self.assertEqual(slugify("Hello World!"), "hello-world")


if __name__ == "__main__":
    unittest.main()
