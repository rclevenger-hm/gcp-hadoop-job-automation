resource "google_service_account" "runtime" {
  for_each     = local.runtime_names
  account_id   = "${local.prefix}-${each.key}"
  display_name = "Hadoop ${each.key} runtime"
}
resource "google_service_account" "build" { account_id = "${local.prefix}-build" }
resource "google_service_account" "push" { account_id = "${local.prefix}-push" }
resource "google_service_account" "scheduler" { account_id = "${local.prefix}-schedule" }
resource "google_project_iam_member" "database" {
  for_each = local.runtime_names
  project  = var.project_id
  role     = "roles/datastore.user"
  member   = "serviceAccount:${google_service_account.runtime[each.key].email}"
}
resource "google_project_iam_member" "build" {
  project = var.project_id
  role    = "roles/cloudbuild.builds.builder"
  member  = "serviceAccount:${google_service_account.build.email}"
}
resource "google_storage_bucket_iam_member" "build_source" {
  bucket = google_storage_bucket.source.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.build.email}"
}
