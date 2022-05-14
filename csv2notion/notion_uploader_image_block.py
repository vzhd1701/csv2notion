from typing import Optional

from notion.block import ImageBlock
from notion.collection import CollectionRowBlock
from notion.operations import build_operation

from csv2notion.notion_uploader_file import get_file_id


def set_image_block_caption(row: CollectionRowBlock, caption: str) -> None:
    image_block = get_cover_image_block(row)
    if not image_block:
        return
    image_block.caption = caption


def add_image_block(
    row: CollectionRowBlock, image_url: str, image_meta: dict, image_caption: str
) -> None:
    attrs = {
        "display_source": image_url,
        "source": image_url,
    }

    if image_caption is not None:
        attrs["caption"] = image_caption

    file_id = get_file_id(image_url)
    if file_id:
        attrs["file_id"] = file_id

    if row.children:
        image_block = get_cover_image_block(row)
        if image_block:
            _update_image_block(row, image_block, attrs)
        else:
            image_block = row.children.add_new(ImageBlock, **attrs)
            image_block.move_to(row, "first-child")
    else:
        image_block = row.children.add_new(ImageBlock, **attrs)

    image_block.set("properties.cover_meta", image_meta)


def get_cover_image_block(row: CollectionRowBlock) -> Optional[ImageBlock]:
    if not row.children:
        return None

    image_block = row.children[0]
    if not isinstance(image_block, ImageBlock):
        return None

    if not image_block.get("properties.cover_meta"):
        return None

    return image_block


def _update_image_block(row: CollectionRowBlock, image_block, attrs):
    with row._client.as_atomic_transaction():
        # Need to add it manually, Notion SDK doesn't work here
        file_id = attrs.pop("file_id", None)

        for k, v in attrs.items():
            setattr(image_block, k, v)

        if file_id:
            row._client.submit_transaction(
                build_operation(
                    id=image_block.id,
                    path=["file_ids"],
                    args={"id": file_id},
                    command="listAfter",
                )
            )
