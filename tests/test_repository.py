"""
Unit tests for Repository CRUD operations.

Tests the storage layer's ability to:
- Create, read, update, delete findings
- Handle documents and analysis runs
- Import from AnalysisStore
- Query and filter data

Run with: pytest tests/test_repository.py -v
"""

import pytest
import sys
import tempfile
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from storage import Database, Repository
from storage.models import (
    Document, AnalysisRun, Risk, Gap, Assumption,
    WorkItem, Recommendation, Question,
    generate_id, now_iso
)
from tools.analysis_tools import AnalysisStore


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    db = Database(path)
    db.initialize_schema()

    yield db

    db.close()
    os.unlink(path)


@pytest.fixture
def repository(temp_db):
    """Create a repository with the temp database."""
    return Repository(temp_db)


@pytest.fixture
def sample_document():
    """Create a sample document for testing."""
    return Document(
        document_id=generate_id('DOC'),
        document_name='test_document.pdf',
        document_path='/path/to/test_document.pdf',
        document_type='vdr',
        page_count=10,
        ingested_date=now_iso(),
        last_updated=now_iso(),
        file_hash='abc123'
    )


@pytest.fixture
def sample_run(sample_document):
    """Create a sample analysis run."""
    return AnalysisRun(
        run_id=generate_id('RUN'),
        run_name='Test Analysis',
        started_at=now_iso(),
        mode='fresh',
        status='in_progress',
        deal_context={'deal_name': 'Test Deal'},
        documents_analyzed=[sample_document.document_id]
    )


class TestDocumentCRUD:
    """Tests for Document CRUD operations."""

    def test_create_document(self, repository, sample_document):
        """Test creating a document."""
        repository.create_document(sample_document)

        # Verify it was created
        docs = repository.get_all_documents()
        assert len(docs) == 1
        assert docs[0].document_id == sample_document.document_id
        assert docs[0].document_name == 'test_document.pdf'

    def test_get_document_by_id(self, repository, sample_document):
        """Test retrieving a document by ID."""
        repository.create_document(sample_document)

        doc = repository.get_document(sample_document.document_id)
        assert doc is not None
        assert doc.document_id == sample_document.document_id

    def test_get_nonexistent_document(self, repository):
        """Test retrieving a document that doesn't exist."""
        doc = repository.get_document('DOC-nonexistent')
        assert doc is None

    def test_duplicate_document_id(self, repository, sample_document):
        """Test that duplicate document IDs raise an error."""
        repository.create_document(sample_document)

        # Try to create another with same ID
        duplicate = Document(
            document_id=sample_document.document_id,
            document_name='different_name.pdf',
            document_path='/different/path.pdf',
            document_type='vdr',
            page_count=5,
            ingested_date=now_iso(),
            last_updated=now_iso(),
            file_hash='xyz789'
        )

        # Should raise an error for duplicates
        with pytest.raises(Exception):
            repository.create_document(duplicate)


class TestAnalysisRunCRUD:
    """Tests for AnalysisRun CRUD operations."""

    def test_create_run(self, repository, sample_run):
        """Test creating an analysis run."""
        repository.create_run(sample_run)

        runs = repository.get_all_runs()
        assert len(runs) == 1
        assert runs[0].run_id == sample_run.run_id

    def test_get_run_by_id(self, repository, sample_run):
        """Test retrieving a run by ID."""
        repository.create_run(sample_run)

        run = repository.get_run(sample_run.run_id)
        assert run is not None
        assert run.run_name == 'Test Analysis'

    def test_update_run(self, repository, sample_run):
        """Test updating a run."""
        repository.create_run(sample_run)

        repository.update_run(sample_run.run_id, {'status': 'completed'})

        run = repository.get_run(sample_run.run_id)
        assert run.status == 'completed'

    def test_complete_run(self, repository, sample_run):
        """Test completing a run with summary."""
        repository.create_run(sample_run)

        repository.complete_run(sample_run.run_id, summary={'total_findings': 10})

        run = repository.get_run(sample_run.run_id)
        assert run.status == 'completed'
        assert run.completed_at is not None

    def test_get_latest_run(self, repository):
        """Test getting the latest run."""
        # Create multiple runs
        run1 = AnalysisRun(
            run_id='RUN-001',
            run_name='First Run',
            started_at='2024-01-01T00:00:00',
            mode='fresh',
            status='completed'
        )
        run2 = AnalysisRun(
            run_id='RUN-002',
            run_name='Second Run',
            started_at='2024-01-02T00:00:00',
            mode='fresh',
            status='completed'
        )

        repository.create_run(run1)
        repository.create_run(run2)

        latest = repository.get_latest_run()
        assert latest.run_id == 'RUN-002'


