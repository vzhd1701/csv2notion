from datetime import datetime
from itertools import starmap
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from cached_property import cached_property
from notion.collection import CollectionRowBlock
from notion.maps import field_map
from notion.operations import build_operation
from notion.utils import remove_signed_prefix_as_needed

from csv2notion.notion_row_image_block import RowCoverImageBlock
from csv2notion.notion_row_upload_file import Meta, is_meta_different, upload_filetype
from csv2notion.utils_static import FileType

NamedURLs = Dict[str, str]


class CollectionRowBlockExtended(CollectionRowBlock):  # noqa: WPS214
    icon_meta = field_map("properties.meta.icon")
    cover_meta = field_map("properties.meta.cover")
    cover_block_meta = field_map("properties.meta.cover_block")

    @cached_property  # type: ignore
    def image_block(self) -> RowCoverImageBlock:
        return RowCoverImageBlock(self)

    @property
    def icon(self) -> str:
        return super().icon  # type: ignore

    @icon.setter
    def icon(self, icon: FileType) -> None:
        new_icon: Optional[FileType] = icon if icon else None

        if not self._is_meta_changed("icon_meta", new_icon, self.icon):
            return

        if new_icon is None:
            icon_meta = None
        else:
            new_icon, icon_meta = upload_filetype(self, new_icon)

        self.icon_meta = icon_meta
        CollectionRowBlock.icon.fset(self, new_icon)

    @property
    def cover(self) -> Optional[str]:
        return super().cover  # type: ignore

    @cover.setter
    def cover(self, image: FileType) -> None:
        new_image: Optional[FileType] = image if image else None

        if not self._is_meta_changed("cover_meta", new_image, self.cover):
            return

        if new_image is None:
            cover_meta = None
        else:
            new_image, cover_meta = upload_filetype(self, new_image)

        self.cover_meta = cover_meta
        CollectionRowBlock.cover.fset(self, new_image)

    @property
    def cover_block(self) -> Optional[str]:
        return self.image_block.url  # type: ignore

    @cover_block.setter
    def cover_block(self, image: FileType) -> None:
        if self._client.in_transaction():
            raise RuntimeError("Cannot set cover_block during atomic transaction")

        new_image: Optional[FileType] = image if image else None

        if not self._is_meta_changed("cover_block_meta", new_image, self.cover_block):
            return

        if new_image is None:
            cover_block_meta = None
        else:
            new_image, cover_block_meta = upload_filetype(self, new_image)

        self.cover_block_meta = cover_block_meta
        self.image_block.url = new_image

    @property
    def cover_block_caption(self) -> Optional[str]:
        return self.image_block.caption  # type: ignore

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

    def set_property(self, identifier: str, new_value: Any) -> None:
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

    def _convert_python_to_notion(
        self, raw_value: Any, prop: Dict[str, str], identifier: str = "<unknown>"
    ) -> Any:
        if prop["type"] == "file" and isinstance(raw_value, dict):
            filelist = []
            for filename, url in raw_value.items():
                url = remove_signed_prefix_as_needed(url)
                filelist += [[filename, [["a", url]]], [","]]
            result_value = filelist[:-1]

            return ["properties", prop["id"]], result_value

        return super()._convert_python_to_notion(raw_value, prop, identifier)

    def _upload_column_files(self, column_id: str, files: List[FileType]) -> NamedURLs:
        column_files_meta, column_files_urls = self._process_column_files(files)

        self.set(f"properties.meta.file_columns.{column_id}", column_files_meta)

        return column_files_urls

    def _process_column_files(
        self, files: List[FileType]
    ) -> Tuple[List[Meta], NamedURLs]:
        column_files_meta: List[Meta] = []
        column_files_urls: NamedURLs = {}

        for filetype in files:
            file_url, file_meta = upload_filetype(self, filetype)

            column_files_urls[get_filetype_name(filetype)] = file_url
            column_files_meta.append(file_meta)

        return column_files_meta, column_files_urls

    def _is_file_column_changed(self, column_id: str, files: List[FileType]) -> bool:
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
        meta_parameter: str,
        new_val: Optional[FileType],
        current_val: Optional[str],
    ) -> bool:
        if (current_val is None or new_val is None) and current_val != new_val:
            return True

        current_value_meta = getattr(self, meta_parameter)

        return is_meta_different(new_val, current_val, current_value_meta)


def get_filetype_name(filetype: FileType) -> str:
    return filetype.name if isinstance(filetype, Path) else filetype
