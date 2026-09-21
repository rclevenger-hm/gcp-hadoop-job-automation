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

