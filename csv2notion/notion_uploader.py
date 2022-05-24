from dataclasses import dataclass
from typing import Any, Dict

from csv2notion.notion_db import NotionDB
from csv2notion.notion_row import CollectionRowBlockExtended


@dataclass
class NotionUploadRow(object):
    columns: Dict[str, Any]
    properties: Dict[str, Any]

    def key(self) -> str:
        return str(list(self.columns.values())[0])


class NotionRowUploader(object):
    def __init__(self, db: NotionDB):
        self.db = db

    def upload_row(self, row: NotionUploadRow, is_merge: bool) -> None:
        post_properties = _extract_post_properties(row.properties)

        db_row = self._get_db_row(row, is_merge)

        # these need to be updated after
        # because they can't be updated in atomic transaction
        for prop, prop_val in post_properties.items():
            setattr(db_row, prop, prop_val)

    def _get_db_row(
        self, row: NotionUploadRow, is_merge: bool
    ) -> CollectionRowBlockExtended:
        existing_row = self.db.rows.get(row.key()) if is_merge else None

        if is_merge and existing_row:
            cur_row = existing_row
            cur_row.update(properties=row.properties, columns=row.columns)
        else:
            cur_row = self.db.add_row(properties=row.properties, columns=row.columns)

        return cur_row


def _extract_post_properties(properties: Dict[str, Any]) -> Dict[str, Any]:
    return {
        p: properties.pop(p)
        for p in properties.copy()
        if p in {"cover_block", "cover_block_caption", "last_edited_time"}
    }
