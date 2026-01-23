"""
Shared Services Analyzer

Analyzes dependencies on parent company or shared services center.
Identifies hidden headcount needs and generates TSA recommendations.
"""

import logging
import uuid
from typing import List, Dict, Optional, Any

from models.organization_models import (
    SharedServiceDependency,
    TSAItem,
    StaffingNeed,
    RoleCategory
)
from models.organization_stores import SharedServicesSummary

logger = logging.getLogger(__name__)

# Common shared services and their typical FTE equivalents
SHARED_SERVICE_DEFAULTS = {
    "erp_administration": {
        "fte": 2.0,
        "criticality": "critical",
        "tsa_months": 12,
        "roles_needed": ["ERP Administrator", "ERP Developer"]
    },
    "erp_support": {
        "fte": 1.5,
        "criticality": "high",
        "tsa_months": 12,
        "roles_needed": ["ERP Support Analyst"]
    },
    "network_engineering": {
        "fte": 1.0,
        "criticality": "high",
        "tsa_months": 6,
        "roles_needed": ["Network Engineer"]
    },
    "security_operations": {
        "fte": 2.0,
        "criticality": "critical",
        "tsa_months": 12,
        "roles_needed": ["Security Analyst", "Security Engineer"]
    },
    "identity_management": {
        "fte": 0.5,
        "criticality": "high",
        "tsa_months": 6,
        "roles_needed": ["IAM Administrator"]
    },
    "help_desk": {
        "fte": 2.0,
        "criticality": "medium",
        "tsa_months": 3,
        "roles_needed": ["Help Desk Technician"]
    },
    "it_procurement": {
        "fte": 0.5,
        "criticality": "medium",
        "tsa_months": 6,
        "roles_needed": ["IT Procurement Specialist"]
    },
    "database_administration": {
        "fte": 1.0,
        "criticality": "high",
        "tsa_months": 9,
        "roles_needed": ["DBA"]
    },
    "cloud_administration": {
        "fte": 1.0,
        "criticality": "high",
        "tsa_months": 6,
        "roles_needed": ["Cloud Engineer"]
    },
    "application_development": {
        "fte": 2.0,
        "criticality": "medium",
        "tsa_months": 12,
        "roles_needed": ["Developer", "Business Analyst"]
    },
    "it_leadership": {
        "fte": 0.5,
        "criticality": "high",
        "tsa_months": 3,
        "roles_needed": ["IT Manager"]
    },
    "compliance_security": {
        "fte": 0.5,
        "criticality": "high",
        "tsa_months": 6,
        "roles_needed": ["Compliance Analyst"]
    }
}

# Keywords to identify shared services from descriptions
SERVICE_KEYWORDS = {
    "erp_administration": ["erp", "sap", "oracle apps", "dynamics", "netsuite", "enterprise resource"],
    "network_engineering": ["network", "wan", "lan", "firewall", "routing", "switching"],
    "security_operations": ["security", "soc", "threat", "incident response", "vulnerability"],
    "identity_management": ["identity", "active directory", "iam", "sso", "authentication"],
    "help_desk": ["help desk", "service desk", "support", "tier 1"],
    "database_administration": ["database", "dba", "sql server", "oracle db"],
    "cloud_administration": ["cloud", "aws", "azure", "gcp"],
    "application_development": ["development", "programming", "software", "applications"],
    "it_procurement": ["procurement", "purchasing", "vendor management"],
    "compliance_security": ["compliance", "audit", "sox", "hipaa", "pci"]
}

# TSA duration estimation factors (Point 66)
TSA_DURATION_FACTORS = {
    "complexity": {
        "low": 0.75,      # Simple service, reduce duration
        "medium": 1.0,    # Standard duration
        "high": 1.5,      # Complex service, increase duration
        "critical": 2.0   # Business-critical, extend duration
    },
    "replacement_difficulty": {
        "easy": 0.5,      # Easy to replace (common skill)
        "moderate": 1.0,  # Standard replacement
        "hard": 1.5,      # Specialized skill required
        "very_hard": 2.0  # Rare skill or custom system
    },
    "integration_depth": {
        "standalone": 0.5,   # Minimal integration
        "moderate": 1.0,     # Some integration
        "deep": 1.5,         # Deep integration
        "embedded": 2.0      # Deeply embedded in operations
    }
}

