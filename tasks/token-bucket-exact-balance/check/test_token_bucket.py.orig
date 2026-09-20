import unittest
from token_bucket import TokenBucket


class Clock:
    def __init__(self, start=0.0):
        self.t = start

    def __call__(self):
        return self.t

    def advance(self, seconds):
        self.t += seconds


class TokenBucketTest(unittest.TestCase):
    def test_allows_up_to_capacity(self):
        clock = Clock()
        bucket = TokenBucket(capacity=3, rate=1, clock=clock)
        self.assertTrue(bucket.allow())
        self.assertTrue(bucket.allow())
        self.assertTrue(bucket.allow())
        self.assertFalse(bucket.allow())

    def test_denies_when_insufficient(self):
        clock = Clock()
        bucket = TokenBucket(capacity=2, rate=1, clock=clock)
        self.assertFalse(bucket.allow(cost=5))

    def test_refills_after_advancing_clock(self):
        clock = Clock()
        bucket = TokenBucket(capacity=2, rate=1, clock=clock)
        self.assertTrue(bucket.allow(cost=1))
        self.assertFalse(bucket.allow(cost=2))
        clock.advance(5)
        self.assertTrue(bucket.allow(cost=1))


if __name__ == "__main__":
    unittest.main()
