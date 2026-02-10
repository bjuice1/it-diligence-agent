"""
Tests for Phase 9-10: EOL & Technical Debt Assessment

Run with: pytest tests/test_phase_9_10_eol_technical_debt.py -v
"""
import pytest
from tools.analysis_tools import (
    AnalysisStore,
    # EOL Enums
    EOL_STATUS,
    TECHNICAL_DEBT_SEVERITY,
    TECHNICAL_DEBT_CATEGORIES,
    MODERNIZATION_URGENCY,
    # EOL Reference Data
    EOL_REFERENCE_DATA,
    get_eol_info,
    find_eol_matches
)


class TestEOLEnums:
    """Test that EOL enums exist and have correct values."""

    def test_eol_status_has_values(self):
        """Verify EOL_STATUS has expected values."""
        assert "Current" in EOL_STATUS
        assert "Supported" in EOL_STATUS
        assert "Extended_Support" in EOL_STATUS
        assert "Approaching_EOL" in EOL_STATUS
        assert "Past_EOL" in EOL_STATUS
        assert "Community_Only" in EOL_STATUS
        assert "Unknown" in EOL_STATUS

    def test_technical_debt_severity_has_values(self):
        """Verify TECHNICAL_DEBT_SEVERITY has expected values."""
        assert "Critical" in TECHNICAL_DEBT_SEVERITY
        assert "High" in TECHNICAL_DEBT_SEVERITY
        assert "Medium" in TECHNICAL_DEBT_SEVERITY
        assert "Low" in TECHNICAL_DEBT_SEVERITY
        assert "Unknown" in TECHNICAL_DEBT_SEVERITY

    def test_technical_debt_categories_has_values(self):
        """Verify TECHNICAL_DEBT_CATEGORIES has expected values."""
        assert "Version_Debt" in TECHNICAL_DEBT_CATEGORIES
        assert "Architecture_Debt" in TECHNICAL_DEBT_CATEGORIES
        assert "Code_Debt" in TECHNICAL_DEBT_CATEGORIES
        assert "Integration_Debt" in TECHNICAL_DEBT_CATEGORIES
        assert "Security_Debt" in TECHNICAL_DEBT_CATEGORIES
        assert "Skills_Debt" in TECHNICAL_DEBT_CATEGORIES

    def test_modernization_urgency_has_values(self):
        """Verify MODERNIZATION_URGENCY has expected values."""
        assert "Immediate" in MODERNIZATION_URGENCY
        assert "Near_Term_12_Months" in MODERNIZATION_URGENCY
        assert "Medium_Term_24_Months" in MODERNIZATION_URGENCY
        assert "Long_Term" in MODERNIZATION_URGENCY
        assert "Not_Required" in MODERNIZATION_URGENCY
        assert "Unknown" in MODERNIZATION_URGENCY


class TestEOLReferenceData:
    """Test the EOL reference data and lookup functions."""

    def test_reference_data_has_sap_entries(self):
        """Verify SAP products are in reference data."""
        assert "SAP_ECC_6.0" in EOL_REFERENCE_DATA
        assert "SAP_S4HANA_2023" in EOL_REFERENCE_DATA

    def test_reference_data_has_oracle_entries(self):
        """Verify Oracle products are in reference data."""
        assert "Oracle_EBS_12.2" in EOL_REFERENCE_DATA
        assert "Oracle_Database_19c" in EOL_REFERENCE_DATA

    def test_reference_data_has_microsoft_entries(self):
        """Verify Microsoft products are in reference data."""
        assert "Windows_Server_2022" in EOL_REFERENCE_DATA
        assert "Microsoft_Dynamics_365_FO" in EOL_REFERENCE_DATA

    def test_reference_data_structure(self):
        """Verify reference data entries have correct structure."""
        entry = EOL_REFERENCE_DATA["SAP_ECC_6.0"]
        assert "eol_date" in entry
        assert "status" in entry
        assert "notes" in entry

    def test_get_eol_info_found(self):
        """Test get_eol_info returns data for known product."""
        info = get_eol_info("SAP_ECC_6.0")
        assert info is not None
        assert info["status"] == "Approaching_EOL"
        assert info["eol_date"] == "2027-12"

    def test_get_eol_info_not_found(self):
        """Test get_eol_info returns None for unknown product."""
        info = get_eol_info("Unknown_Product_123")
        assert info is None

    def test_find_eol_matches_exact(self):
        """Test find_eol_matches with exact vendor/product."""
        matches = find_eol_matches("SAP", "ECC")
        assert len(matches) >= 1
        assert any("SAP_ECC" in m["key"] for m in matches)

    def test_find_eol_matches_with_version(self):
        """Test find_eol_matches boosts confidence for version match."""
        matches = find_eol_matches("SAP", "ECC", "6.0")
        version_match = [m for m in matches if "6.0" in m["key"]]
        assert len(version_match) >= 1
        assert version_match[0]["confidence"] == "high"

    def test_find_eol_matches_no_results(self):
        """Test find_eol_matches returns empty for unknown vendor."""
        matches = find_eol_matches("UnknownVendor", "UnknownProduct")
        assert len(matches) == 0


