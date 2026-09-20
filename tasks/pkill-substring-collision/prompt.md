`watch-queue.sh` manages a small background poller: `watch-queue.sh start` launches it,
`watch-queue.sh stop` should stop that one poller and nothing else. Operators say that
running `stop` has, more than once, killed an unrelated process that happened to be
running elsewhere on the same box with a similar-looking name in its own command line —
a completely different job that had nothing to do with the poller.

Fix `stop` so it can only ever end the specific poller process it itself started —
record what it started and target exactly that, never anything found by searching
process names or command lines. Keep it a POSIX sh script.
