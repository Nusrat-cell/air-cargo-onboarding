from datetime import datetime

import pandas as pd
import pytest

from cargo import mapping, pipeline, sample

TODAY = datetime(2026, 10, 19)


@pytest.fixture(scope="module")
def planted_files(tmp_path_factory):
    d = tmp_path_factory.mktemp("data")
    planted = sample.write(d)
    return d, planted


@pytest.mark.parametrize("client", ["acme_airlines", "bluesky_forwarding"])
def test_every_planted_fault_is_quarantined_with_its_reason(planted_files, tmp_path, client):
    d, planted = planted_files
    report = pipeline.onboard(d / f"{client}.csv", f"clients/{client}.yaml", tmp_path, today=TODAY)
    assert report["by_reason"] == planted[client]
    assert report["rows_clean"] + report["rows_quarantined"] == report["rows_in"]


def test_pounds_are_converted_to_kilograms(planted_files, tmp_path):
    d, _ = planted_files
    pipeline.onboard(d / "bluesky_forwarding.csv", "clients/bluesky_forwarding.yaml", tmp_path, today=TODAY)
    clean = pd.read_parquet(tmp_path / "bluesky_forwarding_clean.parquet")
    assert clean["weight_kg"].between(10, 1000).all()


def test_small_file_goes_and_dirty_file_does_not(tmp_path):
    clean_rows = sample._rows(100, 5)
    pd.DataFrame([{"AWB": r["awb"], "Origin": r["origin"], "Dest": r["destination"], "FlightDate": r["date"],
                   "Pcs": r["pieces"], "WeightKg": r["weight"], "L": r["l"], "W": r["w"], "H": r["h"],
                   "ChgKg": r["chargeable"]} for r in clean_rows]).to_csv(tmp_path / "ok.csv", index=False)
    assert pipeline.onboard(tmp_path / "ok.csv", "clients/acme_airlines.yaml", tmp_path / "o1", today=TODAY)["decision"] == "GO"
    rows = sample._rows(40, 6)
    for r in rows[:10]:
        r["origin"] = "XXX"
    pd.DataFrame([{"AWB": r["awb"], "Origin": r["origin"], "Dest": r["destination"], "FlightDate": r["date"],
                   "Pcs": r["pieces"], "WeightKg": r["weight"], "L": r["l"], "W": r["w"], "H": r["h"],
                   "ChgKg": r["chargeable"]} for r in rows]).to_csv(tmp_path / "bad.csv", index=False)
    assert pipeline.onboard(tmp_path / "bad.csv", "clients/acme_airlines.yaml", tmp_path / "o2", today=TODAY)["decision"] == "NO-GO"


def test_mapping_that_misses_a_column_is_rejected(tmp_path):
    bad = tmp_path / "m.yaml"
    bad.write_text('client: x\ndelimiter: ","\nweight_unit: kg\ndate_format: "%Y-%m-%d"\ncolumns:\n  awb: AWB\n', encoding="utf-8")
    with pytest.raises(ValueError):
        mapping.load(bad)


def test_prometheus_file_has_quarantine_counts(planted_files, tmp_path):
    d, _ = planted_files
    pipeline.onboard(d / "acme_airlines.csv", "clients/acme_airlines.yaml", tmp_path, today=TODAY)
    text = (tmp_path / "acme_airlines.prom").read_text()
    assert "cargo_rows_in" in text and "cargo_rows_quarantined_total" in text and "cargo_onboarding_go" in text
