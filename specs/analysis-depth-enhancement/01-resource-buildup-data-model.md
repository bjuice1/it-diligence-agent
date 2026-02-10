# Specification 01: Resource Buildup Data Model

**Document ID:** SPEC-RESOURCE-01
**Version:** 1.0
**Date:** February 10, 2026
**Status:** Ready for Implementation
**Dependencies:** None (Foundation specification)
**Enables:** Specs 02 (Calculator), 03 (Integration), 04 (Hierarchical), 05 (UI)

---

## Overview

This specification defines the **ResourceBuildUp** data model and its supporting structures, providing the foundational architecture for transparent resource planning in IT diligence analysis. The model parallels the existing `CostBuildUp` framework's excellence while focusing on FTE allocation, effort calculation, skill requirements, and resource sourcing.

**Purpose:** Enable the same level of transparency for resource planning that currently exists for cost estimation.

**Problem Solved:** Addresses critical user feedback: *"Resource buildup lens is another cyphen of work"* - currently only basic timeline exists, no FTE breakdown, effort calculation, or skill mapping.

**Success Criteria:** Every finding requiring resources can display: FTE breakdown by role, total effort in person-months, peak headcount, skills required, sourcing mix, assumptions, and confidence level.

---

## Architecture

### System Context

```
┌─────────────────────────────────────────────────────────────┐
│                    IT Diligence Agent                        │
│                                                              │
│  ┌────────────────┐        ┌────────────────┐             │
│  │   Finding      │◄───────┤  CostBuildUp   │ (Existing)  │
│  │   Model        │        │                │             │
│  └────────────────┘        └────────────────┘             │
│         ▲                                                   │
│         │                                                   │
│         │  ┌────────────────┐        ┌──────────────────┐ │
│         └──┤ ResourceBuildUp│◄───────┤ RoleRequirement  │ │
│            │   (NEW)        │        │   (NEW)          │ │
│            └────────────────┘        └──────────────────┘ │
│                    ▲                                        │
│                    │                                        │
│                    │ sourced from                           │
│            ┌───────┴────────┐                              │
│            │  Inventory     │                              │
│            │  Facts         │                              │
│            └────────────────┘                              │
└─────────────────────────────────────────────────────────────┘
```

### Model Relationships

```python
Finding 1──────* ResourceBuildUp
ResourceBuildUp 1──────* RoleRequirement
ResourceBuildUp *──────1 CostBuildUp (bidirectional link)
ResourceBuildUp *──────* Fact (source_facts)
```

### Storage Strategy

**Primary Storage:** JSON field in `Finding` model (`resource_buildup_json`)
- Rationale: Matches `cost_buildup_json` pattern, minimal schema changes
- Serialization: Python dataclass → JSON via `to_dict()` / `from_dict()`
- Alternative: Separate table (more normalized, but adds complexity)

**Secondary Storage:** Embedded RoleRequirement objects within ResourceBuildUp JSON
- Rationale: RoleRequirements are tightly coupled to parent ResourceBuildUp
- No need for independent querying of individual roles

---

## Specification

### 1. ResourceBuildUp Model

#### 1.1 Core Model Definition

