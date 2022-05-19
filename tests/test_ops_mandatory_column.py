import os

import pytest

from csv2notion.cli import cli
from csv2notion.utils_exceptions import NotionError


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_mandatory_column_missing(tmp_path, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b,c\n1,2,3\n")

    test_db = db_maker.from_csv_head("a,b,c")

    with pytest.raises(NotionError) as e:
        cli(
            [
                "--token",
                db_maker.token,
                "--url",
                test_db.url,
                "--mandatory-column",
                "d",
                str(test_file),
            ]
        )

    assert "Mandatory column(s) {'d'} not found in csv file" in str(e.value)


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_mandatory_column_empty(tmp_path, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b,c,d\n1,2,3,\n")

    test_db = db_maker.from_csv_head("a,b,c,d")

    with pytest.raises(NotionError) as e:
        cli(
            [
                "--token",
                db_maker.token,
                "--url",
                test_db.url,
                "--mandatory-column",
                "d",
                str(test_file),
            ]
        )

    assert "CSV [2]: Mandatory column 'd' is empty" in str(e.value)


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_mandatory_column_icon_empty(tmp_path, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b,c,icon url\n1,2,3,\n")

    test_db = db_maker.from_csv_head("a,b,c")

    with pytest.raises(NotionError) as e:
        cli(
            [
                "--token",
                db_maker.token,
                "--url",
                test_db.url,
                "--mandatory-column",
                "icon url",
                "--icon-column",
                "icon url",
                str(test_file),
            ]
        )

    assert "CSV [2]: Mandatory column 'icon url' is empty" in str(e.value)


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_mandatory_column_image_empty(tmp_path, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b,c,image url\n1,2,3,\n")

    test_db = db_maker.from_csv_head("a,b,c")

    with pytest.raises(NotionError) as e:
        cli(
            [
                "--token",
                db_maker.token,
                "--url",
                test_db.url,
                "--mandatory-column",
                "image url",
                "--image-column",
                "image url",
                str(test_file),
            ]
        )

    assert "CSV [2]: Mandatory column 'image url' is empty" in str(e.value)


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_mandatory_column_image_caption_empty(tmp_path, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b,c,image caption\n1,2,3,\n")

    test_db = db_maker.from_csv_head("a,b,c")

    with pytest.raises(NotionError) as e:
        cli(
            [
                "--token",
                db_maker.token,
                "--url",
                test_db.url,
                "--mandatory-column",
                "image caption",
                "--image-caption-column",
                "image caption",
                str(test_file),
            ]
        )

    assert "CSV [2]: Mandatory column 'image caption' is empty" in str(e.value)


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_mandatory_column_ok(tmp_path, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b,c\n1,2,3\n")

    test_db = db_maker.from_csv_head("a,b,c")

    cli(
        [
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            "--mandatory-column",
            "c",
            str(test_file),
        ]
    )

    table_header = {c["name"] for c in test_db.schema}
    table_rows = test_db.rows

    assert table_header == {"a", "b", "c"}
    assert len(table_rows) == 1
    assert getattr(table_rows[0].columns, "a") == "1"
    assert getattr(table_rows[0].columns, "b") == "2"
    assert getattr(table_rows[0].columns, "c") == "3"
