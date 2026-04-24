#!/usr/bin/env python3

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DB_PATH = ROOT / "db" / "marketpulse.sqlite3"
OUTPUT_PATH = ROOT / "frontend" / "app" / "public" / "data" / "requests.json"

SQL = """
SELECT
  request_id,
  received_at,
  source_kind,
  sender_organization,
  sender_domain,
  primary_role,
  seniority,
  sector,
  location_city,
  remote_mode,
  rate_amount,
  rate_currency,
  rate_unit,
  duration_months,
  review_status,
  overall_confidence
FROM requests
ORDER BY received_at ASC, request_id ASC
"""


def main() -> None:
  if not DB_PATH.exists():
    raise SystemExit(f"Database file not found: {DB_PATH}")

  OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

  connection = sqlite3.connect(DB_PATH)
  connection.row_factory = sqlite3.Row

  try:
    rows = [dict(row) for row in connection.execute(SQL)]
  finally:
    connection.close()

  payload = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "database_path": str(DB_PATH.relative_to(ROOT)),
    "snapshot_note": "Local SQLite snapshot for frontend analytics. Values may include partially normalized fields.",
    "row_count": len(rows),
    "requests": rows,
  }

  OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
  print(f"Wrote {len(rows)} requests to {OUTPUT_PATH}")


if __name__ == "__main__":
  main()