```python
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from datetime import datetime

@dataclass
class ResourceBuildUp:
    """
    Comprehensive resource planning transparency for IT separation/migration workstreams.

    Provides FTE breakdown, effort calculation, skill requirements, and sourcing strategy
    with full transparency of assumptions and source data. Analogous to CostBuildUp but
    for human resources instead of financial costs.

    Example Use Case:
        Application Migration workstream needs 6 FTEs for 6 months:
        - 0.5 PM, 1.0 Architect, 3.0 Developers, 2.0 QA, 0.5 DevOps
        - Total: 34 person-months, peak headcount 6 FTEs in months 3-5
        - Skills: Java, React, AWS, PostgreSQL
        - 60% internal, 30% contractor, 10% vendor
    """

    # Identity
    id: str                                    # Unique identifier (RB-{workstream}-{timestamp})
    workstream: str                            # "application_migration", "identity_access", etc.
    workstream_display: str                    # "Application Migration" (human-readable)

    # Duration
    duration_months_low: float                 # Minimum duration estimate
    duration_months_high: float                # Maximum duration estimate
    duration_confidence: str                   # "high", "medium", "low"

    # FTE Breakdown
    roles: List['RoleRequirement']             # Detailed role-by-role breakdown
    total_effort_pm: float                     # Sum of all role efforts (person-months)
    peak_headcount: int                        # Maximum concurrent FTEs required
    peak_period: str                           # "Months 3-5" or "Q2 2026"

    # Skills & Sourcing
    skills_required: List[str]                 # ["Java", "AWS", "PostgreSQL", ...]
    skill_criticality: Dict[str, str]          # {"Java": "critical", "PostgreSQL": "important"}
    sourcing_mix: Dict[str, float]             # {"internal": 0.6, "contractor": 0.3, "vendor": 0.1}
    sourcing_rationale: str                    # Why this mix (e.g., "Limited internal SAP expertise")

    # Transparency & Provenance
    estimation_method: str                     # "benchmark", "expert_judgment", "historical", "hybrid"
    estimation_source: str                     # "Gartner 2025", "Prior migration project", etc.
    benchmark_reference: Optional[str]         # URL or citation for benchmark
    assumptions: List[str]                     # ["Team has cloud experience", "APIs documented"]
    risks: List[str]                           # ["Key person risk", "Skill gap in legacy tech"]
    source_facts: List[str]                    # Fact IDs that drove resource needs (F-APP-001, F-INFRA-012)
    confidence: float                          # 0.0-1.0, overall confidence in estimate

    # Linking
    finding_id: str                            # Parent finding
    drives_cost_buildup_id: Optional[str]      # Linked CostBuildUp (labor cost derived from this)

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None           # User or "system" for auto-generated
    version: int = 1                           # For versioning if estimates change

    def calculate_total_effort(self) -> float:
        """Sum effort across all roles."""
        return sum(role.effort_pm for role in self.roles)

    def calculate_peak_headcount(self) -> int:
        """Calculate maximum concurrent FTEs (assumes all roles overlap at peak)."""
        return sum(int(role.fte) + (1 if role.fte % 1 >= 0.5 else 0) for role in self.roles)

    def get_role_by_name(self, role_name: str) -> Optional['RoleRequirement']:
        """Find a specific role in the breakdown."""
        return next((r for r in self.roles if r.role == role_name), None)

    def to_dict(self) -> Dict:
        """Serialize to JSON for storage in Finding.resource_buildup_json."""
        return {
            'id': self.id,
            'workstream': self.workstream,
            'workstream_display': self.workstream_display,
            'duration_months_low': self.duration_months_low,
            'duration_months_high': self.duration_months_high,
            'duration_confidence': self.duration_confidence,
            'roles': [role.to_dict() for role in self.roles],
            'total_effort_pm': self.total_effort_pm,
            'peak_headcount': self.peak_headcount,
            'peak_period': self.peak_period,
            'skills_required': self.skills_required,
            'skill_criticality': self.skill_criticality,
            'sourcing_mix': self.sourcing_mix,
            'sourcing_rationale': self.sourcing_rationale,
            'estimation_method': self.estimation_method,
            'estimation_source': self.estimation_source,
            'benchmark_reference': self.benchmark_reference,
            'assumptions': self.assumptions,
            'risks': self.risks,
            'source_facts': self.source_facts,
            'confidence': self.confidence,
            'finding_id': self.finding_id,
            'drives_cost_buildup_id': self.drives_cost_buildup_id,
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by,
            'version': self.version,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ResourceBuildUp':
        """Deserialize from JSON."""
        roles_data = data.pop('roles', [])
        created_at_str = data.pop('created_at', None)

        resource_buildup = cls(
            **{k: v for k, v in data.items() if k in cls.__annotations__}
        )

        resource_buildup.roles = [RoleRequirement.from_dict(r) for r in roles_data]
        if created_at_str:
            resource_buildup.created_at = datetime.fromisoformat(created_at_str)

        return resource_buildup

    def format_summary(self, detailed: bool = False) -> str:
        """
        Format resource buildup for display.

        Args:
            detailed: If True, includes full role breakdown and assumptions

        Returns:
            Formatted string for UI display
        """
        lines = []

        # Header
        lines.append(f"📊 {self.workstream_display}")
        lines.append(f"Duration: {self.duration_months_low}-{self.duration_months_high} months")
        lines.append(f"Total Effort: {self.total_effort_pm:.1f} person-months")
        lines.append(f"Peak Headcount: {self.peak_headcount} FTEs ({self.peak_period})")
        lines.append("")

        # Role Breakdown
        lines.append("👥 Resource Breakdown:")
        for role in sorted(self.roles, key=lambda r: r.effort_pm, reverse=True):
            lines.append(f"  • {role.role}: {role.fte} FTE × {role.duration_months:.1f} mo = {role.effort_pm:.1f} PM")
            if detailed and role.skills:
                lines.append(f"    Skills: {', '.join(role.skills)}")
        lines.append("")

        # Skills Summary
        critical_skills = [s for s, c in self.skill_criticality.items() if c == "critical"]
        if critical_skills:
            lines.append(f"🎯 Critical Skills: {', '.join(critical_skills)}")

        # Sourcing
        sourcing_display = ", ".join([f"{k}: {int(v*100)}%" for k, v in self.sourcing_mix.items()])
        lines.append(f"📋 Sourcing Mix: {sourcing_display}")
        if self.sourcing_rationale:
            lines.append(f"   Rationale: {self.sourcing_rationale}")
        lines.append("")

        # Transparency
        lines.append(f"📐 Method: {self.estimation_method.replace('_', ' ').title()}")
        if self.estimation_source:
            lines.append(f"📚 Source: {self.estimation_source}")
        lines.append(f"✅ Confidence: {self._confidence_label(self.confidence)}")

        if detailed:
            lines.append("")
            lines.append("🔍 Assumptions:")
            for assumption in self.assumptions:
                lines.append(f"  • {assumption}")

            if self.risks:
                lines.append("")
                lines.append("⚠️ Risks:")
                for risk in self.risks:
                    lines.append(f"  • {risk}")

        return "\n".join(lines)

    def _confidence_label(self, score: float) -> str:
        """Convert confidence score to human-readable label."""
        if score >= 0.8:
            return f"High ({int(score*100)}%)"
        elif score >= 0.5:
            return f"Medium ({int(score*100)}%)"
        else:
            return f"Low ({int(score*100)}%)"
```

