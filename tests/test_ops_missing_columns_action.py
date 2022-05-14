import logging

import pytest

from csv2notion.cli import cli
from csv2notion.utils_exceptions import NotionError


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_missing_columns_action_fail(tmp_path, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b,c\n1,2,3\n")

    test_db = db_maker.from_csv_head("a,b")

    with pytest.raises(NotionError) as e:
        cli(
            [
                "--token",
                db_maker.token,
                "--url",
                test_db.url,
                "--missing-columns-action",
                "fail",
                str(test_file),
            ]
        )

    assert "CSV columns missing from Notion DB: {'c'}" in str(e.value)


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_missing_columns_action_ignore(tmp_path, db_maker, caplog):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b,c\n1,2,3\n")

    test_db = db_maker.from_csv_head("a,b")

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        cli(
            [
                "--token",
                db_maker.token,
                "--url",
                test_db.url,
                "--missing-columns-action",
                "ignore",
                str(test_file),
            ]
        )

    table_header = {c["name"] for c in test_db.schema}
    table_rows = test_db.rows

    assert table_header == {"a", "b"}
    assert len(table_rows) == 1
    assert getattr(table_rows[0], "a") == "1"
    assert getattr(table_rows[0], "b") == "2"
    assert "CSV columns missing from Notion DB: {'c'}" in caplog.text


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_missing_columns_action_add(tmp_path, db_maker, caplog):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b,c\na,b,c\n")

    test_db = db_maker.from_csv_head("a,b")

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        cli(
            [
                "--token",
                db_maker.token,
                "--url",
                test_db.url,
                "--missing-columns-action",
                "add",
                str(test_file),
            ]
        )

    test_db.refresh()

    table_header = {c["name"] for c in test_db.schema}
    table_rows = test_db.rows

    assert table_header == {"a", "b", "c"}
    assert len(table_rows) == 1
    assert getattr(table_rows[0], "a") == "a"
    assert getattr(table_rows[0], "b") == "b"
    assert getattr(table_rows[0], "c") == "c"
    assert "Adding missing columns to the DB: {'c'}" in caplog.text
