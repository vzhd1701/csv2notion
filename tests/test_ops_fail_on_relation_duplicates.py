import os

import pytest

from csv2notion.cli import cli
from csv2notion.notion.utils import slugify
from csv2notion.utils import NotionError


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
            [
                "--token",
                db_maker.token,
                "--url",
                test_db.url,
                "--fail-on-relation-duplicates",
                str(test_file),
            ]
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
        [
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            "--fail-on-relation-duplicates",
            str(test_file),
        ]
    )

    table_main_rows = test_db.rows
    table_main_header = test_db.header

    table_relation_rows = test_db_relation.rows
    table_relation_header = test_db_relation.header

    relation_column = f"Related to {test_db.page.title} (b)"

    assert table_main_header == {"a", "b"}
    assert len(table_main_rows) == 1
    assert table_relation_header == {"c", "d", relation_column}
    assert len(table_relation_rows) == 1

    assert getattr(table_main_rows[0], "a") == "a"
    assert getattr(table_main_rows[0], "b") == []
    assert getattr(table_relation_rows[0], "c") == "cc"
    assert getattr(table_relation_rows[0], "d") == ""
    assert getattr(table_relation_rows[0], slugify(relation_column)) == []
