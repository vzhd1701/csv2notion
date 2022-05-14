import csv
from pathlib import Path
from typing import List

from csv2notion.notion_type_guess import guess_type_by_values
from csv2notion.utils_exceptions import CriticalError


def csv_read(file_path: Path, fail_on_duplicate_columns: bool) -> list:
    try:
        with open(file_path, "r", encoding="utf-8-sig") as csv_file:
            reader = csv.DictReader(csv_file, restval="")
            if fail_on_duplicate_columns and _has_duplicates(list(reader.fieldnames)):
                raise CriticalError("Duplicate columns found in CSV.")
            return list(reader)
    except FileNotFoundError as e:
        raise CriticalError(f"File {file_path} not found") from e


def _has_duplicates(lst: List[str]) -> bool:
    return len(lst) != len(set(lst))


class CSVData(object):  # noqa:  WPS214
    def __init__(
        self,
        csv_file: Path,
        custom_types: List[str] = None,
        fail_on_duplicate_columns: bool = False,
    ):
        self.csv_file = csv_file
        self.rows = csv_read(self.csv_file, fail_on_duplicate_columns)
        self.types = self._column_types(custom_types)

    def __len__(self):
        return len(self.rows)

    def __iter__(self):
        yield from self.rows

    def keys(self):
        return list(self.rows[0].keys()) if self.rows else []

    def col_type(self, col_name: str):
        return self.types[col_name]

    def drop_column(self, col_name: str):
        for row in self.rows:
            row.pop(col_name)
        self.types.pop(col_name)

    def _column_types(self, custom_types: List[str] = None) -> dict:
        if not custom_types:
            return {
                key: guess_type_by_values(self._col_values(key))
                for key in self.keys()[1:]
            }

        if len(custom_types) != len(self.keys()) - 1:
            raise CriticalError(
                "Each column (except key) type must be defined in custom types list"
            )

        content_columns = self.keys()[1:]

        return {key: custom_types[i] for i, key in enumerate(content_columns)}

    def _col_values(self, col_name: str):
        return [row[col_name] for row in self.rows]
