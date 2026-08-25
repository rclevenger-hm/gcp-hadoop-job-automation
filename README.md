# GCP Hadoop Job Automation

[![CI](https://github.com/rclevenger-hm/gcp-hadoop-job-automation/actions/workflows/ci.yml/badge.svg)](https://github.com/rclevenger-hm/gcp-hadoop-job-automation/actions/workflows/ci.yml)

A private, asynchronous Hadoop JAR job service for **existing Google Cloud Dataproc clusters**. Python Cloud Run functions admit jobs, persist ownership and state in Firestore, dispatch through Pub/Sub, and reconcile native Dataproc status every minute.

It preserves the OCI service's `jar_path`, `job_class`, `input_path`, and `output_path` contract. A server-configured `profile` selects an approved cluster and URI prefixes. The service adds durable idempotency, job history, quotas, cancellation, and bounded driver-output reads. It creates no clusters and opens no SSH connections.

## Quick start

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --require-hashes -r requirements-dev.txt
ruff check app tests scripts main.py
python -m pytest
python scripts/check_contract.py
python scripts/build.py
terraform -chdir=terraform init -backend=false -lockfile=readonly
terraform -chdir=terraform validate
terraform -chdir=terraform test
```

CI uses Python 3.13 and Terraform 1.13.5. Local Python 3.12 is also supported. Tests use local fakes and SDK protobuf validation; they do not start a cluster or execute a Hadoop job.

