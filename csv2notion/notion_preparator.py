import logging
from typing import Iterable, List, Set

from csv2notion.csv_data import CSVData
from csv2notion.notion_db import NotionDB
from csv2notion.utils import UNSETTABLE_TYPES, NotionError

logger = logging.getLogger(__name__)


class NotionPreparator(object):
    def __init__(self, db: NotionDB, csv: CSVData, conversion_rules: dict) -> None:
        self.db = db
        self.csv = csv
        self.rules = conversion_rules

    def prepare(self) -> None:
        self._validate_image_column()
        self._validate_image_caption_column()
        self._validate_icon_column()
        self._vlaidate_mandatory_columns()

        if self.rules["is_merge"]:
            self._validate_key_column(self.csv.keys()[0])

            if self.rules["merge_only_columns"]:
                self._vlaidate_merge_only_columns()
                ignored_columns = set(self.csv.keys()[1:]) - set(
                    self.rules["merge_only_columns"]
                )
                self._drop_columns(ignored_columns)

        missing_columns = self._get_missing_columns()
        if missing_columns:
            warn_text = f"CSV columns missing from Notion DB: {missing_columns}"

            if self.rules["missing_columns_action"] == "add":
                logger.info(f"Adding missing columns to the DB: {missing_columns}")
                self._add_columns(missing_columns)
            elif self.rules["missing_columns_action"] == "fail":
                raise NotionError(warn_text)
            else:
                logger.warning(warn_text)

        unsupported_columns = self._get_unsupported_columns()
        if unsupported_columns:
            warn_text = (
                f"Cannot set value to these columns"
                f" due to unsupported type: {unsupported_columns}"
            )

            if self.rules["fail_on_unsupported_columns"]:
                raise NotionError(warn_text)
            else:
                logger.warning(warn_text)

            self._drop_columns(unsupported_columns)

        inaccessible_relations = self._get_inaccessible_relations()
        if inaccessible_relations:
            warn_text = f"Columns with inaccessible relations: {inaccessible_relations}"

            if self.rules["fail_on_inaccessible_relations"]:
                raise NotionError(warn_text)
            else:
                logger.warning(warn_text)

            self._drop_columns(inaccessible_relations)

        if self.rules["fail_on_relation_duplicates"]:
            self._validate_relations_duplicates()

        if self.rules["fail_on_duplicates"]:
            self._validate_csv_duplicates()
            self._validate_db_duplicates()

    def _add_columns(self, columns: Iterable[str]) -> None:
        for column in columns:
            self.db.add_column(column, self.csv.col_type(column))

    def _drop_columns(self, columns: Iterable[str]) -> None:
        for column in columns:
            self.csv.drop_column(column)

    def _get_unsupported_columns(self) -> List[str]:
        return [
            k
            for k in self.csv.keys()
            if k in self.db.schema and self.db.schema[k]["type"] in UNSETTABLE_TYPES
        ]

    def _get_inaccessible_relations(self) -> List[str]:
        relation_keys = [
            s_name
            for s_name, s in self.db.schema.items()
            if s["type"] == "relation" and s_name in self.csv.keys()
        ]

        inaccessible_relations = []

        for relation_key in relation_keys:
            try:
                self.db.relation(relation_key)
            except KeyError:
                inaccessible_relations.append(relation_key)

        return inaccessible_relations

    def _get_missing_columns(self) -> Set[str]:
        csv_keys = set(self.csv.keys())
        schema_keys = set(self.db.schema)

        if self.rules["image_column"] and not self.rules["image_column_keep"]:
            csv_keys -= {self.rules["image_column"]}

        if (
            self.rules["image_caption_column"]
            and not self.rules["image_caption_column_keep"]
        ):
            csv_keys -= {self.rules["image_caption_column"]}

        if self.rules["icon_column"] and not self.rules["icon_column_keep"]:
            csv_keys -= {self.rules["icon_column"]}

        return csv_keys - schema_keys

    def _validate_db_duplicates(self) -> None:
        if self.db.is_db_has_duplicates():
            raise NotionError("Duplicate values found in DB key column.")

    def _validate_relations_duplicates(self) -> None:
        relation_keys = [
            s_name
            for s_name, s in self.db.schema.items()
            if s["type"] == "relation" and s_name in self.csv.keys()
        ]

        for relation in relation_keys:
            if self.db.is_relation_has_duplicates(relation):
                relation_name = self.db.relation(relation)["name"]
                raise NotionError(
                    f"Collection DB '{relation_name}' used in '{relation}'"
                    f" relation column has duplicates which"
                    f" cannot be unambiguously mapped with CSV data."
                )

    def _validate_key_column(self, key_column: str) -> None:
        if key_column not in self.db.schema:
            raise NotionError(f"Key column '{key_column}' does not exist in Notion DB.")
        if self.db.schema[key_column]["type"] != "title":
            raise NotionError(f"Notion DB column '{key_column}' is not a key column.")

    def _validate_image_column(self) -> None:
        if self.rules["image_column"] is None:
            return

        if self.rules["image_column"] not in self.csv.keys():
            raise NotionError(
                f"Image column '{self.rules['image_column']}' not found in csv file."
            )

    def _validate_image_caption_column(self) -> None:
        if self.rules["image_caption_column"] is None:
            return

        if self.rules["image_caption_column"] not in self.csv.keys():
            raise NotionError(
                f"Image caption column '{self.rules['image_caption_column']}'"
                f" not found in csv file."
            )

    def _validate_icon_column(self) -> None:
        if self.rules["icon_column"] is None:
            return

        if self.rules["icon_column"] not in self.csv.keys():
            raise NotionError(
                f"Icon column '{self.rules['icon_column']}' not found in csv file."
            )

    def _vlaidate_mandatory_columns(self) -> None:
        missing_columns = set(self.rules["mandatory_columns"]) - set(self.csv.keys())
        if missing_columns:
            raise NotionError(
                f"Mandatory column(s) {missing_columns} not found in csv file."
            )

    def _vlaidate_merge_only_columns(self) -> None:
        missing_columns = set(self.rules["merge_only_columns"]) - set(self.csv.keys())
        if missing_columns:
            raise NotionError(
                f"Merge only column(s) {missing_columns} not found in csv file."
            )

    def _validate_csv_duplicates(self):
        first_column_values = [v[self.csv.keys()[0]] for v in self.csv]
        if len(set(first_column_values)) != len(first_column_values):
            raise NotionError("Duplicate values found in first column in CSV.")
