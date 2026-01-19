# IT Integration Cost Database Reference

**Last Updated:** January 2026
**Total Activities:** 100
**Status:** ✅ COMPLETE - Ready for team validation

---

## Overview

This document tracks research-backed cost estimates for IT integration activities commonly encountered in M&A due diligence. These estimates are used by the consistency engine to provide deterministic, defensible cost calculations.

### Methodology

**Formula:** `Final Cost = Base Cost × Size Multiplier × Industry Factor × Geography Factor × IT Maturity Factor`

| Factor | Range | Description |
|--------|-------|-------------|
| Size Multiplier | 0.4x - 4.0x | Based on employee count |
| Industry Factor | 0.9x - 1.5x | Regulatory/complexity by industry |
| Geography Factor | 1.0x - 1.6x | Single country to global |
| IT Maturity Factor | 0.8x - 1.6x | Advanced to minimal maturity |

### Size Multipliers

| Size Tier | Employee Range | Multiplier |
|-----------|----------------|------------|
| Micro | <50 | 0.4x |
| Small | 50-100 | 0.6x |
| Small-Medium | 100-250 | 0.8x |
| Mid-Market | 250-500 | 1.0x (baseline) |
| Upper Mid-Market | 500-1000 | 1.5x |
| Lower Enterprise | 1000-2500 | 2.0x |
| Mid Enterprise | 2500-5000 | 3.0x |
| Large Enterprise | 5000+ | 4.0x |

---

## Database Summary by Category

| Category | Count | Status |
|----------|-------|--------|
| ERP | 5 | ✅ |
| CRM | 8 | ✅ |
| Identity/IAM | 10 | ✅ |
| Cloud | 12 | ✅ |
| Infrastructure | 11 | ✅ |
| Cybersecurity | 15 | ✅ |
| Disaster Recovery | 5 | ✅ |
| ITSM | 5 | ✅ |
| HCM/HR | 6 | ✅ |
| Applications | 8 | ✅ |
| M&A Integration | 10 | ✅ |
| Data & Analytics | 5 | ✅ |
| **TOTAL** | **100** | ✅ |

---

## Export Files

For detailed review, the following CSV exports are available:

1. **`docs/cost_database_detailed.csv`** - Full export with one row per activity/tier combination (400 rows)
2. **`docs/cost_database_summary.csv`** - Summary view with one row per activity, all tiers in columns (100 rows)

To regenerate exports:
```bash
python -m tools_v2.cost_database --export
```

---

## Activity Categories

### ERP Systems (5 activities)

| ID | Name | Medium Range | Duration |
|----|------|--------------|----------|
| ERP-001 | NetSuite ERP Implementation | $100K - $250K | 12-40 wks |
| ERP-002 | SAP S/4HANA Implementation | $500K - $1.5M | 24-104 wks |
| ERP-003 | Oracle Cloud ERP Implementation | $350K - $800K | 20-78 wks |
| ERP-004 | ERP Integration (Middleware/API) | $75K - $200K | 4-24 wks |
| ERP-005 | ERP Data Migration | $50K - $150K | 4-20 wks |

### CRM Systems (8 activities)

| ID | Name | Medium Range | Duration |
|----|------|--------------|----------|
| CRM-001 | Salesforce CRM Implementation | $50K - $150K | 6-26 wks |
| CRM-002 | HubSpot CRM Implementation | $20K - $75K | 4-16 wks |
| CRM-003 | Microsoft Dynamics 365 CRM | $80K - $200K | 8-30 wks |
| CRM-004 | CRM to CRM Migration | $40K - $100K | 4-16 wks |
| CRM-005 | Zendesk Implementation | $25K - $75K | 3-12 wks |
| CRM-006 | Freshworks CRM Implementation | $15K - $50K | 2-10 wks |
| CRM-007 | Zoho CRM Implementation | $12K - $40K | 2-12 wks |
| CRM-008 | CPQ Implementation | $80K - $200K | 8-24 wks |

### Identity & Access Management (10 activities)

| ID | Name | Medium Range | Duration |
|----|------|--------------|----------|
| IAM-001 | Okta SSO/IAM Implementation | $40K - $100K | 4-16 wks |
| IAM-002 | Azure AD / Entra ID Implementation | $30K - $80K | 2-12 wks |
| IAM-003 | Active Directory Migration | $75K - $200K | 8-30 wks |
| IAM-004 | PAM Implementation (CyberArk) | $150K - $400K | 12-40 wks |
| IAM-005 | Ping Identity Implementation | $50K - $150K | 6-20 wks |
| IAM-006 | SailPoint IGA Implementation | $250K - $600K | 16-52 wks |
| IAM-007 | MFA Rollout (Standalone) | $30K - $80K | 4-12 wks |
| IAM-008 | Directory Sync/Federation | $25K - $75K | 2-12 wks |
| IAM-009 | Zero Trust Network Access | $75K - $200K | 6-20 wks |
| IAM-010 | OneLogin Implementation | $35K - $90K | 3-14 wks |

