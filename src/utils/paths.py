from __future__ import annotations

from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def imports_dir() -> Path:
    return project_root() / "imports"


def processed_data_dir() -> Path:
    return project_root() / "data" / "processed"


def hypotheses_data_dir() -> Path:
    return project_root() / "data" / "hypotheses"


def decision_data_dir() -> Path:
    return project_root() / "data" / "decision"


def gold_import_path() -> Path:
    return imports_dir() / "xauusd_d.csv"


def silver_import_path() -> Path:
    return imports_dir() / "xagusd_d.csv"
