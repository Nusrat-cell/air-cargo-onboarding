"""Row rules. Each failing row gets exactly one reason (the first rule it breaks) and goes to quarantine."""
from datetime import datetime

import pandas as pd

from . import awb
from .airports import IATA

VOLUMETRIC_DIVISOR = 6000  # cm3 per kg, the usual IATA air cargo rule
TOLERANCE = 0.01


def validate(df: pd.DataFrame, date_format: str, today: datetime):
    """Return (clean, quarantine). quarantine has a 'reason' column."""
    df = df.copy()
    df["flight_dt"] = pd.to_datetime(df["flight_date"], format=date_format, errors="coerce")
    df["volumetric_kg"] = (df["length_cm"] * df["width_cm"] * df["height_cm"] / VOLUMETRIC_DIVISOR).round(2)
    expected = df[["weight_kg", "volumetric_kg"]].max(axis=1)
    reason = pd.Series("", index=df.index, dtype="object")

    def mark(mask, text):
        hit = mask & (reason == "")
        reason[hit] = text

    mark(~df["awb"].astype(str).map(awb.is_valid), "invalid AWB number or check digit")
    mark(df["awb"].astype(str).str.replace("-", "").duplicated(keep="first") & (reason == ""), "duplicate AWB in file")
    mark(~df["origin"].isin(IATA) | ~df["destination"].isin(IATA), "unknown IATA airport code")
    mark(df["origin"] == df["destination"], "origin equals destination")
    mark(df["flight_dt"].isna(), "unreadable flight date")
    mark(df["flight_dt"] > pd.Timestamp(today), "flight date in the future")
    mark(~(df["weight_kg"] > 0) | ~(df["pieces"] > 0), "weight or pieces not positive")
    mark(df["volumetric_kg"].isna(), "dimensions missing")
    mark(((df["chargeable_kg"] - expected).abs() > expected * TOLERANCE), "chargeable weight does not match")

    quarantine = df[reason != ""].copy()
    quarantine["reason"] = reason[reason != ""]
    clean = df[reason == ""].drop(columns=["flight_date"]).rename(columns={"flight_dt": "flight_date"})
    return clean.reset_index(drop=True), quarantine.reset_index(drop=True)
