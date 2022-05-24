import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Iterable, Iterator

from notion.client import NotionClient

from csv2notion.notion_db import NotionDB
from csv2notion.notion_db_client import ClonableNotionClient
from csv2notion.notion_uploader import NotionRowUploader


class ThreadRowUploader(object):
    def __init__(self, client: NotionClient, collection_id: str) -> None:
        self.thread_data = threading.local()

        self.client = client
        self.collection_id = collection_id

    def worker(self, *args: Any, **kwargs: Any) -> None:
        try:
            notion_uploader = self.thread_data.uploader
        except AttributeError:
            client = ClonableNotionClient(old_client=self.client)
            notion_db = NotionDB(client, self.collection_id)
            notion_uploader = NotionRowUploader(notion_db)
            self.thread_data.uploader = notion_uploader

        notion_uploader.upload_row(*args, **kwargs)


def process_iter(
    worker: Callable[[Any], None], tasks: Iterable[Any], max_workers: int
) -> Iterator[None]:
    if max_workers == 1:
        yield from map(worker, tasks)
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(worker, t) for t in tasks]

            yield from (f.result() for f in as_completed(futures))
