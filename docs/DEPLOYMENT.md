# Deployment

## Prerequisites

Use a dedicated billed Google Cloud project. Supply an existing regional Dataproc classic cluster capable of Hadoop JAR jobs, an approved GCS JAR, input/output locations, and the actual cluster driver-output bucket/prefix. The cluster's VM service account and Dataproc service agent must already have their required compute, storage, networking and logging access. No arbitrary local JAR upload is performed by this service.

The cluster executes trusted approved application code under its VM service account. Configure that account's data access, egress, encryption, logging and network isolation before exposing the API. Ensure application artifacts cannot be replaced by API consumers. Prefix validation is admission policy, not a sandbox for arbitrary JAR code.

Create a protected, versioned GCS Terraform state bucket outside this stack. Enable Google Cloud credentials through ADC or workload identity. Deployment credentials need permission to manage the resources declared in Terraform, attach the build/runtime accounts, bind IAM, enable APIs, and create the billing budget. Runtime accounts have narrower permissions.

## Local deployment

```bash
python scripts/build.py
cp terraform/terraform.tfvars.example terraform/development.tfvars
# Edit every placeholder; existing cluster and bucket names must be real.
terraform -chdir=terraform init -lockfile=readonly \
  -backend-config=bucket=YOUR_STATE_BUCKET -backend-config=prefix=hadoop/dev
terraform -chdir=terraform plan -var-file=development.tfvars -out=deploy.tfplan
terraform -chdir=terraform apply deploy.tfplan
terraform -chdir=terraform output -raw api_url
```

Review the plan first. It creates the control plane, source bucket, IAM grants, database, queue, scheduler, alerts and budget. It does not create/resize/delete a Dataproc cluster. Build the `artifacts/` source directory before Terraform packaging. Cloud Build installs pinned, hashed runtime requirements on Python 3.13; no locally compiled binaries are shipped.

## GitHub OIDC workflow

Configure Workload Identity Federation restricted to this repository and the intended branch/environment. The deployment service account must trust that provider through `roles/iam.workloadIdentityUser`; avoid JSON service-account keys. Protect the selected GitHub environment and review its cloud deployment permissions.

Set these environment variables in GitHub: `GCP_WORKLOAD_IDENTITY_PROVIDER`, `GCP_DEPLOY_SERVICE_ACCOUNT`, `GCP_PROJECT_ID`, `GCP_REGION`, `FIRESTORE_LOCATION`, `SERVICE_NAME` (default `hadoop`), `CLUSTER_PROFILES` (JSON map shaped like `examples/profiles.json`), `TF_STATE_BUCKET`, `NOTIFICATION_EMAIL`, `BILLING_ACCOUNT_ID`, `MONTHLY_BUDGET` (default 100), and `BUDGET_CURRENCY` (default USD).

Run **Deploy GCP** manually and choose dev/stage/prod. It runs application checks, builds sources, authenticates without a stored key, validates/tests Terraform, plans/applies using remote state, and confirms anonymous API access is denied. It never submits a live Hadoop job. CI alone does not deploy.

## Consumer identity

For local development, run `gcloud auth application-default login` using an identity allowed to impersonate an approved consumer service account. Grant token creation only on that consumer account, and use the CLI's `--impersonate` flag. The CLI mints an ID token with email and sends the two required headers.

On Google Cloud, ADC can obtain an ID token from the runtime service-account identity. That account must appear in a profile's `allowed_callers`. Ownership uses the numeric service-account subject, so deleting and recreating an account with the same email does not transfer old jobs.

## Read-only acceptance check

```bash
python scripts/smoke.py --url "$API_URL" --impersonate "$CALLER_SERVICE_ACCOUNT"
```

Verify Pub/Sub's service agent has token creation on the dedicated push identity and publisher/subscriber grants for dead-letter forwarding. Verify Scheduler can invoke reconciliation, Firestore indexes are ready, and notification emails are confirmed. These are provisioned by Terraform but live deployment remains the final integration check.

## Upgrades and rollback

Keep the same service prefix, project, region and Firestore database while jobs are active. Profiles are snapshotted for admitted jobs, but SDK project/region come from runtime configuration. Do not repoint them during active execution. Change infrastructure in a reviewed plan, preserve state, and deploy a previously verified source revision to roll back code.

Firestore deletion protection and `ABANDON` prevent accidental database destruction through normal stack teardown. Source-bucket force deletion is disabled. A deliberate retirement must first reconcile remote jobs, preserve needed records, and separately remove retained resources.
