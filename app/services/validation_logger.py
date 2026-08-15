import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class ValidationLogger:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log_failure(
        self,
        *,
        schema_name: str,
        attempt: int,
        raw_output: str,
        error_type: str,
        details: list[dict[str, Any]],
    ) -> None:
        record = {
            "timestamp": datetime.now(UTC).isoformat(),
            "schema_name": schema_name,
            "attempt": attempt,
            "error_type": error_type,
            "details": details,
            "raw_output": raw_output,
        }
        with self.path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