class TestAssessApplicationEOL:
    """Test the assess_application_eol tool."""

    @pytest.fixture
    def store(self):
        """Fresh AnalysisStore for each test."""
        return AnalysisStore()

    def test_assess_eol_basic(self, store):
        """Test recording basic EOL assessment."""
        result = store.execute_tool("assess_application_eol", {
            "application_name": "SAP ECC",
            "vendor": "SAP",
            "current_version": "ECC 6.0 EHP8",
            "eol_status": "Approaching_EOL",
            "eol_date": "2027-12",
            "eol_source": "EOL_Reference_Data"
        })

        assert result["status"] == "recorded"
        assert result["id"] == "EOL-001"
        assert result["type"] == "eol_assessment"

    def test_assess_eol_full(self, store):
        """Test recording full EOL assessment with all fields."""
        result = store.execute_tool("assess_application_eol", {
            "application_name": "Oracle Database",
            "application_id": "APP-001",
            "vendor": "Oracle",
            "current_version": "12c",
            "eol_status": "Past_EOL",
            "eol_date": "2022-03",
            "eol_source": "EOL_Reference_Data",
            "latest_available_version": "23c",
            "version_gap": "Critical",
            "upgrade_path_available": True,
            "upgrade_path_notes": "Direct upgrade path available with migration assistant",
            "risk_if_not_upgraded": "No security patches, compliance gap, vendor support unavailable",
            "notes": "Critical database supporting ERP"
        })

        assert result["status"] == "recorded"
        assert result["id"] == "EOL-001"

        # Verify stored correctly
        assessments = store.get_eol_assessments()
        assert len(assessments) == 1
        assert assessments[0]["application_name"] == "Oracle Database"
        assert assessments[0]["eol_status"] == "Past_EOL"
        assert assessments[0]["version_gap"] == "Critical"

    def test_assess_eol_multiple(self, store):
        """Test recording multiple EOL assessments."""
        store.execute_tool("assess_application_eol", {
            "application_name": "SAP ECC",
            "vendor": "SAP",
            "current_version": "ECC 6.0",
            "eol_status": "Approaching_EOL",
            "eol_source": "EOL_Reference_Data"
        })

        store.execute_tool("assess_application_eol", {
            "application_name": "Windows Server",
            "vendor": "Microsoft",
            "current_version": "2012 R2",
            "eol_status": "Past_EOL",
            "eol_source": "EOL_Reference_Data"
        })

        assessments = store.get_eol_assessments()
        assert len(assessments) == 2
        assert assessments[0]["id"] == "EOL-001"
        assert assessments[1]["id"] == "EOL-002"


