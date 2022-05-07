import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from csv2notion.notion_db import NotionDB, get_notion_client


class ThreadRowUploader(object):
    def __init__(self, token, url):
        self.thread_data = threading.local()

        self.token = token
        self.url = url

    def worker(self, *args, **kwargs):
        try:
            notion_db = self.thread_data.db
        except AttributeError:
            client = get_notion_client(self.token)
            notion_db = NotionDB(client, self.url)
            self.thread_data.db = notion_db

        notion_db.upload_row(*args, **kwargs)


def process_iter(worker, tasks, max_workers):
    if max_workers == 1:
        for task in tasks:
            yield worker(task)
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(worker, t) for t in tasks]

            for future in as_completed(futures):
                yield future.result()
