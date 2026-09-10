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

