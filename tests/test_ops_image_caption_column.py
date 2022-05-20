import logging
import re

import pytest

from csv2notion.cli import cli
from csv2notion.utils_exceptions import NotionError


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_image_caption_column_missing(tmp_path, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b,c\na,b,c\n")

    test_db = db_maker.from_csv_head("a,b,c")

    with pytest.raises(NotionError) as e:
        cli(
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            "--image-caption-column",
            "image caption",
            str(test_file),
        )

    assert "Image caption column 'image caption' not found in csv file" in str(e.value)


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_image_caption_column_empty(tmp_path, db_maker):
    test_image_url = "https://via.placeholder.com/100"

    test_file = tmp_path / "test.csv"
    test_file.write_text(f"a,b,image url,image caption\na,b,{test_image_url},\n")

    test_db = db_maker.from_csv_head("a,b")

    cli(
        "--token",
        db_maker.token,
        "--url",
        test_db.url,
        "--image-column",
        "image url",
        "--image-caption-column",
        "image caption",
        str(test_file),
    )

    image = test_db.rows[0].children[0]

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1
    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"] == "b"
    assert len(test_db.rows[0].children) == 1

    assert image.caption == ""


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_image_caption_column_skip_for_new_db(tmp_path, db_maker):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("a,b,image column\na,b,\n")

    test_db = db_maker.from_cli(
        "--token",
        db_maker.token,
        "--image-caption-column",
        "image column",
        str(test_file),
    )

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1
    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"] == "b"
    assert len(test_db.rows[0].children) == 0


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_image_caption_column_ok(tmp_path, db_maker):
    test_image_url = "https://via.placeholder.com/100"

    test_file = tmp_path / "test.csv"
    test_file.write_text(f"a,b,image url,image caption\na,b,{test_image_url},test\n")

    test_db = db_maker.from_csv_head("a,b")

    cli(
        "--token",
        db_maker.token,
        "--url",
        test_db.url,
        "--image-column",
        "image url",
        "--image-caption-column",
        "image caption",
        str(test_file),
    )

    image = test_db.rows[0].children[0]

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1
    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"] == "b"
    assert len(test_db.rows[0].children) == 1

    assert image.caption == "test"


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_image_caption_column_overwrite(tmp_path, db_maker):
    test_image_url = "https://via.placeholder.com/100"

    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text(f"a,image url,image caption\na,{test_image_url},test1\n")

    test_db = db_maker.from_cli(
        "--token",
        db_maker.token,
        "--image-column",
        "image url",
        "--image-caption-column",
        "image caption",
        str(test_file),
    )

    test_file.write_text(f"a,image url,image caption\na,{test_image_url},test2\n")

    cli(
        "--token",
        db_maker.token,
        "--url",
        test_db.url,
        "--image-column",
        "image url",
        "--image-caption-column",
        "image caption",
        "--merge",
        str(test_file),
    )

    image = test_db.rows[0].children[0]

    assert test_db.header == {"a"}
    assert len(test_db.rows) == 1
    assert test_db.rows[0].columns["a"] == "a"
    assert len(test_db.rows[0].children) == 1

    assert image.caption == "test2"


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_image_caption_column_keep(tmp_path, db_maker):
    test_image_url = "https://via.placeholder.com/100"

    test_file = tmp_path / "test.csv"
    test_file.write_text(f"a,b,image url,image caption\na,b,{test_image_url},test\n")

    test_db = db_maker.from_csv_head("a,b,image caption")

    cli(
        "--token",
        db_maker.token,
        "--url",
        test_db.url,
        "--image-column",
        "image url",
        "--image-caption-column",
        "image caption",
        "--image-caption-column-keep",
        str(test_file),
    )

    image = test_db.rows[0].children[0]

    assert test_db.header == {"a", "b", "image caption"}
    assert len(test_db.rows) == 1
    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"] == "b"
    assert test_db.rows[0].columns["image caption"] == "test"
    assert len(test_db.rows[0].children) == 1

    assert image.caption == "test"


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_image_caption_column_keep_for_new_db(tmp_path, db_maker):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("a,b,image file,image caption\na,b,,\n")

    test_db = db_maker.from_cli(
        "--token",
        db_maker.token,
        "--image-column",
        "image file",
        "--image-caption-column",
        "image caption",
        "--image-caption-column-keep",
        str(test_file),
    )

    assert test_db.header == {"a", "b", "image caption"}
    assert len(test_db.rows) == 1
    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"] == "b"
    assert test_db.rows[0].columns["image caption"] == ""
    assert len(test_db.rows[0].children) == 0
