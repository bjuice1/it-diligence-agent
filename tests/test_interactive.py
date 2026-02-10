"""
Tests for the interactive CLI module.
"""

import json
import tempfile
from pathlib import Path

from interactive import Session, InteractiveCLI, COMMANDS
from interactive.commands import (
    cmd_help, cmd_status, cmd_list, cmd_explain,
    cmd_adjust, cmd_undo, cmd_add, cmd_clear, cmd_show,
    cmd_delete, cmd_note, cmd_search, cmd_history,
    VALID_SEVERITIES, VALID_PHASES, VALID_PRIORITIES, VALID_OWNERS, VALID_COST_ESTIMATES,
    VALID_DOMAINS
)
from stores.fact_store import FactStore
from tools_v2.reasoning_tools import ReasoningStore


class TestSession:
    """Test Session class functionality."""

    def test_create_empty_session(self):
        """Test creating empty session."""
        session = Session()
        assert isinstance(session.fact_store, FactStore)
        assert isinstance(session.reasoning_store, ReasoningStore)
        assert session.deal_context == {}
        assert session.modifications == []
        assert not session.has_unsaved_changes

    def test_create_session_with_stores(self):
        """Test creating session with existing stores."""
        fact_store = FactStore(deal_id="test-deal")
        reasoning_store = ReasoningStore(fact_store=fact_store)

        session = Session(
            fact_store=fact_store,
            reasoning_store=reasoning_store,
            deal_context={"notes": []}
        )

        assert session.fact_store is fact_store
        assert session.reasoning_store is reasoning_store

    def test_modification_tracking(self):
        """Test modification tracking."""
        session = Session()
        assert not session.has_unsaved_changes
        assert session.unsaved_change_count == 0

        # Record a modification
        session.record_modification(
            item_type='risk',
            item_id='R-001',
            field='severity',
            old_value='medium',
            new_value='high'
        )

        assert session.has_unsaved_changes
        assert session.unsaved_change_count == 1
        assert len(session.modifications) == 1

    def test_mark_saved(self):
        """Test marking session as saved."""
        session = Session()
        session.record_modification('risk', 'R-001', 'severity', 'medium', 'high')
        assert session.has_unsaved_changes

        session.mark_saved()
        assert not session.has_unsaved_changes

    def test_add_deal_context(self):
        """Test adding deal context."""
        session = Session()
        session.add_deal_context("Healthcare deal - HIPAA applies")

        assert 'notes' in session.deal_context
        assert len(session.deal_context['notes']) == 1
        assert session.deal_context['notes'][0]['text'] == "Healthcare deal - HIPAA applies"

    def test_clear_deal_context(self):
        """Test clearing deal context."""
        session = Session()
        session.add_deal_context("Test context")
        session.clear_deal_context()

        assert session.deal_context == {}

    def test_get_summary(self):
        """Test getting session summary."""
        session = Session()

        # Add some facts
        session.fact_store.add_fact(
            domain="infrastructure",
            category="hosting",
            item="Primary Data Center",
            details={"vendor": "Equinix"},
            status="documented",
            evidence={"exact_quote": "Located at Equinix CH3"}
        )

        summary = session.get_summary()

        assert summary['facts'] == 1
        assert summary['gaps'] == 0
        assert 'infrastructure' in summary['domains_with_facts']
        assert 'risk_summary' in summary
        assert 'cost_summary' in summary

    def test_get_item_by_id_risk(self):
        """Test getting risk by ID."""
        session = Session()

        # Add a risk
        risk_id = session.reasoning_store.add_risk(
            domain="infrastructure",
            title="EOL VMware",
            description="VMware 6.7 is end of life",
            category="technical_debt",
            severity="high",
            integration_dependent=False,
            mitigation="Upgrade to vSphere 8",
            based_on_facts=["F-INFRA-001"],
            confidence="high",
            reasoning="VMware 6.7 EOL was Oct 2022"
        )

        result = session.get_item_by_id(risk_id)
        assert result is not None
        item_type, item = result
        assert item_type == 'risk'
        assert item.title == "EOL VMware"

    def test_get_item_by_id_work_item(self):
        """Test getting work item by ID."""
        session = Session()

        wi_id = session.reasoning_store.add_work_item(
            domain="infrastructure",
            title="VMware Upgrade",
            description="Upgrade VMware",
            phase="Day_100",
            priority="high",
            owner_type="target",
            triggered_by=["F-INFRA-001"],
            based_on_facts=["F-INFRA-001"],
            confidence="high",
            reasoning="Required for support",
            cost_estimate="100k_to_500k"
        )

        result = session.get_item_by_id(wi_id)
        assert result is not None
        item_type, item = result
        assert item_type == 'work_item'
        assert item.title == "VMware Upgrade"

    def test_adjust_risk_severity(self):
        """Test adjusting risk severity."""
        session = Session()

        risk_id = session.reasoning_store.add_risk(
            domain="infrastructure",
            title="Test Risk",
            description="Test",
            category="general",
            severity="medium",
            integration_dependent=False,
            mitigation="",
            based_on_facts=[],
            confidence="medium",
            reasoning=""
        )

        success = session.adjust_risk(risk_id, "severity", "critical")
        assert success

        risk = session.get_risk(risk_id)
        assert risk.severity == "critical"

        # Check modification was recorded
        assert len(session.modifications) == 1
        mod = session.modifications[0]
        assert mod.old_value == "medium"
        assert mod.new_value == "critical"

    def test_undo_last_modification(self):
        """Test undoing last modification."""
        session = Session()

        risk_id = session.reasoning_store.add_risk(
            domain="infrastructure",
            title="Test Risk",
            description="Test",
            category="general",
            severity="medium",
            integration_dependent=False,
            mitigation="",
            based_on_facts=[],
            confidence="medium",
            reasoning=""
        )

        # Make a change
        session.adjust_risk(risk_id, "severity", "critical")
        assert session.get_risk(risk_id).severity == "critical"

        # Undo it
        mod = session.undo_last()
        assert mod is not None
        assert session.get_risk(risk_id).severity == "medium"


