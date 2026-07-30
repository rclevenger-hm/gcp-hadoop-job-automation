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
