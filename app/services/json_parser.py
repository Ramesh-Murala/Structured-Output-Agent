import json
from typing import Any


class JSONParseError(ValueError):
    pass


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise JSONParseError("Duplicate JSON object key")
        result[key] = value
    return result


def parse_json_object(raw_output: str) -> dict[str, Any]:
    try:
        value = json.loads(raw_output, object_pairs_hook=_reject_duplicate_keys)
    except json.JSONDecodeError as exc:
        raise JSONParseError(str(exc)) from exc

    if not isinstance(value, dict):
        raise JSONParseError("Expected a JSON object at the top level")

    return value
