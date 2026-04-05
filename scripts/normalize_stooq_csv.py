#!/usr/bin/env python3

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
IMPORTS_DIR = ROOT / "imports"
OUTPUT_PATH = IMPORTS_DIR / "normalized_gold_silver.csv"


@dataclass(frozen=True, slots=True)
class NormalizedRow:
    recorded_on: date
    metal: str
    price: float


def main() -> None:
    sources = [
        ("xauusd_d.csv", "gold"),
        ("xagusd_d.csv", "silver"),
    ]

    normalized_rows: set[NormalizedRow] = set()
    rows_read_by_file: dict[str, int] = {}

    for filename, metal in sources:
        path = IMPORTS_DIR / filename
        rows = read_stooq_rows(path, metal)
        rows_read_by_file[filename] = rows["rows_read"]
        normalized_rows.update(rows["normalized_rows"])

    ordered_rows = sorted(normalized_rows, key=lambda row: (row.recorded_on, row.metal))
    write_normalized_csv(OUTPUT_PATH, ordered_rows)

    if ordered_rows:
        date_min = ordered_rows[0].recorded_on.isoformat()
        date_max = ordered_rows[-1].recorded_on.isoformat()
    else:
        date_min = "n/a"
        date_max = "n/a"

    for filename, count in rows_read_by_file.items():
        print(f"{filename}: read {count} data rows")
    print(f"normalized_gold_silver.csv: wrote {len(ordered_rows)} rows")
    print(f"date range: {date_min} -> {date_max}")


def read_stooq_rows(path: Path, metal: str) -> dict[str, object]:
    if not path.exists():
        raise FileNotFoundError(f"Missing input file: {path}")

    normalized_rows: set[NormalizedRow] = set()
    rows_read = 0

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"CSV file has no header: {path}")
        fieldnames = [field.strip().lower() for field in reader.fieldnames]
        if "date" not in fieldnames or "close" not in fieldnames:
            raise ValueError(f"CSV file must contain Date and Close columns: {path}")

        for raw_row in reader:
            rows_read += 1
            row = {str(key).strip().lower(): (value or "").strip() for key, value in raw_row.items()}
            if not row.get("close"):
                continue

            recorded_on = date.fromisoformat(row["date"])
            price = float(row["close"])
            if price <= 0:
                continue

            normalized_rows.add(
                NormalizedRow(
                    recorded_on=recorded_on,
                    metal=metal,
                    price=round(price, 2),
                )
            )

    return {"rows_read": rows_read, "normalized_rows": normalized_rows}


def write_normalized_csv(path: Path, rows: list[NormalizedRow]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["date", "metal", "price"])
        for row in rows:
            writer.writerow([row.recorded_on.isoformat(), row.metal, f"{row.price:.2f}"])


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Normalization failed: {exc}", file=sys.stderr)
        raise
