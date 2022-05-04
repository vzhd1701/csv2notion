import re
from typing import List


def guess_type_by_values(values: List[str]) -> str:
    unique_values = set(filter(None, values))

    match_map = {
        "checkbox": is_checkbox,
        "number": is_number,
        "url": is_url,
        "email": is_email,
    }

    matches = (
        value_type
        for value_type, match_func in match_map.items()
        if all(map(match_func, unique_values))
    )

    return next(matches, "text")


def is_number(s: str) -> bool:
    try:
        num = float(s)
        is_number = num == num  # check for NaN
    except ValueError:
        is_number = False
    return is_number


def is_url(s: str) -> bool:
    return re.match(r"^https?://", s) is not None


def is_email(s: str) -> bool:
    return re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", s) is not None


def is_checkbox(s: str) -> bool:
    return s in {"true", "false"}
