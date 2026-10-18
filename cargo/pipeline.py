"""Onboard one client file: read, map, validate, write clean data and quarantine, decide GO or NO-GO."""
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from . import mapping, metrics, validate

GO_THRESHOLD = 0.05  # more than 5 percent quarantined means NO-GO until someone decides


def onboard(client_file, mapping_file, out_dir, today=None):
    today = today or datetime.now()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    cfg = mapping.load(mapping_file)
    raw = pd.read_csv(client_file, sep=cfg["delimiter"], dtype=str)
    mapped = mapping.apply(raw, cfg)
    clean, quarantine = validate.validate(mapped, cfg["date_format"], today)

    clean.to_parquet(out / f"{cfg['client']}_clean.parquet", index=False)
    quarantine.to_csv(out / f"{cfg['client']}_quarantine.csv", index=False)

    rows_in = len(raw)
    share = len(quarantine) / rows_in if rows_in else 1.0
    go = share <= GO_THRESHOLD
    by_reason = quarantine["reason"].value_counts().to_dict()
    report = {
        "client": cfg["client"], "rows_in": rows_in, "rows_clean": len(clean),
        "rows_quarantined": len(quarantine), "quarantine_share": round(share, 4),
        "by_reason": by_reason, "decision": "GO" if go else "NO-GO",
    }
    (out / f"{cfg['client']}_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    metrics.write(out / f"{cfg['client']}.prom", cfg["client"], rows_in, len(clean), by_reason, go)
    return report
