from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

from notion.collection import CollectionRowBlock
from notion.operations import build_operation

from csv2notion.notion_db import NotionDB
from csv2notion.notion_uploader_file import is_meta_different, upload_file
from csv2notion.notion_uploader_image_block import (
    add_image_block,
    get_cover_image_block,
    set_image_block_caption,
)


@dataclass
class NotionUploadRow(object):
    row: dict
    image: Optional[Union[str, Path]]
    image_caption: Optional[str]
    icon: Optional[Union[str, Path]]
    last_edited_time: Optional[datetime]

    def key(self):
        return list(self.row.values())[0]


class NotionRowUploader(object):
    def __init__(self, db: NotionDB):
        self.db = db

    def upload_row(self, row: NotionUploadRow, is_merge: bool, image_mode: str):
        db_row = self._get_db_row(row, image_mode, is_merge)

        if row.image:
            _set_row_image(db_row, row, image_mode)

        if row.image_caption is not None and image_mode == "block" and not row.image:
            set_image_block_caption(db_row, row.image_caption)

        if row.icon:
            _set_row_icon(db_row, row)

        if row.last_edited_time:
            _set_last_edited_time(db_row, row.last_edited_time)

    def _get_db_row(
        self, row: NotionUploadRow, image_mode: str, is_merge: bool
    ) -> CollectionRowBlock:
        if is_merge and self.db.rows.get(row.key()):
            cur_row = self.db.rows.get(row.key())
            self.db.update_row(cur_row, row.row)

            if row.image and not _is_image_changed(row.image, image_mode, cur_row):
                row.image = None

            if row.icon and not _is_icon_changed(row.icon, cur_row):
                row.icon = None
        else:
            cur_row = self.db.add_row(row.row)

        return cur_row


def _set_row_image(db_row: CollectionRowBlock, row: NotionUploadRow, image_mode: str):
    if isinstance(row.image, Path):
        image_url, image_meta = upload_file(db_row, row.image)
    else:
        image_url = row.image
        image_meta = {"type": "url", "url": row.image}

    if image_mode == "block":
        add_image_block(db_row, image_url, image_meta, row.image_caption)
    elif image_mode == "cover":
        db_row.cover = image_url
        db_row.set("properties.cover_meta", image_meta)


def _set_row_icon(db_row: CollectionRowBlock, row: NotionUploadRow):
    if isinstance(row.icon, Path):
        icon, icon_meta = upload_file(db_row, row.icon)
    else:
        icon = row.icon
        icon_meta = {"type": "url", "url": row.icon}
    db_row.icon = icon
    db_row.set("properties.icon_meta", icon_meta)


def _set_last_edited_time(row: CollectionRowBlock, time: datetime):
    row._client.submit_transaction(
        build_operation(
            id=row.id,
            path="last_edited_time",
            args=int(time.timestamp() * 1000),
            table=row._table,
        ),
        update_last_edited=False,
    )


def _is_image_changed(
    image: Union[str, Path], image_mode: str, cur_row: CollectionRowBlock
):
    if image_mode == "block":
        image_block = get_cover_image_block(cur_row)
        if not image_block:
            return True

        image_meta = image_block.get("properties.cover_meta")
        image_url = image_block.source

        return is_meta_different(image, image_url, image_meta)

    image_meta = cur_row.get("properties.cover_meta")
    image_url = cur_row.cover

    return is_meta_different(image, image_url, image_meta)


def _is_icon_changed(image: Union[str, Path], cur_row: CollectionRowBlock):
    icon_meta = cur_row.get("properties.icon_meta")
    icon_url = cur_row.icon

    return is_meta_different(image, icon_url, icon_meta)
