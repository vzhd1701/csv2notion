import datetime
import logging
import os
import re

import pytest
from dateutil.tz import tz

from csv2notion.cli import cli
from csv2notion.utils import CriticalError


def test_custom_types_bad():
    with pytest.raises(CriticalError) as e:
        cli(
            [
                "--token",
                "fake",
                "--custom-types",
                "bad_type",
                "--url",
                "https://www.notion.so/test",
                "fake_file",
            ]
        )

    assert "Unknown types: bad_type; allowed types:" in str(e.value)


def test_custom_types_bad_count(tmp_path):
    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b\na,b")

    with pytest.raises(CriticalError) as e:
        cli(
            [
                "--token",
                "fake",
                "--custom-types",
                "text,text",
                "--url",
                "https://www.notion.so/test",
                str(test_file),
            ]
        )

    assert "Each column (except key) type must be defined in custom types list" in str(
        e.value
    )


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_custom_types_checkbox(tmp_path, caplog, db_maker):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("a,b\na,true\nb,false\nc,test")

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        cli(
            [
                "--token",
                db_maker.token,
                "--custom-types",
                "checkbox",
                "--max-threads=1",
                str(test_file),
            ]
        )

    url = re.search(r"New database URL: (.*)$", caplog.text, re.M)[1]

    test_db = db_maker.from_url(url)

    table_rows = test_db.rows
    table_header = test_db.header

    assert test_db.schema_dict["b"]["type"] == "checkbox"

    assert table_header == {"a", "b"}
    assert len(table_rows) == 3

    assert getattr(table_rows[0], "a") == "a"
    assert getattr(table_rows[0], "b") == True
    assert getattr(table_rows[1], "a") == "b"
    assert getattr(table_rows[1], "b") == False
    assert getattr(table_rows[2], "a") == "c"
    assert getattr(table_rows[2], "b") == False


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_custom_types_date(tmp_path, caplog, db_maker):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("a,b\na,2001-12-01\nb,bad")

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        cli(
            [
                "--token",
                db_maker.token,
                "--custom-types",
                "date",
                "--max-threads=1",
                str(test_file),
            ]
        )

    url = re.search(r"New database URL: (.*)$", caplog.text, re.M)[1]

    test_db = db_maker.from_url(url)

    table_rows = test_db.rows
    table_header = test_db.header

    assert test_db.schema_dict["b"]["type"] == "date"

    assert table_header == {"a", "b"}
    assert len(table_rows) == 2

    assert getattr(table_rows[0], "a") == "a"
    assert getattr(table_rows[0], "b").start == datetime.datetime(2001, 12, 1)
    assert getattr(table_rows[1], "a") == "b"
    assert getattr(table_rows[1], "b") is None


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_custom_types_textlike(tmp_path, caplog, db_maker):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("a,b,c,d,e\na1,b1,c1,d1,e1")

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        cli(
            [
                "--token",
                db_maker.token,
                "--custom-types",
                "email,phone_number,url,text",
                "--max-threads=1",
                str(test_file),
            ]
        )

    url = re.search(r"New database URL: (.*)$", caplog.text, re.M)[1]

    test_db = db_maker.from_url(url)

    table_rows = test_db.rows
    table_header = test_db.header

    assert test_db.schema_dict["b"]["type"] == "email"
    assert test_db.schema_dict["c"]["type"] == "phone_number"
    assert test_db.schema_dict["d"]["type"] == "url"
    assert test_db.schema_dict["e"]["type"] == "text"

    assert table_header == {"a", "b", "c", "d", "e"}
    assert len(table_rows) == 1

    assert getattr(table_rows[0], "a") == "a1"
    assert getattr(table_rows[0], "b") == "b1"
    assert getattr(table_rows[0], "c") == "c1"
    assert getattr(table_rows[0], "d") == "d1"
    assert getattr(table_rows[0], "e") == "e1"


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_custom_types_multi_select(tmp_path, caplog, db_maker):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text('a,b\na,"b1, b2, b3"')

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        cli(
            [
                "--token",
                db_maker.token,
                "--custom-types",
                "multi_select",
                "--max-threads=1",
                str(test_file),
            ]
        )

    url = re.search(r"New database URL: (.*)$", caplog.text, re.M)[1]

    test_db = db_maker.from_url(url)

    table_rows = test_db.rows
    table_header = test_db.header

    options = {v["value"] for v in test_db.schema_dict["b"]["options"]}

    assert test_db.schema_dict["b"]["type"] == "multi_select"
    assert options == {"b1", "b2", "b3"}

    assert table_header == {"a", "b"}
    assert len(table_rows) == 1

    assert getattr(table_rows[0], "a") == "a"
    assert getattr(table_rows[0], "b") == ["b1", "b2", "b3"]


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_custom_types_select(tmp_path, caplog, db_maker):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("a,b\na1,b1\na2,b2")

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        cli(
            [
                "--token",
                db_maker.token,
                "--custom-types",
                "select",
                "--max-threads=1",
                str(test_file),
            ]
        )

    url = re.search(r"New database URL: (.*)$", caplog.text, re.M)[1]

    test_db = db_maker.from_url(url)

    table_rows = test_db.rows
    table_header = test_db.header

    options = {v["value"] for v in test_db.schema_dict["b"]["options"]}

    assert test_db.schema_dict["b"]["type"] == "select"
    assert options == {"b1", "b2"}

    assert table_header == {"a", "b"}
    assert len(table_rows) == 2

    assert getattr(table_rows[0], "a") == "a1"
    assert getattr(table_rows[0], "b") == "b1"
    assert getattr(table_rows[1], "a") == "a2"
    assert getattr(table_rows[1], "b") == "b2"


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_custom_types_number(tmp_path, caplog, db_maker):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("a,b\na1,100\na2,1.25\na3,bad")

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        cli(
            [
                "--token",
                db_maker.token,
                "--custom-types",
                "number",
                "--max-threads=1",
                str(test_file),
            ]
        )

    url = re.search(r"New database URL: (.*)$", caplog.text, re.M)[1]

    test_db = db_maker.from_url(url)

    table_rows = test_db.rows
    table_header = test_db.header

    assert test_db.schema_dict["b"]["type"] == "number"

    assert table_header == {"a", "b"}
    assert len(table_rows) == 3

    assert getattr(table_rows[0], "a") == "a1"
    assert getattr(table_rows[0], "b") == 100
    assert getattr(table_rows[1], "a") == "a2"
    assert getattr(table_rows[1], "b") == 1.25
    assert getattr(table_rows[2], "a") == "a3"
    assert getattr(table_rows[2], "b") is None


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_custom_types_created_time(tmp_path, caplog, db_maker):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("a,b\na,2001-12-01\nb,bad")

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        cli(
            [
                "--token",
                db_maker.token,
                "--custom-types",
                "created_time",
                "--max-threads=1",
                str(test_file),
            ]
        )

    url = re.search(r"New database URL: (.*)$", caplog.text, re.M)[1]

    test_db = db_maker.from_url(url)
    test_client = test_db.page._client

    table_rows = test_db.rows
    table_header = test_db.header

    cur_timezone = tz.gettz(
        test_client.get_record_data("user_settings", test_client.current_user.id)[
            "settings"
        ]["time_zone"]
    )
    test_time = datetime.datetime(2001, 12, 1).replace(tzinfo=cur_timezone)
    test_time = test_time.astimezone(tz.tzutc())
    test_time = test_time.replace(tzinfo=None)

    assert test_db.schema_dict["b"]["type"] == "created_time"

    assert table_header == {"a", "b"}
    assert len(table_rows) == 2

    assert getattr(table_rows[0], "a") == "a"
    assert getattr(table_rows[0], "b") == test_time
    assert getattr(table_rows[1], "a") == "b"
    # this one will be set to now, but it's generated by server so we can't check it
    assert isinstance(getattr(table_rows[1], "b"), datetime.datetime)


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_custom_types_last_edited_time(tmp_path, caplog, db_maker):
    test_file = tmp_path / f"{db_maker.page_name}.csv"
    test_file.write_text("a,b\na,2001-12-01\nb,bad")

    with caplog.at_level(logging.INFO, logger="csv2notion"):
        cli(
            [
                "--token",
                db_maker.token,
                "--custom-types",
                "last_edited_time",
                "--max-threads=1",
                str(test_file),
            ]
        )

    url = re.search(r"New database URL: (.*)$", caplog.text, re.M)[1]

    test_db = db_maker.from_url(url)
    test_client = test_db.page._client

    table_rows = test_db.rows
    table_header = test_db.header

    cur_timezone = tz.gettz(
        test_client.get_record_data("user_settings", test_client.current_user.id)[
            "settings"
        ]["time_zone"]
    )
    test_time = datetime.datetime(2001, 12, 1).replace(tzinfo=cur_timezone)
    test_time = test_time.astimezone(tz.tzutc())
    test_time = test_time.replace(tzinfo=None)

    assert test_db.schema_dict["b"]["type"] == "last_edited_time"

    assert table_header == {"a", "b"}
    assert len(table_rows) == 2

    assert getattr(table_rows[0], "a") == "a"
    assert getattr(table_rows[0], "b") == test_time
    assert getattr(table_rows[1], "a") == "b"
    # this one will be set to now, but it's generated by server so we can't check it
    assert isinstance(getattr(table_rows[1], "b"), datetime.datetime)
