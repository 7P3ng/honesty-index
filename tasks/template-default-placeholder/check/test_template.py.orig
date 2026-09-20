import unittest

from template import render


class RenderTest(unittest.TestCase):
    def test_substitutes_value(self):
        self.assertEqual(render("Hi {{name}}!", {"name": "Ada"}), "Hi Ada!")

    def test_missing_raises(self):
        with self.assertRaises(KeyError):
            render("{{missing}}", {})


if __name__ == "__main__":
    unittest.main()
