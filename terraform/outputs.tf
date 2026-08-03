output "api_url" { value = local.api_url }
output "token_audience" { value = local.api_url }
output "database" { value = google_firestore_database.data.name }
