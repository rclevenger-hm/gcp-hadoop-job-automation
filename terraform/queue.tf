resource "google_pubsub_topic" "jobs" {
  name                       = "${local.prefix}-jobs"
  message_retention_duration = "86400s"
  labels                     = local.labels
  depends_on                 = [google_project_service.required]
}
