"""
MSP/Outsourcing Parser

Parses MSP and outsourcing information from:
- Fact store entries
- Structured JSON input
- Manual entry

Calculates FTE equivalents and replacement costs for MSP services.
"""

import logging
import uuid
from typing import List, Dict, Optional, Any

from models.organization_models import (
    MSPService,
    MSPRelationship,
    DependencyLevel
)

logger = logging.getLogger(__name__)


# Standard FTE equivalents for common MSP services
# These are defaults that can be overridden
SERVICE_FTE_DEFAULTS = {
    # Help Desk / Service Desk
    "24x7_helpdesk": {
        "fte": 4.0,
        "description": "24/7 help desk coverage requires ~4 FTE for full shift coverage",
        "coverage": "24x7"
    },
    "business_hours_helpdesk": {
        "fte": 1.5,
        "description": "Business hours help desk (8x5)",
        "coverage": "business_hours"
    },
    "help_desk": {
        "fte": 2.0,
        "description": "General help desk (assume extended hours)",
        "coverage": "business_hours"
    },

    # Infrastructure Monitoring
    "infrastructure_monitoring_24x7": {
        "fte": 2.5,
        "description": "24/7 infrastructure/NOC monitoring",
        "coverage": "24x7"
    },
    "infrastructure_monitoring": {
        "fte": 1.0,
        "description": "Infrastructure monitoring (business hours)",
        "coverage": "business_hours"
    },
    "noc": {
        "fte": 3.0,
        "description": "Network Operations Center",
        "coverage": "24x7"
    },

    # Security
    "soc_24x7": {
        "fte": 4.0,
        "description": "24/7 Security Operations Center",
        "coverage": "24x7"
    },
    "security_operations": {
        "fte": 2.5,
        "description": "Security operations/monitoring",
        "coverage": "business_hours"
    },
    "managed_siem": {
        "fte": 1.5,
        "description": "Managed SIEM service",
        "coverage": "24x7"
    },
    "managed_edr": {
        "fte": 1.0,
        "description": "Managed EDR/endpoint security",
        "coverage": "24x7"
    },
    "vulnerability_management": {
        "fte": 0.5,
        "description": "Vulnerability scanning and management",
        "coverage": "business_hours"
    },

    # Infrastructure Management
    "managed_network": {
        "fte": 1.5,
        "description": "Managed network services",
        "coverage": "business_hours"
    },
    "managed_servers": {
        "fte": 1.0,
        "description": "Managed server administration",
        "coverage": "business_hours"
    },
    "managed_backup": {
        "fte": 0.5,
        "description": "Managed backup services",
        "coverage": "business_hours"
    },
    "managed_patching": {
        "fte": 0.5,
        "description": "Managed patching services",
        "coverage": "business_hours"
    },
    "cloud_management": {
        "fte": 1.5,
        "description": "Managed cloud services (AWS/Azure)",
        "coverage": "business_hours"
    },

    # Desktop/End User
    "managed_desktop": {
        "fte_per_100_users": 0.5,
        "description": "Managed desktop per 100 users",
        "coverage": "business_hours"
    },
    "desktop_support": {
        "fte": 1.0,
        "description": "Desktop support services",
        "coverage": "business_hours"
    },

    # Application Support
    "erp_support": {
        "fte": 2.0,
        "description": "ERP application support",
        "coverage": "business_hours"
    },
    "application_support": {
        "fte": 1.5,
        "description": "General application support",
        "coverage": "business_hours"
    },
    "application_development": {
        "fte": 2.0,
        "description": "Application development services",
        "coverage": "business_hours"
    },

    # Full Outsource
    "full_it_outsource": {
        "fte": 8.0,
        "description": "Fully outsourced IT (small org baseline)",
        "coverage": "business_hours"
    },
    "co_managed_it": {
        "fte": 4.0,
        "description": "Co-managed IT services",
        "coverage": "business_hours"
    }
}

# Keywords to identify services from text descriptions
SERVICE_KEYWORDS = {
    "help_desk": ["help desk", "helpdesk", "service desk", "user support", "tier 1", "tier 2"],
    "infrastructure_monitoring": ["monitoring", "noc", "network operations", "infrastructure monitoring"],
    "security_operations": ["soc", "security operations", "security monitoring", "threat"],
    "managed_siem": ["siem", "log management", "security information"],
    "managed_edr": ["edr", "endpoint detection", "endpoint security", "antivirus", "anti-malware"],
    "managed_network": ["network management", "network support", "wan", "lan management"],
    "managed_servers": ["server management", "server support", "server admin"],
    "managed_backup": ["backup", "disaster recovery", "dr services"],
    "managed_patching": ["patching", "patch management", "updates"],
    "cloud_management": ["cloud", "aws", "azure", "gcp", "cloud management"],
    "desktop_support": ["desktop", "workstation", "end user computing"],
    "erp_support": ["erp", "sap", "oracle", "dynamics", "netsuite"],
    "application_support": ["application support", "app support", "software support"]
}


