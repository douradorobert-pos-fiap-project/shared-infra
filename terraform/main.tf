terraform {
  required_version = ">= 1.9.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }

  backend "s3" {
    bucket       = "terraform-state-264040538379-us-east-1"
    key          = "sandbox/terraform.tfstate"
    region       = "us-east-1"
    use_lockfile = true
  }
}
