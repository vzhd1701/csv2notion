import random
import string
from typing import Iterable, List, Set


def rand_id(id_length: int) -> str:
    rand_chars = random.sample(string.digits + string.ascii_letters, id_length)
    return "".join(rand_chars)


def rand_id_list(size: int, id_length: int) -> List[str]:
    """Generate a list of guaranteed unique ids"""

    rand_ids: Set[str] = set()

    while len(rand_ids) < size:
        rand_ids.add(rand_id(id_length))

    return list(rand_ids)


def rand_id_unique(size: int, existing_ids: Iterable[str]) -> str:
    existing_ids = set(existing_ids)

    while True:
        new_id = rand_id(size)
        if new_id not in existing_ids:
            return new_id
