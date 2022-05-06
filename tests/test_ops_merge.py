import logging
import os
import re

import pytest

from csv2notion.cli import cli
from csv2notion.notion.block import ImageBlock, TextBlock
from csv2notion.utils import NotionError


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

    assert getattr(table_rows[0], "a") == "a"
    assert getattr(table_rows[0], "b") == "b2"
    assert getattr(table_rows[0], "c") == "c1"


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

    assert getattr(table_rows[0], "a") == "a"
    assert getattr(table_rows[0], "b") == "b1"
    assert getattr(table_rows[0], "c") == "c2"


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_merge_image_column_ok(tmp_path, db_maker):
    test_image_url = "https://via.placeholder.com/100"

    test_file = tmp_path / "test.csv"
    test_file.write_text(f"a,image url\na,{test_image_url}\n")

    test_db = db_maker.from_csv_head("a,b")

    test_db.add_row({"a": "a", "b": "b1"})

    cli(
        [
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            "--merge",
            "--image-column",
            "image url",
            str(test_file),
        ]
    )

    table_rows = test_db.rows
    table_header = test_db.header
    image = table_rows[0].children[0]

    assert table_header == {"a", "b"}
    assert len(table_rows) == 1

    assert getattr(table_rows[0], "a") == "a"
    assert getattr(table_rows[0], "b") == "b1"
    assert len(table_rows[0].children) == 1
    assert image.type == "image"
    assert image.caption == "cover"
    assert image.display_source == test_image_url


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_merge_image_column_with_content_ok(tmp_path, db_maker):
    test_image_url = "https://via.placeholder.com/100"

    test_file = tmp_path / "test.csv"
    test_file.write_text(f"a,image url\na,{test_image_url}\n")

    test_db = db_maker.from_csv_head("a,b")

    test_row = test_db.add_row({"a": "a", "b": "b1"})
    test_row.children.add_new(TextBlock, title="test")

    cli(
        [
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            "--merge",
            "--image-column",
            "image url",
            str(test_file),
        ]
    )

    table_rows = test_db.rows
    table_header = test_db.header
    image = table_rows[0].children[0]

    assert table_header == {"a", "b"}
    assert len(table_rows) == 1

    assert getattr(table_rows[0], "a") == "a"
    assert getattr(table_rows[0], "b") == "b1"
    assert len(table_rows[0].children) == 2
    assert image.type == "image"
    assert image.caption == "cover"
    assert image.display_source == test_image_url


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_merge_image_column_with_image_content_ok(tmp_path, db_maker):
    test_image_url = "https://via.placeholder.com/100"

    test_file = tmp_path / "test.csv"
    test_file.write_text(f"a,image url\na,{test_image_url}\n")

    test_db = db_maker.from_csv_head("a,b")

    test_row = test_db.add_row({"a": "a", "b": "b1"})
    test_row.children.add_new(
        ImageBlock, caption="cover", display_source="https://via.placeholder.com/200"
    )

    cli(
        [
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            "--merge",
            "--image-column",
            "image url",
            str(test_file),
        ]
    )

    table_rows = test_db.rows
    table_header = test_db.header
    image = table_rows[0].children[0]

    assert table_header == {"a", "b"}
    assert len(table_rows) == 1

    assert getattr(table_rows[0], "a") == "a"
    assert getattr(table_rows[0], "b") == "b1"
    assert len(table_rows[0].children) == 1
    assert image.type == "image"
    assert image.caption == "cover"
    assert image.display_source == test_image_url


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_merge_image_column_with_image_content_file_ok(
    tmp_path, smallest_gif, db_maker, caplog
):
    test_image1 = tmp_path / "test_image1.gif"
    test_image1.write_bytes(smallest_gif)

    test_image2 = tmp_path / "test_image2.gif"
    test_image2.write_bytes(smallest_gif)

    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text(f"a,b,image file\na,b,{test_image1.name}")

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        cli(
            [
                "--token",
                db_maker.token,
                "--image-column",
                "image file",
                str(test_file),
            ]
        )

    url = re.search(r"New database URL: (.*)$", caplog.text, re.M)[1]

    test_db = db_maker.from_url(url)

    test_file.write_text(f"a,b,image file\na,b,{test_image2.name}")

    cli(
        [
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            "--merge",
            "--image-column",
            "image file",
            str(test_file),
        ]
    )

    table_rows = test_db.rows
    table_header = test_db.header
    image = table_rows[0].children[0]

    assert table_header == {"a", "b"}
    assert len(table_rows) == 1

    assert getattr(table_rows[0], "a") == "a"
    assert getattr(table_rows[0], "b") == "b"
    assert len(table_rows[0].children) == 1
    assert image.type == "image"
    assert image.caption == "cover"
    assert test_image2.name in image.display_source
