from datetime import datetime
from pathlib import Path
from typing import Optional, Union

from dateutil.parser import ParserError
from dateutil.parser import parse as date_parse
from emoji import distinct_emoji_list, emoji_count, replace_emoji
from notion.collection import NotionDate

from csv2notion.notion_type_guess import is_url
from csv2notion.utils_exceptions import TypeConversionError
from csv2notion.utils_static import FileType
from csv2notion.utils_str import split_str


def map_checkbox(s: str) -> bool:
    return s == "true"


def map_date(s: str) -> datetime:
    try:
        return date_parse(s)
    except ParserError as e:
        raise TypeConversionError(e) from e


def map_notion_date(s: str) -> NotionDate:
    dates = split_str(s)

    if not dates:
        raise TypeConversionError("Date field is empty")

    if len(dates) > 2:
        raise TypeConversionError("Date field doesn't support more than 2 values")

    if len(dates) == 2:
        return NotionDate(start=map_date(dates[0]), end=map_date(dates[1]))

    return NotionDate(start=map_date(dates[0]))


def map_number(s: str) -> Union[int, float]:
    try:
        float_value = float(s)
    except ValueError as e:
        raise TypeConversionError(e) from e

    if float_value.is_integer():
        return int(float_value)

    return float_value


def map_icon(s: str) -> FileType:
    icon_emoji = _get_icon_emoji(s)
    if icon_emoji:
        return icon_emoji

    return s if is_url(s) else Path(s)


def map_url_or_file(s: str) -> FileType:
    return s if is_url(s) else Path(s)


def _get_icon_emoji(s: str) -> Optional[str]:
    # string has anything other than emoji
    if replace_emoji(s) != "":
        return None

    # string must contain exactly one emoji for icon
    if emoji_count(s) != 1:
        return None

    return str(distinct_emoji_list(s)[0])
