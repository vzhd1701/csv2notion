from typing import Any, Dict, List, Optional, Tuple

import requests
from notion.client import NotionClient
from notion.user import User
from notion.utils import InvalidNotionIdentifier

from csv2notion.csv_data import CSVData
from csv2notion.notion_db_collection import CollectionExtended
from csv2notion.notion_row import CollectionRowBlockExtended
from csv2notion.utils_exceptions import NotionError
from csv2notion.utils_rand_id import rand_id_list


class NotionDB(object):  # noqa: WPS214
    def __init__(self, client: NotionClient, collection_id: str):
        self.client = client
        self.collection = CollectionExtended(self.client, collection_id)

        self._cache_columns: Dict[str, Dict[str, str]] = {}
        self._cache_relations: Dict[str, NotionDB] = {}
        self._cache_rows: Dict[str, CollectionRowBlockExtended] = {}
        self._cache_users: Dict[str, User] = {}

    @property
    def name(self) -> str:
        return str(self.collection.name)

    @property
    def columns(self) -> Dict[str, Dict[str, str]]:
        if not self._cache_columns:
            self._cache_columns = {
                p["name"]: p for p in self.collection.get_schema_properties()
            }

        return self._cache_columns

    @property
    def key_column(self) -> str:
        column_values = self.columns.values()
        return next(c["name"] for c in column_values if c["type"] == "title")

    @property
    def rows(self) -> Dict[str, CollectionRowBlockExtended]:
        if not self._cache_rows:
            self._cache_rows = self.collection.get_unique_rows()

        return self._cache_rows

    @property
    def relations(self) -> Dict[str, "NotionDB"]:
        if not self._cache_relations:
            relations = [c for c in self.columns.values() if c["type"] == "relation"]

            self._cache_relations = {
                r["name"]: NotionDB(self.client, r["collection_id"]) for r in relations
            }

        return self._cache_relations

    @property
    def users(self) -> Dict[str, User]:
        if not self._cache_users:
            self._cache_users = {u.email: u for u in self.client.current_space.users}

        return self._cache_users

    def get_user_by_name(self, name: str) -> Optional[User]:
        name_match = (u for u in self.users.values() if u.name == name)
        return next(name_match, None)

    def find_user(self, email: str) -> Optional[User]:
        res = self.client.post("findUser", {"email": email}).json()

        try:
            user_id = res["value"]["value"]["id"]
        except KeyError:
            return None

        found_user = User(self.client, user_id)

        self.users[found_user.email] = found_user

        return found_user

    def has_duplicates(self) -> bool:
        return self.collection.has_duplicates()

    def is_accessible(self) -> bool:
        return self.collection.is_accessible()

    def add_column(self, column_name: str, column_type: str) -> None:
        self.collection.add_column(column_name, column_type)

        self._cache_columns = {}
        self._cache_rows = {}

    def add_row(
        self,
        properties: Optional[Dict[str, Any]] = None,
        columns: Optional[Dict[str, Any]] = None,
    ) -> CollectionRowBlockExtended:
        new_row = self.collection.add_row_block(properties=properties, columns=columns)

        key = columns.get(self.key_column) if columns else None
        if key:
            self.rows[key] = new_row

        return new_row

    def add_row_key(self, key: str) -> CollectionRowBlockExtended:
        return self.add_row(columns={self.key_column: key})


def get_collection_id(client: NotionClient, notion_url: str) -> str:
    try:
        block = client.get_block(notion_url, force_refresh=True)
    except InvalidNotionIdentifier as e:
        raise NotionError("Invalid URL.") from e

    if block.type != "collection_view_page":
        raise NotionError("Provided URL links does not point to a Notion database.")

    return str(block.collection.id)


def notion_db_from_csv(
    client: NotionClient,
    page_name: str,
    csv_data: CSVData,
    skip_columns: Optional[List[str]] = None,
) -> Tuple[str, str]:
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

    return str(page.get_browseable_url()), page.collection.id


def _schema_from_csv(
    csv_data: CSVData, skip_columns: Optional[List[str]] = None
) -> Dict[str, Dict[str, str]]:
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


def get_notion_client(token: str) -> NotionClient:
    try:
        return NotionClient(token_v2=token)
    except requests.exceptions.HTTPError as e:
        raise NotionError("Invalid Notion token") from e
