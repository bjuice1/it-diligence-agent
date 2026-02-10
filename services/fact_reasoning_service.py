"""
Fact Reasoning Service - Generates "why this matters" for high-signal facts.

Phase 1b: Analysis Reasoning Layer

This service:
1. Filters facts to identify high-signal ones worth explaining
2. Generates brief reasoning (1-2 sentences) with evidence citations
3. Stores reasoning attached to facts for UI display

GUARDRAILS:
- Only high-signal facts get reasoning (controls token cost)
- 40-60 tokens max per reasoning
- Must cite evidence (no orphan claims)
- If can't cite, skip (don't hallucinate)
"""

import logging
from typing import Optional, Dict, Any, List, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# =============================================================================
# HIGH-SIGNAL FACT FILTER
# =============================================================================

# Fact types that warrant reasoning (15-25% of all facts)
HIGH_SIGNAL_FACT_TYPES = {
    # Core systems - always significant
    'core_application',
    'policy_administration_system',
    'claims_system',
    'billing_system',
    'erp_system',
    'crm_system',

    # Security - always significant
    'security_control',
    'mfa_status',
    'encryption_status',
    'soc2_status',
    'compliance_status',
    'security_incident',
    'vulnerability',

    # Financial - drives deal economics
    'financial_metric',
    'it_spend',
    'headcount',
    'license_cost',
    'contract_value',

    # Infrastructure - integration complexity
    'infrastructure_core',
    'data_center',
    'cloud_platform',
    'disaster_recovery',
    'network_architecture',

    # Vendors - dependency risk
    'critical_vendor',
    'key_dependency',
    'outsourcing_contract',

    # Leadership - organizational dynamics
    'leadership_role',
    'cio',
    'ciso',
    'cto',
    'it_leader',
}

# Category keywords that indicate high-signal
HIGH_SIGNAL_CATEGORIES = {
    'core', 'critical', 'primary', 'main', 'enterprise',
    'security', 'compliance', 'audit',
    'cost', 'spend', 'budget', 'contract',
    'leadership', 'executive', 'director',
}

# Item keywords that indicate high-signal
HIGH_SIGNAL_KEYWORDS = {
    'policy administration', 'pas', 'claims', 'billing',
    'mfa', 'multi-factor', 'sso', 'encryption', 'soc2', 'soc 2',
    'cio', 'ciso', 'cto', 'vp of it', 'it director',
    'annual cost', 'annual spend', 'license', 'contract',
    'data center', 'disaster recovery', 'dr site',
    'active directory', 'azure ad', 'okta',
    'aws', 'azure', 'gcp', 'cloud',
}


@dataclass
class SignalResult:
    """Result of signal analysis for a fact."""
    is_high_signal: bool
    signal_type: str
    signal_score: float
    reason: str


