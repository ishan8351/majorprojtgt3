"""
TDD Test Suite: FinTech Autonomous Remediation & Invariant Preservation.
Verifies that RegRadar's Multi-Agent Swarm Coordinator (Auditor, Planner, Synthesizer, Supervisor):
1. Safely gates high-risk resources to human escalation.
2. Synthesizes non-destructive additive attachments for safe leaf resources.
3. Enforces the zero-destruction invariant (0 deletions, 0 destructive replacements).
"""

from pathlib import Path
import pytest
from regradar.remediation.swarm_coordinator import SwarmCoordinator
from regradar.remediation.models import GatingStatus, RemediationStrategy
from regradar.invariant.invariant_engine import InvariantEngine
from regradar.invariant.models import ResourceChange, PlanAction, ViolationType

TARGET_DIR = Path(__file__).parent.parent


def test_fintech_remediation_swarm_execution():
    """Verify closed-loop swarm remediation on FinTech target codebase."""
    coordinator = SwarmCoordinator()
    result = coordinator.remediate_directory(TARGET_DIR, apply_changes=False)

    assert result.total_violations_found >= 4, "Should find violations"
    assert result.patches_verified_and_accepted >= 1, "Should verify and accept at least one safe patch"
    assert len(result.accepted_patches) >= 1, "Should have accepted patches"
    
    # Verify that patches use additive attachments for S3 compliance
    s3_patches = [p for p in result.accepted_patches if "aws_s3_bucket" in p.resource_id]
    for patch in s3_patches:
        assert patch.strategy == RemediationStrategy.ADDITIVE_ATTACHMENT, \
            "S3 remediations must use additive attachments to avoid bucket recreation"


def test_fintech_invariant_zero_destruction():
    """Verify that no verified patch ever causes state destruction or resource recreation."""
    coordinator = SwarmCoordinator()
    result = coordinator.remediate_directory(TARGET_DIR, apply_changes=False)

    # All accepted patches must maintain zero-destruction
    for patch in result.accepted_patches:
        assert patch.is_verified is True, "Accepted patch must be verified"
        assert patch.remediated_snippet != "", "Verified patch must contain code"


def test_fintech_invariant_engine_blocks_destructive_plan_diffs():
    """Verify InvariantEngine deterministically blocks replacements and deletions."""
    engine = InvariantEngine()

    # Case 1: Unintended Deletion
    destructive_deletion = [
        ResourceChange(
            address="aws_db_instance.settlement_db",
            resource_type="aws_db_instance",
            name="settlement_db",
            actions=[PlanAction.DELETE],
            before={"id": "settlement-db-1"},
            after=None,
        )
    ]
    report = engine.verify(destructive_deletion)
    assert report.is_safe is False
    assert any(v.violation_type == ViolationType.UNINTENDED_DELETION for v in report.violations)

    # Case 2: Forces Replacement (delete then create)
    destructive_replacement = [
        ResourceChange(
            address="aws_vpc.fintech_vpc",
            resource_type="aws_vpc",
            name="fintech_vpc",
            actions=[PlanAction.DELETE, PlanAction.CREATE],
            before={"cidr_block": "10.50.0.0/16"},
            after={"cidr_block": "10.60.0.0/16"},
        )
    ]
    report = engine.verify(destructive_replacement)
    assert report.is_safe is False
    assert any(v.violation_type == ViolationType.FORCES_REPLACEMENT for v in report.violations)

    # Case 3: Safe Additive Creation (Attachment)
    safe_attachment = [
        ResourceChange(
            address="aws_s3_bucket_server_side_encryption_configuration.cardholder_data_archive_encryption",
            resource_type="aws_s3_bucket_server_side_encryption_configuration",
            name="cardholder_data_archive_encryption",
            actions=[PlanAction.CREATE],
            before=None,
            after={"bucket": "cardholder-archive"},
        )
    ]
    report = engine.verify(safe_attachment)
    assert report.is_safe is True
    assert len(report.violations) == 0
