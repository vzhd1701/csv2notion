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
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            "--fail-on-missing-columns",
            str(test_file),
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
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            str(test_file),
        )

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1
    assert test_db.rows[0].columns["a"] == "1"
    assert test_db.rows[0].columns["b"] == "2"
    assert "CSV columns missing from Notion DB: {'c'}" in caplog.text


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_missing_columns_action_add(tmp_path, db_maker, caplog):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b,c\na,b,c\n")

    test_db = db_maker.from_csv_head("a,b")

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        cli(
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            "--add-missing-columns",
            str(test_file),
        )

    test_db.refresh()

    assert test_db.header == {"a", "b", "c"}
    assert len(test_db.rows) == 1
    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"] == "b"
    assert test_db.rows[0].columns["c"] == "c"
    assert "Adding missing columns to the DB: {'c'}" in caplog.text
