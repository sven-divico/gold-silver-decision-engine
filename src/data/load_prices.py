from __future__ import annotations

from pathlib import Path
import re

import pandas as pd


ASSET_COLUMN_PREFIX = {
    "gold": "gold",
    "silver": "silver",
}

OPTIONAL_PRICE_COLUMNS = ("open", "high", "low", "volume")


def load_gold_prices(path: str | Path) -> pd.DataFrame:
    return _load_prices(path, asset_name="gold")


def load_silver_prices(path: str | Path) -> pd.DataFrame:
    return _load_prices(path, asset_name="silver")


def normalize_price_frame(df: pd.DataFrame, asset_name: str) -> pd.DataFrame:
    prefix = _asset_prefix(asset_name)
    if df.empty:
        raise ValueError(f"{asset_name} price data is empty.")

    normalized = df.copy()
    normalized.columns = [_to_snake_case(column) for column in normalized.columns]

    date_column = _require_column(normalized, "date", asset_name)
    close_column = _require_column(normalized, "close", asset_name)

    keep_columns = [date_column, close_column]
    keep_columns.extend(column for column in OPTIONAL_PRICE_COLUMNS if column in normalized.columns)
    normalized = normalized.loc[:, keep_columns]

    normalized[date_column] = pd.to_datetime(normalized[date_column], errors="coerce")
    if normalized[date_column].isna().any():
        raise ValueError(f"{asset_name} price data contains invalid dates.")

    normalized[close_column] = pd.to_numeric(normalized[close_column], errors="coerce")
    if normalized[close_column].isna().any():
        raise ValueError(f"{asset_name} close column is not numeric after coercion.")

    for column in OPTIONAL_PRICE_COLUMNS:
        if column in normalized.columns:
            normalized[column] = pd.to_numeric(normalized[column], errors="coerce")

    rename_map = {
        date_column: "date",
        close_column: f"{prefix}_close",
    }
    for column in OPTIONAL_PRICE_COLUMNS:
        if column in normalized.columns:
            rename_map[column] = f"{prefix}_{column}"

    normalized = normalized.rename(columns=rename_map)
    normalized = normalized.sort_values("date")
    normalized = normalized.drop_duplicates(subset="date", keep="last")
    normalized["date"] = normalized["date"].dt.normalize()
    normalized = normalized.reset_index(drop=True)

    normalized.attrs["source_metadata"] = {
        "asset": asset_name,
        "normalized_rows": int(len(normalized)),
        "date_min": _iso_date(normalized["date"].min()),
        "date_max": _iso_date(normalized["date"].max()),
    }
    return normalized


def _load_prices(path: str | Path, *, asset_name: str) -> pd.DataFrame:
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Missing input file: {csv_path}")

    raw = pd.read_csv(csv_path)
    normalized = normalize_price_frame(raw, asset_name=asset_name)
    source_metadata = dict(normalized.attrs.get("source_metadata", {}))
    source_metadata.update(
        {
            "source_path": str(csv_path),
            "original_rows": int(len(raw)),
        }
    )
    normalized.attrs["source_metadata"] = source_metadata
    return normalized


def _require_column(df: pd.DataFrame, column_name: str, asset_name: str) -> str:
    if column_name not in df.columns:
        raise ValueError(f"{asset_name} price data is missing required column: {column_name}")
    return column_name


def _asset_prefix(asset_name: str) -> str:
    if asset_name not in ASSET_COLUMN_PREFIX:
        raise ValueError(f"Unsupported asset name: {asset_name}")
    return ASSET_COLUMN_PREFIX[asset_name]


def _to_snake_case(value: str) -> str:
    value = value.strip()
    value = re.sub(r"[^0-9A-Za-z]+", "_", value)
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    return value.strip("_").lower()


def _iso_date(value: pd.Timestamp | None) -> str | None:
    if value is None or pd.isna(value):
        return None
    return value.date().isoformat()
