# GCP Hadoop Job Automation

[![CI](https://github.com/rclevenger-hm/gcp-hadoop-job-automation/actions/workflows/ci.yml/badge.svg)](https://github.com/rclevenger-hm/gcp-hadoop-job-automation/actions/workflows/ci.yml)

A private, asynchronous Hadoop JAR job service for **existing Google Cloud Dataproc clusters**. Python Cloud Run functions admit jobs, persist ownership and state in Firestore, dispatch through Pub/Sub, and reconcile native Dataproc status every minute.

It preserves the OCI service's `jar_path`, `job_class`, `input_path`, and `output_path` contract. A server-configured `profile` selects an approved cluster and URI prefixes. The service adds durable idempotency, job history, quotas, cancellation, and bounded driver-output reads. It creates no clusters and opens no SSH connections.

