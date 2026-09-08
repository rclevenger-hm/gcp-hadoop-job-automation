# Deployment

## Prerequisites

Use a dedicated billed Google Cloud project. Supply an existing regional Dataproc classic cluster capable of Hadoop JAR jobs, an approved GCS JAR, input/output locations, and the actual cluster driver-output bucket/prefix. The cluster's VM service account and Dataproc service agent must already have their required compute, storage, networking and logging access. No arbitrary local JAR upload is performed by this service.

The cluster executes trusted approved application code under its VM service account. Configure that account's data access, egress, encryption, logging and network isolation before exposing the API. Ensure application artifacts cannot be replaced by API consumers. Prefix validation is admission policy, not a sandbox for arbitrary JAR code.

Create a protected, versioned GCS Terraform state bucket outside this stack. Enable Google Cloud credentials through ADC or workload identity. Deployment credentials need permission to manage the resources declared in Terraform, attach the build/runtime accounts, bind IAM, enable APIs, and create the billing budget. Runtime accounts have narrower permissions.

