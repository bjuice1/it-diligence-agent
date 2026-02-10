# Spec 06: Fact Reasoning Expansion
**Version:** 1.0
**Date:** February 10, 2026
**Status:** Ready for Implementation
**Dependencies:** Spec 05 (UI enhancement to display expanded reasoning)

---

## Executive Summary

This specification **expands fact reasoning coverage** from the current 15-25% to a target of 30-50%, providing more explanatory context while managing LLM API costs through intelligent prioritization.

### Current State

**Existing Implementation** (from audit):
- ✅ FactReasoning model exists
- ✅ 20+ signal types detect high-value facts
- ✅ Reasoning explains "why this matters"
- ✅ Coverage: 15-25% of facts (intentional cost control)

**Gaps:**
- ❌ Coverage too narrow - many important facts lack reasoning
- ❌ Signal types may miss domain-specific patterns
- ❌ No domain-based prioritization (flat 15-25% across all categories)
- ❌ User cannot adjust reasoning depth preference

### Target State

**Domain-Specific Coverage:**
```
Critical domains (Applications, Security):    50% coverage
Important domains (Infrastructure, Identity): 35% coverage
Standard domains (Network, Endpoints):        20% coverage
```

**Enhanced Signal Types:**
- Expand from 20 → 40 signal patterns
- Add integration risk, data migration complexity, vendor lock-in
- Domain-specific signals (e.g., security_gap, compliance_violation)

**User-Configurable:**
- Admin setting: reasoning_depth (low/medium/high)
- Per-deal override: "Generate more reasoning for this deal"
- Cost monitoring dashboard

---

## Architecture Overview

### Signal Detection Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    Fact Ingestion                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Fact: "Oracle E-Business Suite 11i (2006 release)"         │
│                                                              │
│  ↓                                                           │
│                                                              │
│  STAGE 1: Domain Classification                             │
│  ──────────────────────────                                 │
│  → Category: application                                    │
│  → Domain: critical (ERP system)                            │
│  → Target Coverage: 50%                                     │
│                                                              │
│  ↓                                                           │
│                                                              │
│  STAGE 2: Signal Type Detection                             │
│  ────────────────────────────                               │
│  → Signal Type: erp_system (MATCH: "Oracle" + "ERP")        │
│  → Signal Score: 0.92 (very high)                           │
│  → Additional Signals:                                       │
│     • legacy_technology (MATCH: "2006", "11i")              │
│     • integration_risk (INFERRED: old SOAP APIs)            │
│                                                              │
│  ↓                                                           │
│                                                              │
│  STAGE 3: Coverage Decision                                 │
│  ───────────────────────                                    │
│  → Domain target: 50%                                       │
│  → Current coverage: 38% (12 of 32 facts)                   │
│  → Signal score: 0.92 (above threshold)                     │
│  → **DECISION: Generate Reasoning** ✅                      │
│                                                              │
│  ↓                                                           │
│                                                              │
│  STAGE 4: Reasoning Generation                              │
│  ──────────────────────────                                 │
│  → Prompt Template: erp_system_reasoning.txt                │
│  → LLM API Call (40-60 tokens)                              │
│  → Output: "Oracle E-Business Suite 11i is end-of-life..." │
│                                                              │
│  ↓                                                           │
│                                                              │
│  STAGE 5: FactReasoning Creation                            │
│  ─────────────────────────────                              │
│  → reasoning_text: "..."                                    │
│  → signal_type: "erp_system"                                │
│  → signal_score: 0.92                                       │
│  → source_refs: ["F-APP-001"]                               │
│  → visibility: "client_safe"                                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Expanded Signal Types

### Existing Signal Types (20)

**From Audit:**
- Core applications: ERP, CRM, HCM, finance systems
- Security controls: MFA, SIEM, endpoint protection, firewalls
- Financial metrics: IT spend, headcount
- Critical vendors and dependencies
- Compliance systems: audit logging, data governance

### New Signal Types (20 additional)

