import logging
from functools import partial
from pathlib import Path
from typing import List

from csv2notion.csv_data import CSVData
from csv2notion.notion_convert_map import (
    map_checkbox,
    map_date,
    map_icon,
    map_image,
    map_number,
)
from csv2notion.notion_db import NotionDB
from csv2notion.notion_uploader import NotionUploadRow
from csv2notion.utils_exceptions import NotionError, TypeConversionError
from csv2notion.utils_str import split_str

logger = logging.getLogger(__name__)


class NotionRowConverter(object):  # noqa:  WPS214
    def __init__(self, db: NotionDB, conversion_rules: dict):
        self.db = db
        self.rules = conversion_rules

    def convert_to_notion_rows(self, csv_data: CSVData) -> List[NotionUploadRow]:
        notion_rows = []
        for i, row in enumerate(csv_data, 2):
            try:
                notion_rows.append(self._convert_row(row))
            except NotionError as e:
                raise NotionError(f"CSV [{i}]: {e}")

        return notion_rows

    def _convert_row(self, row: dict) -> NotionUploadRow:
        image = self._map_image(row)
        image_caption = self._map_image_caption(row)
        icon = self._map_icon(row)

        notion_row, last_edited_time = self._map_columns(row)

        return NotionUploadRow(
            row=notion_row,
            image=image,
            image_caption=image_caption,
            icon=icon,
            last_edited_time=last_edited_time,
        )

    def _map_columns(self, row):
        notion_row = {}
        last_edited_time = None

        for col_key, col_value in row.items():
            col_type = self.db.schema[col_key]["type"]

            notion_row[col_key] = self._map_column(col_key, col_value, col_type)

            self._raise_if_mandatory_empty(col_key, notion_row[col_key])

            # These cannot be None, server will set them if they are missing
            if notion_row[col_key] is None:
                if col_type in {"created_time", "last_edited_time"}:
                    notion_row.pop(col_key)

            # There can only be one last_edited_time, picking last column if multiple
            if col_type == "last_edited_time":
                last_edited_time = notion_row.pop(col_key, None)

        return notion_row, last_edited_time

    def _map_column(self, col_key, col_value, value_type):
        conversion_map = {
            "relation": partial(self._map_relation, col_key),
            "checkbox": map_checkbox,
            "date": map_date,
            "created_time": map_date,
            "last_edited_time": map_date,
            "multi_select": split_str,
            "number": map_number,
        }

        try:
            return conversion_map[value_type](col_value)
        except KeyError:
            return col_value
        except TypeConversionError as e:
            if col_value == "" or not self.rules["fail_on_conversion_error"]:
                return None

            raise NotionError(e) from e

    def _map_icon(self, row):
        icon = None

        if self.rules["icon_column"]:
            icon = row.get(self.rules["icon_column"], "").strip()
            if icon:
                icon = map_icon(icon)
                if isinstance(icon, Path):
                    icon = self._relative_path(icon)
            else:
                icon = None

            self._raise_if_mandatory_empty(self.rules["icon_column"], icon)

            if not self.rules["icon_column_keep"]:
                row.pop(self.rules["icon_column"], None)

        if not icon and self.rules["default_icon"]:
            icon = self.rules["default_icon"]

        return icon

    def _map_image(self, row):
        image = None
        if self.rules["image_column"]:
            image = row.get(self.rules["image_column"], "").strip()
            if image:
                image = map_image(image)
                if isinstance(image, Path):
                    image = self._relative_path(image)
            else:
                image = None

            self._raise_if_mandatory_empty(self.rules["image_column"], image)

            if not self.rules["image_column_keep"]:
                row.pop(self.rules["image_column"], None)
        return image

    def _map_image_caption(self, row):
        image_caption = None
        if self.rules["image_caption_column"]:
            image_caption = row.get(self.rules["image_caption_column"], "").strip()

            self._raise_if_mandatory_empty(
                self.rules["image_caption_column"], image_caption
            )

            if not self.rules["image_caption_column_keep"]:
                row.pop(self.rules["image_caption_column"], None)
        return image_caption

    def _raise_if_mandatory_empty(self, col_key, col_value):
        is_mandatory = col_key in self.rules["mandatory_columns"]

        if is_mandatory and not col_value:
            raise NotionError(f"Mandatory column '{col_key}' is empty")

    def _relative_path(self, path):
        search_path = self.rules["files_search_path"]

        path = Path(path)

        if not path.is_absolute():
            path = search_path / path

        if not path.exists():
            raise NotionError(f"File {path.name} does not exist")

        return path

    def _map_relation(self, relation_column, col_value):
        col_value = split_str(col_value)

        resolved_relations = []
        for v in col_value:
            resolved_relation = self._resolve_relation(relation_column, v)
            if resolved_relation:
                resolved_relations.append(self._resolve_relation(relation_column, v))

        return resolved_relations

    def _resolve_relation(self, relation_column, key):
        relation = self.db.relation(relation_column)

        try:
            return relation["rows"][key]
        except KeyError:
            if self.rules["missing_relations_action"] == "add":
                self.db.add_relation_row(relation_column, key)
                return relation["rows"][key]
            elif self.rules["missing_relations_action"] == "fail":
                raise NotionError(
                    f"Value '{key}' for relation"
                    f" '{relation_column} [column] -> {relation['name']} [DB]'"
                    f" is not a valid value."
                )

            return None
