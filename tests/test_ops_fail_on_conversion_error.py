import logging

import pytest

from csv2notion.utils_exceptions import NotionError


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_fail_on_conversion_error(tmp_path, db_maker, caplog):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("a,b\na,not_a_number")

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        e = db_maker.from_raising_cli(
            "--token",
            db_maker.token,
            "--fail-on-conversion-error",
            "--custom-types",
            "number",
            str(test_file),
        )

    assert isinstance(e.raised, NotionError)
    assert "Error during conversion" in str(e.raised)
    assert "CSV [2]: could not convert string to float: 'not_a_number'" in caplog.text


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_fail_on_conversion_error_empty(tmp_path, db_maker):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("a,b\na,")

    test_db = db_maker.from_cli(
        "--token",
        db_maker.token,
        "--fail-on-conversion-error",
        "--custom-types",
        "number",
        str(test_file),
    )

    assert test_db.schema_dict["b"]["type"] == "number"

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1

    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"] is None


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_fail_on_conversion_error_ok(tmp_path, db_maker):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("a,b\na,123")

    test_db = db_maker.from_cli(
        "--token",
        db_maker.token,
        "--fail-on-conversion-error",
        "--custom-types",
        "number",
        str(test_file),
    )

    assert test_db.schema_dict["b"]["type"] == "number"

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1

    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"] == 123