#### 1.2 Field Specifications

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | str | Format: `RB-{workstream}-{timestamp}` | Unique identifier |
| `workstream` | str | snake_case, max 50 chars | Internal key (e.g., "application_migration") |
| `workstream_display` | str | max 100 chars | Human-readable (e.g., "Application Migration") |
| `duration_months_low` | float | >= 0.5, <= 60 | Minimum duration in months |
| `duration_months_high` | float | >= duration_months_low, <= 60 | Maximum duration in months |
| `duration_confidence` | str | Enum: "high", "medium", "low" | Confidence in duration estimate |
| `roles` | List[RoleRequirement] | min 1, max 20 | FTE breakdown by role |
| `total_effort_pm` | float | >= 0, auto-calculated | Sum of role efforts |
| `peak_headcount` | int | >= 0, auto-calculated | Max concurrent FTEs |
| `peak_period` | str | max 50 chars | When peak occurs (e.g., "Months 3-5") |
| `skills_required` | List[str] | max 50 items, each max 50 chars | Required technical skills |
| `skill_criticality` | Dict[str, str] | Values: "critical", "important", "nice_to_have" | Skill importance |
| `sourcing_mix` | Dict[str, float] | Keys: "internal", "contractor", "vendor"; values sum to 1.0 | Resource sourcing |
| `sourcing_rationale` | str | max 500 chars | Why this sourcing mix |
| `estimation_method` | str | Enum: "benchmark", "expert_judgment", "historical", "hybrid" | How estimated |
| `estimation_source` | str | max 200 chars | Where estimate came from |
| `benchmark_reference` | str (optional) | max 500 chars, URL or citation | Reference link |
| `assumptions` | List[str] | max 20 items, each max 200 chars | Key assumptions made |
| `risks` | List[str] | max 20 items, each max 200 chars | Resource risks |
| `source_facts` | List[str] | Fact IDs, e.g., "F-APP-001" | Evidence trail |
| `confidence` | float | 0.0-1.0 | Overall estimate confidence |
| `finding_id` | str | Must exist in Finding table | Parent finding |
| `drives_cost_buildup_id` | str (optional) | CostBuildUp ID | Linked cost estimate |
| `created_at` | datetime | Auto-set | Creation timestamp |
| `created_by` | str (optional) | max 100 chars | Creator (user or "system") |
| `version` | int | >= 1 | Version number |

---

### 2. RoleRequirement Model

