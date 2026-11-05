import json
import math
from typing import Any

MAX_JSON_CHARACTERS = 100_000
MAX_INTEGER_DIGITS = 1_000


class JSONParseError(ValueError):
    pass


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise JSONParseError("Duplicate JSON object key")
        result[key] = value
    return result


def _reject_non_finite_constant(value: str) -> Any:
    raise JSONParseError("Non-finite JSON number")


def _parse_finite_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise JSONParseError("Non-finite JSON number")
    return number


def _parse_bounded_int(value: str) -> int:
    digits = value.removeprefix("-")
    if len(digits) > MAX_INTEGER_DIGITS:
        raise JSONParseError(
            f"JSON integer exceeds {MAX_INTEGER_DIGITS}-digit limit"
        )
    return int(value)


def parse_json_object(raw_output: str) -> dict[str, Any]:
    if len(raw_output) > MAX_JSON_CHARACTERS:
        raise JSONParseError(
            f"JSON output exceeds {MAX_JSON_CHARACTERS}-character limit"
        )
    try:
        value = json.loads(
            raw_output, object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_non_finite_constant, parse_float=_parse_finite_float,
            parse_int=_parse_bounded_int,
        )
    except JSONParseError:
        raise
    except (json.JSONDecodeError, ValueError) as exc:
        raise JSONParseError(str(exc)) from exc

    if not isinstance(value, dict):
        raise JSONParseError("Expected a JSON object at the top level")

    return value
