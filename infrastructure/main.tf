terraform {
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
    dokku = {
      source  = "aliksend/dokku"
      version = "~> 1.0.24"
    }
  }

  backend "s3" {
    encrypt = true
  }
}

variable "domain" {
  description = "Domain (no www)"
}

variable "cloudflare_api_token" {
  description = "Cloudflare API token"
}

variable "hosting_domain" {
  description = "Hosting domain"
}

variable "secret_key" {
  description = "Django secret key"
}

variable "site_verb" {
  description = "The verb the site asks about"
  default     = "do"
}

variable "zoneid" {
  description = "Cloudflare zone ID"
}

provider "dokku" {
  ssh_host = var.hosting_domain
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}
