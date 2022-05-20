import os

import pytest
from notion.utils import slugify

from csv2notion.cli import cli
from csv2notion.utils_exceptions import NotionError


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_fail_on_relation_duplicates(tmp_path, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b\na,b\n")

    test_db = db_maker.from_csv_head("a,b")
    test_db_relation = db_maker.from_csv_head("c,d")

    test_db.set_relation("b", test_db_relation)

    test_db_relation.add_row({"c": "cc"})
    test_db_relation.add_row({"c": "cc"})

    with pytest.raises(NotionError) as e:
        cli(
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            "--fail-on-relation-duplicates",
            str(test_file),
        )

    relation_name = test_db_relation.page.title

    assert (
        f"Collection DB '{relation_name}' used in 'b' relation column has duplicates"
        f" which cannot be unambiguously mapped with CSV data." in str(e.value)
    )


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_fail_on_relation_duplicates_ok(tmp_path, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b\na,b\n")

    test_db = db_maker.from_csv_head("a,b")
    test_db_relation = db_maker.from_csv_head("c,d")

    test_db.set_relation("b", test_db_relation)

    test_db_relation.add_row({"c": "cc"})

    cli(
        "--token",
        db_maker.token,
        "--url",
        test_db.url,
        "--fail-on-relation-duplicates",
        str(test_file),
    )

    test_db.refresh()
    test_db_relation.refresh()

    relation_column = f"Related to {test_db.page.title} (b)"

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1
    assert test_db_relation.header == {"c", "d", relation_column}
    assert len(test_db_relation.rows) == 1

    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"] == []
    assert test_db_relation.rows[0].columns["c"] == "cc"
    assert test_db_relation.rows[0].columns["d"] == ""
    assert test_db_relation.rows[0].columns[slugify(relation_column)] == []
