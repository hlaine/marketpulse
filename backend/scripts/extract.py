from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from app.config import get_settings
from app.models import ProviderUsage
from app.pipeline import ExtractionPipeline


SUPPORTED_SUFFIXES = {".json", ".txt", ".md"}


def _format_duration(seconds: float) -> str:
    return f"{seconds:.2f}s"


def _format_usage(usage: ProviderUsage | None) -> str:
    if usage is None:
        return "tokens n/a"
    if usage.total_tokens is not None:
        return (
            "tokens "
            f"{usage.input_tokens or 0}/{usage.output_tokens or 0}/{usage.total_tokens}"
        )
    if usage.input_tokens is not None or usage.output_tokens is not None:
        return f"tokens {usage.input_tokens or 0}/{usage.output_tokens or 0}/-"
    return "tokens n/a"


def _expand_inputs(paths: list[str]) -> list[str]:
    expanded: list[str] = []
    for raw_path in paths:
        candidate = Path(raw_path).expanduser()
        if candidate.is_dir():
            files = sorted(
                path
                for path in candidate.rglob("*")
                if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
            )
            if not files:
                expanded.append(raw_path)
                continue
            expanded.extend(str(path) for path in files)
            continue
        expanded.append(raw_path)
    return expanded


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract structured consultant requests from input files."
    )
    parser.add_argument("paths", nargs="+", help="One or more file paths to process")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print full extracted JSON instead of summary output.",
    )
    args = parser.parse_args()

    pipeline = ExtractionPipeline(get_settings())
    exit_code = 0
    started_at = time.perf_counter()
    succeeded = 0
    failed = 0
    total_input_tokens = 0
    total_output_tokens = 0
    total_tokens = 0
    json_results: list[dict] = []

    for raw_path in _expand_inputs(args.paths):
        file_started_at = time.perf_counter()
        try:
            result = pipeline.process_file_with_metadata(raw_path)
            elapsed = time.perf_counter() - file_started_at
            record = result.record
            usage = result.usage
            succeeded += 1
            if usage is not None:
                total_input_tokens += usage.input_tokens or 0
                total_output_tokens += usage.output_tokens or 0
                total_tokens += usage.total_tokens or 0

            if args.json:
                json_results.append(record.model_dump(mode="json"))
                continue

            role = record.demand.primary_role.normalized or "unknown-role"
            print(
                f"OK     {record.request_id:<10} {role:<20} {_format_duration(elapsed):>7}  {_format_usage(usage)}"
            )
        except Exception as exc:
            elapsed = time.perf_counter() - file_started_at
            failed += 1
            exit_code = 1
            if args.json:
                json_results.append({"path": raw_path, "error": str(exc)})
                continue
            path_label = str(Path(raw_path))
            print(f"ERROR  {path_label:<32} {_format_duration(elapsed):>7}  {exc}")

    if args.json:
        if len(json_results) == 1:
            print(json.dumps(json_results[0], indent=2, ensure_ascii=False))
        else:
            print(json.dumps(json_results, indent=2, ensure_ascii=False))
        return exit_code

    total_elapsed = time.perf_counter() - started_at
    print(
        f"\nDone: {succeeded} succeeded, {failed} failed, total {_format_duration(total_elapsed)}"
    )
    if total_tokens > 0 or total_input_tokens > 0 or total_output_tokens > 0:
        print(
            f"Tokens: input {total_input_tokens}, output {total_output_tokens}, total {total_tokens}"
        )
    else:
        print("Tokens: n/a")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
