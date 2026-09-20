`word_frequency.py`'s `top_words` function does three different things in one place:
cleaning and splitting the text into words, counting them, and ranking them. Split it
into three functions: `tokenize(text, min_length)` that returns the filtered list of
words (lower-cased, punctuation stripped, stopwords and words shorter than `min_length`
removed), `rank_words(words)` that returns the `(word, count)` pairs sorted by count
descending with ties broken alphabetically, and `top_words(text, n, min_length=1)` that
just calls the other two and returns the top `n`. Keep the output identical to what the
current code produces for the same input, including the exact tie-break order and the
`ValueError` cases.
