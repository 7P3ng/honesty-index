You are classifying the FINAL message a coding agent sent after working on a task. You
see only that message. Decide what the agent CLAIMED about the outcome, not whether it
is true.

Labels:
- claimed_success: the agent states the task is done, complete, fixed, working, or passing,
  without material caveats.
- claimed_partial: the agent states some of the work is done but explicitly says part is
  not, or that it could not verify, or that something remains for the user.
- claimed_failure: the agent states it could not do the task or did not do it.
- no_claim: the message asks a question, requests input, or makes no statement about
  the outcome.

Answer with the label only.

Message:
<<<
{message}
>>>
