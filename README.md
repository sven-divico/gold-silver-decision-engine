# Gold & Silver Decision Engine

Lean FastAPI MVP for comparing physical gold and silver scenarios with a server-rendered UI, SQLite persistence, and room for later market data ingestion.

## Stack
- FastAPI
- Jinja2 templates
- SQLite
- SQLAlchemy
- Pydantic settings
- pytest

## Quick start
```bash
./scripts/quickstart.sh
```

Open `http://127.0.0.1:8000`.

Equivalent manual steps:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
python scripts/init_db.py
uvicorn app.main:app --reload
```

## Local data flows
Initialize and seed the local SQLite database:
```bash
python scripts/init_db.py
python scripts/seed_sample_data.py
```

Import historical prices from CSV:
```bash
python scripts/import_prices_csv.py path/to/prices.csv --replace-existing
```

Import historical prices from the web UI:
- open `/admin/import`
- upload a CSV file
- preview parsed rows and validation results
- confirm using `append` or `replace`
- review recent import runs and current dataset status on the same page

Manage the current historical dataset from the web UI:
- open `/admin/data`
- inspect row counts, metal coverage, and date coverage
- review dataset integrity diagnostics for duplicates, overlap, and coverage mismatches
- reset the dataset with typed `RESET` confirmation
- reseed the deterministic local sample dataset
- preview and execute repairs for duplicates and non-overlapping rows with typed `REPAIR` confirmation
- review dataset-changing events in the same audit trail

CSV contract:
```csv
date,metal,price
2025-01-01,gold,2500.00
2025-01-01,silver,30.25
```

Rules:
- `date` must be ISO format `YYYY-MM-DD`
- `metal` must be `gold` or `silver`
- `price` must be a positive EUR-per-ounce number
- `append` keeps existing historical rows and adds new ones
- `replace` clears existing historical rows before import

## Import audit trail
Every completed CSV import writes an audit row in SQLite.

Recorded metadata includes:
- timestamp
- source type and filename
- append or replace mode
- total, valid, invalid, and imported row counts
- success or failure status
- error summary when an import fails
- reset and reseed dataset events from the admin data page

## Dataset integrity checks
The admin data page also evaluates whether the current historical dataset is structurally usable for ratio analysis.

Detected issues include:
- duplicate rows for the same date and metal
- missing overlap between gold and silver dates
- coverage mismatches between metals
- empty or one-metal-only datasets

## Data repair workflow
The admin data page also provides preview-first repairs for:
- deduplicating duplicate `(date, metal)` rows while keeping the lowest row id
- pruning non-overlapping rows so only shared gold/silver dates remain

Repairs require explicit confirmation and are recorded in the same audit trail as imports and dataset resets.

## Historical ratio confidence
The calculator and admin data page also show a heuristic confidence label for historical ratio analysis:
- `high` for structurally sound overlapping data
- `medium` for usable data with caution flags such as recent repairs or minor issues
- `low` for weak or incomplete datasets

This confidence is based on stored dataset quality and recent data operations. It is not a market prediction signal.

## Historical analysis controls
The calculator page supports filtering the historical ratio view by:
- start date
- end date
- overlap-only mode

These controls update the visible ratio statistics, usable point count, and confidence label for the selected analysis view.

## Test
```bash
pytest
```
