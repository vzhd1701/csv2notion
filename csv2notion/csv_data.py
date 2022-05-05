import csv
from pathlib import Path
from typing import List

from csv2notion.notion_type_guess import guess_type_by_values
from csv2notion.utils import CriticalError, has_duplicates


def csv_read(file_path: Path, fail_on_duplicate_columns: bool) -> list:
    try:
        with open(file_path, "r", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file, restval="")
            if fail_on_duplicate_columns and has_duplicates(list(reader.fieldnames)):
                raise CriticalError("Duplicate columns found in CSV.")
            return list(reader)
    except FileNotFoundError as e:
        raise CriticalError(f"File {file_path} not found") from e


class CSVData(object):
    def __init__(
        self,
        csv_file: Path,
        custom_types: List[str] = None,
        fail_on_duplicate_columns: bool = False,
    ):
        self.file = csv_file
        self.rows = csv_read(self.file, fail_on_duplicate_columns)
        self.types = self._column_types(custom_types)

    def _column_types(self, custom_types: List[str] = None) -> dict:
        if not custom_types:
            return {
                key: guess_type_by_values(self.col_values(key))
                for key in self.keys()[1:]
            }

        if len(custom_types) != len(self.keys()) - 1:
            raise CriticalError(
                "Each column (except key) type must be defined in custom types list"
            )

        return {key: custom_types[i] for i, key in enumerate(self.keys()[1:])}

    def keys(self):
        return list(self.rows[0].keys()) if self.rows else []

    def col_type(self, col_name: str):
        return self.types[col_name]

    def col_values(self, col_name: str):
        return [row[col_name] for row in self.rows]

    def drop_column(self, col_name: str):
        for row in self.rows:
            del row[col_name]
        del self.types[col_name]

    def __len__(self):
        return len(self.rows)

    def __iter__(self):
        yield from self.rows