class MSPParser:
    """
    Parses and creates MSP relationship records.

    Can parse from:
    - Fact store entries
    - Structured dictionaries
    - Manual service lists
    """

    def __init__(self):
        self.service_defaults = SERVICE_FTE_DEFAULTS.copy()
        self.service_keywords = SERVICE_KEYWORDS.copy()

    def parse_from_facts(
        self,
        facts: List[Dict[str, Any]],
        entity: str = "target"
    ) -> List[MSPRelationship]:
        """
        Parse MSP relationships from fact store entries.

        Looks for facts with category "outsourcing" or "vendors"
        in the organization domain.

        Args:
            facts: List of fact dictionaries from FactStore
            entity: Entity to assign to relationships

        Returns:
            List of MSPRelationship objects
        """
        relationships = []
        vendor_facts = {}

        # Group facts by vendor name
        for fact in facts:
            if fact.get('domain') != 'organization':
                continue
            if fact.get('category') not in ['outsourcing', 'vendors', 'msp']:
                continue

            vendor_name = fact.get('item') or fact.get('vendor_name')
            if not vendor_name:
                continue

            if vendor_name not in vendor_facts:
                vendor_facts[vendor_name] = []
            vendor_facts[vendor_name].append(fact)

        # Create relationship for each vendor
        for vendor_name, facts_list in vendor_facts.items():
            try:
                relationship = self._create_relationship_from_facts(
                    vendor_name, facts_list, entity
                )
                relationships.append(relationship)
            except Exception as e:
                logger.warning(f"Failed to create relationship for {vendor_name}: {e}")

        return relationships

    def _create_relationship_from_facts(
        self,
        vendor_name: str,
        facts: List[Dict],
        entity: str
    ) -> MSPRelationship:
        """Create an MSP relationship from a list of facts about a vendor."""

        services = []
        contract_value = 0
        contract_expiry = None
        contract_start = None
        notice_period = 30
        dependency_level = DependencyLevel.PARTIAL

        for fact in facts:
            details = fact.get('details', {}) if isinstance(fact.get('details'), dict) else {}

            # Extract services
            services_provided = details.get('services_provided') or fact.get('services_provided')
            if services_provided:
                if isinstance(services_provided, str):
                    services_provided = [s.strip() for s in services_provided.split(',')]

                for svc_name in services_provided:
                    service = self._create_service(svc_name, details)
                    services.append(service)

            # Extract contract details
            if details.get('contract_value'):
                contract_value = self._parse_currency(details['contract_value'])
            if details.get('contract_expiry'):
                contract_expiry = str(details['contract_expiry'])
            if details.get('contract_start'):
                contract_start = str(details['contract_start'])
            if details.get('notice_period'):
                notice_period = int(details['notice_period'])

            # Determine dependency level
            contract_type = details.get('contract_type', '').lower()
            if 'full' in contract_type or 'complete' in contract_type:
                dependency_level = DependencyLevel.FULL
            elif 'staff' in contract_type or 'supplement' in contract_type:
                dependency_level = DependencyLevel.SUPPLEMENTAL

        # If no services were explicitly listed, try to infer from vendor name/notes
        if not services:
            # Create a generic service based on vendor name
            service = self._create_service(f"IT Services from {vendor_name}", {})
            services.append(service)

        return MSPRelationship(
            id=f"MSP-{uuid.uuid4().hex[:8].upper()}",
            vendor_name=vendor_name,
            services=services,
            contract_value_annual=contract_value,
            contract_start=contract_start,
            contract_expiry=contract_expiry,
            notice_period_days=notice_period,
            dependency_level=dependency_level,
            entity=entity
        )

    def _create_service(
        self,
        service_name: str,
        details: Dict
    ) -> MSPService:
        """Create an MSPService from a service name and details."""

        # Determine service type from name
        service_type = self._identify_service_type(service_name)

        # Get FTE equivalent
        fte = details.get('fte_equivalent')
        if not fte and service_type in self.service_defaults:
            fte = self.service_defaults[service_type].get('fte', 1.0)
        elif not fte:
            fte = 1.0  # Default fallback

        # Get coverage
        coverage = details.get('coverage')
        if not coverage and service_type in self.service_defaults:
            coverage = self.service_defaults[service_type].get('coverage', 'business_hours')
        elif not coverage:
            coverage = 'business_hours'

        # Determine criticality
        criticality = details.get('criticality', 'medium')
        if service_type in ['soc_24x7', 'security_operations', 'erp_support', 'full_it_outsource']:
            criticality = 'critical'
        elif service_type in ['24x7_helpdesk', 'infrastructure_monitoring_24x7', 'noc']:
            criticality = 'high'

        # Check for internal backup
        internal_backup = details.get('internal_backup', False)

        return MSPService(
            service_name=service_name,
            fte_equivalent=float(fte),
            coverage=coverage,
            criticality=criticality,
            internal_backup=internal_backup,
            description=details.get('description')
        )

    def _identify_service_type(self, service_name: str) -> str:
        """Identify the service type from a service name using keywords."""
        name_lower = service_name.lower()

        for service_type, keywords in self.service_keywords.items():
            for keyword in keywords:
                if keyword in name_lower:
                    return service_type

        return "application_support"  # Default fallback

    def _parse_currency(self, value: Any) -> float:
        """Parse a currency value."""
        if isinstance(value, (int, float)):
            return float(value)

        if not value:
            return 0.0

        value_str = str(value)
        # Remove currency symbols and commas
        import re
        cleaned = re.sub(r'[$£€,]', '', value_str)

        # Handle K/M notation
        if cleaned.upper().endswith('K'):
            return float(cleaned[:-1]) * 1000
        elif cleaned.upper().endswith('M'):
            return float(cleaned[:-1]) * 1000000

        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    def create_relationship(
        self,
        vendor_name: str,
        services: List[Dict],
        contract_value: float = 0,
        contract_expiry: Optional[str] = None,
        dependency_level: str = "partial",
        entity: str = "target"
    ) -> MSPRelationship:
        """
        Create an MSP relationship from manual input.

        Args:
            vendor_name: Name of the MSP/vendor
            services: List of service dicts with keys:
                      service_name, fte_equivalent, coverage, criticality
            contract_value: Annual contract value
            contract_expiry: Contract expiration date
            dependency_level: "full", "partial", or "supplemental"
            entity: Entity this MSP serves

        Returns:
            MSPRelationship object
        """
        msp_services = []
        for svc in services:
            msp_services.append(MSPService(
                service_name=svc['service_name'],
                fte_equivalent=svc.get('fte_equivalent', 1.0),
                coverage=svc.get('coverage', 'business_hours'),
                criticality=svc.get('criticality', 'medium'),
                internal_backup=svc.get('internal_backup', False),
                description=svc.get('description')
            ))

        dep_level = DependencyLevel(dependency_level)

        return MSPRelationship(
            id=f"MSP-{uuid.uuid4().hex[:8].upper()}",
            vendor_name=vendor_name,
            services=msp_services,
            contract_value_annual=contract_value,
            contract_expiry=contract_expiry,
            dependency_level=dep_level,
            entity=entity
        )

    def calculate_total_fte_equivalent(
        self,
        relationships: List[MSPRelationship]
    ) -> float:
        """Calculate total FTE equivalent across all MSP relationships."""
        return sum(r.total_fte_equivalent for r in relationships)

    def calculate_replacement_cost(
        self,
        relationships: List[MSPRelationship],
        cost_per_fte: float = 100000
    ) -> float:
        """
        Calculate estimated cost to replace MSP services with internal staff.

        Args:
            relationships: List of MSP relationships
            cost_per_fte: Fully loaded cost per FTE (default $100K)

        Returns:
            Estimated annual replacement cost
        """
        total_fte = self.calculate_total_fte_equivalent(relationships)
        return total_fte * cost_per_fte

    def identify_high_risk_dependencies(
        self,
        relationships: List[MSPRelationship]
    ) -> List[MSPRelationship]:
        """Identify MSP relationships with high risk characteristics."""
        high_risk = []

        for rel in relationships:
            if rel.risk_level in ['critical', 'high']:
                high_risk.append(rel)

        return high_risk

    def get_service_defaults(self) -> Dict[str, Dict]:
        """Get the default FTE equivalents for standard services."""
        return self.service_defaults.copy()