class TestCommands:
    """Test command functions."""

    def test_cmd_help_basic(self):
        """Test help command."""
        session = Session()
        output = cmd_help(session, [])

        assert "IT DUE DILIGENCE" in output
        assert "help" in output
        assert "status" in output
        assert "list" in output
        assert "explain" in output
        assert "adjust" in output

    def test_cmd_help_specific_command(self):
        """Test help for specific command."""
        session = Session()
        output = cmd_help(session, ["adjust"])

        assert "adjust" in output.lower()
        assert "severity" in output
        assert "phase" in output

    def test_cmd_status_empty(self):
        """Test status command on empty session."""
        session = Session()
        output = cmd_status(session, [])

        assert "SESSION STATUS" in output
        assert "Facts:" in output
        assert "Risks:" in output

    def test_cmd_status_with_data(self):
        """Test status command with data."""
        session = Session()

        # Add facts and risks
        session.fact_store.add_fact(
            domain="infrastructure",
            category="compute",
            item="VMware",
            details={},
            status="documented",
            evidence={}
        )

        session.reasoning_store.add_risk(
            domain="infrastructure",
            title="Test Risk",
            description="Test",
            category="general",
            severity="high",
            integration_dependent=False,
            mitigation="",
            based_on_facts=[],
            confidence="medium",
            reasoning=""
        )

        output = cmd_status(session, [])

        assert "Facts:    1" in output
        assert "Risks:    1" in output
        assert "High:     1" in output

    def test_cmd_list_facts(self):
        """Test list facts command."""
        session = Session()
        session.fact_store.add_fact(
            domain="infrastructure",
            category="compute",
            item="VMware Environment",
            details={"version": "6.7"},
            status="documented",
            evidence={}
        )

        output = cmd_list(session, ["facts"])

        assert "FACTS" in output
        assert "INFRASTRUCTURE" in output
        assert "VMware Environment" in output

    def test_cmd_list_risks(self):
        """Test list risks command."""
        session = Session()
        session.reasoning_store.add_risk(
            domain="infrastructure",
            title="EOL Software",
            description="Test",
            category="general",
            severity="high",
            integration_dependent=False,
            mitigation="",
            based_on_facts=[],
            confidence="medium",
            reasoning=""
        )

        output = cmd_list(session, ["risks"])

        assert "RISKS" in output
        assert "R-" in output  # Hash-based ID
        assert "EOL Software" in output
        assert "HIGH" in output

    def test_cmd_list_work_items(self):
        """Test list work items command."""
        session = Session()
        session.reasoning_store.add_work_item(
            domain="infrastructure",
            title="Upgrade VMware",
            description="Test",
            phase="Day_100",
            priority="high",
            owner_type="target",
            triggered_by=[],
            based_on_facts=[],
            confidence="medium",
            reasoning="",
            cost_estimate="100k_to_500k"
        )

        output = cmd_list(session, ["work-items"])

        assert "WORK ITEMS" in output
        assert "WI-" in output  # Hash-based ID
        assert "Upgrade VMware" in output
        assert "Day_100" in output

    def test_cmd_list_with_filter(self):
        """Test list with filter."""
        session = Session()

        # Add risks with different severities
        session.reasoning_store.add_risk(
            domain="infrastructure",
            title="High Risk",
            description="Test",
            category="general",
            severity="high",
            integration_dependent=False,
            mitigation="",
            based_on_facts=[],
            confidence="medium",
            reasoning=""
        )

        session.reasoning_store.add_risk(
            domain="infrastructure",
            title="Low Risk",
            description="Test",
            category="general",
            severity="low",
            integration_dependent=False,
            mitigation="",
            based_on_facts=[],
            confidence="medium",
            reasoning=""
        )

        output = cmd_list(session, ["risks", "--severity", "high"])

        assert "High Risk" in output
        assert "Low Risk" not in output

    def test_cmd_explain_risk(self):
        """Test explain command for risk."""
        session = Session()

        session.fact_store.add_fact(
            domain="infrastructure",
            category="compute",
            item="VMware",
            details={},
            status="documented",
            evidence={"exact_quote": "VMware vSphere 6.7"}
        )

        risk_id = session.reasoning_store.add_risk(
            domain="infrastructure",
            title="EOL VMware",
            description="VMware is end of life",
            category="technical_debt",
            severity="high",
            integration_dependent=False,
            mitigation="Upgrade to newer version",
            based_on_facts=["F-INFRA-001"],
            confidence="high",
            reasoning="VMware 6.7 EOL Oct 2022"
        )

        output = cmd_explain(session, [risk_id])

        assert risk_id in output
        assert "RISK: EOL VMware" in output
        assert "Severity:" in output and "HIGH" in output
        assert "REASONING" in output
        assert "EVIDENCE" in output
        assert "F-INFRA-001" in output

    def test_cmd_adjust_risk_severity(self):
        """Test adjust risk severity."""
        session = Session()

        risk_id = session.reasoning_store.add_risk(
            domain="infrastructure",
            title="Test Risk",
            description="Test",
            category="general",
            severity="medium",
            integration_dependent=False,
            mitigation="",
            based_on_facts=[],
            confidence="medium",
            reasoning=""
        )

        output = cmd_adjust(session, [risk_id, "severity", "critical"])

        assert f"{risk_id} severity" in output
        assert "medium" in output
        assert "critical" in output
        assert session.get_risk(risk_id).severity == "critical"

    def test_cmd_adjust_invalid_severity(self):
        """Test adjust with invalid severity."""
        session = Session()

        risk_id = session.reasoning_store.add_risk(
            domain="infrastructure",
            title="Test Risk",
            description="Test",
            category="general",
            severity="medium",
            integration_dependent=False,
            mitigation="",
            based_on_facts=[],
            confidence="medium",
            reasoning=""
        )

        output = cmd_adjust(session, [risk_id, "severity", "invalid"])

        assert "Invalid severity" in output
        assert session.get_risk(risk_id).severity == "medium"  # Unchanged

    def test_cmd_adjust_work_item_phase(self):
        """Test adjust work item phase."""
        session = Session()

        wi_id = session.reasoning_store.add_work_item(
            domain="infrastructure",
            title="Test Work Item",
            description="Test",
            phase="Day_100",
            priority="medium",
            owner_type="target",
            triggered_by=[],
            based_on_facts=[],
            confidence="medium",
            reasoning="",
            cost_estimate="25k_to_100k"
        )

        output = cmd_adjust(session, [wi_id, "phase", "Day_1"])

        assert "phase" in output
        assert "Day_100" in output
        assert "Day_1" in output
        assert session.get_work_item(wi_id).phase == "Day_1"

    def test_cmd_undo(self):
        """Test undo command."""
        session = Session()

        risk_id = session.reasoning_store.add_risk(
            domain="infrastructure",
            title="Test Risk",
            description="Test",
            category="general",
            severity="medium",
            integration_dependent=False,
            mitigation="",
            based_on_facts=[],
            confidence="medium",
            reasoning=""
        )

        cmd_adjust(session, [risk_id, "severity", "high"])
        output = cmd_undo(session, [])

        assert "Undone" in output
        assert session.get_risk(risk_id).severity == "medium"

    def test_cmd_undo_nothing(self):
        """Test undo when nothing to undo."""
        session = Session()
        output = cmd_undo(session, [])
        assert "Nothing to undo" in output

    def test_cmd_add_context(self):
        """Test add context command."""
        session = Session()
        output = cmd_add(session, ["context", "Healthcare deal - HIPAA applies"])

        assert "Added deal context" in output
        assert len(session.deal_context.get('notes', [])) == 1

    def test_cmd_clear_context(self):
        """Test clear context command."""
        session = Session()
        session.add_deal_context("Test")
        output = cmd_clear(session, ["context"])

        assert "cleared" in output
        assert session.deal_context == {}

    def test_cmd_show_context(self):
        """Test show context command."""
        session = Session()
        session.add_deal_context("Healthcare deal - HIPAA applies")
        output = cmd_show(session, ["context"])

        assert "Deal Context" in output
        assert "Healthcare deal" in output