**Category:** integration_risk
```python
{
    "name": "integration_risk",
    "patterns": [
        r"integration.*complex",
        r"tightly coupled",
        r"hard-coded dependencies",
        r"API.*unavailable",
        r"SOAP.*only",
        r"no REST API"
    ],
    "reasoning_template": """
        This fact indicates integration complexity that may:
        - Delay M&A separation timelines
        - Increase development effort for new integrations
        - Create technical debt post-acquisition
        - Block cloud migration or modernization

        Recommended actions:
        - Document all integration points
        - Assess API modernization requirements
        - Plan integration layer refactoring
    """,
    "domain_applicability": ["application", "infrastructure"],
    "min_score": 0.7
}
```

**Category:** data_migration_complexity
```python
{
    "name": "data_migration_complexity",
    "patterns": [
        r"(\d+)\s*(TB|PB|petabyte|terabyte)",  # Large data volumes
        r"unstructured data",
        r"data quality.*poor",
        r"no data dictionary",
        r"legacy.*format",
        r"mainframe.*data"
    ],
    "reasoning_template": """
        This fact suggests significant data migration challenges:
        - Volume: {volume} requires extended migration windows
        - Complexity: Data transformation/cleansing needed
        - Risk: Data loss or corruption during migration
        - Timeline: May extend separation by {estimated_months} months

        Mitigation:
        - Engage data migration specialist
        - Plan phased migration approach
        - Implement robust validation & rollback
    """,
    "domain_applicability": ["data", "application"],
    "min_score": 0.75
}
```

**Category:** vendor_lock_in
```python
{
    "name": "vendor_lock_in",
    "patterns": [
        r"proprietary.*format",
        r"vendor-specific.*API",
        r"no export.*capability",
        r"locked.*contract",
        r"exclusive.*agreement",
        r"non-standard.*protocol"
    ],
    "reasoning_template": """
        This fact indicates vendor lock-in risk:
        - Difficulty switching vendors post-acquisition
        - Potential leverage in contract negotiations
        - Limited integration flexibility
        - May require custom development to abstract

        Considerations:
        - Assess contract exit clauses
        - Evaluate alternative vendors
        - Budget for abstraction layer if needed
    """,
    "domain_applicability": ["vendor", "application", "infrastructure"],
    "min_score": 0.65
}
```

**Category:** security_gap
```python
{
    "name": "security_gap",
    "patterns": [
        r"no.*MFA",
        r"unencrypted.*data",
        r"admin.*password.*shared",
        r"no.*patching.*process",
        r"firewall.*disabled",
        r"antivirus.*not.*installed",
        r"log.*not.*retained"
    ],
    "reasoning_template": """
        **SECURITY RISK IDENTIFIED:**

        This fact represents a critical security gap that:
        - Violates {compliance_standard} compliance requirements
        - Exposes organization to {threat_type} attacks
        - May result in data breach or regulatory fines
        - Requires immediate remediation post-acquisition

        Immediate Actions:
        - Flag for Day 1 security hardening plan
        - Budget ${estimated_cost} for remediation
        - Engage security team for assessment

        **Visibility:** Internal only (do not share with seller)
    """,
    "domain_applicability": ["security", "compliance"],
    "min_score": 0.85,  # High priority
    "visibility": "internal_only"
}
```

**Category:** compliance_violation
```python
{
    "name": "compliance_violation",
    "patterns": [
        r"PCI.*non-compliant",
        r"GDPR.*violation",
        r"SOX.*controls.*missing",
        r"HIPAA.*not.*implemented",
        r"retention.*policy.*violated"
    ],
    "reasoning_template": """
        **COMPLIANCE VIOLATION DETECTED:**

        This fact indicates non-compliance with {regulation}:
        - Potential fines: ${fine_range}
        - Remediation timeline: {timeline}
        - Deal impact: May require escrow or price adjustment

        Due Diligence Actions:
        - Request compliance audit reports
        - Assess remediation costs
        - Engage legal counsel
        - Consider deal structure implications

        **Visibility:** Internal only
    """,
    "domain_applicability": ["compliance", "security", "data"],
    "min_score": 0.90,  # Very high priority
    "visibility": "internal_only"
}
```

