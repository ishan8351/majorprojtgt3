terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ==============================================================================
# 1. FOUNDATION NETWORK TIER (ROOT TOPOLOGY)
# ==============================================================================

resource "aws_vpc" "fintech_vpc" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name        = "fintech-core-clearing-vpc"
    Environment = var.environment
    Compliance  = "PCI-DSS-v4.0;DORA;SOC2"
    Tier        = "Foundation"
    ManagedBy   = "RegRadar"
  }
}

resource "aws_internet_gateway" "fintech_igw" {
  vpc_id = aws_vpc.fintech_vpc.id

  tags = {
    Name        = "fintech-clearing-igw"
    Environment = var.environment
    Compliance  = "PCI-DSS-v4.0"
  }
}

# Public Ingress Subnets (Dual AZ)
resource "aws_subnet" "public_a" {
  vpc_id            = aws_vpc.fintech_vpc.id
  cidr_block        = "10.50.1.0/24"
  availability_zone = "${var.aws_region}a"

  tags = {
    Name        = "fintech-public-ingress-a"
    Environment = var.environment
    Tier        = "Public"
  }
}

resource "aws_subnet" "public_b" {
  vpc_id            = aws_vpc.fintech_vpc.id
  cidr_block        = "10.50.2.0/24"
  availability_zone = "${var.aws_region}b"

  tags = {
    Name        = "fintech-public-ingress-b"
    Environment = var.environment
    Tier        = "Public"
  }
}

# Application Processing Subnets (Dual AZ Private)
resource "aws_subnet" "app_a" {
  vpc_id            = aws_vpc.fintech_vpc.id
  cidr_block        = "10.50.10.0/24"
  availability_zone = "${var.aws_region}a"

  tags = {
    Name        = "fintech-private-app-a"
    Environment = var.environment
    Tier        = "Application"
  }
}

resource "aws_subnet" "app_b" {
  vpc_id            = aws_vpc.fintech_vpc.id
  cidr_block        = "10.50.20.0/24"
  availability_zone = "${var.aws_region}b"

  tags = {
    Name        = "fintech-private-app-b"
    Environment = var.environment
    Tier        = "Application"
  }
}

# Isolated Database Subnets (Dual AZ Dedicated CDE)
resource "aws_subnet" "db_a" {
  vpc_id            = aws_vpc.fintech_vpc.id
  cidr_block        = "10.50.30.0/24"
  availability_zone = "${var.aws_region}a"

  tags = {
    Name        = "fintech-pci-database-a"
    Environment = var.environment
    Tier        = "Database"
    Compliance  = "PCI-DSS Cardholder Data Environment (CDE)"
  }
}

resource "aws_subnet" "db_b" {
  vpc_id            = aws_vpc.fintech_vpc.id
  cidr_block        = "10.50.40.0/24"
  availability_zone = "${var.aws_region}b"

  tags = {
    Name        = "fintech-pci-database-b"
    Environment = var.environment
    Tier        = "Database"
    Compliance  = "PCI-DSS Cardholder Data Environment (CDE)"
  }
}

resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.fintech_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.fintech_igw.id
  }

  tags = {
    Name = "fintech-public-rt"
  }
}

resource "aws_route_table_association" "public_a_assoc" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public_rt.id
}

resource "aws_route_table_association" "public_b_assoc" {
  subnet_id      = aws_subnet.public_b.id
  route_table_id = aws_route_table.public_rt.id
}

resource "aws_db_subnet_group" "fintech_db_subnets" {
  name       = "fintech-pci-db-subnet-group"
  subnet_ids = [aws_subnet.db_a.id, aws_subnet.db_b.id]

  tags = {
    Name        = "fintech-db-subnet-group"
    Environment = var.environment
  }
}

# ==============================================================================
# 2. PERIMETER & ZERO-TRUST SECURITY GROUPS
# ==============================================================================

# Statutory Smell 1 & 2:
# - CKV_AWS_24: Ingress from 0.0.0.0/0 on port 22 (SSH)
# - CKV_AWS_23: Security group missing description
resource "aws_security_group" "pci_ingress_sg" {
  name   = "fintech-payment-alb-sg"
  vpc_id = aws_vpc.fintech_vpc.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name       = "fintech-pci-ingress-sg"
    Compliance = "PCI-DSS Req 1.3"
  }
}

resource "aws_security_group" "app_tier_sg" {
  name        = "fintech-app-processing-sg"
  description = "Security group for internal financial transaction clearing microservices"
  vpc_id      = aws_vpc.fintech_vpc.id

  ingress {
    from_port       = 8443
    to_port         = 8443
    protocol        = "tcp"
    security_groups = [aws_security_group.pci_ingress_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "fintech-app-tier-sg"
  }
}

resource "aws_security_group" "db_tier_sg" {
  name        = "fintech-db-pci-sg"
  description = "Strict zero-trust database security group for PCI cardholder repository"
  vpc_id      = aws_vpc.fintech_vpc.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app_tier_sg.id]
  }

  tags = {
    Name = "fintech-db-tier-sg"
  }
}

