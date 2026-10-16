terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.95"
    }
  }

  # Local state by default. For a team, store state remotely, e.g.:
  # backend "s3" {
  #   bucket       = "my-tfstate-bucket"
  #   key          = "stockpilot/terraform.tfstate"
  #   region       = "ap-south-1"
  #   use_lockfile = true
  # }
}
