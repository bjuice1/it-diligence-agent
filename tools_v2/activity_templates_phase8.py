"""
Activity Templates V2 - Phase 8: Compliance & Regulatory

Phase 8: IT Compliance and Regulatory Requirements
- Data Privacy (GDPR, CCPA, privacy programs)
- Industry Regulations (SOX, HIPAA, PCI-DSS, GLBA)
- Security Compliance (SOC 2, ISO 27001, NIST)
- Audit Readiness (internal/external audit prep)
- Policy & Procedures (IT governance documentation)
- Compliance Tooling (GRC platforms, monitoring)

Key considerations for carveouts:
- Standalone entity needs its own compliance posture
- Can't rely on parent's certifications/attestations
- May need to establish compliance programs from scratch
- Regulatory obligations transfer with the business
- Timeline pressure often conflicts with compliance needs

Each activity template includes:
- name: Activity name
- description: What this activity involves
- activity_type: "assessment", "implementation", "certification"
- cost_model: How cost is calculated
- timeline_months: Duration range
- requires_tsa: Whether TSA is typically needed
- regulatory_driver: What regulation/standard drives this
- notes: Implementation considerations
"""

from typing import Dict, List, Any

# Import shared modifiers from Phase 1
from tools_v2.activity_templates_v2 import COMPLEXITY_MULTIPLIERS, INDUSTRY_MODIFIERS

# =============================================================================
# PHASE 8: DATA PRIVACY
# =============================================================================

