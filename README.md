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

## Submit a job

After [deployment](docs/DEPLOYMENT.md), customize the examples and authenticate using an allowed service account:

```bash
python scripts/client.py --url "$API_URL" --impersonate "$CALLER_SERVICE_ACCOUNT" \
  submit --file examples/job.json --key wordcount-2026-001
python scripts/client.py --url "$API_URL" --impersonate "$CALLER_SERVICE_ACCOUNT" history
python scripts/client.py --url "$API_URL" --impersonate "$CALLER_SERVICE_ACCOUNT" get "$JOB_ID"
python scripts/client.py --url "$API_URL" --impersonate "$CALLER_SERVICE_ACCOUNT" logs "$JOB_ID"
python scripts/client.py --url "$API_URL" --impersonate "$CALLER_SERVICE_ACCOUNT" cancel "$JOB_ID"
```

A new admission returns HTTP 202. A same-key replay returns 200 without consuming another daily job unit. Use the same key after a transport error; a different key requests a different job. Choose a fresh output directory for each logical run.

## Recovery semantics

Firestore persists a native Dataproc request UUID and a unique job ID before dispatch. Ambiguous submissions are looked up by that exact job ID, verified against their submission label and Hadoop inputs, and may retry with the **same IDs**, at most five attempts within 24 hours. Once attached, the immutable remote job UUID fences later reads. Cancellation intent survives concurrent submission.

`NEEDS_REVIEW` stops automation when an outcome cannot be established. It does **not** prove that a remote job stopped or failed. The service does not promise exactly-once Hadoop side effects; see [architecture](docs/ARCHITECTURE.md).

## Included infrastructure

Terraform provisions three IAM-private functions, separate runtime identities, a protected Firestore database and indexes, authenticated Pub/Sub push with dead letters, minute reconciliation, private source storage, alerting, and a project-filtered billing budget. It binds narrow Dataproc permissions to a dedicated project and object-read access to approved log prefixes. Existing clusters, JARs, input/output buckets, and their runtime permissions remain prerequisites.

Deployment is manual through the OIDC workflow or Terraform. Publication and CI do not deploy cloud resources or run billable Hadoop jobs.

