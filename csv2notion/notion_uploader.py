from dataclasses import dataclass
from datetime import datetime
from itertools import starmap
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from notion.collection import CollectionRowBlock
from notion.operations import build_operation

from csv2notion.notion_db import NotionDB
from csv2notion.notion_uploader_file import is_meta_different, upload_file
from csv2notion.notion_uploader_image_block import (
    add_image_block,
    get_cover_image_block,
    set_image_block_caption,
)

FileType = Union[str, Path]
FileColumns = Dict[str, List[FileType]]


@dataclass
class NotionUploadRow(object):
    row: dict
    image: Optional[FileType]
    image_caption: Optional[str]
    icon: Optional[FileType]
    file_columns: Optional[FileColumns]
    last_edited_time: Optional[datetime]

    def key(self):
        return list(self.row.values())[0]


class NotionRowUploader(object):
    def __init__(self, db: NotionDB):
        self.db = db

    def upload_row(self, row: NotionUploadRow, is_merge: bool, image_mode: str):
        db_row = self._get_db_row(row, image_mode, is_merge)

        if row.image:
            _set_row_image(db_row, image_mode, row.image, row.image_caption)

        if row.image_caption is not None and image_mode == "block" and not row.image:
            set_image_block_caption(db_row, row.image_caption)

        if row.icon:
            _set_row_icon(db_row, row.icon)

        if row.file_columns:
            _set_row_files(db_row, row.file_columns)

        if row.last_edited_time:
            _set_last_edited_time(db_row, row.last_edited_time)

    def _get_db_row(
        self, row: NotionUploadRow, image_mode: str, is_merge: bool
    ) -> CollectionRowBlock:
        if is_merge and self.db.rows.get(row.key()):
            cur_row = self.db.rows.get(row.key())
            self.db.update_row(cur_row, row.row)

            _merge_check(cur_row, image_mode, row)
        else:
            cur_row = self.db.add_row(row.row)

        return cur_row


def _merge_check(cur_row, image_mode, row):
    if row.image and not _is_image_changed(cur_row, row.image, image_mode):
        row.image = None

    if row.icon and not _is_icon_changed(cur_row, row.icon):
        row.icon = None

    if row.file_columns and not _is_file_columns_changed(cur_row, row.file_columns):
        row.file_columns = {}


def _set_row_image(
    db_row: CollectionRowBlock,
    image_mode: str,
    image: FileType,
    image_caption: Optional[str],
):
    if isinstance(image, Path):
        image_url, image_meta = upload_file(db_row, image)
    else:
        image_url = image
        image_meta = {"type": "url", "url": image}

    if image_mode == "block":
        add_image_block(db_row, image_url, image_meta, image_caption)
    elif image_mode == "cover":
        db_row.cover = image_url
        db_row.set("properties.cover_meta", image_meta)


def _set_row_icon(db_row: CollectionRowBlock, icon: FileType):
    if isinstance(icon, Path):
        icon, icon_meta = upload_file(db_row, icon)
    else:
        icon_meta = {"type": "url", "url": icon}

    db_row.icon = icon
    db_row.set("properties.icon_meta", icon_meta)


def _set_row_files(db_row: CollectionRowBlock, file_columns: FileColumns):
    for column_name, files in file_columns.items():
        _set_column_files(db_row, column_name, files)


def _set_column_files(
    db_row: CollectionRowBlock, column_name: str, files: List[FileType]
):
    column_id = db_row.collection.get_schema_property(column_name)["id"]

    column_files_meta, column_files_urls = _process_column_files(db_row, files)

    db_row.set(f"properties.{column_id}", column_files_urls)
    db_row.set(f"properties.file_column_meta.{column_id}", column_files_meta)


def _process_column_files(
    db_row: CollectionRowBlock, files: List[FileType]
) -> Tuple[List, List]:
    column_files_meta = []
    column_files_urls = []

    for file_or_url in files:
        if isinstance(file_or_url, Path):
            file_name = file_or_url.name
            file_url, file_meta = upload_file(db_row, file_or_url)
        else:
            file_name = file_or_url
            file_url = file_or_url
            file_meta = {"type": "url", "url": file_url}

        if column_files_urls:
            column_files_urls.append([","])
        column_files_urls.append([file_name, [["a", file_url]]])

        column_files_meta.append(file_meta)

    return column_files_meta, column_files_urls


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


def _is_image_changed(cur_row: CollectionRowBlock, image: FileType, image_mode: str):
    if image_mode == "block":
        image_block = get_cover_image_block(cur_row)
        if not image_block:
            return True

        image_meta = image_block.get("properties.cover_meta")
        image_url = image_block.source
    else:
        image_meta = cur_row.get("properties.cover_meta")
        image_url = cur_row.cover

    return is_meta_different(image, image_url, image_meta)


def _is_icon_changed(cur_row: CollectionRowBlock, image: FileType):
    icon_meta = cur_row.get("properties.icon_meta")
    icon_url = cur_row.icon

    return is_meta_different(image, icon_url, icon_meta)


def _is_file_columns_changed(cur_row: CollectionRowBlock, file_columns: FileColumns):
    for column_name, files in file_columns.items():
        if _is_file_column_changed(cur_row, column_name, files):
            return True

    return False


def _is_file_column_changed(
    cur_row: CollectionRowBlock, column_name: str, files: List[FileType]
):
    column_id = cur_row.collection.get_schema_property(column_name)["id"]

    files_meta = cur_row.get(f"properties.file_column_meta.{column_id}")
    files_url = getattr(cur_row, column_name)

    if not files_meta or not files_url:
        return True

    if not (len(files_meta) == len(files_url) == len(files)):  # noqa: WPS508
        return True

    return any(starmap(is_meta_different, zip(files, files_url, files_meta)))
