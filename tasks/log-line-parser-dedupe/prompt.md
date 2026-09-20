`parser.py` has two nearly-identical helper functions, `parse_info_line` and
`parse_error_line`. They both parse a timestamp and a message and differ only in the
level label they attach to the result. Collapse them into a single shared
implementation: the module should no longer define separate `parse_info_line` and
`parse_error_line` functions. Keep the public `parse_line(line)` function's signature
and behaviour exactly as they are now, including how it handles malformed lines,
unknown levels, and empty or whitespace-only messages.