**Category:** technical_debt
```python
{
    "name": "technical_debt",
    "patterns": [
        r"end-of-life",
        r"unsupported.*version",
        r"no.*longer.*maintained",
        r"legacy.*codebase",
        r"spaghetti.*code",
        r"no.*documentation",
        r"(\d+).*years.*old.*code"
    ],
    "reasoning_template": """
        This fact indicates technical debt accumulation:
        - Modernization cost: ${estimated_cost_range}
        - Modernization timeline: {timeline_months} months
        - Integration impact: May block certain integrations
        - Cloud migration: Likely requires refactoring

        Strategic Options:
        - Option 1: Modernize in place (${cost1})
        - Option 2: Replace with SaaS alternative (${cost2})
        - Option 3: Maintain as-is (ongoing risk)

        Recommendation: {recommended_option}
    """,
    "domain_applicability": ["application", "infrastructure"],
    "min_score": 0.70
}
```

**Category:** scale_constraint
```python
{
    "name": "scale_constraint",
    "patterns": [
        r"capacity.*\d+%",  # "at 85% capacity"
        r"performance.*degradation",
        r"cannot.*scale",
        r"bottleneck",
        r"single.*point.*of.*failure",
        r"maxed.*out"
    ],
    "reasoning_template": """
        This fact reveals scalability constraints:
        - Current utilization: {utilization_pct}%
        - Time to capacity: {months_to_capacity} months
        - Growth impact: Cannot support planned growth
        - Risk: Service degradation or outage

        Remediation Options:
        - Short-term: Capacity increase (${short_term_cost})
        - Long-term: Architecture redesign (${long_term_cost})

        Timeline Impact: May delay integration by {delay_months} months
    """,
    "domain_applicability": ["infrastructure", "application"],
    "min_score": 0.75
}
```

**Additional Signal Types (13 more):**
1. `cloud_readiness` - Assess cloud migration feasibility
2. `disaster_recovery_gap` - Missing DR/backup capabilities
3. `single_vendor_dependency` - Over-reliance on one vendor
4. `expensive_license` - High-cost licensing models
5. `custom_development` - Custom-built systems (not COTS)
6. `integration_spaghetti` - Too many point-to-point integrations
7. `data_residency_issue` - Data sovereignty/compliance risks
8. `organizational_dependency` - Knowledge concentrated in one person
9. `workflow_automation_gap` - Manual processes that should be automated
10. `monitoring_gap` - Lack of observability
11. `change_management_risk` - Poor change control processes
12. `test_coverage_gap` - Insufficient testing
13. `api_versioning_issue` - API breaking changes risk

---

## Domain-Based Prioritization

### Domain Classification

```python
from enum import Enum

class DomainCategory(Enum):
    """Domain categories with coverage targets."""

    CRITICAL = "critical"      # 50% coverage target
    IMPORTANT = "important"    # 35% coverage target
    STANDARD = "standard"      # 20% coverage target
    LOW_PRIORITY = "low"       # 10% coverage target

# Domain mapping
DOMAIN_CATEGORIES = {
    # Critical (50% coverage)
    "application": DomainCategory.CRITICAL,
    "erp": DomainCategory.CRITICAL,
    "crm": DomainCategory.CRITICAL,
    "financial": DomainCategory.CRITICAL,
    "security": DomainCategory.CRITICAL,
    "compliance": DomainCategory.CRITICAL,
    "data": DomainCategory.CRITICAL,

    # Important (35% coverage)
    "infrastructure": DomainCategory.IMPORTANT,
    "identity": DomainCategory.IMPORTANT,
    "cloud": DomainCategory.IMPORTANT,
    "vendor": DomainCategory.IMPORTANT,
    "integration": DomainCategory.IMPORTANT,

    # Standard (20% coverage)
    "network": DomainCategory.STANDARD,
    "endpoint": DomainCategory.STANDARD,
    "backup": DomainCategory.STANDARD,
    "monitoring": DomainCategory.STANDARD,

    # Low Priority (10% coverage)
    "peripheral": DomainCategory.LOW_PRIORITY,
    "administrative": DomainCategory.LOW_PRIORITY,
}

def get_target_coverage(category: str) -> float:
    """Get coverage target % for a fact category."""
    domain_cat = DOMAIN_CATEGORIES.get(category.lower(), DomainCategory.STANDARD)

    if domain_cat == DomainCategory.CRITICAL:
        return 0.50
    elif domain_cat == DomainCategory.IMPORTANT:
        return 0.35
    elif domain_cat == DomainCategory.STANDARD:
        return 0.20
    else:
        return 0.10
```

