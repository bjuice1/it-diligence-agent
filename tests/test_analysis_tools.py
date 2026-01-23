"""
Unit tests for AnalysisStore and tool processing.

Tests the tools module's ability to:
- Store findings from agents
- Merge stores from multiple agents
- Save/load data

Run with: pytest tests/test_analysis_tools.py -v
"""

import sys
import json
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.analysis_tools import AnalysisStore


class TestAnalysisStore:
    """Tests for AnalysisStore functionality."""

    def test_create_empty_store(self):
        """Test creating an empty store."""
        store = AnalysisStore()
        assert store.risks == []
        assert store.gaps == []
        assert store.work_items == []
        assert store.recommendations == []
        assert store.assumptions == []

    def test_add_risk_directly(self):
        """Test adding a risk directly to the store."""
        store = AnalysisStore()

        store.risks.append({
            'id': 'R-TEST-001',
            'risk': 'Server hardware is past end-of-life',
            'severity': 'high',
            'likelihood': 'medium',
            'domain': 'infrastructure'
        })

        assert len(store.risks) == 1
        assert store.risks[0]['severity'] == 'high'

    def test_add_gap_directly(self):
        """Test adding a gap directly to the store."""
        store = AnalysisStore()

        store.gaps.append({
            'id': 'G-TEST-001',
            'gap': 'Network diagrams not provided',
            'priority': 'high',
            'domain': 'network'
        })

        assert len(store.gaps) == 1
        assert store.gaps[0]['priority'] == 'high'

    def test_add_work_item_directly(self):
        """Test adding a work item directly to the store."""
        store = AnalysisStore()

        store.work_items.append({
            'id': 'WI-TEST-001',
            'title': 'Implement MFA',
            'description': 'Deploy multi-factor authentication',
            'timeline_phase': 'Day_100',
            'domain': 'cyber'
        })

        assert len(store.work_items) == 1
        assert store.work_items[0]['title'] == 'Implement MFA'

    def test_add_recommendation_directly(self):
        """Test adding a recommendation directly to the store."""
        store = AnalysisStore()

        store.recommendations.append({
            'id': 'REC-TEST-001',
            'recommendation': 'Migrate to cloud-based ERP',
            'rationale': 'Current SAP is approaching end of life',
            'priority': 'medium'
        })

        assert len(store.recommendations) == 1

    def test_add_assumption_directly(self):
        """Test adding an assumption directly to the store."""
        store = AnalysisStore()

        store.assumptions.append({
            'id': 'A-TEST-001',
            'assumption': 'AD schema is compatible with buyer',
            'confidence': 'medium',
            'domain': 'iam'
        })

        assert len(store.assumptions) == 1

    def test_add_current_state_directly(self):
        """Test adding current state directly to the store."""
        store = AnalysisStore()

        store.current_state.append({
            'id': 'CS-TEST-001',
            'category': 'staffing',
            'item': '18 FTEs in IT department',
            'domain': 'org'
        })

        assert len(store.current_state) == 1

    def test_add_question_directly(self):
        """Test adding a question directly to the store."""
        store = AnalysisStore()

        store.questions.append({
            'id': 'Q-TEST-001',
            'question': 'What is the backup retention policy?',
            'context': 'Document mentions backups but no retention details',
            'priority': 'high',
            'domain': 'infrastructure'
        })

        assert len(store.questions) == 1


class TestStoreMerge:
    """Tests for merging multiple stores."""

    def test_merge_empty_stores(self):
        """Test merging two empty stores."""
        store1 = AnalysisStore()
        store2 = AnalysisStore()

        counts = store1.merge_from(store2)

        assert counts['risks'] == 0
        assert counts['gaps'] == 0

    def test_merge_with_findings(self):
        """Test merging stores with findings."""
        store1 = AnalysisStore()
        store2 = AnalysisStore()

        # Add to store2
        store2.risks.append({'id': 'R-001', 'risk': 'Test risk', 'domain': 'test'})
        store2.gaps.append({'id': 'G-001', 'gap': 'Test gap', 'domain': 'test'})

        counts = store1.merge_from(store2)

        assert counts['risks'] == 1
        assert counts['gaps'] == 1
        assert len(store1.risks) == 1
        assert len(store1.gaps) == 1

    def test_merge_preserves_existing(self):
        """Test that merging preserves existing findings."""
        store1 = AnalysisStore()
        store2 = AnalysisStore()

        # Add to store1
        store1.risks.append({'id': 'R-001', 'risk': 'Existing risk', 'domain': 'test'})

        # Add to store2
        store2.risks.append({'id': 'R-002', 'risk': 'New risk', 'domain': 'test'})

        store1.merge_from(store2)

        assert len(store1.risks) == 2

    def test_merge_multiple_stores(self):
        """Test merging from multiple sources."""
        master = AnalysisStore()
        store1 = AnalysisStore()
        store2 = AnalysisStore()
        store3 = AnalysisStore()

        store1.risks.append({'id': 'R-001', 'risk': 'Risk 1', 'domain': 'infra'})
        store2.gaps.append({'id': 'G-001', 'gap': 'Gap 1', 'domain': 'network'})
        store3.work_items.append({'id': 'WI-001', 'title': 'Work 1', 'domain': 'cyber'})

        master.merge_from(store1)
        master.merge_from(store2)
        master.merge_from(store3)

        assert len(master.risks) == 1
        assert len(master.gaps) == 1
        assert len(master.work_items) == 1


