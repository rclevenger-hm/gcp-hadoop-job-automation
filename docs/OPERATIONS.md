# Operations

## Routine checks

Monitor function 5xx rates, Pub/Sub dead letters, scheduler delivery, and `NEEDS_REVIEW` state alerts. Confirm notification email channels. Inspect Cloud Logging events `api_request`, `api_error`, `worker_error`, `reconcile_complete`, and `job_state`. The request ID is returned in `X-Request-Id`.

Use the API's status/history/usage endpoints for caller-visible state. Query native Dataproc status as an operator when diagnosing a discrepancy. The control plane polls each minute but the 120-second lease, shard limits and backlog can extend visible latency.

## Submission outcome unknown

Wait for the grace period and exact native lookup. The system can retry only with the original persisted `submission_id` and `dataproc_job_id`. Investigate Dataproc availability and worker IAM if the status persists. Do not submit a fresh logical key just to make an ambiguous request disappear; that requests a second job.

For `NEEDS_REVIEW`, inspect the recorded profile/request, native ID, submission label, Hadoop inputs and any attached `remote_uuid` before deciding whether execution occurred. This state stops automatic changes and does not imply the remote workload is stopped. Record the operator decision externally; no unsafe force-reset endpoint is provided.

## Cancellation

Cancellation before any dispatch is immediate. Otherwise the API records intent and reconciliation calls Dataproc cancellation after verifying remote identity. Native completion may win. Missing or mismatched remote jobs require review rather than cancellation of an unverified replacement. Check the cluster when cancellation cannot be confirmed.

## Queue and dead letters

A publish failure leaves a durable queued record for reconciliation. Duplicate Pub/Sub messages are harmless because dispatch requires a versioned queued-state claim. Malformed/unprocessable deliveries return a retryable status and can move to the dead-letter topic after Pub/Sub's approximate delivery-attempt threshold.

Inspect dead letters before replay. Fix IAM/configuration errors first. Replaying an original tenant/job reference consults durable state and cannot start a terminal or expired job. The queue retention is one day, dead-letter retention seven days, and new dispatch expires after one day.

## Logs and data retention

Driver output is uploaded asynchronously in numbered GCS segments. Use byte offsets and check later when `LOG_NOT_READY` appears. YARN/container logs follow the existing cluster logging configuration. This stack does not manage lifecycle or retention of JARs, job output, driver logs, or the cluster staging bucket.

Terminal metadata is visible for the configured retention period, then hidden immediately while Firestore TTL deletion catches up. Active records never expire automatically. Review uncertain terminal records before their retention expires. PITR is enabled for Firestore; recovery and replacement-database cutover require a deliberate operator procedure.

## Backlog and service changes

The reconciler rotates through 16 hash shards with up to 25 candidates each and a time budget. Scale the deployment only after examining remote API latency, Firestore contention and scheduler overlap. Daily limits are per authenticated subject, not global project spend caps. Keep project/region/database stable with active jobs.

Before removing a profile or caller, decide how its existing jobs will be observed and cancelled. Admitted jobs retain their profile snapshot, but callers removed from the global allowed email list lose API access; operators must manage those remaining jobs.