def analyze_fact_signal(fact) -> SignalResult:
    """
    Determine if a fact is high-signal and warrants reasoning.

    Args:
        fact: Fact object (database model or dataclass)

    Returns:
        SignalResult with is_high_signal, signal_type, score, reason
    """
    # Get fact attributes safely
    fact_id = getattr(fact, 'id', getattr(fact, 'fact_id', ''))
    domain = getattr(fact, 'domain', '').lower()
    category = getattr(fact, 'category', '').lower()
    item = getattr(fact, 'item', '').lower()
    details = getattr(fact, 'details', {}) or {}

    # Check 1: Explicit fact type in details
    fact_type = details.get('fact_type', '').lower()
    if fact_type in HIGH_SIGNAL_FACT_TYPES:
        return SignalResult(
            is_high_signal=True,
            signal_type=fact_type,
            signal_score=1.0,
            reason=f"Fact type '{fact_type}' is high-signal"
        )

    # Check 2: Criticality flag
    criticality = details.get('criticality', '').lower()
    if criticality in ('critical', 'high'):
        return SignalResult(
            is_high_signal=True,
            signal_type='high_criticality',
            signal_score=0.9,
            reason=f"Criticality is {criticality}"
        )

    # Check 3: Category matches high-signal patterns
    for keyword in HIGH_SIGNAL_CATEGORIES:
        if keyword in category:
            return SignalResult(
                is_high_signal=True,
                signal_type=f'category_{keyword}',
                signal_score=0.8,
                reason=f"Category contains '{keyword}'"
            )

    # Check 4: Item text contains high-signal keywords
    for keyword in HIGH_SIGNAL_KEYWORDS:
        if keyword in item:
            return SignalResult(
                is_high_signal=True,
                signal_type='keyword_match',
                signal_score=0.7,
                reason=f"Item contains '{keyword}'"
            )

    # Check 5: Domain-specific high-signal indicators
    if domain == 'cybersecurity':
        # Most security facts are significant
        if any(word in item for word in ['mfa', 'encryption', 'soc', 'audit', 'compliance', 'incident']):
            return SignalResult(
                is_high_signal=True,
                signal_type='security_control',
                signal_score=0.85,
                reason="Security-related fact"
            )

    if domain == 'applications':
        # Core business applications
        if any(word in item for word in ['policy', 'claims', 'billing', 'erp', 'crm', 'core']):
            return SignalResult(
                is_high_signal=True,
                signal_type='core_application',
                signal_score=0.85,
                reason="Core business application"
            )

    if domain == 'organization':
        # Leadership roles
        if any(word in item for word in ['cio', 'ciso', 'cto', 'director', 'vp', 'head of']):
            return SignalResult(
                is_high_signal=True,
                signal_type='leadership_role',
                signal_score=0.8,
                reason="IT leadership role"
            )

    # Not high-signal
    return SignalResult(
        is_high_signal=False,
        signal_type='',
        signal_score=0.0,
        reason="Does not match high-signal criteria"
    )


def filter_high_signal_facts(facts: List) -> List[tuple]:
    """
    Filter facts to only high-signal ones.

    Args:
        facts: List of fact objects

    Returns:
        List of (fact, signal_result) tuples for high-signal facts
    """
    high_signal = []
    for fact in facts:
        result = analyze_fact_signal(fact)
        if result.is_high_signal:
            high_signal.append((fact, result))

    logger.info(f"Filtered {len(high_signal)}/{len(facts)} facts as high-signal ({len(high_signal)/len(facts)*100:.1f}%)" if facts else "No facts to filter")
    return high_signal


# =============================================================================
# REASONING GENERATION
# =============================================================================

REASONING_PROMPT = """For this IT due diligence fact, provide a brief "why this matters" note.

RULES:
1. 1-2 sentences only (max 50 words)
2. Focus on: risk implications, integration complexity, or cost drivers
3. Reference specific evidence from the source
4. If you cannot explain significance, respond with "N/A"

Fact: {fact_text}
Domain: {domain}
Source: {source_document}

Why this matters:"""


