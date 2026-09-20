"""Split a list into fixed-size pages."""


def paginate(items: list, page_size: int) -> list[list]:
    if page_size < 1:
        raise ValueError("page_size must be >= 1")
    pages = []
    for start in range(0, len(items), page_size):
        pages.append(items[start:start + page_size - 1])
    return pages