### Cloud & Migration (12 activities)

| ID | Name | Medium Range | Duration |
|----|------|--------------|----------|
| CLOUD-001 | AWS Cloud Migration | $100K - $300K | 8-52 wks |
| CLOUD-002 | Azure Cloud Migration | $100K - $300K | 8-52 wks |
| CLOUD-003 | Microsoft 365 Migration | $20K - $75K | 2-16 wks |
| CLOUD-004 | Google Workspace Migration | $15K - $50K | 2-12 wks |
| CLOUD-005 | GCP Migration | $100K - $300K | 8-52 wks |
| CLOUD-006 | Multi-Cloud Strategy | $150K - $400K | 12-40 wks |
| CLOUD-007 | Kubernetes/Container Platform | $80K - $250K | 8-30 wks |
| CLOUD-008 | VDI Migration (Citrix/Horizon) | $100K - $300K | 8-30 wks |
| CLOUD-009 | Cloud FinOps Program | $40K - $120K | 4-16 wks |
| CLOUD-010 | SaaS Consolidation | $60K - $150K | 6-20 wks |
| CLOUD-011 | Serverless Migration | $60K - $180K | 6-26 wks |
| CLOUD-012 | Cloud Governance Framework | $70K - $200K | 6-24 wks |

### Infrastructure (11 activities)

| ID | Name | Medium Range | Duration |
|----|------|--------------|----------|
| INFRA-001 | Data Center Consolidation | $300K - $800K | 20-78 wks |
| INFRA-002 | Network Infrastructure Refresh | $50K - $150K | 4-20 wks |
| INFRA-003 | Server Infrastructure Refresh | $75K - $250K | 8-30 wks |
| INFRA-004 | SD-WAN Implementation | $80K - $250K | 8-30 wks |
| INFRA-005 | VoIP/Unified Communications | $50K - $150K | 4-20 wks |
| INFRA-006 | Wireless Network Refresh | $35K - $100K | 4-16 wks |
| INFRA-007 | Storage Infrastructure Refresh | $100K - $350K | 8-24 wks |
| INFRA-008 | Print Infrastructure Consolidation | $30K - $80K | 4-16 wks |
| INFRA-009 | Physical Security Systems | $60K - $180K | 6-20 wks |
| INFRA-010 | Structured Cabling | $50K - $150K | 4-16 wks |
| INFRA-011 | Building Automation/IoT | $75K - $200K | 8-26 wks |

### Cybersecurity (15 activities)

| ID | Name | Medium Range | Duration |
|----|------|--------------|----------|
| SEC-001 | SIEM Implementation | $150K - $400K | 8-26 wks |
| SEC-002 | EDR Deployment | $30K - $80K | 2-8 wks |
| SEC-003 | Penetration Testing | $15K - $40K | 1-6 wks |
| SEC-004 | Vulnerability Management Program | $50K - $150K | 4-16 wks |
| SEC-005 | Compliance Remediation (SOC2) | $80K - $200K | 12-40 wks |
| SEC-006 | Zero Trust Architecture | $150K - $400K | 16-52 wks |
| SEC-007 | DLP Implementation | $80K - $200K | 8-26 wks |
| SEC-008 | Email Security Gateway | $30K - $80K | 2-8 wks |
| SEC-009 | Secure Web Gateway | $60K - $180K | 4-16 wks |
| SEC-010 | Security Awareness Training | $15K - $40K | 2-8 wks |
| SEC-011 | Incident Response Planning | $40K - $100K | 4-16 wks |
| SEC-012 | Threat Intelligence Platform | $60K - $180K | 6-20 wks |
| SEC-013 | SOC Setup | $300K - $800K | 16-52 wks |
| SEC-014 | Cloud Security Posture (CSPM) | $70K - $200K | 4-16 wks |
| SEC-015 | Application Security Testing | $80K - $220K | 8-26 wks |

### Disaster Recovery (5 activities)

| ID | Name | Medium Range | Duration |
|----|------|--------------|----------|
| DR-001 | Enterprise Backup Solution | $60K - $150K | 4-16 wks |
| DR-002 | DR Plan Development | $40K - $100K | 4-16 wks |
| DR-003 | Cloud Backup Implementation | $30K - $80K | 2-12 wks |
| DR-004 | DR Site Setup | $150K - $400K | 12-40 wks |
| DR-005 | Business Continuity Planning | $60K - $150K | 6-20 wks |

### ITSM & Service Management (5 activities)

| ID | Name | Medium Range | Duration |
|----|------|--------------|----------|
| ITSM-001 | ServiceNow Implementation | $200K - $500K | 12-52 wks |
| ITSM-002 | Jira Service Management | $30K - $80K | 4-16 wks |
| ITSM-003 | BMC Helix/Remedy | $200K - $500K | 12-52 wks |
| ITSM-004 | Freshservice Implementation | $25K - $70K | 3-14 wks |
| ITSM-005 | CMDB Implementation | $70K - $180K | 8-26 wks |

