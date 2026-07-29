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
resource "google_project_iam_custom_role" "dataproc" {
  for_each = {
    api       = ["dataproc.jobs.get"]
    worker    = ["dataproc.jobs.create", "dataproc.jobs.get", "dataproc.clusters.use"]
    reconcile = ["dataproc.jobs.get", "dataproc.jobs.cancel"]
  }
  role_id     = "${replace(local.prefix, "-", "_")}_${each.key}"
  title       = "Hadoop ${each.key} Dataproc access"
  permissions = each.value
  depends_on  = [google_project_service.required]
}
resource "google_project_iam_member" "dataproc" {
  for_each = local.runtime_names
  project  = var.project_id
  role     = google_project_iam_custom_role.dataproc[each.key].name
  member   = "serviceAccount:${google_service_account.runtime[each.key].email}"
}
resource "google_project_iam_custom_role" "logs" {
  role_id     = "${replace(local.prefix, "-", "_")}_logs"
  title       = "Read admitted Hadoop driver objects"
  permissions = ["storage.objects.get"]
}
