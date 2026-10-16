# Credentials come from the standard AWS chain (aws configure / env vars / SSO).
# Never put access keys in .tf or .tfvars files.
provider "aws" {
  region = var.region

  default_tags {
    tags = local.tags
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}
