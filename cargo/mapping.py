"""Per client mapping files describe how a client's columns, units and date format map to the standard layout."""
from pathlib import Path

import pandas as pd
import yaml

STANDARD = ["awb", "origin", "destination", "flight_date", "pieces", "weight_kg",
            "length_cm", "width_cm", "height_cm", "chargeable_kg"]
LB_TO_KG = 0.45359237


def load(path):
    cfg = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    for key in ("client", "delimiter", "columns", "weight_unit", "date_format"):
        if key not in cfg:
            raise ValueError(f"mapping {path} is missing '{key}'")
    if cfg["weight_unit"] not in ("kg", "lb"):
        raise ValueError("weight_unit must be kg or lb")
    missing = [c for c in STANDARD if c not in cfg["columns"]]
    if missing:
        raise ValueError(f"mapping {path} does not map: {missing}")
    return cfg


def apply(raw: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Rename to the standard columns and convert the weights to kg. Dates stay text until validation."""
    inverse = {client_col: std for std, client_col in cfg["columns"].items()}
    missing = [c for c in inverse if c not in raw.columns]
    if missing:
        raise ValueError(f"file is missing columns the mapping expects: {missing}")
    df = raw.rename(columns=inverse)[STANDARD].copy()
    for col in ("pieces", "weight_kg", "length_cm", "width_cm", "height_cm", "chargeable_kg"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    if cfg["weight_unit"] == "lb":
        df["weight_kg"] = (df["weight_kg"] * LB_TO_KG).round(2)
        df["chargeable_kg"] = (df["chargeable_kg"] * LB_TO_KG).round(2)
    return df
