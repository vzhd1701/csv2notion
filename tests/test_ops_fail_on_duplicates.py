import os

import pytest

from csv2notion.cli import cli
from csv2notion.utils_exceptions import NotionError


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_fail_on_duplicates_csv(tmp_path, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b\na,b1\na,b2")

    test_db = db_maker.from_csv_head("a,b")

    with pytest.raises(NotionError) as e:
        cli(
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            "--fail-on-duplicates",
            str(test_file),
        )

    assert "Duplicate values found in first column in CSV" in str(e.value)


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_fail_on_duplicates_csv_ok(tmp_path, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b\na1,b1\na2,b2")

    test_db = db_maker.from_csv_head("a,b")

    cli(
        "--token",
        db_maker.token,
        "--url",
        test_db.url,
        "--fail-on-duplicates",
        "--max-threads=1",
        str(test_file),
    )

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 2

    assert test_db.rows[0].columns["a"] == "a1"
    assert test_db.rows[0].columns["b"] == "b1"
    assert test_db.rows[1].columns["a"] == "a2"
    assert test_db.rows[1].columns["b"] == "b2"


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_fail_on_duplicates_db(tmp_path, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b\na,b")

    test_db = db_maker.from_csv_head("a,b")

    test_db.add_row({"a": "a1", "b": "b1"})
    test_db.add_row({"a": "a1", "b": "b1"})

    with pytest.raises(NotionError) as e:
        cli(
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            "--fail-on-duplicates",
            str(test_file),
        )

    assert "Duplicate values found in DB key column" in str(e.value)


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_fail_on_duplicates_db_ok(tmp_path, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b\na3,b3")

    test_db = db_maker.from_csv_head("a,b")

    test_db.add_row({"a": "a1", "b": "b1"})
    test_db.add_row({"a": "a2", "b": "b2"})

    cli(
        "--token",
        db_maker.token,
        "--url",
        test_db.url,
        "--fail-on-duplicates",
        "--max-threads=1",
        str(test_file),
    )

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 3

    assert test_db.rows[0].columns["a"] == "a1"
    assert test_db.rows[0].columns["b"] == "b1"
    assert test_db.rows[1].columns["a"] == "a2"
    assert test_db.rows[1].columns["b"] == "b2"
    assert test_db.rows[2].columns["a"] == "a3"
    assert test_db.rows[2].columns["b"] == "b3"
