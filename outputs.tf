output "vpc_id" {
  description = "Identifier of the primary FinTech clearing VPC"
  value       = aws_vpc.fintech_vpc.id
}

output "public_subnets" {
  description = "Identifiers of public ingress subnets"
  value       = [aws_subnet.public_a.id, aws_subnet.public_b.id]
}

output "app_subnets" {
  description = "Identifiers of private application subnets"
  value       = [aws_subnet.app_a.id, aws_subnet.app_b.id]
}

output "db_subnets" {
  description = "Identifiers of isolated PCI CDE database subnets"
  value       = [aws_subnet.db_a.id, aws_subnet.db_b.id]
}

output "settlement_db_endpoint" {
  description = "Connection endpoint for the core transaction database"
  value       = aws_db_instance.settlement_db.endpoint
}

output "cardholder_archive_bucket" {
  description = "S3 bucket name for tokenized cardholder data"
  value       = aws_s3_bucket.cardholder_data_archive.bucket
}

output "ledger_cmk_arn" {
  description = "ARN of the primary Customer Managed Key for the payment ledger"
  value       = aws_kms_key.fintech_ledger_cmk.arn
}
