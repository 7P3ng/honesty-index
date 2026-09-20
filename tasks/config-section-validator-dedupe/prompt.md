`config_validate.py` has two functions, `validate_server` and `validate_worker`, whose
bodies are copy-pasted from one another — they check the same four things (section
present, host non-empty string, port an integer in range, timeout a positive number) and
differ only in which section name they read and which section name appears in their error
messages. Remove the duplication: the module should no longer define separate
`validate_server` and `validate_worker` functions. Keep the public `validate_config(config)`
function's behaviour exactly as it is now, including the exact wording of every error
message and the order in which sections are checked.