class TestAssessTechnicalDebt:
    """Test the assess_technical_debt tool."""

    @pytest.fixture
    def store(self):
        """Fresh AnalysisStore for each test."""
        return AnalysisStore()

    def test_assess_debt_basic(self, store):
        """Test recording basic technical debt."""
        result = store.execute_tool("assess_technical_debt", {
            "application_name": "SAP ECC",
            "debt_category": "Version_Debt",
            "debt_description": "Running ECC 6.0 which approaches EOL in 2027",
            "severity": "High",
            "modernization_urgency": "Near_Term_12_Months"
        })

        assert result["status"] == "recorded"
        assert result["id"] == "TD-001"
        assert result["type"] == "technical_debt"

    def test_assess_debt_full(self, store):
        """Test recording full technical debt with all fields."""
        result = store.execute_tool("assess_technical_debt", {
            "application_name": "SAP ECC",
            "application_id": "APP-001",
            "debt_category": "Code_Debt",
            "debt_description": "500+ custom ABAP reports and 200+ custom programs requiring S/4HANA compatibility review",
            "severity": "Critical",
            "severity_reasoning": "Blocks migration to S/4HANA, major project risk",
            "business_impact": "Prevents ERP modernization, increasing support costs",
            "modernization_urgency": "Immediate",
            "estimated_effort": "Very_High",
            "remediation_options": [
                "Rewrite custom code for S/4HANA",
                "Replace with standard SAP functionality",
                "Third-party migration tools"
            ],
            "dependencies": ["S/4HANA migration project", "Code remediation budget"],
            "eol_assessment_id": "EOL-001",
            "notes": "Custom code audit completed in Q2"
        })

        assert result["status"] == "recorded"
        assert result["id"] == "TD-001"

        # Verify stored correctly
        debts = store.get_technical_debt_assessments()
        assert len(debts) == 1
        assert debts[0]["debt_category"] == "Code_Debt"
        assert debts[0]["severity"] == "Critical"
        assert len(debts[0]["remediation_options"]) == 3

    def test_assess_debt_multiple_per_app(self, store):
        """Test recording multiple debt items for same application."""
        store.execute_tool("assess_technical_debt", {
            "application_name": "SAP ECC",
            "debt_category": "Version_Debt",
            "debt_description": "Outdated ECC version",
            "severity": "High",
            "modernization_urgency": "Near_Term_12_Months"
        })

        store.execute_tool("assess_technical_debt", {
            "application_name": "SAP ECC",
            "debt_category": "Code_Debt",
            "debt_description": "Heavy customizations",
            "severity": "Critical",
            "modernization_urgency": "Immediate"
        })

        store.execute_tool("assess_technical_debt", {
            "application_name": "SAP ECC",
            "debt_category": "Skills_Debt",
            "debt_description": "ABAP developer shortage",
            "severity": "Medium",
            "modernization_urgency": "Medium_Term_24_Months"
        })

        debts = store.get_technical_debt_assessments()
        assert len(debts) == 3

        # All for same app
        assert all(d["application_name"] == "SAP ECC" for d in debts)


class TestEOLGetterMethods:
    """Test EOL getter and summary methods."""

    @pytest.fixture
    def populated_store(self):
        """Create store with sample EOL data."""
        store = AnalysisStore()

        # Current/Supported
        store.execute_tool("assess_application_eol", {
            "application_name": "SAP S/4HANA",
            "vendor": "SAP",
            "current_version": "2023",
            "eol_status": "Current",
            "eol_source": "EOL_Reference_Data"
        })

        # Approaching EOL
        store.execute_tool("assess_application_eol", {
            "application_name": "SAP ECC",
            "vendor": "SAP",
            "current_version": "ECC 6.0",
            "eol_status": "Approaching_EOL",
            "eol_date": "2027-12",
            "eol_source": "EOL_Reference_Data",
            "risk_if_not_upgraded": "No patches after 2027"
        })

        # Past EOL
        store.execute_tool("assess_application_eol", {
            "application_name": "Oracle Database",
            "vendor": "Oracle",
            "current_version": "11g",
            "eol_status": "Past_EOL",
            "eol_date": "2020-12",
            "eol_source": "EOL_Reference_Data",
            "risk_if_not_upgraded": "Security risk, no vendor support"
        })

        return store

    def test_get_eol_assessments(self, populated_store):
        """Test getting all EOL assessments."""
        assessments = populated_store.get_eol_assessments()
        assert len(assessments) == 3

    def test_get_eol_assessments_by_status(self, populated_store):
        """Test filtering by EOL status."""
        past_eol = populated_store.get_eol_assessments_by_status("Past_EOL")
        assert len(past_eol) == 1
        assert past_eol[0]["application_name"] == "Oracle Database"

        current = populated_store.get_eol_assessments_by_status("Current")
        assert len(current) == 1
        assert current[0]["application_name"] == "SAP S/4HANA"

    def test_get_eol_risks(self, populated_store):
        """Test getting EOL risk items."""
        risks = populated_store.get_eol_risks()
        assert len(risks) == 2  # Approaching_EOL and Past_EOL

        app_names = [r["application_name"] for r in risks]
        assert "SAP ECC" in app_names
        assert "Oracle Database" in app_names

    def test_get_eol_summary(self, populated_store):
        """Test EOL summary generation."""
        summary = populated_store.get_eol_summary()

        assert summary["status"] == "analyzed"
        assert summary["total_assessed"] == 3
        assert summary["past_eol_count"] == 1
        assert summary["approaching_eol_count"] == 1
        assert summary["current_count"] == 1
        assert len(summary["risks"]) == 2

    def test_get_eol_summary_empty(self):
        """Test EOL summary with no assessments."""
        store = AnalysisStore()
        summary = store.get_eol_summary()

        assert summary["status"] == "no_assessments"
        assert summary["total_assessed"] == 0