#### 2.1 Core Model Definition

```python
@dataclass
class RoleRequirement:
    """
    Individual role within a resource buildup.

    Specifies FTE allocation, duration, effort calculation, required skills,
    and seniority level for a single role type in a workstream.

    Example:
        Solution Architect: 1.0 FTE × 4 months = 4.0 person-months
        Skills: AWS, Microservices, Architecture patterns
        Seniority: Senior
    """

    # Role Identity
    role: str                          # "Solution Architect", "Senior Developer", "QA Engineer"
    role_category: str                 # "leadership", "architecture", "development", "qa", "ops"

    # FTE Allocation
    fte: float                         # Full-time equivalent (1.0 = full-time, 0.5 = half-time)
    duration_months: float             # How many months this role is needed
    effort_pm: float                   # FTE × duration = person-months (auto-calculated)

    # Phase Allocation (optional)
    phase_allocation: Optional[Dict[str, float]] = None
    # Example: {"planning": 0.25, "execution": 0.5, "testing": 0.25}

    # Skills & Seniority
    skills: List[str] = field(default_factory=list)          # Required technical/domain skills
    seniority: str = "mid"                                    # "junior", "mid", "senior", "lead"
    certifications: List[str] = field(default_factory=list)   # Optional certifications required

    # Cost Multiplier (for labor cost calculation)
    cost_multiplier: float = 1.0       # Relative cost vs. baseline (senior = 1.3, junior = 0.8)

    def calculate_effort(self) -> float:
        """Calculate person-months: FTE × duration."""
        return self.fte * self.duration_months

    def to_dict(self) -> Dict:
        """Serialize for JSON storage."""
        return {
            'role': self.role,
            'role_category': self.role_category,
            'fte': self.fte,
            'duration_months': self.duration_months,
            'effort_pm': self.effort_pm,
            'phase_allocation': self.phase_allocation,
            'skills': self.skills,
            'seniority': self.seniority,
            'certifications': self.certifications,
            'cost_multiplier': self.cost_multiplier,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'RoleRequirement':
        """Deserialize from JSON."""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})

    def format_display(self) -> str:
        """Format role for display."""
        effort_str = f"{self.fte} FTE × {self.duration_months:.1f} mo = {self.effort_pm:.1f} PM"
        seniority_str = f"[{self.seniority.capitalize()}]" if self.seniority != "mid" else ""
        return f"{self.role} {seniority_str}: {effort_str}"
```

#### 2.2 Role Taxonomy

**Standard Roles:**

| Role | Category | Typical FTE Range | Typical Duration | Common Skills |
|------|----------|-------------------|------------------|---------------|
| Project Manager | leadership | 0.3-1.0 | Full duration | PMI, Agile, Stakeholder mgmt |
| Program Manager | leadership | 0.5-1.0 | Full duration | Portfolio mgmt, Governance |
| Solution Architect | architecture | 0.5-2.0 | Planning + execution | Cloud, Integration, Design patterns |
| Enterprise Architect | architecture | 0.2-0.5 | Planning phase | EA frameworks, Strategy |
| Senior Developer | development | 1.0-5.0 | Execution phase | Language-specific, frameworks |
| Mid-Level Developer | development | 2.0-10.0 | Execution phase | Language-specific |
| QA Engineer | qa | 0.5-3.0 | Testing phase | Test automation, Selenium |
| QA Lead | qa | 0.3-1.0 | Testing phase | Test strategy, CI/CD |
| DevOps Engineer | ops | 0.3-2.0 | Build + deployment | CI/CD, Infrastructure as code |
| DBA | ops | 0.2-1.0 | Data migration | SQL, NoSQL, ETL |
| Security Engineer | ops | 0.2-1.0 | Security review | AppSec, Network security |
| Change Manager | leadership | 0.3-0.5 | Transition phase | OCM, Training |
| Business Analyst | leadership | 0.3-1.0 | Planning + execution | Requirements, Process mapping |

**Seniority Levels:**

| Level | Years Experience | Cost Multiplier | Typical Use Cases |
|-------|------------------|-----------------|-------------------|
| Junior | 0-3 years | 0.8 | Simple tasks, supervised work |
| Mid | 3-7 years | 1.0 | Standard workload, independent work |
| Senior | 7-12 years | 1.3 | Complex tasks, mentoring |
| Lead | 12+ years | 1.5 | Technical leadership, architecture |

