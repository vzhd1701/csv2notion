import logging
from functools import partial
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from notion.user import User
from notion.utils import InvalidNotionIdentifier, extract_id

from csv2notion.csv_data import CSVData, CSVRowType
from csv2notion.notion_convert_map import (
    map_checkbox,
    map_date,
    map_icon,
    map_number,
    map_url_or_file,
)
from csv2notion.notion_db import NotionDB
from csv2notion.notion_row import CollectionRowBlockExtended
from csv2notion.notion_type_guess import is_email
from csv2notion.notion_uploader import NotionUploadRow
from csv2notion.utils_exceptions import NotionError, TypeConversionError
from csv2notion.utils_static import ConversionRules, FileType
from csv2notion.utils_str import split_str

logger = logging.getLogger(__name__)


class NotionRowConverter(object):  # noqa:  WPS214
    def __init__(self, db: NotionDB, conversion_rules: ConversionRules):
        self.db = db
        self.rules = conversion_rules

        self._current_row = 0

    def convert_to_notion_rows(self, csv_data: CSVData) -> List[NotionUploadRow]:
        notion_rows = []

        # starting with 2nd row, because first is header
        self._current_row = 2

        for row in csv_data:
            try:
                notion_rows.append(self._convert_row(row))
            except NotionError as e:
                raise NotionError(f"CSV [{self._current_row}]: {e}")
            self._current_row += 1

        return notion_rows

    def _error(self, error: str) -> None:
        logger.error(f"CSV [{self._current_row}]: {error}")

        if self.rules.fail_on_conversion_error:
            raise NotionError("Error during conversion.")

    def _convert_row(self, row: CSVRowType) -> NotionUploadRow:
        properties = self._map_properties(row)
        columns = self._map_columns(row)

        return NotionUploadRow(columns=columns, properties=properties)

    def _map_properties(self, row: CSVRowType) -> Dict[str, Any]:
        properties = {}

        if self.rules.image_column_mode == "block":
            properties["cover_block"] = self._map_image(row)
            properties["cover_block_caption"] = self._map_image_caption(row)
        else:
            properties["cover"] = self._map_image(row)

        properties["icon"] = self._map_icon(row)

        properties["created_time"] = self._pop_column_type(row, "created_time")
        properties["last_edited_time"] = self._pop_column_type(row, "last_edited_time")

        return {k: v for k, v in properties.items() if v is not None}

    def _map_columns(self, row: CSVRowType) -> Dict[str, Any]:
        notion_row = {}

        for col_key, col_value in row.items():
            col_type = self.db.columns[col_key]["type"]

            notion_row[col_key] = self._map_column(col_key, col_value, col_type)

            self._raise_if_mandatory_empty(col_key, notion_row[col_key])

        return notion_row

    def _map_column(
        self, col_key: str, col_value: str, value_type: str
    ) -> Optional[Any]:
        conversion_map: Dict[str, Callable[[str], Any]] = {
            "relation": partial(self._map_relation, col_key),
            "checkbox": map_checkbox,
            "date": map_date,
            "created_time": map_date,
            "last_edited_time": map_date,
            "multi_select": split_str,
            "number": map_number,
            "file": self._map_file,
            "person": self._map_person,
        }

        try:
            return conversion_map[value_type](col_value)
        except KeyError:
            return col_value
        except TypeConversionError as e:
            if not col_value.strip():
                return None

            self._error(str(e))
            return None

    def _pop_column_type(self, row: CSVRowType, col_type_to_pop: str) -> Optional[Any]:
        """Some column types can't have multiple values (like created_time)
        so we pop them out of the row leaving only the last non-empty one"""

        last_col_value = None

        for col_key, col_value in list(row.items()):
            col_type = self.db.columns[col_key]["type"]

            if col_type == col_type_to_pop:
                result_value = self._map_column(col_key, col_value, col_type)

                self._raise_if_mandatory_empty(col_key, result_value)

                if result_value is not None:
                    last_col_value = result_value

                row.pop(col_key)

        return last_col_value

    def _map_icon(self, row: CSVRowType) -> Optional[FileType]:
        icon: Optional[FileType] = None

        if self.rules.icon_column:
            icon = row.get(self.rules.icon_column, "").strip()
            if icon:
                icon = map_icon(icon)
                if isinstance(icon, Path):
                    icon = self._relative_path(icon)

            self._raise_if_mandatory_empty(self.rules.icon_column, icon)

            if not self.rules.icon_column_keep:
                row.pop(self.rules.icon_column, None)

        if not icon and self.rules.default_icon:
            icon = self.rules.default_icon

        return icon

    def _map_image(self, row: CSVRowType) -> Optional[FileType]:
        image: Optional[FileType] = None

        if self.rules.image_column:
            image = row.get(self.rules.image_column, "").strip()
            if image:
                image = map_url_or_file(image)
                if isinstance(image, Path):
                    image = self._relative_path(image)

            self._raise_if_mandatory_empty(self.rules.image_column, image)

            if not self.rules.image_column_keep:
                row.pop(self.rules.image_column, None)

        return image

    def _map_image_caption(self, row: CSVRowType) -> Optional[str]:
        image_caption = None

        if self.rules.image_caption_column:
            image_caption = row.get(self.rules.image_caption_column, "").strip()

            self._raise_if_mandatory_empty(
                self.rules.image_caption_column, image_caption
            )

            if not self.rules.image_caption_column_keep:
                row.pop(self.rules.image_caption_column, None)

        return image_caption

    def _map_file(self, s: str) -> List[FileType]:
        col_value = split_str(s)

        resolved_uris = []
        for v in col_value:
            file_uri = map_url_or_file(v)

            if isinstance(file_uri, Path):
                rel_file_uri = self._ensure_path(file_uri)

                if rel_file_uri is None:
                    continue

                file_uri = rel_file_uri

            if file_uri not in resolved_uris:
                resolved_uris.append(file_uri)

        return resolved_uris

    def _ensure_path(self, path: Path) -> Optional[Path]:
        ensured_path = self._relative_path(path)
        if ensured_path is None:
            return None

        if _is_banned_extension(ensured_path):
            self._error(
                f"File extension '*{ensured_path.suffix}' is not allowed"
                f" to upload on Notion."
            )
            return None

        return ensured_path

    def _relative_path(self, path: Path) -> Optional[Path]:
        search_path = self.rules.files_search_path

        if not path.is_absolute():
            path = search_path / path

        if not path.exists():
            self._error(f"File {path.name} does not exist.")
            return None

        return path

    def _map_relation(
        self, relation_column: str, col_value: str
    ) -> List[CollectionRowBlockExtended]:
        col_values = split_str(col_value)

        resolved_relations = []
        for v in col_values:
            if v.startswith("https://www.notion.so/"):
                resolved_relation = self._resolve_relation_by_url(relation_column, v)
            else:
                resolved_relation = self._resolve_relation_by_key(relation_column, v)

            if resolved_relation and resolved_relation not in resolved_relations:
                resolved_relations.append(resolved_relation)

        return resolved_relations

    def _resolve_relation_by_key(
        self, relation_column: str, key: str
    ) -> Optional[CollectionRowBlockExtended]:
        relation = self.db.relations[relation_column]

        try:
            return relation.rows[key]
        except KeyError:
            if self.rules.add_missing_relations:
                return relation.add_row_key(key)

            self._error(
                f"Value '{key}' for relation"
                f" '{relation_column} [column] -> {relation.name} [DB]'"
                f" is not a valid value."
            )

            return None

    def _resolve_relation_by_url(
        self, relation_column: str, url: str
    ) -> Optional[CollectionRowBlockExtended]:
        block_id = self._extract_id(url)
        if block_id is None:
            return None

        relation = self.db.relations[relation_column]
        relation_rows = relation.rows.values()

        try:
            return next(r for r in relation_rows if r.id == block_id)
        except StopIteration:
            self._error(
                f"Row with url '{url}' not found in relation"
                f" '{relation_column} [column] -> {relation.name} [DB]'."
            )

            return None

    def _extract_id(self, url: str) -> Optional[str]:
        try:
            return str(extract_id(url))
        except InvalidNotionIdentifier:
            self._error(f"'{url}' is not a valid Notion URL.")

            return None

    def _map_person(self, col_value: str) -> List[User]:
        col_values = split_str(col_value)

        resolved_persons = []
        for v in col_values:
            if is_email(v):
                resolved_person = self.db.users.get(v)

                if not resolved_person:
                    resolved_person = self.db.find_user(v)
            else:
                resolved_person = self.db.get_user_by_name(v)

            if resolved_person is None:
                self._error(f"Person '{v}' cannot be resolved.")
                continue

            if resolved_person not in resolved_persons:
                resolved_persons.append(resolved_person)

        return resolved_persons

    def _raise_if_mandatory_empty(self, col_key: str, col_value: Any) -> None:
        is_mandatory = col_key in self.rules.mandatory_column

        if is_mandatory and not col_value:
            raise NotionError(f"Mandatory column '{col_key}' is empty")


def _is_banned_extension(file_path: Path) -> bool:
    return file_path.suffix in {".exe", ".com", ".js"}
