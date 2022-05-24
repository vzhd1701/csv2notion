import logging

import pytest
from notion.user import User

from csv2notion.utils_exceptions import NotionError


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_fail_on_unsettable_columns(tmp_path, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b,c,d,e\na,b,c,d,e")

    e = db_maker.from_raising_cli(
        "--token",
        db_maker.token,
        "--column-types",
        "created_by,last_edited_by,rollup,formula",
        "--fail-on-unsettable-columns",
        str(test_file),
    )

    assert isinstance(e.raised, NotionError)
    assert (
        "Cannot set value to these columns"
        " due to unsupported type: ['b', 'c', 'd', 'e']" in str(e.raised)
    )


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_fail_on_unsettable_columns_ok(tmp_path, caplog, db_maker):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("a,b,c,d,e\na,b,c,d,e")

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        test_db = db_maker.from_cli(
            "--token",
            db_maker.token,
            "--column-types",
            "created_by,last_edited_by,rollup,formula",
            str(test_file),
        )

    assert test_db.schema_dict["b"]["type"] == "created_by"
    assert test_db.schema_dict["c"]["type"] == "last_edited_by"
    assert test_db.schema_dict["d"]["type"] == "rollup"
    assert test_db.schema_dict["e"]["type"] == "formula"

    assert test_db.header == {"a", "b", "c", "d", "e"}
    assert len(test_db.rows) == 1

    assert test_db.rows[0].columns["a"] == "a"
    assert isinstance(test_db.rows[0].columns["b"], User)
    assert isinstance(test_db.rows[0].columns["c"], User)
    assert test_db.rows[0].columns["d"] is None
    assert test_db.rows[0].columns["e"] is None
    assert (
        "Cannot set value to these columns"
        " due to unsupported type: ['b', 'c', 'd', 'e']" in caplog.text
    )