class TestInteractiveCLI:
    """Test InteractiveCLI class."""

    def test_parse_command_simple(self):
        """Test parsing simple commands."""
        session = Session()
        cli = InteractiveCLI(session)

        cmd, args = cli.parse_command("help")
        assert cmd == "help"
        assert args == []

    def test_parse_command_with_args(self):
        """Test parsing commands with arguments."""
        session = Session()
        cli = InteractiveCLI(session)

        cmd, args = cli.parse_command("explain R-001")
        assert cmd == "explain"
        assert args == ["R-001"]

    def test_parse_command_with_quoted_args(self):
        """Test parsing commands with quoted arguments."""
        session = Session()
        cli = InteractiveCLI(session)

        cmd, args = cli.parse_command('add context "Healthcare deal - HIPAA applies"')
        assert cmd == "add"
        assert args == ["context", "Healthcare deal - HIPAA applies"]

    def test_parse_command_empty(self):
        """Test parsing empty command."""
        session = Session()
        cli = InteractiveCLI(session)

        cmd, args = cli.parse_command("")
        assert cmd is None
        assert args == []

    def test_execute_command_help(self):
        """Test executing help command."""
        session = Session()
        cli = InteractiveCLI(session)

        output = cli.execute_command("help", [])
        assert "IT DUE DILIGENCE" in output

    def test_execute_command_unknown(self):
        """Test executing unknown command."""
        session = Session()
        cli = InteractiveCLI(session)

        output = cli.execute_command("unknown_cmd", [])
        assert "Unknown command" in output

    def test_execute_command_exit(self):
        """Test executing exit command."""
        session = Session()
        cli = InteractiveCLI(session)

        output = cli.execute_command("exit", [])
        assert output == "_EXIT"

    def test_execute_command_exit_with_changes(self):
        """Test executing exit with unsaved changes."""
        session = Session()
        session.record_modification('risk', 'R-001', 'severity', 'medium', 'high')

        cli = InteractiveCLI(session)
        output = cli.execute_command("exit", [])

        assert output.startswith("_EXIT_CHECK:")