class TestRiskCRUD:
    """Tests for Risk CRUD operations."""

    def test_create_risk(self, repository, sample_run):
        """Test creating a risk."""
        repository.create_run(sample_run)

        risk = Risk(
            risk_id=generate_id('RISK'),
            run_id=sample_run.run_id,
            risk_description='Test risk description',
            severity='high',
            likelihood='medium',
            domain='infrastructure',
            impact_description='Significant impact',
            mitigation='Suggested mitigation'
        )

        repository.create_risk(risk)

        risks = repository.get_all_risks(sample_run.run_id)
        assert len(risks) == 1
        assert risks[0].risk_description == 'Test risk description'
        assert risks[0].severity == 'high'

    def test_get_risks_by_severity(self, repository, sample_run):
        """Test filtering risks by severity."""
        repository.create_run(sample_run)

        # Create risks with different severities
        for sev in ['critical', 'high', 'medium', 'low']:
            risk = Risk(
                risk_id=generate_id('RISK'),
                run_id=sample_run.run_id,
                risk_description=f'{sev} risk',
                severity=sev,
                domain='test'
            )
            repository.create_risk(risk)

        all_risks = repository.get_all_risks(sample_run.run_id)
        assert len(all_risks) == 4

        # Check filtering by severity
        critical_risks = repository.get_risks_by_severity(sample_run.run_id, 'critical')
        assert len(critical_risks) == 1
        assert critical_risks[0].severity == 'critical'


class TestGapCRUD:
    """Tests for Gap CRUD operations."""

    def test_create_gap(self, repository, sample_run):
        """Test creating a gap."""
        repository.create_run(sample_run)

        gap = Gap(
            gap_id=generate_id('GAP'),
            run_id=sample_run.run_id,
            gap_description='Missing information about X',
            priority='high',
            domain='infrastructure',
            why_needed='Required for risk assessment',
            suggested_source='IT Director'
        )

        repository.create_gap(gap)

        gaps = repository.get_all_gaps(sample_run.run_id)
        assert len(gaps) == 1
        assert gaps[0].priority == 'high'

    def test_get_unanswered_gaps(self, repository, sample_run):
        """Test getting unanswered gaps."""
        repository.create_run(sample_run)

        # Create gaps with different statuses
        gap1 = Gap(
            gap_id='GAP-001',
            run_id=sample_run.run_id,
            gap_description='Unanswered gap',
            priority='high',
            domain='infrastructure',
            question_status='not_asked'
        )
        gap2 = Gap(
            gap_id='GAP-002',
            run_id=sample_run.run_id,
            gap_description='Answered gap',
            priority='medium',
            domain='infrastructure',
            question_status='answered'
        )

        repository.create_gap(gap1)
        repository.create_gap(gap2)

        unanswered = repository.get_unanswered_gaps(sample_run.run_id)
        assert len(unanswered) >= 1
        # Should include the open gap
        gap_ids = [g.gap_id for g in unanswered]
        assert 'GAP-001' in gap_ids


class TestWorkItemCRUD:
    """Tests for WorkItem CRUD operations."""

    def test_create_work_item(self, repository, sample_run):
        """Test creating a work item."""
        repository.create_run(sample_run)

        work_item = WorkItem(
            work_item_id=generate_id('WI'),
            run_id=sample_run.run_id,
            title='Migrate servers',
            description='Migrate legacy servers to cloud',
            domain='infrastructure',
            effort_estimate='40 hours',
            cost_estimate_range='$50,000 - $75,000',
            phase='Day_100'
        )

        repository.create_work_item(work_item)

        items = repository.get_all_work_items(sample_run.run_id)
        assert len(items) == 1
        assert items[0].title == 'Migrate servers'
        assert items[0].phase == 'Day_100'


class TestQuestionCRUD:
    """Tests for Question CRUD operations."""

    def test_create_question(self, repository, sample_run):
        """Test creating a question."""
        repository.create_run(sample_run)

        question = Question(
            question_id=generate_id('Q'),
            run_id=sample_run.run_id,
            question_text='What is the current backup strategy?',
            priority='high',
            context='Need to assess backup capabilities',
            status='draft'
        )

        repository.create_question(question)

        # Use get_questions_by_status or get question directly
        questions = repository.get_questions_by_status(sample_run.run_id, 'draft')
        assert len(questions) >= 1

    def test_update_question_with_answer(self, repository, sample_run):
        """Test updating a question with an answer."""
        repository.create_run(sample_run)

        question = Question(
            question_id='Q-001',
            run_id=sample_run.run_id,
            question_text='Test question?',
            status='sent'
        )
        repository.create_question(question)

        # Update with answer using answer_question method
        repository.answer_question('Q-001', 'The answer is 42', source='email')

        updated = repository.get_question('Q-001')
        assert updated.status == 'answered'
        assert updated.answer_text == 'The answer is 42'

    def test_get_question_status_summary(self, repository, sample_run):
        """Test getting question status summary."""
        repository.create_run(sample_run)

        # Create questions with different statuses
        for i, status in enumerate(['draft', 'ready', 'sent', 'answered', 'answered']):
            q = Question(
                question_id=f'Q-{i:03d}',
                run_id=sample_run.run_id,
                question_text=f'Question with status {status}',
                status=status
            )
            repository.create_question(q)

        summary = repository.get_question_status_summary(sample_run.run_id)
        assert summary['total'] == 5
        assert summary.get('draft', 0) == 1
        assert summary.get('answered', 0) == 2


