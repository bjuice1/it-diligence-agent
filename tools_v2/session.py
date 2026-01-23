"""
DD Session Management - State Persistence for Incremental Analysis.

Enables:
- Persist state between runs (facts, findings, narratives)
- Track which documents have been processed
- Incremental updates (process only new docs)
- Deal context management
- Run history and change tracking

Usage:
    # Create new session
    session = DDSession.create("acme_corp_2024", deal_type="carve_out")

    # Add documents and run analysis
    session.add_documents([Path("doc1.pdf"), Path("doc2.pdf")])
    session.run_discovery()
    session.run_reasoning()
    session.save()

    # Later: Resume and add more docs
    session = DDSession.load("acme_corp_2024")
    session.add_documents([Path("doc3.pdf")])  # Only processes new doc
    session.run_discovery()  # Incremental
    session.run_reasoning()  # Re-runs on full fact set
    session.save()
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging

from tools_v2.fact_store import FactStore
from tools_v2.reasoning_tools import ReasoningStore
from tools_v2.narrative_tools import NarrativeStore

logger = logging.getLogger(__name__)


class DealType(Enum):
    """
    Types of buy-side deals with different analysis focus.

    CARVE_OUT: Target is being separated from a parent company.
               Focus on standalone readiness, TSA dependencies, stranded costs.

    BOLT_ON: Target is being integrated into buyer's existing platform.
             Focus on synergies, platform alignment, integration complexity.
    """
    CARVE_OUT = "carve_out"
    BOLT_ON = "bolt_on"

    @classmethod
    def from_string(cls, value: str) -> "DealType":
        """Convert string to DealType, with fallback."""
        normalized = value.lower().replace("-", "_").replace(" ", "_")
        try:
            return cls(normalized)
        except ValueError:
            # Default to bolt_on as it's the more common scenario
            logger.warning(f"Unknown deal type '{value}', defaulting to BOLT_ON")
            return cls.BOLT_ON


# Deal type specific analysis focus
DEAL_TYPE_CONFIG = {
    DealType.CARVE_OUT: {
        "description": "Target separating from parent company - focus on standalone readiness",
        "focus_areas": [
            "tsa_dependencies",
            "stranded_costs",
            "standalone_readiness",
            "parent_services",
            "shared_infrastructure",
            "separation_complexity"
        ],
        "key_questions": [
            "What IT services does target currently receive from parent?",
            "What's the cost to replicate parent services vs. TSA?",
            "Can target operate Day 1 standalone? If not, what's the gap?",
            "What shared infrastructure needs separation (network, identity, apps)?",
            "What contracts are in parent's name that need transfer?",
            "Are there shared systems where data needs to be carved out?"
        ],
        "risk_lens": "Can they operate independently without parent support?",
        "cost_lens": "Stranded cost + standup cost for missing capabilities",
        "day1_priority": "Business continuity without parent",
        "typical_issues": [
            "Shared Active Directory / identity",
            "Parent-provided network connectivity",
            "Shared ERP or financial systems",
            "IT support provided by parent",
            "Licenses in parent's name"
        ]
    },
    DealType.BOLT_ON: {
        "description": "Target integrating into buyer's platform - focus on synergies and alignment",
        "focus_areas": [
            "platform_alignment",
            "integration_complexity",
            "synergies",
            "redundancy",
            "migration_readiness",
            "consolidation_opportunities"
        ],
        "key_questions": [
            "Does target's stack align with buyer's platform?",
            "What can be consolidated for synergy savings?",
            "What's the integration timeline and complexity?",
            "Where are the redundant systems that can be eliminated?",
            "What's the migration path for target's data and users?",
            "Are there integration blockers (legacy systems, technical debt)?"
        ],
        "risk_lens": "Integration friction and synergy realization risk",
        "cost_lens": "Integration cost offset by synergy savings",
        "day1_priority": "Connectivity and basic interoperability",
        "typical_issues": [
            "Platform mismatches (AWS vs Azure, VMware vs Hyper-V)",
            "Application overlap requiring rationalization",
            "Identity integration complexity",
            "Data migration volume and complexity",
            "Network connectivity between environments"
        ]
    }
}


@dataclass
class ProcessedDocument:
    """Track a processed document."""
    filename: str
    file_hash: str  # SHA256 of content for change detection
    processed_at: str
    file_size: int
    fact_count: int = 0  # Facts extracted from this doc
    entity: str = "target"  # "target" or "buyer"


@dataclass
class SessionRun:
    """Track a single analysis run."""
    run_id: str
    started_at: str
    completed_at: Optional[str] = None
    phase: str = "discovery"  # discovery, reasoning, narrative
    domains_processed: List[str] = field(default_factory=list)
    documents_processed: List[str] = field(default_factory=list)
    facts_added: int = 0
    facts_updated: int = 0
    status: str = "running"  # running, completed, failed
    error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)


# Industry hierarchy - maps industry to sub-industries
INDUSTRY_HIERARCHY = {
    "financial_services": {
        "display_name": "Financial Services",
        "sub_industries": [
            ("commercial_banking", "Commercial Banking"),
            ("mortgage_lending", "Mortgage Lending"),
            ("wealth_management", "Wealth Management"),
            ("broker_dealer", "Broker-Dealer"),
            ("credit_union", "Credit Union"),
            ("fintech", "Fintech"),
            ("insurance_services", "Insurance Services"),
        ]
    },
    "healthcare": {
        "display_name": "Healthcare",
        "sub_industries": [
            ("hospital_system", "Hospital System"),
            ("physician_practice", "Physician Practice"),
            ("specialty_clinic", "Specialty Clinic"),
            ("behavioral_health", "Behavioral Health"),
            ("post_acute", "Post-Acute Care"),
            ("healthcare_it", "Healthcare IT/Services"),
        ]
    },
    "manufacturing": {
        "display_name": "Manufacturing",
        "sub_industries": [
            ("discrete", "Discrete Manufacturing"),
            ("process", "Process Manufacturing"),
            ("job_shop", "Job Shop"),
            ("oem", "OEM"),
            ("contract_manufacturing", "Contract Manufacturing"),
        ]
    },
    "retail": {
        "display_name": "Retail",
        "sub_industries": [
            ("brick_mortar", "Brick & Mortar"),
            ("ecommerce", "E-Commerce"),
            ("omnichannel", "Omnichannel"),
            ("grocery", "Grocery"),
            ("specialty_retail", "Specialty Retail"),
        ]
    },
    "insurance": {
        "display_name": "Insurance",
        "sub_industries": [
            ("property_casualty", "Property & Casualty"),
            ("life_annuity", "Life & Annuity"),
            ("health_insurance", "Health Insurance"),
            ("reinsurance", "Reinsurance"),
            ("insurtech", "Insurtech"),
        ]
    },
    # Other industries without sub-industries yet
    "aviation_mro": {"display_name": "Aviation / Aerospace MRO", "sub_industries": []},
    "defense_contractor": {"display_name": "Defense Contractor", "sub_industries": []},
    "life_sciences": {"display_name": "Life Sciences / Pharmaceutical", "sub_industries": []},
    "logistics": {"display_name": "Logistics / Distribution", "sub_industries": []},
    "energy_utilities": {"display_name": "Energy / Utilities", "sub_industries": []},
    "construction": {"display_name": "Construction / Engineering", "sub_industries": []},
    "food_beverage": {"display_name": "Food & Beverage Manufacturing", "sub_industries": []},
    "professional_services": {"display_name": "Professional Services", "sub_industries": []},
    "education": {"display_name": "Education", "sub_industries": []},
    "hospitality": {"display_name": "Hospitality", "sub_industries": []},
}


@dataclass
class IndustryContext:
    """Rich industry context for analysis framing."""
    industry: str
    industry_display: str
    sub_industry: Optional[str] = None
    sub_industry_display: Optional[str] = None
    secondary_industries: List[str] = field(default_factory=list)
    regulatory_frameworks: List[str] = field(default_factory=list)
    key_systems: List[str] = field(default_factory=list)
    risk_elevations: List[str] = field(default_factory=list)
    diligence_questions: List[str] = field(default_factory=list)
    red_flags: List[str] = field(default_factory=list)

    def to_prompt_context(self) -> str:
        """Format industry context for prompt injection."""
        lines = [
            f"## INDUSTRY CONTEXT: {self.industry_display.upper()}",
            "",
        ]

        if self.sub_industry_display:
            lines.append(f"**Sub-Industry:** {self.sub_industry_display}")
            lines.append("")

        if self.secondary_industries:
            lines.append(f"**Also relevant:** {', '.join(self.secondary_industries)}")
            lines.append("")

        if self.regulatory_frameworks:
            lines.extend([
                "### Regulatory Framework",
                "This industry operates under these regulatory requirements:",
            ])
            for reg in self.regulatory_frameworks:
                lines.append(f"- {reg}")
            lines.append("")

        if self.key_systems:
            lines.extend([
                "### Industry-Critical Systems",
                "For this industry, pay special attention to:",
            ])
            for system in self.key_systems:
                lines.append(f"- {system}")
            lines.append("")

        if self.risk_elevations:
            lines.extend([
                "### Elevated Risk Categories",
                "In this industry, these risk categories carry extra weight:",
            ])
            for risk in self.risk_elevations:
                lines.append(f"- {risk}")
            lines.append("")

        if self.diligence_questions:
            lines.extend([
                "### Industry-Specific Questions to Answer",
                "The deal team needs answers to these industry-specific questions:",
            ])
            for q in self.diligence_questions[:10]:  # Top 10
                lines.append(f"- {q}")
            lines.append("")

        if self.red_flags:
            lines.extend([
                "### Red Flags for This Industry",
                "Watch for these industry-specific warning signs:",
            ])
            for flag in self.red_flags[:8]:  # Top 8
                lines.append(f"- {flag}")

        return "\n".join(lines)


@dataclass
class DealContext:
    """Deal context that shapes analysis."""
    target_name: str
    buyer_name: Optional[str] = None
    deal_type: str = "bolt_on"  # carve_out or bolt_on
    industry: Optional[str] = None  # e.g., healthcare, financial_services
    sub_industry: Optional[str] = None  # e.g., commercial_banking, hospital_system
    secondary_industries: List[str] = field(default_factory=list)  # For ambiguous companies
    industry_confirmed: bool = False  # True if user confirmed, False if auto-detected
    deal_size: Optional[str] = None  # small, medium, large, mega
    integration_approach: Optional[str] = None
    timeline_pressure: Optional[str] = None  # normal, accelerated, urgent
    custom_focus_areas: List[str] = field(default_factory=list)
    notes: Optional[str] = None

    # Valid industry keys for reference
    VALID_INDUSTRIES = list(INDUSTRY_HIERARCHY.keys())

    def detect_industry_from_text(self, text: str) -> Optional[str]:
        """
        Auto-detect industry from document text using industry triggers.

        Args:
            text: Document text to analyze

        Returns:
            Detected industry key or None
        """
        try:
            from prompts.shared.industry_application_considerations import detect_industry_from_text
            matches = detect_industry_from_text(text)
            if matches and matches[0][1] >= 3:  # Require at least 3 trigger matches
                detected = matches[0][0]
                logger.info(f"Auto-detected industry: {detected} ({matches[0][1]} matches)")
                return detected
        except ImportError:
            logger.warning("Industry detection module not available")
        return None

    def set_industry(self, industry: str, sub_industry: Optional[str] = None, confirmed: bool = True) -> bool:
        """
        Set industry with validation.

        Args:
            industry: Industry key to set
            sub_industry: Optional sub-industry key
            confirmed: Whether user confirmed this selection

        Returns:
            True if valid and set, False otherwise
        """
        if industry.lower() in self.VALID_INDUSTRIES:
            self.industry = industry.lower()
            self.industry_confirmed = confirmed
            if sub_industry:
                self.sub_industry = sub_industry.lower()
            return True
        logger.warning(f"Invalid industry '{industry}'. Valid options: {self.VALID_INDUSTRIES}")
        return False

    def get_industry_context(self) -> Optional[IndustryContext]:
        """
        Build rich industry context from industry configuration.

        Returns:
            IndustryContext with regulatory frameworks, key systems, questions, etc.
        """
        if not self.industry:
            return None

        try:
            from prompts.shared.industry_application_considerations import (
                INDUSTRY_APPLICATION_CONSIDERATIONS,
                get_industry_considerations
            )

            config = get_industry_considerations(self.industry)
            if not config:
                return None

            hierarchy = INDUSTRY_HIERARCHY.get(self.industry, {})

            # Get sub-industry display name
            sub_display = None
            if self.sub_industry and hierarchy.get("sub_industries"):
                for key, display in hierarchy["sub_industries"]:
                    if key == self.sub_industry:
                        sub_display = display
                        break

            # Extract key information from industry config
            diligence = config.get("diligence_considerations", {})

            return IndustryContext(
                industry=self.industry,
                industry_display=config.get("display_name", self.industry.replace("_", " ").title()),
                sub_industry=self.sub_industry,
                sub_industry_display=sub_display,
                secondary_industries=self.secondary_industries,
                regulatory_frameworks=config.get("compliance_drivers", []),
                key_systems=[app["name"] for app in config.get("expected_applications", {}).values()][:6],
                risk_elevations=self._get_elevated_risks_for_industry(),
                diligence_questions=diligence.get("key_questions", []),
                red_flags=diligence.get("red_flags", []),
            )
        except ImportError:
            logger.warning("Industry considerations module not available")
            return None

    def _get_elevated_risks_for_industry(self) -> List[str]:
        """Get risk categories that should be elevated for this industry."""
        elevations = {
            "financial_services": [
                "Regulatory compliance (SOX, GLBA, BSA/AML)",
                "IT controls and segregation of duties",
                "Data security and privacy",
                "Audit trail integrity",
                "Change management controls",
            ],
            "healthcare": [
                "HIPAA compliance and PHI protection",
                "Clinical system availability",
                "Patient safety systems",
                "BAA coverage for vendors",
                "Audit logging for PHI access",
            ],
            "manufacturing": [
                "OT/SCADA security",
                "Quality system integrity",
                "Supply chain continuity",
                "Safety system availability",
                "Production system uptime",
            ],
            "defense_contractor": [
                "CMMC/NIST 800-171 compliance",
                "CUI protection",
                "Cleared environment security",
                "ITAR/export control",
                "Supply chain security",
            ],
        }
        return elevations.get(self.industry, [])

    def get_analysis_config(self) -> Dict[str, Any]:
        """Get deal-type specific analysis configuration."""
        deal_type_enum = DealType.from_string(self.deal_type)
        config = DEAL_TYPE_CONFIG.get(deal_type_enum, DEAL_TYPE_CONFIG[DealType.BOLT_ON])

        # Add custom focus areas if provided
        if self.custom_focus_areas:
            config = dict(config)  # Copy
            config["focus_areas"] = list(config["focus_areas"]) + self.custom_focus_areas

        return config

    def to_prompt_context(self) -> str:
        """Format deal context for injection into reasoning prompts."""
        config = self.get_analysis_config()
        deal_type_display = self.deal_type.replace('_', ' ').title()

        # Get industry display name from hierarchy
        industry_display = None
        sub_industry_display = None
        if self.industry:
            hierarchy = INDUSTRY_HIERARCHY.get(self.industry, {})
            industry_display = hierarchy.get("display_name", self.industry.replace("_", " ").title())
            if self.sub_industry and hierarchy.get("sub_industries"):
                for key, display in hierarchy["sub_industries"]:
                    if key == self.sub_industry:
                        sub_industry_display = display
                        break

        lines = [
            "## DEAL CONTEXT",
            "",
            f"**Target:** {self.target_name}",
        ]

        if self.buyer_name:
            lines.append(f"**Buyer:** {self.buyer_name}")

        lines.append(f"**Deal Type:** {deal_type_display}")

        if industry_display:
            industry_str = industry_display
            if sub_industry_display:
                industry_str += f" ({sub_industry_display})"
            lines.append(f"**Industry:** {industry_str}")

        lines.extend([
            "",
            "### What This Means",
            config.get('description', ''),
            "",
            "### Analysis Focus Areas",
            f"Given this is a {deal_type_display.lower()} transaction, prioritize these areas:",
        ])

        for area in config["focus_areas"]:
            lines.append(f"- {area.replace('_', ' ').title()}")

        lines.extend([
            "",
            "### Key Questions to Answer",
        ])

        for q in config["key_questions"]:
            lines.append(f"- {q}")

        lines.extend([
            "",
            "### Risk Lens",
            f"Primary question: {config['risk_lens']}",
            "",
            "### Cost Lens",
            config['cost_lens'],
            "",
            "### Day 1 Priority",
            config.get('day1_priority', 'Business continuity'),
        ])

        # Add typical issues to watch for
        typical_issues = config.get('typical_issues', [])
        if typical_issues:
            lines.extend([
                "",
                f"### Common Issues for {deal_type_display} Deals",
                "Watch for these typical challenges:",
            ])
            for issue in typical_issues:
                lines.append(f"- {issue}")

        if self.notes:
            lines.extend(["", "### Additional Deal Notes", self.notes])

        # Add industry-specific context if available
        industry_context = self.get_industry_context()
        if industry_context:
            lines.extend([
                "",
                "---",
                "",
                industry_context.to_prompt_context()
            ])

        return "\n".join(lines)


@dataclass
class SessionState:
    """Complete session state for persistence."""
    session_id: str
    created_at: str
    updated_at: str
    deal_context: DealContext
    processed_documents: List[ProcessedDocument]
    run_history: List[SessionRun]
    current_phase: str = "initialized"  # initialized, discovery, reasoning, narrative, complete

    # Paths to data files (relative to session dir)
    facts_file: str = "facts.json"
    reasoning_file: str = "reasoning.json"
    narratives_file: str = "narratives.json"


class DDSession:
    """
    Manages state for an IT due diligence deal analysis.

    Enables incremental analysis across multiple runs:
    - Tracks which documents have been processed
    - Persists facts, findings, narratives between runs
    - Only processes new/changed documents
    - Maintains deal context throughout
    """

    SESSIONS_DIR = Path("sessions")

    def __init__(
        self,
        session_id: str,
        session_dir: Path,
        state: SessionState,
        fact_store: FactStore,
        reasoning_store: Optional[ReasoningStore] = None,
        narrative_store: Optional[NarrativeStore] = None
    ):
        self.session_id = session_id
        self.session_dir = session_dir
        self.state = state
        self.fact_store = fact_store
        self.reasoning_store = reasoning_store or ReasoningStore(fact_store=fact_store)
        self.narrative_store = narrative_store or NarrativeStore()

        # Pending documents (added but not yet processed)
        self._pending_documents: List[Path] = []
        self._current_run: Optional[SessionRun] = None

        logger.info(f"Session initialized: {session_id}")

    @classmethod
    def create(
        cls,
        session_id: str,
        target_name: str,
        deal_type: str = "platform",
        buyer_name: Optional[str] = None,
        industry: Optional[str] = None,
        sessions_dir: Optional[Path] = None
    ) -> "DDSession":
        """
        Create a new session for a deal.

        Args:
            session_id: Unique identifier (e.g., "acme_corp_2024")
            target_name: Name of target company
            deal_type: Type of deal (carve_out, bolt_on, platform)
            buyer_name: Optional buyer name
            industry: Optional industry vertical
            sessions_dir: Override default sessions directory

        Returns:
            New DDSession instance
        """
        base_dir = sessions_dir or cls.SESSIONS_DIR
        session_dir = base_dir / session_id

        if session_dir.exists():
            raise ValueError(f"Session already exists: {session_id}. Use DDSession.load() to resume.")

        # Create session directory structure
        session_dir.mkdir(parents=True)
        (session_dir / "documents").mkdir()
        (session_dir / "outputs").mkdir()

        # Create deal context
        deal_context = DealContext(
            target_name=target_name,
            buyer_name=buyer_name,
            deal_type=deal_type,
            industry=industry
        )

        # Create initial state
        now = datetime.now().isoformat()
        state = SessionState(
            session_id=session_id,
            created_at=now,
            updated_at=now,
            deal_context=deal_context,
            processed_documents=[],
            run_history=[]
        )

        # Create stores
        fact_store = FactStore()

        session = cls(
            session_id=session_id,
            session_dir=session_dir,
            state=state,
            fact_store=fact_store
        )

        # Save initial state
        session.save()

        logger.info(f"Created new session: {session_id} ({deal_type})")
        return session

    @classmethod
    def load(cls, session_id: str, sessions_dir: Optional[Path] = None) -> "DDSession":
        """
        Load an existing session.

        Args:
            session_id: Session identifier
            sessions_dir: Override default sessions directory

        Returns:
            Loaded DDSession instance
        """
        base_dir = sessions_dir or cls.SESSIONS_DIR
        session_dir = base_dir / session_id

        if not session_dir.exists():
            raise ValueError(f"Session not found: {session_id}")

        state_file = session_dir / "state.json"
        if not state_file.exists():
            raise ValueError(f"Session state file not found: {state_file}")

        # Load state
        with open(state_file) as f:
            state_dict = json.load(f)

        # Reconstruct state objects
        deal_context = DealContext(**state_dict["deal_context"])
        processed_docs = [ProcessedDocument(**d) for d in state_dict["processed_documents"]]
        run_history = [SessionRun(**r) for r in state_dict["run_history"]]

        state = SessionState(
            session_id=state_dict["session_id"],
            created_at=state_dict["created_at"],
            updated_at=state_dict["updated_at"],
            deal_context=deal_context,
            processed_documents=processed_docs,
            run_history=run_history,
            current_phase=state_dict.get("current_phase", "initialized"),
            facts_file=state_dict.get("facts_file", "facts.json"),
            reasoning_file=state_dict.get("reasoning_file", "reasoning.json"),
            narratives_file=state_dict.get("narratives_file", "narratives.json")
        )

        # Load fact store
        facts_path = session_dir / state.facts_file
        if facts_path.exists():
            fact_store = FactStore.load(str(facts_path))
        else:
            fact_store = FactStore()

        # Load reasoning store
        reasoning_store = ReasoningStore(fact_store=fact_store)
        reasoning_path = session_dir / state.reasoning_file
        if reasoning_path.exists():
            reasoning_store.load(str(reasoning_path))

        # Load narrative store
        narrative_store = NarrativeStore()
        narrative_path = session_dir / state.narratives_file
        if narrative_path.exists():
            narrative_store.load(str(narrative_path))

        session = cls(
            session_id=session_id,
            session_dir=session_dir,
            state=state,
            fact_store=fact_store,
            reasoning_store=reasoning_store,
            narrative_store=narrative_store
        )

        logger.info(f"Loaded session: {session_id} ({len(processed_docs)} docs, {len(fact_store.facts)} facts)")
        return session

    @classmethod
    def list_sessions(cls, sessions_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
        """List all available sessions."""
        base_dir = sessions_dir or cls.SESSIONS_DIR

        if not base_dir.exists():
            return []

        sessions = []
        for session_dir in base_dir.iterdir():
            if session_dir.is_dir():
                state_file = session_dir / "state.json"
                if state_file.exists():
                    with open(state_file) as f:
                        state = json.load(f)
                    sessions.append({
                        "session_id": state["session_id"],
                        "target_name": state["deal_context"]["target_name"],
                        "deal_type": state["deal_context"]["deal_type"],
                        "industry": state["deal_context"].get("industry"),
                        "created_at": state["created_at"],
                        "updated_at": state["updated_at"],
                        "current_phase": state.get("current_phase", "unknown"),
                        "document_count": len(state["processed_documents"]),
                        "run_count": len(state["run_history"])
                    })

        return sorted(sessions, key=lambda x: x["updated_at"], reverse=True)

    def save(self):
        """Save current session state to disk."""
        self.state.updated_at = datetime.now().isoformat()

        # Save state
        state_file = self.session_dir / "state.json"
        state_dict = {
            "session_id": self.state.session_id,
            "created_at": self.state.created_at,
            "updated_at": self.state.updated_at,
            "deal_context": asdict(self.state.deal_context),
            "processed_documents": [asdict(d) for d in self.state.processed_documents],
            "run_history": [asdict(r) for r in self.state.run_history],
            "current_phase": self.state.current_phase,
            "facts_file": self.state.facts_file,
            "reasoning_file": self.state.reasoning_file,
            "narratives_file": self.state.narratives_file
        }

        with open(state_file, 'w') as f:
            json.dump(state_dict, f, indent=2)

        # Save fact store
        self.fact_store.save(str(self.session_dir / self.state.facts_file))

        # Save reasoning store if it has content
        if self.reasoning_store.risks or self.reasoning_store.work_items:
            self.reasoning_store.save(str(self.session_dir / self.state.reasoning_file))

        # Save narrative store if it has content
        if self.narrative_store.domain_narratives:
            self.narrative_store.save(str(self.session_dir / self.state.narratives_file))

        logger.info(f"Session saved: {self.session_id}")

    def add_documents(
        self,
        document_paths: List[Path],
        entity: str = "target"
    ) -> Dict[str, List[str]]:
        """
        Add documents to the session for processing.

        Only new or changed documents will be queued for processing.

        Args:
            document_paths: List of paths to documents
            entity: "target" or "buyer"

        Returns:
            Dict with 'new', 'changed', 'unchanged' document lists
        """
        result = {"new": [], "changed": [], "unchanged": []}

        # Build lookup of already processed docs
        processed_lookup = {d.filename: d for d in self.state.processed_documents}

        for doc_path in document_paths:
            if not doc_path.exists():
                logger.warning(f"Document not found: {doc_path}")
                continue

            filename = doc_path.name
            file_hash = self._compute_file_hash(doc_path)

            if filename in processed_lookup:
                existing = processed_lookup[filename]
                if existing.file_hash == file_hash:
                    result["unchanged"].append(filename)
                else:
                    result["changed"].append(filename)
                    self._pending_documents.append(doc_path)
            else:
                result["new"].append(filename)
                self._pending_documents.append(doc_path)

        logger.info(f"Documents queued: {len(result['new'])} new, {len(result['changed'])} changed, {len(result['unchanged'])} unchanged")
        return result

    def get_pending_documents(self) -> List[Path]:
        """Get documents queued for processing."""
        return list(self._pending_documents)

    def get_processed_documents(self) -> List[ProcessedDocument]:
        """Get list of already processed documents."""
        return list(self.state.processed_documents)

    def mark_document_processed(
        self,
        doc_path: Path,
        fact_count: int = 0,
        entity: str = "target"
    ):
        """Mark a document as processed."""
        filename = doc_path.name
        file_hash = self._compute_file_hash(doc_path)
        file_size = doc_path.stat().st_size

        # Remove from pending
        self._pending_documents = [p for p in self._pending_documents if p.name != filename]

        # Update or add to processed list
        existing_idx = None
        for i, d in enumerate(self.state.processed_documents):
            if d.filename == filename:
                existing_idx = i
                break

        processed_doc = ProcessedDocument(
            filename=filename,
            file_hash=file_hash,
            processed_at=datetime.now().isoformat(),
            file_size=file_size,
            fact_count=fact_count,
            entity=entity
        )

        if existing_idx is not None:
            self.state.processed_documents[existing_idx] = processed_doc
        else:
            self.state.processed_documents.append(processed_doc)

    def start_run(self, phase: str, domains: List[str]) -> SessionRun:
        """Start a new analysis run."""
        run_id = f"{phase}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self._current_run = SessionRun(
            run_id=run_id,
            started_at=datetime.now().isoformat(),
            phase=phase,
            domains_processed=domains,
            documents_processed=[p.name for p in self._pending_documents]
        )

        return self._current_run

    def complete_run(
        self,
        facts_added: int = 0,
        facts_updated: int = 0,
        metrics: Optional[Dict] = None
    ):
        """Complete the current run."""
        if self._current_run:
            self._current_run.completed_at = datetime.now().isoformat()
            self._current_run.status = "completed"
            self._current_run.facts_added = facts_added
            self._current_run.facts_updated = facts_updated
            self._current_run.metrics = metrics or {}

            self.state.run_history.append(self._current_run)
            self._current_run = None

    def fail_run(self, error: str):
        """Mark the current run as failed."""
        if self._current_run:
            self._current_run.completed_at = datetime.now().isoformat()
            self._current_run.status = "failed"
            self._current_run.error = error

            self.state.run_history.append(self._current_run)
            self._current_run = None

    def get_deal_context_for_prompts(self) -> str:
        """Get deal context formatted for prompt injection."""
        return self.state.deal_context.to_prompt_context()

    def get_deal_context_dict(self) -> Dict[str, Any]:
        """Get deal context as dictionary."""
        return asdict(self.state.deal_context)

    def update_deal_context(self, **kwargs):
        """Update deal context fields."""
        for key, value in kwargs.items():
            if hasattr(self.state.deal_context, key):
                setattr(self.state.deal_context, key, value)

    def set_industry(self, industry: str) -> bool:
        """
        Set the industry for this session.

        Args:
            industry: Industry key (e.g., 'aviation_mro', 'healthcare')

        Returns:
            True if valid and set, False if invalid
        """
        if self.state.deal_context.set_industry(industry):
            logger.info(f"Industry set to: {industry}")
            return True
        return False

    def detect_industry(self, document_text: str, auto_set: bool = False) -> Optional[str]:
        """
        Detect industry from document text.

        Args:
            document_text: Text to analyze for industry signals
            auto_set: If True and industry detected, automatically set it

        Returns:
            Detected industry key or None
        """
        detected = self.state.deal_context.detect_industry_from_text(document_text)
        if detected and auto_set:
            self.state.deal_context.industry = detected
            logger.info(f"Industry auto-set to: {detected}")
        return detected

    def get_industry(self) -> Optional[str]:
        """Get the current industry setting."""
        return self.state.deal_context.industry

    def get_run_history(self) -> List[SessionRun]:
        """Get history of all runs."""
        return list(self.state.run_history)

    def get_last_run(self, phase: Optional[str] = None) -> Optional[SessionRun]:
        """Get the most recent run, optionally filtered by phase."""
        runs = self.state.run_history
        if phase:
            runs = [r for r in runs if r.phase == phase]
        return runs[-1] if runs else None

    def get_change_summary(self) -> Dict[str, Any]:
        """
        Get summary of changes since last save.

        Useful for showing what would be affected by a new run.
        """
        pending_count = len(self._pending_documents)
        total_facts = len(self.fact_store.facts)
        total_risks = len(self.reasoning_store.risks)
        total_work_items = len(self.reasoning_store.work_items)

        last_discovery = self.get_last_run("discovery")
        last_reasoning = self.get_last_run("reasoning")

        return {
            "pending_documents": pending_count,
            "total_facts": total_facts,
            "total_risks": total_risks,
            "total_work_items": total_work_items,
            "last_discovery": last_discovery.completed_at if last_discovery else None,
            "last_reasoning": last_reasoning.completed_at if last_reasoning else None,
            "needs_discovery": pending_count > 0,
            "needs_reasoning": pending_count > 0 or (last_discovery and (not last_reasoning or last_reasoning.completed_at < last_discovery.completed_at))
        }

    def export_outputs(self, output_dir: Path) -> Dict[str, Path]:
        """
        Export all outputs to a directory.

        Args:
            output_dir: Directory to export to

        Returns:
            Dict mapping output type to file path
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        outputs = {}

        # Facts
        facts_file = output_dir / f"facts_{timestamp}.json"
        self.fact_store.save(str(facts_file))
        outputs["facts"] = facts_file

        # Reasoning
        if self.reasoning_store.risks or self.reasoning_store.work_items:
            reasoning_file = output_dir / f"reasoning_{timestamp}.json"
            self.reasoning_store.save(str(reasoning_file))
            outputs["reasoning"] = reasoning_file

        # Narratives
        if self.narrative_store.domain_narratives:
            narrative_file = output_dir / f"narratives_{timestamp}.json"
            self.narrative_store.save(str(narrative_file))
            outputs["narratives"] = narrative_file

        # Session state summary
        summary_file = output_dir / f"session_summary_{timestamp}.json"
        summary = {
            "session_id": self.session_id,
            "deal_context": asdict(self.state.deal_context),
            "documents_processed": len(self.state.processed_documents),
            "total_facts": len(self.fact_store.facts),
            "total_gaps": len(self.fact_store.gaps),
            "total_risks": len(self.reasoning_store.risks),
            "total_work_items": len(self.reasoning_store.work_items),
            "run_count": len(self.state.run_history),
            "exported_at": datetime.now().isoformat()
        }
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        outputs["summary"] = summary_file

        return outputs

    @staticmethod
    def _compute_file_hash(file_path: Path) -> str:
        """Compute SHA256 hash of file content."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def __repr__(self):
        return (f"DDSession(id={self.session_id}, "
                f"docs={len(self.state.processed_documents)}, "
                f"facts={len(self.fact_store.facts)}, "
                f"phase={self.state.current_phase})")
