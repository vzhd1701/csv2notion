from datetime import datetime
from pathlib import Path
from typing import Union

from dateutil.parser import ParserError
from dateutil.parser import parse as date_parse
from emoji import is_emoji

from csv2notion.notion_type_guess import is_url
from csv2notion.utils_exceptions import TypeConversionError


def map_checkbox(s: str) -> bool:
    return s == "true"


def map_date(s: str) -> datetime:
    try:
        return date_parse(s)
    except ParserError as e:
        raise TypeConversionError(e) from e


def map_number(s: str) -> Union[int, float]:
    try:
        float_value = float(s)
    except ValueError as e:
        raise TypeConversionError(e) from e

    if float_value.is_integer():
        return int(float_value)

    return float_value


def map_icon(s: str) -> Union[str, Path]:
    return s if is_url(s) or is_emoji(s) else Path(s)


def map_image(s: str) -> Union[str, Path]:
    return s if is_url(s) else Path(s)
