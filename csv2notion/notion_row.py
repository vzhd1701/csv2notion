from datetime import datetime
from itertools import starmap
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from cached_property import cached_property
from notion.collection import CollectionRowBlock
from notion.maps import field_map
from notion.operations import build_operation
from notion.utils import remove_signed_prefix_as_needed

from csv2notion.notion_row_image_block import RowCoverImageBlock
from csv2notion.notion_row_upload_file import is_meta_different, upload_filetype
from csv2notion.utils_static import FileType


class CollectionRowBlockExtended(CollectionRowBlock):  # noqa: WPS214
    icon_meta = field_map("properties.meta.icon")
    cover_meta = field_map("properties.meta.cover")
    cover_block_meta = field_map("properties.meta.cover_block")

    @cached_property
    def image_block(self) -> RowCoverImageBlock:
        return RowCoverImageBlock(self)

    @property
    def icon(self) -> str:
        return super().icon

    @icon.setter
    def icon(self, icon: FileType) -> None:
        if not self._is_meta_changed(icon, self.icon, "icon_meta"):
            return

        icon, icon_meta = upload_filetype(self, icon)

        self.icon_meta = icon_meta
        CollectionRowBlock.icon.fset(self, icon)

    @property
    def cover(self) -> Optional[str]:
        return super().cover

    @cover.setter
    def cover(self, image: FileType) -> None:
        if image == "":
            image = None

        if not self._is_meta_changed(image, self.cover, "cover_meta"):
            return

        image, cover_meta = upload_filetype(self, image)

        self.cover_meta = cover_meta
        CollectionRowBlock.cover.fset(self, image)

    @property
    def cover_block(self) -> Optional[str]:
        return self.image_block.url

    @cover_block.setter
    def cover_block(self, image: FileType) -> None:
        if self._client.in_transaction():
            raise RuntimeError("Cannot set cover_block during atomic transaction")

        if image == "":
            image = None

        if not self._is_meta_changed(image, self.cover_block, "cover_block_meta"):
            return

        image, cover_block_meta = upload_filetype(self, image)

        self.cover_block_meta = cover_block_meta
        self.image_block.url = image

    @property
    def cover_block_caption(self) -> Optional[str]:
        return self.image_block.caption

    @cover_block_caption.setter
    def cover_block_caption(self, caption: Optional[str]) -> None:
        if self.cover_block_caption == caption:
            return

        self.image_block.caption = caption

    @property
    def created_time(self) -> datetime:
        created_time = self.get("created_time")
        return datetime.utcfromtimestamp(created_time / 1000)

    @created_time.setter
    def created_time(self, time: datetime) -> None:
        self.set("created_time", int(time.timestamp() * 1000))

    @property
    def last_edited_time(self) -> datetime:
        last_edited_time = self.get("last_edited_time")
        return datetime.utcfromtimestamp(last_edited_time / 1000)

    @last_edited_time.setter
    def last_edited_time(self, time: datetime) -> None:
        if self._client.in_transaction():
            raise RuntimeError("Cannot set last_edited_time during atomic transaction")

        self._client.submit_transaction(
            build_operation(
                id=self.id,
                path="last_edited_time",
                args=int(time.timestamp() * 1000),
                table=self._table,
            ),
            update_last_edited=False,
        )

    def set_property(self, identifier, new_value):
        prop = self.collection.get_schema_property(identifier)
        if prop is None:
            raise AttributeError(f"Object does not have property '{identifier}'")

        if prop["type"] in {"select", "multi_select"}:
            schema_update, prop = self.collection.check_schema_select_options(
                prop, new_value
            )
            if schema_update:
                self.collection.set(
                    "schema.{0}.options".format(prop["id"]), prop["options"]
                )

        if prop["type"] == "file":
            if not self._is_file_column_changed(prop["id"], new_value):
                return
            new_value = self._upload_column_files(prop["id"], new_value)

        path, new_value = self._convert_python_to_notion(
            new_value, prop, identifier=identifier
        )

        self.set(path, new_value)

    def _convert_python_to_notion(self, raw_value, prop, identifier="<unknown>"):
        if prop["type"] == "file" and isinstance(raw_value, dict):
            filelist = []
            for filename, url in raw_value.items():
                url = remove_signed_prefix_as_needed(url)
                filelist += [[filename, [["a", url]]], [","]]
            result_value = filelist[:-1]

            return ["properties", prop["id"]], result_value

        return super()._convert_python_to_notion(raw_value, prop, identifier)

    def _upload_column_files(
        self, column_id: str, files: List[FileType]
    ) -> Dict[str, str]:
        column_files_meta, column_files_urls = self._process_column_files(files)

        self.set(f"properties.meta.file_columns.{column_id}", column_files_meta)

        return column_files_urls

    def _process_column_files(self, files: List[FileType]) -> Tuple[list, dict]:
        column_files_meta = []
        column_files_urls = {}

        for filetype in files:
            file_url, file_meta = upload_filetype(self, filetype)

            column_files_urls[get_filetype_name(filetype)] = file_url
            column_files_meta.append(file_meta)

        return column_files_meta, column_files_urls

    def _is_file_column_changed(self, column_id: str, files: List[FileType]):
        files_meta = self.get(f"properties.meta.file_columns.{column_id}")
        files_url = self.get_property(column_id)

        # if column is empty and files list is empty, nothing to change
        if not any([files, files_meta, files_url]):
            return False

        if not files_meta or not files_url:
            return True

        if not (len(files_meta) == len(files_url) == len(files)):  # noqa: WPS508
            return True

        return any(starmap(is_meta_different, zip(files, files_url, files_meta)))

    def _is_meta_changed(
        self,
        new_val: Optional[FileType],
        current_val: Optional[str],
        meta_parameter: str,
    ) -> bool:
        if (current_val is None or new_val is None) and current_val != new_val:
            return True

        current_value_meta = getattr(self, meta_parameter)

        return is_meta_different(new_val, current_val, current_value_meta)


def get_filetype_name(filetype: FileType) -> str:
    return filetype.name if isinstance(filetype, Path) else filetype
