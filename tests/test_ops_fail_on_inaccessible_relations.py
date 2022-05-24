import logging

import pytest

from csv2notion.cli import cli
from csv2notion.utils_exceptions import NotionError


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
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            "--fail-on-inaccessible-relations",
            str(test_file),
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
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            str(test_file),
        )

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1

    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"] == []
    assert "Columns with inaccessible relations: ['b']" in caplog.text