### Coverage Algorithm

```python
import random
from typing import List, Optional
from web.database import Fact, FactReasoning

class ReasoningCoverageManager:
    """
    Manages fact reasoning generation with domain-based coverage targets.

    Ensures:
    - Critical domains get 50% coverage
    - Important domains get 35% coverage
    - Standard domains get 20% coverage
    - High-signal facts prioritized within each domain
    """

    def __init__(self, target_coverage_multiplier: float = 1.0):
        """
        Initialize manager.

        Args:
            target_coverage_multiplier: Adjust all targets (e.g., 1.5 = 50% more coverage)
        """
        self.multiplier = target_coverage_multiplier

    def should_generate_reasoning(
        self,
        fact: Fact,
        signal_score: float,
        signal_type: str
    ) -> bool:
        """
        Decide if reasoning should be generated for this fact.

        Args:
            fact: Fact instance
            signal_score: Detection score (0.0-1.0)
            signal_type: Type of signal detected

        Returns:
            True if reasoning should be generated
        """
        # Get domain target coverage
        target_coverage = get_target_coverage(fact.category) * self.multiplier

        # Calculate current coverage for this domain
        current_coverage = self._calculate_current_coverage(fact.category, fact.deal_id)

        # Decision logic
        if current_coverage < target_coverage:
            # Below target - use probabilistic selection weighted by signal score
            threshold = self._calculate_threshold(
                current_coverage,
                target_coverage,
                signal_score
            )
            return random.random() < threshold
        else:
            # At/above target - only generate for very high signal scores
            return signal_score >= 0.90

    def _calculate_current_coverage(self, category: str, deal_id: str) -> float:
        """Calculate current reasoning coverage % for this domain."""
        from sqlalchemy import func

        # Total facts in this category
        total = Fact.query.filter(
            Fact.deal_id == deal_id,
            Fact.category == category
        ).count()

        if total == 0:
            return 0.0

        # Facts with reasoning in this category
        with_reasoning = Fact.query.join(FactReasoning).filter(
            Fact.deal_id == deal_id,
            Fact.category == category
        ).count()

        return with_reasoning / total

    def _calculate_threshold(
        self,
        current_coverage: float,
        target_coverage: float,
        signal_score: float
    ) -> float:
        """
        Calculate probability threshold for generating reasoning.

        Logic:
        - Far below target → generate more aggressively
        - Near target → become selective
        - Signal score boosts probability
        """
        # How far below target?
        gap = target_coverage - current_coverage

        # Base probability from gap (0.0 = at target, 1.0 = far below)
        gap_factor = min(gap / target_coverage, 1.0)

        # Boost based on signal score
        score_boost = signal_score * 0.5  # Up to +50% probability

        # Combined probability
        probability = gap_factor + score_boost

        # Cap at 95% (never 100% certainty to allow variability)
        return min(probability, 0.95)
```

---

## Enhanced Signal Detection

### SignalDetector Class

