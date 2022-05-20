import logging
from functools import partial
from pathlib import Path
from typing import List

from notion.utils import InvalidNotionIdentifier, extract_id

from csv2notion.csv_data import CSVData
from csv2notion.notion_convert_map import (
    map_checkbox,
    map_date,
    map_icon,
    map_number,
    map_url_or_file,
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
        properties = self._map_properties(row)
        columns = self._map_columns(row)

        return NotionUploadRow(columns=columns, properties=properties)

    def _map_properties(self, row):
        properties = {}

        if self.rules["image_column_mode"] == "block":
            properties["cover_block"] = self._map_image(row)
            properties["cover_block_caption"] = self._map_image_caption(row)
        else:
            properties["cover"] = self._map_image(row)

        properties["icon"] = self._map_icon(row)

        properties["created_time"] = self._pop_column_type(row, "created_time")
        properties["last_edited_time"] = self._pop_column_type(row, "last_edited_time")

        return {k: v for k, v in properties.items() if v is not None}

    def _map_columns(self, row):
        notion_row = {}

        for col_key, col_value in row.items():
            col_type = self.db.schema[col_key]["type"]

            notion_row[col_key] = self._map_column(col_key, col_value, col_type)

            self._raise_if_mandatory_empty(col_key, notion_row[col_key])

        return notion_row

    def _map_column(self, col_key, col_value, value_type):
        conversion_map = {
            "relation": partial(self._map_relation, col_key),
            "checkbox": map_checkbox,
            "date": map_date,
            "created_time": map_date,
            "last_edited_time": map_date,
            "multi_select": split_str,
            "number": map_number,
            "file": self._map_file,
        }

        try:
            return conversion_map[value_type](col_value)
        except KeyError:
            return col_value
        except TypeConversionError as e:
            if col_value == "" or not self.rules["fail_on_conversion_error"]:
                return None

            raise NotionError(e) from e

    def _pop_column_type(self, row, col_type_to_pop):
        """Some column types can't have multiple values (like created_time)
        so we pop them out of the row leaving only the last non-empty one"""

        last_col_value = None

        for col_key, col_value in list(row.items()):
            col_type = self.db.schema[col_key]["type"]

            if col_type == col_type_to_pop:
                result_value = self._map_column(col_key, col_value, col_type)

                self._raise_if_mandatory_empty(col_key, result_value)

                if result_value is not None:
                    last_col_value = result_value

                row.pop(col_key)

        return last_col_value

    def _map_icon(self, row):
        icon = None

        if self.rules["icon_column"]:
            icon = row.get(self.rules["icon_column"], "").strip()
            if icon:
                icon = map_icon(icon)
                if isinstance(icon, Path):
                    icon = self._relative_path(icon)

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
                image = map_url_or_file(image)
                if isinstance(image, Path):
                    image = self._relative_path(image)

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

    def _map_file(self, s: str) -> list:
        col_value = split_str(s)

        resolved_uris = []
        for v in col_value:
            file_uri = map_url_or_file(v)
            if isinstance(file_uri, Path):
                file_uri = self._relative_path(file_uri)

                if _is_banned_extension(file_uri):
                    raise NotionError(
                        f"File extension '*{file_uri.suffix}' is not allowed"
                        f" to upload on Notion."
                    )

            if file_uri not in resolved_uris:
                resolved_uris.append(file_uri)

        return resolved_uris

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
            if v.startswith("https://www.notion.so/"):
                resolved_relation = self._resolve_relation_by_url(relation_column, v)
            else:
                resolved_relation = self._resolve_relation_by_key(relation_column, v)

            if resolved_relation and resolved_relation not in resolved_relations:
                resolved_relations.append(resolved_relation)

        return resolved_relations

    def _resolve_relation_by_key(self, relation_column, key):
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

    def _resolve_relation_by_url(self, relation_column, url):
        try:
            block_id = extract_id(url)
        except InvalidNotionIdentifier:
            if self.rules["missing_relations_action"] == "ignore":
                return None
            raise NotionError(f"'{url}' is not a valid Notion URL.")

        relation = self.db.relation(relation_column)

        try:
            return next(r for r in relation["rows"].values() if r.id == block_id)
        except StopIteration:
            if self.rules["missing_relations_action"] in {"add", "fail"}:
                raise NotionError(
                    f"Row with url '{url}' not found in relation"
                    f" '{relation_column} [column] -> {relation['name']} [DB]'."
                )

            return None


def _is_banned_extension(file_path: Path) -> bool:
    return file_path.suffix in {".exe", ".com", ".js"}
