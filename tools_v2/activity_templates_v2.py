"""
Activity Templates V2 - Comprehensive Template Library

Phase 1: Carveout Core
- Identity Workstream
- Email Workstream
- Core Infrastructure Workstream

Each activity template includes:
- name: Activity name
- description: What this activity involves
- activity_type: "implementation", "operational", "license", "operational_runrate"
- cost_model: How cost is calculated
- cost_anchors: Market-based cost ranges
- timeline_months: Duration range
- complexity_modifiers: Adjustments for simple/moderate/complex scenarios
- requires_tsa: Whether TSA is typically needed
- tsa_duration: TSA duration if applicable
- prerequisites: What must happen first
- dependencies: What this enables
- notes: Implementation considerations

Cost Anchor Sources:
- Market rates from IT consulting firms
- Vendor pricing (Microsoft, Okta, etc.)
- Historical deal data
- Industry benchmarks
"""

from typing import Dict, List

# =============================================================================
# COMPLEXITY MODIFIERS
# =============================================================================

COMPLEXITY_MULTIPLIERS = {
    "simple": 0.7,      # Small company, standard config, minimal customization
    "moderate": 1.0,    # Typical mid-market, some complexity
    "complex": 1.5,     # Enterprise, heavy customization, legacy systems
    "highly_complex": 2.0,  # Regulated industry, global, extensive legacy
}

INDUSTRY_MODIFIERS = {
    "standard": 1.0,
    "financial_services": 1.3,  # Regulatory, security requirements
    "healthcare": 1.25,         # HIPAA, data sensitivity
    "government": 1.4,          # Compliance, clearance requirements
    "retail": 1.1,              # PCI, seasonal considerations
    "manufacturing": 1.15,      # OT/IT convergence
}

# =============================================================================
# PHASE 1: IDENTITY WORKSTREAM
# =============================================================================