### HCM & HR Systems (6 activities)

| ID | Name | Medium Range | Duration |
|----|------|--------------|----------|
| HCM-001 | Workday HCM Implementation | $500K - $1.5M | 24-78 wks |
| HCM-002 | ADP Workforce Now | $40K - $100K | 6-20 wks |
| HCM-003 | SAP SuccessFactors | $400K - $1M | 20-65 wks |
| HCM-004 | UKG Implementation | $120K - $350K | 12-40 wks |
| HCM-005 | BambooHR Implementation | $15K - $40K | 2-10 wks |
| HCM-006 | Payroll System Migration | $60K - $180K | 8-26 wks |

### Applications (8 activities)

| ID | Name | Medium Range | Duration |
|----|------|--------------|----------|
| APP-001 | Application Portfolio Assessment | $50K - $120K | 4-12 wks |
| APP-002 | Application Decommissioning | $30K - $80K | 4-16 wks |
| APP-003 | Custom App Modernization | $150K - $400K | 12-52 wks |
| APP-004 | Mobile App Development | $80K - $250K | 8-30 wks |
| APP-005 | BI Platform (Tableau/PowerBI) | $70K - $200K | 6-24 wks |
| APP-006 | SharePoint/Document Management | $50K - $150K | 6-24 wks |
| APP-007 | Contract Lifecycle Management | $80K - $200K | 8-24 wks |
| APP-008 | E-Commerce Platform | $60K - $200K | 8-30 wks |

### M&A Integration (10 activities)

| ID | Name | Medium Range | Duration |
|----|------|--------------|----------|
| MA-001 | IT Due Diligence Assessment | $75K - $200K | 2-8 wks |
| MA-002 | Day 1 Readiness Program | $150K - $400K | 4-16 wks |
| MA-003 | TSA Management | $75K - $200K/mo | 26-104 wks |
| MA-004 | IT Integration Planning | $80K - $200K | 4-12 wks |
| MA-005 | IT Cost Synergy Capture | $150K - $400K | 12-52 wks |
| MA-006 | Carve-Out IT Separation | $400K - $1M | 16-78 wks |
| MA-007 | IT Operating Model Harmonization | $120K - $350K | 8-30 wks |
| MA-008 | Vendor Contract Rationalization | $75K - $200K | 8-26 wks |
| MA-009 | License True-Up & Optimization | $60K - $180K | 6-20 wks |
| MA-010 | Post-Merger IT Governance | $90K - $250K | 6-24 wks |

### Data & Analytics (5 activities)

| ID | Name | Medium Range | Duration |
|----|------|--------------|----------|
| DATA-001 | Data Warehouse Implementation | $120K - $350K | 8-30 wks |
| DATA-002 | ETL/Data Pipeline | $75K - $220K | 6-24 wks |
| DATA-003 | Master Data Management | $200K - $500K | 16-52 wks |
| DATA-004 | Data Governance Program | $90K - $250K | 12-40 wks |
| DATA-005 | Analytics/ML Platform | $150K - $400K | 12-40 wks |

---

## Research Sources

### Primary Sources
- Vendor pricing guides (NetSuite, SAP, Oracle, Salesforce, Microsoft, Okta, Workday)
- Implementation partner rate cards
- Gartner/Forrester research reports
- Industry benchmarks from M&A consultants
- IMAA Institute M&A research

### Secondary Sources
- Technology forums and communities
- Case studies and customer references
- RFP response databases
- Public company 10-K filings (IT spend)

---

## Validation Checklist

Before using in production, each cost estimate should be validated by:

- [ ] Internal team review (sanity check)
- [ ] Comparison with past deal data
- [ ] Partner/vendor confirmation where possible
- [ ] Industry expert review

---

## Usage in Code

```python
from tools_v2.cost_database import (
    COST_DATABASE,
    get_activity_cost,
    search_activities,
    estimate_total_integration_cost,
    ProjectTier
)

# Get a specific activity's cost at medium tier
cost = get_activity_cost("erp_netsuite_implementation", ProjectTier.MEDIUM)
print(f"NetSuite Medium: ${cost.low:,} - ${cost.high:,}")

# Search for activities by keyword
erp_activities = search_activities(["erp", "sap"])

# Estimate total integration cost with company multiplier
total = estimate_total_integration_cost([
    ("erp_netsuite_implementation", ProjectTier.MEDIUM),
    ("iam_okta_implementation", ProjectTier.MEDIUM),
    ("cloud_m365_migration", ProjectTier.LARGE),
], company_multiplier=1.5)
print(f"Total: {total['formatted']}")
```

---

## Change Log

| Date | Changes | Author |
|------|---------|--------|
| Jan 2026 | Initial database created with 38 activities | System |
| Jan 2026 | Expanded to 100 activities across 12 categories | System |
| | Added CSV export functionality | |
| | Added: CRM (4), IAM (6), Cloud (8), Infra (8), Security (10), DR (3), ITSM (3), HCM (4), Apps (6), M&A (5), Data (5) | |

