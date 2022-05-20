import logging
import re

import pytest

from csv2notion.cli import cli
from csv2notion.utils_exceptions import NotionError


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_merge_key_missing(tmp_path, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b\na,b\n")

    test_db = db_maker.from_csv_head("c,d")

    with pytest.raises(NotionError) as e:
        cli(
            [
                "--token",
                db_maker.token,
                "--url",
                test_db.url,
                "--merge",
                str(test_file),
            ]
        )

    assert f"Key column 'a' does not exist in Notion DB" in str(e.value)


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_merge_key_invalid(tmp_path, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b\na,b\n")

    test_db = db_maker.from_csv_head("c,a")

    with pytest.raises(NotionError) as e:
        cli(
            [
                "--token",
                db_maker.token,
                "--url",
                test_db.url,
                "--merge",
                str(test_file),
            ]
        )

    assert f"Notion DB column 'a' is not a key column" in str(e.value)


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_merge_ok(tmp_path, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b\na,b2\n")

    test_db = db_maker.from_csv_head("a,b,c")

    test_db.add_row({"a": "a", "b": "b1", "c": "c1"})

    cli(
        [
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            "--merge",
            str(test_file),
        ]
    )

    table_rows = test_db.rows
    table_header = test_db.header

    assert table_header == {"a", "b", "c"}
    assert len(table_rows) == 1

    assert getattr(table_rows[0].columns, "a") == "a"
    assert getattr(table_rows[0].columns, "b") == "b2"
    assert getattr(table_rows[0].columns, "c") == "c1"


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_merge_bom_csv_ok(tmp_path, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_bytes("a,b\na,b2\n".encode("utf-8-sig"))

    test_db = db_maker.from_csv_head("a,b,c")

    test_db.add_row({"a": "a", "b": "b1", "c": "c1"})

    cli(
        [
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            "--merge",
            str(test_file),
        ]
    )

    table_rows = test_db.rows
    table_header = test_db.header

    assert table_header == {"a", "b", "c"}
    assert len(table_rows) == 1

    assert getattr(table_rows[0].columns, "a") == "a"
    assert getattr(table_rows[0].columns, "b") == "b2"
    assert getattr(table_rows[0].columns, "c") == "c1"


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_merge_only_column_missing(tmp_path, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b\na,b\n")

    test_db = db_maker.from_csv_head("a,b,c")

    with pytest.raises(NotionError) as e:
        cli(
            [
                "--token",
                db_maker.token,
                "--url",
                test_db.url,
                "--merge",
                "--merge-only-column",
                "c",
                str(test_file),
            ]
        )

    assert "Merge only column(s) {'c'} not found in csv file" in str(e.value)


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_merge_only_column_ok(tmp_path, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b,c\na,b2,c2\n")

    test_db = db_maker.from_csv_head("a,b,c")

    test_db.add_row({"a": "a", "b": "b1", "c": "c1"})

    cli(
        [
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            "--merge",
            "--merge-only-column",
            "c",
            str(test_file),
        ]
    )

    table_rows = test_db.rows
    table_header = test_db.header

    assert table_header == {"a", "b", "c"}
    assert len(table_rows) == 1

    assert getattr(table_rows[0].columns, "a") == "a"
    assert getattr(table_rows[0].columns, "b") == "b1"
    assert getattr(table_rows[0].columns, "c") == "c2"


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_merge_skip_new(tmp_path, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b\na1,b1\n")

    test_db = db_maker.from_cli("--token", db_maker.token, str(test_file))

    test_file.write_text("a,b\na1,b11\na2,b22\n")

    cli(
        [
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            "--merge",
            "--merge-skip-new",
            "--max-threads=1",
            str(test_file),
        ]
    )

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1

    assert getattr(test_db.rows[0].columns, "a") == "a1"
    assert getattr(test_db.rows[0].columns, "b") == "b11"
