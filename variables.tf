variable "aws_region" {
  type        = string
  description = "AWS region for payment clearing core deployment"
  default     = "us-east-1"
}

variable "environment" {
  type        = string
  description = "Deployment lifecycle stage"
  default     = "production"
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the core FinTech VPC"
  default     = "10.50.0.0/16"
}

variable "db_password" {
  type        = string
  description = "Master password for PostgreSQL settlement database"
  default     = "FintechSecureVault2026!#"
  sensitive   = true
}
