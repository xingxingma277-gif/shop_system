
def normalize_page(page: int, page_size: int, *, max_page_size: int = 100):
    """
    Normalize pagination params.
    - page: >= 1
    - page_size: 1..max_page_size
    """
    try:
        page_num = int(page)
    except Exception:
        page_num = 1
    if page_num < 1:
        page_num = 1

    try:
        page_size_num = int(page_size)
    except Exception:
        page_size_num = 20
    if page_size_num < 1:
        page_size_num = 1
    if page_size_num > max_page_size:
        page_size_num = max_page_size

    return page_num, page_size_num
