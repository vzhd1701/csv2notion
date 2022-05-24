import logging

import pytest


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_column_types_person(tmp_path, db_maker):
    test_user_name = db_maker.client.current_user.name

    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text(f"a,b\na1,{test_user_name}\na2,bad\na3,")

    test_db = db_maker.from_cli(
        "--token",
        db_maker.token,
        "--column-types",
        "person",
        "--max-threads=1",
        str(test_file),
    )

    assert test_db.schema_dict["b"]["type"] == "person"

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 3

    assert test_db.rows[0].columns["a"] == "a1"
    assert test_db.rows[0].columns["b"] == [db_maker.client.current_user]
    assert test_db.rows[1].columns["a"] == "a2"
    assert test_db.rows[1].columns["b"] == []
    assert test_db.rows[2].columns["a"] == "a3"
    assert test_db.rows[2].columns["b"] == []


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_column_types_person_missing(tmp_path, db_maker, caplog):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("a,b\na1,missing")

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        test_db = db_maker.from_cli(
            "--token",
            db_maker.token,
            "--column-types",
            "person",
            str(test_file),
        )

    assert test_db.schema_dict["b"]["type"] == "person"

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1

    assert test_db.rows[0].columns["a"] == "a1"
    assert test_db.rows[0].columns["b"] == []

    assert "Person 'missing' cannot be resolved." in caplog.text


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_column_types_person_missing_fail(tmp_path, db_maker, caplog):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("a,b\na1,missing")

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        e = db_maker.from_raising_cli(
            "--token",
            db_maker.token,
            "--column-types",
            "person",
            "--fail-on-conversion-error",
            str(test_file),
        )

    assert "Error during conversion" in str(e.raised)
    assert "Person 'missing' cannot be resolved." in caplog.text


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_column_types_person_email(tmp_path, db_maker):
    test_user_email = db_maker.client.current_user.email

    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text(f"a,b\na1,{test_user_email}")

    test_db = db_maker.from_cli(
        "--token",
        db_maker.token,
        "--column-types",
        "person",
        str(test_file),
    )

    assert test_db.schema_dict["b"]["type"] == "person"

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1

    assert test_db.rows[0].columns["a"] == "a1"
    assert test_db.rows[0].columns["b"] == [db_maker.client.current_user]


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_column_types_person_email_external(tmp_path, db_maker, caplog):
    test_user = db_maker.find_user("test_py_notion2@protonmail.com")

    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text(f"a,b\na1,{test_user.email}")

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        test_db = db_maker.from_cli(
            "--token",
            db_maker.token,
            "--column-types",
            "person",
            str(test_file),
        )

    assert test_db.schema_dict["b"]["type"] == "person"

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1

    assert test_db.rows[0].columns["a"] == "a1"
    assert test_db.rows[0].columns["b"] == [test_user]


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_column_types_person_email_missing(tmp_path, db_maker, caplog):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("a,b\na1,missing@mail.com")

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        test_db = db_maker.from_cli(
            "--token",
            db_maker.token,
            "--column-types",
            "person",
            str(test_file),
        )

    assert test_db.schema_dict["b"]["type"] == "person"

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1

    assert test_db.rows[0].columns["a"] == "a1"
    assert test_db.rows[0].columns["b"] == []

    assert "Person 'missing@mail.com' cannot be resolved." in caplog.text


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_column_types_person_email_missing_fail(tmp_path, db_maker, caplog):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("a,b\na1,missing@mail.com")

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        e = db_maker.from_raising_cli(
            "--token",
            db_maker.token,
            "--column-types",
            "person",
            "--fail-on-conversion-error",
            str(test_file),
        )

    assert "Error during conversion" in str(e.raised)
    assert "Person 'missing@mail.com' cannot be resolved." in caplog.text
