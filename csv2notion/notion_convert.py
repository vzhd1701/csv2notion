import logging
from functools import partial
from pathlib import Path

from csv2notion.csv_data import CSVData
from csv2notion.notion_convert_utils import (
    TypeConversionError,
    map_checkbox,
    map_date,
    map_icon,
    map_image,
    map_number,
)
from csv2notion.notion_db import NotionDB, NotionUploadRow
from csv2notion.utils import NotionError, split_str

logger = logging.getLogger(__name__)


class NotionRowConverter(object):
    def __init__(self, db: NotionDB, conversion_rules: dict):
        self.db = db
        self.rules = conversion_rules

    def convert_to_notion_rows(self, csv_data: CSVData):
        result = []
        for i, row in enumerate(csv_data, 2):
            try:
                result.append(self._convert_row(row))
            except NotionError as e:
                raise NotionError(f"CSV [{i}]: {e}")

        return result

    def _convert_row(self, row: dict):
        notion_row = {}

        image = self._map_image(row)
        image_caption = self._map_image_caption(row)
        icon = self._map_icon(row)

        last_edited_time = None

        for key, value in row.items():
            if not self.db.schema.get(key):
                continue

            value_type = self.db.schema[key]["type"]

            conversion_map = {
                "relation": partial(self._map_relation, key),
                "checkbox": map_checkbox,
                "date": map_date,
                "created_time": map_date,
                "last_edited_time": map_date,
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

            # These cannot be None, server will set them if they are missing
            if notion_row[key] is None:
                if value_type in {"created_time", "last_edited_time"}:
                    notion_row.pop(key)

            # There can only be one last_edited_time, picking last column if multiple
            if notion_row.get(key) and value_type == "last_edited_time":
                last_edited_time = notion_row.pop(key)

        return NotionUploadRow(
            row=notion_row,
            image=image,
            image_caption=image_caption,
            icon=icon,
            last_edited_time=last_edited_time,
        )

    def _map_icon(self, row):
        icon = None

        if self.rules["icon_column"]:
            icon = row.get(self.rules["icon_column"], "").strip()
            if icon:
                icon = map_icon(icon)
                if isinstance(icon, Path):
                    icon = self._relative_path(icon)
            elif self.rules["icon_column"] in self.rules["mandatory_columns"]:
                raise NotionError(
                    f"Mandatory column '{self.rules['icon_column']}' is empty"
                )
            else:
                icon = None

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
            elif self.rules["image_column"] in self.rules["mandatory_columns"]:
                raise NotionError(
                    f"Mandatory column '{self.rules['image_column']}' is empty"
                )
            else:
                image = None

            if not self.rules["image_column_keep"]:
                row.pop(self.rules["image_column"], None)
        return image

    def _map_image_caption(self, row):
        image_caption = None
        if self.rules["image_caption_column"]:
            image_caption = row.get(self.rules["image_caption_column"], "").strip()
            if not image_caption and self._is_mandatory(
                self.rules["image_caption_column"]
            ):
                raise NotionError(
                    f"Mandatory column '{self.rules['image_caption_column']}' is empty"
                )

            if not self.rules["image_caption_column_keep"]:
                row.pop(self.rules["image_caption_column"], None)
        return image_caption

    def _is_mandatory(self, key):
        return key in self.rules["mandatory_columns"]

    def _relative_path(self, path):
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
