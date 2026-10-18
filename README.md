# Air Cargo Client Onboarding

When an air cargo analytics company takes on a new client, the client sends a file of shipments in its own layout, its own units and its own date format. This project onboards one such file: it maps the columns to a standard layout, converts the units, checks every row against air cargo rules, sends bad rows to a quarantine file with a reason, and ends with a GO or NO-GO decision for the file. It is a practice project with invented data, built to learn the domain.

## What it checks

- AWB number: 3 digit airline prefix, 7 digit serial and a check digit. The check digit is the serial modulo 7, so a mistyped waybill is caught.
- IATA airport codes: the origin and destination must be known codes, and must differ.
- Flight date: must be readable in the client's format and not in the future.
- Weight and pieces: must be positive. Pounds are converted to kilograms.
- Chargeable weight: the larger of actual weight and volumetric weight (length x width x height in cm, divided by 6000). A file whose chargeable weight is more than 1 percent off is quarantined.
- Duplicates: the same AWB twice in one file keeps the first and quarantines the second.

Each bad row gets one reason, the first rule it breaks. More than 5 percent of rows in quarantine means NO-GO until a person has looked at the reasons and decided.

## Two sample clients

- acme_airlines: kilograms, ISO dates, comma separated.
- bluesky_forwarding: pounds, day first dates, semicolon separated, different column names.

Both files have faults planted on purpose, and the tests check that every planted fault is found with the right reason. Both first runs end in NO-GO, which is how a real first file usually goes.

A new client is a new mapping file in `clients/`, not new code.

## Run it

    pip install -r requirements.txt
    python -m cargo sample data
    python -m cargo onboard data/acme_airlines.csv clients/acme_airlines.yaml out
    python -m pytest -q

The onboard command writes a clean Parquet file, a quarantine CSV with reasons, a JSON report and a Prometheus text file (rows in, rows clean, quarantined by reason, GO flag).

With Docker:

    docker build -t cargo-onboarding .
    docker run cargo-onboarding

## Cloud and operations parts

- `cargo/s3.py` uploads and downloads files with boto3 for a landing and a processed zone on S3.
- `infra/s3.yaml` is a CloudFormation template for two private, encrypted, versioned buckets.
- `k8s/cronjob.yaml` runs the onboarding every morning as a Kubernetes CronJob, as a non root user with resource limits.
- `.github/workflows/ci.yml` runs the tests, builds the Docker image and runs it, lints the CloudFormation template with cfn-lint and validates the Kubernetes manifest with kubeconform.

## What has been run and what has not

Run and passing: the 10 pytest tests on both sample clients, the rule checks, the unit conversion and the Prometheus output. The S3 functions are tested against moto, which imitates the S3 API. The CloudFormation template passes cfn-lint, and the CronJob passes kubeconform with strict schema checking. The Docker image is built and run in the GitHub Actions workflow.

Not run: nothing here has touched a real AWS account, and the CronJob has not run on a real Kubernetes cluster. The airport list holds only 36 codes, so a real deployment would load the full IATA list.