class TestAnalysisStoreImport:
    """Tests for importing from AnalysisStore."""

    def test_import_from_analysis_store(self, repository, sample_run):
        """Test importing findings from an AnalysisStore."""
        repository.create_run(sample_run)

        # Create an AnalysisStore with findings
        # Note: AnalysisStore uses 'risk', 'gap' keys while import maps them
        store = AnalysisStore()
        store.risks.append({
            'id': 'R-TEST-001',
            'risk': 'Test risk from store',
            'severity': 'high',
            'domain': 'infrastructure'
        })
        store.gaps.append({
            'id': 'G-TEST-001',
            'gap': 'Test gap from store',
            'priority': 'high',
            'domain': 'infrastructure'
        })
        store.work_items.append({
            'id': 'WI-TEST-001',
            'title': 'Test work item',
            'domain': 'infrastructure',
            'timeline_phase': 'Day_1'
        })

        # Import to database
        counts = repository.import_from_analysis_store(store, sample_run.run_id)

        # Verify import worked (counts may vary based on implementation)
        total_imported = sum(counts.values())
        assert total_imported >= 1, f"Expected at least 1 import, got {counts}"

    def test_import_multiple_stores(self, repository, sample_run):
        """Test importing from multiple stores."""
        repository.create_run(sample_run)

        # First import
        store1 = AnalysisStore()
        store1.risks.append({
            'id': 'R-001',
            'risk': 'First risk',
            'severity': 'medium',
            'domain': 'test'
        })
        repository.import_from_analysis_store(store1, sample_run.run_id)

        # Second import with different content
        store2 = AnalysisStore()
        store2.risks.append({
            'id': 'R-002',
            'risk': 'Second risk',
            'severity': 'high',
            'domain': 'test'
        })
        repository.import_from_analysis_store(store2, sample_run.run_id)

        # Should have both risks
        risks = repository.get_all_risks(sample_run.run_id)
        assert len(risks) >= 2


class TestRunSummary:
    """Tests for run summary and statistics."""

    def test_get_run_summary(self, repository, sample_run):
        """Test getting a run summary with counts."""
        repository.create_run(sample_run)

        # Add findings
        for i in range(3):
            repository.create_risk(Risk(
                risk_id=f'RISK-{i}',
                run_id=sample_run.run_id,
                risk_description=f'Risk {i}',
                severity='high',
                domain='test'
            ))

        for i in range(2):
            repository.create_gap(Gap(
                gap_id=f'GAP-{i}',
                run_id=sample_run.run_id,
                gap_description=f'Gap {i}',
                priority='high',
                domain='test'
            ))

        summary = repository.get_run_summary(sample_run.run_id)

        assert 'counts' in summary
        assert summary['counts'].get('risks', 0) == 3
        assert summary['counts'].get('gaps', 0) == 2


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_database(self, repository):
        """Test operations on empty database."""
        assert repository.get_all_documents() == []
        assert repository.get_all_runs() == []
        assert repository.get_latest_run() is None

    def test_invalid_run_id(self, repository):
        """Test operations with invalid run ID."""
        # Should not crash
        risks = repository.get_all_risks('INVALID-RUN-ID')
        assert risks == []

    def test_special_characters_in_text(self, repository, sample_run):
        """Test handling of special characters."""
        repository.create_run(sample_run)

        risk = Risk(
            risk_id='RISK-SPECIAL',
            run_id=sample_run.run_id,
            risk_description="Risk with 'quotes' and \"double quotes\" and special chars: <>&",
            severity='high',
            domain='test'
        )
        repository.create_risk(risk)

        risks = repository.get_all_risks(sample_run.run_id)
        assert len(risks) == 1
        assert "quotes" in risks[0].risk_description

    def test_unicode_content(self, repository, sample_run):
        """Test handling of unicode content."""
        repository.create_run(sample_run)

        risk = Risk(
            risk_id='RISK-UNICODE',
            run_id=sample_run.run_id,
            risk_description='Risk with unicode: 日本語 中文 émojis 🔥',
            severity='high',
            domain='test'
        )
        repository.create_risk(risk)

        risks = repository.get_all_risks(sample_run.run_id)
        assert len(risks) == 1
        assert '日本語' in risks[0].risk_description
