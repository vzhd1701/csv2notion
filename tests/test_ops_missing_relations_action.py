import os

import pytest
from notion.utils import slugify

from csv2notion.cli import cli
from csv2notion.utils_exceptions import NotionError


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
                db_maker.token,
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


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_missing_relations_action_fail_url_404(tmp_path, db_maker):
    url_404 = "https://www.notion.so/e3dc27928dfd4f4cae532b98a76bbba1"

    test_file = tmp_path / "test.csv"
    test_file.write_text(f"a,b\naa,{url_404}")

    test_db = db_maker.from_csv_head("a,b")
    test_db_relation = db_maker.from_csv_head("c,d")

    test_db.set_relation("b", test_db_relation)

    with pytest.raises(NotionError) as e:
        cli(
            [
                "--token",
                db_maker.token,
                "--url",
                test_db.url,
                "--missing-relations-action",
                "fail",
                str(test_file),
            ]
        )

    relation_name = test_db_relation.page.title

    assert (
        f"CSV [2]: Row with url '{url_404}' not found"
        f" in relation 'b [column] -> {relation_name} [DB]'." in str(e.value)
    )


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_missing_relations_action_fail_url_bad(tmp_path, db_maker):
    url_bad = "https://www.notion.so/123"

    test_file = tmp_path / "test.csv"
    test_file.write_text(f"a,b\naa,{url_bad}")

    test_db = db_maker.from_csv_head("a,b")
    test_db_relation = db_maker.from_csv_head("c,d")

    test_db.set_relation("b", test_db_relation)

    with pytest.raises(NotionError) as e:
        cli(
            [
                "--token",
                db_maker.token,
                "--url",
                test_db.url,
                "--missing-relations-action",
                "fail",
                str(test_file),
            ]
        )

    assert f"CSV [2]: '{url_bad}' is not a valid Notion URL." in str(e.value)


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
            db_maker.token,
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

    assert getattr(table_main_rows[0].columns, "a") == "aa"
    assert getattr(table_main_rows[0].columns, "b") == [table_relation_rows[0]]
    assert getattr(table_relation_rows[0].columns, "c") == "bb"
    assert getattr(table_relation_rows[0].columns, "d") == ""
    assert getattr(table_relation_rows[0].columns, slugify(relation_column)) == [
        table_main_rows[0]
    ]


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_missing_relations_action_add_url_404(tmp_path, db_maker):
    url_404 = "https://www.notion.so/e3dc27928dfd4f4cae532b98a76bbba1"

    test_file = tmp_path / "test.csv"
    test_file.write_text(f"a,b\naa,{url_404}")

    test_db = db_maker.from_csv_head("a,b")
    test_db_relation = db_maker.from_csv_head("c,d")

    test_db.set_relation("b", test_db_relation)

    with pytest.raises(NotionError) as e:
        cli(
            [
                "--token",
                db_maker.token,
                "--url",
                test_db.url,
                "--missing-relations-action",
                "add",
                str(test_file),
            ]
        )

    relation_name = test_db_relation.page.title

    assert (
        f"CSV [2]: Row with url '{url_404}' not found"
        f" in relation 'b [column] -> {relation_name} [DB]'." in str(e.value)
    )


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_missing_relations_action_add_url_bad(tmp_path, db_maker):
    url_bad = "https://www.notion.so/123"

    test_file = tmp_path / "test.csv"
    test_file.write_text(f"a,b\naa,{url_bad}")

    test_db = db_maker.from_csv_head("a,b")
    test_db_relation = db_maker.from_csv_head("c,d")

    test_db.set_relation("b", test_db_relation)

    with pytest.raises(NotionError) as e:
        cli(
            [
                "--token",
                db_maker.token,
                "--url",
                test_db.url,
                "--missing-relations-action",
                "add",
                str(test_file),
            ]
        )

    assert f"CSV [2]: '{url_bad}' is not a valid Notion URL." in str(e.value)


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
            db_maker.token,
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

    assert getattr(table_main_rows[0].columns, "a") == "aa"
    assert getattr(table_main_rows[0].columns, "b") == []


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_missing_relations_action_ignore_url_404(tmp_path, db_maker):
    url_404 = "https://www.notion.so/e3dc27928dfd4f4cae532b98a76bbba1"

    test_file = tmp_path / "test.csv"
    test_file.write_text(f"a,b\naa,{url_404}")

    test_db = db_maker.from_csv_head("a,b")
    test_db_relation = db_maker.from_csv_head("c,d")

    test_db.set_relation("b", test_db_relation)

    cli(
        [
            "--token",
            db_maker.token,
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

    assert getattr(table_main_rows[0].columns, "a") == "aa"
    assert getattr(table_main_rows[0].columns, "b") == []


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_missing_relations_action_ignore_url_bad(tmp_path, db_maker):
    url_bad = "https://www.notion.so/123"

    test_file = tmp_path / "test.csv"
    test_file.write_text(f"a,b\naa,{url_bad}")

    test_db = db_maker.from_csv_head("a,b")
    test_db_relation = db_maker.from_csv_head("c,d")

    test_db.set_relation("b", test_db_relation)

    cli(
        [
            "--token",
            db_maker.token,
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

    assert getattr(table_main_rows[0].columns, "a") == "aa"
    assert getattr(table_main_rows[0].columns, "b") == []


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_missing_relations_action_ignore_url_ok(tmp_path, db_maker):
    test_db = db_maker.from_csv_head("a,b")
    test_db_relation = db_maker.from_csv_head("c,d")

    relation_row = test_db_relation.add_row({"c": "cc", "d": "dd"})
    relation_url = relation_row.get_browseable_url()

    test_db.set_relation("b", test_db_relation)

    test_file = tmp_path / "test.csv"
    test_file.write_text(f"a,b\naa,{relation_url}")

    cli(
        [
            "--token",
            db_maker.token,
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
    assert len(table_relation_rows) == 1

    assert getattr(table_main_rows[0].columns, "a") == "aa"
    assert getattr(table_main_rows[0].columns, "b") == [relation_row]
