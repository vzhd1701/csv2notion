import logging
import os

import pytest

from csv2notion.cli import cli
from csv2notion.utils import NotionError


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_fail_on_inaccessible_relations(tmp_path, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b\na,b\n")

    test_db = db_maker.from_csv_head("a,b")
    test_db_relation = db_maker.from_csv_head("c,d")

    test_db.set_relation("b", test_db_relation)

    # delete relation page to make it inaccessible
    test_db_relation.remove()

    with pytest.raises(NotionError) as e:
        cli(
            [
                "--token",
                db_maker.token,
                "--url",
                test_db.url,
                "--fail-on-inaccessible-relations",
                str(test_file),
            ]
        )

    assert "Columns with inaccessible relations: ['b']" in str(e.value)


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_fail_on_inaccessible_relations_ignore(tmp_path, db_maker, caplog):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b\na,b\n")

    test_db = db_maker.from_csv_head("a,b")
    test_db_relation = db_maker.from_csv_head("c,d")

    test_db.set_relation("b", test_db_relation)

    # delete relation page to make it inaccessible
    test_db_relation.remove()

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        cli(
            [
                "--token",
                db_maker.token,
                "--url",
                test_db.url,
                str(test_file),
            ]
        )

    table_main_rows = test_db.rows
    table_main_header = test_db.header

    assert table_main_header == {"a", "b"}
    assert len(table_main_rows) == 1

    assert getattr(table_main_rows[0], "a") == "a"
    assert getattr(table_main_rows[0], "b") == []
    assert "Columns with inaccessible relations: ['b']" in caplog.text
