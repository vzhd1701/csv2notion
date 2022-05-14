from typing import List


def split_str(s: str, sep: str = ",") -> List[str]:
    return [v.strip() for v in s.split(sep) if v.strip()]
