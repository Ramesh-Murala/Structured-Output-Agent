import json
from typing import Any


class JSONParseError(ValueError):
    pass


def parse_json_object(raw_output: str) -> dict[str, Any]:
    try:
        value = json.loads(raw_output)
    except json.JSONDecodeError as exc:
        raise JSONParseError(str(exc)) from exc

    if not isinstance(value, dict):
        raise JSONParseError("Expected a JSON object at the top level")

    return value
