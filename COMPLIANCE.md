# FinTech Statutory Regulatory Compliance Specification

This document provides a detailed compliance crosswalk for the Payment Clearing & Settlement Core across three primary standards:
1. **PCI-DSS v4.0** (Payment Card Industry Data Security Standard)
2. **DORA** (EU Regulation 2022/2554 - Digital Operational Resilience Act)
3. **SOC 2 Type II** (AICPA Trust Services Criteria)

---

## 1. PCI-DSS v4.0 Statutory Audit Crosswalk

| PCI-DSS v4.0 Section | Requirement Title | Mandatory Technical Control | IaC Target Resource | Current Configuration State | RegRadar Governance Action |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Req 1.2** | Network Security Controls (NSCs) | All security groups must include an identifiable purpose and description. | `aws_security_group.pci_ingress_sg` | Missing description attribute (`CKV_AWS_23`) | **Remediated In-Place:** Synthesizes clear descriptive attribute. |
| **Req 1.3** | Restricted CDE Access | Direct public ingress from `0.0.0.0/0` on port 22 (SSH) is strictly prohibited. | `aws_security_group.pci_ingress_sg` | Ingress allows port 22 from `0.0.0.0/0` (`CKV_AWS_24`) | **Intermediate Blast-Radius Gate:** Gated for plan-diff verification. |
| **Req 3.4** | Render PAN Unreadable | Primary Account Numbers must be strongly encrypted at rest using AES-256 or KMS. | `aws_s3_bucket.cardholder_data_archive` | Default encryption block absent (`CKV_AWS_19` / `CKV_AWS_145`) | **Remediated Additively:** Injects standalone `aws_s3_bucket_server_side_encryption_configuration`. |
| **Req 3.5 / 3.6** | Cryptographic Key Protection | Keys must be customer-managed with documented lifecycle and annual rotation. | `aws_kms_key.fintech_ledger_cmk` | `enable_key_rotation = true` configured | **Compliant:** Verified active CMK rotation. |
| **Req 7.1** | Least Privilege Access | Authorization roles must restrict unconstrained wildcards (`*`). | `aws_iam_policy.payment_worker_policy` | Statement allows `Action: "*"` (`CKV_AWS_40`) | **Leaf-Safe Review:** Scoped to least privilege. |
| **Req 10.2** | Automated Audit Trails | Multi-region audit logging required with tamper-proof integrity and encryption. | `aws_cloudtrail.fintech_audit_trail` | Missing KMS encryption key (`CKV_AWS_36`) | **Remediated In-Place:** Attaches CMK key ARN. |
| **Req 10.2.1** | Audit Log Resilience | Audit storage must be protected against accidental deletion and tampering. | `aws_s3_bucket.settlement_audit_logs` | Missing bucket versioning (`CKV_AWS_21`) | **Remediated Additively:** Injects standalone `aws_s3_bucket_versioning` attachment. |

---

## 2. EU DORA (Regulation 2022/2554) Compliance Alignment

| DORA Article | Operational Mandate | IaC Implementation | Invariant Guarantee |
| :--- | :--- | :--- | :--- |
| **Article 6 (Risk Framework)** | Systems must ensure zero-interruption deployments and resilience against configuration crashes. | Multi-tier VPC with Dual-AZ redundancy across compute and database. | RegRadar dry-run sandbox prevents disruptive changes. |
| **Article 9 (Protection & Prevention)** | Comprehensive cryptographic protection of stored data and managed encryption keys. | AWS KMS Customer Managed Keys, S3 server-side encryption, and RDS storage encryption. | Additive encryption prevents bucket or database recreation. |
| **Article 10 (Detection of Anomalies)** | Continuous, immutable event logging across all infrastructure layers. | CloudTrail multi-region trail with CloudWatch integration and KMS envelope encryption. | Invariant engine prevents audit log deletion. |
| **Article 11 (Disaster Recovery)** | Continuous data availability with zero data loss recovery objectives. | S3 object versioning and RDS Multi-AZ failover configurations. | Protects recovery baselines from accidental removal. |

---

## 3. SOC 2 Type II Trust Services Criteria

| Criteria | Category | Control Description | Verification Status |
| :--- | :--- | :--- | :---: |
| **CC6.1** | Logical Access | Authorization limited through role-based access control and instance profiles. | Verified |
| **CC6.6** | Boundary Defense | Perimeter security groups restrict ingress to HTTPS :443; database isolated in private subnets. | Verified |
| **CC6.7** | Data Transmission | All network traffic forced through TLS encrypted protocols. | Verified |
| **CC6.8** | Unauthorized Code | Storage buckets protected against unauthorized object deletion via versioning and public access blocks. | Verified |
| **CC7.2** | System Monitoring | Multi-region audit trails capture all API activities and resource modifications. | Verified |