# ==============================================================================
# 3. CRYPTOGRAPHIC KEY INFRASTRUCTURE (KMS CMK)
# ==============================================================================

resource "aws_kms_key" "fintech_ledger_cmk" {
  description             = "KMS Customer Managed Key for PCI-DSS transactional ledger & cardholder data"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    Name        = "fintech-ledger-cmk"
    Environment = var.environment
    Compliance  = "PCI-DSS v4.0 Req 3.5 / 3.6"
  }
}

resource "aws_kms_alias" "fintech_ledger_key_alias" {
  name          = "alias/fintech-payment-ledger"
  target_key_id = aws_kms_key.fintech_ledger_cmk.key_id
}

# ==============================================================================
# 4. STATEFUL TRANSACTION & SETTLEMENT DATABASE (RDS POSTGRESQL)
# ==============================================================================

# Statutory Smell 3:
# - CKV_AWS_16: Database storage encryption disabled (storage_encrypted = false)
resource "aws_db_instance" "settlement_db" {
  identifier             = "fintech-core-settlement-db"
  allocated_storage      = 100
  max_allocated_storage  = 500
  engine                 = "postgres"
  engine_version         = "15.4"
  instance_class         = "db.r6g.xlarge"
  db_name                = "settlementdb"
  username               = "pciadmin"
  password               = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.fintech_db_subnets.name
  vpc_security_group_ids = [aws_security_group.db_tier_sg.id]
  multi_az               = true
  skip_final_snapshot    = true
  storage_encrypted      = false

  tags = {
    Name        = "fintech-settlement-database"
    Environment = var.environment
    Compliance  = "PCI-DSS v4.0 Req 3.4"
  }
}

# ==============================================================================
# 5. IMMUTABLE CARDHOLDER STORAGE & TRANSACTION ARCHIVE (S3)
# ==============================================================================

# Statutory Smells 4 & 5:
# - CKV_AWS_19 / CKV_AWS_145: S3 bucket unencrypted / missing SSE-KMS
# - CKV_AWS_21: S3 bucket missing object versioning
resource "aws_s3_bucket" "cardholder_data_archive" {
  bucket = "fintech-cardholder-tokenized-vault-prod"

  tags = {
    Name        = "fintech-cardholder-archive"
    Environment = var.environment
    Compliance  = "PCI-DSS v4.0 Req 3.4;DORA Art 9"
    DataType    = "TokenizedPAN"
  }
}

resource "aws_s3_bucket" "settlement_audit_logs" {
  bucket = "fintech-settlement-audit-trail-prod"

  tags = {
    Name        = "fintech-settlement-audit-logs"
    Environment = var.environment
    Compliance  = "PCI-DSS v4.0 Req 10.2;SOC2 CC6.8"
  }
}

# ==============================================================================
# 6. STATUTORY TELEMETRY & AUDIT TRAIL (CLOUDTRAIL)
# ==============================================================================

# Statutory Smell 6:
# - CKV_AWS_36: CloudTrail trail missing KMS Master Key encryption
resource "aws_cloudtrail" "fintech_audit_trail" {
  name                          = "fintech-pci-audit-trail"
  s3_bucket_name                = aws_s3_bucket.settlement_audit_logs.id
  include_global_service_events = true
  is_multi_region_trail         = true
  enable_logging                = true

  tags = {
    Name        = "fintech-pci-cloudtrail"
    Compliance  = "PCI-DSS v4.0 Req 10.2.1 / 10.3"
    Environment = var.environment
  }
}

# ==============================================================================
# 7. IAM AUTHORIZATION & WORKER COMPUTE TIER
# ==============================================================================

# Statutory Smell 7:
# - CKV_AWS_40: Unconstrained IAM wildcard policy ("Action": "*")
resource "aws_iam_policy" "payment_worker_policy" {
  name        = "fintech-worker-execution-policy"
  description = "Execution role policy for payment clearing worker instances"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "*",
      "Resource": "*"
    }
  ]
}
EOF
}

resource "aws_iam_role" "payment_worker_role" {
  name = "fintech-payment-clearing-role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Effect": "Allow"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "payment_worker_attach" {
  role       = aws_iam_role.payment_worker_role.name
  policy_arn = aws_iam_policy.payment_worker_policy.arn
}

resource "aws_iam_instance_profile" "payment_worker_profile" {
  name = "fintech-payment-worker-profile"
  role = aws_iam_role.payment_worker_role.name
}

# Statutory Smell 8:
# - CKV_AWS_79: EC2 Instance missing IMDSv2 enforcement (metadata_options http_tokens)
resource "aws_instance" "payment_worker_a" {
  ami                  = "ami-0c55b159cbfafe1f0"
  instance_type        = "c6i.2xlarge"
  subnet_id            = aws_subnet.app_a.id
  iam_instance_profile = aws_iam_instance_profile.payment_worker_profile.name
  vpc_security_group_ids = [
    aws_security_group.app_tier_sg.id
  ]

  tags = {
    Name        = "fintech-payment-worker-a"
    Environment = var.environment
    Compliance  = "PCI-DSS v4.0;DORA Art 6"
  }
}
