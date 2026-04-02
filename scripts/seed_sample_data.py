from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import models  # noqa: F401
from app.db import SessionLocal, create_tables
from app.services.data_management import reseed_historical_data


def main() -> None:
    create_tables()

    with SessionLocal() as session:
        result = reseed_historical_data(
            session,
            source_type="cli_seed",
            source_name="seed_sample_data.py",
        )

    print(result.message)


if __name__ == "__main__":
    main()
