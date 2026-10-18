"""Prometheus metrics written as a text file, so a scheduled job can expose them without running a server."""
from prometheus_client import CollectorRegistry, Counter, Gauge, write_to_textfile


def write(path, client: str, rows_in: int, rows_clean: int, by_reason: dict, go: bool):
    reg = CollectorRegistry()
    Gauge("cargo_rows_in", "Rows read from the client file", ["client"], registry=reg).labels(client).set(rows_in)
    Gauge("cargo_rows_clean", "Rows that passed all rules", ["client"], registry=reg).labels(client).set(rows_clean)
    q = Counter("cargo_rows_quarantined", "Rows sent to quarantine", ["client", "reason"], registry=reg)
    for reason, n in by_reason.items():
        q.labels(client, reason).inc(n)
    Gauge("cargo_onboarding_go", "1 when the file meets the GO threshold", ["client"], registry=reg).labels(client).set(1 if go else 0)
    write_to_textfile(str(path), reg)
