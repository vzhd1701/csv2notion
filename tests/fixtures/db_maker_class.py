import logging
import re
from pathlib import Path

from notion.user import User
from pyfakefs.fake_filesystem_unittest import Patcher
from testfixtures import LogCapture, ShouldRaise

from csv2notion.cli import cli
from csv2notion.csv_data import CSVData
from csv2notion.notion_db import notion_db_from_csv
from tests.fixtures.db_maker_notion_db import NotionDB


class NotionDBMaker(object):
    def __init__(self, client, token, page_name):
        self.client = client
        self.token = token
        self.page_name = page_name
        self.databases = []

    def from_csv_head(self, csv_head) -> NotionDB:
        col_number = len(csv_head.split(","))
        csv_body = ",".join(["test"] * col_number)  # noqa: WPS435
        csv_content = f"{csv_head}\n{csv_body}"

        with Patcher() as patcher:
            patcher.fs.create_file("test.csv", contents=csv_content)
            csv_data = CSVData(Path("test.csv"))

        url, collection_id = notion_db_from_csv(
            self.client, page_name=self.page_name, csv_data=csv_data
        )

        return self.from_url(url)

    def from_url(self, url) -> NotionDB:
        page = self.client.get_block(url)

        new_db = NotionDB(page, url)

        self.databases.append(new_db)

        return new_db

    def from_cli(self, *args: str) -> NotionDB:
        with LogCapture("csv2notion", level=logging.INFO) as log:
            cli(*args)

        url = re.search("New database URL: (.*)$", str(log), re.M)[1]

        return self.from_url(url)

    def from_raising_cli(self, *args: str) -> ShouldRaise:
        with ShouldRaise() as e:
            with LogCapture("csv2notion", level=logging.INFO) as log:
                cli(*args)

        url = re.search("New database URL: (.*)$", str(log), re.M)[1]

        self.from_url(url)

        return e

    def find_user(self, email: str):
        res = self.client.post("findUser", {"email": email}).json()

        try:
            user_id = res["value"]["value"]["id"]
        except KeyError:
            return None

        return User(self.client, user_id)

    def cleanup(self):
        for db in self.databases:
            db.remove()
        self.databases = []
