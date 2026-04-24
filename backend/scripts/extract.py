from __future__ import annotations

import argparse
import json

from app.config import get_settings
from app.pipeline import ExtractionPipeline


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract structured consultant requests from input files."
    )
    parser.add_argument("paths", nargs="+", help="One or more file paths to process")
    args = parser.parse_args()

    pipeline = ExtractionPipeline(get_settings())
    results = [
        pipeline.process_file(path).model_dump(mode="json") for path in args.paths
    ]
    if len(results) == 1:
        print(json.dumps(results[0], indent=2, ensure_ascii=False))
    else:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
