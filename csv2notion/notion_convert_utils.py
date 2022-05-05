from datetime import datetime
from pathlib import Path
from typing import List, Union

import dateutil.parser
from emoji import is_emoji

from csv2notion.csv_data import CSVData
from csv2notion.notion_type_guess import is_url
from csv2notion.utils import rand_id_list


class TypeConversionError(Exception):
    pass


def map_checkbox(value: str) -> bool:
    return value == "true"


def map_date(value: str) -> datetime:
    try:
        return dateutil.parser.parse(value)
    except dateutil.parser.ParserError as e:
        raise TypeConversionError(e) from e


def map_number(value: str) -> Union[int, float]:
    try:
        float_value = float(value)
    except ValueError as e:
        raise TypeConversionError(e) from e

    if float_value.is_integer():
        return int(float_value)

    return float_value


def map_icon(s: str) -> Union[str, Path]:
    return s if is_url(s) or is_emoji(s) else Path(s)


def map_image(s: str) -> Union[str, Path]:
    return s if is_url(s) else Path(s)


def schema_from_csv(csv_data: CSVData) -> dict:
    columns = csv_data.keys()

    schema_ids = rand_id_list(len(columns) - 1, 4)

    schema = {"title": {"name": columns[0], "type": "title"}}

    for col_id, col_key in zip(schema_ids, columns[1:]):
        schema[col_id] = {
            "name": col_key,
            "type": csv_data.col_type(col_key),
        }

    return schema
