import hashlib
import logging
import os
import re

import pytest
from notion.block import ImageBlock, TextBlock

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

    assert getattr(table_rows[0], "a") == "a"
    assert getattr(table_rows[0], "b") == "b2"
    assert getattr(table_rows[0], "c") == "c1"


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
    assert image.display_source == test_image_url


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_merge_image_column_with_content_other_image(tmp_path, db_maker):
    test_image_url = "https://via.placeholder.com/100"

    test_file = tmp_path / "test.csv"
    test_file.write_text(f"a,image url\na,{test_image_url}\n")

    test_db = db_maker.from_csv_head("a,b")

    test_row = test_db.add_row({"a": "a", "b": "b1"})
    test_row.children.add_new(ImageBlock, source="https://via.placeholder.com/200")

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
    assert image.display_source == test_image_url


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_merge_image_column_with_image_content_ok(tmp_path, db_maker, caplog):
    test_image_url1 = "https://via.placeholder.com/100"
    test_image_url2 = "https://via.placeholder.com/200"

    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text(f"a,b,image url\na,b,{test_image_url1}\n")

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        cli(
            [
                "--token",
                db_maker.token,
                "--image-column",
                "image url",
                str(test_file),
            ]
        )

    url = re.search(r"New database URL: (.*)$", caplog.text, re.M)[1]

    test_db = db_maker.from_url(url)

    test_file.write_text(f"a,b,image url\na,b,{test_image_url2}")

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
    assert getattr(table_rows[0], "b") == "b"
    assert len(table_rows[0].children) == 1
    assert image.type == "image"
    assert image.display_source == test_image_url2


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_merge_image_column_with_image_content_file_no_reupload(
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
    image_meta_pre = (
        test_db.rows[0].children[0].get("properties.cover_meta", force_refresh=True)
    )

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

    image = test_db.rows[0].children[0]
    image_meta_after = (
        test_db.rows[0].children[0].get("properties.cover_meta", force_refresh=True)
    )

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1

    assert getattr(test_db.rows[0], "a") == "a"
    assert getattr(test_db.rows[0], "b") == "b"
    assert len(test_db.rows[0].children) == 1

    assert image.type == "image"
    assert image_meta_pre == image_meta_after


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_merge_image_column_with_image_content_file_reupload(
    tmp_path, smallest_gif, db_maker, caplog
):
    test_image1 = tmp_path / "test_image1.gif"
    test_image1.write_bytes(smallest_gif)

    test_image2_bytes = smallest_gif + b"0"
    test_image2_sha256 = hashlib.sha256(test_image2_bytes).hexdigest()

    test_image2 = tmp_path / "test_image2.gif"
    test_image2.write_bytes(test_image2_bytes)

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

    image = test_db.rows[0].children[0]
    image_meta = (
        test_db.rows[0].children[0].get("properties.cover_meta", force_refresh=True)
    )

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1

    assert getattr(test_db.rows[0], "a") == "a"
    assert getattr(test_db.rows[0], "b") == "b"
    assert len(test_db.rows[0].children) == 1

    assert image.type == "image"
    assert image_meta["sha256"] == test_image2_sha256


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_merge_image_column_cover_with_content(tmp_path, db_maker, caplog):
    test_image_url1 = "https://via.placeholder.com/100"
    test_image_url2 = "https://via.placeholder.com/200"

    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text(f"a,b,image url\na,b,{test_image_url1}\n")

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        cli(
            [
                "--token",
                db_maker.token,
                "--image-column",
                "image url",
                "--image-column-mode",
                "cover",
                str(test_file),
            ]
        )

    url = re.search(r"New database URL: (.*)$", caplog.text, re.M)[1]

    test_db = db_maker.from_url(url)

    test_file.write_text(f"a,b,image url\na,b,{test_image_url2}\n")

    cli(
        [
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            "--merge",
            "--image-column",
            "image url",
            "--image-column-mode",
            "cover",
            str(test_file),
        ]
    )

    table_rows = test_db.rows
    table_header = test_db.header

    assert table_header == {"a", "b"}
    assert len(table_rows) == 1

    assert getattr(table_rows[0], "a") == "a"
    assert getattr(table_rows[0], "b") == "b"
    assert len(table_rows[0].children) == 0
    assert table_rows[0].cover == test_image_url2


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_merge_image_column_cover_empty(tmp_path, db_maker):
    test_image_url = "https://via.placeholder.com/100"

    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text(f"a,b,image url\na,b,{test_image_url}\n")

    test_db = db_maker.from_csv_head("a,b")
    test_db.add_row({"a": "a", "b": "b"})

    cli(
        [
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            "--merge",
            "--image-column",
            "image url",
            "--image-column-mode",
            "cover",
            str(test_file),
        ]
    )

    table_rows = test_db.rows
    table_header = test_db.header

    assert table_header == {"a", "b"}
    assert len(table_rows) == 1

    assert getattr(table_rows[0], "a") == "a"
    assert getattr(table_rows[0], "b") == "b"
    assert len(table_rows[0].children) == 0
    assert table_rows[0].cover == test_image_url


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_merge_icon_column_with_content(tmp_path, db_maker, caplog):
    test_icon_url1 = "https://via.placeholder.com/100"
    test_icon_url2 = "https://via.placeholder.com/200"

    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text(f"a,b,icon url\na,b,{test_icon_url1}\n")

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        cli(
            [
                "--token",
                db_maker.token,
                "--icon-column",
                "icon url",
                str(test_file),
            ]
        )

    url = re.search(r"New database URL: (.*)$", caplog.text, re.M)[1]

    test_db = db_maker.from_url(url)

    test_file.write_text(f"a,b,icon url\na,b,{test_icon_url2}\n")

    cli(
        [
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            "--merge",
            "--icon-column",
            "icon url",
            str(test_file),
        ]
    )

    table_rows = test_db.rows
    table_header = test_db.header

    assert table_header == {"a", "b"}
    assert len(table_rows) == 1

    assert getattr(table_rows[0], "a") == "a"
    assert getattr(table_rows[0], "b") == "b"
    assert len(table_rows[0].children) == 0
    assert table_rows[0].icon == test_icon_url2


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_merge_icon_column_with_content_no_reupload(
    tmp_path, db_maker, smallest_gif, caplog
):
    test_icon1 = tmp_path / "test_icon1.gif"
    test_icon1.write_bytes(smallest_gif)

    test_icon2 = tmp_path / "test_icon2.gif"
    test_icon2.write_bytes(smallest_gif)

    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text(f"a,b,icon file\na,b,{test_icon1.name}")

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        cli(
            [
                "--token",
                db_maker.token,
                "--icon-column",
                "icon file",
                str(test_file),
            ]
        )

    url = re.search(r"New database URL: (.*)$", caplog.text, re.M)[1]

    test_db = db_maker.from_url(url)
    icon_meta_pre = test_db.rows[0].get("properties.icon_meta", force_refresh=True)

    test_file.write_text(f"a,b,icon file\na,b,{test_icon2}\n")

    cli(
        [
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            "--merge",
            "--icon-column",
            "icon file",
            str(test_file),
        ]
    )

    table_rows = test_db.rows
    table_header = test_db.header

    icon_meta_after = test_db.rows[0].get("properties.icon_meta", force_refresh=True)

    assert table_header == {"a", "b"}
    assert len(table_rows) == 1

    assert getattr(table_rows[0], "a") == "a"
    assert getattr(table_rows[0], "b") == "b"
    assert len(table_rows[0].children) == 0
    assert icon_meta_pre == icon_meta_after


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_merge_icon_column_url_to_file(tmp_path, db_maker, smallest_gif, caplog):
    test_icon_url = "https://via.placeholder.com/100"

    test_icon_file = tmp_path / "test_icon_file.gif"
    test_icon_file.write_bytes(smallest_gif)

    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text(f"a,b,icon url\na,b,{test_icon_url}")

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        cli(
            [
                "--token",
                db_maker.token,
                "--icon-column",
                "icon url",
                str(test_file),
            ]
        )

    url = re.search(r"New database URL: (.*)$", caplog.text, re.M)[1]

    test_db = db_maker.from_url(url)

    test_file.write_text(f"a,b,icon file\na,b,{test_icon_file}\n")

    cli(
        [
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            "--merge",
            "--icon-column",
            "icon file",
            str(test_file),
        ]
    )

    table_rows = test_db.rows
    table_header = test_db.header

    assert table_header == {"a", "b"}
    assert len(table_rows) == 1

    assert getattr(table_rows[0], "a") == "a"
    assert getattr(table_rows[0], "b") == "b"
    assert len(table_rows[0].children) == 0
    assert test_icon_file.name in table_rows[0].icon


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_merge_icon_column_with_content_reupload_manually_replaced(
    tmp_path, db_maker, smallest_gif, caplog
):
    test_icon1 = tmp_path / "test_icon1.gif"
    test_icon1.write_bytes(smallest_gif)

    test_icon2 = tmp_path / "test_icon2.gif"
    test_icon2.write_bytes(smallest_gif)

    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text(f"a,b,icon file\na,b,{test_icon1.name}")

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        cli(
            [
                "--token",
                db_maker.token,
                "--icon-column",
                "icon file",
                str(test_file),
            ]
        )

    url = re.search(r"New database URL: (.*)$", caplog.text, re.M)[1]

    test_db = db_maker.from_url(url)

    test_db.rows[0].icon = "https://via.placeholder.com/100"

    test_file.write_text(f"a,b,icon file\na,b,{test_icon2}\n")

    cli(
        [
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            "--merge",
            "--icon-column",
            "icon file",
            str(test_file),
        ]
    )

    table_rows = test_db.rows
    table_header = test_db.header

    assert table_header == {"a", "b"}
    assert len(table_rows) == 1

    assert getattr(table_rows[0], "a") == "a"
    assert getattr(table_rows[0], "b") == "b"
    assert len(table_rows[0].children) == 0
    assert test_icon2.name in table_rows[0].icon
