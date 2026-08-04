output "api_url" { value = local.api_url }
output "token_audience" { value = local.api_url }
output "database" { value = google_firestore_database.data.name }
output "job_topic" { value = google_pubsub_topic.jobs.id }
output "dead_letter_subscription" { value = google_pubsub_subscription.dead_letter.id }
