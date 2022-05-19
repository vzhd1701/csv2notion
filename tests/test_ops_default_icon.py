import pytest

from csv2notion.cli import cli
from csv2notion.utils_exceptions import CriticalError


def test_default_icon_file_not_found():
    with pytest.raises(CriticalError) as e:
        cli(
            [
                "--token",
                "fake",
                "--default-icon",
                "fake_icon.jpg",
                "fake",
            ]
        )

    assert "File not found: fake_icon.jpg" in str(e.value)


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_default_icon_file(tmp_path, smallest_gif, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b\na,b\n")

    test_image = tmp_path / "test_image.gif"
    test_image.write_bytes(smallest_gif)

    test_db = db_maker.from_csv_head("a,b")

    cli(
        [
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            "--default-icon",
            str(test_image.resolve()),
            str(test_file),
        ]
    )

    table_header = test_db.header
    table_rows = test_db.rows

    assert table_header == {"a", "b"}
    assert len(table_rows) == 1
    assert getattr(table_rows[0].columns, "a") == "a"
    assert getattr(table_rows[0].columns, "b") == "b"

    assert test_image.name in table_rows[0].icon


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_default_icon_url(tmp_path, db_maker):
    test_icon_url = "https://via.placeholder.com/100"

    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b\na,b\n")

    test_db = db_maker.from_csv_head("a,b")

    cli(
        [
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            "--default-icon",
            test_icon_url,
            str(test_file),
        ]
    )

    table_header = test_db.header
    table_rows = test_db.rows

    assert table_header == {"a", "b"}
    assert len(table_rows) == 1
    assert getattr(table_rows[0].columns, "a") == "a"
    assert getattr(table_rows[0].columns, "b") == "b"

    assert table_rows[0].icon == test_icon_url


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_default_icon_emoji(tmp_path, db_maker):
    test_icon_emoji = "🤔"

    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b\na,b\n")

    test_db = db_maker.from_csv_head("a,b")

    cli(
        [
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            "--default-icon",
            test_icon_emoji,
            str(test_file),
        ]
    )

    table_header = test_db.header
    table_rows = test_db.rows

    assert table_header == {"a", "b"}
    assert len(table_rows) == 1
    assert getattr(table_rows[0].columns, "a") == "a"
    assert getattr(table_rows[0].columns, "b") == "b"

    assert table_rows[0].icon == test_icon_emoji


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_default_icon_column_priority(tmp_path, db_maker):
    test_icon_url_default = "https://via.placeholder.com/100"
    test_icon_url_column = "https://via.placeholder.com/200"

    test_file = tmp_path / "test.csv"
    test_file.write_text(f"a,b,icon url\na1,b1,{test_icon_url_column}\na2,b2,")

    test_db = db_maker.from_csv_head("a,b")

    cli(
        [
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            "--icon-column",
            "icon url",
            "--default-icon",
            test_icon_url_default,
            "--max-threads=1",
            str(test_file),
        ]
    )

    table_header = test_db.header
    table_rows = test_db.rows

    assert table_header == {"a", "b"}
    assert len(table_rows) == 2
    assert getattr(table_rows[0].columns, "a") == "a1"
    assert getattr(table_rows[0].columns, "b") == "b1"
    assert getattr(table_rows[1].columns, "a") == "a2"
    assert getattr(table_rows[1].columns, "b") == "b2"

    assert table_rows[0].icon == test_icon_url_column
    assert table_rows[1].icon == test_icon_url_default


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_default_icon_merge_only(tmp_path, db_maker):
    test_icon_emoji_default = "🤔"

    test_file = tmp_path / "test.csv"
    test_file.write_text(f"a,b\na1,b1\na2,b2")

    test_db = db_maker.from_csv_head("a,b")

    cli(
        [
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            "--default-icon",
            test_icon_emoji_default,
            "--merge",
            "--merge-only-column",
            "a",
            "--max-threads=1",
            str(test_file),
        ]
    )

    table_header = test_db.header
    table_rows = test_db.rows

    assert table_header == {"a", "b"}
    assert len(table_rows) == 2
    assert getattr(table_rows[0].columns, "a") == "a1"
    assert getattr(table_rows[0].columns, "b") == ""
    assert getattr(table_rows[1].columns, "a") == "a2"
    assert getattr(table_rows[1].columns, "b") == ""

    assert table_rows[0].icon == test_icon_emoji_default
    assert table_rows[1].icon == test_icon_emoji_default