class TestTechnicalDebtGetterMethods:
    """Test technical debt getter and summary methods."""

    @pytest.fixture
    def populated_store(self):
        """Create store with sample technical debt data."""
        store = AnalysisStore()

        # Critical debt
        store.execute_tool("assess_technical_debt", {
            "application_name": "SAP ECC",
            "debt_category": "Code_Debt",
            "debt_description": "Heavy ABAP customizations",
            "severity": "Critical",
            "modernization_urgency": "Immediate"
        })

        # High debt
        store.execute_tool("assess_technical_debt", {
            "application_name": "SAP ECC",
            "debt_category": "Version_Debt",
            "debt_description": "Outdated version",
            "severity": "High",
            "modernization_urgency": "Near_Term_12_Months"
        })

        # Medium debt
        store.execute_tool("assess_technical_debt", {
            "application_name": "Legacy App",
            "debt_category": "Documentation_Debt",
            "debt_description": "Missing system documentation",
            "severity": "Medium",
            "modernization_urgency": "Medium_Term_24_Months"
        })

        # Low debt
        store.execute_tool("assess_technical_debt", {
            "application_name": "CRM System",
            "debt_category": "Architecture_Debt",
            "debt_description": "Monolithic architecture",
            "severity": "Low",
            "modernization_urgency": "Long_Term"
        })

        return store

    def test_get_technical_debt_assessments(self, populated_store):
        """Test getting all technical debt assessments."""
        debts = populated_store.get_technical_debt_assessments()
        assert len(debts) == 4

    def test_get_technical_debt_by_severity(self, populated_store):
        """Test filtering by severity."""
        critical = populated_store.get_technical_debt_by_severity("Critical")
        assert len(critical) == 1
        assert critical[0]["debt_category"] == "Code_Debt"

        high = populated_store.get_technical_debt_by_severity("High")
        assert len(high) == 1

    def test_get_critical_technical_debt(self, populated_store):
        """Test getting Critical and High severity debt."""
        critical_high = populated_store.get_critical_technical_debt()
        assert len(critical_high) == 2

        severities = [d["severity"] for d in critical_high]
        assert "Critical" in severities
        assert "High" in severities

    def test_get_technical_debt_summary(self, populated_store):
        """Test technical debt summary generation."""
        summary = populated_store.get_technical_debt_summary()

        assert summary["status"] == "analyzed"
        assert summary["total_debt_items"] == 4
        assert summary["critical_count"] == 1
        assert summary["high_count"] == 1
        assert len(summary["critical_items"]) == 2  # Critical + High

        # Check category counts
        assert summary["by_category"]["Code_Debt"] == 1
        assert summary["by_category"]["Version_Debt"] == 1
        assert summary["by_category"]["Documentation_Debt"] == 1
        assert summary["by_category"]["Architecture_Debt"] == 1

    def test_get_technical_debt_summary_empty(self):
        """Test technical debt summary with no assessments."""
        store = AnalysisStore()
        summary = store.get_technical_debt_summary()

        assert summary["status"] == "no_assessments"
        assert summary["total_debt_items"] == 0


class TestIDGeneration:
    """Test ID generation for EOL and technical debt."""

    def test_eol_id_sequence(self):
        """Test EOL assessment IDs are sequential."""
        store = AnalysisStore()

        for i in range(5):
            result = store.execute_tool("assess_application_eol", {
                "application_name": f"App {i}",
                "vendor": "Vendor",
                "current_version": "1.0",
                "eol_status": "Current",
                "eol_source": "Assumption"
            })
            assert result["id"] == f"EOL-{i+1:03d}"

    def test_technical_debt_id_sequence(self):
        """Test technical debt IDs are sequential."""
        store = AnalysisStore()

        for i in range(5):
            result = store.execute_tool("assess_technical_debt", {
                "application_name": f"App {i}",
                "debt_category": "Version_Debt",
                "debt_description": "Test debt",
                "severity": "Medium",
                "modernization_urgency": "Long_Term"
            })
            assert result["id"] == f"TD-{i+1:03d}"

    def test_ids_independent(self):
        """Test EOL and TD IDs are independent sequences."""
        store = AnalysisStore()

        eol_result = store.execute_tool("assess_application_eol", {
            "application_name": "App 1",
            "vendor": "Vendor",
            "current_version": "1.0",
            "eol_status": "Current",
            "eol_source": "Assumption"
        })

        td_result = store.execute_tool("assess_technical_debt", {
            "application_name": "App 1",
            "debt_category": "Version_Debt",
            "debt_description": "Test debt",
            "severity": "Medium",
            "modernization_urgency": "Long_Term"
        })

        assert eol_result["id"] == "EOL-001"
        assert td_result["id"] == "TD-001"