DATA_PRIVACY_TEMPLATES = {
    "compliance": [
        # -----------------------------------------------------------------
        # PRIVACY PROGRAM
        # -----------------------------------------------------------------
        {
            "id": "CMP-PRV-001",
            "name": "Privacy program assessment",
            "description": "Assess current privacy practices and regulatory obligations",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (30000, 80000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "regulatory_driver": ["GDPR", "CCPA", "Privacy"],
            "prerequisites": [],
            "outputs": ["Privacy inventory", "Regulatory mapping", "Gap analysis", "Risk assessment"],
        },
        {
            "id": "CMP-PRV-002",
            "name": "Data inventory and mapping",
            "description": "Create comprehensive data inventory and data flow mapping",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (40000, 120000),
            "per_system_cost": (1000, 4000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "regulatory_driver": ["GDPR", "CCPA"],
            "prerequisites": ["CMP-PRV-001"],
            "outputs": ["Data inventory", "Data flow diagrams", "Processing activities", "Retention schedules"],
        },
        {
            "id": "CMP-PRV-003",
            "name": "Privacy program establishment",
            "description": "Establish standalone privacy program and governance",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (50000, 150000),
            "timeline_months": (2, 4),
            "requires_tsa": False,
            "regulatory_driver": ["GDPR", "CCPA", "Privacy"],
            "prerequisites": ["CMP-PRV-001"],
            "outputs": ["Privacy policies", "Governance framework", "Roles and responsibilities", "Training program"],
        },
        # -----------------------------------------------------------------
        # GDPR
        # -----------------------------------------------------------------
        {
            "id": "CMP-PRV-010",
            "name": "GDPR compliance assessment",
            "description": "Assess GDPR compliance requirements for standalone entity",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (40000, 100000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "regulatory_driver": ["GDPR"],
            "prerequisites": [],
            "outputs": ["GDPR gap analysis", "Lawful basis review", "Cross-border transfer assessment"],
            "notes": "Required if processing EU resident data",
        },
        {
            "id": "CMP-PRV-011",
            "name": "GDPR remediation and implementation",
            "description": "Implement GDPR compliance controls and processes",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (75000, 250000),
            "timeline_months": (3, 6),
            "requires_tsa": False,
            "regulatory_driver": ["GDPR"],
            "prerequisites": ["CMP-PRV-010"],
            "outputs": ["DPIA process", "Consent management", "Subject access request process", "Breach notification process"],
        },
        {
            "id": "CMP-PRV-012",
            "name": "Data Protection Officer (DPO) appointment",
            "description": "Appoint and establish DPO function",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (20000, 60000),  # Setup costs; ongoing is separate
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "regulatory_driver": ["GDPR"],
            "prerequisites": ["CMP-PRV-010"],
            "outputs": ["DPO appointment", "DPO charter", "Reporting structure"],
            "notes": "Can be outsourced; required for certain organizations",
        },
        {
            "id": "CMP-PRV-013",
            "name": "EU representative appointment",
            "description": "Appoint EU representative for non-EU entities",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (10000, 30000),
            "timeline_months": (0.25, 0.75),
            "requires_tsa": False,
            "regulatory_driver": ["GDPR"],
            "prerequisites": ["CMP-PRV-010"],
            "outputs": ["EU representative agreement", "Contact registration"],
        },
        {
            "id": "CMP-PRV-014",
            "name": "International data transfer mechanisms",
            "description": "Establish lawful mechanisms for cross-border data transfers",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (30000, 80000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "regulatory_driver": ["GDPR", "Schrems II"],
            "prerequisites": ["CMP-PRV-010"],
            "outputs": ["SCCs", "TIA documentation", "Supplementary measures", "Transfer register"],
        },
        # -----------------------------------------------------------------
        # CCPA / US PRIVACY
        # -----------------------------------------------------------------
        {
            "id": "CMP-PRV-020",
            "name": "CCPA/CPRA compliance assessment",
            "description": "Assess California privacy law compliance requirements",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (25000, 70000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "regulatory_driver": ["CCPA", "CPRA"],
            "prerequisites": [],
            "outputs": ["CCPA gap analysis", "Consumer rights assessment", "Vendor assessment"],
        },
        {
            "id": "CMP-PRV-021",
            "name": "CCPA/CPRA remediation",
            "description": "Implement CCPA compliance controls",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (50000, 150000),
            "timeline_months": (2, 4),
            "requires_tsa": False,
            "regulatory_driver": ["CCPA", "CPRA"],
            "prerequisites": ["CMP-PRV-020"],
            "outputs": ["Privacy notice updates", "Opt-out mechanisms", "Consumer request process", "Vendor agreements"],
        },
        {
            "id": "CMP-PRV-022",
            "name": "US state privacy law compliance",
            "description": "Address emerging US state privacy laws (Virginia, Colorado, etc.)",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (30000, 90000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "regulatory_driver": ["VCDPA", "CPA", "State Privacy"],
            "prerequisites": ["CMP-PRV-020"],
            "outputs": ["Multi-state compliance framework", "Consent management", "Consumer rights processes"],
        },
        # -----------------------------------------------------------------
        # PRIVACY TOOLS
        # -----------------------------------------------------------------
        {
            "id": "CMP-PRV-030",
            "name": "Privacy management platform implementation",
            "description": "Implement privacy management/OneTrust type platform",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (50000, 200000),
            "per_module_cost": (15000, 50000),
            "timeline_months": (2, 4),
            "requires_tsa": False,
            "regulatory_driver": ["GDPR", "CCPA", "Privacy"],
            "prerequisites": ["CMP-PRV-001"],
            "outputs": ["Privacy platform", "Cookie consent", "DSAR automation", "Vendor management"],
            "notes": "OneTrust, TrustArc, BigID, etc.",
        },
        {
            "id": "CMP-PRV-031",
            "name": "Consent management implementation",
            "description": "Implement consent management for web and applications",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (20000, 60000),
            "per_site_cost": (2000, 8000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "regulatory_driver": ["GDPR", "ePrivacy"],
            "prerequisites": [],
            "outputs": ["Cookie banners", "Consent records", "Preference center"],
        },
    ],
}

# =============================================================================
# PHASE 8: INDUSTRY REGULATIONS
# =============================================================================

INDUSTRY_REGULATION_TEMPLATES = {
    "compliance": [
        # -----------------------------------------------------------------
        # SOX COMPLIANCE
        # -----------------------------------------------------------------
        {
            "id": "CMP-SOX-001",
            "name": "SOX IT controls assessment",
            "description": "Assess IT general controls for SOX compliance",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (50000, 150000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "regulatory_driver": ["SOX"],
            "prerequisites": [],
            "outputs": ["ITGC inventory", "Control gaps", "Risk assessment", "Remediation roadmap"],
            "notes": "Required for US public companies",
        },
        {
            "id": "CMP-SOX-002",
            "name": "SOX ITGC remediation",
            "description": "Remediate IT general control deficiencies",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (75000, 250000),
            "timeline_months": (2, 6),
            "requires_tsa": False,
            "regulatory_driver": ["SOX"],
            "prerequisites": ["CMP-SOX-001"],
            "outputs": ["Remediated controls", "Control documentation", "Testing evidence"],
        },
        {
            "id": "CMP-SOX-003",
            "name": "SOX control documentation",
            "description": "Document IT controls for SOX compliance",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (40000, 100000),
            "per_system_cost": (3000, 10000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "regulatory_driver": ["SOX"],
            "prerequisites": ["CMP-SOX-001"],
            "outputs": ["Control matrices", "Process narratives", "Control descriptions", "RCM updates"],
        },
        {
            "id": "CMP-SOX-004",
            "name": "SOX segregation of duties analysis",
            "description": "Analyze and remediate SoD conflicts in key systems",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (30000, 80000),
            "per_system_cost": (5000, 20000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "regulatory_driver": ["SOX"],
            "prerequisites": ["CMP-SOX-001"],
            "outputs": ["SoD matrix", "Conflict analysis", "Remediation plan", "Mitigating controls"],
        },
        # -----------------------------------------------------------------
        # HIPAA
        # -----------------------------------------------------------------
        {
            "id": "CMP-HIP-001",
            "name": "HIPAA security assessment",
            "description": "Assess HIPAA Security Rule compliance",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (40000, 120000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "regulatory_driver": ["HIPAA"],
            "prerequisites": [],
            "outputs": ["HIPAA gap analysis", "Risk assessment", "ePHI inventory", "Remediation roadmap"],
            "notes": "Required for covered entities and business associates",
        },
        {
            "id": "CMP-HIP-002",
            "name": "HIPAA remediation program",
            "description": "Implement HIPAA security controls",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (75000, 300000),
            "timeline_months": (3, 9),
            "requires_tsa": False,
            "regulatory_driver": ["HIPAA"],
            "prerequisites": ["CMP-HIP-001"],
            "outputs": ["Administrative safeguards", "Physical safeguards", "Technical safeguards", "Policies and procedures"],
        },
        {
            "id": "CMP-HIP-003",
            "name": "Business Associate Agreement management",
            "description": "Establish BAA framework and vendor compliance",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (20000, 60000),
            "per_vendor_cost": (500, 2000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "regulatory_driver": ["HIPAA"],
            "prerequisites": [],
            "outputs": ["BAA template", "Vendor inventory", "Executed BAAs", "Compliance tracking"],
        },
        # -----------------------------------------------------------------
        # PCI-DSS
        # -----------------------------------------------------------------
        {
            "id": "CMP-PCI-001",
            "name": "PCI-DSS scope assessment",
            "description": "Assess PCI-DSS scope and compliance requirements",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (30000, 80000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "regulatory_driver": ["PCI-DSS"],
            "prerequisites": [],
            "outputs": ["Scope definition", "Network diagram", "Data flow analysis", "Gap assessment"],
            "notes": "Required if processing payment card data",
        },
        {
            "id": "CMP-PCI-002",
            "name": "PCI-DSS remediation",
            "description": "Remediate PCI-DSS compliance gaps",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (50000, 200000),
            "timeline_months": (2, 6),
            "requires_tsa": False,
            "regulatory_driver": ["PCI-DSS"],
            "prerequisites": ["CMP-PCI-001"],
            "outputs": ["Control implementation", "Network segmentation", "Encryption", "Access controls"],
        },
        {
            "id": "CMP-PCI-003",
            "name": "PCI-DSS certification (QSA assessment)",
            "description": "Engage QSA for PCI-DSS certification",
            "activity_type": "certification",
            "phase": "certification",
            "base_cost": (40000, 150000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "regulatory_driver": ["PCI-DSS"],
            "prerequisites": ["CMP-PCI-002"],
            "outputs": ["ROC", "AOC", "SAQ (if applicable)"],
            "notes": "Level 1 merchants require QSA; others may self-assess",
        },
        # -----------------------------------------------------------------
        # FINANCIAL SERVICES
        # -----------------------------------------------------------------
        {
            "id": "CMP-FIN-001",
            "name": "GLBA compliance assessment",
            "description": "Assess GLBA Safeguards Rule compliance",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (30000, 80000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "regulatory_driver": ["GLBA"],
            "prerequisites": [],
            "outputs": ["GLBA gap analysis", "Risk assessment", "Control inventory"],
        },
        {
            "id": "CMP-FIN-002",
            "name": "GLBA/financial services remediation",
            "description": "Implement GLBA and financial services controls",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (50000, 150000),
            "timeline_months": (2, 4),
            "requires_tsa": False,
            "regulatory_driver": ["GLBA"],
            "prerequisites": ["CMP-FIN-001"],
            "outputs": ["Information security program", "Access controls", "Encryption", "Vendor management"],
        },
        {
            "id": "CMP-FIN-003",
            "name": "NYDFS cybersecurity compliance",
            "description": "Comply with NY DFS 23 NYCRR 500",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (50000, 150000),
            "timeline_months": (2, 4),
            "requires_tsa": False,
            "regulatory_driver": ["NYDFS 500"],
            "prerequisites": [],
            "outputs": ["Cybersecurity program", "CISO appointment", "Penetration testing", "Annual certification"],
            "notes": "Required for financial services in NY",
        },
    ],
}

# =============================================================================
# PHASE 8: SECURITY COMPLIANCE
# =============================================================================

SECURITY_COMPLIANCE_TEMPLATES = {
    "compliance": [
        # -----------------------------------------------------------------
        # SOC 2
        # -----------------------------------------------------------------
        {
            "id": "CMP-SOC-001",
            "name": "SOC 2 readiness assessment",
            "description": "Assess readiness for SOC 2 Type I/II certification",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (30000, 80000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "regulatory_driver": ["SOC 2"],
            "prerequisites": [],
            "outputs": ["Gap analysis", "Trust services criteria mapping", "Remediation roadmap"],
        },
        {
            "id": "CMP-SOC-002",
            "name": "SOC 2 control implementation",
            "description": "Implement controls for SOC 2 compliance",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (75000, 250000),
            "timeline_months": (3, 6),
            "requires_tsa": False,
            "regulatory_driver": ["SOC 2"],
            "prerequisites": ["CMP-SOC-001"],
            "outputs": ["Control implementation", "Policy updates", "Evidence collection process"],
        },
        {
            "id": "CMP-SOC-003",
            "name": "SOC 2 Type I audit",
            "description": "Engage auditor for SOC 2 Type I report",
            "activity_type": "certification",
            "phase": "certification",
            "base_cost": (40000, 100000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "regulatory_driver": ["SOC 2"],
            "prerequisites": ["CMP-SOC-002"],
            "outputs": ["SOC 2 Type I report", "Management assertion"],
        },
        {
            "id": "CMP-SOC-004",
            "name": "SOC 2 Type II audit",
            "description": "Engage auditor for SOC 2 Type II report",
            "activity_type": "certification",
            "phase": "certification",
            "base_cost": (60000, 150000),
            "timeline_months": (3, 6),  # Observation period
            "requires_tsa": False,
            "regulatory_driver": ["SOC 2"],
            "prerequisites": ["CMP-SOC-003"],
            "outputs": ["SOC 2 Type II report", "Management assertion"],
            "notes": "Requires 6-12 month observation period",
        },
        # -----------------------------------------------------------------
        # ISO 27001
        # -----------------------------------------------------------------
        {
            "id": "CMP-ISO-001",
            "name": "ISO 27001 gap assessment",
            "description": "Assess readiness for ISO 27001 certification",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (35000, 90000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "regulatory_driver": ["ISO 27001"],
            "prerequisites": [],
            "outputs": ["Gap analysis", "Risk assessment", "Statement of Applicability draft"],
        },
        {
            "id": "CMP-ISO-002",
            "name": "ISO 27001 ISMS implementation",
            "description": "Implement Information Security Management System",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (100000, 350000),
            "timeline_months": (4, 9),
            "requires_tsa": False,
            "regulatory_driver": ["ISO 27001"],
            "prerequisites": ["CMP-ISO-001"],
            "outputs": ["ISMS documentation", "Risk treatment plan", "Control implementation", "Internal audit capability"],
        },
        {
            "id": "CMP-ISO-003",
            "name": "ISO 27001 certification audit",
            "description": "Engage certification body for ISO 27001 audit",
            "activity_type": "certification",
            "phase": "certification",
            "base_cost": (30000, 80000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "regulatory_driver": ["ISO 27001"],
            "prerequisites": ["CMP-ISO-002"],
            "outputs": ["ISO 27001 certificate", "Surveillance audit schedule"],
        },
        # -----------------------------------------------------------------
        # NIST FRAMEWORKS
        # -----------------------------------------------------------------
        {
            "id": "CMP-NST-001",
            "name": "NIST CSF assessment",
            "description": "Assess cybersecurity maturity against NIST CSF",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (30000, 80000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "regulatory_driver": ["NIST CSF"],
            "prerequisites": [],
            "outputs": ["Current profile", "Target profile", "Gap analysis", "Roadmap"],
        },
        {
            "id": "CMP-NST-002",
            "name": "NIST CSF implementation",
            "description": "Implement controls aligned to NIST CSF",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (75000, 250000),
            "timeline_months": (3, 9),
            "requires_tsa": False,
            "regulatory_driver": ["NIST CSF"],
            "prerequisites": ["CMP-NST-001"],
            "outputs": ["Control implementation", "Maturity improvement", "Documentation"],
        },
        {
            "id": "CMP-NST-003",
            "name": "NIST 800-53 control assessment",
            "description": "Assess against NIST 800-53 control catalog",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (40000, 120000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "regulatory_driver": ["NIST 800-53", "FedRAMP"],
            "prerequisites": [],
            "outputs": ["Control assessment", "POA&M", "SSP draft"],
            "notes": "Required for federal government contractors",
        },
        # -----------------------------------------------------------------
        # OTHER CERTIFICATIONS
        # -----------------------------------------------------------------
        {
            "id": "CMP-CRT-001",
            "name": "HITRUST assessment",
            "description": "HITRUST CSF assessment and certification",
            "activity_type": "certification",
            "phase": "certification",
            "base_cost": (75000, 250000),
            "timeline_months": (4, 8),
            "requires_tsa": False,
            "regulatory_driver": ["HITRUST"],
            "prerequisites": [],
            "outputs": ["HITRUST assessment", "Certification (if applicable)"],
            "notes": "Common in healthcare; combines multiple frameworks",
        },
        {
            "id": "CMP-CRT-002",
            "name": "FedRAMP authorization support",
            "description": "Support FedRAMP authorization process",
            "activity_type": "certification",
            "phase": "certification",
            "base_cost": (200000, 750000),
            "timeline_months": (9, 18),
            "requires_tsa": False,
            "regulatory_driver": ["FedRAMP"],
            "prerequisites": [],
            "outputs": ["SSP", "SAR", "POA&M", "ATO"],
            "notes": "Required for federal cloud services; extensive effort",
        },
    ],
}

# =============================================================================
# PHASE 8: AUDIT READINESS
# =============================================================================

AUDIT_READINESS_TEMPLATES = {
    "compliance": [
        # -----------------------------------------------------------------
        # INTERNAL AUDIT
        # -----------------------------------------------------------------
        {
            "id": "CMP-AUD-001",
            "name": "IT audit universe development",
            "description": "Develop IT audit universe and risk-based audit plan",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (25000, 60000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "regulatory_driver": ["Internal Audit"],
            "prerequisites": [],
            "outputs": ["Audit universe", "Risk assessment", "Annual audit plan"],
        },
        {
            "id": "CMP-AUD-002",
            "name": "IT internal audit capability",
            "description": "Establish or enhance IT internal audit function",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (50000, 150000),
            "timeline_months": (2, 4),
            "requires_tsa": False,
            "regulatory_driver": ["Internal Audit"],
            "prerequisites": [],
            "outputs": ["Audit methodology", "Audit tools", "Team training", "Audit programs"],
        },
        {
            "id": "CMP-AUD-003",
            "name": "Control self-assessment program",
            "description": "Implement control self-assessment process",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (30000, 80000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "regulatory_driver": ["Internal Audit", "SOX"],
            "prerequisites": [],
            "outputs": ["CSA process", "Assessment tools", "Reporting framework"],
        },
        # -----------------------------------------------------------------
        # EXTERNAL AUDIT PREP
        # -----------------------------------------------------------------
        {
            "id": "CMP-AUD-010",
            "name": "External audit readiness assessment",
            "description": "Prepare for external IT audit (financial statement)",
            "activity_type": "assessment",
            "phase": "assessment",
            "base_cost": (25000, 70000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "regulatory_driver": ["External Audit"],
            "prerequisites": [],
            "outputs": ["Readiness assessment", "Evidence inventory", "Gap remediation plan"],
        },
        {
            "id": "CMP-AUD-011",
            "name": "Audit evidence repository setup",
            "description": "Establish centralized audit evidence management",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (20000, 60000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "regulatory_driver": ["External Audit", "SOX"],
            "prerequisites": [],
            "outputs": ["Evidence repository", "Collection process", "Retention policy"],
        },
        {
            "id": "CMP-AUD-012",
            "name": "Audit support during examination",
            "description": "Provide support during external audit examination",
            "activity_type": "implementation",
            "phase": "certification",
            "base_cost": (30000, 100000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "regulatory_driver": ["External Audit"],
            "prerequisites": [],
            "outputs": ["PBC responses", "Walkthroughs", "Evidence provision", "Finding remediation"],
        },
        # -----------------------------------------------------------------
        # CONTINUOUS MONITORING
        # -----------------------------------------------------------------
        {
            "id": "CMP-AUD-020",
            "name": "Continuous control monitoring setup",
            "description": "Implement automated control monitoring",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (50000, 150000),
            "per_control_cost": (500, 2000),
            "timeline_months": (2, 4),
            "requires_tsa": False,
            "regulatory_driver": ["SOX", "Compliance"],
            "prerequisites": [],
            "outputs": ["Automated monitoring", "Exception reporting", "Dashboard"],
        },
        {
            "id": "CMP-AUD-021",
            "name": "GRC platform implementation",
            "description": "Implement governance, risk, and compliance platform",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (75000, 300000),
            "per_module_cost": (20000, 75000),
            "timeline_months": (3, 6),
            "requires_tsa": False,
            "regulatory_driver": ["GRC"],
            "prerequisites": [],
            "outputs": ["GRC platform", "Control library", "Risk register", "Issue tracking"],
            "notes": "ServiceNow GRC, RSA Archer, OneTrust, etc.",
        },
    ],
}

# =============================================================================
# PHASE 8: POLICY & PROCEDURES
# =============================================================================

POLICY_TEMPLATES = {
    "compliance": [
        # -----------------------------------------------------------------
        # IT GOVERNANCE
        # -----------------------------------------------------------------
        {
            "id": "CMP-POL-001",
            "name": "IT governance framework establishment",
            "description": "Establish IT governance framework and structures",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (40000, 100000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "regulatory_driver": ["Governance"],
            "prerequisites": [],
            "outputs": ["Governance framework", "Steering committee charter", "Decision rights", "RACI matrix"],
        },
        {
            "id": "CMP-POL-002",
            "name": "IT policy framework development",
            "description": "Develop comprehensive IT policy framework",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (50000, 150000),
            "timeline_months": (2, 4),
            "requires_tsa": False,
            "regulatory_driver": ["Compliance"],
            "prerequisites": [],
            "outputs": ["Policy framework", "Core policies", "Standards", "Guidelines"],
        },
        # -----------------------------------------------------------------
        # SECURITY POLICIES
        # -----------------------------------------------------------------
        {
            "id": "CMP-POL-010",
            "name": "Information security policy suite",
            "description": "Develop information security policies",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (40000, 120000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "regulatory_driver": ["ISO 27001", "SOC 2", "Security"],
            "prerequisites": [],
            "outputs": ["Security policy", "Acceptable use policy", "Access control policy", "Incident response policy"],
        },
        {
            "id": "CMP-POL-011",
            "name": "Security procedures and standards",
            "description": "Develop security procedures and technical standards",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (30000, 80000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "regulatory_driver": ["Security"],
            "prerequisites": ["CMP-POL-010"],
            "outputs": ["Configuration standards", "Hardening guides", "Operational procedures"],
        },
        {
            "id": "CMP-POL-012",
            "name": "Incident response plan development",
            "description": "Develop and test incident response capabilities",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (35000, 100000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "regulatory_driver": ["Security", "GDPR", "HIPAA"],
            "prerequisites": [],
            "outputs": ["IR plan", "Playbooks", "Communication templates", "Tabletop exercise"],
        },
        {
            "id": "CMP-POL-013",
            "name": "Business continuity / DR planning",
            "description": "Develop BC/DR plans and procedures",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (50000, 150000),
            "timeline_months": (2, 4),
            "requires_tsa": False,
            "regulatory_driver": ["Business Continuity"],
            "prerequisites": [],
            "outputs": ["BC plan", "DR plan", "RTO/RPO definitions", "Testing procedures"],
        },
        # -----------------------------------------------------------------
        # OPERATIONAL POLICIES
        # -----------------------------------------------------------------
        {
            "id": "CMP-POL-020",
            "name": "IT operations policies and procedures",
            "description": "Develop IT operations documentation",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (30000, 80000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "regulatory_driver": ["Operations"],
            "prerequisites": [],
            "outputs": ["Change management", "Problem management", "Release management", "Capacity management"],
        },
        {
            "id": "CMP-POL-021",
            "name": "Data management policies",
            "description": "Develop data governance and management policies",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (30000, 80000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "regulatory_driver": ["Data Governance", "Privacy"],
            "prerequisites": [],
            "outputs": ["Data governance policy", "Data classification", "Retention policy", "Quality standards"],
        },
        {
            "id": "CMP-POL-022",
            "name": "Vendor management policy",
            "description": "Develop vendor/third-party management framework",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (25000, 70000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "regulatory_driver": ["Vendor Management", "Compliance"],
            "prerequisites": [],
            "outputs": ["Vendor policy", "Risk assessment framework", "Contract requirements", "Monitoring process"],
        },
        # -----------------------------------------------------------------
        # TRAINING & AWARENESS
        # -----------------------------------------------------------------
        {
            "id": "CMP-POL-030",
            "name": "Security awareness program",
            "description": "Establish security awareness training program",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (25000, 75000),
            "per_user_cost": (10, 30),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "regulatory_driver": ["Security", "Compliance"],
            "prerequisites": [],
            "outputs": ["Training platform", "Course content", "Phishing simulation", "Compliance tracking"],
        },
        {
            "id": "CMP-POL-031",
            "name": "Role-based compliance training",
            "description": "Develop role-specific compliance training",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (20000, 60000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "regulatory_driver": ["HIPAA", "PCI", "Privacy"],
            "prerequisites": [],
            "outputs": ["Training modules", "Certification tracking", "Annual refreshers"],
        },
    ],
}

# =============================================================================
# COMBINED TEMPLATES FOR PHASE 8
# =============================================================================

def get_phase8_templates() -> Dict[str, Dict[str, List[Dict]]]:
    """Get all Phase 8 templates organized by category and workstream."""
    return {
        "compliance": {
            "data_privacy": DATA_PRIVACY_TEMPLATES["compliance"],
            "industry_regulation": INDUSTRY_REGULATION_TEMPLATES["compliance"],
            "security_compliance": SECURITY_COMPLIANCE_TEMPLATES["compliance"],
            "audit_readiness": AUDIT_READINESS_TEMPLATES["compliance"],
            "policy_procedures": POLICY_TEMPLATES["compliance"],
        },
    }


def get_phase8_activity_by_id(activity_id: str) -> Dict:
    """Look up a Phase 8 activity by its ID."""
    all_templates = get_phase8_templates()

    for category, workstreams in all_templates.items():
        for workstream, activities in workstreams.items():
            for activity in activities:
                if activity.get("id") == activity_id:
                    return activity

    return None


def calculate_phase8_activity_cost(
    activity: Dict,
    user_count: int = 1000,
    system_count: int = 30,
    vendor_count: int = 50,
    site_count: int = 8,
    control_count: int = 100,
    module_count: int = 3,
    complexity: str = "moderate",
    industry: str = "standard",
) -> tuple:
    """
    Calculate cost range for a Phase 8 activity based on quantities and modifiers.

    Returns: (low, high, formula)
    """
    # Get complexity and industry multipliers
    complexity_mult = COMPLEXITY_MULTIPLIERS.get(complexity, 1.0)
    industry_mult = INDUSTRY_MODIFIERS.get(industry, 1.0)
    combined_mult = complexity_mult * industry_mult

    low, high = 0, 0
    formula_parts = []

    # Base cost
    if "base_cost" in activity:
        base_low, base_high = activity["base_cost"]
        low += base_low
        high += base_high
        formula_parts.append(f"Base: ${base_low:,.0f}-${base_high:,.0f}")

    # Per-unit costs
    if "per_user_cost" in activity:
        per_low, per_high = activity["per_user_cost"]
        low += per_low * user_count
        high += per_high * user_count
        formula_parts.append(f"{user_count:,} users × ${per_low}-${per_high}")

    if "per_system_cost" in activity:
        per_low, per_high = activity["per_system_cost"]
        low += per_low * system_count
        high += per_high * system_count
        formula_parts.append(f"{system_count} systems × ${per_low:,}-${per_high:,}")

    if "per_vendor_cost" in activity:
        per_low, per_high = activity["per_vendor_cost"]
        low += per_low * vendor_count
        high += per_high * vendor_count
        formula_parts.append(f"{vendor_count} vendors × ${per_low:,}-${per_high:,}")

    if "per_site_cost" in activity:
        per_low, per_high = activity["per_site_cost"]
        low += per_low * site_count
        high += per_high * site_count
        formula_parts.append(f"{site_count} sites × ${per_low:,}-${per_high:,}")

    if "per_control_cost" in activity:
        per_low, per_high = activity["per_control_cost"]
        low += per_low * control_count
        high += per_high * control_count
        formula_parts.append(f"{control_count} controls × ${per_low:,}-${per_high:,}")

    if "per_module_cost" in activity:
        per_low, per_high = activity["per_module_cost"]
        low += per_low * module_count
        high += per_high * module_count
        formula_parts.append(f"{module_count} modules × ${per_low:,}-${per_high:,}")

    formula = " + ".join(formula_parts) if formula_parts else "Unknown cost model"

    # Apply modifiers
    if combined_mult != 1.0:
        low = int(low * combined_mult)
        high = int(high * combined_mult)
        formula += f" × {combined_mult:.2f} ({complexity}/{industry})"

    return (int(low), int(high), formula)


def get_regulatory_requirements(
    industries: List[str] = None,
    data_types: List[str] = None,
    geographies: List[str] = None,
) -> List[str]:
    """
    Determine applicable regulatory requirements based on business context.

    Returns list of regulatory drivers that likely apply.
    """
    requirements = set()

    # Industry-based requirements
    industry_regs = {
        "healthcare": ["HIPAA", "HITRUST"],
        "financial_services": ["SOX", "GLBA", "PCI-DSS", "NYDFS 500"],
        "retail": ["PCI-DSS", "CCPA"],
        "technology": ["SOC 2", "ISO 27001"],
        "government": ["FedRAMP", "NIST 800-53", "FISMA"],
        "manufacturing": ["NIST CSF"],
    }

    if industries:
        for ind in industries:
            if ind.lower() in industry_regs:
                requirements.update(industry_regs[ind.lower()])

    # Data type requirements
    data_regs = {
        "pii": ["GDPR", "CCPA", "Privacy"],
        "phi": ["HIPAA"],
        "payment_card": ["PCI-DSS"],
        "financial": ["SOX", "GLBA"],
    }

    if data_types:
        for dt in data_types:
            if dt.lower() in data_regs:
                requirements.update(data_regs[dt.lower()])

    # Geography requirements
    geo_regs = {
        "eu": ["GDPR"],
        "california": ["CCPA", "CPRA"],
        "new_york_financial": ["NYDFS 500"],
        "federal_us": ["FedRAMP", "FISMA"],
    }

    if geographies:
        for geo in geographies:
            if geo.lower() in geo_regs:
                requirements.update(geo_regs[geo.lower()])

    return sorted(list(requirements))


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'DATA_PRIVACY_TEMPLATES',
    'INDUSTRY_REGULATION_TEMPLATES',
    'SECURITY_COMPLIANCE_TEMPLATES',
    'AUDIT_READINESS_TEMPLATES',
    'POLICY_TEMPLATES',
    'get_phase8_templates',
    'get_phase8_activity_by_id',
    'calculate_phase8_activity_cost',
    'get_regulatory_requirements',
]
