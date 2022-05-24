import logging
from typing import Callable, Dict, Iterable, List, Set

from csv2notion.csv_data import CSVData
from csv2notion.notion_db import NotionDB
from csv2notion.utils_exceptions import NotionError
from csv2notion.utils_static import UNSETTABLE_TYPES, ConversionRules

logger = logging.getLogger(__name__)


class NotionPreparator(object):  # noqa: WPS214
    def __init__(
        self, db: NotionDB, csv: CSVData, conversion_rules: ConversionRules
    ) -> None:
        self.db = db
        self.csv = csv
        self.rules = conversion_rules

    def prepare(self) -> None:
        steps: List[Callable[[], None]] = [
            self._validate_image_column,
            self._validate_image_caption_column,
            self._validate_icon_column,
            self._validate_mandatory_columns,
            self._handle_merge,
            self._handle_missing_columns,
            self._handle_unsupported_columns,
            self._handle_inaccessible_relations,
        ]

        if self.rules.fail_on_relation_duplicates:
            steps += [self._validate_relations_duplicates]

        if self.rules.fail_on_duplicates:
            steps += [self._validate_csv_duplicates, self._validate_db_duplicates]

        steps += [self._validate_columns_left]

        for step in steps:
            step()

    def _validate_image_column(self) -> None:
        if self.rules.image_column is None:
            return

        if self.rules.image_column not in self.csv.columns:
            raise NotionError(
                f"Image column '{self.rules.image_column}' not found in csv file."
            )

    def _validate_image_caption_column(self) -> None:
        if self.rules.image_caption_column is None:
            return

        if self.rules.image_caption_column not in self.csv.columns:
            raise NotionError(
                f"Image caption column '{self.rules.image_caption_column}'"
                f" not found in csv file."
            )

    def _validate_icon_column(self) -> None:
        if self.rules.icon_column is None:
            return

        if self.rules.icon_column not in self.csv.columns:
            raise NotionError(
                f"Icon column '{self.rules.icon_column}' not found in csv file."
            )

    def _validate_mandatory_columns(self) -> None:
        mandatory_columns = set(self.rules.mandatory_column)
        csv_columns = set(self.csv.columns)

        missing_columns = mandatory_columns - csv_columns
        if missing_columns:
            raise NotionError(
                f"Mandatory column(s) {missing_columns} not found in csv file."
            )

    def _handle_merge(self) -> None:
        if self.rules.merge:
            self._validate_key_column(self.csv.key_column)

            if self.rules.merge_only_column:
                self._vlaidate_merge_only_columns()
                ignored_columns = set(self.csv.content_columns) - set(
                    self.rules.merge_only_column
                )
                self.csv.drop_columns(*ignored_columns)

            if self.rules.merge_skip_new:
                self.csv.drop_rows(*self._get_new_row_keys())

    def _handle_missing_columns(self) -> None:
        missing_columns = self._get_missing_columns()
        if missing_columns:
            warn_text = f"CSV columns missing from Notion DB: {missing_columns}"

            if self.rules.add_missing_columns:
                logger.info(f"Adding missing columns to the DB: {missing_columns}")
                self._add_columns(missing_columns)
            elif self.rules.fail_on_missing_columns:
                raise NotionError(warn_text)
            else:
                logger.warning(warn_text)
                self.csv.drop_columns(*missing_columns)

    def _handle_unsupported_columns(self) -> None:
        unsupported_columns = self._get_unsupported_columns()
        if unsupported_columns:
            warn_text = (
                f"Cannot set value to these columns"
                f" due to unsupported type: {unsupported_columns}"
            )

            if self.rules.fail_on_unsettable_columns:
                raise NotionError(warn_text)
            else:
                logger.warning(warn_text)

            self.csv.drop_columns(*unsupported_columns)

    def _handle_inaccessible_relations(self) -> None:
        inaccessible_relations = [
            r_col for r_col, r in self.db.relations.items() if not r.is_accessible()
        ]

        if inaccessible_relations:
            warn_text = f"Columns with inaccessible relations: {inaccessible_relations}"

            if self.rules.fail_on_inaccessible_relations:
                raise NotionError(warn_text)
            else:
                logger.warning(warn_text)

            self.csv.drop_columns(*inaccessible_relations)

    def _validate_relations_duplicates(self) -> None:
        for relation_key, relation in self._present_relations().items():
            if relation.has_duplicates():
                raise NotionError(
                    f"Collection DB '{relation.name}' used in '{relation_key}'"
                    f" relation column has duplicates which"
                    f" cannot be unambiguously mapped with CSV data."
                )

    def _validate_db_duplicates(self) -> None:
        if self.db.has_duplicates():
            raise NotionError("Duplicate values found in DB key column.")

    def _validate_key_column(self, key_column: str) -> None:
        if key_column not in self.db.columns:
            raise NotionError(f"Key column '{key_column}' does not exist in Notion DB.")
        if self.db.columns[key_column]["type"] != "title":
            raise NotionError(f"Notion DB column '{key_column}' is not a key column.")

    def _vlaidate_merge_only_columns(self) -> None:
        merge_only_columns = set(self.rules.merge_only_column)
        csv_columns = set(self.csv.columns)

        missing_columns = merge_only_columns - csv_columns
        if missing_columns:
            raise NotionError(
                f"Merge only column(s) {missing_columns} not found in csv file."
            )

    def _validate_csv_duplicates(self) -> None:
        csv_keys = [v[self.csv.key_column] for v in self.csv]
        if len(set(csv_keys)) != len(csv_keys):
            raise NotionError("Duplicate values found in first column in CSV.")

    def _validate_columns_left(self) -> None:
        if not self.csv.columns:
            raise NotionError("No columns left after validation, nothing to upload.")

    def _add_columns(self, columns: Iterable[str]) -> None:
        for column in columns:
            self.db.add_column(column, self.csv.col_type(column))

    def _present_columns(self) -> List[str]:
        return [k for k in self.csv.columns if k in self.db.columns]

    def _present_relations(self) -> Dict[str, NotionDB]:
        relations = self.db.relations.items()
        return {k: v for k, v in relations if k in self.csv.columns}

    def _get_unsupported_columns(self) -> List[str]:
        return [
            k
            for k in self._present_columns()
            if self.db.columns[k]["type"] in UNSETTABLE_TYPES
        ]

    def _get_missing_columns(self) -> Set[str]:
        csv_columns = set(self.csv.columns)
        db_columns = set(self.db.columns)

        if self.rules.image_column and not self.rules.image_column_keep:
            csv_columns -= {self.rules.image_column}

        if self.rules.image_caption_column:
            if not self.rules.image_caption_column_keep:
                csv_columns -= {self.rules.image_caption_column}

        if self.rules.icon_column and not self.rules.icon_column_keep:
            csv_columns -= {self.rules.icon_column}

        return csv_columns - db_columns

    def _get_new_row_keys(self) -> Set[str]:
        csv_keys = {v[self.csv.key_column] for v in self.csv}
        db_keys = set(self.db.rows)

        return csv_keys - db_keys