---

### 3. Database Schema Changes

#### 3.1 Finding Model Updates

```python
# Add to Finding model in web/database.py (around line 883)

class Finding(db.Model, SoftDeleteMixin):
    # ... existing fields ...

    # Existing cost field
    cost_buildup_json = Column(JSON, default=None)  # Line 883 (existing)

    # NEW: Resource buildup field
    resource_buildup_json = Column(JSON, default=None, nullable=True)

    # Helper methods
    def get_resource_buildup(self) -> Optional[ResourceBuildUp]:
        """Deserialize resource buildup from JSON."""
        if not self.resource_buildup_json:
            return None
        try:
            from tools_v2.resource_tools import ResourceBuildUp
            return ResourceBuildUp.from_dict(self.resource_buildup_json)
        except Exception as e:
            logger.error(f"Failed to deserialize resource buildup: {e}")
            return None

    def set_resource_buildup(self, resource_buildup: ResourceBuildUp):
        """Serialize resource buildup to JSON."""
        self.resource_buildup_json = resource_buildup.to_dict()

    def has_resource_buildup(self) -> bool:
        """Check if finding has resource buildup."""
        return self.resource_buildup_json is not None
```

#### 3.2 Migration Script

**File:** `web/migrations/migration_006_add_resource_buildup.py`

```python
"""
Migration 006: Add resource_buildup_json column to Finding model.

This migration adds support for ResourceBuildUp storage in findings,
enabling transparent resource planning with FTE breakdown, effort calculation,
and skill requirements.

Safe to run: Column is nullable, no data loss risk.
"""

from web.database import db, Finding
from sqlalchemy import Column, JSON, text
import logging

logger = logging.getLogger(__name__)

def run_migration(app):
    """
    Add resource_buildup_json column to findings table.

    Args:
        app: Flask application instance with database context
    """
    with app.app_context():
        try:
            # Check if column already exists
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('findings')]

            if 'resource_buildup_json' in columns:
                logger.info("Column 'resource_buildup_json' already exists, skipping migration")
                return

            # Add column (PostgreSQL syntax)
            if db.engine.dialect.name == 'postgresql':
                db.session.execute(text(
                    "ALTER TABLE findings ADD COLUMN resource_buildup_json JSONB"
                ))
            # SQLite syntax
            elif db.engine.dialect.name == 'sqlite':
                db.session.execute(text(
                    "ALTER TABLE findings ADD COLUMN resource_buildup_json TEXT"
                ))
            else:
                # Generic JSON for other databases
                db.session.execute(text(
                    "ALTER TABLE findings ADD COLUMN resource_buildup_json JSON"
                ))

            db.session.commit()
            logger.info("✅ Migration 006 complete: Added resource_buildup_json column")

        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Migration 006 failed: {e}")
            raise

def rollback_migration(app):
    """
    Remove resource_buildup_json column (rollback).

    WARNING: This will delete all resource buildup data!
    """
    with app.app_context():
        try:
            db.session.execute(text(
                "ALTER TABLE findings DROP COLUMN resource_buildup_json"
            ))
            db.session.commit()
            logger.info("✅ Migration 006 rolled back: Removed resource_buildup_json column")

        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Migration 006 rollback failed: {e}")
            raise
```

---

### 4. Validation Rules

#### 4.1 ResourceBuildUp Validation

```python
def validate_resource_buildup(rb: ResourceBuildUp) -> Tuple[bool, List[str]]:
    """
    Validate ResourceBuildUp instance.

    Returns:
        (is_valid, list_of_errors)
    """
    errors = []

    # Duration validation
    if rb.duration_months_low < 0.5:
        errors.append("Duration low must be >= 0.5 months")
    if rb.duration_months_high < rb.duration_months_low:
        errors.append("Duration high must be >= duration low")
    if rb.duration_months_high > 60:
        errors.append("Duration high exceeds maximum (60 months)")

    # Roles validation
    if not rb.roles:
        errors.append("At least one role required")
    if len(rb.roles) > 20:
        errors.append("Too many roles (max 20)")

    # Effort validation
    calculated_effort = sum(role.effort_pm for role in rb.roles)
    if abs(calculated_effort - rb.total_effort_pm) > 0.1:
        errors.append(f"Total effort mismatch: {rb.total_effort_pm} != {calculated_effort}")

    # Sourcing mix validation
    if rb.sourcing_mix:
        total = sum(rb.sourcing_mix.values())
        if abs(total - 1.0) > 0.01:
            errors.append(f"Sourcing mix must sum to 1.0, got {total}")

    # Confidence validation
    if not (0.0 <= rb.confidence <= 1.0):
        errors.append(f"Confidence must be 0.0-1.0, got {rb.confidence}")

    # Skills validation
    if len(rb.skills_required) > 50:
        errors.append("Too many skills (max 50)")

    return (len(errors) == 0, errors)
```

