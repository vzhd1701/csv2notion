import logging
import random
import string
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable, List, Optional

ALLOWED_TYPES = frozenset(
    [
        "checkbox",
        "date",
        "multi_select",
        "select",
        "number",
        "email",
        "phone_number",
        "url",
        "text",
    ]
)


class CriticalError(Exception):
    pass


class NotionError(Exception):
    pass


def setup_logging(is_verbose: bool = False, log_file: Optional[Path] = None) -> None:
    logging.basicConfig(format="%(levelname)s: %(message)s")

    logging.getLogger("csv2notion").setLevel(
        logging.DEBUG if is_verbose else logging.INFO
    )

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)-8.8s] %(message)s")
        )
        logging.getLogger("csv2notion").addHandler(file_handler)


def process_iter(worker, tasks, max_workers):
    if max_workers == 1:
        for task in tasks:
            yield worker(task)
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(worker, t) for t in tasks]

            for future in as_completed(futures):
                yield future.result()


def rand_id(id_length):
    rand_chars = random.sample(string.digits + string.ascii_letters, id_length)
    return "".join(rand_chars)


def rand_id_list(size, id_length):
    """Generate a list of guaranteed unique ids"""

    rand_ids = set()

    while len(rand_ids) < size:
        rand_ids.add(rand_id(id_length))

    return list(rand_ids)


def rand_id_unique(size: int, existing_ids: Iterable[str]):
    existing_ids = set(existing_ids)

    while True:
        new_id = rand_id(size)
        if new_id not in existing_ids:
            return new_id


def has_duplicates(lst: List[str]) -> bool:
    return len(lst) != len(set(lst))


def split_str(s: str, sep: str = ",") -> List[str]:
    return [v.strip() for v in s.split(sep) if v.strip()]
