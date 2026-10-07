resource "google_storage_bucket" "source" {
  name                        = "${var.project_id}-${local.prefix}-source"
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = false
  versioning { enabled = true }
  labels     = local.labels
  depends_on = [google_project_service.required]
}
data "archive_file" "source" {
  type        = "zip"
  source_dir  = "${path.module}/../artifacts"
  output_path = "${path.module}/../build/function-source.zip"
}
resource "google_storage_bucket_object" "source" {
  name   = "source-${data.archive_file.source.output_sha256}.zip"
  bucket = google_storage_bucket.source.name
  source = data.archive_file.source.output_path
}
