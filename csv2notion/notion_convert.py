from functools import partial
from pathlib import Path

from emoji import is_emoji

from csv2notion.csv_data import CSVData
from csv2notion.notion_convert_utils import (
    TypeConversionError,
    map_checkbox,
    map_date,
    map_number,
)
from csv2notion.notion_db import NotionDB, NotionError, NotionUploadRow
from csv2notion.notion_type_guess import is_url
from csv2notion.utils import split_str


def _validate_csv_duplicates(csv_data):
    first_column_values = [v[csv_data.keys()[0]] for v in csv_data]
    if len(set(first_column_values)) != len(first_column_values):
        raise NotionError("Duplicate values found in first column in CSV.")


def _drop_columns(columns, csv_data: CSVData):
    for column in columns:
        csv_data.drop_column(column)


class NotionRowConverter(object):
    def __init__(self, db: NotionDB, conversion_rules: dict):
        self.db = db
        self.rules = conversion_rules

    def prepare(self, csv_data):
        self._validate_image_column(csv_data.keys())
        self._validate_icon_column(csv_data.keys())
        self._vlaidate_mandatory_columns(csv_data.keys())

        if self.rules["is_merge"]:
            self._validate_key_column(csv_data.keys()[0])

            if self.rules["merge_only_columns"]:
                self._vlaidate_merge_only_columns(csv_data.keys())
                ignored_columns = set(csv_data.keys()[1:]) - set(
                    self.rules["merge_only_columns"]
                )
                _drop_columns(ignored_columns, csv_data)

        missing_columns = self._get_missing_columns(csv_data.keys())
        if missing_columns:
            if self.rules["missing_columns_action"] == "add":
                self._add_columns(missing_columns, csv_data)
            elif self.rules["missing_columns_action"] == "fail":
                raise NotionError(
                    f"CSV columns missing from Notion DB: {missing_columns}"
                )

        if self.rules["fail_on_relation_duplicates"]:
            self._validate_relations_duplicates(csv_data.keys())

        if self.rules["fail_on_duplicates"]:
            _validate_csv_duplicates(csv_data)
            self._validate_db_duplicates()

    def convert_to_notion_rows(self, csv_data: CSVData):
        result = []
        for i, row in enumerate(csv_data, 2):
            try:
                result.append(self._convert_row(row))
            except NotionError as e:
                raise NotionError(f"CSV [{i}]: {e}")

        return result

    def _add_columns(self, columns, csv_data: CSVData):
        for column in columns:
            self.db.add_column(column, csv_data.col_type(column))

    def _convert_row(self, row):
        notion_row = {}

        image = self._map_image(row)
        icon = self._map_icon(row)

        for key, value in row.items():
            if not self.db.schema.get(key):
                continue

            value_type = self.db.schema[key]["type"]

            conversion_map = {
                "relation": partial(self._map_relation, key),
                "checkbox": map_checkbox,
                "date": map_date,
                "multi_select": split_str,
                "number": map_number,
            }

            try:
                notion_row[key] = conversion_map[value_type](value)
            except KeyError:
                notion_row[key] = value
            except TypeConversionError as e:
                if value == "" or not self.rules["fail_on_conversion_error"]:
                    notion_row[key] = None
                else:
                    raise NotionError(e) from e

            if key in self.rules["mandatory_columns"] and not notion_row[key]:
                raise NotionError(f"Mandatory column '{key}' is empty")

        return NotionUploadRow(notion_row, image, icon)

    def _map_icon(self, row):
        icon = None
        if self.rules["icon_column"]:
            icon = row.get(self.rules["icon_column"], "").strip()
            if icon:
                icon = icon if is_url(icon) or is_emoji(icon) else self._map_path(icon)
            elif self.rules["icon_column"] in self.rules["mandatory_columns"]:
                raise NotionError(
                    f"Mandatory column '{self.rules['icon_column']}' is empty"
                )
            else:
                icon = None

            if not self.rules["icon_column_keep"]:
                row.pop(self.rules["icon_column"], None)
        return icon

    def _map_image(self, row):
        image = None
        if self.rules["image_column"]:
            image = row.get(self.rules["image_column"], "").strip()
            if image:
                image = image if is_url(image) else self._map_path(image)
            elif self.rules["image_column"] in self.rules["mandatory_columns"]:
                raise NotionError(
                    f"Mandatory column '{self.rules['image_column']}' is empty"
                )
            else:
                image = None

            if not self.rules["image_column_keep"]:
                row.pop(self.rules["image_column"], None)
        return image

    def _map_path(self, path):
        search_path = self.rules["files_search_path"]

        path = Path(path)

        if not path.is_absolute():
            path = search_path / path

        if not path.exists():
            raise NotionError(f"File {path.name} does not exist")

        return path

    def _map_relation(self, relation_column, value):
        value = split_str(value)

        relation = self.db.relation(relation_column)

        result = []
        for v in value:
            try:
                result.append(relation["rows"][v])
            except KeyError:
                if self.rules["missing_relations_action"] == "add":
                    self.db.add_relation_row(relation_column, v)
                    result.append(relation["rows"][v])
                elif self.rules["missing_relations_action"] == "ignore":
                    continue
                elif self.rules["missing_relations_action"] == "fail":
                    raise NotionError(
                        f"Value '{v}' for relation"
                        f" '{relation_column} [column] -> {relation['name']} [DB]'"
                        f" is not a valid value."
                    )
        return result

    def _validate_db_duplicates(self):
        if self.db.is_db_has_duplicates():
            raise NotionError("Duplicate values found in DB key column.")

    def _validate_relations_duplicates(self, keys):
        relation_keys = [
            s_name
            for s_name, s in self.db.schema.items()
            if s["type"] == "relation" and s_name in keys
        ]

        for relation in relation_keys:
            if self.db.is_relation_has_duplicates(relation):
                relation_name = self.db.relation(relation)["name"]
                raise NotionError(
                    f"Collection DB '{relation_name}' used in '{relation}'"
                    f" relation column has duplicates which"
                    f" cannot be unambiguously mapped with CSV data."
                )

    def _get_missing_columns(self, column_keys):
        csv_keys = set(column_keys)
        schema_keys = set(self.db.schema)

        if self.rules["image_column"] and not self.rules["image_column_keep"]:
            csv_keys -= {self.rules["image_column"]}

        if self.rules["icon_column"] and not self.rules["icon_column_keep"]:
            csv_keys -= {self.rules["icon_column"]}

        return csv_keys - schema_keys

    def _validate_key_column(self, key_column: str):
        if key_column not in self.db.schema:
            raise NotionError(f"Key column '{key_column}' does not exist in Notion DB.")
        if self.db.schema[key_column]["type"] != "title":
            raise NotionError(f"Notion DB column '{key_column}' is not a key column.")

    def _validate_image_column(self, csv_keys):
        if self.rules["image_column"] and self.rules["image_column"] not in csv_keys:
            raise NotionError(
                f"Image column '{self.rules['image_column']}' not found in csv file."
            )

    def _validate_icon_column(self, csv_keys):
        if self.rules["icon_column"] and self.rules["icon_column"] not in csv_keys:
            raise NotionError(
                f"Icon column '{self.rules['icon_column']}' not found in csv file."
            )

    def _vlaidate_mandatory_columns(self, csv_keys):
        missing_columns = set(self.rules["mandatory_columns"]) - set(csv_keys)
        if missing_columns:
            raise NotionError(
                f"Mandatory column(s) {missing_columns} not found in csv file."
            )

    def _vlaidate_merge_only_columns(self, csv_keys):
        missing_columns = set(self.rules["merge_only_columns"]) - set(csv_keys)
        if missing_columns:
            raise NotionError(
                f"Merge only column(s) {missing_columns} not found in csv file."
            )
