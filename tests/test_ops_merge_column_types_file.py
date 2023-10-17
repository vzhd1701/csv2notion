import re

import pytest

from csv2notion.cli import cli
from csv2notion.notion_row_upload_file import get_file_id


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_merge_column_types_file_with_content_no_reupload(
    tmp_path, db_maker, smallest_gif
):
    test_icon = tmp_path / "test_icon1.gif"
    test_icon.write_bytes(smallest_gif)

    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text(f"a,b\na,{test_icon.name}")

    test_db = db_maker.from_cli(
        "--token",
        db_maker.token,
        "--column-types",
        "file",
        str(test_file),
    )

    pre_file_url = test_db.rows[0].columns["b"][0]
    pre_file_id = get_file_id(pre_file_url)

    cli(
        "--token",
        db_maker.token,
        "--url",
        test_db.url,
        "--merge",
        "--column-types",
        "file",
        str(test_file),
    )

    post_file_url = test_db.rows[0].columns["b"][0]
    post_file_id = get_file_id(post_file_url)

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1

    assert test_db.rows[0].columns["a"] == "a"
    assert pre_file_id == post_file_id


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_merge_column_types_file_with_content_reupload(
    tmp_path, smallest_gif, db_maker
):
    test_image1 = tmp_path / "test_image1.gif"
    test_image1.write_bytes(smallest_gif)

    test_image2_bytes = smallest_gif + b"0"
    test_image2 = tmp_path / "test_image2.gif"
    test_image2.write_bytes(test_image2_bytes)

    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text(f"a,b\na,{test_image1.name}")

    test_db = db_maker.from_cli(
        "--token",
        db_maker.token,
        "--column-types",
        "file",
        str(test_file),
    )

    pre_file_url = test_db.rows[0].columns["b"][0]
    pre_file_id = get_file_id(pre_file_url)

    test_file.write_text(f"a,b\na,{test_image2.name}")

    cli(
        "--token",
        db_maker.token,
        "--url",
        test_db.url,
        "--merge",
        "--column-types",
        "file",
        str(test_file),
    )

    post_file_url = test_db.rows[0].columns["b"][0]
    post_file_id = get_file_id(post_file_url)

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1

    assert test_db.rows[0].columns["a"] == "a"
    assert pre_file_id != post_file_id


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_merge_column_types_file_with_content_upload_on_empty(
    tmp_path, smallest_gif, db_maker
):
    test_image = tmp_path / "test_image.gif"
    test_image.write_bytes(smallest_gif)

    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("a,b\na,")

    test_db = db_maker.from_cli(
        "--token",
        db_maker.token,
        "--column-types",
        "file",
        str(test_file),
    )

    test_file.write_text(f"a,b\na,{test_image.name}")

    cli(
        "--token",
        db_maker.token,
        "--url",
        test_db.url,
        "--merge",
        "--column-types",
        "file",
        str(test_file),
    )

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1

    assert test_db.rows[0].columns["a"] == "a"
    assert test_image.name in test_db.rows[0].columns["b"][0]


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_merge_column_types_file_with_content_number_change(tmp_path, db_maker):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("a,b\na,https://via.placeholder.com/100")

    test_db = db_maker.from_cli(
        "--token",
        db_maker.token,
        "--column-types",
        "file",
        str(test_file),
    )

    test_file.write_text(
        'a,b\na,"https://via.placeholder.com/100, https://via.placeholder.com/200"'
    )

    cli(
        "--token",
        db_maker.token,
        "--url",
        test_db.url,
        "--merge",
        "--column-types",
        "file",
        str(test_file),
    )

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1

    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"] == [
        "https://via.placeholder.com/100",
        "https://via.placeholder.com/200",
    ]


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_merge_column_types_file_with_content_order_change(tmp_path, db_maker):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text(
        'a,b\na,"https://via.placeholder.com/200, https://via.placeholder.com/100"'
    )

    test_db = db_maker.from_cli(
        "--token",
        db_maker.token,
        "--column-types",
        "file",
        str(test_file),
    )

    test_file.write_text(
        'a,b\na,"https://via.placeholder.com/100, https://via.placeholder.com/200"'
    )

    cli(
        "--token",
        db_maker.token,
        "--url",
        test_db.url,
        "--merge",
        "--column-types",
        "file",
        str(test_file),
    )

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1

    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"] == [
        "https://via.placeholder.com/100",
        "https://via.placeholder.com/200",
    ]