```python
import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class SignalDefinition:
    """Definition of a signal type."""
    name: str
    patterns: List[str]  # Regex patterns
    reasoning_template: str
    domain_applicability: List[str]  # Which domains this applies to
    min_score: float = 0.7
    visibility: str = "client_safe"  # or "internal_only"

class SignalDetector:
    """
    Detects signals in facts and calculates signal scores.

    Enhanced with 40 signal types (up from 20).
    """

    def __init__(self):
        self.signals = self._load_signal_definitions()

    def _load_signal_definitions(self) -> List[SignalDefinition]:
        """Load all 40 signal definitions."""
        # This would load from a config file or database
        # For now, inline definitions

        return [
            # EXISTING 20 SIGNALS (simplified here)
            SignalDefinition(
                name="erp_system",
                patterns=[
                    r"(SAP|Oracle|Microsoft Dynamics|Infor|NetSuite).*ERP",
                    r"ERP.*(system|platform|solution)"
                ],
                reasoning_template="...",
                domain_applicability=["application", "financial"],
                min_score=0.85
            ),

            # NEW SIGNALS
            SignalDefinition(
                name="integration_risk",
                patterns=[
                    r"integration.*complex",
                    r"tightly coupled",
                    r"SOAP.*only",
                    r"no REST API"
                ],
                reasoning_template="...",
                domain_applicability=["application", "infrastructure"],
                min_score=0.70
            ),

            SignalDefinition(
                name="data_migration_complexity",
                patterns=[
                    r"(\d+)\s*(TB|PB|petabyte|terabyte)",
                    r"unstructured data",
                    r"legacy.*format"
                ],
                reasoning_template="...",
                domain_applicability=["data", "application"],
                min_score=0.75
            ),

            # ... (remaining 37 signal definitions)
        ]

    def detect(self, fact: Fact) -> List[Tuple[str, float, str]]:
        """
        Detect signals in a fact.

        Args:
            fact: Fact instance

        Returns:
            List of (signal_type, score, reasoning_template) tuples
        """
        detected = []
        content_lower = fact.content.lower()

        for signal in self.signals:
            # Check domain applicability
            if fact.category.lower() not in signal.domain_applicability:
                continue

            # Check patterns
            matches = 0
            for pattern in signal.patterns:
                if re.search(pattern, content_lower, re.IGNORECASE):
                    matches += 1

            if matches == 0:
                continue

            # Calculate score
            # More pattern matches = higher score
            match_ratio = matches / len(signal.patterns)
            score = min(signal.min_score + (match_ratio * 0.2), 1.0)

            detected.append((signal.name, score, signal.reasoning_template))

        # Sort by score descending
        detected.sort(key=lambda x: x[1], reverse=True)

        return detected
```

---

## Reasoning Generation

### Enhanced ReasoningGenerator

```python
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class ReasoningGenerator:
    """
    Generates reasoning text for facts using LLM.

    Enhanced with better prompts and template variables.
    """

    def __init__(self, llm_client):
        """
        Args:
            llm_client: LLM API client (e.g., OpenAI, Anthropic)
        """
        self.llm = llm_client
        self.coverage_manager = ReasoningCoverageManager()
        self.signal_detector = SignalDetector()

    def generate_for_fact(
        self,
        fact: Fact,
        force: bool = False
    ) -> Optional[FactReasoning]:
        """
        Generate reasoning for a fact if warranted.

        Args:
            fact: Fact instance
            force: If True, bypass coverage checks

        Returns:
            FactReasoning instance if generated, else None
        """
        # Detect signals
        detected_signals = self.signal_detector.detect(fact)

        if not detected_signals and not force:
            # No signals detected, skip
            return None

        # Get highest-scoring signal
        signal_type, signal_score, template = detected_signals[0]

        # Check if should generate (coverage-based)
        if not force:
            should_generate = self.coverage_manager.should_generate_reasoning(
                fact, signal_score, signal_type
            )
            if not should_generate:
                logger.debug(
                    f"Skipping reasoning for {fact.id} (coverage target met, score={signal_score:.2f})"
                )
                return None

        # Generate reasoning text
        reasoning_text = self._generate_reasoning_text(fact, signal_type, template)

        if not reasoning_text:
            return None

        # Create FactReasoning
        fact_reasoning = FactReasoning(
            fact_id=fact.id,
            reasoning_text=reasoning_text,
            signal_type=signal_type,
            signal_score=signal_score,
            source_refs=[fact.id],
            visibility="client_safe"  # Could be determined by signal definition
        )

        logger.info(
            f"Generated reasoning for {fact.id}: {signal_type} (score={signal_score:.2f})"
        )

        return fact_reasoning

    def _generate_reasoning_text(
        self,
        fact: Fact,
        signal_type: str,
        template: str
    ) -> Optional[str]:
        """Generate reasoning text using LLM."""

        # Build prompt
        prompt = f"""
You are an expert M&A technology due diligence analyst.

Given the following fact from a deal evaluation:

Fact: {fact.content}
Category: {fact.category}
Signal Type: {signal_type}

Using this template as guidance:
{template}

Generate a concise (40-60 tokens) explanation of why this fact matters for the M&A deal, focusing on:
1. Business impact
2. Deal implications
3. Recommended actions

Keep the tone professional and actionable. Do not repeat the fact verbatim.
"""

        try:
            # Call LLM (example with OpenAI-style API)
            response = self.llm.complete(
                prompt=prompt,
                max_tokens=80,
                temperature=0.7
            )

            reasoning_text = response.strip()

            # Validate length (40-60 tokens ≈ 200-300 chars)
            if len(reasoning_text) < 100:
                logger.warning(f"Reasoning too short for {fact.id}: {len(reasoning_text)} chars")
                return None

            return reasoning_text

        except Exception as e:
            logger.error(f"LLM reasoning generation failed for {fact.id}: {e}")
            return None
```

