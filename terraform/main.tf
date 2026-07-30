terraform {
  required_version = ">= 1.9, < 2.0"
  backend "gcs" {}
  required_providers {
    google-beta = { source = "hashicorp/google-beta", version = "~> 7.0" }
    google      = { source = "hashicorp/google", version = "~> 7.0" }
    archive     = { source = "hashicorp/archive", version = "~> 2.7" }
  }
}
provider "google" {
  project = var.project_id
  region  = var.region
}
provider "google-beta" {
  project = var.project_id
  region  = var.region
}
data "google_project" "current" { project_id = var.project_id }
locals {
  prefix        = "${var.name}-${var.environment}"
  labels        = { service = "hadoop-automation", environment = var.environment, managed_by = "terraform" }
  api_url       = "https://${var.region}-${var.project_id}.cloudfunctions.net/${local.prefix}-api"
  runtime_names = toset(["api", "worker", "reconcile"])
  consumers     = toset(flatten([for p in var.cluster_profiles : p.allowed_callers]))
  common_env = {
    GCP_PROJECT_ID      = var.project_id
    DATAPROC_REGION     = var.region
    FIRESTORE_DATABASE  = google_firestore_database.data.name
    JOB_TOPIC           = google_pubsub_topic.jobs.id
    SERVICE_NAME        = local.prefix
    CLUSTER_PROFILES    = jsonencode(var.cluster_profiles)
    DAILY_JOB_LIMIT     = tostring(var.daily_job_limit)
    REQUESTS_PER_MINUTE = tostring(var.requests_per_minute)
    RETENTION_DAYS      = tostring(var.retention_days)
  }
}
