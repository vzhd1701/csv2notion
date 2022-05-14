import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from csv2notion.notion_db import NotionDB, get_notion_client
from csv2notion.notion_uploader import NotionRowUploader


class ThreadRowUploader(object):
    def __init__(self, token, url):
        self.thread_data = threading.local()

        self.token = token
        self.url = url

    def worker(self, *args, **kwargs):
        try:
            notion_uploader = self.thread_data.uploader
        except AttributeError:
            client = get_notion_client(self.token)
            notion_db = NotionDB(client, self.url)
            notion_uploader = NotionRowUploader(notion_db)
            self.thread_data.uploader = notion_uploader

        notion_uploader.upload_row(*args, **kwargs)


def process_iter(worker, tasks, max_workers):
    if max_workers == 1:
        yield from map(worker, tasks)
    else:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(worker, t) for t in tasks]

            yield from (f.result() for f in as_completed(futures))
