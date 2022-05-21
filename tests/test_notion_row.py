from datetime import datetime

import pytest

from csv2notion.utils_exceptions import NotionError


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_notion_row_cover_block_in_transaction(db_maker):
    test_db = db_maker.from_csv_head("a")
    test_db.add_row({"a": "a"})

    test_row = test_db.rows[0]

    with pytest.raises(RuntimeError) as e:
        with test_row._client.as_atomic_transaction():
            test_row.cover_block = "https://via.placeholder.com/100"

    assert "Cannot set cover_block during atomic transaction" in str(e.value)


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_notion_row_last_edited_time_in_transaction(db_maker):
    test_db = db_maker.from_csv_head("a")
    test_db.add_row({"a": "a"})

    test_row = test_db.rows[0]

    with pytest.raises(RuntimeError) as e:
        with test_row._client.as_atomic_transaction():
            test_row.last_edited_time = datetime.now()

    assert "Cannot set last_edited_time during atomic transaction" in str(e.value)


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_notion_row_set_missing_property(db_maker):
    test_db = db_maker.from_csv_head("a")
    test_db.add_row({"a": "a"})

    test_row = test_db.rows[0]

    with pytest.raises(AttributeError) as e:
        test_row.set_property("missing", "value")

    assert "Object does not have property 'missing'" in str(e.value)


@pytest.mark.vcr()
@pytest.mark.usefixtures("vcr_uuid4")
def test_notion_row_bad_upload(db_maker, tmp_path, mocker, smallest_gif):
    test_image = tmp_path / "test_image.gif"
    test_image.write_bytes(smallest_gif)

    test_db = db_maker.from_csv_head("a")
    test_db.add_row({"a": "a"})

    test_row = test_db.rows[0]

    mocker.patch("csv2notion.notion_row_upload_file._upload_file", return_value="")
    with pytest.raises(NotionError) as e:
        test_row.cover = test_image

    assert "Could not upload file" in str(e.value)
