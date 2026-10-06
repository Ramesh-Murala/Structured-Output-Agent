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


@pytest.mark.parametrize(
    "payload",
    ['{"name":"first","name":"second"}', '{"candidate":{"email":"a","email":"b"}}'],
)
def test_rejects_duplicate_keys_at_any_depth(payload: str) -> None:
    with pytest.raises(JSONParseError, match="Duplicate JSON object key"):
        parse_json_object(payload)