---

## User Configuration

### Admin Settings

```python
from web.database import db

class SystemSettings(db.Model):
    """System-wide configuration settings."""
    __tablename__ = 'system_settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.JSON, nullable=False)
    description = db.Column(db.Text)

    @staticmethod
    def get_reasoning_depth() -> str:
        """
        Get current reasoning depth setting.

        Returns:
            "low", "medium", or "high"
        """
        setting = SystemSettings.query.filter_by(key='reasoning_depth').first()
        if not setting:
            return "medium"  # Default
        return setting.value.get('depth', 'medium')

    @staticmethod
    def get_coverage_multiplier() -> float:
        """
        Get coverage multiplier based on depth setting.

        Returns:
            0.5 (low), 1.0 (medium), or 1.5 (high)
        """
        depth = SystemSettings.get_reasoning_depth()

        if depth == "low":
            return 0.5  # 50% of target coverage (10%, 17.5%, 25%)
        elif depth == "high":
            return 1.5  # 150% of target coverage (15%, 52.5%, 75%)
        else:
            return 1.0  # 100% of target coverage (10%, 35%, 50%)
```

### Admin UI

**File:** `web/templates/admin/settings.html`

```html
<div class="settings-section">
  <h3>Fact Reasoning Configuration</h3>

  <div class="form-group">
    <label for="reasoning-depth">Reasoning Depth:</label>
    <select id="reasoning-depth" class="form-control">
      <option value="low">Low (15-20% coverage, lower cost)</option>
      <option value="medium" selected>Medium (30-40% coverage, balanced)</option>
      <option value="high">High (50-75% coverage, higher cost)</option>
    </select>
    <small class="form-text text-muted">
      Higher coverage provides more explanatory context but increases LLM API costs.
    </small>
  </div>

  <div class="cost-estimate">
    <h4>Estimated Monthly Cost:</h4>
    <div class="cost-breakdown">
      <div>Low: ~$50-100/month (5-10 deals)</div>
      <div>Medium: ~$150-250/month (5-10 deals)</div>
      <div>High: ~$300-500/month (5-10 deals)</div>
    </div>
  </div>

  <button class="btn btn-primary" onclick="saveReasoningSettings()">
    Save Settings
  </button>
</div>

<script>
function saveReasoningSettings() {
  const depth = document.getElementById('reasoning-depth').value;

  fetch('/api/admin/settings', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      key: 'reasoning_depth',
      value: { depth: depth }
    })
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      alert('Settings saved successfully');
    }
  });
}
</script>
```

