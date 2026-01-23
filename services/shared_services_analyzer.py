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
