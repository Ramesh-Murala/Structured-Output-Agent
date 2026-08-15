import json
from typing import Any


def build_retry_prompt(
    *,
    original_prompt: str,
    raw_output: str,
    errors: list[dict[str, Any]],
) -> str:
    return (
        f"{original_prompt}\n\n"
        "Your previous response failed validation. Correct the response and return only valid JSON.\n"
        f"Previous response:\n{raw_output}\n\n"
        f"Validation errors:\n{json.dumps(errors, ensure_ascii=False)}"
    )
