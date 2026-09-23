# Security boundaries

## Identity and ownership

Cloud Run IAM gates all three functions. API requests additionally undergo local verification of the Google ID token. The ownership hash uses canonical issuer plus numeric subject. Caller-supplied email, tenant, project, native job ID, or cluster fields are not accepted as authentication or placement authority.

Worker and reconciler trust only their platform-authenticated service identities. Do not grant public invoker, broad project-wide invoker, or direct access to their service accounts. A project administrator remains a trusted operator and can alter IAM and job records.

## Runtime permissions

| Runtime | Dataproc permissions | Other access |
|---|---|---|
| API | `jobs.get` | Firestore read/write, publish jobs, prefix-scoped driver object reads |
| Worker | `jobs.create`, `jobs.get`, `clusters.use` | Firestore read/write |
| Reconciler | `jobs.get`, `jobs.cancel` | Firestore read/write, publish jobs |

No runtime may create/delete a cluster or delete a Dataproc job. Dataproc grants and `roles/datastore.user` are project scoped; application profiles enforce allowed cluster names and tenant records. This is not IAM-level per-cluster or per-tenant isolation. Use a dedicated project or separate deployments for stronger isolation. The build identity is separate and uses Cloud Build's builder role plus source reads.

## Artifact and data controls

Only configured GCS JAR directories and input/output prefixes are admitted. Drivers run under the existing cluster VM service account and may access anything it can access. A malicious approved JAR can bypass the admission path policy internally; restrict artifact writers and use narrowly scoped cluster service accounts.

Runtime API access to GCS logs grants only object get with resource-name conditions on configured prefixes. The log endpoint first verifies ownership and the remote job fingerprint. Consumers cannot specify a log URL. The API does not list buckets or expose signed download URLs.

## Bounds and observability

HTTP bodies, arguments, pagination, log ranges, dispatch attempts, admission age, API rates, daily admissions, instance counts and reconciliation batches are bounded. Function infrastructure can buffer an HTTP body before application code; the 64 KiB application check is not a claim about edge-level request buffering.

Structured logs include generated request IDs, status codes, exception types and hashed job IDs/state transitions. Job arguments, tokens, input data and SDK exception text are omitted. Driver logs returned to authorized owners may contain application-sensitive content, so treat them accordingly.

## Remaining operational risks

Native request-ID deduplication is not an unlimited exactly-once guarantee. Administrative deletion/recreation of remote jobs can race verification; runtime roles cannot perform those deletions. Protect Firestore, deployment credentials, approved artifacts and cluster administrators. Terraform budgets send notifications and do not cap spend or stop a running cluster.

Report vulnerabilities privately to the repository owner before publishing sensitive reproduction details. Include the affected component, expected boundary, and a minimal test with no credentials.
