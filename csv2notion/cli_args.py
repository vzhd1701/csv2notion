import argparse
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple, Union

from csv2notion.notion_convert_map import map_icon
from csv2notion.utils_exceptions import CriticalError
from csv2notion.utils_static import ALLOWED_TYPES, FileType
from csv2notion.utils_str import split_str
from csv2notion.version import __version__

ArgToken = Union[str, Tuple[str, str]]
ArgOption = Dict[str, Any]
ArgSchema = Dict[str, Dict[ArgToken, ArgOption]]
HELP_ARGS_WIDTH = 50


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="csv2notion",
        description="Import/Merge CSV file into Notion database",
        usage="%(prog)s [-h] --token TOKEN [--url URL] [OPTION]... FILE",
        add_help=False,
        formatter_class=lambda prog: argparse.RawTextHelpFormatter(
            prog, max_help_position=HELP_ARGS_WIDTH
        ),
    )

    schema: ArgSchema = {
        "POSITIONAL": {
            "csv_file": {
                "type": Path,
                "help": "CSV file to upload",
                "metavar": "FILE",
            }
        },
        "general options": {
            "--token": {
                "help": "Notion token, stored in token_v2 cookie for notion.so",
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
                "type": lambda x: max(int(x), 1),
                "default": 5,
                "help": "upload threads (default: 5)",
                "metavar": "NUMBER",
            },
            "--log": {
                "type": Path,
                "metavar": "FILE",
                "help": "file to store program log",
            },
            "--verbose": {
                "action": "store_true",
                "help": "output debug information",
            },
            "--version": {
                "action": "version",
                "version": f"%(prog)s {__version__}",
            },
            ("-h", "--help"): {
                "action": "help",
                "help": "show this help message and exit",
            },
        },
        "column options": {
            "--column-types": {
                "help": (
                    "comma-separated list of column types to use for non-key columns;"
                    "\nif none is provided, types will be guessed from CSV values"
                    "\n(can also be used with --add-missing-columns flag)"
                ),
                "metavar": "TYPES",
                "type": _parse_column_types,
            },
            "--add-missing-columns": {
                "action": "store_true",
                "help": (
                    "if columns are present in CSV but not in Notion DB,"
                    " add them to Notion DB"
                ),
            },
        },
        "merge options": {
            "--merge": {
                "action": "store_true",
                "help": (
                    "merge CSV with existing Notion DB rows,"
                    " first column will be used as a key"
                ),
            },
            "--merge-only-column": {
                "action": "append",
                "help": (
                    "CSV column that should be updated on merge;"
                    "\nwhen provided, other columns will be ignored"
                    "\n(use multiple times for multiple columns)"
                ),
                "metavar": "COLUMN",
                "default": [],
            },
            "--merge-skip-new": {
                "action": "store_true",
                "help": (
                    "skip new rows in CSV that are not already in Notion DB"
                    " during merge"
                ),
            },
        },
        "relations options": {
            "--add-missing-relations": {
                "action": "store_true",
                "help": "add missing entries into linked Notion DB",
            },
        },
        "page cover options": {
            "--image-column": {
                "help": (
                    "CSV column that points to URL or image file"
                    " that will be embedded for that row"
                ),
                "metavar": "COLUMN",
            },
            "--image-column-keep": {
                "action": "store_true",
                "help": "keep image CSV column as a Notion DB column",
            },
            "--image-column-mode": {
                "choices": ["cover", "block"],
                "default": "block",
                "help": (
                    "upload image as [cover] or insert it as [block]"
                    " (default: block)"
                ),
            },
            "--image-caption-column": {
                "help": (
                    "CSV column that points to text caption"
                    " that will be added to the image block"
                    "\nif --image-column-mode is set to 'block'"
                ),
                "metavar": "COLUMN",
            },
            "--image-caption-column-keep": {
                "action": "store_true",
                "help": "keep image caption CSV column as a Notion DB column",
            },
        },
        "page icon options": {
            "--icon-column": {
                "help": (
                    "CSV column that points to emoji, URL or image file"
                    "\nthat will be used as page icon for that row"
                ),
                "metavar": "COLUMN",
            },
            "--icon-column-keep": {
                "action": "store_true",
                "help": "keep icon CSV column as a Notion DB column",
            },
            "--default-icon": {
                "help": (
                    "Emoji, URL or image file"
                    " that will be used as page icon for every row by default"
                ),
                "metavar": "ICON",
                "type": _parse_default_icon,
            },
        },
        "validation options": {
            "--mandatory-column": {
                "action": "append",
                "help": (
                    "CSV column that cannot be empty"
                    " (use multiple times for multiple columns)"
                ),
                "metavar": "COLUMN",
                "default": [],
            },
            "--fail-on-relation-duplicates": {
                "action": "store_true",
                "help": (
                    "fail if any linked DBs in relation columns have duplicate entries;"
                    "\notherwise, first entry in alphabetical order"
                    "\nwill be treated as unique when looking up relations"
                ),
            },
            "--fail-on-duplicates": {
                "action": "store_true",
                "help": (
                    "fail if Notion DB or CSV has duplicates in key column,"
                    "\nuseful when sanitizing before merge to avoid ambiguous mapping"
                ),
            },
            "--fail-on-duplicate-csv-columns": {
                "action": "store_true",
                "help": (
                    "fail if CSV has duplicate columns;"
                    "\notherwise last column will be used"
                ),
            },
            "--fail-on-conversion-error": {
                "action": "store_true",
                "help": (
                    "fail if any column type conversion error occurs;"
                    "\notherwise errors will be replaced with empty strings"
                ),
            },
            "--fail-on-inaccessible-relations": {
                "action": "store_true",
                "help": (
                    "fail if any relation column points to a Notion DB that"
                    "\nis not accessible to the current user;"
                    "\notherwise those columns will be ignored"
                ),
            },
            "--fail-on-missing-columns": {
                "action": "store_true",
                "help": (
                    "fail if columns are present in CSV but not in Notion DB;"
                    "\notherwise those columns will be ignored"
                ),
            },
            "--fail-on-unsettable-columns": {
                "action": "store_true",
                "help": (
                    "fail if DB has columns that don't support assigning value to them;"
                    "\notherwise those columns will be ignored"
                    "\n(columns with type created_by, last_edited_by,"
                    " rollup or formula)"
                ),
            },
        },
    }

    _parse_schema(parser, schema)

    return parser.parse_args(argv)


def _parse_schema(  # noqa: WPS210
    parser: argparse.ArgumentParser, schema: ArgSchema
) -> None:
    group: argparse._ActionsContainer

    for group_name, group_args in schema.items():
        if group_name == "POSITIONAL":
            group = parser
        else:
            group = parser.add_argument_group(group_name)

        for arg, arg_params in group_args.items():
            opt_arg = [arg] if isinstance(arg, str) else arg
            group.add_argument(*opt_arg, **arg_params)


def _parse_default_icon(default_icon: str) -> FileType:
    default_icon_filetype = map_icon(default_icon)
    if isinstance(default_icon_filetype, Path):
        if not default_icon_filetype.exists():
            raise CriticalError(f"File not found: {default_icon_filetype}")
    return default_icon_filetype


def _parse_column_types(column_types: str) -> List[str]:
    column_types_list = split_str(column_types)
    unknown_types = set(column_types_list) - set(ALLOWED_TYPES)
    if unknown_types:
        raise CriticalError(
            "Unknown types: {0}; allowed types: {1}".format(
                ", ".join(unknown_types), ", ".join(ALLOWED_TYPES)
            )
        )
    return column_types_list
