"""Two invented clients with different layouts and planted faults, so every rule has something to catch."""
import random
from pathlib import Path

import pandas as pd

from . import awb
from .airports import IATA

CODES = sorted(IATA)
PREFIXES = ["176", "074", "020", "157"]


def _rows(n, seed):
    rnd = random.Random(seed)
    rows = []
    for i in range(n):
        o, d = rnd.sample(CODES, 2)
        l, w, h = rnd.randint(40, 120), rnd.randint(30, 100), rnd.randint(30, 100)
        actual = round(rnd.uniform(20, 900), 2)
        vol = round(l * w * h / 6000, 2)
        rows.append(dict(awb=awb.make(rnd.choice(PREFIXES), 1000000 + i * 13), origin=o, destination=d,
                         date=f"2026-0{rnd.randint(1, 9)}-{rnd.randint(10, 28)}", pieces=rnd.randint(1, 12),
                         weight=actual, l=l, w=w, h=h, chargeable=round(max(actual, vol), 2)))
    return rows


def _plant(rows, seed):
    """Break some rows on purpose and return how many of each fault were planted."""
    rnd = random.Random(seed + 1)
    idx = rnd.sample(range(5, len(rows)), 14)
    rows[idx[0]]["awb"] = rows[idx[0]]["awb"][:-1] + str((int(rows[idx[0]]["awb"][-1]) + 1) % 7)
    rows[idx[1]]["awb"] = rows[idx[1]]["awb"][:-1] + str((int(rows[idx[1]]["awb"][-1]) + 2) % 7)
    rows[idx[2]]["origin"] = "XXX"
    rows[idx[3]]["destination"] = rows[idx[3]]["origin"]
    rows[idx[4]]["date"] = "not a date"
    rows[idx[5]]["date"] = "2031-01-15"
    rows[idx[6]]["weight"] = 0
    rows[idx[7]]["pieces"] = 0
    rows[idx[8]]["chargeable"] = round(rows[idx[8]]["chargeable"] * 1.4, 2)
    rows[idx[9]]["chargeable"] = round(rows[idx[9]]["chargeable"] * 0.6, 2)
    rows[idx[10]]["l"] = None
    rows.append(dict(rows[2]))   # exact duplicate of an earlier row
    rows.append(dict(rows[3]))
    return {"invalid AWB number or check digit": 2, "duplicate AWB in file": 2, "unknown IATA airport code": 1,
            "origin equals destination": 1, "unreadable flight date": 1, "flight date in the future": 1,
            "weight or pieces not positive": 2, "chargeable weight does not match": 2, "dimensions missing": 1}


def write(directory):
    d = Path(directory)
    d.mkdir(parents=True, exist_ok=True)
    # Client A: kilograms, ISO dates, comma separated
    a = _rows(200, 11)
    planted_a = _plant(a, 11)
    pd.DataFrame([{"AWB": r["awb"], "Origin": r["origin"], "Dest": r["destination"], "FlightDate": r["date"],
                   "Pcs": r["pieces"], "WeightKg": r["weight"], "L": r["l"], "W": r["w"], "H": r["h"],
                   "ChgKg": r["chargeable"]} for r in a]).to_csv(d / "acme_airlines.csv", index=False)
    # Client B: pounds, day first dates, semicolon separated, different column names
    b = _rows(150, 22)
    planted_b = _plant(b, 22)
    rows = []
    for r in b:
        y, m, dd = r["date"].split("-") if r["date"].count("-") == 2 else ("", "", "")
        date = f"{dd}/{m}/{y}" if y.isdigit() else r["date"]
        rows.append({"Waybill": r["awb"].replace("-", ""), "From": r["origin"], "To": r["destination"],
                     "Date": date, "Packages": r["pieces"], "GrossLb": round(r["weight"] * 2.2046, 2) if r["weight"] else 0,
                     "Len": r["l"], "Wid": r["w"], "Hei": r["h"], "ChargeLb": round(r["chargeable"] * 2.2046, 2)})
    pd.DataFrame(rows).to_csv(d / "bluesky_forwarding.csv", index=False, sep=";")
    return {"acme_airlines": planted_a, "bluesky_forwarding": planted_b}
