"""
Data Models for IT Due Diligence Agent Storage Layer

Point 45 of 115PP: Data classes for each entity type.

These models provide:
- Type safety for database operations
- Serialization/deserialization
- Validation
- Conversion between AnalysisStore format and database format
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import uuid


def generate_id(prefix: str) -> str:
    """Generate unique ID with prefix"""
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def now_iso() -> str:
    """Get current timestamp in ISO format"""
    return datetime.now().isoformat()


@dataclass
class Document:
    """
    Source document tracking (Points 34, 36-39).

    Tracks VDR documents, meeting transcripts, and other sources.
    """
    document_id: str
    document_name: str
    document_type: str = "vdr"  # vdr, meeting_transcript, email, other
    document_path: Optional[str] = None
    page_count: Optional[int] = None
    ingested_date: str = field(default_factory=now_iso)
    last_updated: str = field(default_factory=now_iso)
    file_hash: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, name: str, doc_type: str = "vdr", path: str = None, **kwargs) -> "Document":
        return cls(
            document_id=generate_id("DOC"),
            document_name=name,
            document_type=doc_type,
            document_path=path,
            **kwargs
        )

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['metadata'] = json.dumps(d['metadata'])
        return d

    @classmethod
    def from_row(cls, row: Dict) -> "Document":
        data = dict(row)
        if data.get('metadata'):
            data['metadata'] = json.loads(data['metadata'])
        return cls(**data)


@dataclass
class AnalysisRun:
    """
    Analysis session tracking (Point 35).

    Tracks each analysis run for iterative analysis support.
    """
    run_id: str
    run_name: Optional[str] = None
    started_at: str = field(default_factory=now_iso)
    completed_at: Optional[str] = None
    mode: str = "fresh"  # fresh, incremental
    status: str = "in_progress"  # in_progress, completed, failed
    deal_context: Dict[str, Any] = field(default_factory=dict)
    documents_analyzed: List[str] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, name: str = None, mode: str = "fresh", deal_context: Dict = None) -> "AnalysisRun":
        return cls(
            run_id=generate_id("RUN"),
            run_name=name or f"Analysis {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            mode=mode,
            deal_context=deal_context or {}
        )

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['deal_context'] = json.dumps(d['deal_context'])
        d['documents_analyzed'] = json.dumps(d['documents_analyzed'])
        d['summary'] = json.dumps(d['summary'])
        return d

    @classmethod
    def from_row(cls, row: Dict) -> "AnalysisRun":
        data = dict(row)
        for field_name in ['deal_context', 'documents_analyzed', 'summary']:
            if data.get(field_name):
                data[field_name] = json.loads(data[field_name])
        return cls(**data)


@dataclass
class SourceEvidence:
    """
    Common source evidence structure (Points 40-43).

    Used for attribution across all finding types.
    """
    exact_quote: Optional[str] = None
    source_section: Optional[str] = None
    evidence_type: str = "direct_statement"  # direct_statement, logical_inference, pattern_based
    confidence_level: str = "medium"  # high, medium, low

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "SourceEvidence":
        if not data:
            return cls()
        # Handle case where data might be a string instead of dict
        if not isinstance(data, dict):
            return cls()
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class InventoryItem:
    """
    Current state inventory entry (Point 27).

    Captures what exists in the target environment.
    """
    item_id: str
    run_id: str
    domain: str
    category: str
    item_name: str
    description: Optional[str] = None
    status: str = "documented"  # documented, partial, gap
    maturity: Optional[str] = None  # low, medium, high
    standalone_viability: Optional[str] = None  # viable, constrained, high_risk
    key_characteristics: List[str] = field(default_factory=list)
    source_document_id: Optional[str] = None
    source_page: Optional[int] = None
    source_section: Optional[str] = None
    source_evidence: Optional[SourceEvidence] = None
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['key_characteristics'] = json.dumps(d['key_characteristics'])
        d['source_evidence'] = json.dumps(d['source_evidence']) if d['source_evidence'] else None
        return d

    @classmethod
    def from_row(cls, row: Dict) -> "InventoryItem":
        data = dict(row)
        if data.get('key_characteristics'):
            data['key_characteristics'] = json.loads(data['key_characteristics'])
        if data.get('source_evidence'):
            data['source_evidence'] = SourceEvidence.from_dict(json.loads(data['source_evidence']))
        return cls(**data)

    @classmethod
    def from_analysis_store(cls, store_item: Dict, run_id: str) -> "InventoryItem":
        """Convert from AnalysisStore format"""
        source_evidence = None
        if store_item.get('source_evidence'):
            source_evidence = SourceEvidence.from_dict(store_item['source_evidence'])

        return cls(
            item_id=store_item.get('id', generate_id('CS')),
            run_id=run_id,
            domain=store_item.get('domain', 'unknown'),
            category=store_item.get('category', 'general'),
            item_name=store_item.get('summary', '')[:200],
            description=store_item.get('summary'),
            status='documented',
            maturity=store_item.get('maturity'),
            standalone_viability=store_item.get('standalone_viability'),
            key_characteristics=store_item.get('key_characteristics', []),
            source_evidence=source_evidence
        )


@dataclass
class Risk:
    """
    Risk finding (Point 28).

    Captures identified risks with attribution.
    """
    risk_id: str
    run_id: str
    domain: str
    risk_description: str
    trigger_description: Optional[str] = None
    severity: str = "medium"
    likelihood: str = "medium"
    risk_type: Optional[str] = None
    integration_dependent: bool = True
    standalone_exposure: Optional[str] = None
    deal_impact: List[str] = field(default_factory=list)
    impact_description: Optional[str] = None
    mitigation: Optional[str] = None
    cost_impact_estimate: Optional[str] = None
    risk_score: Optional[float] = None
    priority_rank: Optional[int] = None
    source_type: str = "document"
    source_document_id: Optional[str] = None
    source_page: Optional[int] = None
    source_section: Optional[str] = None
    speaker_name: Optional[str] = None
    statement_date: Optional[str] = None
    confidence_level: str = "medium"
    source_evidence: Optional[SourceEvidence] = None
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['deal_impact'] = json.dumps(d['deal_impact'])
        d['integration_dependent'] = 1 if d['integration_dependent'] else 0
        d['source_evidence'] = json.dumps(d['source_evidence']) if d['source_evidence'] else None
        return d

    @classmethod
    def from_row(cls, row: Dict) -> "Risk":
        data = dict(row)
        if data.get('deal_impact'):
            data['deal_impact'] = json.loads(data['deal_impact'])
        data['integration_dependent'] = bool(data.get('integration_dependent', 1))
        if data.get('source_evidence'):
            data['source_evidence'] = SourceEvidence.from_dict(json.loads(data['source_evidence']))
        return cls(**data)

    @classmethod
    def from_analysis_store(cls, store_item: Dict, run_id: str) -> "Risk":
        """Convert from AnalysisStore format"""
        source_evidence = None
        if store_item.get('source_evidence'):
            source_evidence = SourceEvidence.from_dict(store_item['source_evidence'])

        return cls(
            risk_id=store_item.get('id', generate_id('R')),
            run_id=run_id,
            domain=store_item.get('domain', 'unknown'),
            risk_description=store_item.get('risk', ''),
            trigger_description=store_item.get('trigger'),
            severity=store_item.get('severity', 'medium'),
            likelihood=store_item.get('likelihood', 'medium'),
            risk_type=store_item.get('risk_type'),
            integration_dependent=store_item.get('integration_dependent', True),
            standalone_exposure=store_item.get('standalone_exposure'),
            deal_impact=store_item.get('deal_impact', []),
            impact_description=store_item.get('impact_description'),
            mitigation=store_item.get('mitigation'),
            cost_impact_estimate=store_item.get('cost_impact_estimate'),
            risk_score=store_item.get('risk_score'),
            priority_rank=store_item.get('priority_rank'),
            source_evidence=source_evidence,
            confidence_level=source_evidence.confidence_level if source_evidence else 'medium'
        )


@dataclass
class Gap:
    """
    Knowledge gap (Point 29).

    Tracks missing information that needs to be obtained.
    """
    gap_id: str
    run_id: str
    domain: str
    gap_description: str
    why_needed: Optional[str] = None
    priority: str = "medium"
    gap_type: Optional[str] = None  # missing_document, incomplete_detail, unclear_statement, unstated_critical
    suggested_source: Optional[str] = None
    cost_impact: Optional[str] = None
    question_status: str = "not_asked"  # not_asked, question_drafted, sent, answered
    source_type: str = "document"
    source_document_id: Optional[str] = None
    source_section: Optional[str] = None
    confidence_level: str = "high"
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_row(cls, row: Dict) -> "Gap":
        return cls(**dict(row))

    @classmethod
    def from_analysis_store(cls, store_item: Dict, run_id: str) -> "Gap":
        """Convert from AnalysisStore format"""
        return cls(
            gap_id=store_item.get('id', generate_id('G')),
            run_id=run_id,
            domain=store_item.get('domain', 'unknown'),
            gap_description=store_item.get('gap', ''),
            why_needed=store_item.get('why_needed'),
            priority=store_item.get('priority', 'medium'),
            gap_type=store_item.get('gap_type'),
            suggested_source=store_item.get('suggested_source'),
            cost_impact=store_item.get('cost_impact')
        )


@dataclass
class Assumption:
    """
    Analysis assumption (Point 30).

    Tracks assumptions made during analysis with validation status.
    """
    assumption_id: str
    run_id: str
    domain: str
    assumption_text: str
    basis: Optional[str] = None
    confidence: str = "medium"
    impact: Optional[str] = None
    validation_needed: Optional[str] = None
    validation_status: str = "unvalidated"  # unvalidated, validated, invalidated
    supporting_quote: Optional[str] = None
    source_type: str = "document"
    source_document_id: Optional[str] = None
    source_section: Optional[str] = None
    speaker_name: Optional[str] = None
    statement_date: Optional[str] = None
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_row(cls, row: Dict) -> "Assumption":
        return cls(**dict(row))

    @classmethod
    def from_analysis_store(cls, store_item: Dict, run_id: str) -> "Assumption":
        """Convert from AnalysisStore format"""
        return cls(
            assumption_id=store_item.get('id', generate_id('A')),
            run_id=run_id,
            domain=store_item.get('domain', 'unknown'),
            assumption_text=store_item.get('assumption', ''),
            basis=store_item.get('basis'),
            confidence=store_item.get('confidence', 'medium'),
            impact=store_item.get('impact'),
            validation_needed=store_item.get('validation_needed'),
            supporting_quote=store_item.get('supporting_quote')
        )


@dataclass
class WorkItem:
    """
    Integration work item (Point 31).

    Tasks needed for integration, organized by phase.
    """
    work_item_id: str
    run_id: str
    domain: str
    title: str
    description: Optional[str] = None
    category: Optional[str] = None  # migration, integration, remediation, assessment, decommission, security, compliance
    phase: str = "Day_100"  # Day_1, Day_100, Post_100, Optional
    phase_rationale: Optional[str] = None
    effort_estimate: Optional[str] = None
    cost_estimate_range: Optional[str] = None
    depends_on: List[str] = field(default_factory=list)
    skills_required: List[str] = field(default_factory=list)
    triggered_by: List[str] = field(default_factory=list)
    priority_score: Optional[int] = None
    source_document_id: Optional[str] = None
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['depends_on'] = json.dumps(d['depends_on'])
        d['skills_required'] = json.dumps(d['skills_required'])
        d['triggered_by'] = json.dumps(d['triggered_by'])
        return d

    @classmethod
    def from_row(cls, row: Dict) -> "WorkItem":
        data = dict(row)
        for field_name in ['depends_on', 'skills_required', 'triggered_by']:
            if data.get(field_name):
                data[field_name] = json.loads(data[field_name])
        return cls(**data)

    @classmethod
    def from_analysis_store(cls, store_item: Dict, run_id: str) -> "WorkItem":
        """Convert from AnalysisStore format"""
        return cls(
            work_item_id=store_item.get('id', generate_id('WI')),
            run_id=run_id,
            domain=store_item.get('domain', 'unknown'),
            title=store_item.get('title', ''),
            description=store_item.get('description'),
            category=store_item.get('category'),
            phase=store_item.get('phase', 'Day_100'),
            phase_rationale=store_item.get('phase_rationale'),
            effort_estimate=store_item.get('effort_estimate'),
            cost_estimate_range=store_item.get('cost_estimate_range'),
            depends_on=store_item.get('depends_on', []),
            skills_required=store_item.get('skills_required', []),
            triggered_by=store_item.get('triggered_by', []),
            priority_score=store_item.get('priority_score')
        )


@dataclass
class Recommendation:
    """
    Strategic recommendation (Point 32).

    Deal team recommendations with rationale.
    """
    recommendation_id: str
    run_id: str
    domain: str
    recommendation_text: str
    rationale: Optional[str] = None
    priority: str = "medium"
    timing: Optional[str] = None  # pre_close, day_1, first_90_days, ongoing
    investment_required: Optional[str] = None
    driven_by: List[str] = field(default_factory=list)
    source_document_id: Optional[str] = None
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['driven_by'] = json.dumps(d['driven_by'])
        return d

    @classmethod
    def from_row(cls, row: Dict) -> "Recommendation":
        data = dict(row)
        if data.get('driven_by'):
            data['driven_by'] = json.loads(data['driven_by'])
        return cls(**data)

    @classmethod
    def from_analysis_store(cls, store_item: Dict, run_id: str) -> "Recommendation":
        """Convert from AnalysisStore format"""
        return cls(
            recommendation_id=store_item.get('id', generate_id('REC')),
            run_id=run_id,
            domain=store_item.get('domain', 'unknown'),
            recommendation_text=store_item.get('recommendation', ''),
            rationale=store_item.get('rationale'),
            priority=store_item.get('priority', 'medium'),
            timing=store_item.get('timing'),
            investment_required=store_item.get('investment_required'),
            driven_by=store_item.get('driven_by', [])
        )


@dataclass
class StrategicConsideration:
    """
    Strategic consideration (Point 33).

    Deal-relevant implications and observations.
    """
    consideration_id: str
    run_id: str
    domain: str
    theme: str
    observation: str
    implication: Optional[str] = None
    deal_relevance: List[str] = field(default_factory=list)
    buyer_alignment: Optional[str] = None  # aligned, partial, misaligned, unknown
    source_type: str = "document"
    source_document_id: Optional[str] = None
    source_section: Optional[str] = None
    source_evidence: Optional[SourceEvidence] = None
    speaker_name: Optional[str] = None
    statement_date: Optional[str] = None
    confidence_level: str = "medium"
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['deal_relevance'] = json.dumps(d['deal_relevance'])
        d['source_evidence'] = json.dumps(d['source_evidence']) if d['source_evidence'] else None
        return d

    @classmethod
    def from_row(cls, row: Dict) -> "StrategicConsideration":
        data = dict(row)
        if data.get('deal_relevance'):
            data['deal_relevance'] = json.loads(data['deal_relevance'])
        if data.get('source_evidence'):
            data['source_evidence'] = SourceEvidence.from_dict(json.loads(data['source_evidence']))
        return cls(**data)

    @classmethod
    def from_analysis_store(cls, store_item: Dict, run_id: str) -> "StrategicConsideration":
        """Convert from AnalysisStore format"""
        source_evidence = None
        if store_item.get('source_evidence'):
            source_evidence = SourceEvidence.from_dict(store_item['source_evidence'])

        return cls(
            consideration_id=store_item.get('id', generate_id('SC')),
            run_id=run_id,
            domain=store_item.get('domain', 'unknown'),
            theme=store_item.get('theme', ''),
            observation=store_item.get('observation', ''),
            implication=store_item.get('implication'),
            deal_relevance=store_item.get('deal_relevance', []),
            buyer_alignment=store_item.get('buyer_alignment'),
            source_evidence=source_evidence,
            confidence_level=source_evidence.confidence_level if source_evidence else 'medium'
        )


@dataclass
class Question:
    """
    Seller question linked to gaps/assumptions.

    Tracks questions sent to seller and their answers.
    """
    question_id: str
    run_id: str
    question_text: str
    linked_gap_id: Optional[str] = None
    linked_assumption_id: Optional[str] = None
    context: Optional[str] = None
    priority: str = "medium"
    status: str = "draft"  # draft, ready, sent, answered, closed
    sent_date: Optional[str] = None
    answer_text: Optional[str] = None
    answer_date: Optional[str] = None
    answer_source: Optional[str] = None  # email, call, document
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)

    @classmethod
    def create(cls, run_id: str, question: str, gap_id: str = None, **kwargs) -> "Question":
        return cls(
            question_id=generate_id("Q"),
            run_id=run_id,
            question_text=question,
            linked_gap_id=gap_id,
            **kwargs
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_row(cls, row: Dict) -> "Question":
        return cls(**dict(row))