# Risk scoring weights (Point 67)
DEPENDENCY_RISK_WEIGHTS = {
    "criticality": 0.30,
    "replacement_difficulty": 0.25,
    "fte_equivalent": 0.15,
    "will_transfer": 0.20,
    "tsa_duration": 0.10
}

# Replacement cost multipliers (Point 68)
REPLACEMENT_COST_RANGES = {
    "low": 0.8,     # Optimistic scenario
    "mid": 1.0,     # Expected scenario
    "high": 1.3     # Conservative scenario
}


class SharedServicesAnalyzer:
    """
    Analyzes shared services dependencies and calculates hidden headcount needs.
    """

    def __init__(self, cost_per_fte: float = 100000):
        self.service_defaults = SHARED_SERVICE_DEFAULTS.copy()
        self.service_keywords = SERVICE_KEYWORDS.copy()
        self.cost_per_fte = cost_per_fte

    def identify_dependencies(
        self,
        facts: List[Dict[str, Any]]
    ) -> List[SharedServiceDependency]:
        """
        Identify shared service dependencies from fact store entries.

        Args:
            facts: List of fact dictionaries

        Returns:
            List of SharedServiceDependency objects
        """
        dependencies = []

        for fact in facts:
            # Look for shared services indicators
            if fact.get('domain') != 'organization':
                continue

            category = fact.get('category', '').lower()
            item = fact.get('item', '').lower()
            details = fact.get('details', {}) if isinstance(fact.get('details'), dict) else {}
            evidence = fact.get('evidence', '').lower()

            # Check for shared services indicators
            is_shared = any([
                category in ['shared_services', 'parent_services', 'corporate_it'],
                'parent' in item or 'corporate' in item or 'shared' in item,
                'parent' in evidence or 'corporate provides' in evidence or 'shared services' in evidence,
                details.get('provider', '').lower() in ['parent', 'corporate', 'shared services']
            ])

            if is_shared:
                dep = self._create_dependency_from_fact(fact)
                if dep:
                    dependencies.append(dep)

        return dependencies

    def _create_dependency_from_fact(
        self,
        fact: Dict[str, Any]
    ) -> Optional[SharedServiceDependency]:
        """Create a SharedServiceDependency from a fact."""
        details = fact.get('details', {}) if isinstance(fact.get('details'), dict) else {}

        service_name = fact.get('item', 'Unknown Service')
        provider = details.get('provider', 'Parent Company')

        # Identify service type
        service_type = self._identify_service_type(service_name)
        defaults = self.service_defaults.get(service_type, {})

        # Get FTE equivalent
        fte = details.get('fte_equivalent') or defaults.get('fte', 1.0)

        # Get criticality
        criticality = details.get('criticality') or defaults.get('criticality', 'medium')

        # Determine if it will transfer
        will_transfer = details.get('will_transfer', False)

        # TSA details
        tsa_candidate = details.get('tsa_candidate', True)
        tsa_months = details.get('tsa_duration_months') or defaults.get('tsa_months', 12)

        return SharedServiceDependency(
            id=f"SS-{uuid.uuid4().hex[:8].upper()}",
            service_name=service_name,
            provider=provider,
            fte_equivalent=float(fte),
            will_transfer=will_transfer,
            criticality=criticality,
            tsa_candidate=tsa_candidate,
            tsa_duration_months=tsa_months,
            description=fact.get('evidence')
        )

    def _identify_service_type(self, service_name: str) -> str:
        """Identify service type from name using keywords."""
        name_lower = service_name.lower()

        for svc_type, keywords in self.service_keywords.items():
            for keyword in keywords:
                if keyword in name_lower:
                    return svc_type

        return "application_support"

    def create_dependency(
        self,
        service_name: str,
        provider: str,
        fte_equivalent: float,
        will_transfer: bool = False,
        criticality: str = "medium",
        tsa_candidate: bool = True,
        tsa_duration_months: int = 12,
        description: Optional[str] = None
    ) -> SharedServiceDependency:
        """Create a shared service dependency manually."""
        return SharedServiceDependency(
            id=f"SS-{uuid.uuid4().hex[:8].upper()}",
            service_name=service_name,
            provider=provider,
            fte_equivalent=fte_equivalent,
            will_transfer=will_transfer,
            criticality=criticality,
            tsa_candidate=tsa_candidate,
            tsa_duration_months=tsa_duration_months,
            description=description
        )

    def calculate_hidden_headcount(
        self,
        dependencies: List[SharedServiceDependency]
    ) -> float:
        """Calculate total hidden headcount need from dependencies."""
        return sum(d.replacement_fte_need for d in dependencies)

    def calculate_hidden_cost(
        self,
        dependencies: List[SharedServiceDependency]
    ) -> float:
        """Calculate total hidden annual cost."""
        return sum(d.replacement_cost_annual for d in dependencies)

    def generate_summary(
        self,
        dependencies: List[SharedServiceDependency]
    ) -> SharedServicesSummary:
        """Generate a summary of shared services dependencies."""
        total_fte = sum(d.fte_equivalent for d in dependencies)
        transferring = sum(d.fte_equivalent for d in dependencies if d.will_transfer)
        non_transferring = sum(d.fte_equivalent for d in dependencies if not d.will_transfer)

        key_concerns = []
        for d in dependencies:
            if d.criticality == 'critical' and not d.will_transfer:
                key_concerns.append(f"Critical service '{d.service_name}' not transferring - immediate action needed")
            elif d.criticality == 'high' and not d.will_transfer:
                key_concerns.append(f"High-priority service '{d.service_name}' requires replacement planning")

        return SharedServicesSummary(
            total_dependencies=len(dependencies),
            total_fte_equivalent=total_fte,
            transferring_fte=transferring,
            non_transferring_fte=non_transferring,
            hidden_headcount_need=self.calculate_hidden_headcount(dependencies),
            hidden_cost_annual=self.calculate_hidden_cost(dependencies),
            tsa_candidate_count=sum(1 for d in dependencies if d.tsa_candidate),
            critical_dependencies=sum(1 for d in dependencies if d.criticality == 'critical'),
            key_concerns=key_concerns
        )

    def generate_tsa_recommendations(
        self,
        dependencies: List[SharedServiceDependency]
    ) -> List[TSAItem]:
        """Generate TSA recommendations for dependencies."""
        tsa_items = []

        for dep in dependencies:
            if not dep.tsa_candidate:
                continue
            if dep.will_transfer:
                continue  # No TSA needed if service transfers

            # Estimate monthly cost (FTE cost / 12, with markup for TSA overhead)
            monthly_cost = (dep.fte_equivalent * self.cost_per_fte / 12) * 1.3

            # Define exit criteria
            if dep.criticality == 'critical':
                exit_criteria = "Internal capability fully operational with documented procedures and trained staff"
            else:
                exit_criteria = "Internal or alternative solution implemented and validated"

            # Define replacement plan
            service_type = self._identify_service_type(dep.service_name)
            defaults = self.service_defaults.get(service_type, {})
            roles_needed = defaults.get('roles_needed', ['IT Specialist'])

            replacement_plan = f"Hire or contract: {', '.join(roles_needed)}"

            tsa_items.append(TSAItem(
                id=f"TSA-{uuid.uuid4().hex[:8].upper()}",
                service=dep.service_name,
                provider=dep.provider,
                duration_months=dep.tsa_duration_months,
                estimated_monthly_cost=monthly_cost,
                exit_criteria=exit_criteria,
                replacement_plan=replacement_plan,
                related_dependency_id=dep.id
            ))

        # Sort by criticality (critical first)
        criticality_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        tsa_items.sort(key=lambda t: criticality_order.get(
            next((d.criticality for d in dependencies if d.id == t.related_dependency_id), 'low'), 3
        ))

        return tsa_items

    def generate_staffing_needs(
        self,
        dependencies: List[SharedServiceDependency]
    ) -> List[StaffingNeed]:
        """Generate staffing needs to replace shared services."""
        staffing_needs = []

        for dep in dependencies:
            if dep.will_transfer:
                continue  # No staffing need if service transfers

            service_type = self._identify_service_type(dep.service_name)
            defaults = self.service_defaults.get(service_type, {})
            roles_needed = defaults.get('roles_needed', ['IT Specialist'])

            # Distribute FTE across needed roles
            fte_per_role = dep.fte_equivalent / len(roles_needed) if roles_needed else dep.fte_equivalent

            for role in roles_needed:
                # Map role to category
                category = self._role_to_category(role)

                # Estimate salary based on role
                salary = self._estimate_salary(role)

                staffing_needs.append(StaffingNeed(
                    id=f"SN-{uuid.uuid4().hex[:8].upper()}",
                    role=role,
                    category=category,
                    fte_count=fte_per_role,
                    urgency=dep.urgency,
                    reason=f"Replace shared service: {dep.service_name} from {dep.provider}",
                    estimated_salary=salary,
                    source="shared_services"
                ))

        return staffing_needs

    def _role_to_category(self, role: str) -> RoleCategory:
        """Map a role name to a category."""
        role_lower = role.lower()

        if any(x in role_lower for x in ['security', 'compliance', 'iam']):
            return RoleCategory.SECURITY
        elif any(x in role_lower for x in ['network', 'cloud', 'system', 'infrastructure']):
            return RoleCategory.INFRASTRUCTURE
        elif any(x in role_lower for x in ['developer', 'analyst', 'erp', 'application']):
            return RoleCategory.APPLICATIONS
        elif any(x in role_lower for x in ['dba', 'database', 'data']):
            return RoleCategory.DATA
        elif any(x in role_lower for x in ['help desk', 'support', 'technician']):
            return RoleCategory.SERVICE_DESK
        elif any(x in role_lower for x in ['manager', 'director', 'lead']):
            return RoleCategory.LEADERSHIP
        else:
            return RoleCategory.OTHER

    def _estimate_salary(self, role: str) -> float:
        """Estimate salary for a role."""
        role_lower = role.lower()

        # Rough salary estimates
        if any(x in role_lower for x in ['director', 'manager']):
            return 130000
        elif any(x in role_lower for x in ['engineer', 'developer', 'architect']):
            return 110000
        elif any(x in role_lower for x in ['analyst', 'administrator', 'admin', 'dba']):
            return 90000
        elif any(x in role_lower for x in ['specialist']):
            return 75000
        elif any(x in role_lower for x in ['technician', 'support']):
            return 55000
        else:
            return 80000

    # =========================================================================
    # TSA Duration Estimation (Point 66)
    # =========================================================================

    def estimate_tsa_duration(
        self,
        dependency: SharedServiceDependency,
        complexity: str = "medium",
        replacement_difficulty: str = "moderate",
        integration_depth: str = "moderate"
    ) -> Dict[str, Any]:
        """
        Estimate TSA duration based on multiple factors (Point 66).

        Args:
            dependency: The shared service dependency
            complexity: low/medium/high/critical
            replacement_difficulty: easy/moderate/hard/very_hard
            integration_depth: standalone/moderate/deep/embedded

        Returns:
            Dict with duration estimate and breakdown
        """
        # Get base duration
        service_type = self._identify_service_type(dependency.service_name)
        defaults = self.service_defaults.get(service_type, {})
        base_months = defaults.get('tsa_months', 12)

        # Apply factors
        complexity_factor = TSA_DURATION_FACTORS["complexity"].get(complexity, 1.0)
        difficulty_factor = TSA_DURATION_FACTORS["replacement_difficulty"].get(
            replacement_difficulty, 1.0
        )
        integration_factor = TSA_DURATION_FACTORS["integration_depth"].get(
            integration_depth, 1.0
        )

        # Calculate adjusted duration
        adjusted_months = base_months * complexity_factor * difficulty_factor * integration_factor

        # Apply FTE scaling (more FTE = longer transition)
        fte_factor = 1.0 + (dependency.fte_equivalent - 1) * 0.1
        adjusted_months *= fte_factor

        # Round to nearest month
        estimated_months = max(3, round(adjusted_months))

        return {
            'service_name': dependency.service_name,
            'base_duration_months': base_months,
            'complexity': complexity,
            'complexity_factor': complexity_factor,
            'replacement_difficulty': replacement_difficulty,
            'difficulty_factor': difficulty_factor,
            'integration_depth': integration_depth,
            'integration_factor': integration_factor,
            'fte_scaling_factor': fte_factor,
            'estimated_duration_months': estimated_months,
            'recommended_range': {
                'minimum': max(3, estimated_months - 2),
                'recommended': estimated_months,
                'conservative': estimated_months + 3
            }
        }

    # =========================================================================
    # Dependency Risk Scoring (Point 67)
    # =========================================================================

    def calculate_dependency_risk_score(
        self,
        dependency: SharedServiceDependency
    ) -> Dict[str, Any]:
        """
        Calculate risk score for a shared service dependency (Point 67).

        Returns score 0-100 with breakdown.
        """
        scores = {}

        # Criticality score (0-100)
        criticality_scores = {
            'critical': 100,
            'high': 75,
            'medium': 50,
            'low': 25
        }
        scores['criticality'] = criticality_scores.get(dependency.criticality, 50)

        # Replacement difficulty (based on FTE and service type)
        service_type = self._identify_service_type(dependency.service_name)
        base_difficulty = {
            'erp_administration': 80,
            'security_operations': 75,
            'database_administration': 70,
            'network_engineering': 65,
            'cloud_administration': 65,
            'identity_management': 60,
            'application_development': 55,
            'compliance_security': 50,
            'help_desk': 35,
            'it_procurement': 30
        }.get(service_type, 50)
        scores['replacement_difficulty'] = base_difficulty

        # FTE scaling (more FTE = higher risk)
        fte_score = min(100, dependency.fte_equivalent * 25)
        scores['fte_equivalent'] = fte_score

        # Transfer risk (not transferring = higher risk)
        scores['will_transfer'] = 0 if dependency.will_transfer else 100

        # TSA duration risk
        tsa_score = min(100, dependency.tsa_duration_months * 8)
        scores['tsa_duration'] = tsa_score

        # Calculate weighted total
        total_score = 0
        for factor, weight in DEPENDENCY_RISK_WEIGHTS.items():
            total_score += scores.get(factor, 0) * weight

        # Classify risk level
        if total_score >= 75:
            risk_level = "critical"
        elif total_score >= 50:
            risk_level = "high"
        elif total_score >= 25:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            'dependency_id': dependency.id,
            'service_name': dependency.service_name,
            'total_risk_score': round(total_score, 1),
            'risk_level': risk_level,
            'score_breakdown': scores,
            'weights_applied': DEPENDENCY_RISK_WEIGHTS.copy(),
            'mitigation_priority': 1 if total_score >= 75 else (2 if total_score >= 50 else 3)
        }

    def rank_dependencies_by_risk(
        self,
        dependencies: List[SharedServiceDependency]
    ) -> List[Dict]:
        """Rank all dependencies by risk score."""
        scored = [self.calculate_dependency_risk_score(d) for d in dependencies]
        scored.sort(key=lambda x: x['total_risk_score'], reverse=True)
        return scored

    # =========================================================================
    # Replacement Cost Ranges (Point 68)
    # =========================================================================

    def calculate_replacement_cost_range(
        self,
        dependency: SharedServiceDependency
    ) -> Dict[str, float]:
        """
        Calculate low/mid/high replacement cost estimates (Point 68).

        Returns dict with three cost scenarios.
        """
        base_cost = dependency.replacement_cost_annual

        return {
            'low': base_cost * REPLACEMENT_COST_RANGES['low'],
            'mid': base_cost * REPLACEMENT_COST_RANGES['mid'],
            'high': base_cost * REPLACEMENT_COST_RANGES['high'],
            'service_name': dependency.service_name,
            'fte_equivalent': dependency.fte_equivalent,
            'cost_per_fte': self.cost_per_fte,
            'notes': self._get_cost_range_notes(dependency)
        }

    def _get_cost_range_notes(self, dependency: SharedServiceDependency) -> str:
        """Generate notes explaining cost range."""
        notes = []

        if dependency.criticality == 'critical':
            notes.append("Critical service may require premium talent")

        if dependency.fte_equivalent > 2:
            notes.append("Multi-FTE service may have team-building costs")

        service_type = self._identify_service_type(dependency.service_name)
        if service_type in ['erp_administration', 'security_operations']:
            notes.append("Specialized skills may be above market rate")

        if not dependency.will_transfer:
            notes.append("No knowledge transfer from incumbent")

        return "; ".join(notes) if notes else "Standard replacement scenario"

    def calculate_total_replacement_cost_range(
        self,
        dependencies: List[SharedServiceDependency]
    ) -> Dict[str, float]:
        """Calculate aggregate replacement cost ranges."""
        totals = {'low': 0, 'mid': 0, 'high': 0}

        for dep in dependencies:
            if dep.will_transfer:
                continue
            costs = self.calculate_replacement_cost_range(dep)
            totals['low'] += costs['low']
            totals['mid'] += costs['mid']
            totals['high'] += costs['high']

        return totals

    # =========================================================================
    # Criticality Ranking (Point 69)
    # =========================================================================

    def rank_by_criticality(
        self,
        dependencies: List[SharedServiceDependency]
    ) -> Dict[str, List[SharedServiceDependency]]:
        """
        Rank dependencies by business impact (Point 69).

        Returns dict grouping dependencies by criticality level.
        """
        rankings = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': []
        }

        for dep in dependencies:
            level = dep.criticality
            if level in rankings:
                rankings[level].append(dep)
            else:
                rankings['medium'].append(dep)

        # Sort within each level by FTE (higher FTE first)
        for level in rankings:
            rankings[level].sort(key=lambda d: d.fte_equivalent, reverse=True)

        return rankings

    def get_critical_dependencies_summary(
        self,
        dependencies: List[SharedServiceDependency]
    ) -> Dict[str, Any]:
        """Get summary of critical dependencies requiring immediate attention."""
        critical = [d for d in dependencies if d.criticality == 'critical']
        high = [d for d in dependencies if d.criticality == 'high']

        return {
            'critical_count': len(critical),
            'high_count': len(high),
            'critical_services': [d.service_name for d in critical],
            'high_priority_services': [d.service_name for d in high],
            'total_critical_fte': sum(d.fte_equivalent for d in critical),
            'total_high_fte': sum(d.fte_equivalent for d in high),
            'immediate_attention_required': len(critical) > 0
        }

    # =========================================================================
    # Day 1 Readiness Checklist (Point 70)
    # =========================================================================

    def generate_day1_checklist(
        self,
        dependencies: List[SharedServiceDependency]
    ) -> List[Dict[str, Any]]:
        """
        Generate Day 1 readiness checklist (Point 70).

        Returns list of action items needed before Day 1.
        """
        checklist = []

        # Group by criticality
        ranked = self.rank_by_criticality(dependencies)

        # Critical items first
        for dep in ranked['critical']:
            if not dep.will_transfer:
                checklist.append({
                    'priority': 'P0',
                    'category': 'Critical Service Coverage',
                    'action': f"Confirm TSA coverage for {dep.service_name}",
                    'responsible': 'Deal Lead',
                    'due': 'Signing',
                    'dependency_id': dep.id,
                    'risk_if_missed': 'Business continuity failure'
                })
                checklist.append({
                    'priority': 'P0',
                    'category': 'Critical Service Coverage',
                    'action': f"Identify interim support contact for {dep.service_name}",
                    'responsible': 'IT Lead',
                    'due': 'Day 1',
                    'dependency_id': dep.id,
                    'risk_if_missed': 'No escalation path for issues'
                })

        # High priority items
        for dep in ranked['high']:
            if not dep.will_transfer:
                checklist.append({
                    'priority': 'P1',
                    'category': 'High Priority Service',
                    'action': f"Document current state of {dep.service_name}",
                    'responsible': 'IT Lead',
                    'due': 'Week 1',
                    'dependency_id': dep.id,
                    'risk_if_missed': 'Knowledge loss during transition'
                })

        # Access and credentials
        for dep in dependencies:
            if dep.tsa_candidate:
                checklist.append({
                    'priority': 'P1',
                    'category': 'Access Management',
                    'action': f"Verify continued access for {dep.service_name} under TSA",
                    'responsible': 'Security Lead',
                    'due': 'Day 1',
                    'dependency_id': dep.id,
                    'risk_if_missed': 'Service access failure'
                })

        # Communication items
        checklist.append({
            'priority': 'P0',
            'category': 'Communication',
            'action': 'Distribute TSA contact list to IT staff',
            'responsible': 'IT Director',
            'due': 'Day 1',
            'dependency_id': None,
            'risk_if_missed': 'Staff unable to get support'
        })

        checklist.append({
            'priority': 'P0',
            'category': 'Communication',
            'action': 'Brief service desk on escalation procedures for TSA services',
            'responsible': 'Service Desk Manager',
            'due': 'Day 1',
            'dependency_id': None,
            'risk_if_missed': 'Incorrect routing of support requests'
        })

        # Sort by priority
        priority_order = {'P0': 0, 'P1': 1, 'P2': 2}
        checklist.sort(key=lambda x: (priority_order.get(x['priority'], 3), x['due']))

        return checklist

    def generate_day1_readiness_report(
        self,
        dependencies: List[SharedServiceDependency]
    ) -> Dict[str, Any]:
        """Generate comprehensive Day 1 readiness report."""
        checklist = self.generate_day1_checklist(dependencies)
        risk_rankings = self.rank_dependencies_by_risk(dependencies)
        critical_summary = self.get_critical_dependencies_summary(dependencies)
        cost_range = self.calculate_total_replacement_cost_range(dependencies)

        p0_items = [c for c in checklist if c['priority'] == 'P0']
        p1_items = [c for c in checklist if c['priority'] == 'P1']

        return {
            'executive_summary': {
                'total_dependencies': len(dependencies),
                'critical_dependencies': critical_summary['critical_count'],
                'high_priority_dependencies': critical_summary['high_count'],
                'p0_actions_required': len(p0_items),
                'p1_actions_required': len(p1_items),
                'estimated_replacement_cost': cost_range
            },
            'critical_summary': critical_summary,
            'risk_rankings': risk_rankings[:5],  # Top 5 risks
            'day1_checklist': checklist,
            'tsa_services': [d.service_name for d in dependencies if d.tsa_candidate],
            'recommendations': [
                "Complete all P0 items before Day 1",
                "Establish TSA governance structure",
                "Create weekly TSA status reporting",
                "Begin replacement planning for critical services"
            ]
        }