#### 4.2 RoleRequirement Validation

```python
def validate_role_requirement(role: RoleRequirement) -> Tuple[bool, List[str]]:
    """Validate RoleRequirement instance."""
    errors = []

    # FTE validation
    if role.fte < 0:
        errors.append(f"Role {role.role}: FTE must be >= 0")
    if role.fte > 10:
        errors.append(f"Role {role.role}: FTE exceeds maximum (10)")

    # Duration validation
    if role.duration_months < 0:
        errors.append(f"Role {role.role}: Duration must be >= 0")

    # Effort validation
    calculated_effort = role.fte * role.duration_months
    if abs(calculated_effort - role.effort_pm) > 0.01:
        errors.append(f"Role {role.role}: Effort mismatch")

    # Seniority validation
    valid_seniority = ["junior", "mid", "senior", "lead"]
    if role.seniority not in valid_seniority:
        errors.append(f"Role {role.role}: Invalid seniority '{role.seniority}'")

    return (len(errors) == 0, errors)
```

---

### 5. Example Usage

#### 5.1 Creating a ResourceBuildUp

```python
from tools_v2.resource_tools import ResourceBuildUp, RoleRequirement
from datetime import datetime

# Define roles
roles = [
    RoleRequirement(
        role="Project Manager",
        role_category="leadership",
        fte=0.5,
        duration_months=7,
        effort_pm=3.5,
        skills=["PMI", "Agile", "Stakeholder Management"],
        seniority="senior",
        cost_multiplier=1.2
    ),
    RoleRequirement(
        role="Solution Architect",
        role_category="architecture",
        fte=1.0,
        duration_months=4,
        effort_pm=4.0,
        skills=["AWS", "Microservices", "Cloud Architecture"],
        seniority="senior",
        cost_multiplier=1.4
    ),
    RoleRequirement(
        role="Senior Developer",
        role_category="development",
        fte=3.0,
        duration_months=6,
        effort_pm=18.0,
        skills=["Java", "Spring Boot", "React", "PostgreSQL"],
        seniority="senior",
        cost_multiplier=1.3
    ),
    RoleRequirement(
        role="QA Engineer",
        role_category="qa",
        fte=2.0,
        duration_months=3,
        effort_pm=6.0,
        skills=["Selenium", "Test Automation", "CI/CD"],
        seniority="mid",
        cost_multiplier=1.0
    ),
    RoleRequirement(
        role="DevOps Engineer",
        role_category="ops",
        fte=0.5,
        duration_months=5,
        effort_pm=2.5,
        skills=["Docker", "Kubernetes", "Terraform", "AWS"],
        seniority="senior",
        cost_multiplier=1.3
    ),
]

# Create ResourceBuildUp
resource_buildup = ResourceBuildUp(
    id="RB-app-migration-20260210",
    workstream="application_migration",
    workstream_display="Application Migration",
    duration_months_low=6,
    duration_months_high=8,
    duration_confidence="medium",
    roles=roles,
    total_effort_pm=34.0,
    peak_headcount=6,
    peak_period="Months 3-5",
    skills_required=["Java", "Spring Boot", "React", "PostgreSQL", "AWS", "Docker", "Kubernetes"],
    skill_criticality={
        "Java": "critical",
        "Spring Boot": "critical",
        "React": "important",
        "PostgreSQL": "important",
        "AWS": "critical",
        "Docker": "important",
        "Kubernetes": "nice_to_have"
    },
    sourcing_mix={"internal": 0.6, "contractor": 0.3, "vendor": 0.1},
    sourcing_rationale="Limited internal cloud expertise, contractors for specialized skills",
    estimation_method="benchmark",
    estimation_source="Gartner 2025: Application Modernization Benchmarks",
    benchmark_reference="https://www.gartner.com/doc/app-modernization-2025",
    assumptions=[
        "Team has prior cloud migration experience",
        "APIs are well-documented and RESTful",
        "No major architecture changes required",
        "Modern tech stack (Spring Boot 3.x)",
        "Parallel testing with development"
    ],
    risks=[
        "Key person risk: Lead architect may be unavailable in Q2",
        "Skill gap: Limited Kubernetes expertise internally",
        "Dependency: Waiting for network team to provision VPCs"
    ],
    source_facts=["F-APP-001", "F-APP-005", "F-APP-012", "F-INFRA-008"],
    confidence=0.75,
    finding_id="FIND-APP-MIGRATION-001",
    drives_cost_buildup_id="CB-app-migration-labor-20260210",
    created_at=datetime.utcnow(),
    created_by="system",
    version=1
)

# Validate
is_valid, errors = validate_resource_buildup(resource_buildup)
if not is_valid:
    print(f"Validation errors: {errors}")
else:
    print("✅ ResourceBuildUp valid")

# Serialize to JSON for storage
resource_json = resource_buildup.to_dict()

# Store in Finding
finding = Finding.query.get("FIND-APP-MIGRATION-001")
finding.set_resource_buildup(resource_buildup)
db.session.commit()

# Display
print(resource_buildup.format_summary(detailed=True))
```