class TestSessionLoadSave:
    """Test session load/save functionality."""

    def test_save_to_files(self):
        """Test saving session to files."""
        session = Session()

        # Add some data
        session.fact_store.add_fact(
            domain="infrastructure",
            category="compute",
            item="VMware",
            details={"version": "6.7"},
            status="documented",
            evidence={"exact_quote": "VMware vSphere 6.7"}
        )

        session.reasoning_store.add_risk(
            domain="infrastructure",
            title="EOL VMware",
            description="Test",
            category="general",
            severity="high",
            integration_dependent=False,
            mitigation="",
            based_on_facts=["F-INFRA-001"],
            confidence="medium",
            reasoning=""
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            saved_files = session.save_to_files(Path(tmpdir), "test")

            assert 'facts' in saved_files
            assert 'findings' in saved_files
            assert saved_files['facts'].exists()
            assert saved_files['findings'].exists()

            # Verify saved content
            with open(saved_files['facts']) as f:
                facts_data = json.load(f)
                assert len(facts_data['facts']) == 1

    def test_load_from_files(self):
        """Test loading session from files."""
        # Create files
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create facts file
            facts_data = {
                "facts": [{
                    "fact_id": "F-INFRA-001",
                    "domain": "infrastructure",
                    "category": "compute",
                    "item": "VMware",
                    "details": {"version": "6.7"},
                    "status": "documented",
                    "evidence": {"exact_quote": "VMware 6.7"}
                }],
                "gaps": []
            }

            facts_file = tmpdir / "facts.json"
            with open(facts_file, 'w') as f:
                json.dump(facts_data, f)

            # Create findings file
            findings_data = {
                "domain": "infrastructure",
                "findings": {
                    "risks": [{
                        "domain": "infrastructure",
                        "title": "EOL VMware",
                        "description": "Test",
                        "category": "general",
                        "severity": "high",
                        "based_on_facts": ["F-INFRA-001"]
                    }],
                    "work_items": [],
                    "strategic_considerations": [],
                    "recommendations": []
                }
            }

            findings_file = tmpdir / "findings.json"
            with open(findings_file, 'w') as f:
                json.dump(findings_data, f)

            # Load session
            session = Session.load_from_files(
                facts_file=facts_file,
                findings_file=findings_file
            )

            assert len(session.fact_store.facts) == 1
            assert len(session.reasoning_store.risks) == 1
            assert session.reasoning_store.risks[0].title == "EOL VMware"


class TestValidationConstants:
    """Test validation constants."""

    def test_valid_severities(self):
        """Test valid severity values."""
        assert 'critical' in VALID_SEVERITIES
        assert 'high' in VALID_SEVERITIES
        assert 'medium' in VALID_SEVERITIES
        assert 'low' in VALID_SEVERITIES

    def test_valid_phases(self):
        """Test valid phase values."""
        assert 'Day_1' in VALID_PHASES
        assert 'Day_100' in VALID_PHASES
        assert 'Post_100' in VALID_PHASES

    def test_valid_priorities(self):
        """Test valid priority values."""
        assert 'critical' in VALID_PRIORITIES
        assert 'high' in VALID_PRIORITIES
        assert 'medium' in VALID_PRIORITIES
        assert 'low' in VALID_PRIORITIES

    def test_valid_owners(self):
        """Test valid owner values."""
        assert 'buyer' in VALID_OWNERS
        assert 'target' in VALID_OWNERS
        assert 'shared' in VALID_OWNERS
        assert 'vendor' in VALID_OWNERS

    def test_valid_cost_estimates(self):
        """Test valid cost estimate values."""
        assert 'under_25k' in VALID_COST_ESTIMATES
        assert '25k_to_100k' in VALID_COST_ESTIMATES
        assert '100k_to_500k' in VALID_COST_ESTIMATES
        assert '500k_to_1m' in VALID_COST_ESTIMATES
        assert 'over_1m' in VALID_COST_ESTIMATES

    def test_valid_domains(self):
        """Test valid domain values."""
        assert 'infrastructure' in VALID_DOMAINS
        assert 'network' in VALID_DOMAINS
        assert 'cybersecurity' in VALID_DOMAINS
        assert 'applications' in VALID_DOMAINS
        assert 'identity_access' in VALID_DOMAINS
        assert 'organization' in VALID_DOMAINS


class TestManualEntryCommands:
    """Test manual entry commands (add fact, risk, work-item, gap)."""

    def test_add_fact(self):
        """Test adding a manual fact."""
        session = Session()
        output = cmd_add(session, ["fact", "infrastructure", "Primary DC is in Chicago"])

        assert "Added fact" in output
        assert "F-TGT-INFRA-001" in output
        assert len(session.fact_store.facts) == 1
        assert session.fact_store.facts[0].item == "Primary DC is in Chicago"

    def test_add_fact_invalid_domain(self):
        """Test adding fact with invalid domain."""
        session = Session()
        output = cmd_add(session, ["fact", "invalid_domain", "Test fact"])

        assert "Invalid domain" in output
        assert len(session.fact_store.facts) == 0

    def test_add_risk(self):
        """Test adding a manual risk."""
        session = Session()
        output = cmd_add(session, ["risk", "No SIEM deployed", "high", "No centralized security monitoring"])

        assert "Added risk" in output
        assert "R-" in output  # Hash-based ID
        assert len(session.reasoning_store.risks) == 1
        assert session.reasoning_store.risks[0].title == "No SIEM deployed"
        assert session.reasoning_store.risks[0].severity == "high"

    def test_add_risk_invalid_severity(self):
        """Test adding risk with invalid severity."""
        session = Session()
        output = cmd_add(session, ["risk", "Test Risk", "invalid", "Test description"])

        assert "Invalid severity" in output
        assert len(session.reasoning_store.risks) == 0

    def test_add_work_item(self):
        """Test adding a manual work item."""
        session = Session()
        output = cmd_add(session, ["work-item", "Deploy SIEM solution", "Day_100", "100k_to_500k"])

        assert "Added work item" in output
        assert "WI-" in output  # Hash-based ID
        assert len(session.reasoning_store.work_items) == 1
        assert session.reasoning_store.work_items[0].title == "Deploy SIEM solution"
        assert session.reasoning_store.work_items[0].phase == "Day_100"

    def test_add_work_item_invalid_phase(self):
        """Test adding work item with invalid phase."""
        session = Session()
        output = cmd_add(session, ["work-item", "Test Item", "Day_50", "25k_to_100k"])

        assert "Invalid phase" in output
        assert len(session.reasoning_store.work_items) == 0

    def test_add_gap(self):
        """Test adding a manual gap."""
        session = Session()
        output = cmd_add(session, ["gap", "cybersecurity", "Missing penetration test results"])

        assert "Added gap" in output
        assert "G-TGT-CYBER-001" in output
        assert len(session.fact_store.gaps) == 1
        assert session.fact_store.gaps[0].description == "Missing penetration test results"


class TestDeleteCommand:
    """Test delete command."""

    def test_delete_risk(self):
        """Test deleting a risk."""
        session = Session()
        risk_id = session.reasoning_store.add_risk(
            domain="infrastructure",
            title="Test Risk",
            description="Test",
            category="general",
            severity="medium",
            integration_dependent=False,
            mitigation="",
            based_on_facts=[],
            confidence="medium",
            reasoning=""
        )

        assert len(session.reasoning_store.risks) == 1
        output = cmd_delete(session, [risk_id])

        assert "Deleted risk" in output
        assert len(session.reasoning_store.risks) == 0

    def test_delete_work_item(self):
        """Test deleting a work item."""
        session = Session()
        wi_id = session.reasoning_store.add_work_item(
            domain="infrastructure",
            title="Test Work Item",
            description="Test",
            phase="Day_100",
            priority="medium",
            owner_type="target",
            triggered_by=[],
            based_on_facts=[],
            confidence="medium",
            reasoning="",
            cost_estimate="25k_to_100k"
        )

        assert len(session.reasoning_store.work_items) == 1
        output = cmd_delete(session, [wi_id])

        assert "Deleted work item" in output
        assert len(session.reasoning_store.work_items) == 0

    def test_delete_fact(self):
        """Test deleting a fact."""
        session = Session()
        session.fact_store.add_fact(
            domain="infrastructure",
            category="compute",
            item="VMware",
            details={},
            status="documented",
            evidence={}
        )

        assert len(session.fact_store.facts) == 1
        output = cmd_delete(session, ["F-TGT-INFRA-001"])

        assert "Deleted fact" in output
        assert len(session.fact_store.facts) == 0

    def test_delete_nonexistent(self):
        """Test deleting nonexistent item."""
        session = Session()
        output = cmd_delete(session, ["R-999"])

        assert "not found" in output


class TestNoteCommand:
    """Test note command."""

    def test_note_on_risk(self):
        """Test adding a note to a risk."""
        session = Session()
        risk_id = session.reasoning_store.add_risk(
            domain="infrastructure",
            title="Test Risk",
            description="Test",
            category="general",
            severity="medium",
            integration_dependent=False,
            mitigation="",
            based_on_facts=[],
            confidence="medium",
            reasoning="Original reasoning"
        )

        output = cmd_note(session, [risk_id, "Discussed with CTO - confirmed critical"])

        assert "Added note" in output
        risk = session.get_risk(risk_id)
        assert "Discussed with CTO" in risk.reasoning

    def test_note_on_work_item(self):
        """Test adding a note to a work item."""
        session = Session()
        wi_id = session.reasoning_store.add_work_item(
            domain="infrastructure",
            title="Test Work Item",
            description="Test",
            phase="Day_100",
            priority="medium",
            owner_type="target",
            triggered_by=[],
            based_on_facts=[],
            confidence="medium",
            reasoning="Original",
            cost_estimate="25k_to_100k"
        )

        output = cmd_note(session, [wi_id, "Buyer to fund this"])

        assert "Added note" in output
        wi = session.get_work_item(wi_id)
        assert "Buyer to fund" in wi.reasoning

    def test_note_nonexistent_item(self):
        """Test adding note to nonexistent item."""
        session = Session()
        output = cmd_note(session, ["R-999", "Test note"])

        assert "not found" in output


class TestSearchCommand:
    """Test search command."""

    def test_search_facts(self):
        """Test searching facts."""
        session = Session()
        session.fact_store.add_fact(
            domain="infrastructure",
            category="compute",
            item="VMware vSphere 6.7 environment",
            details={"version": "6.7"},
            status="documented",
            evidence={}
        )

        output = cmd_search(session, ["VMware"])

        assert "VMware" in output
        assert "F-TGT-INFRA-001" in output

    def test_search_risks(self):
        """Test searching risks."""
        session = Session()
        session.reasoning_store.add_risk(
            domain="infrastructure",
            title="EOL VMware Software",
            description="VMware is end of life",
            category="general",
            severity="high",
            integration_dependent=False,
            mitigation="",
            based_on_facts=[],
            confidence="medium",
            reasoning=""
        )

        output = cmd_search(session, ["VMware"])

        assert "VMware" in output
        assert "R-" in output  # Hash-based ID
        assert "risk" in output

    def test_search_no_results(self):
        """Test search with no results."""
        session = Session()
        output = cmd_search(session, ["nonexistent_term"])

        assert "No results found" in output

    def test_search_case_insensitive(self):
        """Test case-insensitive search."""
        session = Session()
        session.fact_store.add_fact(
            domain="infrastructure",
            category="compute",
            item="VMware Environment",
            details={},
            status="documented",
            evidence={}
        )

        output = cmd_search(session, ["vmware"])  # lowercase

        assert "VMware" in output


class TestHistoryCommand:
    """Test history command."""

    def test_history_empty(self):
        """Test history with no modifications."""
        session = Session()
        output = cmd_history(session, [])

        assert "No modifications" in output

    def test_history_with_modifications(self):
        """Test history with modifications."""
        session = Session()
        risk_id = session.reasoning_store.add_risk(
            domain="infrastructure",
            title="Test Risk",
            description="Test",
            category="general",
            severity="medium",
            integration_dependent=False,
            mitigation="",
            based_on_facts=[],
            confidence="medium",
            reasoning=""
        )

        cmd_adjust(session, [risk_id, "severity", "high"])

        output = cmd_history(session, [])

        assert "Modification History" in output
        assert "severity" in output
        assert "medium" in output
        assert "high" in output


class TestCommandRegistry:
    """Test command registry completeness."""

    def test_all_commands_registered(self):
        """Test all commands are in the registry."""
        expected_commands = [
            'help', 'status', 'list', 'explain', 'adjust', 'undo',
            'add', 'clear', 'show', 'export', 'delete', 'note',
            'search', 'history'
        ]

        for cmd in expected_commands:
            assert cmd in COMMANDS, f"Command '{cmd}' not in registry"

    def test_commands_are_callable(self):
        """Test all registered commands are callable."""
        for cmd_name, cmd_func in COMMANDS.items():
            assert callable(cmd_func), f"Command '{cmd_name}' is not callable"
