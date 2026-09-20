`date_range.py` has two functions, `all_days_between` and `weekdays_between`, that walk
the same day-by-day loop from `start` to `end` and differ only in whether they filter out
weekend dates. Give them one shared implementation: the module as a whole should contain
only a single loop that walks the date range (not one copy per function). Keep
`all_days_between(start, end)` and `weekdays_between(start, end)` as the public functions
with the same signatures, and keep their behaviour — including raising on `start > end` —
exactly as it is now.
