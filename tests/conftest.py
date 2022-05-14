import base64
import json
import os
import uuid
from pathlib import Path

import pytest
from notion.client import NotionClient
from pyfakefs.fake_filesystem_unittest import Patcher

from csv2notion.csv_data import CSVData
from csv2notion.notion_db import make_new_db_from_csv
from csv2notion.utils_rand_id import rand_id


@pytest.fixture(scope="module")
def vcr_config():
    """Remove meta bloat to reduce cassette size"""

    def response_cleaner(response):
        bloat_headers = [
            "Content-Security-Policy",
            "Expect-CT",
            "ETag",
            "Referrer-Policy",
            "Strict-Transport-Security",
            "Vary",
            "Date",
            "Server",
            "Connection",
            "Set-Cookie",
        ]

        for h in response["headers"].copy():
            if h.startswith("X-") or h.startswith("CF-") or h in bloat_headers:
                response["headers"].pop(h)

        return response

    return {
        "filter_headers": [
            ("cookie", "PRIVATE"),
            "Accept",
            "Accept-Encoding",
            "Connection",
            "User-Agent",
        ],
        "before_record_response": response_cleaner,
        "decode_compressed_response": True,
    }


@pytest.fixture()
def vcr_uuid4(mocker, vcr_cassette_dir, vcr_cassette_name):
    uuid_casette_path = Path(vcr_cassette_dir) / f"{vcr_cassette_name}.uuid4.json"

    if uuid_casette_path.exists():
        with open(uuid_casette_path, "r") as f:
            uuid_casette = [uuid.UUID(u) for u in json.load(f)]

        mocker.patch("uuid.uuid4", side_effect=uuid_casette)
    else:
        uuid_casette = []

        orign_uuid4 = uuid.uuid4

        def uuid4():
            u = orign_uuid4()
            uuid_casette.append(u)
            return u

        mocker.patch("uuid.uuid4", side_effect=uuid4)

    yield

    if not uuid_casette_path.exists() and uuid_casette:
        uuid_casette_path.parent.mkdir(parents=True, exist_ok=True)

        with open(uuid_casette_path, "w") as f:
            json.dump([str(u) for u in uuid_casette], f)


class NotionDB(object):
    def __init__(self, page, url):
        self.page = page
        self.url = url

    def set_relation(self, column_name, relation_db):
        schema_raw = self.page.collection.get("schema")

        col_id = next(k for k, v in schema_raw.items() if v["name"] == column_name)

        schema_raw[col_id] = {
            "name": column_name,
            "type": "relation",
            "property": rand_id(4),
            "collection_id": relation_db.page.collection.id,
            "collection_pointer": {
                "id": relation_db.page.collection.id,
                "spaceId": relation_db.page.space_info["spaceId"],
                "table": "collection",
            },
        }
        self.page.collection.set("schema", schema_raw)

    def add_row(self, row):
        kwargs = {self.schema_dict[k]["slug"]: v for k, v in row.items()}
        return self.page.collection.add_row(**kwargs)

    @property
    def header(self):
        return set(self.schema_dict.keys())

    @property
    def default_view(self):
        return list(self.page.views)[0]

    @property
    def default_view_header(self):
        header_order = self.default_view.get(
            "format.table_properties", force_refresh=True
        )

        # if header order is not set explicitly, it will be in alphabetical order
        if not header_order:
            first_column = next(c["name"] for c in self.schema if c["type"] == "title")
            other_columns = [c["name"] for c in self.schema if c["type"] != "title"]
            return [first_column] + sorted(other_columns)

        view_header = []
        for h in header_order:
            h_key = next(
                k for k, v in self.schema_dict.items() if v["id"] == h["property"]
            )
            view_header.append(h_key)

        return view_header

    @property
    def schema(self):
        return self.page.collection.get_schema_properties()

    @property
    def schema_dict(self):
        return {p["name"]: p for p in self.schema}

    @property
    def rows(self):
        key_column_slug = next(k["slug"] for k in self.schema if k["type"] == "title")
        return sorted(
            self.page.collection.get_rows(), key=lambda r: getattr(r, key_column_slug)
        )

    def refresh(self):
        self.page.refresh()

    def remove(self):
        if self.page:
            self.page.remove(permanently=True)
            self.page = None


class NotionDBMaker(object):
    def __init__(self, client, token, page_name):
        self.client = client
        self.token = token
        self.page_name = page_name
        self.databases = []

    def from_csv_head(self, csv_head):
        col_number = len(csv_head.split(","))
        csv_body = ",".join(["test"] * col_number)
        csv_content = f"{csv_head}\n{csv_body}"

        with Patcher() as patcher:
            patcher.fs.create_file("test.csv", contents=csv_content)
            csv_data = CSVData(Path("test.csv"))

        url = make_new_db_from_csv(
            self.client, page_name=self.page_name, csv_data=csv_data
        )

        return self.from_url(url)

    def from_url(self, url):
        page = self.client.get_block(url)

        new_db = NotionDB(page, url)

        self.databases.append(new_db)

        return new_db

    def cleanup(self):
        for db in self.databases:
            db.remove()
        self.databases = []


@pytest.fixture()
def db_maker(vcr_cassette_dir, vcr_cassette_name):
    casette_path = Path(vcr_cassette_dir) / f"{vcr_cassette_name}.yaml"

    # if cassette exists and no token, probably CI test
    if casette_path.exists() and not os.environ.get("NOTION_TEST_TOKEN"):
        token = "fake_token"
    else:
        token = os.environ.get("NOTION_TEST_TOKEN")

    if not token:
        raise RuntimeError(
            "No token found. Set NOTION_TEST_TOKEN environment variable."
        )

    client = NotionClient(token_v2=token)

    test_page_title = "TESTING PAGE"

    try:
        top_pages = client.get_top_level_pages()
    except KeyError:  # pragma: no cover
        # Need empty account to test
        top_pages = []

    for page in top_pages.copy():
        try:
            if page.title == test_page_title:
                page.remove(permanently=True)
        except AttributeError:
            page.remove(permanently=True)

    if top_pages:
        raise RuntimeError("Testing requires empty account")

    db_maker = NotionDBMaker(client, token, test_page_title)

    yield db_maker

    db_maker.cleanup()


@pytest.fixture()
def smallest_gif():
    yield base64.b64decode("R0lGODlhAQABAAAAACH5BAEAAAAALAAAAAABAAEAAAIA")
