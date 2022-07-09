import os
from pathlib import Path

import pytest
from notion.client import NotionClient

from csv2notion.notion_db_client import NotionClientExtended
from tests.fixtures.db_maker_class import NotionDBMaker


@pytest.fixture()
def db_maker(vcr_cassette_dir, vcr_cassette_name):
    token = _get_token(vcr_cassette_dir, vcr_cassette_name)

    client = NotionClientExtended(token_v2=token)

    test_page_title = "TESTING PAGE"

    _ensure_empty_workspace(client, test_page_title)

    notion_db_maker = NotionDBMaker(client, token, test_page_title)

    yield notion_db_maker

    notion_db_maker.cleanup()


def _get_token(vcr_cassette_dir, vcr_cassette_name):
    casette_path = Path(vcr_cassette_dir) / f"{vcr_cassette_name}.yaml"

    # if cassette exists and no token, probably CI test
    if casette_path.exists() and not os.environ.get("NOTION_TEST_TOKEN"):
        token = "fake_token"
    else:
        token = os.environ.get("NOTION_TEST_TOKEN")

    if not token:
        raise RuntimeError(
            "No token found. Set NOTION_TEST_TOKEN environment variable."
        )

    return token


def _ensure_empty_workspace(client, test_page_title):
    """Ensures that testing starts with empty workspace"""

    try:
        top_pages = client.get_top_level_pages()
    except KeyError:  # pragma: no cover
        # Need empty account to test
        top_pages = []

    _remove_top_pages_with_title(top_pages, test_page_title)

    if top_pages:
        raise RuntimeError("Testing requires empty account")


def _remove_top_pages_with_title(top_pages, test_page_title):
    """
    Removes all pages with title `test_page_title` from the current workspace
    Also removes half-baked collections without title attribute
    """

    for page in top_pages.copy():
        try:
            if page.title == test_page_title:
                page.remove(permanently=True)
        except AttributeError:
            page.remove(permanently=True)