**Output:**
```
📊 Application Migration
Duration: 6-8 months
Total Effort: 34.0 person-months
Peak Headcount: 6 FTEs (Months 3-5)

👥 Resource Breakdown:
  • Senior Developer: 3.0 FTE × 6.0 mo = 18.0 PM
    Skills: Java, Spring Boot, React, PostgreSQL
  • QA Engineer: 2.0 FTE × 3.0 mo = 6.0 PM
    Skills: Selenium, Test Automation, CI/CD
  • Solution Architect: 1.0 FTE × 4.0 mo = 4.0 PM
    Skills: AWS, Microservices, Cloud Architecture
  • Project Manager: 0.5 FTE × 7.0 mo = 3.5 PM
    Skills: PMI, Agile, Stakeholder Management
  • DevOps Engineer: 0.5 FTE × 5.0 mo = 2.5 PM
    Skills: Docker, Kubernetes, Terraform, AWS

🎯 Critical Skills: Java, Spring Boot, AWS
📋 Sourcing Mix: internal: 60%, contractor: 30%, vendor: 10%
   Rationale: Limited internal cloud expertise, contractors for specialized skills

📐 Method: Benchmark
📚 Source: Gartner 2025: Application Modernization Benchmarks
✅ Confidence: Medium (75%)

🔍 Assumptions:
  • Team has prior cloud migration experience
  • APIs are well-documented and RESTful
  • No major architecture changes required
  • Modern tech stack (Spring Boot 3.x)
  • Parallel testing with development

⚠️ Risks:
  • Key person risk: Lead architect may be unavailable in Q2
  • Skill gap: Limited Kubernetes expertise internally
  • Dependency: Waiting for network team to provision VPCs
```

---

## Benefits

### 1. Transparency Parity with Cost Model
- Users now see **exactly the same level of detail** for resources as they do for costs
- No more "black box" resource estimates
- Builds trust in the analysis

### 2. Actionable Staffing Insights
- FTE breakdown by role enables **actual hiring/contracting decisions**
- Skill requirements guide **recruitment/training planning**
- Sourcing mix informs **make-vs-buy decisions**

### 3. Risk Visibility
- Explicit risk tracking (key person, skill gaps, dependencies)
- Assumptions documented for challenge/validation
- Confidence scoring helps prioritize further research

### 4. Cost Integration Foundation
- ResourceBuildUp → CostBuildUp linking enables **effort-driven cost estimation**
- Validates that labor costs match resource requirements
- Enables what-if analysis (adjust resources → see cost impact)

### 5. Audit Trail
- Source facts tracked (which inventory items drove resource needs)
- Estimation method and source documented
- Versioning supports estimate refinement over time

---

## Expectations

### Success Metrics

**Technical:**
- ✅ 100% of findings with resource needs can store ResourceBuildUp
- ✅ Serialization/deserialization roundtrips without data loss
- ✅ Validation catches 95%+ of data quality issues

