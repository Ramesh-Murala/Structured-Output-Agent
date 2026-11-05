import json
from typing import Any

MAX_RETRY_OUTPUT_CHARACTERS = 4_000


def build_retry_prompt(
    *,
    original_prompt: str,
    raw_output: str,
    errors: list[dict[str, Any]],
) -> str:
    output_preview = raw_output[:MAX_RETRY_OUTPUT_CHARACTERS]
    if len(raw_output) > MAX_RETRY_OUTPUT_CHARACTERS:
        output_preview += "\n[previous response truncated]"
    return (
        f"{original_prompt}\n\n"
        "Your previous response failed validation. Correct the response and return only valid JSON.\n"
        f"Previous response:\n{output_preview}\n\n"
        f"Validation errors:\n{json.dumps(errors, ensure_ascii=False)}"
    )
