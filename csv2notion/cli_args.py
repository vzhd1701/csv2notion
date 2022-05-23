import argparse
from pathlib import Path
from typing import Any, Dict, List, Sequence

from csv2notion.notion_convert_map import map_icon
from csv2notion.utils_exceptions import CriticalError
from csv2notion.utils_static import ALLOWED_TYPES, FileType
from csv2notion.utils_str import split_str
from csv2notion.version import __version__


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="csv2notion", description="Import/Merge CSV file into Notion database"
    )

    schema: Dict[str, Dict[str, Any]] = {
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
        "--image-caption-column": {
            "help": (
                "CSV column that points to text caption"
                " that will be added to the image block"
                " if --image-column-mode is set to 'block'"
            ),
            "metavar": "COLUMN",
        },
        "--image-caption-column-keep": {
            "action": "store_true",
            "default": False,
            "help": "keep image caption CSV column as a Notion DB column",
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
        "--add-missing-columns": {
            "action": "store_true",
            "default": False,
            "help": (
                "if columns are present in CSV but not in Notion DB,"
                " add them to Notion DB"
            ),
        },
        "--add-missing-relations": {
            "action": "store_true",
            "default": False,
            "help": "add missing entries into linked Notion DB",
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
        "--fail-on-missing-columns": {
            "action": "store_true",
            "default": False,
            "help": (
                "fail if columns are present in CSV but not in Notion DB;"
                " otherwise those columns will be ignored"
            ),
        },
        "--fail-on-unsupported-columns": {
            "action": "store_true",
            "default": False,
            "help": (
                "fail if DB has columns that are not supported by this tool;"
                " otherwise those columns will be ignored"
                " (columns with type created_by, last_edited_by, rollup or formula)"
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
                " (use multiple times for multiple columns)"
            ),
            "metavar": "COLUMN",
        },
        "--merge-skip-new": {
            "action": "store_true",
            "default": False,
            "help": (
                "skip new rows in CSV that are not already in Notion DB during merge"
            ),
        },
        "--mandatory-column": {
            "action": "append",
            "help": (
                "CSV column that cannot be empty"
                " (use multiple times for multiple columns)"
            ),
            "metavar": "COLUMN",
        },
        "--log": {
            "type": Path,
            "metavar": "FILE",
            "help": "file to store program log",
        },
        "--verbose": {
            "action": "store_true",
            "default": False,
            "help": "output debug information",
        },
        "--version": {
            "action": "version",
            "version": f"%(prog)s {__version__}",
        },
    }

    for arg, arg_params in schema.items():
        parser.add_argument(arg, **arg_params)

    parsed_args = parser.parse_args(argv)

    _post_process_args(parsed_args)

    return parsed_args


def _post_process_args(parsed_args: argparse.Namespace) -> None:
    if parsed_args.mandatory_column is None:
        parsed_args.mandatory_column = []

    if parsed_args.merge_only_column is None:
        parsed_args.merge_only_column = []

    parsed_args.max_threads = max(parsed_args.max_threads, 1)

    if parsed_args.custom_types:
        parsed_args.custom_types = _parse_custom_types(parsed_args.custom_types)

    if parsed_args.default_icon:
        parsed_args.default_icon = _parse_default_icon(parsed_args.default_icon)


def _parse_default_icon(default_icon: str) -> FileType:
    default_icon_filetype = map_icon(default_icon)
    if isinstance(default_icon_filetype, Path):
        if not default_icon_filetype.exists():
            raise CriticalError(f"File not found: {default_icon_filetype}")
    return default_icon_filetype


def _parse_custom_types(custom_types: str) -> List[str]:
    custom_types_list = split_str(custom_types)
    unknown_types = set(custom_types_list) - set(ALLOWED_TYPES)
    if unknown_types:
        raise CriticalError(
            "Unknown types: {0}; allowed types: {1}".format(
                ", ".join(unknown_types), ", ".join(ALLOWED_TYPES)
            )
        )
    return custom_types_list
