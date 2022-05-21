import logging
from argparse import Namespace
from functools import partial
from typing import List

from notion.client import NotionClient
from tqdm import tqdm

from csv2notion.csv_data import CSVData
from csv2notion.notion_convert import NotionRowConverter
from csv2notion.notion_db import NotionDB, notion_db_from_csv
from csv2notion.notion_preparator import NotionPreparator
from csv2notion.notion_uploader import NotionUploadRow
from csv2notion.utils_threading import ThreadRowUploader, process_iter

logger = logging.getLogger(__name__)


def new_database(args: Namespace, client: NotionClient, csv_data: CSVData) -> str:
    skip_columns = []
    if args.image_column and not args.image_column_keep:
        skip_columns.append(args.image_column)
    if args.icon_column and not args.icon_column_keep:
        skip_columns.append(args.icon_column)
    if args.image_caption_column and not args.image_caption_column_keep:
        skip_columns.append(args.image_caption_column)

    logger.info("Creating new database")

    url, collection_id = notion_db_from_csv(
        client,
        page_name=args.csv_file.stem,
        csv_data=csv_data,
        skip_columns=skip_columns,
    )

    logger.info(f"New database URL: {url}")

    return collection_id


def convert_csv_to_notion_rows(
    csv_data: CSVData, client: NotionClient, collection_id: str, args: Namespace
) -> List[NotionUploadRow]:
    notion_db = NotionDB(client, collection_id)

    conversion_rules = {
        "files_search_path": args.csv_file.parent,
        "default_icon": args.default_icon,
        "image_column": args.image_column,
        "image_column_keep": args.image_column_keep,
        "image_column_mode": args.image_column_mode,
        "image_caption_column": args.image_caption_column,
        "image_caption_column_keep": args.image_caption_column_keep,
        "icon_column": args.icon_column,
        "icon_column_keep": args.icon_column_keep,
        "mandatory_columns": args.mandatory_column,
        "is_merge": args.merge,
        "merge_only_columns": args.merge_only_column,
        "merge_skip_new": args.merge_skip_new,
        "missing_columns_action": args.missing_columns_action,
        "missing_relations_action": args.missing_relations_action,
        "fail_on_relation_duplicates": args.fail_on_relation_duplicates,
        "fail_on_duplicates": args.fail_on_duplicates,
        "fail_on_conversion_error": args.fail_on_conversion_error,
        "fail_on_inaccessible_relations": args.fail_on_inaccessible_relations,
        "fail_on_unsupported_columns": args.fail_on_unsupported_columns,
    }

    NotionPreparator(notion_db, csv_data, conversion_rules).prepare()

    converter = NotionRowConverter(notion_db, conversion_rules)
    return converter.convert_to_notion_rows(csv_data)


def upload_rows(
    notion_rows: List[NotionUploadRow],
    token: str,
    collection_id: str,
    is_merge: bool,
    max_threads: int,
) -> None:
    worker = partial(
        ThreadRowUploader(token, collection_id).worker,
        is_merge=is_merge,
    )

    tdqm_iter = tqdm(
        iterable=process_iter(worker, notion_rows, max_workers=max_threads),
        total=len(notion_rows),
        leave=False,
    )

    # Consume iterator
    list(tdqm_iter)
