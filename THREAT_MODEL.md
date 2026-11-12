# FinTech Payment Clearing Core Threat Model (STRIDE)

This document presents a structured STRIDE threat analysis for the Payment Clearing & Settlement Core infrastructure.

---

## 1. STRIDE Analysis Matrix

| Threat Category | Threat Scenario | Impact Level | Architectural Mitigation | RegRadar Invariant Defense |
| :--- | :--- | :---: | :--- | :--- |
| **Spoofing (S)** | Attacker spoofs an EC2 instance identity or steals temporary instance credentials via SSRF. | CRITICAL | EC2 IMDSv2 enforcement (`http_tokens = "required"`). | `CKV_AWS_79` enforced on `aws_instance.payment_worker_a`. |
| **Tampering (T)** | Malicious or accidental modification of payment audit logs or cardholder token vault. | HIGH | S3 Object Versioning + KMS encryption with annual key rotation. | Additive `aws_s3_bucket_versioning` and `aws_kms_key` rotation enforced. |
| **Repudiation (R)** | Rogue administrator alters transaction records without leaving an identifiable trail. | HIGH | Multi-region AWS CloudTrail logging with KMS envelope encryption. | `CKV_AWS_36` enforced on `aws_cloudtrail.fintech_audit_trail`. |
| **Information Disclosure (I)** | Unencrypted S3 bucket exposed publicly or cardholder data intercepted in transit. | CRITICAL | S3 default SSE-KMS encryption + Public Access Block + TLS-only ALB. | Additive `aws_s3_bucket_server_side_encryption_configuration` attached without modifying base bucket. |
| **Denial of Service (D)** | Cascading deletion of root VPC or database subnet group caused by unvalidated AI patch. | CATASTROPHIC | Topological blast-radius risk gating + Ephemeral plan diff verification. | `aws_vpc.fintech_vpc` gated as `CRITICAL_ROOT`; 0 deletions allowed. |
| **Elevation of Privilege (E)** | Compromised worker node leverages wildcard IAM policy to assume full administrator privileges. | CRITICAL | Least privilege IAM policy removing unconstrained `Action: "*"`. | `CKV_AWS_40` detected and flagged for least-privilege scoping. |

---

## 2. Attack Surface Reduction Walkthrough

1. **Direct Database Exposure:**
   * *Risk:* Direct SQL injection or brute force against port 5432 from public internet.
   * *Mitigation:* Isolated `aws_subnet.db_a` and `aws_subnet.db_b` have no route to IGW or NAT; `db_tier_sg` accepts traffic strictly from `app_tier_sg`.

2. **Automated LLM Outage Injection:**
   * *Risk:* An unconstrained generative AI agent modifies an immutable attribute (e.g. database `identifier` or VPC `cidr_block`), forcing complete recreation of live state.
   * *Mitigation:* RegRadar evaluates the execution graph (`tofu show -json`). Any plan containing `["delete", "create"]` is deterministically blocked.
