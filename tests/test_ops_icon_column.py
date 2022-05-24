import logging

import pytest

from csv2notion.cli import cli
from csv2notion.utils_exceptions import NotionError


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_icon_column_missing(tmp_path, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b,c\na,b,c\n")

    test_db = db_maker.from_csv_head("a,b,c")

    with pytest.raises(NotionError) as e:
        cli(
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            "--icon-column",
            "icon file",
            str(test_file),
        )

    assert "Icon column 'icon file' not found in csv file" in str(e.value)


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_icon_column_file_not_found(tmp_path, db_maker, caplog):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b,icon file\na,b,test_image.jpg\n")

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        test_db = db_maker.from_cli(
            "--token",
            db_maker.token,
            "--icon-column",
            "icon file",
            str(test_file),
        )

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1
    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"] == "b"
    assert len(test_db.rows[0].children) == 0
    assert test_db.rows[0].icon is None

    assert "test_image.jpg does not exist" in caplog.text


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_icon_column_file_not_found_fail(tmp_path, db_maker, caplog):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b,icon file\na,b,test_image.jpg\n")

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        e = db_maker.from_raising_cli(
            "--token",
            db_maker.token,
            "--icon-column",
            "icon file",
            "--fail-on-conversion-error",
            str(test_file),
        )

    assert "Error during conversion" in str(e.raised)
    assert "test_image.jpg does not exist" in caplog.text


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_icon_column_empty(tmp_path, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b,icon file\na,b,\n")

    test_db = db_maker.from_csv_head("a,b")

    cli(
        "--token",
        db_maker.token,
        "--url",
        test_db.url,
        "--icon-column",
        "icon file",
        str(test_file),
    )

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1
    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"] == "b"
    assert len(test_db.rows[0].children) == 0
    assert test_db.rows[0].icon is None


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_icon_column_skip_for_new_db(tmp_path, db_maker):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("a,b,icon file\na,b,\n")

    test_db = db_maker.from_cli(
        "--token",
        db_maker.token,
        "--icon-column",
        "icon file",
        str(test_file),
    )

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1
    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"] == "b"
    assert len(test_db.rows[0].children) == 0


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_icon_column_ok(tmp_path, smallest_gif, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b,icon file\na,b,test_image.gif\n")

    test_image = tmp_path / "test_image.gif"
    test_image.write_bytes(smallest_gif)

    test_db = db_maker.from_csv_head("a,b")

    cli(
        "--token",
        db_maker.token,
        "--url",
        test_db.url,
        "--icon-column",
        "icon file",
        str(test_file),
    )

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1
    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"] == "b"
    assert len(test_db.rows[0].children) == 0
    assert test_image.name in test_db.rows[0].icon


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_icon_column_url_ok(tmp_path, db_maker):
    test_icon_url = "https://via.placeholder.com/100"

    test_file = tmp_path / "test.csv"
    test_file.write_text(f"a,b,icon url\na,b,{test_icon_url}\n")

    test_db = db_maker.from_csv_head("a,b")

    cli(
        "--token",
        db_maker.token,
        "--url",
        test_db.url,
        "--icon-column",
        "icon url",
        str(test_file),
    )

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1
    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"] == "b"
    assert len(test_db.rows[0].children) == 0
    assert test_db.rows[0].icon == test_icon_url


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_icon_column_emoji_ok(tmp_path, db_maker):
    test_icon_emoji = "🤔"

    test_file = tmp_path / "test.csv"
    test_file.write_text(f"a,b,icon emoji\na,b,{test_icon_emoji}\n", encoding="utf-8")

    test_db = db_maker.from_csv_head("a,b")

    cli(
        "--token",
        db_maker.token,
        "--url",
        test_db.url,
        "--icon-column",
        "icon emoji",
        str(test_file),
    )

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1
    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"] == "b"
    assert len(test_db.rows[0].children) == 0
    assert test_db.rows[0].icon == test_icon_emoji


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_icon_column_keep_missing(tmp_path, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b\na,b\n")

    test_db = db_maker.from_csv_head("a,b,icon url")

    with pytest.raises(NotionError) as e:
        cli(
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            "--icon-column",
            "icon url",
            "--icon-column-keep",
            str(test_file),
        )

    assert "Icon column 'icon url' not found in csv file" in str(e.value)


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_icon_column_keep_ok(tmp_path, db_maker):
    test_icon_url = "https://via.placeholder.com/100"

    test_file = tmp_path / "test.csv"
    test_file.write_text(f"a,b,icon url\na,b,{test_icon_url}\n")

    test_db = db_maker.from_csv_head("a,b,icon url")

    cli(
        "--token",
        db_maker.token,
        "--url",
        test_db.url,
        "--icon-column",
        "icon url",
        "--icon-column-keep",
        str(test_file),
    )

    assert test_db.header == {"a", "b", "icon url"}
    assert len(test_db.rows) == 1
    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"] == "b"
    assert test_db.rows[0].columns["icon url"] == test_icon_url
    assert len(test_db.rows[0].children) == 0
    assert test_db.rows[0].icon == test_icon_url


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_icon_column_keep_ok_for_new_db(tmp_path, db_maker):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("a,b,icon file\na,b,\n")

    test_db = db_maker.from_cli(
        "--token",
        db_maker.token,
        "--icon-column",
        "icon file",
        "--icon-column-keep",
        str(test_file),
    )

    assert test_db.header == {"a", "b", "icon file"}
    assert len(test_db.rows) == 1
    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"] == "b"
    assert test_db.rows[0].columns["icon file"] == ""
    assert len(test_db.rows[0].children) == 0


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_icon_column_keep_same_property_name(tmp_path, db_maker):
    test_icon_url = "https://via.placeholder.com/100"

    test_file = tmp_path / "test.csv"
    test_file.write_text(f"a,icon\na,{test_icon_url}\n")

    test_db = db_maker.from_csv_head("a,icon")

    cli(
        "--token",
        db_maker.token,
        "--url",
        test_db.url,
        "--icon-column",
        "icon",
        "--icon-column-keep",
        str(test_file),
    )

    assert test_db.header == {"a", "icon"}
    assert len(test_db.rows) == 1
    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["icon"] == test_icon_url
    assert len(test_db.rows[0].children) == 0
    assert test_db.rows[0].icon == test_icon_url
