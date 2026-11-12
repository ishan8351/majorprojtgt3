"""
TDD Test Suite: FinTech Payment Clearing & Settlement Core Topology & Parsing.
Verifies that RegRadar's AST parser, reference extractor, and dependency graph builder
can accurately parse the complex multi-tier FinTech codebase and extract all resource
bindings without syntax errors or unresolvable references.
"""

from pathlib import Path
import pytest
from regradar.parser.hcl_parser import HCLParser
from regradar.graph.builder import DependencyGraphBuilder
from regradar.graph.centrality import CentralityEngine

TARGET_DIR = Path(__file__).parent.parent


def test_hcl_parser_discovers_all_fintech_resources():
    """Verify HCL parser parses the fintech payment codebase into valid AST structures."""
    parser = HCLParser()
    resources = parser.parse_directory(TARGET_DIR)
    
    assert len(resources) >= 15, f"Expected at least 15 resources in complex FinTech core, got {len(resources)}"
    
    resource_ids = set(resources.keys())
    # Verify core architectural tiers are represented
    assert "aws_vpc.fintech_vpc" in resource_ids, "Missing root VPC"
    assert "aws_subnet.public_a" in resource_ids, "Missing public subnet A"
    assert "aws_subnet.app_a" in resource_ids, "Missing app subnet A"
    assert "aws_subnet.db_a" in resource_ids, "Missing DB subnet A"
    assert "aws_security_group.pci_ingress_sg" in resource_ids, "Missing PCI Ingress SG"
    assert "aws_security_group.app_tier_sg" in resource_ids, "Missing App Tier SG"
    assert "aws_security_group.db_tier_sg" in resource_ids, "Missing DB Tier SG"
    assert "aws_kms_key.fintech_ledger_cmk" in resource_ids, "Missing KMS CMK"
    assert "aws_db_instance.settlement_db" in resource_ids, "Missing Settlement DB"
    assert "aws_s3_bucket.cardholder_data_archive" in resource_ids, "Missing Cardholder Data Archive S3"
    assert "aws_cloudtrail.fintech_audit_trail" in resource_ids, "Missing FinTech Audit Trail"
    assert "aws_instance.payment_worker_a" in resource_ids, "Missing Payment Worker EC2"


def test_fintech_dependency_dag_structure():
    """Verify that the dependency DAG correctly models the multi-tier hierarchy."""
    parser = HCLParser()
    resources = parser.parse_directory(TARGET_DIR)
    builder = DependencyGraphBuilder(resources)
    dag = builder.graph

    assert len(builder.find_cycles()) == 0, "Dependency graph must be a strict DAG without cyclical deadlocks"

    # Dependency edge direction: Dependency -> Dependent (e.g. VPC -> Subnet)
    assert dag.has_edge("aws_vpc.fintech_vpc", "aws_subnet.public_a"), "VPC must precede public subnet"
    assert dag.has_edge("aws_vpc.fintech_vpc", "aws_subnet.app_a"), "VPC must precede app subnet"
    assert dag.has_edge("aws_vpc.fintech_vpc", "aws_subnet.db_a"), "VPC must precede DB subnet"
    assert dag.has_edge("aws_vpc.fintech_vpc", "aws_security_group.pci_ingress_sg"), "VPC must precede ingress SG"
    
    # Subnet group depends on subnets
    assert dag.has_edge("aws_subnet.db_a", "aws_db_subnet_group.fintech_db_subnets") or \
           dag.has_edge("aws_subnet.db_b", "aws_db_subnet_group.fintech_db_subnets"), \
           "Subnet group must depend on DB subnets"

    # DB instance depends on DB subnet group and DB security group
    assert dag.has_edge("aws_security_group.db_tier_sg", "aws_db_instance.settlement_db"), \
           "Settlement DB must depend on DB Tier SG"

    # Worker instance depends on App Subnet and App SG
    assert dag.has_edge("aws_subnet.app_a", "aws_instance.payment_worker_a"), \
           "Worker instance must depend on App Subnet"
    assert dag.has_edge("aws_security_group.app_tier_sg", "aws_instance.payment_worker_a"), \
           "Worker instance must depend on App Tier SG"


def test_fintech_attribute_extraction_fidelity():
    """Verify detailed AST attribute extraction for key resources."""
    parser = HCLParser()
    resources = parser.parse_directory(TARGET_DIR)

    vpc = resources["aws_vpc.fintech_vpc"]
    assert "cidr_block" in vpc.attributes
    assert vpc.attributes["enable_dns_support"] is True
    assert vpc.attributes["enable_dns_hostnames"] is True

    db = resources["aws_db_instance.settlement_db"]
    assert str(db.attributes["engine"]).strip('"') == "postgres"
    assert db.attributes["multi_az"] is True
    assert db.attributes["storage_encrypted"] is False

    kms = resources["aws_kms_key.fintech_ledger_cmk"]
    assert kms.attributes["enable_key_rotation"] is True


def test_fintech_graph_export_formats():
    """Verify Mermaid flowchart and Graphviz DOT exports produce valid diagrams."""
    parser = HCLParser()
    resources = parser.parse_directory(TARGET_DIR)
    builder = DependencyGraphBuilder(resources)
    engine = CentralityEngine(builder.graph)

    mermaid_content = engine.to_mermaid()
    assert mermaid_content.startswith("```mermaid\nflowchart TD")
    assert "aws_vpc_fintech_vpc" in mermaid_content

    dot_content = engine.to_dot()
    assert "digraph" in dot_content
    assert "aws_vpc.fintech_vpc" in dot_content
