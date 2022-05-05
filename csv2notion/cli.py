import argparse
import logging
import sys
from functools import partial
from pathlib import Path
from typing import List

from tqdm import tqdm

from csv2notion.csv_data import CSVData
from csv2notion.notion_convert import NotionRowConverter
from csv2notion.notion_convert_utils import map_icon
from csv2notion.notion_db import NotionDB, get_notion_client, make_new_db_from_csv
from csv2notion.utils import (
    ALLOWED_TYPES,
    CriticalError,
    NotionError,
    process_iter,
    setup_logging,
    split_str,
)
from csv2notion.version import __version__

logger = logging.getLogger(__name__)


def cli(argv: List[str]) -> None:
    args = parse_args(argv)

    setup_logging(log_file=args.log)

    logger.info("Validating CSV & Notion DB schema")

    csv_data = CSVData(
        args.csv_file, args.custom_types, args.fail_on_duplicate_csv_columns
    )

    if not csv_data:
        raise CriticalError("CSV file is empty")

    client = get_notion_client(args.token)

    if not args.url:
        logger.info("Creating new database")
        args.url = make_new_db_from_csv(
            client, page_name=args.csv_file.stem, csv_data=csv_data
        )
        logger.info(f"New database URL: {args.url}")

    notion_db = NotionDB(client, args.url)

    conversion_rules = {
        "files_search_path": args.csv_file.parent,
        "default_icon": args.default_icon,
        "image_column": args.image_column,
        "image_column_keep": args.image_column_keep,
        "icon_column": args.icon_column,
        "icon_column_keep": args.icon_column_keep,
        "mandatory_columns": args.mandatory_column,
        "is_merge": args.merge,
        "merge_only_columns": args.merge_only_column,
        "missing_columns_action": args.missing_columns_action,
        "missing_relations_action": args.missing_relations_action,
        "fail_on_relation_duplicates": args.fail_on_relation_duplicates,
        "fail_on_duplicates": args.fail_on_duplicates,
        "fail_on_conversion_error": args.fail_on_conversion_error,
        "fail_on_inaccessible_relations": args.fail_on_inaccessible_relations,
    }

    converter = NotionRowConverter(notion_db, conversion_rules)

    converter.prepare(csv_data)
    notion_rows = converter.convert_to_notion_rows(csv_data)

    logger.info(f"Uploading {args.csv_file.name}...")

    worker = partial(
        notion_db.upload_row, is_merge=args.merge, image_mode=args.image_column_mode
    )

    tdqm_iter = tqdm(
        iterable=process_iter(worker, notion_rows, max_workers=args.max_threads),
        total=len(notion_rows),
        leave=False,
    )

    for _ in tdqm_iter:
        pass

    logger.info("Done!")


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="csv2notion", description="Import/Merge CSV file into Notion database"
    )

    schema = {
        "csv_file": {
            "type": Path,
            "help": "CSV file to upload",
            "metavar": "FILE",
        },
        "--token": {
            "help": (
                "Notion token, stored in token_v2 cookie for notion.so"
                " [NEEDED FOR UPLOAD]"
            ),
            "required": True,
        },
        "--url": {
            "help": (
                "Notion database URL; if none is provided,"
                " will create a new database"
            ),
            "metavar": "URL",
        },
        "--max-threads": {
            "type": int,
            "default": 5,
            "help": "upload threads (default: 5)",
            "metavar": "NUMBER",
        },
        "--custom-types": {
            "help": (
                "comma-separated list of custom types to use for non-key columns;"
                " if none is provided, types will be guessed from CSV values"
                " (used when creating a new database or"
                " --missing-columns-action is set to 'add')"
            ),
            "metavar": "TYPES",
        },
        "--image-column": {
            "help": (
                "CSV column that points to URL or image file"
                " that will be embedded for that row"
            ),
            "metavar": "COLUMN",
        },
        "--image-column-keep": {
            "action": "store_true",
            "default": False,
            "help": "keep image CSV column as a Notion DB column",
        },
        "--image-column-mode": {
            "choices": ["cover", "block"],
            "default": "block",
            "help": (
                "upload image as [cover] or insert it as [block]" " (default: block)"
            ),
        },
        "--icon-column": {
            "help": (
                "CSV column that points to emoji, URL or image file"
                " that will be used as page icon for that row"
            ),
            "metavar": "COLUMN",
        },
        "--icon-column-keep": {
            "action": "store_true",
            "default": False,
            "help": "keep icon CSV column as a Notion DB column",
        },
        "--default-icon": {
            "help": (
                "Emoji, URL or image file"
                " that will be used as page icon for every row by default"
            ),
            "metavar": "ICON",
        },
        "--missing-columns-action": {
            "choices": ["add", "ignore", "fail"],
            "default": "ignore",
            "help": (
                "if columns are present in CSV but not in Notion DB,"
                " [add] them to Notion DB, [ignore] them or [fail] (default: ignore)"
            ),
        },
        "--missing-relations-action": {
            "choices": ["add", "ignore", "fail"],
            "default": "ignore",
            "help": (
                "if entries are missing from linked Notion DB,"
                " [add] them to Notion DB, [ignore] them or [fail] (default: ignore)"
            ),
        },
        "--fail-on-relation-duplicates": {
            "action": "store_true",
            "default": False,
            "help": (
                "fail if any linked DBs in relation columns have duplicate entries;"
                " otherwise, first entry in alphabetical order"
                " will be treated as unique when looking up relations"
            ),
        },
        "--fail-on-duplicates": {
            "action": "store_true",
            "default": False,
            "help": (
                "fail if Notion DB or CSV has duplicates in key column,"
                " useful when sanitizing before merge to avoid ambiguous mapping"
            ),
        },
        "--fail-on-duplicate-csv-columns": {
            "action": "store_true",
            "default": False,
            "help": (
                "fail if CSV has duplicate columns; otherwise last column will be used"
            ),
        },
        "--fail-on-conversion-error": {
            "action": "store_true",
            "default": False,
            "help": (
                "fail if any column type conversion error occurs;"
                " otherwise errors will be replaced with empty strings"
            ),
        },
        "--fail-on-inaccessible-relations": {
            "action": "store_true",
            "default": False,
            "help": (
                "fail if any relation column points to a Notion DB that"
                " is not accessible to the current user;"
                " otherwise those columns will be ignored"
            ),
        },
        "--merge": {
            "action": "store_true",
            "default": False,
            "help": (
                "merge CSV with existing Notion DB rows,"
                " first column will be used as a key"
            ),
        },
        "--merge-only-column": {
            "action": "append",
            "help": (
                "CSV column that should be updated on merge;"
                " when provided, other columns will be ignored"
                " (define multiple times for multiple columns)"
            ),
            "metavar": "COLUMN",
        },
        "--mandatory-column": {
            "action": "append",
            "help": (
                "CSV column that cannot be empty"
                " (define multiple times for multiple columns)"
            ),
            "metavar": "COLUMN",
        },
        "--log": {
            "type": Path,
            "metavar": "FILE",
            "help": "file to store program log",
        },
        "--version": {
            "action": "version",
            "version": f"%(prog)s {__version__}",
        },
    }

    for arg, arg_params in schema.items():
        parser.add_argument(arg, **arg_params)

    parsed_args = parser.parse_args(argv)

    if parsed_args.mandatory_column is None:
        parsed_args.mandatory_column = []

    if parsed_args.merge_only_column is None:
        parsed_args.merge_only_column = []

    parsed_args.max_threads = max(parsed_args.max_threads, 1)

    if parsed_args.custom_types:
        parsed_args.custom_types = split_str(parsed_args.custom_types, ",")
        unknown_types = set(parsed_args.custom_types) - set(ALLOWED_TYPES)
        if unknown_types:
            raise CriticalError(
                f"Unknown types: {', '.join(unknown_types)};"
                f" allowed types: {', '.join(ALLOWED_TYPES)}"
            )

    if parsed_args.default_icon:
        parsed_args.default_icon = map_icon(parsed_args.default_icon)
        if isinstance(parsed_args.default_icon, Path):
            if not parsed_args.default_icon.exists():
                raise CriticalError(f"File not found: {parsed_args.default_icon}")

    return parsed_args


def critical_error(msg: str) -> None:
    logger.critical(msg)
    sys.exit(1)


def main() -> None:
    try:
        cli(sys.argv[1:])
    except (NotionError, CriticalError) as e:
        critical_error(str(e))
    except KeyboardInterrupt:
        sys.exit(1)
