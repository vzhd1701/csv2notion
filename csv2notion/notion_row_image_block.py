from typing import Any, Optional, cast

from notion.block import ImageBlock
from notion.collection import CollectionRowBlock
from notion.maps import field_map
from notion.operations import build_operation

from csv2notion.notion_row_upload_file import get_file_id


class CoverImageBlock(ImageBlock):
    is_cover_block = field_map("properties.is_cover_block")

    def update(self, **attrs: Any) -> None:
        with self._client.as_atomic_transaction():
            file_id = attrs.pop("file_id", None)

            for k, v in attrs.items():
                setattr(self, k, v)

            if file_id:
                self._client.submit_transaction(
                    build_operation(
                        id=self.id,
                        path=["file_ids"],
                        args={"id": file_id},
                        command="listAfter",
                    )
                )


class RowCoverImageBlock(object):  # noqa: WPS214
    def __init__(self, row: CollectionRowBlock):
        self.row = row

        self._image_block: Optional[CoverImageBlock] = None

    @property
    def image_block(self) -> Optional[CoverImageBlock]:
        if self._image_block is None:
            self._image_block = self._get_cover_image_block()

        return self._image_block

    @image_block.setter
    def image_block(self, image_block: CoverImageBlock) -> None:
        self._image_block = image_block

    @property
    def caption(self) -> Optional[str]:
        if self.image_block is None:
            return None

        caption = self.image_block.caption

        return str(caption) if caption is not None else None

    @caption.setter
    def caption(self, caption: Optional[str]) -> None:
        if self.image_block is None:
            return

        self.image_block.caption = caption

    @property
    def url(self) -> str:
        if self.image_block is None:
            return ""

        return str(self.image_block.source)

    @url.setter
    def url(self, image_url: Optional[str]) -> None:
        if image_url is None:
            if self.image_block is not None:
                self.image_block.remove()
            return

        attrs = {
            "display_source": image_url,
            "source": image_url,
        }

        file_id = get_file_id(image_url)
        if file_id:
            attrs["file_id"] = file_id

        if self.row.children:
            if self.image_block:
                self.image_block.update(**attrs)
            else:
                self.image_block = self._add_new_image_block(**attrs)
                self.image_block.move_to(self.row, "first-child")
        else:
            self.image_block = self._add_new_image_block(**attrs)

        self.image_block.is_cover_block = True

    def _add_new_image_block(self, **attrs: Any) -> CoverImageBlock:
        image_block = self.row.children.add_new(ImageBlock, **attrs)
        image_block = CoverImageBlock(image_block._client, image_block._id)
        return cast(CoverImageBlock, image_block)

    def _get_cover_image_block(self) -> Optional[CoverImageBlock]:
        if not self.row.children:
            return None

        image_block = self.row.children[0]
        if not isinstance(image_block, ImageBlock):
            return None

        image_block = CoverImageBlock(image_block._client, image_block._id)

        if not image_block.is_cover_block:
            return None

        return cast(CoverImageBlock, image_block)
