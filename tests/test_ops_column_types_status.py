import logging

import pytest

from csv2notion.cli import cli


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_column_types_status(tmp_path, db_maker):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text(f"a,b\na1,Not started\na2,In progress\na3,Done\na4,")

    test_db = db_maker.from_cli(
        "--token",
        db_maker.token,
        "--column-types",
        "status",
        "--max-threads=1",
        str(test_file),
    )

    assert test_db.schema_dict["b"]["type"] == "status"

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 4

    assert test_db.rows[0].columns["a"] == "a1"
    assert test_db.rows[0].columns["b"] == "Not started"
    assert test_db.rows[1].columns["a"] == "a2"
    assert test_db.rows[1].columns["b"] == "In progress"
    assert test_db.rows[2].columns["a"] == "a3"
    assert test_db.rows[2].columns["b"] == "Done"
    assert test_db.rows[3].columns["a"] == "a4"
    assert test_db.rows[3].columns["b"] == ""


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_column_types_status_add_column(tmp_path, db_maker):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text(f"a,b,c\na1,,In progress")

    test_db = db_maker.from_csv_head("a,b")

    cli(
        "--token",
        db_maker.token,
        "--url",
        test_db.url,
        "--column-types",
        "text,status",
        "--add-missing-columns",
        str(test_file),
    )

    test_db.refresh()

    assert test_db.schema_dict["c"]["type"] == "status"

    assert test_db.header == {"a", "b", "c"}
    assert len(test_db.rows) == 1

    assert test_db.rows[0].columns["a"] == "a1"
    assert test_db.rows[0].columns["b"] == ""
    assert test_db.rows[0].columns["c"] == "In progress"


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_column_types_status_wrong_skip(tmp_path, db_maker, caplog):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text(f"a,b\na1,Bad")

    with caplog.at_level(logging.WARNING, logger="csv2notion"):
        test_db = db_maker.from_cli(
            "--token",
            db_maker.token,
            "--column-types",
            "status",
            "--max-threads=1",
            str(test_file),
        )

    assert test_db.schema_dict["b"]["type"] == "status"

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1

    assert test_db.rows[0].columns["a"] == "a1"
    assert test_db.rows[0].columns["b"] == ""

    assert (
        "Column 'b' has values missing from available status values in DB: {'Bad'}"
        in caplog.text
    )
    assert "These values will be replaced with default status" in caplog.text


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_column_types_status_wrong_fail(tmp_path, db_maker, caplog):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text(f"a,b\na1,Bad")

    with caplog.at_level(logging.WARNING, logger="csv2notion"):
        e = db_maker.from_raising_cli(
            "--token",
            db_maker.token,
            "--column-types",
            "status",
            "--max-threads=1",
            "--fail-on-wrong-status-values",
            str(test_file),
        )

    assert (
        "Column 'b' has values missing from available status values in DB: {'Bad'}"
        in str(e.raised)
    )


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_column_types_status_bad_value_type(tmp_path, db_maker):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text(f"a,b\na1,")

    test_db = db_maker.from_cli(
        "--token",
        db_maker.token,
        "--column-types",
        "status",
        "--max-threads=1",
        str(test_file),
    )

    with pytest.raises(ValueError) as e:
        test_db.rows[0].columns.b = {"very": "wrong"}

    assert "Wrong value type for 'status' type column 'b'" in str(e.value)


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_column_types_status_bad_value_unacceptable(tmp_path, db_maker):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text(f"a,b\na1,")

    test_db = db_maker.from_cli(
        "--token",
        db_maker.token,
        "--column-types",
        "status",
        "--max-threads=1",
        str(test_file),
    )

    with pytest.raises(ValueError) as e:
        test_db.rows[0].columns.b = "Bad"

    assert (
        "Value 'Bad' not acceptable for property 'b'"
        " (valid options: ['not started', 'in progress', 'done'])"
    ) in str(e.value)