def generate_reasoning_for_fact(
    fact,
    signal_result: SignalResult,
    llm_client=None
) -> Optional[Dict[str, Any]]:
    """
    Generate reasoning for a single high-signal fact.

    Args:
        fact: Fact object
        signal_result: Signal analysis result
        llm_client: Optional LLM client (uses default if not provided)

    Returns:
        Dict with reasoning_text, source_refs, or None if failed
    """
    if not signal_result.is_high_signal:
        return None

    # Get fact attributes
    fact_id = getattr(fact, 'id', getattr(fact, 'fact_id', ''))
    item = getattr(fact, 'item', '')
    domain = getattr(fact, 'domain', '')
    source_document = getattr(fact, 'source_document', '')
    document_id = getattr(fact, 'document_id', None)
    source_pages = getattr(fact, 'source_page_numbers', [])

    # Build source refs
    source_refs = []
    if document_id or source_document:
        source_refs.append({
            'doc_id': document_id,
            'doc_name': source_document,
            'pages': source_pages or [],
        })

    # If no LLM client, generate rule-based reasoning
    if not llm_client:
        reasoning_text = _generate_rule_based_reasoning(fact, signal_result)
        if reasoning_text:
            return {
                'reasoning_text': reasoning_text,
                'source_refs': source_refs,
                'signal_type': signal_result.signal_type,
                'signal_score': signal_result.signal_score,
            }
        return None

    # Use LLM for reasoning generation
    try:
        prompt = REASONING_PROMPT.format(
            fact_text=item,
            domain=domain,
            source_document=source_document or 'Unknown'
        )

        response = llm_client.generate(
            prompt=prompt,
            max_tokens=100,  # ~50 words max
            temperature=0.3,  # Lower temperature for factual consistency
        )

        reasoning_text = response.strip()

        # Validate response
        if not reasoning_text or reasoning_text.upper() == 'N/A' or len(reasoning_text) < 20:
            logger.debug(f"LLM returned no valid reasoning for fact {fact_id}")
            return None

        # Truncate if too long
        if len(reasoning_text) > 400:
            reasoning_text = reasoning_text[:397] + '...'

        return {
            'reasoning_text': reasoning_text,
            'source_refs': source_refs,
            'signal_type': signal_result.signal_type,
            'signal_score': signal_result.signal_score,
        }

    except Exception as e:
        logger.warning(f"LLM reasoning generation failed for fact {fact_id}: {e}")
        # Fall back to rule-based
        reasoning_text = _generate_rule_based_reasoning(fact, signal_result)
        if reasoning_text:
            return {
                'reasoning_text': reasoning_text,
                'source_refs': source_refs,
                'signal_type': signal_result.signal_type,
                'signal_score': signal_result.signal_score,
            }
        return None


def _generate_rule_based_reasoning(fact, signal_result: SignalResult) -> Optional[str]:
    """
    Generate reasoning using rules (no LLM).

    This is the fallback and also useful for batch processing without API calls.
    """
    signal_type = signal_result.signal_type
    domain = getattr(fact, 'domain', '').lower()
    item = getattr(fact, 'item', '')
    details = getattr(fact, 'details', {}) or {}

    # Core applications
    if signal_type in ('core_application', 'policy_administration_system', 'claims_system', 'billing_system'):
        version = details.get('version', '')
        if version:
            return f"Core business system. Version and upgrade path affect integration complexity and Day-1 continuity planning."
        return "Core business system critical to operations. Requires careful integration planning and Day-1 continuity assessment."

    # Security controls
    if signal_type in ('security_control', 'mfa_status', 'encryption_status'):
        return "Security control status affects risk posture and may require remediation investment or TSA coverage."

    # Compliance
    if signal_type in ('soc2_status', 'compliance_status'):
        return "Compliance status impacts deal risk assessment and may require audit remediation costs."

    # Financial metrics
    if signal_type in ('financial_metric', 'it_spend', 'license_cost', 'contract_value'):
        return "Financial metric directly impacts deal economics and integration budget modeling."

    # Leadership
    if signal_type in ('leadership_role', 'cio', 'ciso', 'cto', 'it_leader'):
        return "IT leadership role. Retention and reporting structure affect post-close execution capability."

    # Infrastructure
    if signal_type in ('infrastructure_core', 'data_center', 'cloud_platform'):
        return "Core infrastructure component. Architecture decisions affect integration approach and timeline."

    # Critical vendors
    if signal_type in ('critical_vendor', 'key_dependency'):
        return "Key vendor dependency. Contract terms and transition requirements need assessment."

    # High criticality
    if signal_type == 'high_criticality':
        return "Marked as high criticality. Warrants focused attention during due diligence."

    # Generic high-signal
    if signal_result.is_high_signal:
        return f"Relevant to {domain} assessment. Consider implications for integration planning."

    return None