**User Value:**
- ✅ Users can answer: "How many developers do I need?" (specific FTE count)
- ✅ Users can answer: "What skills are required?" (explicit list)
- ✅ Users can answer: "How confident are you?" (0.0-1.0 score with rationale)
- ✅ Users can answer: "Where did this estimate come from?" (source facts + benchmark)

**Adoption:**
- ✅ 70%+ of cost-bearing findings also have ResourceBuildUp within 3 months
- ✅ User feedback: "Resource planning is now as clear as cost estimation" (>80% agree)

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Model complexity overwhelming for users** | Medium | Medium | Provide summary view by default, detailed on-demand; progressive disclosure |
| **Effort estimates perceived as inaccurate** | Medium | High | Show confidence levels prominently; document assumptions; allow user overrides |
| **Benchmark data not available for all workstreams** | High | Medium | Support "expert_judgment" method; provide templates; collect historical data over time |
| **RoleRequirement granularity insufficient** | Low | Low | Model is extensible; can add fields like `phase_allocation` without breaking changes |
| **JSON storage limits query performance** | Low | Low | Acceptable for reads; if querying needed, can add indexed columns for key fields |
| **Skills taxonomy inconsistency** | Medium | Low | Provide skill picker UI with standard taxonomy; validation can suggest corrections |

---

## Results Criteria

### Verification Checklist

**Data Model:**
- [ ] ResourceBuildUp dataclass defined with all fields
- [ ] RoleRequirement dataclass defined with all fields
- [ ] to_dict() / from_dict() methods serialize correctly
- [ ] format_summary() produces human-readable output
- [ ] Validation functions catch invalid data

**Database:**
- [ ] Finding.resource_buildup_json column added via migration
- [ ] Column accepts JSON/JSONB data
- [ ] Helper methods (get/set_resource_buildup) work
- [ ] Migration is idempotent (safe to run multiple times)
- [ ] Rollback script available and tested

**Testing:**
- [ ] Unit tests for ResourceBuildUp serialization
- [ ] Unit tests for RoleRequirement calculations
- [ ] Unit tests for validation functions
- [ ] Integration test: Create finding with resource buildup, save, retrieve
- [ ] Edge case tests: Empty roles list, negative FTEs, invalid sourcing mix

**Documentation:**
- [ ] Docstrings complete for all classes and methods
- [ ] Example usage provided
- [ ] Migration instructions documented

**Performance:**
- [ ] ResourceBuildUp creation < 1ms
- [ ] Serialization/deserialization < 5ms
- [ ] No performance regression on Finding model operations

---

## Cross-References

**Enables:**
- **Spec 02:** Resource Calculation Engine will instantiate ResourceBuildUp objects
- **Spec 03:** Resource-Cost Integration will link to CostBuildUp via drives_cost_buildup_id
- **Spec 04:** Hierarchical Breakdown will extend ResourceBuildUp with parent_id field
- **Spec 05:** UI Enhancement will display ResourceBuildUp via format_summary() method

**Depends On:**
- None (foundation specification)

**Related Existing Code:**
- `tools_v2/reasoning_tools.py:376-460` - CostBuildUp model (pattern to follow)
- `web/database.py:844-972` - Finding model (where resource_buildup_json is added)
- `web/database.py:684-776` - Fact model (source_facts reference)

---

## Appendix: Alternative Designs Considered

### Alternative 1: Separate ResourceBuildUp Table

**Pros:**
- More normalized
- Easier to query
- Could join in SQL

**Cons:**
- More complex schema changes
- Requires ORM relationship setup
- Over-engineering for read-heavy use case

**Decision:** Rejected - JSON storage matches CostBuildUp pattern, simpler implementation

### Alternative 2: Flat Role List in ResourceBuildUp

**Pros:**
- Simpler data structure
- Easier to display in table

**Cons:**
- Loses role detail (skills, seniority)
- Can't calculate labor cost by role
- Less actionable

**Decision:** Rejected - RoleRequirement sub-model provides necessary granularity

### Alternative 3: Store Only Total Effort, No Role Breakdown

**Pros:**
- Simplest possible model
- Quick to populate

**Cons:**
- Doesn't address user feedback ("explain WHY")
- Can't show FTE breakdown
- No actionable staffing insights

**Decision:** Rejected - Defeats purpose of transparency initiative

---

**Document Status:** ✅ Ready for Implementation
**Next Steps:** Proceed to Spec 02 (Resource Calculation Engine)
**Last Updated:** February 10, 2026
**Version:** 1.0
