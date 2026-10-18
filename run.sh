#!/bin/sh
# Generate the sample client files, then onboard both clients and print the reports.
python -m cargo sample /data/in
python -m cargo onboard /data/in/acme_airlines.csv clients/acme_airlines.yaml /data/out || true
python -m cargo onboard /data/in/bluesky_forwarding.csv clients/bluesky_forwarding.yaml /data/out || true
ls /data/out
