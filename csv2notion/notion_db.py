from typing import List

import requests
from notion.client import NotionClient
from notion.collection import Collection
from notion.utils import InvalidNotionIdentifier

from csv2notion.csv_data import CSVData
from csv2notion.notion_row import CollectionRowBlockExtended
from csv2notion.utils_exceptions import NotionError
from csv2notion.utils_rand_id import rand_id_list, rand_id_unique


class NotionDB(object):  # noqa: WPS214
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

    @property
    def rows(self):
        if not self._cache_rows:
            self._cache_rows = self._collection_rows(self.collection.id)

        return self._cache_rows

    def relation(self, relation_column: str):
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

    def is_relation_has_duplicates(self, relation_column: str) -> bool:
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

    def add_row(self, properties=None, columns=None):
        return self.collection.add_row_block(
            row_class=CollectionRowBlockExtended, properties=properties, columns=columns
        )

    def _validate_collection_duplicates(self, collection_id: str) -> bool:
        collection = self._collection(collection_id)
        row_titles = [row.title for row in collection.get_rows()]

        return len(row_titles) != len(set(row_titles))

    def _collection_rows(self, collection_id: str) -> dict:
        collection = self._collection(collection_id)
        rows = {}
        for row in sorted(collection.get_rows(), key=lambda r: r.title):
            row_conv = CollectionRowBlockExtended(row._client, row._id)
            rows.setdefault(row.title, row_conv)
        return rows

    def _collection_name(self, collection_id: str) -> str:
        collection = self._collection(collection_id)
        return collection.name

    def _collection(self, collection_id: str) -> Collection:
        return self.client.get_collection(collection_id, force_refresh=True)


def make_new_db_from_csv(
    client: NotionClient,
    page_name: str,
    csv_data: CSVData,
    skip_columns: List[str] = None,
) -> str:
    schema = _schema_from_csv(csv_data, skip_columns)

    page_id = client.create_record(
        "block",
        client.current_space,
        type="collection_view_page",
        permissions=[
            {
                "role": "editor",
                "type": "user_permission",
                "user_id": client.current_user.id,
            }
        ],
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


def _schema_from_csv(csv_data: CSVData, skip_columns: List[str] = None) -> dict:
    if skip_columns:
        columns = [c for c in csv_data.columns if c not in skip_columns]
    else:
        columns = csv_data.columns

    schema_ids = rand_id_list(len(columns) - 1, 4)

    schema = {"title": {"name": columns[0], "type": "title"}}

    for col_id, col_key in zip(schema_ids, columns[1:]):
        schema[col_id] = {
            "name": col_key,
            "type": csv_data.col_type(col_key),
        }

    return schema


def get_notion_client(token: str):
    try:
        return NotionClient(token_v2=token)
    except requests.exceptions.HTTPError as e:
        raise NotionError("Invalid Notion token") from e
