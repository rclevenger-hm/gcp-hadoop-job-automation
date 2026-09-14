# Operations

## Routine checks

Monitor function 5xx rates, Pub/Sub dead letters, scheduler delivery, and `NEEDS_REVIEW` state alerts. Confirm notification email channels. Inspect Cloud Logging events `api_request`, `api_error`, `worker_error`, `reconcile_complete`, and `job_state`. The request ID is returned in `X-Request-Id`.

Use the API's status/history/usage endpoints for caller-visible state. Query native Dataproc status as an operator when diagnosing a discrepancy. The control plane polls each minute but the 120-second lease, shard limits and backlog can extend visible latency.

## Submission outcome unknown

Wait for the grace period and exact native lookup. The system can retry only with the original persisted `submission_id` and `dataproc_job_id`. Investigate Dataproc availability and worker IAM if the status persists. Do not submit a fresh logical key just to make an ambiguous request disappear; that requests a second job.

For `NEEDS_REVIEW`, inspect the recorded profile/request, native ID, submission label, Hadoop inputs and any attached `remote_uuid` before deciding whether execution occurred. This state stops automatic changes and does not imply the remote workload is stopped. Record the operator decision externally; no unsafe force-reset endpoint is provided.

