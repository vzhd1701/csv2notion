import os

import pytest

from csv2notion.cli import cli
from csv2notion.utils_exceptions import CriticalError


def test_fail_on_duplicate_csv_columns(tmp_path):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,a,b\na1,a2,b1")

    with pytest.raises(CriticalError) as e:
        cli(
            "--token",
            "fake",
            "--fail-on-duplicate-csv-columns",
            str(test_file),
        )

    assert "Duplicate columns found in CSV" in str(e.value)


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_fail_on_duplicate_csv_columns_ok(tmp_path, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b\na,b")

    test_db = db_maker.from_csv_head("a,b")

    cli(
        "--token",
        db_maker.token,
        "--url",
        test_db.url,
        "--fail-on-duplicate-csv-columns",
        str(test_file),
    )

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1

    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"] == "b"


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_fail_on_duplicate_csv_columns_ignore(tmp_path, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,a,b\na1,a2,b")

    test_db = db_maker.from_csv_head("a,b")

    cli(
        "--token",
        db_maker.token,
        "--url",
        test_db.url,
        str(test_file),
    )

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1

    assert test_db.rows[0].columns["a"] == "a2"
    assert test_db.rows[0].columns["b"] == "b"
