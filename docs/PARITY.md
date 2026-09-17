# Functional comparison

The OCI baseline reviewed is commit `af9ac91b845aa1b8b709d1fdf74b58dc3cdeadde`. The AWS baseline is `63b7daf05cd453cb9d800b092453f17eb7fc03fd`. Cloud-specific capabilities are mapped explicitly rather than represented as identical transports.

## Feature mapping

| Capability | OCI baseline | AWS implementation | This GCP implementation |
|---|---|---|---|
| Hadoop JAR execution | SSH `hadoop jar` | EMR HadoopJarStep | Dataproc HadoopJob |
| Four job fields | Required | Preserved with profile | Preserved with profile |
| Execution | Synchronous, 30-second command deadline | Asynchronous | Asynchronous |
| Command safety | Shell quoting and pinned host key | Structured SDK arguments | Structured SDK arguments |
| Job metadata/history | No persistent job store | DynamoDB | Firestore transactions and indexed history |
| Admission idempotency | None | Tenant-bound key | Subject-bound key plus native Dataproc request UUID |
| Ambiguous submit | Caller receives generic error | Exact step-name reconciliation, no automatic resubmit | Verified exact job lookup; bounded retries with original native IDs |
| Ownership | Function/SSH access | IAM principal hash | Verified Google issuer + numeric subject hash |
| Quotas | No daily admission ledger | Atomic UTC-day and minute counters | Transactional UTC-day and minute counters |
| Cancellation | No durable cancellation endpoint | Intent plus EMR cancellation | Intent plus Dataproc cancellation |
| Logs | Concurrent stdout/stderr, each bounded to 1 MiB | Bounded S3 step streams | Bounded segmented GCS driver output |
| Infrastructure | OCI-specific resources | AWS Terraform | GCP Terraform, OIDC, alerts, budgets |

## Deliberate platform differences

The API returns an accepted job record, not synchronous stdout/stderr. Dataproc's driver output is exposed as `stream=driver`; independent YARN/container stderr remains in the cluster's configured logging system. No claim is made that Dataproc driver output contains every container log.

GCS replaces S3/OCI object URIs. HDFS input paths work on the selected existing cluster. Approved GCS JARs and a fully qualified Java main class map to `jar_file_uris` and `main_class`. The service does not offer arbitrary shell commands, local JAR uploads, cluster creation, or Dataproc Serverless batches.

