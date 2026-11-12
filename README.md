# FinTech Real-Time Payment Clearing & Settlement Core

Banking-grade multi-tier Infrastructure-as-Code (Terraform / OpenTofu) designed for high-throughput payment settlement, cardholder data processing, and statutory compliance under **PCI-DSS v4.0**, the **EU Digital Operational Resilience Act (DORA)**, and **SOC 2 Type II**.

This repository serves as a target infrastructure codebase for **RegRadar**, testing its Abstract Syntax Tree (AST) parsing, topological blast-radius risk bounding, zero-destruction invariant sandboxing, and autonomous compliance remediation.

---

## Architecture Overview

```
                                +---------------------------+
                                |  Internet / Payment Rails |
                                +-------------+-------------+
                                              |
                                              v (HTTPS :443)
                          +---------------------------------------+
                          |   PCI Ingress Security Group (DMZ)    |
                          +-------------------+-------------------+
                                              |
                       +----------------------+----------------------+
                       |                                             |
                       v                                             v
        +-----------------------------+               +-----------------------------+
        | Public Subnet A (us-east-1a)|               | Public Subnet B (us-east-1b)|
        |   - Payment Ingress ALB     |               |   - Payment Ingress ALB     |
        +--------------+--------------+               +--------------+--------------+
                       |                                             |
                       v                                             v
        +-----------------------------+               +-----------------------------+
        |  App Subnet A (us-east-1a)  |               |  App Subnet B (us-east-1b)  |
        |   - Payment Worker A (c6i)  |               |   - Processing Microservices|
        +--------------+--------------+               +--------------+--------------+
                       |                                             |
                       +----------------------+----------------------+
                                              |
                                              v (:5432)
                       +---------------------------------------------+
                       |  Database Subnets (Dedicated PCI CDE Tier)  |
                       |    - Multi-AZ RDS PostgreSQL Instance       |
                       |    - Storage Encrypted (KMS Envelope)       |
                       +----------------------+----------------------+
                                              |
                       +----------------------+----------------------+
                       |                                             |
                       v                                             v
        +-----------------------------+               +-----------------------------+
        |  KMS Primary Ledger CMK     |               |  Tokenized S3 Vault         |
        |   - Annual Key Rotation     |               |   - SSE-KMS Default Encr.   |
        |   - Dedicated Alias         |               |   - Object Versioning (WORM)|
        +-----------------------------+               +-----------------------------+
```

---

## Topological Risk Stratification

RegRadar parses the 26 declarative resources and 30 dependency bindings into a Directed Acyclic Graph (DAG), computing composite risk scores based on betweenness centrality and cascading descendant ratios:

| Risk Tier | Representative Components | Centrality / Blast Radius | Remediation Policy |
| :--- | :--- | :---: | :--- |
| **`CRITICAL_ROOT`** | `aws_vpc.fintech_vpc` | 16 downstream nodes ($S \ge 0.30$) | **Human Review Gated:** Automated AI mutations strictly locked out. |
| **`INTERMEDIATE`** | `aws_subnet.*`, `aws_security_group.*`, `aws_db_subnet_group.*` | 1 to 4 downstream nodes | **Gated Dry-Run:** Invariant plan diff verification required. |
| **`LEAF_SAFE`** | `aws_s3_bucket.*`, `aws_kms_alias.*`, `aws_cloudtrail.*`, `aws_instance.*` | 0 downstream nodes ($S < 0.10$) | **Autonomous Eligible:** Multi-agent swarm synthesizes safe HCL fixes. |

---

## Statutory Compliance Framework Matrix

This codebase intentionally incorporates statutory compliance smells to test automated detection and remediation:

| Regulation | Statute Reference | Checkov Check | Target Resource | Severity | Remediated By |
| :--- | :--- | :---: | :--- | :---: | :--- |
| **PCI-DSS v4.0** | Req 3.4 (Data at Rest) | `CKV_AWS_19` / `CKV_AWS_145` | `aws_s3_bucket.cardholder_data_archive` | HIGH | RegRadar Additive Attachment |
| **PCI-DSS v4.0** | Req 10.2 (Audit Logs) | `CKV_AWS_21` | `aws_s3_bucket.settlement_audit_logs` | MEDIUM | RegRadar Additive Attachment |
| **PCI-DSS v4.0** | Req 1.3 (Perimeter) | `CKV_AWS_24` | `aws_security_group.pci_ingress_sg` | HIGH | Human Escalation (Intermediate) |
| **DORA** | Art 9 (Cryptographic Key) | `CKV_AWS_36` | `aws_cloudtrail.fintech_audit_trail` | HIGH | RegRadar In-Place Attribute |
| **SOC 2 Type II** | CC6.1 (Least Privilege) | `CKV_AWS_40` | `aws_iam_policy.payment_worker_policy` | CRITICAL | Gated Human Review |
| **NIST SP 800-53** | SC-13 (DB Encryption) | `CKV_AWS_16` | `aws_db_instance.settlement_db` | CRITICAL | Invariant Gated (Outage Prevented) |

---

## Test-Driven Development (TDD) Verification

The repository contains an automated test suite verifying topology, centrality stratification, compliance detection, and invariant safety:

```bash
# Run full TDD test suite
PYTHONPATH=../majorproject pytest -v tests/

# Execute topological blast-radius scan
PYTHONPATH=../majorproject python -m regradar.cli scan .

# Run autonomous multi-agent remediation
PYTHONPATH=../majorproject python -m regradar.cli remediate .

# Run empirical governance benchmark
PYTHONPATH=../majorproject python -m regradar.cli benchmark .
```
