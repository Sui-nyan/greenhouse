terraform {
  backend "http" {
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.16"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
    awscc = {
      source  = "hashicorp/awscc"
      version = ">= 0.5.0"
    }
  }
  required_version = ">= 1.2.0"
}

provider "aws" {
  region     = "eu-central-1"
  access_key = var.access_key
  secret_key = var.secret_key
}

provider "awscc" {
  region     = "eu-central-1"
  access_key = var.access_key
  secret_key = var.secret_key
}


locals {
  endpoint_path = "../client/certs/endpoint.txt"
}

data "aws_iot_endpoint" "current" {
  endpoint_type = "iot:Data-ATS"
}

resource "local_file" "endpoint" {
  content  = data.aws_iot_endpoint.current.endpoint_address
  filename = local.endpoint_path
}