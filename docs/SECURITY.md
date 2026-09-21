# Security boundaries

## Identity and ownership

Cloud Run IAM gates all three functions. API requests additionally undergo local verification of the Google ID token. The ownership hash uses canonical issuer plus numeric subject. Caller-supplied email, tenant, project, native job ID, or cluster fields are not accepted as authentication or placement authority.

Worker and reconciler trust only their platform-authenticated service identities. Do not grant public invoker, broad project-wide invoker, or direct access to their service accounts. A project administrator remains a trusted operator and can alter IAM and job records.

