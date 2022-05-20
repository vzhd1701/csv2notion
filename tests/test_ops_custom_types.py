import datetime
import logging
import re

import pytest

from csv2notion.cli import cli
from csv2notion.utils_exceptions import CriticalError


def test_custom_types_bad():
    with pytest.raises(CriticalError) as e:
        cli(
            "--token",
            "fake",
            "--custom-types",
            "bad_type",
            "--url",
            "https://www.notion.so/test",
            "fake_file",
        )

    assert "Unknown types: bad_type; allowed types:" in str(e.value)


def test_custom_types_bad_count(tmp_path):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b\na,b")

    with pytest.raises(CriticalError) as e:
        cli(
            "--token",
            "fake",
            "--custom-types",
            "text,text",
            "--url",
            "https://www.notion.so/test",
            str(test_file),
        )

    assert "Each column (except key) type must be defined in custom types list" in str(
        e.value
    )


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_custom_types_checkbox(tmp_path, db_maker):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("a,b\na,true\nb,false\nc,test")

    test_db = db_maker.from_cli(
        "--token",
        db_maker.token,
        "--custom-types",
        "checkbox",
        "--max-threads=1",
        str(test_file),
    )

    assert test_db.schema_dict["b"]["type"] == "checkbox"

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 3

    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"] == True
    assert test_db.rows[1].columns["a"] == "b"
    assert test_db.rows[1].columns["b"] == False
    assert test_db.rows[2].columns["a"] == "c"
    assert test_db.rows[2].columns["b"] == False


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_custom_types_date(tmp_path, db_maker):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("a,b\na,2001-12-01\nb,bad")

    test_db = db_maker.from_cli(
        "--token",
        db_maker.token,
        "--custom-types",
        "date",
        "--max-threads=1",
        str(test_file),
    )

    assert test_db.schema_dict["b"]["type"] == "date"

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 2

    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"].start == datetime.datetime(2001, 12, 1)
    assert test_db.rows[1].columns["a"] == "b"
    assert test_db.rows[1].columns["b"] is None


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_custom_types_textlike(tmp_path, db_maker):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("a,b,c,d,e\na1,b1,c1,d1,e1")

    test_db = db_maker.from_cli(
        "--token",
        db_maker.token,
        "--custom-types",
        "email,phone_number,url,text",
        "--max-threads=1",
        str(test_file),
    )

    assert test_db.schema_dict["b"]["type"] == "email"
    assert test_db.schema_dict["c"]["type"] == "phone_number"
    assert test_db.schema_dict["d"]["type"] == "url"
    assert test_db.schema_dict["e"]["type"] == "text"

    assert test_db.header == {"a", "b", "c", "d", "e"}
    assert len(test_db.rows) == 1

    assert test_db.rows[0].columns["a"] == "a1"
    assert test_db.rows[0].columns["b"] == "b1"
    assert test_db.rows[0].columns["c"] == "c1"
    assert test_db.rows[0].columns["d"] == "d1"
    assert test_db.rows[0].columns["e"] == "e1"


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_custom_types_multi_select(tmp_path, db_maker):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text('a,b\na,"b1, b2, b3"')

    test_db = db_maker.from_cli(
        "--token",
        db_maker.token,
        "--custom-types",
        "multi_select",
        "--max-threads=1",
        str(test_file),
    )

    options = {v["value"] for v in test_db.schema_dict["b"]["options"]}

    assert test_db.schema_dict["b"]["type"] == "multi_select"
    assert options == {"b1", "b2", "b3"}

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 1

    assert test_db.rows[0].columns["a"] == "a"
    assert test_db.rows[0].columns["b"] == ["b1", "b2", "b3"]


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_custom_types_select(tmp_path, db_maker):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("a,b\na1,b1\na2,b2")

    test_db = db_maker.from_cli(
        "--token",
        db_maker.token,
        "--custom-types",
        "select",
        "--max-threads=1",
        str(test_file),
    )

    options = {v["value"] for v in test_db.schema_dict["b"]["options"]}

    assert test_db.schema_dict["b"]["type"] == "select"
    assert options == {"b1", "b2"}

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 2

    assert test_db.rows[0].columns["a"] == "a1"
    assert test_db.rows[0].columns["b"] == "b1"
    assert test_db.rows[1].columns["a"] == "a2"
    assert test_db.rows[1].columns["b"] == "b2"


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_custom_types_number(tmp_path, db_maker):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("a,b\na1,100\na2,1.25\na3,bad")

    test_db = db_maker.from_cli(
        "--token",
        db_maker.token,
        "--custom-types",
        "number",
        "--max-threads=1",
        str(test_file),
    )

    assert test_db.schema_dict["b"]["type"] == "number"

    assert test_db.header == {"a", "b"}
    assert len(test_db.rows) == 3

    assert test_db.rows[0].columns["a"] == "a1"
    assert test_db.rows[0].columns["b"] == 100
    assert test_db.rows[1].columns["a"] == "a2"
    assert test_db.rows[1].columns["b"] == 1.25
    assert test_db.rows[2].columns["a"] == "a3"
    assert test_db.rows[2].columns["b"] is None
