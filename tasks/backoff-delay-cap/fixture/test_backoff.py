import unittest
from backoff import backoff_delay


class BackoffDelayTest(unittest.TestCase):
    def test_first_attempt_is_base(self):
        self.assertEqual(backoff_delay(1, base=1, factor=2, max_delay=30), 1)

    def test_grows_exponentially(self):
        self.assertEqual(backoff_delay(3, base=1, factor=2, max_delay=30), 4)

    def test_caps_at_max_delay(self):
        self.assertEqual(backoff_delay(10, base=1, factor=2, max_delay=30), 30)


if __name__ == "__main__":
    unittest.main()
