"""Offline fault injection. Measures validation behavior, not model intelligence."""
import argparse
import asyncio
import json
import tempfile
from pathlib import Path

from app.llm.mock_provider import MockProvider
from app.services.agent import StructuredOutputAgent
from app.services.validation_logger import ValidationLogger


async def evaluate():
    cases = json.loads(Path(__file__).with_name("cases.json").read_text())
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        for case in cases:
            results = []
            for retries in (0, 2):
                agent = StructuredOutputAgent(
                    provider=MockProvider(case["outputs"]),
                    validation_logger=ValidationLogger(Path(tmp) / "failures.jsonl"),
                )
                results.append(await agent.run(prompt=case["prompt"], schema_name=case["schema"], max_retries=retries))
            baseline, corrected = results
            rows.append(dict(case=case["name"], first_response_valid=baseline.success,
                             after_retry_valid=corrected.success, provider_calls=corrected.attempts,
                             expected_success=case["expected_success"],
                             failures=[f.error_type for f in corrected.validation_failures]))
    return dict(mode="offline_scripted_fault_injection", cases=len(rows),
                first_response_validity=sum(r["first_response_valid"] for r in rows) / len(rows),
                after_retry_validity=sum(r["after_retry_valid"] for r in rows) / len(rows),
                mean_provider_calls=sum(r["provider_calls"] for r in rows) / len(rows),
                results=rows,
                limitation="Scripted corrections; not live-model success rates, factual accuracy, token cost, or provider latency.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = asyncio.run(evaluate())
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    print(rendered)
    if any(r["after_retry_valid"] != r["expected_success"] for r in result["results"]):
        raise SystemExit("Validation regression")
