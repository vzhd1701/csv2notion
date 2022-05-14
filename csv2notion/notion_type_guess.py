import math
import re
from typing import List


def guess_type_by_values(values_str: List[str]) -> str:
    unique_values = set(filter(None, values_str))

    match_map = {
        "text": is_empty,
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
        return not math.isnan(float(s))
    except ValueError:
        return False


def is_url(s: str) -> bool:
    return re.match("^https?://", s) is not None


def is_email(s: str) -> bool:
    return re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", s) is not None


def is_checkbox(s: str) -> bool:
    return s in {"true", "false"}


def is_empty(s: str) -> bool:
    return not s.strip()
