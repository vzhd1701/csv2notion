import logging
import os
import re

import pytest

from csv2notion.cli import cli
from csv2notion.utils_exceptions import NotionError


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_fail_on_conversion_error(tmp_path, db_maker):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("a,b\na,not_a_number")

    e = db_maker.from_raising_cli(
        "--token",
        db_maker.token,
        "--fail-on-conversion-error",
        "--custom-types",
        "number",
        str(test_file),
    )

    assert isinstance(e.raised, NotionError)
    assert "CSV [2]: could not convert string to float: 'not_a_number'" in str(e.raised)


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_fail_on_conversion_error_ok(tmp_path, db_maker):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("a,b\na,123")

    test_db = db_maker.from_cli(
        "--token",
        db_maker.token,
        "--fail-on-conversion-error",
        "--custom-types",
        "number",
        str(test_file),
    )

    table_rows = test_db.rows
    table_header = test_db.header

    assert test_db.schema_dict["b"]["type"] == "number"

    assert table_header == {"a", "b"}
    assert len(table_rows) == 1

    assert getattr(table_rows[0].columns, "a") == "a"
    assert getattr(table_rows[0].columns, "b") == 123
