import pytest

from app.services.json_parser import JSONParseError, parse_json_object


def test_parse_valid_json_object() -> None:
    assert parse_json_object('{"name":"Ramesh"}') == {"name": "Ramesh"}


def test_rejects_invalid_json() -> None:
    with pytest.raises(JSONParseError):
        parse_json_object('{"name":')


def test_rejects_top_level_array() -> None:
    with pytest.raises(JSONParseError, match="top level"):
        parse_json_object("[]")
