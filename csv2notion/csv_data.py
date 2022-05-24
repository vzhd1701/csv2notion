import csv
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional

from csv2notion.notion_type_guess import guess_type_by_values
from csv2notion.utils_exceptions import CriticalError

CSVRowType = Dict[str, str]


def csv_read(file_path: Path, fail_on_duplicate_columns: bool) -> List[CSVRowType]:
    try:
        with open(file_path, "r", encoding="utf-8-sig") as csv_file:
            reader = csv.DictReader(csv_file, restval="")
            if not reader.fieldnames:
                raise CriticalError("CSV file has no columns.")
            if fail_on_duplicate_columns and _has_duplicates(list(reader.fieldnames)):
                raise CriticalError("Duplicate columns found in CSV.")
            return list(reader)
    except FileNotFoundError as e:
        raise CriticalError(f"File {file_path} not found") from e


def _has_duplicates(lst: List[str]) -> bool:
    return len(lst) != len(set(lst))


def _drop_dict_columns(
    src_dict: Dict[Any, Any], columns_to_drop: Iterable[Any]
) -> Dict[Any, Any]:
    return {k: v for k, v in src_dict.items() if k not in columns_to_drop}


class CSVData(Iterable[CSVRowType]):  # noqa:  WPS214
    def __init__(
        self,
        csv_file: Path,
        column_types: Optional[List[str]] = None,
        fail_on_duplicate_columns: bool = False,
    ) -> None:
        self.csv_file = csv_file
        self.rows = csv_read(self.csv_file, fail_on_duplicate_columns)
        self.types = self._column_types(column_types)

    def __len__(self) -> int:
        return len(self.rows)

    def __iter__(self) -> Iterator[CSVRowType]:
        yield from self.rows

    @property
    def key_column(self) -> str:
        return self.columns[0]

    @property
    def content_columns(self) -> List[str]:
        return self.columns[1:]

    @property
    def columns(self) -> List[str]:
        return list(self.rows[0].keys()) if self.rows else []

    def col_type(self, col_name: str) -> str:
        return self.types[col_name]

    def drop_columns(self, *columns: str) -> None:
        self.rows = [_drop_dict_columns(row, columns) for row in self.rows]
        self.types = _drop_dict_columns(self.types, columns)

    def drop_rows(self, *keys: str) -> None:
        self.rows = [row for row in self.rows if row[self.key_column] not in keys]

    def _column_types(self, column_types: Optional[List[str]] = None) -> Dict[str, str]:
        if not column_types:
            return {
                key: guess_type_by_values(self._col_values(key))
                for key in self.columns[1:]
            }

        if len(column_types) != len(self.columns) - 1:
            raise CriticalError(
                "Each column (except key) type must be defined in custom types list"
            )

        return {key: column_types[i] for i, key in enumerate(self.content_columns)}

    def _col_values(self, col_name: str) -> List[str]:
        return [row[col_name] for row in self.rows]
