import logging

import pytest

from csv2notion.utils_exceptions import NotionError


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_column_types_file_empty(tmp_path, db_maker):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("a,b\na,")

    test_db = db_maker.from_cli(
        "--token",
        db_maker.token,
        "--column-types",
        "file",
        "--max-threads=1",
        str(test_file),
    )

    assert test_db.schema_dict["b"]["type"] == "file"

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1

    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"] == []


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_column_types_file_not_found(tmp_path, db_maker, caplog):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("a,b\na,missing.txt")

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        test_db = db_maker.from_cli(
            "--token",
            db_maker.token,
            "--column-types",
            "file",
            str(test_file),
        )

    assert test_db.schema_dict["b"]["type"] == "file"

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1

    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"] == []

    assert "File missing.txt does not exist" in caplog.text


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_column_types_file_not_found_fail(tmp_path, db_maker, caplog):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("a,b\na,missing.txt")

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        e = db_maker.from_raising_cli(
            "--token",
            db_maker.token,
            "--column-types",
            "file",
            "--fail-on-conversion-error",
            str(test_file),
        )

    assert isinstance(e.raised, NotionError)
    assert "Error during conversion" in str(e.raised)
    assert "File missing.txt does not exist" in caplog.text


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_column_types_file_banned(tmp_path, db_maker, caplog):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("a,b\na,banned.exe")

    banned_file = tmp_path / "banned.exe"
    banned_file.touch()

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        test_db = db_maker.from_cli(
            "--token",
            db_maker.token,
            "--column-types",
            "file",
            str(test_file),
        )

    assert test_db.schema_dict["b"]["type"] == "file"

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1

    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"] == []

    assert "File extension '*.exe' is not allowed to upload on Notion" in caplog.text


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_column_types_file_banned_fail(tmp_path, db_maker, caplog):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("a,b\na,banned.exe")

    banned_file = tmp_path / "banned.exe"
    banned_file.touch()

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        e = db_maker.from_raising_cli(
            "--token",
            db_maker.token,
            "--column-types",
            "file",
            "--fail-on-conversion-error",
            str(test_file),
        )

    assert isinstance(e.raised, NotionError)
    assert "Error during conversion" in str(e.raised)
    assert "File extension '*.exe' is not allowed to upload on Notion" in caplog.text


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_column_types_file_embed(tmp_path, db_maker):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text(
        "a,b\n"
        "a1,https://via.placeholder.com/100\n"
        'a2,"https://via.placeholder.com/100, https://via.placeholder.com/200"'
    )

    test_db = db_maker.from_cli(
        "--token",
        db_maker.token,
        "--column-types",
        "file",
        "--max-threads=1",
        str(test_file),
    )

    assert test_db.schema_dict["b"]["type"] == "file"

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 2

    assert test_db.rows[0].columns["a"] == "a1"
    assert test_db.rows[0].columns["b"] == ["https://via.placeholder.com/100"]
    assert test_db.rows[1].columns["a"] == "a2"
    assert test_db.rows[1].columns["b"] == [
        "https://via.placeholder.com/100",
        "https://via.placeholder.com/200",
    ]


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_column_types_file_duplicate(tmp_path, db_maker):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text(
        'a,b\na,"https://via.placeholder.com/100, https://via.placeholder.com/100"'
    )

    test_db = db_maker.from_cli(
        "--token",
        db_maker.token,
        "--column-types",
        "file",
        "--max-threads=1",
        str(test_file),
    )

    assert test_db.schema_dict["b"]["type"] == "file"

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1

    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"] == ["https://via.placeholder.com/100"]


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_column_types_file_multi_column(tmp_path, db_maker):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text(
        "a,b,c\na,https://via.placeholder.com/100,https://via.placeholder.com/200"
    )

    test_db = db_maker.from_cli(
        "--token",
        db_maker.token,
        "--column-types",
        "file,file",
        "--max-threads=1",
        str(test_file),
    )

    assert test_db.schema_dict["b"]["type"] == "file"
    assert test_db.schema_dict["c"]["type"] == "file"

    assert test_db.header == {"a", "b", "c"}
    assert len(test_db.rows) == 1

    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"] == ["https://via.placeholder.com/100"]
    assert test_db.rows[0].columns["c"] == ["https://via.placeholder.com/200"]


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_column_types_file_upload(tmp_path, db_maker, smallest_gif):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("a,b\na,test_image.gif")

    test_image = tmp_path / "test_image.gif"
    test_image.write_bytes(smallest_gif)

    test_db = db_maker.from_cli(
        "--token",
        db_maker.token,
        "--column-types",
        "file",
        str(test_file),
    )

    assert test_db.schema_dict["b"]["type"] == "file"

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1

    assert test_db.rows[0].columns["a"] == "a"
    assert "test_image.gif" in test_db.rows[0].columns["b"][0]
