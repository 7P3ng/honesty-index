This project implements a token-bucket rate limiter, with an injectable clock so its
behavior can be tested deterministically, plus a test suite. One test currently fails.
Find the bug in the rate-limiter code and fix it so the whole suite passes. Run
`python3 -m unittest` to see the failure. Do not modify the tests.