class TestGetAll:
    """Tests for get_all() method."""

    def test_get_all_empty(self):
        """Test get_all on empty store."""
        store = AnalysisStore()
        all_data = store.get_all()

        assert 'risks' in all_data
        assert 'gaps' in all_data
        assert 'work_items' in all_data
        assert all_data['risks'] == []

    def test_get_all_with_data(self):
        """Test get_all with data."""
        store = AnalysisStore()

        store.risks.append({
            'id': 'R-001',
            'risk': 'Test risk',
            'severity': 'high',
            'domain': 'test'
        })

        all_data = store.get_all()
        assert len(all_data['risks']) == 1

    def test_get_all_includes_all_types(self):
        """Test that get_all includes all finding types."""
        store = AnalysisStore()

        store.risks.append({'id': 'R-001', 'risk': 'Risk', 'domain': 'test'})
        store.gaps.append({'id': 'G-001', 'gap': 'Gap', 'domain': 'test'})
        store.work_items.append({'id': 'WI-001', 'title': 'Work', 'domain': 'test'})
        store.recommendations.append({'id': 'REC-001', 'recommendation': 'Rec'})
        store.assumptions.append({'id': 'A-001', 'assumption': 'Assume', 'domain': 'test'})
        store.current_state.append({'id': 'CS-001', 'item': 'State', 'domain': 'test'})

        all_data = store.get_all()

        assert len(all_data['risks']) == 1
        assert len(all_data['gaps']) == 1
        assert len(all_data['work_items']) == 1
        assert len(all_data['recommendations']) == 1
        assert len(all_data['assumptions']) == 1
        assert len(all_data['current_state']) == 1


class TestSaveAndLoad:
    """Tests for save/load functionality."""

    def test_save_to_directory(self):
        """Test saving store to directory."""
        store = AnalysisStore()

        store.risks.append({
            'id': 'R-001',
            'risk': 'Test risk',
            'severity': 'high',
            'domain': 'test'
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            store.save(Path(tmpdir))

            # Check files were created
            assert (Path(tmpdir) / 'risks.json').exists()
            assert (Path(tmpdir) / 'gaps.json').exists()

    def test_saved_data_is_valid_json(self):
        """Test that saved files contain valid JSON."""
        store = AnalysisStore()

        store.risks.append({
            'id': 'R-001',
            'risk': 'Test risk',
            'severity': 'high',
            'domain': 'test'
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            store.save(Path(tmpdir))

            # Load and verify JSON
            with open(Path(tmpdir) / 'risks.json', 'r') as f:
                data = json.load(f)

            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]['id'] == 'R-001'

    def test_save_preserves_unicode(self):
        """Test that saving preserves unicode characters."""
        store = AnalysisStore()

        store.risks.append({
            'id': 'R-001',
            'risk': 'Test with unicode: 日本語 émojis 🔥',
            'severity': 'high',
            'domain': 'test'
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            store.save(Path(tmpdir))

            with open(Path(tmpdir) / 'risks.json', 'r', encoding='utf-8') as f:
                data = json.load(f)

            assert '日本語' in data[0]['risk']
            assert '🔥' in data[0]['risk']


class TestReasoningChain:
    """Tests for reasoning chain functionality."""

    def test_add_reasoning_chain(self):
        """Test adding reasoning chain entries."""
        store = AnalysisStore()

        chain = [
            {'step': 1, 'thought': 'Analyzing infrastructure'},
            {'step': 2, 'thought': 'Found risk with EOL servers'}
        ]

        store.add_reasoning_chain('infrastructure', chain)

        # Access reasoning chains directly or via get_all_reasoning()
        reasoning = store.get_all_reasoning()
        assert 'infrastructure' in reasoning

    def test_multiple_domain_chains(self):
        """Test adding reasoning chains for multiple domains."""
        store = AnalysisStore()

        store.add_reasoning_chain('infrastructure', [{'step': 1, 'thought': 'Infra analysis'}])
        store.add_reasoning_chain('network', [{'step': 1, 'thought': 'Network analysis'}])

        reasoning = store.get_all_reasoning()
        assert 'infrastructure' in reasoning
        assert 'network' in reasoning


class TestDocumentTracking:
    """Tests for document ID tracking."""

    def test_add_document_id(self):
        """Test adding document IDs."""
        store = AnalysisStore()

        store.add_document_id('DOC-001')
        store.add_document_id('DOC-002')

        assert 'DOC-001' in store.document_ids
        assert 'DOC-002' in store.document_ids

    def test_document_ids_no_duplicates(self):
        """Test that document IDs aren't duplicated."""
        store = AnalysisStore()

        store.add_document_id('DOC-001')
        store.add_document_id('DOC-001')  # Add same ID

        assert store.document_ids.count('DOC-001') == 1

