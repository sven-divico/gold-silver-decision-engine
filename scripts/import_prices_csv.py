from pathlib import Path
import argparse
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import models  # noqa: F401
from app.db import SessionLocal, create_tables
from app.repositories.prices import import_prices_from_csv


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Import historical metal prices from CSV into SQLite. "
            "Expected CSV header: date,metal,price with ISO dates and metal values gold or silver."
        )
    )
    parser.add_argument("csv_path", help="Path to CSV file with columns: date,metal,price")
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help="Delete existing historical price rows before importing the CSV.",
    )
    args = parser.parse_args()

    create_tables()
    with SessionLocal() as session:
        count = import_prices_from_csv(
            session,
            Path(args.csv_path),
            replace_existing=args.replace_existing,
        )
    print(f"Imported {count} historical price rows from CSV.")


if __name__ == "__main__":
    main()
