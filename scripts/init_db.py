from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db import create_tables
from app import models  # noqa: F401


def main() -> None:
    create_tables()
    print("Database initialized.")


if __name__ == "__main__":
    main()
