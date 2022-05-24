import logging

import pytest
from notion.utils import slugify

from csv2notion.cli import cli
from csv2notion.utils_exceptions import NotionError


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_relations_missing(tmp_path, db_maker, caplog):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b\naa,bb\n")

    test_db = db_maker.from_csv_head("a,b")
    test_db_relation = db_maker.from_csv_head("c,d")

    test_db.set_relation("b", test_db_relation)

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        cli(
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            str(test_file),
        )

    test_db.refresh()
    test_db_relation.refresh()

    relation_name = test_db_relation.page.title
    relation_column = f"Related to {test_db.page.title} (b)"

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1
    assert test_db_relation.header == {"c", "d", relation_column}
    assert len(test_db_relation.rows) == 0

    assert test_db.rows[0].columns["a"] == "aa"
    assert test_db.rows[0].columns["b"] == []

    assert (
        f"CSV [2]: Value 'bb' for relation 'b [column] -> {relation_name} [DB]'"
        " is not a valid value" in caplog.text
    )


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_relations_missing_fail(tmp_path, db_maker, caplog):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b\naa,bb\n")

    test_db = db_maker.from_csv_head("a,b")
    test_db_relation = db_maker.from_csv_head("c,d")

    test_db.set_relation("b", test_db_relation)

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        with pytest.raises(NotionError) as e:
            cli(
                "--token",
                db_maker.token,
                "--url",
                test_db.url,
                "--fail-on-conversion-error",
                str(test_file),
            )

    relation_name = test_db_relation.page.title

    assert "Error during conversion" in str(e.value)
    assert (
        f"CSV [2]: Value 'bb' for relation 'b [column] -> {relation_name} [DB]'"
        " is not a valid value" in caplog.text
    )


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_relations_url_404(tmp_path, db_maker, caplog):
    url_404 = "https://www.notion.so/e3dc27928dfd4f4cae532b98a76bbba1"

    test_file = tmp_path / "test.csv"
    test_file.write_text(f"a,b\naa,{url_404}")

    test_db = db_maker.from_csv_head("a,b")
    test_db_relation = db_maker.from_csv_head("c,d")

    test_db.set_relation("b", test_db_relation)

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        cli(
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            str(test_file),
        )

    test_db.refresh()
    test_db_relation.refresh()

    relation_name = test_db_relation.page.title
    relation_column = f"Related to {test_db.page.title} (b)"

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1
    assert test_db_relation.header == {"c", "d", relation_column}
    assert len(test_db_relation.rows) == 0

    assert test_db.rows[0].columns["a"] == "aa"
    assert test_db.rows[0].columns["b"] == []

    assert (
        f"CSV [2]: Row with url '{url_404}' not found"
        f" in relation 'b [column] -> {relation_name} [DB]'." in caplog.text
    )


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_relations_url_404_fail(tmp_path, db_maker, caplog):
    url_404 = "https://www.notion.so/e3dc27928dfd4f4cae532b98a76bbba1"

    test_file = tmp_path / "test.csv"
    test_file.write_text(f"a,b\naa,{url_404}")

    test_db = db_maker.from_csv_head("a,b")
    test_db_relation = db_maker.from_csv_head("c,d")

    test_db.set_relation("b", test_db_relation)

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        with pytest.raises(NotionError) as e:
            cli(
                "--token",
                db_maker.token,
                "--url",
                test_db.url,
                "--fail-on-conversion-error",
                str(test_file),
            )

    relation_name = test_db_relation.page.title

    assert "Error during conversion" in str(e.value)
    assert (
        f"CSV [2]: Row with url '{url_404}' not found"
        f" in relation 'b [column] -> {relation_name} [DB]'." in caplog.text
    )


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_relations_url_bad(tmp_path, db_maker, caplog):
    url_bad = "https://www.notion.so/123"

    test_file = tmp_path / "test.csv"
    test_file.write_text(f"a,b\naa,{url_bad}")

    test_db = db_maker.from_csv_head("a,b")
    test_db_relation = db_maker.from_csv_head("c,d")

    test_db.set_relation("b", test_db_relation)

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        cli(
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            str(test_file),
        )

    test_db.refresh()
    test_db_relation.refresh()

    relation_column = f"Related to {test_db.page.title} (b)"

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1
    assert test_db_relation.header == {"c", "d", relation_column}
    assert len(test_db_relation.rows) == 0

    assert test_db.rows[0].columns["a"] == "aa"
    assert test_db.rows[0].columns["b"] == []

    assert f"CSV [2]: '{url_bad}' is not a valid Notion URL." in caplog.text


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_relations_url_bad_fail(tmp_path, db_maker, caplog):
    url_bad = "https://www.notion.so/123"

    test_file = tmp_path / "test.csv"
    test_file.write_text(f"a,b\naa,{url_bad}")

    test_db = db_maker.from_csv_head("a,b")
    test_db_relation = db_maker.from_csv_head("c,d")

    test_db.set_relation("b", test_db_relation)

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        with pytest.raises(NotionError) as e:
            cli(
                "--token",
                db_maker.token,
                "--url",
                test_db.url,
                "--fail-on-conversion-error",
                str(test_file),
            )

    assert "Error during conversion" in str(e.value)
    assert f"CSV [2]: '{url_bad}' is not a valid Notion URL." in caplog.text


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_relations_add_missing_relations(tmp_path, db_maker):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b\naa,bb\n")

    test_db = db_maker.from_csv_head("a,b")
    test_db_relation = db_maker.from_csv_head("c,d")

    test_db.set_relation("b", test_db_relation)

    cli(
        "--token",
        db_maker.token,
        "--url",
        test_db.url,
        "--add-missing-relations",
        str(test_file),
    )

    test_db.refresh()
    test_db_relation.refresh()

    relation_column = f"Related to {test_db.page.title} (b)"

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1
    assert test_db_relation.header == {"c", "d", relation_column}
    assert len(test_db_relation.rows) == 1

    assert test_db.rows[0].columns["a"] == "aa"
    assert test_db.rows[0].columns["b"] == [test_db_relation.rows[0]]
    assert test_db_relation.rows[0].columns["c"] == "bb"
    assert test_db_relation.rows[0].columns["d"] == ""
    assert test_db_relation.rows[0].columns[slugify(relation_column)] == [
        test_db.rows[0]
    ]


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_relations_add_missing_relations_url_404(tmp_path, db_maker, caplog):
    url_404 = "https://www.notion.so/e3dc27928dfd4f4cae532b98a76bbba1"

    test_file = tmp_path / "test.csv"
    test_file.write_text(f"a,b\naa,{url_404}")

    test_db = db_maker.from_csv_head("a,b")
    test_db_relation = db_maker.from_csv_head("c,d")

    test_db.set_relation("b", test_db_relation)

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        cli(
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            "--add-missing-relations",
            str(test_file),
        )

    test_db.refresh()
    test_db_relation.refresh()

    relation_name = test_db_relation.page.title
    relation_column = f"Related to {test_db.page.title} (b)"

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1
    assert test_db_relation.header == {"c", "d", relation_column}
    assert len(test_db_relation.rows) == 0

    assert test_db.rows[0].columns["a"] == "aa"
    assert test_db.rows[0].columns["b"] == []

    assert (
        f"CSV [2]: Row with url '{url_404}' not found"
        f" in relation 'b [column] -> {relation_name} [DB]'." in caplog.text
    )


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_relations_add_missing_relations_url_404_fail(tmp_path, db_maker, caplog):
    url_404 = "https://www.notion.so/e3dc27928dfd4f4cae532b98a76bbba1"

    test_file = tmp_path / "test.csv"
    test_file.write_text(f"a,b\naa,{url_404}")

    test_db = db_maker.from_csv_head("a,b")
    test_db_relation = db_maker.from_csv_head("c,d")

    test_db.set_relation("b", test_db_relation)

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        with pytest.raises(NotionError) as e:
            cli(
                "--token",
                db_maker.token,
                "--url",
                test_db.url,
                "--add-missing-relations",
                "--fail-on-conversion-error",
                str(test_file),
            )

    relation_name = test_db_relation.page.title

    assert "Error during conversion" in str(e.value)
    assert (
        f"CSV [2]: Row with url '{url_404}' not found"
        f" in relation 'b [column] -> {relation_name} [DB]'." in caplog.text
    )


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_relations_add_missing_relations_url_bad(tmp_path, db_maker, caplog):
    url_bad = "https://www.notion.so/123"

    test_file = tmp_path / "test.csv"
    test_file.write_text(f"a,b\naa,{url_bad}")

    test_db = db_maker.from_csv_head("a,b")
    test_db_relation = db_maker.from_csv_head("c,d")

    test_db.set_relation("b", test_db_relation)

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        cli(
            "--token",
            db_maker.token,
            "--url",
            test_db.url,
            "--add-missing-relations",
            str(test_file),
        )

    test_db.refresh()
    test_db_relation.refresh()

    relation_column = f"Related to {test_db.page.title} (b)"

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1
    assert test_db_relation.header == {"c", "d", relation_column}
    assert len(test_db_relation.rows) == 0

    assert test_db.rows[0].columns["a"] == "aa"
    assert test_db.rows[0].columns["b"] == []

    assert f"CSV [2]: '{url_bad}' is not a valid Notion URL." in caplog.text


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_relations_add_missing_relations_url_bad_fail(tmp_path, db_maker, caplog):
    url_bad = "https://www.notion.so/123"

    test_file = tmp_path / "test.csv"
    test_file.write_text(f"a,b\naa,{url_bad}")

    test_db = db_maker.from_csv_head("a,b")
    test_db_relation = db_maker.from_csv_head("c,d")

    test_db.set_relation("b", test_db_relation)

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        with pytest.raises(NotionError) as e:
            cli(
                "--token",
                db_maker.token,
                "--url",
                test_db.url,
                "--add-missing-relations",
                "--fail-on-conversion-error",
                str(test_file),
            )

    assert "Error during conversion" in str(e.value)
    assert f"CSV [2]: '{url_bad}' is not a valid Notion URL." in caplog.text


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_relations_url(tmp_path, db_maker):
    test_db = db_maker.from_csv_head("a,b")
    test_db_relation = db_maker.from_csv_head("c,d")

    relation_row = test_db_relation.add_row({"c": "cc", "d": "dd"})
    relation_url = relation_row.get_browseable_url()

    test_db.set_relation("b", test_db_relation)

    test_file = tmp_path / "test.csv"
    test_file.write_text(f"a,b\naa,{relation_url}")

    cli(
        "--token",
        db_maker.token,
        "--url",
        test_db.url,
        str(test_file),
    )

    test_db.refresh()
    test_db_relation.refresh()

    relation_column = f"Related to {test_db.page.title} (b)"

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1
    assert test_db_relation.header == {"c", "d", relation_column}
    assert len(test_db_relation.rows) == 1

    assert test_db.rows[0].columns["a"] == "aa"
    assert test_db.rows[0].columns["b"] == [relation_row]
