terraform {
  required_providers {
    oci = {
      source = "oracle/oci"
    }
  }
}

provider "oci" {
  region           = var.region
}

provider "oci" {
  alias            = "home_region"
  region           = "us-ashburn-1"
}