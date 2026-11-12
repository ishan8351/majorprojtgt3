"""
TDD Test Suite: FinTech Blast-Radius & Network Centrality Evaluation.
Verifies that RegRadar's CentralityEngine calculates betweenness centrality,
cascading descendant ratios, and correctly stratifies the FinTech infrastructure
into CRITICAL_ROOT, INTERMEDIATE, and LEAF_SAFE risk tiers.
"""

from pathlib import Path
import pytest
from regradar.parser.hcl_parser import HCLParser
from regradar.graph.builder import DependencyGraphBuilder
from regradar.graph.centrality import CentralityEngine
from regradar.models import RiskTier

TARGET_DIR = Path(__file__).parent.parent


def test_fintech_centrality_risk_tiers():
    """Verify that foundational resources are gated as CRITICAL_ROOT and leaves as LEAF_SAFE."""
    parser = HCLParser()
    resources = parser.parse_directory(TARGET_DIR)
    builder = DependencyGraphBuilder(resources)
    engine = CentralityEngine(builder.graph)
    summary = engine.get_summary()

    metrics = summary.metrics
    assert "aws_vpc.fintech_vpc" in metrics
    
    vpc_metric = metrics["aws_vpc.fintech_vpc"]
    # VPC has massive fanout and cascading descendants
    assert vpc_metric.descendant_count >= 8, f"VPC descendant count was {vpc_metric.descendant_count}, expected >= 8"
    assert vpc_metric.risk_tier == RiskTier.CRITICAL_ROOT, "VPC must be classified as CRITICAL_ROOT"
    assert vpc_metric.auto_remediate is False, "CRITICAL_ROOT VPC must NEVER be auto-remediated"

    # Leaf nodes should be LEAF_SAFE
    leaf_nodes = [m for m in metrics.values() if m.descendant_count == 0]
    assert len(leaf_nodes) > 0, "Expected at least one leaf node in topology"
    for leaf in leaf_nodes:
        assert leaf.risk_tier in [RiskTier.LEAF_SAFE, RiskTier.INTERMEDIATE]


def test_fintech_centrality_descendant_propagation():
    """Verify cascading impact calculation: downstream failure cascades."""
    parser = HCLParser()
    resources = parser.parse_directory(TARGET_DIR)
    builder = DependencyGraphBuilder(resources)
    engine = CentralityEngine(builder.graph)
    summary = engine.get_summary()
    
    # DB Subnet Group sits between Subnets and RDS DB
    assert "aws_db_subnet_group.fintech_db_subnets" in summary.metrics
    db_sg_metric = summary.metrics["aws_db_subnet_group.fintech_db_subnets"]
    assert db_sg_metric.descendant_count >= 1, "DB subnet group must have at least the DB instance as descendant"


def test_fintech_composite_risk_score_bounds():
    """Verify composite blast-radius scores obey mathematical bounds [0.0, 1.0]."""
    parser = HCLParser()
    resources = parser.parse_directory(TARGET_DIR)
    builder = DependencyGraphBuilder(resources)
    engine = CentralityEngine(builder.graph)
    summary = engine.get_summary()

    for node_id, metric in summary.metrics.items():
        assert 0.0 <= metric.blast_radius_score <= 1.0, f"Score out of bounds for {node_id}: {metric.blast_radius_score}"
        assert 0.0 <= metric.betweenness <= 1.0, f"Betweenness out of bounds for {node_id}: {metric.betweenness}"
        assert metric.descendant_count >= 0
        assert metric.in_degree >= 0
        assert metric.out_degree >= 0


def test_fintech_eigenvector_and_pagerank_metrics():
    """Verify eigenvector centrality and PageRank metrics are computed for all nodes."""
    parser = HCLParser()
    resources = parser.parse_directory(TARGET_DIR)
    builder = DependencyGraphBuilder(resources)
    engine = CentralityEngine(builder.graph)
    summary = engine.get_summary()

    for node_id, metric in summary.metrics.items():
        assert hasattr(metric, "eigenvector")
        assert hasattr(metric, "pagerank")
        assert metric.eigenvector >= 0.0
        assert metric.pagerank >= 0.0
