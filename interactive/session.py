"""
Session management for interactive CLI.

Holds the current state including FactStore, ReasoningStore,
modification history, and deal context.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import copy

from tools_v2.fact_store import FactStore
from tools_v2.reasoning_tools import ReasoningStore


@dataclass
class Modification:
    """Record of a single modification."""
    timestamp: str
    item_type: str  # 'risk', 'work_item', 'fact', 'gap', etc.
    item_id: str
    field: str
    old_value: Any
    new_value: Any

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "item_type": self.item_type,
            "item_id": self.item_id,
            "field": self.field,
            "old_value": self.old_value,
            "new_value": self.new_value
        }


class Session:
    """
    Holds state for an interactive CLI session.

    Manages:
    - FactStore with extracted facts
    - ReasoningStore with findings
    - Modification history for undo support
    - Deal context
    - Unsaved changes tracking
    """

    def __init__(
        self,
        fact_store: Optional[FactStore] = None,
        reasoning_store: Optional[ReasoningStore] = None,
        deal_context: Optional[Dict] = None
    ):
        self.fact_store = fact_store or FactStore()
        self.reasoning_store = reasoning_store or ReasoningStore(fact_store=self.fact_store)
        self.deal_context = deal_context or {}

        self.modifications: List[Modification] = []
        self._last_save_modification_count = 0
        self.created_at = datetime.now().isoformat()
        self.source_files: Dict[str, str] = {}  # Track where data was loaded from

    @property
    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved modifications."""
        return len(self.modifications) > self._last_save_modification_count

    @property
    def unsaved_change_count(self) -> int:
        """Number of unsaved changes."""
        return len(self.modifications) - self._last_save_modification_count

    def mark_saved(self):
        """Mark current state as saved."""
        self._last_save_modification_count = len(self.modifications)

    def record_modification(
        self,
        item_type: str,
        item_id: str,
        field: str,
        old_value: Any,
        new_value: Any
    ):
        """Record a modification for history/undo."""
        mod = Modification(
            timestamp=datetime.now().isoformat(),
            item_type=item_type,
            item_id=item_id,
            field=field,
            old_value=old_value,
            new_value=new_value
        )
        self.modifications.append(mod)

    def undo_last(self) -> Optional[Modification]:
        """
        Undo the last modification.

        Returns the undone modification, or None if nothing to undo.
        """
        if not self.modifications:
            return None

        mod = self.modifications.pop()

        # Apply the undo based on item type
        if mod.item_type == 'risk':
            self._undo_risk_modification(mod)
        elif mod.item_type == 'work_item':
            self._undo_work_item_modification(mod)
        elif mod.item_type == 'strategic_consideration':
            self._undo_strategic_modification(mod)
        elif mod.item_type == 'recommendation':
            self._undo_recommendation_modification(mod)

        return mod

    def _undo_risk_modification(self, mod: Modification):
        """Undo a risk modification."""
        for risk in self.reasoning_store.risks:
            if risk.finding_id == mod.item_id:
                setattr(risk, mod.field, mod.old_value)
                break

    def _undo_work_item_modification(self, mod: Modification):
        """Undo a work item modification."""
        for wi in self.reasoning_store.work_items:
            if wi.finding_id == mod.item_id:
                setattr(wi, mod.field, mod.old_value)
                break

    def _undo_strategic_modification(self, mod: Modification):
        """Undo a strategic consideration modification."""
        for sc in self.reasoning_store.strategic_considerations:
            if sc.finding_id == mod.item_id:
                setattr(sc, mod.field, mod.old_value)
                break

    def _undo_recommendation_modification(self, mod: Modification):
        """Undo a recommendation modification."""
        for rec in self.reasoning_store.recommendations:
            if rec.finding_id == mod.item_id:
                setattr(rec, mod.field, mod.old_value)
                break

    # --- Getters for findings ---

    def get_risk(self, risk_id: str) -> Optional[Any]:
        """Get a risk by ID."""
        for risk in self.reasoning_store.risks:
            if risk.finding_id == risk_id:
                return risk
        return None

    def get_work_item(self, wi_id: str) -> Optional[Any]:
        """Get a work item by ID."""
        for wi in self.reasoning_store.work_items:
            if wi.finding_id == wi_id:
                return wi
        return None

    def get_strategic_consideration(self, sc_id: str) -> Optional[Any]:
        """Get a strategic consideration by ID."""
        for sc in self.reasoning_store.strategic_considerations:
            if sc.finding_id == sc_id:
                return sc
        return None

    def get_recommendation(self, rec_id: str) -> Optional[Any]:
        """Get a recommendation by ID."""
        for rec in self.reasoning_store.recommendations:
            if rec.finding_id == rec_id:
                return rec
        return None

    def get_fact(self, fact_id: str) -> Optional[Any]:
        """Get a fact by ID."""
        return self.fact_store.get_fact(fact_id)

    def get_gap(self, gap_id: str) -> Optional[Any]:
        """Get a gap by ID."""
        for gap in self.fact_store.gaps:
            if gap.gap_id == gap_id:
                return gap
        return None

    def get_item_by_id(self, item_id: str) -> Optional[tuple]:
        """
        Get any item by ID, returns (type, item) tuple.

        ID prefixes:
        - R-XXX: Risk
        - WI-XXX: Work Item
        - SC-XXX: Strategic Consideration
        - REC-XXX: Recommendation
        - F-XXX-XXX: Fact
        - G-XXX-XXX: Gap
        """
        if item_id.startswith('R-'):
            item = self.get_risk(item_id)
            return ('risk', item) if item else None
        elif item_id.startswith('WI-'):
            item = self.get_work_item(item_id)
            return ('work_item', item) if item else None
        elif item_id.startswith('SC-'):
            item = self.get_strategic_consideration(item_id)
            return ('strategic_consideration', item) if item else None
        elif item_id.startswith('REC-'):
            item = self.get_recommendation(item_id)
            return ('recommendation', item) if item else None
        elif item_id.startswith('F-'):
            item = self.get_fact(item_id)
            return ('fact', item) if item else None
        elif item_id.startswith('G-'):
            item = self.get_gap(item_id)
            return ('gap', item) if item else None
        return None

    # --- Modification methods ---

    def adjust_risk(self, risk_id: str, field: str, new_value: Any) -> bool:
        """
        Adjust a field on a risk.

        Valid fields: severity, category, mitigation, integration_dependent
        """
        risk = self.get_risk(risk_id)
        if not risk:
            return False

        if not hasattr(risk, field):
            return False

        old_value = getattr(risk, field)
        setattr(risk, field, new_value)
        self.record_modification('risk', risk_id, field, old_value, new_value)
        return True

    def adjust_work_item(self, wi_id: str, field: str, new_value: Any) -> bool:
        """
        Adjust a field on a work item.

        Valid fields: phase, priority, owner_type, cost_estimate
        """
        wi = self.get_work_item(wi_id)
        if not wi:
            return False

        if not hasattr(wi, field):
            return False

        old_value = getattr(wi, field)
        setattr(wi, field, new_value)
        self.record_modification('work_item', wi_id, field, old_value, new_value)
        return True

    def add_deal_context(self, context_text: str):
        """Add or update deal context."""
        if 'notes' not in self.deal_context:
            self.deal_context['notes'] = []
        self.deal_context['notes'].append({
            'text': context_text,
            'added_at': datetime.now().isoformat()
        })

    def clear_deal_context(self):
        """Clear all deal context."""
        self.deal_context = {}

    # --- Summary methods ---

    def get_summary(self) -> Dict:
        """Get a summary of current session state."""
        return {
            "facts": len(self.fact_store.facts),
            "gaps": len(self.fact_store.gaps),
            "risks": len(self.reasoning_store.risks),
            "work_items": len(self.reasoning_store.work_items),
            "strategic_considerations": len(self.reasoning_store.strategic_considerations),
            "recommendations": len(self.reasoning_store.recommendations),
            "modifications": len(self.modifications),
            "unsaved_changes": self.unsaved_change_count,
            "has_deal_context": bool(self.deal_context),
            "domains_with_facts": self._get_domains_with_facts(),
            "risk_summary": self._get_risk_summary(),
            "cost_summary": self._get_cost_summary()
        }

    def _get_domains_with_facts(self) -> List[str]:
        """Get list of domains that have facts."""
        domains = set()
        for fact in self.fact_store.facts:
            domains.add(fact.domain)
        return sorted(list(domains))

    def _get_risk_summary(self) -> Dict[str, int]:
        """Get risk count by severity."""
        summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for risk in self.reasoning_store.risks:
            if risk.severity in summary:
                summary[risk.severity] += 1
        return summary

    def _get_cost_summary(self) -> Dict[str, Dict[str, int]]:
        """Get cost summary by phase."""
        from tools_v2.reasoning_tools import COST_RANGE_VALUES

        by_phase = {
            "Day_1": {"low": 0, "high": 0, "count": 0},
            "Day_100": {"low": 0, "high": 0, "count": 0},
            "Post_100": {"low": 0, "high": 0, "count": 0}
        }

        for wi in self.reasoning_store.work_items:
            phase = wi.phase
            if phase in by_phase and wi.cost_estimate in COST_RANGE_VALUES:
                cost_range = COST_RANGE_VALUES[wi.cost_estimate]
                by_phase[phase]["low"] += cost_range["low"]
                by_phase[phase]["high"] += cost_range["high"]
                by_phase[phase]["count"] += 1

        return by_phase

    # --- Load/Save ---

    @classmethod
    def load_from_files(
        cls,
        facts_file: Optional[Path] = None,
        findings_file: Optional[Path] = None,
        deal_context_file: Optional[Path] = None
    ) -> 'Session':
        """
        Load a session from output files.

        Args:
            facts_file: Path to facts JSON file
            findings_file: Path to findings JSON file
            deal_context_file: Path to deal context JSON file

        Returns:
            New Session instance
        """
        fact_store = FactStore()
        reasoning_store = None
        deal_context = {}
        source_files = {}

        # Load facts
        if facts_file and Path(facts_file).exists():
            fact_store = FactStore.load(str(facts_file))
            source_files['facts'] = str(facts_file)

        # Load findings
        if findings_file and Path(findings_file).exists():
            reasoning_store = cls._load_findings_to_store(findings_file, fact_store)
            source_files['findings'] = str(findings_file)
        else:
            reasoning_store = ReasoningStore(fact_store=fact_store)

        # Load deal context
        if deal_context_file and Path(deal_context_file).exists():
            with open(deal_context_file) as f:
                deal_context = json.load(f)
            source_files['deal_context'] = str(deal_context_file)

        session = cls(
            fact_store=fact_store,
            reasoning_store=reasoning_store,
            deal_context=deal_context
        )
        session.source_files = source_files

        return session

    @classmethod
    def _load_findings_to_store(cls, findings_file: Path, fact_store: FactStore) -> ReasoningStore:
        """Load findings from JSON into a ReasoningStore."""
        store = ReasoningStore(fact_store=fact_store)

        with open(findings_file) as f:
            data = json.load(f)

        # Handle both single-domain and multi-domain formats
        if isinstance(data, dict):
            # Check if it's multi-domain format (keys are domain names)
            if any(k in data for k in ['infrastructure', 'network', 'cybersecurity', 'applications', 'identity_access', 'organization']):
                # Multi-domain format
                for domain, domain_data in data.items():
                    if isinstance(domain_data, dict) and 'findings' in domain_data:
                        cls._add_findings_to_store(store, domain_data['findings'], domain)
            elif 'findings' in data:
                # Single-domain format
                cls._add_findings_to_store(store, data['findings'], data.get('domain', 'unknown'))

        return store

    @classmethod
    def _add_findings_to_store(cls, store: ReasoningStore, findings: Dict, default_domain: str):
        """Add findings dict to store."""
        # Add risks
        for risk in findings.get('risks', []):
            store.add_risk(
                domain=risk.get('domain', default_domain),
                title=risk['title'],
                description=risk['description'],
                category=risk.get('category', 'general'),
                severity=risk.get('severity', 'medium'),
                integration_dependent=risk.get('integration_dependent', False),
                mitigation=risk.get('mitigation', ''),
                based_on_facts=risk.get('based_on_facts', []),
                confidence=risk.get('confidence', 'medium'),
                reasoning=risk.get('reasoning', '')
            )

        # Add work items
        for wi in findings.get('work_items', []):
            store.add_work_item(
                domain=wi.get('domain', default_domain),
                title=wi['title'],
                description=wi['description'],
                phase=wi.get('phase', 'Day_100'),
                priority=wi.get('priority', 'medium'),
                owner_type=wi.get('owner_type', 'target'),
                triggered_by=wi.get('triggered_by', []),
                based_on_facts=wi.get('based_on_facts', []),
                confidence=wi.get('confidence', 'medium'),
                reasoning=wi.get('reasoning', ''),
                cost_estimate=wi.get('cost_estimate', '25k_to_100k'),
                triggered_by_risks=wi.get('triggered_by_risks', []),
                dependencies=wi.get('dependencies', [])
            )

        # Add strategic considerations
        for sc in findings.get('strategic_considerations', []):
            store.add_strategic_consideration(
                domain=sc.get('domain', default_domain),
                title=sc['title'],
                description=sc['description'],
                lens=sc.get('lens', 'operational'),
                implication=sc.get('implication', ''),
                based_on_facts=sc.get('based_on_facts', []),
                confidence=sc.get('confidence', 'medium'),
                reasoning=sc.get('reasoning', '')
            )

        # Add recommendations
        for rec in findings.get('recommendations', []):
            store.add_recommendation(
                domain=rec.get('domain', default_domain),
                title=rec['title'],
                description=rec['description'],
                action_type=rec.get('action_type', 'investigate'),
                urgency=rec.get('urgency', 'medium'),
                rationale=rec.get('rationale', ''),
                based_on_facts=rec.get('based_on_facts', []),
                confidence=rec.get('confidence', 'medium'),
                reasoning=rec.get('reasoning', '')
            )

    def save_to_files(self, output_dir: Path, timestamp: Optional[str] = None) -> Dict[str, Path]:
        """
        Save current session state to files.

        Returns dict mapping file type to path.
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        saved_files = {}

        # Save facts
        facts_file = output_dir / f"facts_{timestamp}.json"
        self.fact_store.save(str(facts_file))
        saved_files['facts'] = facts_file

        # Save findings
        findings_file = output_dir / f"findings_{timestamp}.json"
        findings_data = self.reasoning_store.get_all_findings()
        with open(findings_file, 'w') as f:
            json.dump(findings_data, f, indent=2, default=str)
        saved_files['findings'] = findings_file

        # Save deal context if present
        if self.deal_context:
            context_file = output_dir / f"deal_context_{timestamp}.json"
            with open(context_file, 'w') as f:
                json.dump(self.deal_context, f, indent=2)
            saved_files['deal_context'] = context_file

        # Save modification history
        if self.modifications:
            mods_file = output_dir / f"modifications_{timestamp}.json"
            with open(mods_file, 'w') as f:
                json.dump([m.to_dict() for m in self.modifications], f, indent=2)
            saved_files['modifications'] = mods_file

        self.mark_saved()

        return saved_files
