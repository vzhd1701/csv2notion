import hashlib
import logging
import re

import pytest
from notion.block import ImageBlock, TextBlock

from csv2notion.cli import cli


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_merge_image_column_ok(tmp_path, db_maker):
    test_image_url = "https://via.placeholder.com/100"

    test_file = tmp_path / "test.csv"
    test_file.write_text(f"a,image url\na,{test_image_url}\n")

    test_db = db_maker.from_csv_head("a,b")

    test_db.add_row({"a": "a", "b": "b1"})

    cli(
        "--token",
        db_maker.token,
        "--url",
        test_db.url,
        "--merge",
        "--image-column",
        "image url",
        str(test_file),
    )

    image = test_db.rows[0].children[0]

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1

    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"] == "b1"
    assert len(test_db.rows[0].children) == 1
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
        "--token",
        db_maker.token,
        "--url",
        test_db.url,
        "--merge",
        "--image-column",
        "image url",
        str(test_file),
    )

    image = test_db.rows[0].children[0]

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1

    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"] == "b1"
    assert len(test_db.rows[0].children) == 2
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
        "--token",
        db_maker.token,
        "--url",
        test_db.url,
        "--merge",
        "--image-column",
        "image url",
        str(test_file),
    )

    image = test_db.rows[0].children[0]

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1

    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"] == "b1"
    assert len(test_db.rows[0].children) == 2
    assert image.type == "image"
    assert image.display_source == test_image_url


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_merge_image_column_with_image_content_ok(tmp_path, db_maker):
    test_image_url1 = "https://via.placeholder.com/100"
    test_image_url2 = "https://via.placeholder.com/200"

    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text(f"a,b,image url\na,b,{test_image_url1}\n")

    test_db = db_maker.from_cli(
        "--token",
        db_maker.token,
        "--image-column",
        "image url",
        str(test_file),
    )

    test_file.write_text(f"a,b,image url\na,b,{test_image_url2}")

    cli(
        "--token",
        db_maker.token,
        "--url",
        test_db.url,
        "--merge",
        "--image-column",
        "image url",
        str(test_file),
    )

    image = test_db.rows[0].children[0]

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1

    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"] == "b"
    assert len(test_db.rows[0].children) == 1
    assert image.type == "image"
    assert image.display_source == test_image_url2


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_merge_image_column_with_image_content_remove(tmp_path, db_maker):
    test_image_url = "https://via.placeholder.com/100"

    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text(f"a,image url\na,{test_image_url}\n")

    test_db = db_maker.from_cli(
        "--token",
        db_maker.token,
        "--image-column",
        "image url",
        str(test_file),
    )

    test_file.write_text(f"a,image url\na,")

    cli(
        "--token",
        db_maker.token,
        "--url",
        test_db.url,
        "--merge",
        "--image-column",
        "image url",
        str(test_file),
    )

    assert test_db.header == {"a"}
    assert len(test_db.rows) == 1

    assert test_db.rows[0].columns["a"] == "a"
    assert len(test_db.rows[0].children) == 0


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_merge_image_column_with_image_content_file_no_reupload(
    tmp_path, smallest_gif, db_maker
):
    test_image1 = tmp_path / "test_image1.gif"
    test_image1.write_bytes(smallest_gif)

    test_image2 = tmp_path / "test_image2.gif"
    test_image2.write_bytes(smallest_gif)

    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text(f"a,b,image file\na,b,{test_image1.name}")

    test_db = db_maker.from_cli(
        "--token",
        db_maker.token,
        "--image-column",
        "image file",
        str(test_file),
    )

    image_meta_pre = (
        test_db.rows[0].children[0].get("properties.cover_meta", force_refresh=True)
    )

    test_file.write_text(f"a,b,image file\na,b,{test_image2.name}")

    cli(
        "--token",
        db_maker.token,
        "--url",
        test_db.url,
        "--merge",
        "--image-column",
        "image file",
        str(test_file),
    )

    image = test_db.rows[0].children[0]
    image_meta_after = (
        test_db.rows[0].children[0].get("properties.cover_meta", force_refresh=True)
    )

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1

    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"] == "b"
    assert len(test_db.rows[0].children) == 1

    assert image.type == "image"
    assert image_meta_pre == image_meta_after


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_merge_image_column_with_image_content_file_reupload(
    tmp_path, smallest_gif, db_maker
):
    test_image1 = tmp_path / "test_image1.gif"
    test_image1.write_bytes(smallest_gif)

    test_image2_bytes = smallest_gif + b"0"
    test_image2_sha256 = hashlib.sha256(test_image2_bytes).hexdigest()

    test_image2 = tmp_path / "test_image2.gif"
    test_image2.write_bytes(test_image2_bytes)

    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text(f"a,b,image file\na,b,{test_image1.name}")

    test_db = db_maker.from_cli(
        "--token",
        db_maker.token,
        "--image-column",
        "image file",
        str(test_file),
    )

    test_file.write_text(f"a,b,image file\na,b,{test_image2.name}")

    cli(
        "--token",
        db_maker.token,
        "--url",
        test_db.url,
        "--merge",
        "--image-column",
        "image file",
        str(test_file),
    )

    image = test_db.rows[0].children[0]
    image_is_cover_block = (
        test_db.rows[0].children[0].get("properties.is_cover_block", force_refresh=True)
    )

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1

    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"] == "b"
    assert len(test_db.rows[0].children) == 1

    assert image.type == "image"
    assert image_is_cover_block == True
    assert test_db.rows[0].cover_block_meta["sha256"] == test_image2_sha256


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_merge_image_column_cover_changed_content_file_reupload(
    tmp_path, smallest_gif, db_maker
):
    test_image1 = tmp_path / "test_image1.gif"
    test_image1.write_bytes(smallest_gif)

    test_image2_bytes = smallest_gif + b"0"
    test_image2_sha256 = hashlib.sha256(test_image2_bytes).hexdigest()

    test_image2 = tmp_path / "test_image2.gif"
    test_image2.write_bytes(test_image2_bytes)

    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text(f"a,b,image file\na,b,{test_image1.name}")

    test_db = db_maker.from_cli(
        "--token",
        db_maker.token,
        "--image-column",
        "image file",
        "--image-column-mode",
        "cover",
        str(test_file),
    )

    # changed by third party without updating meta
    test_db.rows[0].set("format.page_cover", "https://via.placeholder.com/100")

    test_file.write_text(f"a,b,image file\na,b,{test_image2.name}")

    cli(
        "--token",
        db_maker.token,
        "--url",
        test_db.url,
        "--merge",
        "--image-column",
        "image file",
        "--image-column-mode",
        "cover",
        str(test_file),
    )

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1

    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"] == "b"

    assert test_image2.name in test_db.rows[0].cover
    assert test_db.rows[0].cover_meta["sha256"] == test_image2_sha256


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_merge_image_column_cover_with_content(tmp_path, db_maker):
    test_image_url1 = "https://via.placeholder.com/100"
    test_image_url2 = "https://via.placeholder.com/200"

    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text(f"a,b,image url\na,b,{test_image_url1}\n")

    test_db = db_maker.from_cli(
        "--token",
        db_maker.token,
        "--image-column",
        "image url",
        "--image-column-mode",
        "cover",
        str(test_file),
    )

    test_file.write_text(f"a,b,image url\na,b,{test_image_url2}\n")

    cli(
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
    )

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1

    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"] == "b"
    assert len(test_db.rows[0].children) == 0
    assert test_db.rows[0].cover == test_image_url2


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_merge_image_column_cover_with_content_no_update(tmp_path, db_maker):
    test_image_url = "https://via.placeholder.com/100"

    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text(f"a,b,image url\na,b,{test_image_url}\n")

    test_db = db_maker.from_cli(
        "--token",
        db_maker.token,
        "--image-column",
        "image url",
        "--image-column-mode",
        "cover",
        str(test_file),
    )

    cli(
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
    )

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1

    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"] == "b"
    assert len(test_db.rows[0].children) == 0
    assert test_db.rows[0].cover == test_image_url


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_merge_image_column_cover_with_content_remove(tmp_path, db_maker):
    test_image_url = "https://via.placeholder.com/100"

    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text(f"a,image url\na,{test_image_url}\n")

    test_db = db_maker.from_cli(
        "--token",
        db_maker.token,
        "--image-column",
        "image url",
        "--image-column-mode",
        "cover",
        str(test_file),
    )

    test_file.write_text(f"a,image url\na,\n")

    cli(
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
    )

    assert test_db.header == {"a"}
    assert len(test_db.rows) == 1

    assert test_db.rows[0].columns["a"] == "a"
    assert len(test_db.rows[0].children) == 0
    assert test_db.rows[0].cover is None


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_merge_image_column_cover_empty(tmp_path, db_maker):
    test_image_url = "https://via.placeholder.com/100"

    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text(f"a,b,image url\na,b,{test_image_url}\n")

    test_db = db_maker.from_csv_head("a,b")
    test_db.add_row({"a": "a", "b": "b"})

    cli(
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
    )

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1

    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"] == "b"
    assert len(test_db.rows[0].children) == 0
    assert test_db.rows[0].cover == test_image_url
