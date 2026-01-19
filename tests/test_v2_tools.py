"""
Unit tests for V2 Tools Module

Tests:
- FactStore: add_fact, add_gap, merge, save/load, format_for_reasoning
- discovery_tools: execute_discovery_tool
- reasoning_tools: ReasoningStore, execute_reasoning_tool

Run with: pytest tests/test_v2_tools.py -v
"""

import pytest
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools_v2.fact_store import FactStore, Fact, Gap, DOMAIN_PREFIXES
from tools_v2.discovery_tools import (
    DISCOVERY_TOOLS,
    execute_discovery_tool,
    validate_discovery_input,
    ALL_DOMAINS
)
from tools_v2.reasoning_tools import (
    REASONING_TOOLS,
    execute_reasoning_tool,
    ReasoningStore,
    Risk,
    StrategicConsideration,
    WorkItem,
    Recommendation
)


# =============================================================================
# FACT STORE TESTS
# =============================================================================

class TestFactStore:
    """Tests for FactStore functionality."""

    def test_create_empty_store(self):
        """Test creating an empty FactStore."""
        store = FactStore()
        assert store.facts == []
        assert store.gaps == []
        assert len(store._fact_counters) == 0
        assert len(store._gap_counters) == 0

    def test_add_fact_returns_id(self):
        """Test that add_fact returns a unique ID."""
        store = FactStore()

        fact_id = store.add_fact(
            domain="infrastructure",
            category="compute",
            item="VMware Environment",
            details={"platform": "VMware", "version": "6.7"},
            status="documented",
            evidence={"exact_quote": "VMware vSphere 6.7 environment"}
        )

        assert fact_id == "F-INFRA-001"
        assert len(store.facts) == 1

    def test_add_fact_increments_counter(self):
        """Test that fact IDs increment correctly."""
        store = FactStore()

        id1 = store.add_fact(
            domain="infrastructure",
            category="compute",
            item="VMware",
            details={},
            status="documented",
            evidence={"exact_quote": "VMware environment"}
        )
        id2 = store.add_fact(
            domain="infrastructure",
            category="storage",
            item="NetApp",
            details={},
            status="documented",
            evidence={"exact_quote": "NetApp storage"}
        )
        id3 = store.add_fact(
            domain="network",
            category="wan",
            item="MPLS",
            details={},
            status="documented",
            evidence={"exact_quote": "MPLS network"}
        )

        assert id1 == "F-INFRA-001"
        assert id2 == "F-INFRA-002"
        assert id3 == "F-NET-001"  # Different domain, new counter

    def test_add_gap_returns_id(self):
        """Test that add_gap returns a unique ID."""
        store = FactStore()

        gap_id = store.add_gap(
            domain="infrastructure",
            category="backup_dr",
            description="No DR RTO/RPO defined",
            importance="high"
        )

        assert gap_id == "G-INFRA-001"
        assert len(store.gaps) == 1

    def test_get_fact_by_id(self):
        """Test retrieving a fact by ID."""
        store = FactStore()

        store.add_fact(
            domain="infrastructure",
            category="compute",
            item="VMware",
            details={"version": "7.0"},
            status="documented",
            evidence={"exact_quote": "VMware 7.0"}
        )

        fact = store.get_fact("F-INFRA-001")
        assert fact is not None
        assert fact.item == "VMware"
        assert fact.details["version"] == "7.0"

    def test_get_fact_returns_none_for_invalid_id(self):
        """Test that get_fact returns None for non-existent ID."""
        store = FactStore()
        fact = store.get_fact("F-INFRA-999")
        assert fact is None

    def test_get_domain_facts(self):
        """Test getting all facts for a domain."""
        store = FactStore()

        # Add facts to different domains
        store.add_fact(
            domain="infrastructure",
            category="compute",
            item="VMware",
            details={},
            status="documented",
            evidence={"exact_quote": "VMware"}
        )
        store.add_fact(
            domain="infrastructure",
            category="storage",
            item="NetApp",
            details={},
            status="documented",
            evidence={"exact_quote": "NetApp"}
        )
        store.add_fact(
            domain="network",
            category="wan",
            item="MPLS",
            details={},
            status="documented",
            evidence={"exact_quote": "MPLS"}
        )
        store.add_gap(
            domain="infrastructure",
            category="backup_dr",
            description="DR not documented",
            importance="high"
        )

        domain_data = store.get_domain_facts("infrastructure")

        assert domain_data["domain"] == "infrastructure"
        assert domain_data["fact_count"] == 2
        assert domain_data["gap_count"] == 1
        assert len(domain_data["categories"]) == 2
        assert "compute" in domain_data["categories"]
        assert "storage" in domain_data["categories"]

    def test_validate_fact_citations(self):
        """Test validating fact ID citations."""
        store = FactStore()

        store.add_fact(
            domain="infrastructure",
            category="compute",
            item="VMware",
            details={},
            status="documented",
            evidence={"exact_quote": "VMware"}
        )
        store.add_fact(
            domain="infrastructure",
            category="storage",
            item="NetApp",
            details={},
            status="documented",
            evidence={"exact_quote": "NetApp"}
        )

        result = store.validate_fact_citations([
            "F-INFRA-001",
            "F-INFRA-002",
            "F-INFRA-999"  # Invalid
        ])

        assert len(result["valid"]) == 2
        assert len(result["invalid"]) == 1
        assert "F-INFRA-999" in result["invalid"]
        assert result["validation_rate"] == pytest.approx(2/3, rel=0.01)

    def test_merge_from_other_store(self):
        """Test merging facts from another store."""
        store1 = FactStore()
        store2 = FactStore()

        store1.add_fact(
            domain="infrastructure",
            category="compute",
            item="VMware",
            details={},
            status="documented",
            evidence={"exact_quote": "VMware"}
        )

        store2.add_fact(
            domain="network",
            category="wan",
            item="MPLS",
            details={},
            status="documented",
            evidence={"exact_quote": "MPLS"}
        )
        store2.add_gap(
            domain="network",
            category="security",
            description="Firewall rules not documented",
            importance="medium"
        )

        counts = store1.merge_from(store2)

        assert counts["facts"] == 1
        assert counts["gaps"] == 1
        assert len(store1.facts) == 2
        assert len(store1.gaps) == 1
        # Merged facts get new IDs
        assert store1.facts[1].fact_id == "F-NET-001"

    def test_save_and_load(self):
        """Test saving and loading FactStore to JSON."""
        store = FactStore()

        store.add_fact(
            domain="infrastructure",
            category="compute",
            item="VMware",
            details={"version": "7.0", "vm_count": 150},
            status="documented",
            evidence={"exact_quote": "VMware 7.0 with 150 VMs"}
        )
        store.add_gap(
            domain="infrastructure",
            category="backup_dr",
            description="No DR testing schedule",
            importance="high"
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            store.save(temp_path)

            # Load into new store
            loaded_store = FactStore.load(temp_path)

            assert len(loaded_store.facts) == 1
            assert len(loaded_store.gaps) == 1
            assert loaded_store.facts[0].item == "VMware"
            assert loaded_store.facts[0].details["version"] == "7.0"
            assert loaded_store.gaps[0].description == "No DR testing schedule"

            # Counter should continue from loaded IDs
            new_id = loaded_store.add_fact(
                domain="infrastructure",
                category="storage",
                item="NetApp",
                details={},
                status="documented",
                evidence={"exact_quote": "NetApp storage"}
            )
            assert new_id == "F-INFRA-002"  # Continues from 001

        finally:
            Path(temp_path).unlink()

    def test_format_for_reasoning(self):
        """Test formatting facts for reasoning agent prompt."""
        store = FactStore()

        store.add_fact(
            domain="infrastructure",
            category="compute",
            item="VMware Environment",
            details={"platform": "VMware", "version": "6.7"},
            status="documented",
            evidence={"exact_quote": "VMware vSphere 6.7 environment"}
        )
        store.add_gap(
            domain="infrastructure",
            category="backup_dr",
            description="No DR RTO/RPO defined",
            importance="high"
        )

        formatted = store.format_for_reasoning("infrastructure")

        assert "INFRASTRUCTURE INVENTORY" in formatted
        assert "F-INFRA-001" in formatted
        assert "VMware Environment" in formatted
        assert "IDENTIFIED GAPS" in formatted
        assert "G-INFRA-001" in formatted

    def test_mark_discovery_complete(self):
        """Test marking discovery complete for a domain."""
        store = FactStore()

        store.mark_discovery_complete(
            domain="infrastructure",
            categories_covered=["compute", "storage"],
            categories_missing=["legacy"]
        )

        assert "infrastructure" in store.discovery_complete
        assert store.discovery_complete["infrastructure"]["complete"] is True
        assert "compute" in store.discovery_complete["infrastructure"]["categories_covered"]

    def test_domain_prefixes(self):
        """Test that all expected domain prefixes exist."""
        expected_domains = [
            "infrastructure", "network", "cybersecurity",
            "applications", "identity_access", "organization"
        ]

        for domain in expected_domains:
            assert domain in DOMAIN_PREFIXES or domain == "general"

    def test_verify_fact(self):
        """Test verifying a fact."""
        store = FactStore()
        fact_id = store.add_fact(
            domain="infrastructure",
            category="compute",
            item="VMware",
            details={},
            status="documented",
            evidence={"exact_quote": "VMware vSphere 6.7"},
            entity="target"
        )

        # Fact should start unverified
        fact = store.get_fact(fact_id)
        assert fact.verified is False
        assert fact.verified_by is None

        # Verify the fact
        result = store.verify_fact(fact_id, "reviewer@example.com")
        assert result is True

        # Check it's now verified
        fact = store.get_fact(fact_id)
        assert fact.verified is True
        assert fact.verified_by == "reviewer@example.com"
        assert fact.verified_at is not None

    def test_verification_stats(self):
        """Test verification statistics."""
        store = FactStore()

        # Add some facts
        id1 = store.add_fact(
            domain="infrastructure", category="compute", item="VMware",
            details={}, status="documented", evidence={"exact_quote": "q"}, entity="target"
        )
        id2 = store.add_fact(
            domain="infrastructure", category="storage", item="NetApp",
            details={}, status="documented", evidence={"exact_quote": "q"}, entity="target"
        )
        id3 = store.add_fact(
            domain="network", category="firewall", item="Palo Alto",
            details={}, status="documented", evidence={"exact_quote": "q"}, entity="target"
        )

        # Verify one
        store.verify_fact(id1, "tester")

        stats = store.get_verification_stats()
        assert stats["total_facts"] == 3
        assert stats["verified_count"] == 1
        assert stats["unverified_count"] == 2
        assert stats["verification_rate"] == 1/3

    def test_bulk_verify(self):
        """Test bulk verification."""
        store = FactStore()

        ids = []
        for i in range(5):
            fact_id = store.add_fact(
                domain="infrastructure", category="compute", item=f"Server{i}",
                details={}, status="documented", evidence={"exact_quote": "q"}, entity="target"
            )
            ids.append(fact_id)

        # Bulk verify first 3
        results = store.bulk_verify(ids[:3], "bulk_reviewer")
        assert results["verified"] == 3
        assert results["not_found"] == 0

        # Check stats
        stats = store.get_verification_stats()
        assert stats["verified_count"] == 3
        assert stats["unverified_count"] == 2


# =============================================================================
# DISCOVERY TOOLS TESTS
# =============================================================================

class TestDiscoveryTools:
    """Tests for discovery tools execution."""

    def test_discovery_tools_structure(self):
        """Test that discovery tools have correct structure."""
        tool_names = [t["name"] for t in DISCOVERY_TOOLS]

        assert "create_inventory_entry" in tool_names
        assert "flag_gap" in tool_names
        assert "complete_discovery" in tool_names

        # Check each tool has required fields
        for tool in DISCOVERY_TOOLS:
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool

    def test_execute_create_inventory_entry(self):
        """Test executing create_inventory_entry tool."""
        store = FactStore()

        result = execute_discovery_tool(
            tool_name="create_inventory_entry",
            tool_input={
                "domain": "infrastructure",
                "category": "compute",
                "item": "VMware Environment",
                "details": {"version": "7.0"},
                "status": "documented",
                "evidence": {"exact_quote": "VMware vSphere 7.0 cluster"}
            },
            fact_store=store
        )

        assert result["status"] == "success"
        assert "fact_id" in result
        assert result["fact_id"] == "F-INFRA-001"
        assert len(store.facts) == 1

    def test_execute_create_inventory_entry_missing_fields(self):
        """Test create_inventory_entry fails with missing required fields."""
        store = FactStore()

        result = execute_discovery_tool(
            tool_name="create_inventory_entry",
            tool_input={
                "domain": "infrastructure",
                # Missing category, item
                "status": "documented",
                "evidence": {"exact_quote": "test"}
            },
            fact_store=store
        )

        assert result["status"] == "error"
        assert "Missing required fields" in result["message"]

    def test_execute_create_inventory_entry_short_quote(self):
        """Test create_inventory_entry fails with too short quote."""
        store = FactStore()

        result = execute_discovery_tool(
            tool_name="create_inventory_entry",
            tool_input={
                "domain": "infrastructure",
                "category": "compute",
                "item": "VMware",
                "status": "documented",
                "evidence": {"exact_quote": "VM"}  # Too short
            },
            fact_store=store
        )

        assert result["status"] == "error"
        assert "at least 10 characters" in result["message"]

    def test_execute_flag_gap(self):
        """Test executing flag_gap tool."""
        store = FactStore()

        result = execute_discovery_tool(
            tool_name="flag_gap",
            tool_input={
                "domain": "infrastructure",
                "category": "backup_dr",
                "description": "No DR RTO/RPO values documented",
                "importance": "high"
            },
            fact_store=store
        )

        assert result["status"] == "success"
        assert "gap_id" in result
        assert result["gap_id"] == "G-INFRA-001"
        assert len(store.gaps) == 1

    def test_execute_complete_discovery(self):
        """Test executing complete_discovery tool."""
        store = FactStore()

        # Add some facts first
        store.add_fact(
            domain="infrastructure",
            category="compute",
            item="VMware",
            details={},
            status="documented",
            evidence={"exact_quote": "VMware environment"}
        )

        result = execute_discovery_tool(
            tool_name="complete_discovery",
            tool_input={
                "domain": "infrastructure",
                "categories_covered": ["compute", "storage"],
                "categories_missing": ["legacy"],
                "summary": "Infrastructure discovery complete"
            },
            fact_store=store
        )

        assert result["status"] == "success"
        assert result["fact_count"] == 1
        assert "infrastructure" in store.discovery_complete

    def test_execute_unknown_tool(self):
        """Test executing unknown tool returns error."""
        store = FactStore()

        result = execute_discovery_tool(
            tool_name="unknown_tool",
            tool_input={},
            fact_store=store
        )

        assert result["status"] == "error"
        assert "Unknown discovery tool" in result["message"]

    def test_validate_discovery_input_valid(self):
        """Test validation passes for valid input."""
        error = validate_discovery_input(
            "create_inventory_entry",
            {
                "domain": "infrastructure",
                "category": "compute",
                "item": "VMware",
                "entity": "target",  # Required field
                "status": "documented",
                "evidence": {"exact_quote": "VMware environment"}
            }
        )
        assert error is None

    def test_validate_discovery_input_missing_field(self):
        """Test validation catches missing fields."""
        error = validate_discovery_input(
            "create_inventory_entry",
            {
                "domain": "infrastructure",
                # Missing category, item, status, evidence
            }
        )
        assert error is not None
        assert "Missing required field" in error

    def test_duplicate_fact_detection_exact_match(self):
        """Test that exact duplicate facts are detected."""
        store = FactStore()

        # Add first fact
        result1 = execute_discovery_tool(
            "create_inventory_entry",
            {
                "domain": "infrastructure",
                "category": "compute",
                "item": "VMware vSphere",
                "status": "documented",
                "evidence": {"exact_quote": "VMware vSphere 6.7"}
            },
            store
        )
        assert result1["status"] == "success"

        # Try to add exact duplicate
        result2 = execute_discovery_tool(
            "create_inventory_entry",
            {
                "domain": "infrastructure",
                "category": "compute",
                "item": "VMware vSphere",  # Exact same item
                "status": "documented",
                "evidence": {"exact_quote": "Different quote"}
            },
            store
        )
        assert result2["status"] == "duplicate"
        assert result2["fact_id"] == result1["fact_id"]

    def test_duplicate_fact_detection_fuzzy_match(self):
        """Test that similar facts are detected as duplicates."""
        store = FactStore()

        # Add first fact
        result1 = execute_discovery_tool(
            "create_inventory_entry",
            {
                "domain": "infrastructure",
                "category": "compute",
                "item": "VMware vSphere Environment",
                "status": "documented",
                "evidence": {"exact_quote": "VMware vSphere 6.7 environment"}
            },
            store
        )
        assert result1["status"] == "success"

        # Try to add similar fact (should trigger fuzzy match)
        result2 = execute_discovery_tool(
            "create_inventory_entry",
            {
                "domain": "infrastructure",
                "category": "compute",
                "item": "VMware vSphere Environments",  # Slightly different
                "status": "documented",
                "evidence": {"exact_quote": "Different evidence"}
            },
            store
        )
        assert result2["status"] == "duplicate"

    def test_duplicate_gap_detection(self):
        """Test that duplicate gaps are detected."""
        store = FactStore()

        # Add first gap
        result1 = execute_discovery_tool(
            "flag_gap",
            {
                "domain": "infrastructure",
                "category": "backup_dr",
                "description": "No DR RTO/RPO defined",
                "importance": "high"
            },
            store
        )
        assert result1["status"] == "success"

        # Try to add duplicate gap
        result2 = execute_discovery_tool(
            "flag_gap",
            {
                "domain": "infrastructure",
                "category": "backup_dr",
                "description": "No DR RTO/RPO defined",  # Exact same
                "importance": "critical"
            },
            store
        )
        assert result2["status"] == "duplicate"
        assert result2["gap_id"] == result1["gap_id"]

    def test_different_domain_not_duplicate(self):
        """Test that same item in different domain is not a duplicate."""
        store = FactStore()

        # Add fact in infrastructure
        result1 = execute_discovery_tool(
            "create_inventory_entry",
            {
                "domain": "infrastructure",
                "category": "compute",
                "item": "Windows Server",
                "status": "documented",
                "evidence": {"exact_quote": "Windows Server 2019"}
            },
            store
        )
        assert result1["status"] == "success"

        # Add same item name in different domain (should NOT be duplicate)
        result2 = execute_discovery_tool(
            "create_inventory_entry",
            {
                "domain": "applications",
                "category": "erp",
                "item": "Windows Server",
                "status": "documented",
                "evidence": {"exact_quote": "Windows Server hosting ERP"}
            },
            store
        )
        assert result2["status"] == "success"
        assert result2["fact_id"] != result1["fact_id"]


# =============================================================================
# REASONING STORE TESTS
# =============================================================================

class TestReasoningStore:
    """Tests for ReasoningStore functionality."""

    def test_create_empty_store(self):
        """Test creating empty ReasoningStore."""
        store = ReasoningStore()
        assert store.risks == []
        assert store.strategic_considerations == []
        assert store.work_items == []
        assert store.recommendations == []

    def test_create_with_fact_store(self):
        """Test creating ReasoningStore with FactStore for validation."""
        fact_store = FactStore()
        fact_store.add_fact(
            domain="infrastructure",
            category="compute",
            item="VMware",
            details={},
            status="documented",
            evidence={"exact_quote": "VMware environment"}
        )

        reasoning_store = ReasoningStore(fact_store=fact_store)
        assert reasoning_store.fact_store is fact_store

    def test_add_risk(self):
        """Test adding a risk."""
        store = ReasoningStore()

        risk_id = store.add_risk(
            domain="infrastructure",
            title="EOL VMware Version",
            description="VMware 6.7 reached end of life",
            category="technical_debt",
            severity="high",
            integration_dependent=False,
            mitigation="Upgrade to VMware 8.0",
            based_on_facts=["F-INFRA-001"],
            confidence="high",
            reasoning="Fact F-INFRA-001 shows VMware 6.7 which is EOL"
        )

        assert risk_id.startswith("R-")  # Hash-based ID
        assert len(store.risks) == 1
        assert store.risks[0].title == "EOL VMware Version"

    def test_add_strategic_consideration(self):
        """Test adding a strategic consideration."""
        store = ReasoningStore()

        sc_id = store.add_strategic_consideration(
            domain="infrastructure",
            title="Cloud Platform Alignment",
            description="Target uses AWS, buyer uses Azure",
            lens="buyer_alignment",
            implication="Migration costs will be significant",
            based_on_facts=["F-INFRA-002", "F-INFRA-003"],
            confidence="high",
            reasoning="Facts show AWS usage, buyer confirmed Azure"
        )

        assert sc_id.startswith("SC-")  # Hash-based ID
        assert len(store.strategic_considerations) == 1

    def test_add_work_item(self):
        """Test adding a work item."""
        store = ReasoningStore()

        wi_id = store.add_work_item(
            domain="infrastructure",
            title="Upgrade VMware to 8.0",
            description="Perform VMware upgrade before integration",
            phase="Day_100",
            priority="high",
            owner_type="target",
            triggered_by=["F-INFRA-001"],
            based_on_facts=["F-INFRA-001"],
            confidence="high",
            reasoning="VMware 6.7 EOL requires upgrade",
            cost_estimate="100k_to_500k"
        )

        assert wi_id.startswith("WI-")  # Hash-based ID
        assert len(store.work_items) == 1
        assert store.work_items[0].phase == "Day_100"

    def test_add_recommendation(self):
        """Test adding a recommendation."""
        store = ReasoningStore()

        rec_id = store.add_recommendation(
            domain="infrastructure",
            title="Budget for VMware upgrade",
            description="Include $150K for VMware upgrade in deal model",
            action_type="budget",
            urgency="pre-close",
            rationale="VMware is EOL and must be upgraded",
            based_on_facts=["F-INFRA-001"],
            confidence="high",
            reasoning="EOL systems require immediate attention"
        )

        assert rec_id.startswith("REC-")  # Hash-based ID
        assert len(store.recommendations) == 1

    def test_get_all_findings(self):
        """Test getting all findings."""
        store = ReasoningStore()

        store.add_risk(
            domain="infrastructure",
            title="Risk 1",
            description="Test",
            category="technical_debt",
            severity="high",
            integration_dependent=False,
            mitigation="Fix it",
            based_on_facts=["F-INFRA-001"],
            confidence="high",
            reasoning="Test"
        )
        store.add_work_item(
            domain="infrastructure",
            title="Work 1",
            description="Test",
            phase="Day_1",
            priority="high",
            owner_type="buyer",
            triggered_by=["F-INFRA-001"],
            based_on_facts=[],
            confidence="high",
            reasoning="Test",
            cost_estimate="25k_to_100k"
        )

        findings = store.get_all_findings()

        assert findings["summary"]["risks"] == 1
        assert findings["summary"]["work_items"] == 1
        assert len(findings["risks"]) == 1
        assert len(findings["work_items"]) == 1

    def test_validate_fact_citations_with_fact_store(self):
        """Test that citations are validated against FactStore."""
        fact_store = FactStore()
        fact_store.add_fact(
            domain="infrastructure",
            category="compute",
            item="VMware",
            details={},
            status="documented",
            evidence={"exact_quote": "VMware environment"}
        )

        reasoning_store = ReasoningStore(fact_store=fact_store)

        # Valid citation
        result = reasoning_store.validate_fact_citations(["F-INFRA-001"])
        assert len(result["valid"]) == 1

        # Invalid citation
        result = reasoning_store.validate_fact_citations(["F-INFRA-999"])
        assert len(result["invalid"]) == 1

    def test_get_evidence_chain(self):
        """Test getting evidence chain for a finding."""
        fact_store = FactStore()
        fact_store.add_fact(
            domain="infrastructure",
            category="compute",
            item="VMware 6.7",
            details={"version": "6.7"},
            status="documented",
            evidence={"exact_quote": "VMware vSphere 6.7"}
        )

        reasoning_store = ReasoningStore(fact_store=fact_store)
        risk_id = reasoning_store.add_risk(
            domain="infrastructure",
            title="EOL VMware",
            description="VMware 6.7 is end of life",
            category="technical_debt",
            severity="high",
            integration_dependent=False,
            mitigation="Upgrade",
            based_on_facts=["F-INFRA-001"],
            confidence="high",
            reasoning="6.7 reached EOL"
        )

        chain = reasoning_store.get_evidence_chain(risk_id)

        assert chain["finding"]["title"] == "EOL VMware"
        assert chain["finding_type"] == "risk"
        assert len(chain["cited_facts"]) == 1
        assert chain["cited_facts"][0]["item"] == "VMware 6.7"
        assert chain["evidence_chain_complete"] is True

    def test_save_and_load(self):
        """Test ReasoningStore save and load preserves all data."""
        # Create store with findings
        fact_store = FactStore()
        fact_store.add_fact(
            domain="infrastructure",
            category="compute",
            item="VMware 6.7",
            details={"version": "6.7"},
            status="documented",
            evidence={"exact_quote": "VMware vSphere 6.7"}
        )

        original_store = ReasoningStore(fact_store=fact_store)

        # Add risk
        original_store.add_risk(
            domain="infrastructure",
            title="EOL VMware",
            description="VMware 6.7 is EOL",
            category="technical_debt",
            severity="high",
            integration_dependent=False,
            mitigation="Upgrade to 8.0",
            based_on_facts=["F-INFRA-001"],
            confidence="high",
            reasoning="6.7 EOL Oct 2022"
        )

        # Add work item
        original_store.add_work_item(
            domain="infrastructure",
            title="Upgrade VMware",
            description="Upgrade from 6.7 to 8.0",
            phase="Day_1",
            priority="high",
            owner_type="target",
            triggered_by=["F-INFRA-001"],  # Must be facts, not risk IDs
            based_on_facts=["F-INFRA-001"],
            confidence="high",
            reasoning="VMware 6.7 is EOL and needs upgrade",
            cost_estimate="100k_to_500k"
        )

        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            original_store.save(temp_path)

            # Load into new store
            loaded_store = ReasoningStore.load(temp_path, fact_store=fact_store)

            # Verify risks preserved
            assert len(loaded_store.risks) == 1
            assert loaded_store.risks[0].title == "EOL VMware"
            assert loaded_store.risks[0].severity == "high"

            # Verify work items preserved
            assert len(loaded_store.work_items) == 1
            assert loaded_store.work_items[0].title == "Upgrade VMware"
            assert loaded_store.work_items[0].phase == "Day_1"

            # Verify counters preserved for continuation (keys are R, WI, SC, REC)
            assert loaded_store._counters.get("R", 0) >= 1

        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_save_and_load_all_finding_types(self):
        """Test that all finding types are preserved through save/load."""
        original_store = ReasoningStore()

        # Add all types
        original_store.add_risk(
            domain="infrastructure",
            title="Risk 1",
            description="A risk",
            category="operational",
            severity="medium",
            integration_dependent=False,
            mitigation="Fix it",
            based_on_facts=["F-001"],
            confidence="medium",
            reasoning="Because"
        )

        original_store.add_strategic_consideration(
            domain="infrastructure",
            title="Strategic 1",
            description="A consideration",
            lens="buyer_alignment",
            implication="Review this aspect",
            based_on_facts=["F-001"],
            confidence="high",
            reasoning="Because of the facts"
        )

        original_store.add_recommendation(
            domain="infrastructure",
            title="Rec 1",
            description="A recommendation",
            action_type="investigate",
            urgency="pre-close",
            based_on_facts=["F-001"],
            rationale="Good idea",
            confidence="high",
            reasoning="Based on the evidence"
        )

        # Save and load
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            original_store.save(temp_path)
            loaded_store = ReasoningStore.load(temp_path)

            assert len(loaded_store.risks) == 1
            assert len(loaded_store.strategic_considerations) == 1
            assert len(loaded_store.recommendations) == 1

        finally:
            Path(temp_path).unlink(missing_ok=True)


# =============================================================================
# REASONING TOOLS TESTS
# =============================================================================

class TestReasoningTools:
    """Tests for reasoning tools execution."""

    def test_reasoning_tools_structure(self):
        """Test that reasoning tools have correct structure."""
        tool_names = [t["name"] for t in REASONING_TOOLS]

        assert "identify_risk" in tool_names
        assert "create_strategic_consideration" in tool_names
        assert "create_work_item" in tool_names
        assert "create_recommendation" in tool_names
        assert "complete_reasoning" in tool_names

    def test_execute_identify_risk(self):
        """Test executing identify_risk tool."""
        store = ReasoningStore()

        result = execute_reasoning_tool(
            tool_name="identify_risk",
            tool_input={
                "domain": "infrastructure",
                "title": "EOL VMware",
                "description": "VMware 6.7 is end of life",
                "category": "technical_debt",
                "severity": "high",
                "integration_dependent": False,
                "mitigation": "Upgrade to VMware 8.0",
                "based_on_facts": ["F-INFRA-001"],
                "confidence": "high",
                "reasoning": "Fact shows VMware 6.7 which reached EOL"
            },
            reasoning_store=store
        )

        assert result["status"] == "success"
        assert "risk_id" in result
        assert result["risk_id"].startswith("R-")  # Hash-based ID

    def test_execute_identify_risk_missing_citations(self):
        """Test identify_risk fails without fact citations."""
        store = ReasoningStore()

        result = execute_reasoning_tool(
            tool_name="identify_risk",
            tool_input={
                "domain": "infrastructure",
                "title": "Test Risk",
                "description": "Test",
                "category": "technical_debt",
                "severity": "high",
                "integration_dependent": False,
                "mitigation": "Test",
                "based_on_facts": [],  # Empty!
                "confidence": "high",
                "reasoning": "Test"
            },
            reasoning_store=store
        )

        assert result["status"] == "error"
        assert "based_on_facts" in result["message"]  # Error about missing citations

    def test_execute_create_work_item(self):
        """Test executing create_work_item tool."""
        store = ReasoningStore()

        result = execute_reasoning_tool(
            tool_name="create_work_item",
            tool_input={
                "domain": "infrastructure",
                "title": "Upgrade VMware",
                "description": "Upgrade VMware to 8.0",
                "phase": "Day_100",
                "priority": "high",
                "owner_type": "target",
                "triggered_by": ["F-INFRA-001"],
                "based_on_facts": [],
                "confidence": "high",
                "reasoning": "EOL requires upgrade",
                "cost_estimate": "100k_to_500k"
            },
            reasoning_store=store
        )

        assert result["status"] == "success"
        assert "work_item_id" in result

    def test_execute_create_work_item_missing_triggered_by(self):
        """Test create_work_item fails without triggered_by."""
        store = ReasoningStore()

        result = execute_reasoning_tool(
            tool_name="create_work_item",
            tool_input={
                "domain": "infrastructure",
                "title": "Test",
                "description": "Test",
                "phase": "Day_1",
                "priority": "high",
                "owner_type": "buyer",
                "triggered_by": [],  # Empty!
                "confidence": "high",
                "reasoning": "Test",
                "cost_estimate": "under_25k"
            },
            reasoning_store=store
        )

        assert result["status"] == "error"
        assert "triggered_by" in result["message"]  # Error about missing triggered_by

    def test_execute_complete_reasoning(self):
        """Test executing complete_reasoning tool."""
        store = ReasoningStore()

        # Add some findings first
        store.add_risk(
            domain="infrastructure",
            title="Test",
            description="Test",
            category="technical_debt",
            severity="high",
            integration_dependent=False,
            mitigation="Test",
            based_on_facts=["F-INFRA-001"],
            confidence="high",
            reasoning="Test"
        )

        result = execute_reasoning_tool(
            tool_name="complete_reasoning",
            tool_input={
                "domain": "infrastructure",
                "facts_analyzed": 5,
                "facts_cited": 3,
                "summary": "Analysis complete"
            },
            reasoning_store=store
        )

        assert result["status"] == "success"
        assert result["risks"] == 1

    def test_execute_unknown_tool(self):
        """Test executing unknown tool returns error."""
        store = ReasoningStore()

        result = execute_reasoning_tool(
            tool_name="unknown_tool",
            tool_input={},
            reasoning_store=store
        )

        assert result["status"] == "error"
        assert "Unknown reasoning tool" in result["message"]


# =============================================================================
# DATACLASS TESTS
# =============================================================================

class TestDataclasses:
    """Tests for dataclass serialization."""

    def test_fact_to_dict(self):
        """Test Fact serialization."""
        fact = Fact(
            fact_id="F-INFRA-001",
            domain="infrastructure",
            category="compute",
            item="VMware",
            details={"version": "7.0"},
            status="documented",
            evidence={"exact_quote": "VMware 7.0"}
        )

        d = fact.to_dict()

        assert d["fact_id"] == "F-INFRA-001"
        assert d["item"] == "VMware"
        assert d["details"]["version"] == "7.0"

    def test_gap_to_dict(self):
        """Test Gap serialization."""
        gap = Gap(
            gap_id="G-INFRA-001",
            domain="infrastructure",
            category="backup_dr",
            description="No DR documented",
            importance="high"
        )

        d = gap.to_dict()

        assert d["gap_id"] == "G-INFRA-001"
        assert d["importance"] == "high"

    def test_risk_to_dict(self):
        """Test Risk serialization."""
        risk = Risk(
            finding_id="R-001",
            domain="infrastructure",
            title="EOL VMware",
            description="VMware is EOL",
            category="technical_debt",
            severity="high",
            integration_dependent=False,
            mitigation="Upgrade",
            based_on_facts=["F-INFRA-001"],
            confidence="high",
            reasoning="Test"
        )

        d = risk.to_dict()

        assert d["finding_id"] == "R-001"
        assert d["title"] == "EOL VMware"
        assert d["based_on_facts"] == ["F-INFRA-001"]


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for discovery → reasoning flow."""

    def test_full_discovery_to_reasoning_flow(self):
        """Test complete flow from discovery to reasoning."""
        # Phase 1: Discovery
        fact_store = FactStore()

        # Extract facts
        execute_discovery_tool(
            "create_inventory_entry",
            {
                "domain": "infrastructure",
                "category": "compute",
                "item": "VMware Environment",
                "details": {"version": "6.7", "vm_count": 150},
                "status": "documented",
                "evidence": {"exact_quote": "VMware vSphere 6.7 with 150 VMs"}
            },
            fact_store
        )

        execute_discovery_tool(
            "flag_gap",
            {
                "domain": "infrastructure",
                "category": "backup_dr",
                "description": "No DR RTO/RPO documented",
                "importance": "high"
            },
            fact_store
        )

        execute_discovery_tool(
            "complete_discovery",
            {
                "domain": "infrastructure",
                "categories_covered": ["compute"],
                "categories_missing": ["backup_dr"],
                "summary": "Discovery complete"
            },
            fact_store
        )

        # Phase 2: Reasoning
        reasoning_store = ReasoningStore(fact_store=fact_store)

        risk_result = execute_reasoning_tool(
            "identify_risk",
            {
                "domain": "infrastructure",
                "title": "EOL VMware Version",
                "description": "VMware 6.7 reached end of life",
                "category": "technical_debt",
                "severity": "high",
                "integration_dependent": False,
                "mitigation": "Upgrade to VMware 8.0",
                "based_on_facts": ["F-INFRA-001"],
                "confidence": "high",
                "reasoning": "Fact F-INFRA-001 shows VMware 6.7"
            },
            reasoning_store
        )

        execute_reasoning_tool(
            "create_work_item",
            {
                "domain": "infrastructure",
                "title": "Upgrade VMware to 8.0",
                "description": "Plan and execute VMware upgrade",
                "phase": "Day_100",
                "priority": "high",
                "owner_type": "target",
                "triggered_by": ["F-INFRA-001"],
                "based_on_facts": [],
                "confidence": "high",
                "reasoning": "VMware EOL requires upgrade",
                "cost_estimate": "100k_to_500k"
            },
            reasoning_store
        )

        # Verify end state
        assert len(fact_store.facts) == 1
        assert len(fact_store.gaps) == 1
        assert len(reasoning_store.risks) == 1
        assert len(reasoning_store.work_items) == 1

        # Verify evidence chain
        risk_id = risk_result["risk_id"]
        chain = reasoning_store.get_evidence_chain(risk_id)
        assert chain["evidence_chain_complete"] is True
        assert len(chain["cited_facts"]) == 1
        assert chain["cited_facts"][0]["item"] == "VMware Environment"

    def test_citation_validation_catches_invalid_facts(self):
        """Test that invalid fact citations are caught."""
        fact_store = FactStore()
        fact_store.add_fact(
            domain="infrastructure",
            category="compute",
            item="VMware",
            details={},
            status="documented",
            evidence={"exact_quote": "VMware environment"}
        )

        reasoning_store = ReasoningStore(fact_store=fact_store)

        # This should log a warning for invalid citation
        reasoning_store.add_risk(
            domain="infrastructure",
            title="Test Risk",
            description="Test",
            category="technical_debt",
            severity="high",
            integration_dependent=False,
            mitigation="Test",
            based_on_facts=["F-INFRA-001", "F-INFRA-999"],  # 999 is invalid
            confidence="high",
            reasoning="Test"
        )

        # Risk is still added, but validation would have logged warning
        assert len(reasoning_store.risks) == 1

        # Explicit validation shows the issue
        result = reasoning_store.validate_fact_citations(["F-INFRA-001", "F-INFRA-999"])
        assert "F-INFRA-999" in result["invalid"]