---

## Cost Monitoring

### Usage Tracking

```python
from datetime import datetime, timedelta
from web.database import db

class LLMUsageLog(db.Model):
    """Track LLM API usage for cost monitoring."""
    __tablename__ = 'llm_usage_log'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    operation = db.Column(db.String(50))  # "fact_reasoning", "finding_generation", etc.
    deal_id = db.Column(db.String(100), index=True)
    tokens_used = db.Column(db.Integer)
    cost_usd = db.Column(db.Float)
    model = db.Column(db.String(50))
    success = db.Column(db.Boolean, default=True)

    @staticmethod
    def log_reasoning_generation(
        deal_id: str,
        tokens: int,
        cost: float,
        model: str,
        success: bool = True
    ):
        """Log a reasoning generation API call."""
        log = LLMUsageLog(
            operation="fact_reasoning",
            deal_id=deal_id,
            tokens_used=tokens,
            cost_usd=cost,
            model=model,
            success=success
        )
        db.session.add(log)
        db.session.commit()

    @staticmethod
    def get_cost_last_30_days() -> float:
        """Get total cost for last 30 days."""
        since = datetime.utcnow() - timedelta(days=30)

        result = db.session.query(
            db.func.sum(LLMUsageLog.cost_usd)
        ).filter(
            LLMUsageLog.timestamp >= since
        ).scalar()

        return result or 0.0

    @staticmethod
    def get_coverage_stats() -> Dict:
        """Get reasoning coverage statistics."""
        from sqlalchemy import func

        # Total facts
        total_facts = Fact.query.count()

        # Facts with reasoning
        with_reasoning = Fact.query.join(FactReasoning).count()

        # Breakdown by domain
        by_domain = db.session.query(
            Fact.category,
            func.count(Fact.id).label('total'),
            func.count(FactReasoning.id).label('with_reasoning')
        ).outerjoin(FactReasoning).group_by(Fact.category).all()

        domain_stats = {}
        for category, total, with_reason in by_domain:
            coverage = (with_reason / total * 100) if total > 0 else 0
            domain_stats[category] = {
                "total": total,
                "with_reasoning": with_reason,
                "coverage_pct": coverage
            }

        return {
            "overall_coverage_pct": (with_reasoning / total_facts * 100) if total_facts > 0 else 0,
            "total_facts": total_facts,
            "facts_with_reasoning": with_reasoning,
            "by_domain": domain_stats
        }
```

### Cost Dashboard

**Endpoint:** `GET /api/admin/llm-usage-stats`

```python
from flask import Blueprint, jsonify

admin_api = Blueprint('admin_api', __name__)

@admin_api.route('/api/admin/llm-usage-stats', methods=['GET'])
def get_llm_usage_stats():
    """Get LLM usage statistics and cost breakdown."""

    cost_30d = LLMUsageLog.get_cost_last_30_days()
    coverage_stats = LLMUsageLog.get_coverage_stats()

    # Project monthly cost
    cost_projection = cost_30d * 1.1  # +10% buffer

    return jsonify({
        "cost_last_30_days": cost_30d,
        "cost_projection_monthly": cost_projection,
        "coverage": coverage_stats,
        "reasoning_depth": SystemSettings.get_reasoning_depth(),
        "recommendations": _get_cost_recommendations(cost_30d, coverage_stats)
    })

def _get_cost_recommendations(cost: float, coverage: Dict) -> List[str]:
    """Generate cost optimization recommendations."""
    recs = []

    if cost > 500:
        recs.append("Cost is high. Consider reducing reasoning depth to 'medium' or 'low'.")

    overall_coverage = coverage.get('overall_coverage_pct', 0)
    if overall_coverage < 20:
        recs.append("Coverage is low. Consider increasing reasoning depth to 'medium'.")
    elif overall_coverage > 60:
        recs.append("Coverage is very high. You may reduce depth to 'medium' to save costs.")

    # Check domain imbalances
    for domain, stats in coverage.get('by_domain', {}).items():
        domain_cov = stats.get('coverage_pct', 0)
        target = get_target_coverage(domain) * 100

        if domain_cov < target * 0.7:  # 30% below target
            recs.append(f"Domain '{domain}' coverage ({domain_cov:.0f}%) is below target ({target:.0f}%).")

    return recs
```

