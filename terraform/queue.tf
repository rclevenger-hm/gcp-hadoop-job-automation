resource "google_pubsub_topic" "jobs" {
  name                       = "${local.prefix}-jobs"
  message_retention_duration = "86400s"
  labels                     = local.labels
  depends_on                 = [google_project_service.required]
}
resource "google_pubsub_topic" "dead_letter" {
  name                       = "${local.prefix}-dead-letter"
  message_retention_duration = "604800s"
  labels                     = local.labels
  depends_on                 = [google_project_service.required]
}
resource "google_pubsub_subscription" "dead_letter" {
  name                       = "${local.prefix}-dead-letter"
  topic                      = google_pubsub_topic.dead_letter.name
  message_retention_duration = "604800s"
  expiration_policy { ttl = "" }
}
resource "google_pubsub_subscription" "jobs" {
  name                       = "${local.prefix}-jobs"
  topic                      = google_pubsub_topic.jobs.name
  ack_deadline_seconds       = 180
  message_retention_duration = "86400s"
  expiration_policy { ttl = "" }
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
  push_config {
    push_endpoint = google_cloudfunctions2_function.service["worker"].service_config[0].uri
    oidc_token {
      service_account_email = google_service_account.push.email
      audience              = google_cloudfunctions2_function.service["worker"].service_config[0].uri
    }
  }
  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dead_letter.id
    max_delivery_attempts = 5
  }
  depends_on = [google_cloud_run_service_iam_member.push, google_service_account_iam_member.pubsub_token]
}
resource "google_project_service_identity" "pubsub" {
  provider   = google-beta
  project    = var.project_id
  service    = "pubsub.googleapis.com"
  depends_on = [google_project_service.required]
}
resource "google_service_account_iam_member" "pubsub_token" {
  service_account_id = google_service_account.push.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:${google_project_service_identity.pubsub.email}"
}
resource "google_pubsub_topic_iam_member" "dead_letter" {
  topic  = google_pubsub_topic.dead_letter.name
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:${google_project_service_identity.pubsub.email}"
}
resource "google_pubsub_subscription_iam_member" "dead_letter_source" {
  subscription = google_pubsub_subscription.jobs.name
  role         = "roles/pubsub.subscriber"
  member       = "serviceAccount:${google_project_service_identity.pubsub.email}"
}
resource "google_cloud_scheduler_job" "reconcile" {
  name             = "${local.prefix}-reconcile"
  region           = var.region
  schedule         = "* * * * *"
  time_zone        = "Etc/UTC"
  attempt_deadline = "120s"
  retry_config {
    retry_count          = 2
    min_backoff_duration = "30s"
    max_backoff_duration = "120s"
  }
  http_target {
    http_method = "POST"
    uri         = google_cloudfunctions2_function.service["reconcile"].service_config[0].uri
    oidc_token {
      service_account_email = google_service_account.scheduler.email
      audience              = google_cloudfunctions2_function.service["reconcile"].service_config[0].uri
    }
  }
  depends_on = [google_project_service.required, google_cloud_run_service_iam_member.scheduler]
}
