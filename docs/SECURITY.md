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