---

## Testing Strategy

### Unit Tests

**File:** `tests/test_reasoning_expansion.py`

```python
import pytest
from services.reasoning_generator import ReasoningGenerator, SignalDetector
from web.database import Fact

class TestSignalDetector:
    def test_detect_erp_signal(self):
        fact = Fact(
            id="F-TEST-001",
            content="Oracle E-Business Suite 11i (ERP system)",
            category="application"
        )

        detector = SignalDetector()
        signals = detector.detect(fact)

        assert len(signals) > 0
        assert signals[0][0] == "erp_system"
        assert signals[0][1] >= 0.85  # High score

    def test_detect_integration_risk(self):
        fact = Fact(
            id="F-TEST-002",
            content="System uses SOAP-only APIs with no REST support, creating integration complexity",
            category="application"
        )

        detector = SignalDetector()
        signals = detector.detect(fact)

        signal_types = [s[0] for s in signals]
        assert "integration_risk" in signal_types

    def test_no_signal_for_irrelevant_content(self):
        fact = Fact(
            id="F-TEST-003",
            content="Office has 5 conference rooms",
            category="administrative"
        )

        detector = SignalDetector()
        signals = detector.detect(fact)

        assert len(signals) == 0

class TestCoverageManager:
    def test_coverage_calculation(self):
        # TODO: Mock database and test coverage calculation
        pass

    def test_should_generate_below_target(self):
        # TODO: Test that facts are selected when below coverage target
        pass

    def test_should_not_generate_above_target(self):
        # TODO: Test that low-signal facts are skipped when above target
        pass
```

---

## Implementation Checklist

### Phase 1: Signal Expansion (Week 1)
- [ ] Define all 20 new signal types with patterns and templates
- [ ] Implement enhanced SignalDetector class
- [ ] Unit tests for all signal types
- [ ] Validation with sample facts

### Phase 2: Coverage Manager (Week 1-2)
- [ ] Implement ReasoningCoverageManager
- [ ] Add domain-based prioritization logic
- [ ] Test coverage calculations
- [ ] Validate probabilistic selection

### Phase 3: LLM Integration (Week 2)
- [ ] Enhance ReasoningGenerator with new signals
- [ ] Improve LLM prompts and templates
- [ ] Test reasoning generation quality
- [ ] Optimize token usage

### Phase 4: Configuration & Monitoring (Week 2-3)
- [ ] Add SystemSettings model
- [ ] Implement admin UI for depth configuration
- [ ] Add LLMUsageLog tracking
- [ ] Build cost dashboard
- [ ] Set up usage alerts

### Phase 5: Testing & Deployment (Week 3)
- [ ] Integration tests
- [ ] Generate reasoning for test deals
- [ ] Validate coverage targets met
- [ ] Cost analysis
- [ ] Production deployment

---

## Success Criteria

✅ **Expansion successful when:**

1. **Coverage targets met:**
   - Critical domains: 45-55% (target 50%)
   - Important domains: 30-40% (target 35%)
   - Standard domains: 15-25% (target 20%)

2. **Signal detection accuracy:** >90% precision on test set

3. **Reasoning quality:** User rating >4.0/5.0 (survey)

4. **Cost under control:** Monthly cost <$300 for medium setting

5. **Performance:** Reasoning generation <200ms per fact

6. **User satisfaction:** "Need more context" feedback drops >50%

---

## Document Status

**Status:** ✅ Ready for Implementation
**Dependencies:** Spec 05 (UI to display expanded reasoning)
**Next Steps:** Proceed to Spec 07 (User Feedback System)

**Author:** Claude Sonnet 4.5
**Date:** February 10, 2026
**Version:** 1.0