IDENTITY_TEMPLATES = {
    "parent_dependency": [
        # -----------------------------------------------------------------
        # ASSESSMENT & DESIGN
        # -----------------------------------------------------------------
        {
            "id": "IDN-001",
            "name": "Identity architecture assessment",
            "description": "Document current identity infrastructure, dependencies, and requirements for standalone operations",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (25000, 50000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["Identity architecture document", "Gap analysis", "Migration approach recommendation"],
            "notes": "Critical first step - informs all other identity activities",
        },
        {
            "id": "IDN-002",
            "name": "Directory services inventory",
            "description": "Inventory all directory objects (users, groups, OUs, GPOs, service accounts)",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (15000, 35000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["IDN-001"],
            "outputs": ["User inventory", "Group inventory", "Service account inventory", "GPO inventory"],
        },
        {
            "id": "IDN-003",
            "name": "SSO application mapping",
            "description": "Map all applications using SSO/federation with current identity provider",
            "activity_type": "implementation",
            "phase": "assessment",
            "per_app_cost": (500, 1500),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["IDN-001"],
            "outputs": ["Application SSO inventory", "Authentication method matrix", "Reconfiguration complexity assessment"],
        },
        {
            "id": "IDN-004",
            "name": "MFA requirements analysis",
            "description": "Analyze current MFA deployment and requirements for standalone environment",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (10000, 25000),
            "timeline_months": (0.25, 0.5),
            "requires_tsa": False,
            "prerequisites": ["IDN-001"],
            "outputs": ["MFA coverage analysis", "Method inventory (app, SMS, hardware)", "Enrollment requirements"],
        },
        {
            "id": "IDN-005",
            "name": "Identity architecture design",
            "description": "Design target-state identity architecture for standalone operations",
            "activity_type": "implementation",
            "phase": "design",
            "base_cost": (40000, 100000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["IDN-001", "IDN-002", "IDN-003"],
            "outputs": ["Target architecture document", "Platform selection", "Migration strategy", "Coexistence approach"],
            "notes": "Key decision point - platform choice (Azure AD, Okta, on-prem AD) drives downstream costs",
        },
        # -----------------------------------------------------------------
        # PLATFORM STANDUP
        # -----------------------------------------------------------------
        {
            "id": "IDN-010",
            "name": "Azure AD tenant provisioning",
            "description": "Provision and configure new Azure AD tenant for standalone operations",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (30000, 75000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["IDN-005"],
            "outputs": ["Configured Azure AD tenant", "Admin accounts", "Base policies"],
            "notes": "Includes P1/P2 feature configuration if licensed",
        },
        {
            "id": "IDN-011",
            "name": "Okta org provisioning",
            "description": "Provision and configure new Okta organization for standalone operations",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (35000, 85000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["IDN-005"],
            "outputs": ["Configured Okta org", "Admin accounts", "Base policies"],
        },
        {
            "id": "IDN-012",
            "name": "On-premises AD forest standup",
            "description": "Design and deploy new on-premises Active Directory forest",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (50000, 120000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["IDN-005"],
            "outputs": ["AD forest", "Domain controllers", "Sites and services", "Base GPOs"],
            "notes": "Less common for new deployments but required for some legacy scenarios",
        },
        {
            "id": "IDN-013",
            "name": "Hybrid identity configuration",
            "description": "Configure Azure AD Connect or equivalent for hybrid identity",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (25000, 60000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["IDN-010", "IDN-012"],
            "outputs": ["Azure AD Connect deployment", "Sync rules", "Password hash sync or PTA"],
        },
        {
            "id": "IDN-014",
            "name": "Identity governance setup",
            "description": "Configure identity governance features (access reviews, entitlement management)",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["IDN-010"],
            "outputs": ["Access review policies", "Entitlement catalogs", "Lifecycle workflows"],
        },
        # -----------------------------------------------------------------
        # USER MIGRATION
        # -----------------------------------------------------------------
        {
            "id": "IDN-020",
            "name": "User account migration",
            "description": "Migrate user accounts to new identity platform",
            "activity_type": "implementation",
            "phase": "migration",
            "per_user_cost": (15, 40),
            "timeline_months": (1, 3),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["IDN-010"],
            "outputs": ["Migrated user accounts", "Profile data", "Attribute mapping"],
            "notes": "Cost varies significantly based on attribute complexity and cleanup required",
        },
        {
            "id": "IDN-021",
            "name": "Group and distribution list migration",
            "description": "Migrate security groups, distribution lists, and dynamic groups",
            "activity_type": "implementation",
            "phase": "migration",
            "base_cost": (15000, 40000),
            "per_group_cost": (50, 150),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["IDN-020"],
            "outputs": ["Migrated groups", "Membership mapping", "Nested group remediation"],
        },
        {
            "id": "IDN-022",
            "name": "Service account migration and remediation",
            "description": "Inventory, migrate, and remediate service accounts",
            "activity_type": "implementation",
            "phase": "migration",
            "per_account_cost": (500, 2000),
            "timeline_months": (1, 3),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["IDN-002"],
            "outputs": ["Service account inventory", "Migrated accounts", "Password rotation", "Ownership assignment"],
            "notes": "Often underestimated - service accounts are frequently undocumented",
        },
        {
            "id": "IDN-023",
            "name": "Password sync/reset coordination",
            "description": "Coordinate password migration strategy and user communication",
            "activity_type": "implementation",
            "phase": "migration",
            "per_user_cost": (2, 8),
            "timeline_months": (0.5, 1),
            "requires_tsa": True,
            "tsa_duration": (1, 2),
            "prerequisites": ["IDN-020"],
            "outputs": ["Password migration strategy", "User communications", "Reset process"],
        },
        # -----------------------------------------------------------------
        # APPLICATION SSO RECONFIGURATION
        # -----------------------------------------------------------------
        {
            "id": "IDN-030",
            "name": "SAML/OIDC SSO reconfiguration - Standard",
            "description": "Reconfigure standard SaaS applications for new identity provider",
            "activity_type": "implementation",
            "phase": "migration",
            "per_app_cost": (2000, 5000),
            "timeline_months": (1, 3),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["IDN-010", "IDN-003"],
            "outputs": ["Reconfigured SSO", "Updated certificates", "Testing validation"],
            "notes": "Standard apps (Salesforce, ServiceNow, etc.) with documented SSO setup",
        },
        {
            "id": "IDN-031",
            "name": "SAML/OIDC SSO reconfiguration - Complex",
            "description": "Reconfigure complex or custom applications for new identity provider",
            "activity_type": "implementation",
            "phase": "migration",
            "per_app_cost": (5000, 15000),
            "timeline_months": (2, 4),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["IDN-010", "IDN-003"],
            "outputs": ["Reconfigured SSO", "Custom claim mappings", "Multi-tenant configuration"],
            "notes": "Custom apps, legacy apps, or apps requiring code changes",
        },
        {
            "id": "IDN-032",
            "name": "Legacy application authentication",
            "description": "Address authentication for legacy apps that don't support modern auth",
            "activity_type": "implementation",
            "phase": "migration",
            "per_app_cost": (8000, 25000),
            "timeline_months": (2, 6),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["IDN-010"],
            "outputs": ["Legacy auth solution", "LDAP proxy or app password", "Header-based auth"],
            "notes": "May require application proxy, LDAP gateway, or code remediation",
        },
        {
            "id": "IDN-033",
            "name": "MFA enrollment campaign",
            "description": "Enroll users in MFA on new identity platform",
            "activity_type": "implementation",
            "phase": "migration",
            "per_user_cost": (5, 15),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["IDN-020"],
            "outputs": ["MFA enrolled users", "Registration reports", "Exception handling"],
        },
        {
            "id": "IDN-034",
            "name": "Conditional access policy implementation",
            "description": "Implement conditional access policies on new platform",
            "activity_type": "implementation",
            "phase": "migration",
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["IDN-010", "IDN-020"],
            "outputs": ["CA policies", "Named locations", "Device compliance integration"],
        },
        # -----------------------------------------------------------------
        # CUTOVER & VALIDATION
        # -----------------------------------------------------------------
        {
            "id": "IDN-040",
            "name": "Identity parallel running",
            "description": "Run parallel identity environments during transition",
            "activity_type": "implementation",
            "phase": "cutover",
            "base_cost": (30000, 75000),
            "timeline_months": (1, 3),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["IDN-020", "IDN-030"],
            "outputs": ["Coexistence configuration", "Cross-tenant collaboration", "Monitoring"],
        },
        {
            "id": "IDN-041",
            "name": "Authentication cutover",
            "description": "Execute cutover from parent to standalone identity",
            "activity_type": "implementation",
            "phase": "cutover",
            "base_cost": (25000, 60000),
            "timeline_months": (0.25, 0.5),
            "requires_tsa": False,
            "prerequisites": ["IDN-040"],
            "outputs": ["Cutover execution", "Rollback plan", "Success validation"],
            "notes": "Critical milestone - requires careful planning and communication",
        },
        {
            "id": "IDN-042",
            "name": "Post-migration identity support",
            "description": "Hypercare support period after identity cutover",
            "activity_type": "implementation",
            "phase": "cutover",
            "base_cost": (20000, 50000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["IDN-041"],
            "outputs": ["Support coverage", "Issue resolution", "Stabilization"],
        },
        {
            "id": "IDN-043",
            "name": "Identity decommissioning",
            "description": "Decommission access to parent identity systems",
            "activity_type": "implementation",
            "phase": "cutover",
            "base_cost": (15000, 35000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["IDN-041"],
            "outputs": ["Access removal", "Trust removal", "Audit documentation"],
        },
    ],
}

# =============================================================================
# PHASE 1: EMAIL WORKSTREAM
# =============================================================================

EMAIL_TEMPLATES = {
    "parent_dependency": [
        # -----------------------------------------------------------------
        # ASSESSMENT & DESIGN
        # -----------------------------------------------------------------
        {
            "id": "EML-001",
            "name": "Email environment assessment",
            "description": "Assess current email infrastructure, configuration, and dependencies",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (20000, 45000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["Email architecture document", "Mailbox inventory", "Configuration baseline"],
        },
        {
            "id": "EML-002",
            "name": "Mailbox inventory and sizing",
            "description": "Detailed inventory of mailboxes with size, type, and usage patterns",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (10000, 25000),
            "timeline_months": (0.25, 0.5),
            "requires_tsa": False,
            "prerequisites": ["EML-001"],
            "outputs": ["Mailbox inventory", "Size distribution", "Inactive mailbox list", "VIP identification"],
        },
        {
            "id": "EML-003",
            "name": "Shared resource mapping",
            "description": "Map shared mailboxes, distribution lists, room/resource mailboxes",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (8000, 20000),
            "timeline_months": (0.25, 0.5),
            "requires_tsa": False,
            "prerequisites": ["EML-001"],
            "outputs": ["Shared mailbox inventory", "DL inventory", "Resource mailbox list", "Ownership matrix"],
        },
        {
            "id": "EML-004",
            "name": "Mail flow analysis",
            "description": "Analyze mail flow, connectors, transport rules, and routing",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (12000, 30000),
            "timeline_months": (0.25, 0.5),
            "requires_tsa": False,
            "prerequisites": ["EML-001"],
            "outputs": ["Mail flow diagram", "Connector inventory", "Transport rule inventory", "Routing requirements"],
        },
        {
            "id": "EML-005",
            "name": "Email security configuration review",
            "description": "Review email security settings, policies, and third-party tools",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (10000, 25000),
            "timeline_months": (0.25, 0.5),
            "requires_tsa": False,
            "prerequisites": ["EML-001"],
            "outputs": ["Security policy inventory", "ATP/Defender config", "Third-party tool inventory", "DLP policies"],
        },
        {
            "id": "EML-006",
            "name": "Email platform design",
            "description": "Design target email platform architecture",
            "activity_type": "implementation",
            "phase": "design",
            "base_cost": (25000, 60000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["EML-001", "EML-002", "EML-004"],
            "outputs": ["Target architecture", "Platform selection", "Migration approach", "Coexistence strategy"],
        },
        # -----------------------------------------------------------------
        # PLATFORM STANDUP
        # -----------------------------------------------------------------
        {
            "id": "EML-010",
            "name": "M365 tenant email configuration",
            "description": "Configure Exchange Online in new M365 tenant",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (25000, 60000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["EML-006"],
            "outputs": ["Configured Exchange Online", "Accepted domains", "Base policies"],
        },
        {
            "id": "EML-011",
            "name": "Google Workspace provisioning",
            "description": "Provision and configure Google Workspace for email",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (25000, 55000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["EML-006"],
            "outputs": ["Configured Google Workspace", "Domain verification", "Base policies"],
        },
        {
            "id": "EML-012",
            "name": "Domain configuration",
            "description": "Configure email domains, DNS records, SPF/DKIM/DMARC",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (8000, 20000),
            "per_domain_cost": (1000, 3000),
            "timeline_months": (0.25, 0.5),
            "requires_tsa": False,
            "prerequisites": ["EML-010"],
            "outputs": ["Verified domains", "DNS records", "Email authentication records"],
        },
        {
            "id": "EML-013",
            "name": "Mail routing configuration",
            "description": "Configure mail routing, connectors, and flow rules",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (15000, 40000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["EML-010", "EML-012"],
            "outputs": ["Connectors", "Transport rules", "Mail flow configuration"],
        },
        {
            "id": "EML-014",
            "name": "Email security policy configuration",
            "description": "Configure email security policies (anti-spam, anti-malware, ATP)",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (15000, 40000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["EML-010"],
            "outputs": ["Anti-spam policies", "Anti-malware policies", "Safe links/attachments", "Quarantine policies"],
        },
        {
            "id": "EML-015",
            "name": "Email archiving and retention setup",
            "description": "Configure email archiving, retention policies, and legal hold",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["EML-010"],
            "outputs": ["Archive configuration", "Retention policies", "Legal hold procedures", "eDiscovery setup"],
        },
        # -----------------------------------------------------------------
        # MAILBOX MIGRATION
        # -----------------------------------------------------------------
        {
            "id": "EML-020",
            "name": "Mailbox migration - Staged",
            "description": "Migrate mailboxes in staged waves",
            "activity_type": "implementation",
            "phase": "migration",
            "per_user_cost": (20, 50),
            "timeline_months": (2, 4),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["EML-010", "EML-013"],
            "outputs": ["Migrated mailboxes", "Migration reports", "Error remediation"],
            "notes": "Standard approach for most migrations",
        },
        {
            "id": "EML-021",
            "name": "Mailbox migration - Cutover",
            "description": "Migrate all mailboxes in single cutover event",
            "activity_type": "implementation",
            "phase": "migration",
            "per_user_cost": (15, 35),
            "timeline_months": (0.5, 1),
            "requires_tsa": True,
            "tsa_duration": (1, 2),
            "prerequisites": ["EML-010", "EML-013"],
            "outputs": ["Migrated mailboxes", "Cutover execution", "Post-migration validation"],
            "notes": "Faster but higher risk - suitable for smaller populations",
        },
        {
            "id": "EML-022",
            "name": "Archive mailbox migration",
            "description": "Migrate online archives and historical data",
            "activity_type": "implementation",
            "phase": "migration",
            "per_user_cost": (10, 30),
            "timeline_months": (1, 3),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["EML-020"],
            "outputs": ["Migrated archives", "Archive integrity validation"],
        },
        {
            "id": "EML-023",
            "name": "Public folder migration",
            "description": "Migrate public folders to modern solution",
            "activity_type": "implementation",
            "phase": "migration",
            "base_cost": (20000, 60000),
            "timeline_months": (1, 3),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["EML-010"],
            "outputs": ["Migrated public folders", "Group mailbox conversion", "SharePoint migration (if applicable)"],
            "notes": "Public folders often migrated to shared mailboxes or SharePoint",
        },
        {
            "id": "EML-024",
            "name": "Shared mailbox migration",
            "description": "Migrate shared mailboxes with permissions",
            "activity_type": "implementation",
            "phase": "migration",
            "per_mailbox_cost": (200, 500),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": True,
            "tsa_duration": (2, 3),
            "prerequisites": ["EML-020"],
            "outputs": ["Migrated shared mailboxes", "Permission mapping", "Delegation configuration"],
        },
        {
            "id": "EML-025",
            "name": "Calendar and contact migration",
            "description": "Migrate calendar data and contacts",
            "activity_type": "implementation",
            "phase": "migration",
            "per_user_cost": (5, 15),
            "timeline_months": (0.5, 1),
            "requires_tsa": True,
            "tsa_duration": (1, 2),
            "prerequisites": ["EML-020"],
            "outputs": ["Migrated calendars", "Migrated contacts", "Meeting re-linking"],
        },
        {
            "id": "EML-026",
            "name": "Resource mailbox migration",
            "description": "Migrate room and equipment mailboxes",
            "activity_type": "implementation",
            "phase": "migration",
            "per_resource_cost": (150, 400),
            "timeline_months": (0.5, 1),
            "requires_tsa": True,
            "tsa_duration": (1, 2),
            "prerequisites": ["EML-020"],
            "outputs": ["Migrated resources", "Booking policies", "Delegate configuration"],
        },
        # -----------------------------------------------------------------
        # COEXISTENCE
        # -----------------------------------------------------------------
        {
            "id": "EML-030",
            "name": "Cross-tenant free/busy configuration",
            "description": "Configure calendar free/busy sharing between tenants",
            "activity_type": "implementation",
            "phase": "coexistence",
            "base_cost": (15000, 35000),
            "timeline_months": (0.5, 1),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["EML-010"],
            "outputs": ["Organization relationship", "Availability address space", "Cross-tenant policies"],
        },
        {
            "id": "EML-031",
            "name": "Mail forwarding configuration",
            "description": "Configure mail forwarding during transition period",
            "activity_type": "implementation",
            "phase": "coexistence",
            "base_cost": (8000, 20000),
            "timeline_months": (0.25, 0.5),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["EML-020"],
            "outputs": ["Forwarding rules", "NDR handling", "Reply-to configuration"],
        },
        {
            "id": "EML-032",
            "name": "Address book synchronization",
            "description": "Synchronize GAL/contacts between environments during transition",
            "activity_type": "implementation",
            "phase": "coexistence",
            "base_cost": (10000, 30000),
            "timeline_months": (0.5, 1),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["EML-010"],
            "outputs": ["GAL sync", "Contact objects", "Address list configuration"],
        },
        # -----------------------------------------------------------------
        # CUTOVER
        # -----------------------------------------------------------------
        {
            "id": "EML-040",
            "name": "MX record cutover",
            "description": "Execute mail routing cutover to new environment",
            "activity_type": "implementation",
            "phase": "cutover",
            "base_cost": (10000, 25000),
            "timeline_months": (0.1, 0.25),
            "requires_tsa": False,
            "prerequisites": ["EML-020", "EML-012"],
            "outputs": ["MX record changes", "Mail flow validation", "NDR monitoring"],
            "notes": "Critical cutover event - typically executed during low-traffic period",
        },
        {
            "id": "EML-041",
            "name": "Email client reconfiguration",
            "description": "Reconfigure Outlook and mobile clients for new environment",
            "activity_type": "implementation",
            "phase": "cutover",
            "per_user_cost": (5, 20),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["EML-040"],
            "outputs": ["Reconfigured clients", "Profile updates", "Mobile device re-enrollment"],
        },
        {
            "id": "EML-042",
            "name": "Post-migration email support",
            "description": "Hypercare support period after email migration",
            "activity_type": "implementation",
            "phase": "cutover",
            "base_cost": (15000, 40000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["EML-040"],
            "outputs": ["Support coverage", "Issue resolution", "User communication"],
        },
    ],
}

# =============================================================================
# PHASE 1: CORE INFRASTRUCTURE WORKSTREAM
# =============================================================================

INFRASTRUCTURE_TEMPLATES = {
    "parent_dependency": [
        # -----------------------------------------------------------------
        # ASSESSMENT & DESIGN
        # -----------------------------------------------------------------
        {
            "id": "INF-001",
            "name": "Infrastructure discovery and inventory",
            "description": "Comprehensive inventory of servers, VMs, storage, and network infrastructure",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (25000, 60000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["Server inventory", "VM inventory", "Storage inventory", "Network inventory", "Dependency map"],
        },
        {
            "id": "INF-002",
            "name": "Application-to-infrastructure mapping",
            "description": "Map applications to underlying infrastructure and dependencies",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["INF-001"],
            "outputs": ["Application infrastructure map", "Dependency matrix", "Criticality assessment"],
        },
        {
            "id": "INF-003",
            "name": "Storage assessment and planning",
            "description": "Assess storage requirements, performance needs, and migration approach",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (15000, 40000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["INF-001"],
            "outputs": ["Storage inventory", "Capacity planning", "Performance requirements", "Migration approach"],
        },
        {
            "id": "INF-004",
            "name": "Backup and DR assessment",
            "description": "Assess backup infrastructure, DR capabilities, and requirements",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (15000, 35000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["INF-001"],
            "outputs": ["Backup inventory", "RPO/RTO requirements", "DR requirements", "Gap analysis"],
        },
        {
            "id": "INF-005",
            "name": "Target infrastructure architecture design",
            "description": "Design target-state infrastructure architecture",
            "activity_type": "implementation",
            "phase": "design",
            "base_cost": (40000, 100000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["INF-001", "INF-002", "INF-003", "INF-004"],
            "outputs": ["Target architecture", "Platform selection", "Sizing specifications", "Migration strategy"],
        },
        # -----------------------------------------------------------------
        # ENVIRONMENT BUILD
        # -----------------------------------------------------------------
        {
            "id": "INF-010",
            "name": "Cloud landing zone deployment",
            "description": "Deploy cloud foundation (Azure, AWS, or GCP landing zone)",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (75000, 200000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "prerequisites": ["INF-005"],
            "outputs": ["Landing zone", "Network topology", "Security baseline", "Governance policies"],
            "notes": "Foundation for cloud-hosted infrastructure",
        },
        {
            "id": "INF-011",
            "name": "On-premises datacenter buildout",
            "description": "Build out on-premises or colocation infrastructure",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (150000, 400000),
            "timeline_months": (2, 4),
            "requires_tsa": False,
            "prerequisites": ["INF-005"],
            "outputs": ["Physical infrastructure", "Compute resources", "Storage systems", "Network infrastructure"],
            "notes": "Less common for new buildouts but required in some scenarios",
        },
        {
            "id": "INF-012",
            "name": "Network connectivity setup",
            "description": "Establish connectivity between environments (ExpressRoute, Direct Connect, VPN)",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (30000, 80000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["INF-010"],
            "outputs": ["Private connectivity", "VPN tunnels", "Routing configuration", "Firewall rules"],
        },
        {
            "id": "INF-013",
            "name": "Security baseline implementation",
            "description": "Implement security baseline on new infrastructure",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (25000, 60000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["INF-010"],
            "outputs": ["Hardening standards", "Security groups/NSGs", "Logging configuration", "Compliance controls"],
        },
        {
            "id": "INF-014",
            "name": "Monitoring and alerting setup",
            "description": "Deploy monitoring, logging, and alerting infrastructure",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["INF-010"],
            "outputs": ["Monitoring platform", "Alert rules", "Dashboards", "Log aggregation"],
        },
        {
            "id": "INF-015",
            "name": "Backup infrastructure deployment",
            "description": "Deploy backup solution for new environment",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (30000, 80000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["INF-010"],
            "outputs": ["Backup infrastructure", "Backup policies", "Retention configuration", "Testing procedures"],
        },
        {
            "id": "INF-016",
            "name": "Disaster recovery setup",
            "description": "Implement DR solution for critical workloads",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (50000, 150000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "prerequisites": ["INF-010", "INF-015"],
            "outputs": ["DR infrastructure", "Replication configuration", "DR runbooks", "Testing schedule"],
        },
        # -----------------------------------------------------------------
        # MIGRATION
        # -----------------------------------------------------------------
        {
            "id": "INF-020",
            "name": "VM migration - Lift and shift",
            "description": "Migrate VMs using rehost approach (Azure Migrate, AWS SMS, etc.)",
            "activity_type": "implementation",
            "phase": "migration",
            "per_vm_cost": (500, 1500),
            "timeline_months": (2, 6),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["INF-010"],
            "outputs": ["Migrated VMs", "Cutover execution", "Post-migration validation"],
            "notes": "Most common approach - minimal changes to workloads",
        },
        {
            "id": "INF-021",
            "name": "VM migration - Replatform",
            "description": "Migrate VMs with platform optimization (OS upgrade, right-sizing)",
            "activity_type": "implementation",
            "phase": "migration",
            "per_vm_cost": (1000, 3000),
            "timeline_months": (3, 8),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["INF-010"],
            "outputs": ["Migrated VMs", "Platform updates", "Performance optimization"],
            "notes": "More effort but better outcomes - modernizes workloads",
        },
        {
            "id": "INF-022",
            "name": "Physical server migration",
            "description": "Migrate physical servers (P2V or P2P)",
            "activity_type": "implementation",
            "phase": "migration",
            "per_server_cost": (2000, 6000),
            "timeline_months": (2, 6),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["INF-010"],
            "outputs": ["Migrated servers", "Virtualization (if P2V)", "Hardware decommission"],
        },
        {
            "id": "INF-023",
            "name": "Database migration",
            "description": "Migrate databases to new environment",
            "activity_type": "implementation",
            "phase": "migration",
            "per_database_cost": (3000, 15000),
            "timeline_months": (2, 6),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["INF-010"],
            "outputs": ["Migrated databases", "Data validation", "Application connectivity"],
            "notes": "Complexity varies significantly by database type and size",
        },
        {
            "id": "INF-024",
            "name": "Storage migration",
            "description": "Migrate storage (SAN, NAS, file shares)",
            "activity_type": "implementation",
            "phase": "migration",
            "per_tb_cost": (200, 600),
            "timeline_months": (2, 6),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["INF-010"],
            "outputs": ["Migrated storage", "Data integrity validation", "Permission mapping"],
        },
        {
            "id": "INF-025",
            "name": "Application migration",
            "description": "Migrate applications to new infrastructure",
            "activity_type": "implementation",
            "phase": "migration",
            "per_app_cost": (5000, 25000),
            "timeline_months": (2, 8),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["INF-020"],
            "outputs": ["Migrated applications", "Integration testing", "Performance validation"],
            "notes": "Cost varies significantly by application complexity",
        },
        # -----------------------------------------------------------------
        # OPERATIONS HANDOFF
        # -----------------------------------------------------------------
        {
            "id": "INF-030",
            "name": "Operations runbook development",
            "description": "Develop operations documentation and runbooks",
            "activity_type": "implementation",
            "phase": "handoff",
            "base_cost": (20000, 50000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["INF-020"],
            "outputs": ["Operations runbooks", "Incident procedures", "Change procedures", "Monitoring guides"],
        },
        {
            "id": "INF-031",
            "name": "Operations team training",
            "description": "Train operations team on new environment",
            "activity_type": "implementation",
            "phase": "handoff",
            "base_cost": (15000, 40000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["INF-030"],
            "outputs": ["Training delivery", "Knowledge transfer", "Competency validation"],
        },
        {
            "id": "INF-032",
            "name": "Support transition",
            "description": "Transition from project support to BAU operations",
            "activity_type": "implementation",
            "phase": "handoff",
            "base_cost": (15000, 35000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["INF-030", "INF-031"],
            "outputs": ["Support transition", "Escalation procedures", "SLA establishment"],
        },
        {
            "id": "INF-033",
            "name": "Legacy infrastructure decommissioning",
            "description": "Decommission legacy infrastructure after migration",
            "activity_type": "implementation",
            "phase": "handoff",
            "per_server_cost": (200, 500),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "prerequisites": ["INF-020"],
            "outputs": ["Decommissioned systems", "Data sanitization", "Asset disposition", "License recovery"],
        },
    ],
}

# =============================================================================
# COMBINED TEMPLATES FOR STAGE 2 MATCHING
# =============================================================================

def get_phase1_templates() -> Dict[str, Dict[str, List[Dict]]]:
    """Get all Phase 1 templates organized by category and workstream."""
    return {
        "parent_dependency": {
            "identity": IDENTITY_TEMPLATES["parent_dependency"],
            "email": EMAIL_TEMPLATES["parent_dependency"],
            "infrastructure": INFRASTRUCTURE_TEMPLATES["parent_dependency"],
        }
    }


def get_activity_by_id(activity_id: str) -> Dict:
    """Look up an activity by its ID."""
    all_templates = get_phase1_templates()

    for category, workstreams in all_templates.items():
        for workstream, activities in workstreams.items():
            for activity in activities:
                if activity.get("id") == activity_id:
                    return activity

    return None


def get_activities_by_phase(phase: str) -> List[Dict]:
    """Get all activities for a given phase."""
    activities = []
    all_templates = get_phase1_templates()

    for category, workstreams in all_templates.items():
        for workstream, acts in workstreams.items():
            for activity in acts:
                if activity.get("phase") == phase:
                    activities.append({**activity, "workstream": workstream, "category": category})

    return activities


def calculate_activity_cost(
    activity: Dict,
    user_count: int = 1000,
    app_count: int = 30,
    server_count: int = 50,
    vm_count: int = 100,
    mailbox_count: int = None,
    database_count: int = 10,
    storage_tb: int = 50,
    complexity: str = "moderate",
    industry: str = "standard",
) -> tuple:
    """
    Calculate cost range for an activity based on quantities and modifiers.

    Returns: (low, high, formula)
    """
    mailbox_count = mailbox_count or user_count

    # Get complexity and industry multipliers
    complexity_mult = COMPLEXITY_MULTIPLIERS.get(complexity, 1.0)
    industry_mult = INDUSTRY_MODIFIERS.get(industry, 1.0)
    combined_mult = complexity_mult * industry_mult

    # Calculate base cost
    if "base_cost" in activity:
        low, high = activity["base_cost"]
        formula = f"Base: ${low:,.0f}-${high:,.0f}"

    elif "per_user_cost" in activity:
        per_low, per_high = activity["per_user_cost"]
        low = per_low * user_count
        high = per_high * user_count
        formula = f"{user_count:,} users × ${per_low}-${per_high}"

    elif "per_app_cost" in activity:
        per_low, per_high = activity["per_app_cost"]
        low = per_low * app_count
        high = per_high * app_count
        formula = f"{app_count} apps × ${per_low:,}-${per_high:,}"

    elif "per_vm_cost" in activity:
        per_low, per_high = activity["per_vm_cost"]
        low = per_low * vm_count
        high = per_high * vm_count
        formula = f"{vm_count} VMs × ${per_low:,}-${per_high:,}"

    elif "per_server_cost" in activity:
        per_low, per_high = activity["per_server_cost"]
        low = per_low * server_count
        high = per_high * server_count
        formula = f"{server_count} servers × ${per_low:,}-${per_high:,}"

    elif "per_mailbox_cost" in activity:
        per_low, per_high = activity["per_mailbox_cost"]
        low = per_low * mailbox_count
        high = per_high * mailbox_count
        formula = f"{mailbox_count} mailboxes × ${per_low:,}-${per_high:,}"

    elif "per_database_cost" in activity:
        per_low, per_high = activity["per_database_cost"]
        low = per_low * database_count
        high = per_high * database_count
        formula = f"{database_count} databases × ${per_low:,}-${per_high:,}"

    elif "per_tb_cost" in activity:
        per_low, per_high = activity["per_tb_cost"]
        low = per_low * storage_tb
        high = per_high * storage_tb
        formula = f"{storage_tb} TB × ${per_low:,}-${per_high:,}"

    elif "per_account_cost" in activity:
        # Estimate service accounts as ~5% of users
        account_count = max(int(user_count * 0.05), 20)
        per_low, per_high = activity["per_account_cost"]
        low = per_low * account_count
        high = per_high * account_count
        formula = f"~{account_count} service accounts × ${per_low:,}-${per_high:,}"

    elif "per_group_cost" in activity:
        # Estimate groups as ~20% of users
        group_count = max(int(user_count * 0.2), 50)
        per_low, per_high = activity["per_group_cost"]
        base_low, base_high = activity.get("base_cost", (0, 0))
        low = base_low + (per_low * group_count)
        high = base_high + (per_high * group_count)
        formula = f"Base + ~{group_count} groups × ${per_low}-${per_high}"

    elif "per_domain_cost" in activity:
        # Assume 2-5 domains typically
        domain_count = 3
        per_low, per_high = activity["per_domain_cost"]
        base_low, base_high = activity.get("base_cost", (0, 0))
        low = base_low + (per_low * domain_count)
        high = base_high + (per_high * domain_count)
        formula = f"Base + ~{domain_count} domains × ${per_low:,}-${per_high:,}"

    elif "per_resource_cost" in activity:
        # Estimate resources as ~5% of users
        resource_count = max(int(user_count * 0.05), 10)
        per_low, per_high = activity["per_resource_cost"]
        low = per_low * resource_count
        high = per_high * resource_count
        formula = f"~{resource_count} resources × ${per_low:,}-${per_high:,}"

    else:
        low, high = 0, 0
        formula = "Unknown cost model"

    # Apply modifiers
    if combined_mult != 1.0:
        low = int(low * combined_mult)
        high = int(high * combined_mult)
        formula += f" × {combined_mult:.2f} ({complexity}/{industry})"

    return (low, high, formula)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'IDENTITY_TEMPLATES',
    'EMAIL_TEMPLATES',
    'INFRASTRUCTURE_TEMPLATES',
    'COMPLEXITY_MULTIPLIERS',
    'INDUSTRY_MODIFIERS',
    'get_phase1_templates',
    'get_activity_by_id',
    'get_activities_by_phase',
    'calculate_activity_cost',
]
