"""
TDD Test Suite: FinTech Compliance Audit & Statutory Smell Identification.
Verifies that RegRadar's CheckovScanner (with AST fallback) successfully detects
intentional compliance violations across PCI-DSS v4.0 and DORA standards in the
FinTech Payment Clearing & Settlement Core.
"""

from pathlib import Path
import pytest
from regradar.remediation.scanner import CheckovScanner
from regradar.knowledge.catalog import get_default_catalog

TARGET_DIR = Path(__file__).parent.parent


def test_fintech_compliance_violations_detected():
    """Verify that all intentional compliance violations are identified."""
    scanner = CheckovScanner()
    violations = scanner.scan_directory(TARGET_DIR)

    assert len(violations) >= 4, f"Expected at least 4 compliance violations in FinTech codebase, got {len(violations)}"

    check_ids = {v.check_id for v in violations}
    # Verify key PCI-DSS compliance checks
    assert "CKV_AWS_19" in check_ids or "CKV_AWS_145" in check_ids, "Should detect unencrypted S3 bucket"
    assert "CKV_AWS_21" in check_ids, "Should detect S3 bucket without object versioning"
    assert "CKV_AWS_24" in check_ids or "CKV_AWS_23" in check_ids, "Should detect permissive or undescribed security group"
    assert "CKV_AWS_16" in check_ids or "CKV_AWS_36" in check_ids or "CKV_AWS_40" in check_ids, \
        "Should detect database or CloudTrail or IAM violation"


def test_fintech_violation_framework_attribution():
    """Verify that discovered violations cite relevant regulatory frameworks (PCI-DSS, NIST, HIPAA, etc.)."""
    scanner = CheckovScanner()
    violations = scanner.scan_directory(TARGET_DIR)

    all_frameworks = []
    for v in violations:
        all_frameworks.extend(v.frameworks)

    framework_text = " ".join(all_frameworks)
    assert "PCI-DSS" in framework_text or "NIST" in framework_text or "GDPR" in framework_text or "HIPAA" in framework_text, \
        "Violations must map to recognized compliance standards"


def test_fintech_specific_resource_violations():
    """Verify exact resource attribution for candidate smells."""
    scanner = CheckovScanner()
    violations = scanner.scan_directory(TARGET_DIR)
    
    violation_map = {v.resource_id: v.check_id for v in violations}
    assert "aws_s3_bucket.cardholder_data_archive" in violation_map
    assert "aws_db_instance.settlement_db" in violation_map
    assert "aws_security_group.pci_ingress_sg" in violation_map


def test_fintech_custom_organizational_rule_discovery():
    """Verify that RegRadar dynamically discovers custom organizational rules."""
    stds, ctrls, reqs, res, rules = get_default_catalog()
    assert "CKV_FINTECH_01" in rules, "Custom rule CKV_FINTECH_01 must be dynamically loaded from rules/custom/"
    rule = rules["CKV_FINTECH_01"]
    assert rule.resource_type == "aws_s3_bucket"
    assert "PCI-DSS" in rule.framework
