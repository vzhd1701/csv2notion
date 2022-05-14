import logging
import re

import pytest
from notion.user import User

from csv2notion.cli import cli
from csv2notion.utils import NotionError


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_fail_on_unsupported_columns(tmp_path, db_maker, caplog):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b,c,d,e\na,b,c,d,e")

    with pytest.raises(NotionError) as e:
        with caplog.at_level(logging.INFO, logger="csv2notion"):
            cli(
                [
                    "--token",
                    db_maker.token,
                    "--custom-types",
                    "created_by,last_edited_by,rollup,formula",
                    "--fail-on-unsupported-columns",
                    str(test_file),
                ]
            )

    url = re.search(r"New database URL: (.*)$", caplog.text, re.M)[1]

    db_maker.from_url(url)

    assert (
        "Cannot set value to these columns"
        " due to unsupported type: ['b', 'c', 'd', 'e']" in str(e.value)
    )


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_fail_on_unsupported_columns_ok(tmp_path, caplog, db_maker):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("a,b,c,d,e\na,b,c,d,e")

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        cli(
            [
                "--token",
                db_maker.token,
                "--custom-types",
                "created_by,last_edited_by,rollup,formula",
                str(test_file),
            ]
        )

    url = re.search(r"New database URL: (.*)$", caplog.text, re.M)[1]

    test_db = db_maker.from_url(url)

    table_rows = test_db.rows
    table_header = test_db.header

    assert test_db.schema_dict["b"]["type"] == "created_by"
    assert test_db.schema_dict["c"]["type"] == "last_edited_by"
    assert test_db.schema_dict["d"]["type"] == "rollup"
    assert test_db.schema_dict["e"]["type"] == "formula"

    assert table_header == {"a", "b", "c", "d", "e"}
    assert len(table_rows) == 1

    assert getattr(table_rows[0], "a") == "a"
    assert isinstance(getattr(table_rows[0], "b"), User)
    assert isinstance(getattr(table_rows[0], "c"), User)
    assert getattr(table_rows[0], "d") is None
    assert getattr(table_rows[0], "e") is None
