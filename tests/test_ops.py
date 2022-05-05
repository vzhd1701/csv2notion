import logging
import os
import re
from pathlib import Path

import pytest

from csv2notion.cli import cli, main
from csv2notion.utils import CriticalError, NotionError


def test_no_args():
    with pytest.raises(SystemExit):
        cli([])


def test_help():
    with pytest.raises(SystemExit):
        cli(["--help"])


def test_missing_csv():
    with pytest.raises(CriticalError) as e:
        cli(["--token", "fake", "fake.csv"])

    assert "File fake.csv not found" in str(e.value)


def test_empty_csv(tmp_path):
    test_file = tmp_path / "test.csv"
    test_file.touch()

    with pytest.raises(CriticalError) as e:
        cli(["--token", "fake", str(test_file)])

    assert "CSV file is empty" in str(e.value)


@pytest.mark.vcr()
def test_bad_token(tmp_path):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b,c\n1,2,3\n")

    with pytest.raises(NotionError) as e:
        cli(["--token", "fake", str(test_file)])

    assert "Invalid Notion token" in str(e.value)


@pytest.mark.skipif(not os.environ.get("NOTION_TEST_TOKEN"), reason="No notion token")
@pytest.mark.vcr()
def test_bad_url(tmp_path):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b,c\na,b,c\n")

    with pytest.raises(NotionError) as e:
        cli(
            [
                "--token",
                os.environ.get("NOTION_TEST_TOKEN"),
                "--url",
                "https://notnotion.com/bad_url",
                str(test_file),
            ]
        )

    assert "Invalid URL" in str(e.value)


@pytest.mark.skipif(not os.environ.get("NOTION_TEST_TOKEN"), reason="No notion token")
@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_bad_url_type(tmp_path, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b,c\na,b,c\n")

    test_db = db_maker.from_csv_head("a,b,c")
    test_row = test_db.add_row({})

    with pytest.raises(NotionError) as e:
        cli(
            [
                "--token",
                os.environ.get("NOTION_TEST_TOKEN"),
                "--url",
                test_row.get_browseable_url(),
                str(test_file),
            ]
        )

    assert "Provided URL links does not point to a Notion database" in str(e.value)


@pytest.mark.skipif(not os.environ.get("NOTION_TEST_TOKEN"), reason="No notion token")
@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_new_page(tmp_path, caplog, db_maker):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("a,b,c\na,b,c\n")

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        cli(["--token", os.environ.get("NOTION_TEST_TOKEN"), str(test_file)])

    url = re.search(r"New database URL: (.*)$", caplog.text, re.M)[1]

    test_db = db_maker.from_url(url)

    table_rows = test_db.rows
    table_header = test_db.header

    assert test_db.page.title == db_maker.page_name
    assert test_db.page.type == "collection_view_page"

    assert table_header == {"a", "b", "c"}
    assert len(table_rows) == 1
    assert getattr(table_rows[0], "a") == "a"
    assert getattr(table_rows[0], "b") == "b"
    assert getattr(table_rows[0], "c") == "c"


@pytest.mark.skipif(not os.environ.get("NOTION_TEST_TOKEN"), reason="No notion token")
@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_new_page_column_order(tmp_path, caplog, db_maker):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("c,b,a\nc,b,a\n")

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        cli(["--token", os.environ.get("NOTION_TEST_TOKEN"), str(test_file)])

    url = re.search(r"New database URL: (.*)$", caplog.text, re.M)[1]

    test_db = db_maker.from_url(url)

    table_rows = test_db.rows
    table_view_header = test_db.default_view_header

    assert test_db.page.title == db_maker.page_name
    assert test_db.page.type == "collection_view_page"

    assert table_view_header == ["c", "b", "a"]
    assert len(table_rows) == 1
    assert getattr(table_rows[0], "a") == "a"
    assert getattr(table_rows[0], "b") == "b"
    assert getattr(table_rows[0], "c") == "c"


@pytest.mark.skipif(not os.environ.get("NOTION_TEST_TOKEN"), reason="No notion token")
@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_existing_page(tmp_path, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b,c\naa,bb,cc\n")

    test_db = db_maker.from_csv_head("a,b,c")

    cli(
        [
            "--token",
            os.environ.get("NOTION_TEST_TOKEN"),
            "--url",
            test_db.url,
            str(test_file),
        ]
    )

    table_header = {c["name"] for c in test_db.schema}
    table_rows = test_db.rows

    assert table_header == {"a", "b", "c"}
    assert len(table_rows) == 1
    assert getattr(table_rows[0], "a") == "aa"
    assert getattr(table_rows[0], "b") == "bb"
    assert getattr(table_rows[0], "c") == "cc"


def test_log_file(fs, mocker):
    mocker.patch(
        "sys.argv",
        ["csv2notion", "--token", "fake", "--log", "test_log.txt", "fake_file.csv"],
    )

    with pytest.raises(SystemExit) as e:
        main()

    log_txt = Path("test_log.txt").read_text("utf-8")

    assert e.value.code == 1
    assert "File fake_file.csv not found" in log_txt


def test_keyboard_interrupt(mocker):
    mocker.patch("csv2notion.cli.cli", side_effect=KeyboardInterrupt)

    with pytest.raises(SystemExit) as e:
        main()

    assert e.value.code == 1


def test_main_import():
    from csv2notion import __main__
