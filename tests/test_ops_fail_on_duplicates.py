import os

import pytest

from csv2notion.cli import cli
from csv2notion.utils import NotionError


@pytest.mark.skipif(not os.environ.get("NOTION_TEST_TOKEN"), reason="No notion token")
@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_fail_on_duplicates_csv(tmp_path, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b\na,b1\na,b2")

    test_db = db_maker.from_csv_head("a,b")

    with pytest.raises(NotionError) as e:
        cli(
            [
                "--token",
                os.environ.get("NOTION_TEST_TOKEN"),
                "--url",
                test_db.url,
                "--fail-on-duplicates",
                str(test_file),
            ]
        )

    assert "Duplicate values found in first column in CSV" in str(e.value)


@pytest.mark.skipif(not os.environ.get("NOTION_TEST_TOKEN"), reason="No notion token")
@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_fail_on_duplicates_csv_ok(tmp_path, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b\na1,b1\na2,b2")

    test_db = db_maker.from_csv_head("a,b")

    cli(
        [
            "--token",
            os.environ.get("NOTION_TEST_TOKEN"),
            "--url",
            test_db.url,
            "--fail-on-duplicates",
            "--max-threads=1",
            str(test_file),
        ]
    )

    table_rows = test_db.rows
    table_header = test_db.header

    assert table_header == {"a", "b"}
    assert len(table_rows) == 2

    assert getattr(table_rows[0], "a") == "a1"
    assert getattr(table_rows[0], "b") == "b1"
    assert getattr(table_rows[1], "a") == "a2"
    assert getattr(table_rows[1], "b") == "b2"


@pytest.mark.skipif(not os.environ.get("NOTION_TEST_TOKEN"), reason="No notion token")
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
            [
                "--token",
                os.environ.get("NOTION_TEST_TOKEN"),
                "--url",
                test_db.url,
                "--fail-on-duplicates",
                str(test_file),
            ]
        )

    assert "Duplicate values found in DB key column" in str(e.value)


@pytest.mark.skipif(not os.environ.get("NOTION_TEST_TOKEN"), reason="No notion token")
@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_fail_on_duplicates_db_ok(tmp_path, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b\na3,b3")

    test_db = db_maker.from_csv_head("a,b")

    test_db.add_row({"a": "a1", "b": "b1"})
    test_db.add_row({"a": "a2", "b": "b2"})

    cli(
        [
            "--token",
            os.environ.get("NOTION_TEST_TOKEN"),
            "--url",
            test_db.url,
            "--fail-on-duplicates",
            "--max-threads=1",
            str(test_file),
        ]
    )

    table_rows = test_db.rows
    table_header = test_db.header

    assert table_header == {"a", "b"}
    assert len(table_rows) == 3

    assert getattr(table_rows[0], "a") == "a1"
    assert getattr(table_rows[0], "b") == "b1"
    assert getattr(table_rows[1], "a") == "a2"
    assert getattr(table_rows[1], "b") == "b2"
    assert getattr(table_rows[2], "a") == "a3"
    assert getattr(table_rows[2], "b") == "b3"
