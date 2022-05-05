import mimetypes
from pathlib import Path
from typing import Union

import requests

from csv2notion.csv_data import CSVData
from csv2notion.notion.block import Block, ImageBlock
from csv2notion.notion.client import NotionClient
from csv2notion.notion.utils import InvalidNotionIdentifier
from csv2notion.notion_convert_utils import schema_from_csv
from csv2notion.utils import NotionError, rand_id_unique

S3_URL_PREFIX = "https://s3-us-west-2.amazonaws.com/secure.notion-static.com/"


def make_new_db_from_csv(
    client: NotionClient, page_name: str, csv_data: CSVData
) -> str:
    schema = schema_from_csv(csv_data)

    permissions = [
        {"role": "editor", "type": "user_permission", "user_id": client.current_user.id}
    ]
    page_id = client.create_record(
        "block",
        client.current_space,
        type="collection_view_page",
        permissions=permissions,
    )
    page = client.get_block(page_id)

    page.collection = client.get_collection(
        client.create_record(
            "collection",
            parent=page,
            schema=schema,
        )
    )

    view = page.views.add_new(view_type="table")

    # Make sure all columns are in the same order as CSV
    table_properties = [{"visible": True, "property": col_id} for col_id in schema]
    view.set("format.table_properties", table_properties)

    page.title = page_name

    return page.get_browseable_url()


def get_notion_client(token: str):
    try:
        return NotionClient(token_v2=token)
    except requests.exceptions.HTTPError as e:
        raise NotionError("Invalid Notion token") from e


class NotionUploadRow(object):
    def __init__(self, row: dict, image: Union[str, Path], icon: Union[str, Path]):
        self.row = row
        self.image = image
        self.icon = icon

    def items(self):
        return self.row.items()

    def key(self):
        return list(self.row.values())[0]


class NotionDB(object):
    def __init__(self, client: NotionClient, notion_url: str):
        self.client = client

        try:
            block = self.client.get_block(notion_url, force_refresh=True)
        except InvalidNotionIdentifier as e:
            raise NotionError("Invalid URL.") from e

        if block.type != "collection_view_page":
            raise NotionError("Provided URL links does not point to a Notion database.")

        self.collection = block.collection
        self.schema = {p["name"]: p for p in self.collection.get_schema_properties()}

        self._cache_relations = {}
        self._cache_rows = {}

    def upload_row(
        self, row: NotionUploadRow, is_merge: bool = False, image_mode: str = None
    ):
        if is_merge and self.rows.get(row.key()):
            cur_row = self.rows.get(row.key())
            self._update_row(cur_row, row)
        else:
            cur_row = self._add_row(row)

        if row.image:
            if isinstance(row.image, Path):
                image_url = self._upload_file(row.image, cur_row)
            else:
                image_url = row.image

            if image_mode == "block":
                _add_image_block(cur_row, image_url)
            elif image_mode == "cover":
                cur_row.cover = image_url

        if row.icon:
            if isinstance(row.icon, Path):
                icon = self._upload_file(row.icon, cur_row)
            else:
                icon = row.icon

            cur_row.icon = icon

    @property
    def rows(self):
        if not self._cache_rows:
            self._cache_rows = self._collection_rows(self.collection.id)

        return self._cache_rows

    def relation(self, relation_column):
        if not self._cache_relations.get(relation_column):
            relation = self.schema[relation_column]
            relation_collection = self._collection(relation["collection_id"])
            if not relation_collection:
                raise KeyError
            self._cache_relations[relation_column] = {
                "name": self._collection_name(relation["collection_id"]),
                "rows": self._collection_rows(relation["collection_id"]),
                "collection": relation_collection,
            }

        return self._cache_relations[relation_column]

    def is_relation_has_duplicates(self, relation_column):
        relation = self.schema[relation_column]
        return self._validate_collection_duplicates(relation["collection_id"])

    def is_db_has_duplicates(self) -> bool:
        return self._validate_collection_duplicates(self.collection.id)

    def add_column(self, column_name: str, column_type: str):
        schema_raw = self.collection.get("schema")
        new_id = rand_id_unique(4, schema_raw)
        schema_raw[new_id] = {"name": column_name, "type": column_type}
        self.collection.set("schema", schema_raw)

        self.schema = {p["name"]: p for p in self.collection.get_schema_properties()}
        self._cache_rows = {}

    def add_relation_row(self, relation_column: str, key_value: str):
        relation = self.relation(relation_column)
        relation["rows"][key_value] = relation["collection"].add_row(title=key_value)

    def _add_row(self, row_data: NotionUploadRow):
        kwargs = {self.schema[k]["slug"]: v for k, v in row_data.items()}

        new_row = self.collection.add_row(**kwargs)

        self.rows[row_data.key()] = new_row

        return new_row

    def _update_row(self, row, row_data: NotionUploadRow):
        kwargs = {self.schema[k]["slug"]: v for k, v in row_data.items()}

        with self.client.as_atomic_transaction():
            for key, val in kwargs.items():
                setattr(row, key, val)

    def _upload_file(self, file_path: Path, block):
        file_mime = mimetypes.guess_type(str(file_path))[0]

        post_data = {
            "bucket": "secure",
            "name": file_path.name,
            "contentType": file_mime,
        }

        if block:
            post_data["record"] = {
                "table": "block",
                "id": block.id,
                "spaceId": block.space_info["spaceId"],
            }

        upload_data = self.client.post("getUploadFileUrl", post_data).json()

        # POST https://www.notion.so/api/v3/syncRecordValues
        # {"requests":[{"pointer":post_data["record"],"version":13}]}

        with open(file_path, "rb") as f:
            file_bin = f.read()

        response = requests.put(
            upload_data["signedPutUrl"],
            data=file_bin,
            headers={"Content-type": file_mime},
        )
        response.raise_for_status()

        return upload_data["url"]

    def _validate_collection_duplicates(self, collection_id: str) -> bool:
        collection = self._collection(collection_id)
        row_titles = [row.title for row in collection.get_rows()]

        return len(row_titles) != len(set(row_titles))

    def _collection_rows(self, collection_id):
        collection = self._collection(collection_id)
        rows = {}
        for row in sorted(collection.get_rows(), key=lambda r: r.title):
            rows.setdefault(row.title, row)
        return rows

    def _collection_name(self, collection_id):
        collection = self._collection(collection_id)
        return collection.name

    def _collection(self, collection_id):
        return self.client.get_collection(collection_id, force_refresh=True)


def _add_image_block(row: Block, image_url: str) -> None:
    attrs = {
        "display_source": image_url,
        "source": image_url,
        "caption": "cover",
    }

    if S3_URL_PREFIX in image_url:
        file_id = image_url[len(S3_URL_PREFIX) :].split("/")[0]
        attrs["file_id"] = file_id

    if row.children:
        first_block = row.children[0]
        if isinstance(first_block, ImageBlock) and first_block.caption == "cover":
            with row._client.as_atomic_transaction():
                for key, value in attrs.items():
                    setattr(first_block, key, value)
        else:
            new_block = row.children.add_new(ImageBlock, **attrs)
            new_block.move_to(row, "first-child")
    else:
        row.children.add_new("image", **attrs)
