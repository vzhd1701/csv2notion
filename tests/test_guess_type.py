import pytest

from csv2notion.notion_type_guess import (
    guess_type_by_values,
    is_checkbox,
    is_email,
    is_number,
    is_url,
)


@pytest.mark.parametrize(
    "value,result",
    [
        ("123", True),
        ("-123", True),
        ("-1.12", True),
        ("Nan", False),
        ("abc", False),
        ("", False),
    ],
)
def test_is_number(value, result):
    assert is_number(value) == result


@pytest.mark.parametrize(
    "value,result",
    [
        ("http://google.com", True),
        ("https://google.com", True),
        ("abc", False),
        ("", False),
    ],
)
def test_is_url(value, result):
    assert is_url(value) == result


@pytest.mark.parametrize(
    "value,result",
    [
        ("test@example.com", True),
        ("test.best@example.com", True),
        ("abc", False),
        ("", False),
    ],
)
def test_is_email(value, result):
    assert is_email(value) == result


@pytest.mark.parametrize(
    "value,result",
    [
        ("true", True),
        ("false", True),
        ("abc", False),
        ("", False),
    ],
)
def test_is_checkbox(value, result):
    assert is_checkbox(value) == result


@pytest.mark.parametrize(
    "values,result",
    [
        (["true"], "checkbox"),
        (["true", "false"], "checkbox"),
        (["true", "false", ""], "checkbox"),
        (["true", "false", "abc"], "text"),
    ],
)
def test_guess_type_by_values(values, result):
    assert guess_type_by_values(values) == result