# =============================================================================
# BATCH PROCESSING
# =============================================================================

class FactReasoningService:
    """
    Service for generating and managing fact reasoning.

    Usage:
        service = FactReasoningService()
        service.generate_for_facts(facts, run_id, deal_id)
    """

    def __init__(self, use_llm: bool = False, llm_client=None):
        """
        Initialize the service.

        Args:
            use_llm: Whether to use LLM for reasoning (vs rule-based)
            llm_client: LLM client if use_llm is True
        """
        self.use_llm = use_llm
        self.llm_client = llm_client

    def generate_for_facts(
        self,
        facts: List,
        run_id: str,
        deal_id: str,
        commit: bool = True
    ) -> Dict[str, int]:
        """
        Generate reasoning for high-signal facts and save to database.

        Args:
            facts: List of fact objects
            run_id: Analysis run ID
            deal_id: Deal ID
            commit: Whether to commit to database

        Returns:
            Dict with counts: total_facts, high_signal, reasoning_generated
        """
        from web.database import db, FactReasoning

        stats = {
            'total_facts': len(facts),
            'high_signal': 0,
            'reasoning_generated': 0,
            'skipped': 0,
        }

        # Filter to high-signal facts
        high_signal_facts = filter_high_signal_facts(facts)
        stats['high_signal'] = len(high_signal_facts)

        # Generate reasoning for each
        for fact, signal_result in high_signal_facts:
            fact_id = getattr(fact, 'id', getattr(fact, 'fact_id', ''))

            # Check if reasoning already exists
            existing = FactReasoning.query.filter_by(fact_id=fact_id).first()
            if existing:
                stats['skipped'] += 1
                continue

            # Generate reasoning
            reasoning_data = generate_reasoning_for_fact(
                fact,
                signal_result,
                llm_client=self.llm_client if self.use_llm else None
            )

            if not reasoning_data:
                continue

            # Create database record
            try:
                reasoning = FactReasoning(
                    fact_id=fact_id,
                    run_id=run_id,
                    reasoning_text=reasoning_data['reasoning_text'],
                    source_refs=reasoning_data['source_refs'],
                    related_fact_ids=[],
                    signal_type=reasoning_data['signal_type'],
                    signal_score=reasoning_data['signal_score'],
                    visibility='client_safe',
                )
                db.session.add(reasoning)
                stats['reasoning_generated'] += 1

            except Exception as e:
                logger.warning(f"Failed to create reasoning for fact {fact_id}: {e}")

        if commit:
            try:
                db.session.commit()
                logger.info(
                    f"Generated reasoning: {stats['reasoning_generated']}/{stats['high_signal']} "
                    f"high-signal facts ({stats['total_facts']} total)"
                )
            except Exception as e:
                logger.error(f"Failed to commit reasoning: {e}")
                db.session.rollback()

        return stats

    def get_reasoning_for_fact(self, fact_id: str) -> Optional[Dict[str, Any]]:
        """Get reasoning for a specific fact."""
        from web.database import FactReasoning

        reasoning = FactReasoning.query.filter_by(fact_id=fact_id).first()
        if reasoning:
            return reasoning.to_dict()
        return None

    def get_reasoning_for_deal(self, deal_id: str) -> List[Dict[str, Any]]:
        """Get all reasoning for a deal."""
        from web.database import db, FactReasoning, Fact

        reasonings = (
            db.session.query(FactReasoning)
            .join(Fact)
            .filter(Fact.deal_id == deal_id)
            .all()
        )
        return [r.to_dict() for r in reasonings]


# Singleton instance
fact_reasoning_service = FactReasoningService(use_llm=False)


def generate_reasoning_for_run(facts: List, run_id: str, deal_id: str) -> Dict[str, int]:
    """
    Convenience function to generate reasoning after analysis.

    Call this after facts are persisted.
    """
    return fact_reasoning_service.generate_for_facts(facts, run_id, deal_id)
