import os

import pytest

from csv2notion.cli import cli
from csv2notion.notion.utils import slugify
from csv2notion.utils import NotionError


@pytest.mark.skipif(not os.environ.get("NOTION_TEST_TOKEN"), reason="No notion token")
@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_missing_relations_action_fail(tmp_path, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b\naa,bb\n")

    test_db = db_maker.from_csv_head("a,b")
    test_db_relation = db_maker.from_csv_head("c,d")

    test_db.set_relation("b", test_db_relation)

    with pytest.raises(NotionError) as e:
        cli(
            [
                "--token",
                os.environ.get("NOTION_TEST_TOKEN"),
                "--url",
                test_db.url,
                "--missing-relations-action",
                "fail",
                str(test_file),
            ]
        )

    relation_name = test_db_relation.page.title

    assert (
        f"CSV [2]: Value 'bb' for relation 'b [column] -> {relation_name} [DB]'"
        " is not a valid value" in str(e.value)
    )


@pytest.mark.skipif(not os.environ.get("NOTION_TEST_TOKEN"), reason="No notion token")
@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_missing_relations_action_add(tmp_path, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b\naa,bb\n")

    test_db = db_maker.from_csv_head("a,b")
    test_db_relation = db_maker.from_csv_head("c,d")

    test_db.set_relation("b", test_db_relation)

    cli(
        [
            "--token",
            os.environ.get("NOTION_TEST_TOKEN"),
            "--url",
            test_db.url,
            "--missing-relations-action",
            "add",
            str(test_file),
        ]
    )

    table_main_rows = test_db.rows
    table_main_header = {c["name"] for c in test_db.schema}

    table_relation_rows = test_db_relation.rows
    table_relation_header = {c["name"] for c in test_db_relation.schema}

    relation_column = f"Related to {test_db.page.title} (b)"

    assert table_main_header == {"a", "b"}
    assert len(table_main_rows) == 1
    assert table_relation_header == {"c", "d", relation_column}
    assert len(table_relation_rows) == 1

    assert getattr(table_main_rows[0], "a") == "aa"
    assert getattr(table_main_rows[0], "b") == [table_relation_rows[0]]
    assert getattr(table_relation_rows[0], "c") == "bb"
    assert getattr(table_relation_rows[0], "d") == ""
    assert getattr(table_relation_rows[0], slugify(relation_column)) == [
        table_main_rows[0]
    ]


@pytest.mark.skipif(not os.environ.get("NOTION_TEST_TOKEN"), reason="No notion token")
@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_missing_relations_action_ignore(tmp_path, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b\naa,bb\n")

    test_db = db_maker.from_csv_head("a,b")
    test_db_relation = db_maker.from_csv_head("c,d")

    test_db.set_relation("b", test_db_relation)

    cli(
        [
            "--token",
            os.environ.get("NOTION_TEST_TOKEN"),
            "--url",
            test_db.url,
            "--missing-relations-action",
            "ignore",
            str(test_file),
        ]
    )

    test_db.refresh()
    test_db_relation.refresh()

    table_main_rows = test_db.rows
    table_main_header = {c["name"] for c in test_db.schema}

    table_relation_rows = test_db_relation.rows
    table_relation_header = {c["name"] for c in test_db_relation.schema}

    relation_column = f"Related to {test_db.page.title} (b)"

    assert table_main_header == {"a", "b"}
    assert len(table_main_rows) == 1
    assert table_relation_header == {"c", "d", relation_column}
    assert len(table_relation_rows) == 0

    assert getattr(table_main_rows[0], "a") == "aa"
    assert getattr(table_main_rows[0], "b") == []
