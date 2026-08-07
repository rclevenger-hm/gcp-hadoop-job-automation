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
