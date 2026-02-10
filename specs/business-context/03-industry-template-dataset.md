# Spec 03: Industry Template Dataset

**Feature:** Business Context
**Status:** Draft
**Dependencies:** Spec 01 (Company Profile — `size_tier`), Spec 02 (Industry Taxonomy — primary industry codes)
**Consumers:** Spec 04 (Benchmark Engine), Spec 05 (UI Rendering)

---

## Overview

JSON dataset of expected technology stacks, organizational patterns, benchmark metrics, typical risks, and core business workflows per industry + size tier. This is **REFERENCE DATA** — versioned, sourced, deterministic. Not LLM-generated. Rendered by the UI (Spec 05), consumed by the benchmark engine (Spec 04).

Each template answers the question: *"For a midmarket P&C insurance company, what does a typical IT environment look like?"* — with specific systems, vendor names, staffing patterns, cost benchmarks, workflow definitions, and deal-lens considerations. Every number has a source citation. Every system list is grounded in real vendor landscapes.

The templates consolidate and extend data already present in the codebase:
- `tools_v2/benchmark_library.py` — BenchmarkData with metric/industry/company_size/low/typical/high/source
- `tools_v2/cost_database.py` — 100+ ActivityCost entries across 12 categories with costs by size tier
- `tools_v2/cost_model.py` — 50+ COST_ANCHORS with per_user, fixed_by_size, fixed_by_complexity pricing
- `prompts/shared/industry_application_considerations.py` — Expected applications per industry with trigger words
- `stores/app_category_mappings.py` — 966+ apps with vendors, categories, industry tags

---

## Architecture

### New Files

| Path | Purpose |
|------|---------|
| `data/industry_templates/insurance.json` | Insurance template (P&C focus, midmarket) |
| `data/industry_templates/healthcare.json` | Healthcare template (Provider focus, midmarket) |
| `data/industry_templates/financial_services.json` | Financial Services template (Banking/Asset Mgmt, midmarket) |
| `data/industry_templates/manufacturing.json` | Manufacturing template (Discrete, midmarket) |
| `data/industry_templates/technology.json` | Technology template (SaaS, midmarket) |
| `data/industry_templates/general.json` | General/Fallback template (cross-industry averages) |
| `stores/industry_templates.py` | Template loader, accessor, schema validation |

### Data Flow

```
data/industry_templates/*.json
        |
        v
stores/industry_templates.py (IndustryTemplateStore)
        |
        +---> Spec 04: Benchmark Engine selects metrics for scoring
        |
        +---> Spec 05: UI renders expected stacks, workflows, deal lens
        |
        +---> Discovery Agent: compares actual vs. expected systems
```

### Relationship to Existing Modules

- **benchmark_library.py** — Templates include `expected_metrics` that align with the same metric keys (`it_pct_revenue`, `cost_per_employee`, `it_staff_ratio`, `app_count_ratio`). Template metrics may extend or refine existing benchmarks with industry-specific detail. The benchmark engine (Spec 04) uses template metrics as the primary source when a template exists, falling back to benchmark_library.py when no template is available.
- **industry_application_considerations.py** — Templates incorporate the expected application lists from this module into the `expected_systems` section, adding cost ranges, migration complexity, and vendor lists. The template is the structured data version of what the considerations module provides as prose.
- **cost_database.py / cost_model.py** — Template `typical_cost_range` values for expected systems are informed by COST_ANCHORS and ActivityCost entries but are expressed as simplified ranges for display purposes.
- **app_category_mappings.py** — Template `common_vendors` lists are validated against known vendors in APP_MAPPINGS to ensure consistency.

---

## Specification

### Template Schema

Each template file covers one primary industry. The file contains a top-level object with metadata and content sections. Size-tier-specific values are embedded within metric ranges (using the `by_size_tier` pattern where values differ materially) but the default presentation targets midmarket, the most common PE deal size.

```json
{
  "template_id": "string — unique identifier: {industry}_{sub_industry}_{size_tier}",
  "industry": "string — primary industry code from Spec 02 taxonomy",
  "sub_industry": "string|null — sub-industry specialization",
  "size_tier": "string — target size tier: small | midmarket | large",
  "version": "string — semver: 1.0, 1.1, etc.",
  "last_updated": "string — YYYY-MM format",
  "provenance": "string — description of data sources used to compile this template",

  "expected_systems": {
    "industry_critical": [
      {
        "category": "string — system category identifier (snake_case)",
        "description": "string — what this system does in business terms",
        "common_vendors": ["string — 2+ real vendor/product names"],
        "criticality": "string — critical | high | medium",
        "typical_cost_range": "string — display-ready cost range (e.g., '$500K-$2M/year')",
        "migration_complexity": "string — high | medium | low",
        "notes": "string — additional context for diligence teams"
      }
    ],
    "industry_common": ["... same structure, criticality typically high or medium"],
    "general_enterprise": ["... standard enterprise systems expected in any company"]
  },

  "expected_metrics": {
    "metric_key": {
      "low": "number",
      "typical": "number",
      "high": "number",
      "unit": "string — %, USD, ratio, count, years",
      "source": "string — specific publication or dataset name with year",
      "notes": "string|null — contextual notes"
    }
  },

  "expected_organization": {
    "typical_roles": [
      {
        "role": "string — job title",
        "category": "string — leadership | infrastructure | applications | security | service_desk | data | project_management | devops",
        "typical_count": "string — range like '2-3' or single like '1'",
        "notes": "string|null"
      }
    ],
    "typical_outsourcing": [
      {
        "function": "string — IT function commonly outsourced",
        "frequency": "string — very_common | common | occasional",
        "typical_model": "string — MSSP | MSP | staff_augmentation | co-managed | BPO"
      }
    ],
    "typical_it_headcount_range": {
      "min": "number",
      "max": "number",
      "notes": "string"
    }
  },

  "typical_risks": [
    {
      "risk": "string — risk description",
      "frequency": "string — very_common | common | occasional",
      "typical_severity": "string — critical | high | medium | low",
      "typical_cost_impact": "string — display-ready cost range",
      "deal_relevance": "string — why this matters in a deal context"
    }
  ],

  "core_workflows": [
    {
      "workflow_id": "string — snake_case identifier",
      "name": "string — display name",
      "description": "string — what this workflow accomplishes",
      "steps": [
        {
          "step": "string — step name",
          "systems": ["string — system category references"],
          "manual_common": "boolean — true if this step is often manual",
          "manual_note": "string|null — context when manual_common is true"
        }
      ],
      "key_integrations": [
        {
          "from": "string — source system category",
          "to": "string — target system category",
          "type": "string — real_time | API | file | batch | manual",
          "criticality": "string — critical | high | medium"
        }
      ]
    }
  ],

  "deal_lens_considerations": {
    "growth": ["string — questions/considerations for growth-oriented deals"],
    "carve_out": ["string — questions/considerations for carve-out deals"],
    "platform_add_on": ["string — questions/considerations for add-on acquisitions"],
    "turnaround": ["string — questions/considerations for turnaround situations"]
  }
}
```

---

### Initial Template Set

Six template files covering the five priority industries plus a general fallback. Each is specified in full below.

---

#### Template 1: Insurance (P&C, Midmarket)

**File:** `data/industry_templates/insurance.json`

```json
{
  "template_id": "insurance_p_and_c_midmarket",
  "industry": "insurance",
  "sub_industry": "p_and_c",
  "size_tier": "midmarket",
  "version": "1.0",
  "last_updated": "2026-02",
  "provenance": "Compiled from Gartner IT Key Metrics 2025, Computer Economics IT Spending & Staffing Benchmarks 2024/2025, Novarica Insurance Technology Research, Productiv SaaS Benchmark Report 2024, industry vendor documentation, M&A integration experience",

  "expected_systems": {
    "industry_critical": [
      {
        "category": "policy_administration",
        "description": "Core policy lifecycle management — quoting, binding, issuing, endorsing, renewing. The system of record for all active and historical policies.",
        "common_vendors": ["Duck Creek", "Guidewire PolicyCenter", "Majesco", "Insurity", "OneShield"],
        "criticality": "critical",
        "typical_cost_range": "$500K-$2M/year",
        "migration_complexity": "high",
        "notes": "Heart of insurance operations. Migration typically 12-18 months. Heavy customization is the norm. Many midmarket carriers still run legacy mainframe-based systems."
      },
      {
        "category": "claims_management",
        "description": "First notice of loss through settlement — intake, assignment, investigation, reserves, payment, subrogation.",
        "common_vendors": ["Guidewire ClaimCenter", "Duck Creek Claims", "Majesco Claims", "Snapsheet", "CCC Intelligent Solutions"],
        "criticality": "critical",
        "typical_cost_range": "$400K-$1.5M/year",
        "migration_complexity": "high",
        "notes": "Claims is the primary cost driver in P&C. Integration with external data sources (weather, police reports, medical) is common."
      },
      {
        "category": "billing_system",
        "description": "Premium billing, payment processing, installment plans, agency bill vs. direct bill, commission accounting.",
        "common_vendors": ["Guidewire BillingCenter", "Duck Creek Billing", "Majesco Billing", "One Inc"],
        "criticality": "critical",
        "typical_cost_range": "$200K-$800K/year",
        "migration_complexity": "high",
        "notes": "Tightly coupled with policy admin. Agency bill vs. direct bill adds complexity. Must handle regulatory premium trust requirements."
      },
      {
        "category": "rating_engine",
        "description": "Actuarial rate calculation, product configuration, underwriting rules, territory and class code management.",
        "common_vendors": ["Guidewire Rating", "Duck Creek Rating", "Earnix", "Instec", "Majesco Rating"],
        "criticality": "critical",
        "typical_cost_range": "$150K-$600K/year",
        "migration_complexity": "high",
        "notes": "Competitive differentiator. Rate changes must be filed with state DOIs. Speed of rate-to-market is a key metric."
      }
    ],
    "industry_common": [
      {
        "category": "agency_portal",
        "description": "Agent-facing portal for quoting, policy servicing, commission inquiry, document download.",
        "common_vendors": ["Applied Epic", "Vertafore AMS360", "HawkSoft", "Custom portals"],
        "criticality": "high",
        "typical_cost_range": "$100K-$400K/year",
        "migration_complexity": "medium",
        "notes": "Critical for agent satisfaction and retention. IVANS/ACORD integration standard."
      },
      {
        "category": "reinsurance_management",
        "description": "Treaty and facultative reinsurance tracking, cession calculations, bordereau reporting.",
        "common_vendors": ["Sapiens ReinsuranceMaster", "RiskMeter", "Gen Re tools", "Spreadsheets (common at midmarket)"],
        "criticality": "high",
        "typical_cost_range": "$100K-$500K/year",
        "migration_complexity": "medium",
        "notes": "Often managed in spreadsheets at midmarket. Automated cession calculations reduce error risk."
      },
      {
        "category": "document_management",
        "description": "Policy document generation, correspondence, forms library, ACORD forms.",
        "common_vendors": ["Hyland OnBase", "Documentum", "Laserfiche", "OpenText", "Nuxeo"],
        "criticality": "high",
        "typical_cost_range": "$75K-$300K/year",
        "migration_complexity": "medium",
        "notes": "Stores policy declarations, endorsements, correspondence. Retention requirements vary by state."
      },
      {
        "category": "data_warehouse_analytics",
        "description": "Actuarial analytics, loss triangles, underwriting performance, regulatory reporting (statutory filings).",
        "common_vendors": ["Snowflake", "SQL Server", "Oracle", "SAS", "Tableau", "Power BI"],
        "criticality": "high",
        "typical_cost_range": "$100K-$500K/year",
        "migration_complexity": "medium",
        "notes": "Statutory reporting (NAIC) and actuarial analysis require clean, consistent data. Loss triangles are critical for reserving."
      },
      {
        "category": "regulatory_compliance",
        "description": "State filing tracking, market conduct, complaint management, DOI correspondence.",
        "common_vendors": ["SERFF (NAIC)", "RegEd", "Wolters Kluwer", "Custom tracking"],
        "criticality": "high",
        "typical_cost_range": "$50K-$200K/year",
        "migration_complexity": "low",
        "notes": "Must track rate/form filings across all operating states. Market conduct compliance is increasingly automated."
      }
    ],
    "general_enterprise": [
      {
        "category": "erp_gl",
        "description": "General ledger, accounts payable/receivable, financial reporting, statutory accounting (SAP/GAAP).",
        "common_vendors": ["NetSuite", "SAP", "Microsoft Dynamics", "Sage Intacct"],
        "criticality": "high",
        "typical_cost_range": "$100K-$500K/year",
        "migration_complexity": "medium",
        "notes": "Insurance requires statutory accounting (SAP basis) in addition to GAAP. Dual-basis reporting is common."
      },
      {
        "category": "email_collaboration",
        "description": "Email, calendaring, instant messaging, video conferencing, file sharing.",
        "common_vendors": ["Microsoft 365", "Google Workspace"],
        "criticality": "high",
        "typical_cost_range": "$50K-$200K/year",
        "migration_complexity": "low",
        "notes": "Standard enterprise capability. M365 dominant in insurance sector."
      },
      {
        "category": "identity_access_management",
        "description": "Single sign-on, multi-factor authentication, directory services, user provisioning.",
        "common_vendors": ["Microsoft Entra ID (Azure AD)", "Okta", "Ping Identity", "CyberArk"],
        "criticality": "high",
        "typical_cost_range": "$30K-$150K/year",
        "migration_complexity": "medium",
        "notes": "Foundation for security posture. MFA enforcement increasingly required by cyber insurers (ironic but true)."
      },
      {
        "category": "backup_disaster_recovery",
        "description": "Data backup, business continuity, disaster recovery, RTO/RPO management.",
        "common_vendors": ["Veeam", "Commvault", "Zerto", "Rubrik", "Datto"],
        "criticality": "high",
        "typical_cost_range": "$50K-$200K/year",
        "migration_complexity": "low",
        "notes": "Insurance regulators increasingly reviewing DR capabilities. State DOIs may require specific BCP documentation."
      },
      {
        "category": "crm",
        "description": "Agent/broker relationship management, pipeline tracking, renewal management.",
        "common_vendors": ["Salesforce", "Microsoft Dynamics 365", "HubSpot"],
        "criticality": "medium",
        "typical_cost_range": "$30K-$150K/year",
        "migration_complexity": "low",
        "notes": "Less common at midmarket P&C carriers. Agency management often handled by agency portal or policy admin."
      },
      {
        "category": "itsm_service_desk",
        "description": "IT service management, ticketing, asset management, change management.",
        "common_vendors": ["ServiceNow", "Jira Service Management", "Freshservice", "ManageEngine"],
        "criticality": "medium",
        "typical_cost_range": "$20K-$100K/year",
        "migration_complexity": "low",
        "notes": "Maturity varies widely at midmarket. May be informal or spreadsheet-based."
      },
      {
        "category": "endpoint_security",
        "description": "Endpoint detection and response, antivirus, device management.",
        "common_vendors": ["CrowdStrike", "SentinelOne", "Microsoft Defender", "Carbon Black"],
        "criticality": "high",
        "typical_cost_range": "$30K-$120K/year",
        "migration_complexity": "low",
        "notes": "Increasingly required by reinsurers and state regulators. NYDFS 500 sets the standard."
      }
    ]
  },

  "expected_metrics": {
    "it_pct_revenue": {
      "low": 3.0,
      "typical": 4.5,
      "high": 6.5,
      "unit": "%",
      "source": "Gartner IT Key Metrics Data 2025 — Insurance Vertical",
      "notes": "P&C typically higher than life due to claims processing intensity and regulatory filing requirements"
    },
    "it_staff_per_100_employees": {
      "low": 2.0,
      "typical": 3.5,
      "high": 5.5,
      "unit": "ratio",
      "source": "Gartner IT Key Metrics Data 2025 — Insurance",
      "notes": "Includes contractors and MSP FTE equivalent. Skews higher when policy admin is maintained in-house."
    },
    "app_count_per_100_employees": {
      "low": 10,
      "typical": 18,
      "high": 30,
      "unit": "count",
      "source": "Productiv SaaS Benchmark Report 2024 — Financial Services/Insurance",
      "notes": "SaaS plus on-prem combined. Insurers with legacy stacks trend lower; those adopting InsurTech point solutions trend higher."
    },
    "it_cost_per_employee": {
      "low": 8000,
      "typical": 14000,
      "high": 22000,
      "unit": "USD",
      "source": "Computer Economics IT Spending & Staffing Benchmarks 2024/2025 — Insurance",
      "notes": "Includes all IT operating expense divided by total headcount."
    },
    "security_pct_it_budget": {
      "low": 6,
      "typical": 10,
      "high": 15,
      "unit": "%",
      "source": "Gartner Security & Risk Management Survey 2024",
      "notes": "Insurance regulators (NYDFS 500, NAIC Model Law) driving increased security investment."
    },
    "cloud_adoption_pct": {
      "low": 25,
      "typical": 40,
      "high": 60,
      "unit": "%",
      "source": "Novarica Insurance Technology Research 2024",
      "notes": "Core systems (policy admin, claims) still predominantly on-prem or hosted. Cloud adoption higher for ancillary systems."
    },
    "outsourcing_pct": {
      "low": 15,
      "typical": 30,
      "high": 50,
      "unit": "%",
      "source": "ISG Outsourcing Index 2024 — Insurance",
      "notes": "Infrastructure management and application support commonly outsourced. Claims adjusting also often outsourced."
    },
    "tech_refresh_cycle_years": {
      "low": 3,
      "typical": 5,
      "high": 7,
      "unit": "years",
      "source": "Gartner Infrastructure & Operations Survey 2024",
      "notes": "Core insurance systems often on longer refresh cycles (7-10+ years) due to migration complexity."
    }
  },

  "expected_organization": {
    "typical_roles": [
      {"role": "CIO / VP of IT / IT Director", "category": "leadership", "typical_count": "1", "notes": "Single IT leader at midmarket. May report to CFO or COO."},
      {"role": "Infrastructure / Network Admin", "category": "infrastructure", "typical_count": "2-3", "notes": "Manages servers, network, cloud infrastructure. Often covers telecom."},
      {"role": "Application Support / Developer", "category": "applications", "typical_count": "2-4", "notes": "Often specialists in the policy admin system. May include vendor-provided staff."},
      {"role": "Security Analyst / CISO", "category": "security", "typical_count": "0-1", "notes": "Dedicated security role uncommon at midmarket. Often outsourced to MSSP or combined with infrastructure."},
      {"role": "Help Desk / Service Desk", "category": "service_desk", "typical_count": "1-3", "notes": "Tier 1 support. May be outsourced."},
      {"role": "DBA / Data Analyst", "category": "data", "typical_count": "1-2", "notes": "Supports actuarial reporting, data warehouse, statutory filings."},
      {"role": "Project Manager / BA", "category": "project_management", "typical_count": "0-1", "notes": "Often shared with business. Formal PMO rare at midmarket."}
    ],
    "typical_outsourcing": [
      {"function": "Security monitoring / SIEM", "frequency": "very_common", "typical_model": "MSSP"},
      {"function": "Infrastructure management", "frequency": "common", "typical_model": "MSP"},
      {"function": "Application development and maintenance", "frequency": "common", "typical_model": "staff_augmentation"},
      {"function": "Help desk / Tier 1 support", "frequency": "common", "typical_model": "MSP"},
      {"function": "Disaster recovery / BCP", "frequency": "occasional", "typical_model": "co-managed"},
      {"function": "Policy admin system support", "frequency": "common", "typical_model": "staff_augmentation"}
    ],
    "typical_it_headcount_range": {
      "min": 8,
      "max": 25,
      "notes": "For a 200-800 employee P&C insurer. Lower end relies heavily on MSP/outsourcing. Higher end maintains in-house policy admin expertise."
    }
  },

  "typical_risks": [
    {
      "risk": "Legacy policy administration system on mainframe or unsupported platform",
      "frequency": "very_common",
      "typical_severity": "high",
      "typical_cost_impact": "$1M-$5M to re-platform",
      "deal_relevance": "Directly impacts integration timeline and post-close capital requirements"
    },
    {
      "risk": "Single-vendor dependency for core insurance suite (policy/claims/billing)",
      "frequency": "very_common",
      "typical_severity": "medium",
      "typical_cost_impact": "$200K-$500K/year in vendor lock-in premium",
      "deal_relevance": "Limits negotiating leverage and constrains technology roadmap"
    },
    {
      "risk": "Manual reinsurance cession calculations using spreadsheets",
      "frequency": "common",
      "typical_severity": "medium",
      "typical_cost_impact": "$100K-$400K to automate",
      "deal_relevance": "Risk of cession errors impacting financial statements"
    },
    {
      "risk": "Inadequate cybersecurity controls relative to NYDFS 500 or NAIC Model Law",
      "frequency": "common",
      "typical_severity": "high",
      "typical_cost_impact": "$300K-$1M for remediation",
      "deal_relevance": "Regulatory exposure. May require immediate post-close investment."
    },
    {
      "risk": "Key person dependency on policy admin system knowledge",
      "frequency": "very_common",
      "typical_severity": "high",
      "typical_cost_impact": "$500K-$2M in transition risk",
      "deal_relevance": "Loss of key personnel post-close can halt system changes"
    },
    {
      "risk": "State regulatory filing systems not integrated with core systems",
      "frequency": "common",
      "typical_severity": "medium",
      "typical_cost_impact": "$50K-$200K to integrate",
      "deal_relevance": "Manual filing processes are error-prone and slow product launches"
    },
    {
      "risk": "No formal IT disaster recovery or business continuity plan",
      "frequency": "occasional",
      "typical_severity": "high",
      "typical_cost_impact": "$150K-$500K to establish",
      "deal_relevance": "Regulatory requirement in many states. Absence is a red flag for DOI examiners."
    }
  ],

  "core_workflows": [
    {
      "workflow_id": "policy_lifecycle",
      "name": "Policy Lifecycle",
      "description": "End-to-end policy management from initial quote through renewal or cancellation. The primary revenue-generating workflow for a P&C carrier.",
      "steps": [
        {"step": "Quote / Rate", "systems": ["rating_engine", "agency_portal"], "manual_common": false, "manual_note": null},
        {"step": "Underwrite", "systems": ["policy_administration", "rating_engine"], "manual_common": true, "manual_note": "Complex risks often require manual underwriter review"},
        {"step": "Bind", "systems": ["policy_administration"], "manual_common": false, "manual_note": null},
        {"step": "Issue", "systems": ["policy_administration", "document_management"], "manual_common": false, "manual_note": null},
        {"step": "Bill", "systems": ["billing_system", "erp_gl"], "manual_common": false, "manual_note": null},
        {"step": "Endorse", "systems": ["policy_administration", "rating_engine"], "manual_common": true, "manual_note": "Complex endorsements (address change with territory impact) often require manual re-rate"},
        {"step": "Renew", "systems": ["policy_administration", "rating_engine"], "manual_common": true, "manual_note": "Renewal underwriting review common for commercial lines"},
        {"step": "Cancel / Non-Renew", "systems": ["policy_administration", "billing_system"], "manual_common": false, "manual_note": null}
      ],
      "key_integrations": [
        {"from": "agency_portal", "to": "policy_administration", "type": "API", "criticality": "high"},
        {"from": "rating_engine", "to": "policy_administration", "type": "real_time", "criticality": "critical"},
        {"from": "policy_administration", "to": "billing_system", "type": "real_time", "criticality": "critical"},
        {"from": "billing_system", "to": "erp_gl", "type": "batch", "criticality": "high"},
        {"from": "policy_administration", "to": "reinsurance_management", "type": "batch", "criticality": "medium"},
        {"from": "policy_administration", "to": "document_management", "type": "API", "criticality": "high"}
      ]
    },
    {
      "workflow_id": "claims_processing",
      "name": "Claims Processing",
      "description": "From first notice of loss through investigation, reserving, settlement, and recovery. The primary cost driver for a P&C carrier.",
      "steps": [
        {"step": "First Notice of Loss (FNOL)", "systems": ["claims_management", "agency_portal"], "manual_common": false, "manual_note": null},
        {"step": "Triage / Assignment", "systems": ["claims_management"], "manual_common": true, "manual_note": "Complex claims require manual adjuster assignment based on expertise"},
        {"step": "Investigation", "systems": ["claims_management"], "manual_common": true, "manual_note": "Field investigation, recorded statements, police reports"},
        {"step": "Reserve Setting", "systems": ["claims_management"], "manual_common": true, "manual_note": "Initial and ongoing reserve adjustments typically require adjuster judgment"},
        {"step": "Settlement / Payment", "systems": ["claims_management", "billing_system", "erp_gl"], "manual_common": false, "manual_note": null},
        {"step": "Subrogation / Recovery", "systems": ["claims_management"], "manual_common": true, "manual_note": "Subrogation pursuit often manual, especially for smaller recoveries"}
      ],
      "key_integrations": [
        {"from": "claims_management", "to": "policy_administration", "type": "real_time", "criticality": "critical"},
        {"from": "claims_management", "to": "erp_gl", "type": "batch", "criticality": "high"},
        {"from": "claims_management", "to": "reinsurance_management", "type": "batch", "criticality": "medium"},
        {"from": "claims_management", "to": "document_management", "type": "API", "criticality": "high"}
      ]
    },
    {
      "workflow_id": "regulatory_reporting",
      "name": "Regulatory & Statutory Reporting",
      "description": "Preparation and filing of statutory financial statements, rate/form filings, and market conduct reports required by state DOIs and NAIC.",
      "steps": [
        {"step": "Data Extraction", "systems": ["data_warehouse_analytics", "erp_gl", "policy_administration"], "manual_common": true, "manual_note": "Data reconciliation between systems is often manual"},
        {"step": "Statutory Statement Preparation", "systems": ["erp_gl", "data_warehouse_analytics"], "manual_common": true, "manual_note": "SAP-basis adjustments often require manual entries"},
        {"step": "NAIC Filing", "systems": ["regulatory_compliance"], "manual_common": false, "manual_note": null},
        {"step": "Rate / Form Filing", "systems": ["regulatory_compliance"], "manual_common": true, "manual_note": "State-by-state filing via SERFF, often with manual review cycles"},
        {"step": "Market Conduct Response", "systems": ["regulatory_compliance", "policy_administration", "claims_management"], "manual_common": true, "manual_note": "Data requests from DOIs typically require manual data pulls"}
      ],
      "key_integrations": [
        {"from": "erp_gl", "to": "data_warehouse_analytics", "type": "batch", "criticality": "high"},
        {"from": "policy_administration", "to": "data_warehouse_analytics", "type": "batch", "criticality": "high"},
        {"from": "claims_management", "to": "data_warehouse_analytics", "type": "batch", "criticality": "high"}
      ]
    }
  ],

  "deal_lens_considerations": {
    "growth": [
      "Can the policy admin system handle 2-3x policy volume without re-platforming?",
      "Are APIs available for digital distribution partnerships and aggregator integrations?",
      "Is the rating engine flexible enough for new product lines and rapid state expansion?",
      "What is the current automation level in underwriting — can it scale without proportional headcount?",
      "How quickly can new states be added to the filing and compliance infrastructure?",
      "Is the data warehouse capable of supporting advanced analytics and predictive modeling?"
    ],
    "carve_out": [
      "Which systems are shared with the parent company (GL, identity, network, email)?",
      "What TSA duration is needed for shared infrastructure and support services?",
      "Are insurance licenses transferable or tied to the parent entity?",
      "Is policy data separable from the parent's data warehouse and reporting systems?",
      "How are reinsurance treaties structured — are they at the entity or group level?",
      "What vendor contracts require consent for assignment or have change-of-control provisions?",
      "Are there shared service desk, security, or infrastructure teams that need to be replicated?"
    ],
    "platform_add_on": [
      "How compatible is the target's policy admin with the acquirer's platform?",
      "Can agency management systems and portals be consolidated?",
      "Are there regulatory complications in combining insurance entities across states?",
      "What is the overlap in carrier appointments and agency relationships?",
      "Can claims handling be consolidated onto a single platform?",
      "How do the targets' actuarial data and loss history integrate with the acquirer's?"
    ],
    "turnaround": [
      "How much technical debt exists in the core policy admin system?",
      "Is claims processing still partially manual or paper-based?",
      "Are there compliance gaps that require immediate investment (NYDFS 500, state DOI findings)?",
      "What is the state of disaster recovery and business continuity?",
      "Are there key person dependencies that create operational risk?",
      "What is the combined ratio impact of manual processes and system inefficiencies?"
    ]
  }
}
```

---

#### Template 2: Healthcare (Provider, Midmarket)

**File:** `data/industry_templates/healthcare.json`

```json
{
  "template_id": "healthcare_provider_midmarket",
  "industry": "healthcare",
  "sub_industry": "provider",
  "size_tier": "midmarket",
  "version": "1.0",
  "last_updated": "2026-02",
  "provenance": "Compiled from HIMSS Healthcare IT Survey 2024, Gartner IT Key Metrics 2025 — Healthcare, Computer Economics IT Spending & Staffing Benchmarks 2024/2025, KLAS Research vendor ratings, CHIME Digital Health Most Wired Survey 2024",

  "expected_systems": {
    "industry_critical": [
      {
        "category": "ehr_emr",
        "description": "Electronic health record — clinical documentation, CPOE, clinical decision support, medication administration, patient chart. The system of record for all clinical activity.",
        "common_vendors": ["Epic", "Oracle Health (Cerner)", "MEDITECH", "athenahealth", "eClinicalWorks", "NextGen"],
        "criticality": "critical",
        "typical_cost_range": "$1M-$10M+ implementation; $500K-$3M/year ongoing",
        "migration_complexity": "high",
        "notes": "EHR is the defining technology decision for a healthcare provider. Epic and Oracle Health dominate at midmarket+. Migration is a multi-year, organization-wide effort. Heavily customized builds are the norm."
      },
      {
        "category": "revenue_cycle_management",
        "description": "Patient registration, charge capture, coding, claims submission, denial management, collections, payment posting.",
        "common_vendors": ["Epic (integrated)", "Oracle Health (integrated)", "Waystar", "R1 RCM", "Availity", "Change Healthcare", "nThrive"],
        "criticality": "critical",
        "typical_cost_range": "$300K-$2M/year",
        "migration_complexity": "high",
        "notes": "Revenue cycle directly impacts cash flow. Many organizations outsource portions of RCM. Coding accuracy and denial management are key performance drivers."
      },
      {
        "category": "practice_management",
        "description": "Patient scheduling, registration, referral management, front-office workflows, insurance verification.",
        "common_vendors": ["Epic (integrated)", "athenahealth", "AdvancedMD", "Kareo", "eClinicalWorks"],
        "criticality": "critical",
        "typical_cost_range": "$100K-$500K/year",
        "migration_complexity": "medium",
        "notes": "Often integrated with EHR at midmarket. Standalone practice management indicates an older or fragmented stack."
      },
      {
        "category": "pharmacy_system",
        "description": "Medication ordering, dispensing, inventory management, drug interaction checking, controlled substance tracking.",
        "common_vendors": ["Epic Willow", "Omnicell", "BD Pyxis", "ScriptPro", "QS/1"],
        "criticality": "critical",
        "typical_cost_range": "$200K-$1M/year",
        "migration_complexity": "high",
        "notes": "Includes automated dispensing cabinets (ADCs) in inpatient settings. EPCS (electronic prescribing of controlled substances) is increasingly mandated."
      }
    ],
    "industry_common": [
      {
        "category": "pacs_imaging",
        "description": "Medical image storage, viewing, and distribution. Vendor-neutral archive (VNA) for long-term image management.",
        "common_vendors": ["GE Healthcare", "Philips", "Fujifilm Synapse", "Agfa", "Change Healthcare Radiology"],
        "criticality": "high",
        "typical_cost_range": "$200K-$1M/year",
        "migration_complexity": "high",
        "notes": "Image data volumes are massive. VNA adoption increasing for vendor independence. DICOM standards enable interoperability."
      },
      {
        "category": "lab_information_system",
        "description": "Laboratory order management, specimen tracking, result reporting, instrument interfacing.",
        "common_vendors": ["Epic Beaker", "Cerner PathNet", "Sunquest", "Orchard Harvest"],
        "criticality": "high",
        "typical_cost_range": "$150K-$800K/year",
        "migration_complexity": "high",
        "notes": "Critical if organization operates in-house lab. HL7/FHIR interfaces to EHR for result delivery."
      },
      {
        "category": "patient_portal",
        "description": "Patient-facing access to health records, messaging with providers, appointment scheduling, bill pay, lab results.",
        "common_vendors": ["MyChart (Epic)", "Oracle Health Patient Portal", "athenaPatient", "Healow"],
        "criticality": "high",
        "typical_cost_range": "$50K-$300K/year",
        "migration_complexity": "low",
        "notes": "21st Century Cures Act requires information access. Patient adoption is a key metric. Interoperability requirements increasing."
      },
      {
        "category": "telehealth",
        "description": "Video visit platform, virtual care workflows, remote patient monitoring integration.",
        "common_vendors": ["Epic Video Visit", "Teladoc", "Amwell", "Doxy.me", "Zoom for Healthcare"],
        "criticality": "medium",
        "typical_cost_range": "$50K-$250K/year",
        "migration_complexity": "low",
        "notes": "Post-COVID standard capability. EHR integration critical for documentation and billing. State licensing requirements vary."
      },
      {
        "category": "clinical_communication",
        "description": "Secure messaging between clinical staff, nurse call integration, critical alerts, on-call scheduling.",
        "common_vendors": ["TigerConnect", "Vocera (Stryker)", "PerfectServe", "Spok"],
        "criticality": "high",
        "typical_cost_range": "$50K-$200K/year",
        "migration_complexity": "low",
        "notes": "HIPAA-compliant messaging required. Replaces pagers in many settings."
      },
      {
        "category": "health_information_exchange",
        "description": "Interoperability with external providers, HIEs, payers — ADT notifications, clinical document exchange.",
        "common_vendors": ["CommonWell", "Carequality", "Epic Care Everywhere", "Rhapsody", "Mirth Connect"],
        "criticality": "medium",
        "typical_cost_range": "$50K-$200K/year",
        "migration_complexity": "medium",
        "notes": "CMS interoperability rules require participation. TEFCA framework emerging. FHIR-based exchange growing."
      }
    ],
    "general_enterprise": [
      {
        "category": "erp_gl",
        "description": "General ledger, AP/AR, supply chain, materials management, financial reporting.",
        "common_vendors": ["Infor CloudSuite Healthcare", "Workday", "Oracle Cloud", "SAP", "PeopleSoft"],
        "criticality": "high",
        "typical_cost_range": "$200K-$800K/year",
        "migration_complexity": "medium",
        "notes": "Supply chain/materials management critical for inpatient settings. GPO integration common."
      },
      {
        "category": "hcm_payroll",
        "description": "Human capital management, payroll, time and attendance, credentialing, scheduling.",
        "common_vendors": ["Workday", "UKG", "ADP", "Kronos", "Infor"],
        "criticality": "high",
        "typical_cost_range": "$100K-$500K/year",
        "migration_complexity": "medium",
        "notes": "Healthcare workforce management is complex — shift scheduling, credential tracking, overtime management for nurses/providers."
      },
      {
        "category": "email_collaboration",
        "description": "Email, calendaring, video conferencing, file sharing.",
        "common_vendors": ["Microsoft 365", "Google Workspace"],
        "criticality": "high",
        "typical_cost_range": "$50K-$300K/year",
        "migration_complexity": "low",
        "notes": "Must be configured for HIPAA compliance (BAA with vendor, encryption, DLP). M365 dominant."
      },
      {
        "category": "identity_access_management",
        "description": "SSO, MFA, directory services, role-based access control for clinical and administrative systems.",
        "common_vendors": ["Microsoft Entra ID", "Okta", "Imprivata (clinical SSO)", "CyberArk"],
        "criticality": "high",
        "typical_cost_range": "$50K-$250K/year",
        "migration_complexity": "medium",
        "notes": "Imprivata tap-and-go common in clinical settings for rapid workstation access. PHI access auditing is a HIPAA requirement."
      },
      {
        "category": "endpoint_security",
        "description": "EDR, antivirus, medical device security, device management.",
        "common_vendors": ["CrowdStrike", "SentinelOne", "Microsoft Defender", "Medigate (medical device)"],
        "criticality": "high",
        "typical_cost_range": "$50K-$200K/year",
        "migration_complexity": "low",
        "notes": "Medical device security is a unique challenge. FDA guidance on medical device cybersecurity applies."
      },
      {
        "category": "backup_disaster_recovery",
        "description": "Clinical and administrative data backup, business continuity, disaster recovery.",
        "common_vendors": ["Veeam", "Commvault", "Zerto", "Rubrik"],
        "criticality": "high",
        "typical_cost_range": "$75K-$300K/year",
        "migration_complexity": "low",
        "notes": "Clinical system downtime directly impacts patient care. RTOs of hours (not days) expected for EHR."
      }
    ]
  },

  "expected_metrics": {
    "it_pct_revenue": {
      "low": 3.0,
      "typical": 4.5,
      "high": 6.0,
      "unit": "%",
      "source": "HIMSS Healthcare IT Survey 2024; Gartner IT Key Metrics 2025 — Healthcare",
      "notes": "Revenue in healthcare is net patient revenue. IT spending varies significantly based on whether EHR is hosted or on-prem."
    },
    "it_staff_per_100_employees": {
      "low": 2.5,
      "typical": 4.0,
      "high": 6.0,
      "unit": "ratio",
      "source": "CHIME Digital Health Most Wired Survey 2024; Gartner IT Key Metrics 2025",
      "notes": "Includes clinical informatics staff. Organizations with Epic/Cerner in-house tend toward higher ratios."
    },
    "app_count_per_100_employees": {
      "low": 12,
      "typical": 22,
      "high": 35,
      "unit": "count",
      "source": "Productiv SaaS Benchmark Report 2024 — Healthcare",
      "notes": "Healthcare has high app counts due to clinical specialization. Medical device software adds to the count."
    },
    "it_cost_per_employee": {
      "low": 8000,
      "typical": 12000,
      "high": 18000,
      "unit": "USD",
      "source": "Computer Economics IT Spending & Staffing Benchmarks 2024/2025 — Healthcare",
      "notes": "Per total employee including clinical staff. Cost per clinical FTE is significantly higher."
    },
    "security_pct_it_budget": {
      "low": 5,
      "typical": 8,
      "high": 14,
      "unit": "%",
      "source": "HIMSS Cybersecurity Survey 2024",
      "notes": "Healthcare is the most targeted sector for ransomware. Investment trending upward but still below financial services."
    },
    "cloud_adoption_pct": {
      "low": 20,
      "typical": 35,
      "high": 55,
      "unit": "%",
      "source": "HIMSS Cloud Study 2024; Flexera State of the Cloud Report 2024",
      "notes": "EHR cloud hosting growing but most midmarket providers still run on-prem or hosted. Cloud adoption higher for ancillary systems."
    },
    "outsourcing_pct": {
      "low": 10,
      "typical": 25,
      "high": 45,
      "unit": "%",
      "source": "ISG Outsourcing Index 2024 — Healthcare",
      "notes": "Revenue cycle management commonly outsourced. IT infrastructure management growing as outsourced function."
    },
    "tech_refresh_cycle_years": {
      "low": 3,
      "typical": 5,
      "high": 7,
      "unit": "years",
      "source": "Gartner Infrastructure & Operations Survey 2024",
      "notes": "Medical devices have their own lifecycle (often 7-10 years). Clinical workstation refresh is typically 4-5 years."
    }
  },

  "expected_organization": {
    "typical_roles": [
      {"role": "CIO / VP of IT", "category": "leadership", "typical_count": "1", "notes": "May also have a CMIO (Chief Medical Information Officer) for clinical systems."},
      {"role": "CISO / Security Director", "category": "security", "typical_count": "0-1", "notes": "HIPAA requires a designated security officer. May be combined with compliance role at midmarket."},
      {"role": "Clinical Informatics / EHR Analyst", "category": "applications", "typical_count": "3-6", "notes": "Build, configuration, and optimization of EHR workflows. Often the largest team."},
      {"role": "Infrastructure / Network Engineer", "category": "infrastructure", "typical_count": "2-4", "notes": "Includes wireless network management critical for clinical mobility."},
      {"role": "Help Desk / Desktop Support", "category": "service_desk", "typical_count": "2-4", "notes": "Must support clinical workflows. Often includes biomedical device support."},
      {"role": "Interface / Integration Analyst", "category": "applications", "typical_count": "1-2", "notes": "Manages HL7, FHIR, and other clinical interfaces. Critical for interoperability."},
      {"role": "DBA / Report Writer", "category": "data", "typical_count": "1-2", "notes": "Clinical reporting, quality metrics, CMS reporting."},
      {"role": "IT Project Manager", "category": "project_management", "typical_count": "0-1", "notes": "Often involved in clinical workflow optimization projects."}
    ],
    "typical_outsourcing": [
      {"function": "Revenue cycle management (coding, billing, collections)", "frequency": "very_common", "typical_model": "BPO"},
      {"function": "Security monitoring / SIEM / SOC", "frequency": "very_common", "typical_model": "MSSP"},
      {"function": "Infrastructure management (server, network)", "frequency": "common", "typical_model": "MSP"},
      {"function": "EHR hosting", "frequency": "common", "typical_model": "vendor_hosted"},
      {"function": "Help desk / Tier 1 support", "frequency": "occasional", "typical_model": "MSP"},
      {"function": "Medical device management (biomed)", "frequency": "occasional", "typical_model": "co-managed"}
    ],
    "typical_it_headcount_range": {
      "min": 12,
      "max": 35,
      "notes": "For a 300-1000 employee healthcare provider. Clinical informatics staff drives higher IT headcount relative to other industries."
    }
  },

  "typical_risks": [
    {
      "risk": "EHR system on legacy or end-of-support version requiring major upgrade or replacement",
      "frequency": "common",
      "typical_severity": "critical",
      "typical_cost_impact": "$2M-$15M+ for replacement; $500K-$3M for major upgrade",
      "deal_relevance": "Largest single IT investment decision. Directly impacts clinical operations and revenue cycle."
    },
    {
      "risk": "HIPAA compliance gaps — incomplete risk assessment, missing BAAs, inadequate PHI safeguards",
      "frequency": "common",
      "typical_severity": "high",
      "typical_cost_impact": "$200K-$1M for remediation; $1M-$10M+ breach exposure",
      "deal_relevance": "Regulatory liability transfers with the acquisition. OCR enforcement is active."
    },
    {
      "risk": "Fragmented clinical systems — multiple EHRs or standalone practice management across sites",
      "frequency": "common",
      "typical_severity": "high",
      "typical_cost_impact": "$1M-$5M to consolidate",
      "deal_relevance": "Integration complexity increases with each disparate system. Clinical workflow disruption risk."
    },
    {
      "risk": "Ransomware / cybersecurity vulnerability in clinical environment",
      "frequency": "very_common",
      "typical_severity": "critical",
      "typical_cost_impact": "$1M-$10M+ including downtime, recovery, breach notification",
      "deal_relevance": "Healthcare is the top ransomware target. Downtime means diverted patients and revenue loss."
    },
    {
      "risk": "Medical device security — unpatched devices on clinical network",
      "frequency": "common",
      "typical_severity": "high",
      "typical_cost_impact": "$200K-$800K for segmentation and monitoring",
      "deal_relevance": "IoMT devices often run legacy OS. Network segmentation is the primary mitigation."
    },
    {
      "risk": "Key person dependency on EHR build team or interface analysts",
      "frequency": "very_common",
      "typical_severity": "high",
      "typical_cost_impact": "$300K-$1M in transition risk",
      "deal_relevance": "EHR tribal knowledge is difficult to replace. Competitive market for Epic/Cerner analysts."
    }
  ],

  "core_workflows": [
    {
      "workflow_id": "patient_encounter",
      "name": "Patient Encounter (Ambulatory)",
      "description": "End-to-end patient visit from scheduling through documentation and billing. The primary clinical and revenue workflow for ambulatory providers.",
      "steps": [
        {"step": "Schedule", "systems": ["practice_management", "patient_portal"], "manual_common": false, "manual_note": null},
        {"step": "Register / Verify Insurance", "systems": ["practice_management", "revenue_cycle_management"], "manual_common": true, "manual_note": "Insurance verification may be manual for complex payer scenarios"},
        {"step": "Clinical Intake (Vitals, HPI)", "systems": ["ehr_emr"], "manual_common": false, "manual_note": null},
        {"step": "Provider Encounter / Documentation", "systems": ["ehr_emr"], "manual_common": false, "manual_note": null},
        {"step": "Order Entry (Labs, Imaging, Rx)", "systems": ["ehr_emr", "lab_information_system", "pacs_imaging", "pharmacy_system"], "manual_common": false, "manual_note": null},
        {"step": "Charge Capture / Coding", "systems": ["revenue_cycle_management", "ehr_emr"], "manual_common": true, "manual_note": "Professional fee coding often requires human coder review for complex visits"},
        {"step": "Claims Submission", "systems": ["revenue_cycle_management"], "manual_common": false, "manual_note": null},
        {"step": "Payment Posting / Denial Follow-up", "systems": ["revenue_cycle_management"], "manual_common": true, "manual_note": "Denial management is heavily manual"}
      ],
      "key_integrations": [
        {"from": "ehr_emr", "to": "revenue_cycle_management", "type": "real_time", "criticality": "critical"},
        {"from": "ehr_emr", "to": "lab_information_system", "type": "API", "criticality": "high"},
        {"from": "ehr_emr", "to": "pacs_imaging", "type": "API", "criticality": "high"},
        {"from": "ehr_emr", "to": "pharmacy_system", "type": "real_time", "criticality": "critical"},
        {"from": "practice_management", "to": "ehr_emr", "type": "real_time", "criticality": "critical"},
        {"from": "revenue_cycle_management", "to": "erp_gl", "type": "batch", "criticality": "high"}
      ]
    },
    {
      "workflow_id": "clinical_orders",
      "name": "Clinical Order Fulfillment",
      "description": "Lab, imaging, and pharmacy order workflows from order entry through result delivery to ordering provider.",
      "steps": [
        {"step": "Order Entry (CPOE)", "systems": ["ehr_emr"], "manual_common": false, "manual_note": null},
        {"step": "Order Routing / Transmission", "systems": ["ehr_emr", "lab_information_system", "pacs_imaging"], "manual_common": false, "manual_note": null},
        {"step": "Specimen Collection / Image Acquisition", "systems": ["lab_information_system", "pacs_imaging"], "manual_common": true, "manual_note": "Physical specimen handling and patient positioning"},
        {"step": "Processing / Analysis", "systems": ["lab_information_system", "pacs_imaging"], "manual_common": false, "manual_note": null},
        {"step": "Result / Report Delivery", "systems": ["ehr_emr", "patient_portal"], "manual_common": false, "manual_note": null},
        {"step": "Provider Review / Sign-off", "systems": ["ehr_emr"], "manual_common": true, "manual_note": "Provider must review and acknowledge critical results"}
      ],
      "key_integrations": [
        {"from": "ehr_emr", "to": "lab_information_system", "type": "real_time", "criticality": "critical"},
        {"from": "ehr_emr", "to": "pacs_imaging", "type": "API", "criticality": "high"},
        {"from": "lab_information_system", "to": "ehr_emr", "type": "real_time", "criticality": "critical"},
        {"from": "pacs_imaging", "to": "ehr_emr", "type": "API", "criticality": "high"}
      ]
    },
    {
      "workflow_id": "compliance_reporting",
      "name": "HIPAA & Quality Reporting",
      "description": "Ongoing compliance activities including HIPAA risk assessments, quality measure reporting (CMS), and breach management.",
      "steps": [
        {"step": "HIPAA Risk Assessment", "systems": ["identity_access_management", "endpoint_security"], "manual_common": true, "manual_note": "Typically annual, often consultant-assisted"},
        {"step": "PHI Access Audit", "systems": ["ehr_emr", "identity_access_management"], "manual_common": true, "manual_note": "Proactive audit log review for inappropriate access"},
        {"step": "Quality Measure Extraction (MIPS/MACRA)", "systems": ["ehr_emr", "data_warehouse_analytics"], "manual_common": true, "manual_note": "Clinical quality measures often require manual chart abstraction"},
        {"step": "CMS Submission", "systems": ["ehr_emr"], "manual_common": false, "manual_note": null}
      ],
      "key_integrations": [
        {"from": "ehr_emr", "to": "health_information_exchange", "type": "API", "criticality": "medium"},
        {"from": "ehr_emr", "to": "identity_access_management", "type": "batch", "criticality": "high"}
      ]
    }
  ],

  "deal_lens_considerations": {
    "growth": [
      "Can the EHR platform support additional locations and providers without re-platforming?",
      "Is the revenue cycle management function scalable (in-house capacity or outsourced model)?",
      "What is the telehealth platform maturity and capacity for virtual care expansion?",
      "Are FHIR APIs available for payer integrations and value-based care data sharing?",
      "Can the scheduling system support patient access expansion (online booking, same-day)?",
      "Is the data warehouse capable of population health analytics for value-based contracts?"
    ],
    "carve_out": [
      "Is the EHR instance shared with the parent health system or standalone?",
      "What TSA duration is needed for shared clinical systems and IT infrastructure?",
      "How is PHI separated between parent and carved-out entity?",
      "Are there shared master patient index or enterprise identity systems?",
      "Which BAAs are at the parent level and need to be novated?",
      "Are provider credentials and payer enrollments tied to the parent entity?",
      "Is there shared HIE connectivity that needs to be re-established?"
    ],
    "platform_add_on": [
      "Is the target on the same EHR platform as the acquirer?",
      "If different EHRs, what is the migration timeline and cost to consolidate?",
      "Can revenue cycle management be consolidated onto a single platform?",
      "How compatible are the clinical workflows between organizations?",
      "What is the overlap in payer contracts and credentialing?",
      "Can a shared patient portal be deployed across both organizations?"
    ],
    "turnaround": [
      "Is the EHR system current or facing end-of-life / unsupported version?",
      "What is the HIPAA compliance posture — when was the last risk assessment?",
      "Are there outstanding compliance findings from CMS, OCR, or state regulators?",
      "What is the cybersecurity posture — has there been a recent penetration test?",
      "Is revenue cycle performance below benchmark (days in AR, denial rate)?",
      "What is the state of clinical documentation — does it support accurate coding?"
    ]
  }
}
```

---

#### Template 3: Financial Services (Banking / Asset Management, Midmarket)

**File:** `data/industry_templates/financial_services.json`

```json
{
  "template_id": "financial_services_banking_midmarket",
  "industry": "financial_services",
  "sub_industry": "banking_asset_mgmt",
  "size_tier": "midmarket",
  "version": "1.0",
  "last_updated": "2026-02",
  "provenance": "Compiled from Deloitte Financial Services IT Survey 2024, Gartner IT Key Metrics 2025 — Banking & Securities, Computer Economics IT Spending & Staffing Benchmarks 2024/2025, Celent/Aite-Novarica vendor research, FFIEC guidance",

  "expected_systems": {
    "industry_critical": [
      {
        "category": "core_banking",
        "description": "Core banking platform — deposit accounts, general ledger, customer information file (CIF), account processing, interest calculation.",
        "common_vendors": ["FIS (Horizon, IBS, Profile)", "Fiserv (DNA, Signature, Premier)", "Jack Henry (SilverLake, CIF 20/20, Core Director)", "Temenos T24", "Finastra (Fusion)", "nCino"],
        "criticality": "critical",
        "typical_cost_range": "$500K-$3M/year",
        "migration_complexity": "high",
        "notes": "Core banking conversion is the highest-risk IT project in financial services. Typically 18-36 months. Midmarket banks are heavily dependent on one of the big three (FIS, Fiserv, Jack Henry)."
      },
      {
        "category": "loan_origination",
        "description": "Loan application intake, underwriting, credit decisioning, document preparation, closing.",
        "common_vendors": ["Encompass (ICE Mortgage Technology)", "Blend", "nCino", "Finastra", "MeridianLink", "Abrigo"],
        "criticality": "critical",
        "typical_cost_range": "$200K-$1M/year",
        "migration_complexity": "high",
        "notes": "Commercial and consumer lending may use different systems. Regulatory compliance (TRID, HMDA, fair lending) is embedded in the workflow."
      },
      {
        "category": "digital_banking",
        "description": "Online and mobile banking platform for consumer and business customers — account access, transfers, bill pay, mobile deposit.",
        "common_vendors": ["Q2", "Alkami", "NCR Digital Banking", "Fiserv Digital", "Jack Henry Banno"],
        "criticality": "critical",
        "typical_cost_range": "$200K-$800K/year",
        "migration_complexity": "medium",
        "notes": "Customer experience differentiator. Mobile banking adoption rate is a key competitive metric. API integration with core is critical."
      },
      {
        "category": "aml_bsa_compliance",
        "description": "Anti-money laundering transaction monitoring, Know Your Customer (KYC), Customer Due Diligence (CDD), Suspicious Activity Report (SAR) filing.",
        "common_vendors": ["Verafin (Nasdaq)", "Actimize (NICE)", "SAS AML", "Oracle FCCM", "Abrigo BAM+"],
        "criticality": "critical",
        "typical_cost_range": "$150K-$800K/year",
        "migration_complexity": "medium",
        "notes": "BSA/AML deficiencies are the most common source of regulatory enforcement actions. System must be tuned to minimize false positives while meeting regulatory expectations."
      }
    ],
    "industry_common": [
      {
        "category": "loan_servicing",
        "description": "Payment processing, escrow management, collections, default management, investor reporting.",
        "common_vendors": ["Black Knight MSP", "Sagent", "FICS", "Often within core banking"],
        "criticality": "high",
        "typical_cost_range": "$150K-$600K/year",
        "migration_complexity": "high",
        "notes": "In-house servicing vs. subservicing is a strategic decision. Servicing data conversion is complex and audit-sensitive."
      },
      {
        "category": "treasury_cash_management",
        "description": "Cash positioning, liquidity management, wholesale/business customer cash management services.",
        "common_vendors": ["Kyriba", "GTreasury", "FIS", "Fiserv", "Jack Henry Treasury"],
        "criticality": "high",
        "typical_cost_range": "$100K-$500K/year",
        "migration_complexity": "medium",
        "notes": "Business banking differentiator. ACH, wire, and positive pay capabilities are revenue drivers."
      },
      {
        "category": "card_management",
        "description": "Debit and credit card issuance, transaction processing, rewards, dispute management.",
        "common_vendors": ["FIS", "Fiserv", "Jack Henry", "Marqeta", "i2c"],
        "criticality": "high",
        "typical_cost_range": "$100K-$500K/year",
        "migration_complexity": "medium",
        "notes": "Interchange revenue is significant. Card processing often tied to core banking vendor ecosystem."
      },
      {
        "category": "regulatory_reporting",
        "description": "Call reports, HMDA, CRA, stress testing, Federal Reserve reporting.",
        "common_vendors": ["Axiom (Wolters Kluwer)", "Workiva", "AxiomSL", "Abrigo"],
        "criticality": "high",
        "typical_cost_range": "$100K-$400K/year",
        "migration_complexity": "medium",
        "notes": "Automation level varies widely. Manual call report preparation is a significant risk area."
      },
      {
        "category": "portfolio_management",
        "description": "Investment portfolio management, trading, performance attribution, client reporting.",
        "common_vendors": ["SS&C Advent", "Charles River (State Street)", "Bloomberg AIM", "Black Diamond", "Orion"],
        "criticality": "high",
        "typical_cost_range": "$200K-$1M/year",
        "migration_complexity": "high",
        "notes": "Applicable to wealth management and asset management arms. Client reporting is a key differentiator."
      },
      {
        "category": "document_management",
        "description": "Loan documents, account documents, correspondence, regulatory filings, imaging.",
        "common_vendors": ["Hyland OnBase", "Laserfiche", "OpenText", "nCino (integrated)"],
        "criticality": "medium",
        "typical_cost_range": "$75K-$300K/year",
        "migration_complexity": "medium",
        "notes": "Retention requirements are extensive (7+ years for many document types). Imaging/OCR for check and document processing."
      }
    ],
    "general_enterprise": [
      {
        "category": "erp_gl",
        "description": "General ledger, financial reporting, AP/AR, fixed assets.",
        "common_vendors": ["Oracle", "SAP", "Microsoft Dynamics", "Sage Intacct", "Often within core banking GL"],
        "criticality": "high",
        "typical_cost_range": "$100K-$500K/year",
        "migration_complexity": "medium",
        "notes": "Many midmarket banks use the core banking GL module rather than a separate ERP. SOX compliance drives GL controls."
      },
      {
        "category": "email_collaboration",
        "description": "Email, calendaring, video conferencing, file sharing with encryption and compliance archiving.",
        "common_vendors": ["Microsoft 365", "Google Workspace"],
        "criticality": "high",
        "typical_cost_range": "$50K-$250K/year",
        "migration_complexity": "low",
        "notes": "Email archiving required for regulatory compliance. DLP for sensitive financial data. M365 dominant."
      },
      {
        "category": "identity_access_management",
        "description": "SSO, MFA, directory services, privileged access management, segregation of duties enforcement.",
        "common_vendors": ["Microsoft Entra ID", "Okta", "CyberArk", "SailPoint"],
        "criticality": "high",
        "typical_cost_range": "$50K-$250K/year",
        "migration_complexity": "medium",
        "notes": "Segregation of duties is a SOX and regulatory requirement. Privileged access management is critical for core banking and treasury systems."
      },
      {
        "category": "endpoint_security",
        "description": "EDR, antivirus, device management, data loss prevention.",
        "common_vendors": ["CrowdStrike", "SentinelOne", "Microsoft Defender", "Carbon Black"],
        "criticality": "high",
        "typical_cost_range": "$40K-$180K/year",
        "migration_complexity": "low",
        "notes": "FFIEC cybersecurity expectations are high. DLP controls required for customer financial data."
      },
      {
        "category": "backup_disaster_recovery",
        "description": "Data backup, business continuity, disaster recovery. Regulators expect tested BCP/DR.",
        "common_vendors": ["Veeam", "Commvault", "Zerto", "Rubrik"],
        "criticality": "high",
        "typical_cost_range": "$75K-$300K/year",
        "migration_complexity": "low",
        "notes": "FFIEC requires annual BCP testing. Core banking RTO typically 4-8 hours. Regulators review DR documentation."
      },
      {
        "category": "itsm_service_desk",
        "description": "IT service management, ticketing, change management, asset management.",
        "common_vendors": ["ServiceNow", "Jira Service Management", "Freshservice"],
        "criticality": "medium",
        "typical_cost_range": "$20K-$100K/year",
        "migration_complexity": "low",
        "notes": "Change management process maturity is important for SOX and regulatory compliance."
      }
    ]
  },

  "expected_metrics": {
    "it_pct_revenue": {
      "low": 5.0,
      "typical": 7.5,
      "high": 10.0,
      "unit": "%",
      "source": "Deloitte Financial Services IT Survey 2024; Gartner IT Key Metrics 2025 — Banking",
      "notes": "Financial services is among the highest IT spending industries. Regulatory compliance and digital transformation are primary drivers."
    },
    "it_staff_per_100_employees": {
      "low": 4.0,
      "typical": 6.0,
      "high": 9.0,
      "unit": "ratio",
      "source": "Gartner IT Key Metrics 2025 — Financial Services",
      "notes": "Higher than most industries due to regulatory requirements and system complexity. Includes compliance and infosec staff."
    },
    "app_count_per_100_employees": {
      "low": 15,
      "typical": 25,
      "high": 40,
      "unit": "count",
      "source": "Productiv SaaS Benchmark Report 2024 — Financial Services",
      "notes": "High app counts due to regulatory, compliance, and risk management tools layered on top of core banking."
    },
    "it_cost_per_employee": {
      "low": 15000,
      "typical": 22000,
      "high": 30000,
      "unit": "USD",
      "source": "Computer Economics IT Spending & Staffing Benchmarks 2024/2025 — Financial Services",
      "notes": "Highest IT cost per employee of any industry. Driven by trading systems, compliance tools, and cybersecurity."
    },
    "security_pct_it_budget": {
      "low": 8,
      "typical": 13,
      "high": 18,
      "unit": "%",
      "source": "Deloitte Financial Services IT Survey 2024; Gartner Security Survey 2024",
      "notes": "FFIEC cybersecurity expectations and regulatory pressure drive highest security investment among industries."
    },
    "cloud_adoption_pct": {
      "low": 20,
      "typical": 35,
      "high": 55,
      "unit": "%",
      "source": "Flexera State of the Cloud Report 2024; Deloitte FS Cloud Study 2024",
      "notes": "Core banking still predominantly on-prem or vendor-hosted. Cloud adoption accelerating for digital banking and analytics."
    },
    "outsourcing_pct": {
      "low": 15,
      "typical": 30,
      "high": 50,
      "unit": "%",
      "source": "ISG Outsourcing Index 2024 — Financial Services",
      "notes": "Core banking operations rarely outsourced. Infrastructure, security monitoring, and application development commonly outsourced."
    },
    "tech_refresh_cycle_years": {
      "low": 3,
      "typical": 5,
      "high": 7,
      "unit": "years",
      "source": "Gartner Infrastructure & Operations Survey 2024",
      "notes": "Core banking systems may run 10-20+ years. Endpoint and infrastructure on standard 4-5 year cycles."
    }
  },

  "expected_organization": {
    "typical_roles": [
      {"role": "CIO / VP of IT", "category": "leadership", "typical_count": "1", "notes": "Often reports to CEO or COO. May have a CTO for digital banking initiatives."},
      {"role": "CISO / Information Security Officer", "category": "security", "typical_count": "1", "notes": "FFIEC and GLBA require a designated ISO. Dedicated role standard even at midmarket."},
      {"role": "Core Banking / Application Support", "category": "applications", "typical_count": "2-4", "notes": "Specialists in the core banking platform. Often vendor-certified."},
      {"role": "Infrastructure / Network Engineer", "category": "infrastructure", "typical_count": "2-4", "notes": "Branch connectivity, ATM network, data center management."},
      {"role": "Database / Reporting Analyst", "category": "data", "typical_count": "1-3", "notes": "Regulatory reporting, data warehouse, analytics. Call report preparation."},
      {"role": "Help Desk / Service Desk", "category": "service_desk", "typical_count": "2-4", "notes": "Supports branch and corporate staff. May include ATM support."},
      {"role": "IT Audit / Compliance Analyst", "category": "security", "typical_count": "0-2", "notes": "SOX controls, audit coordination, vendor risk management. May be shared with compliance department."},
      {"role": "Project Manager", "category": "project_management", "typical_count": "0-1", "notes": "Often involved in regulatory projects and digital banking initiatives."}
    ],
    "typical_outsourcing": [
      {"function": "Security monitoring / SOC / SIEM", "frequency": "very_common", "typical_model": "MSSP"},
      {"function": "Core banking hosting", "frequency": "very_common", "typical_model": "vendor_hosted"},
      {"function": "Penetration testing / vulnerability assessment", "frequency": "very_common", "typical_model": "staff_augmentation"},
      {"function": "Digital banking platform hosting", "frequency": "common", "typical_model": "vendor_hosted"},
      {"function": "Infrastructure management", "frequency": "common", "typical_model": "MSP"},
      {"function": "IT audit and SOX testing", "frequency": "common", "typical_model": "co-managed"},
      {"function": "Application development", "frequency": "occasional", "typical_model": "staff_augmentation"}
    ],
    "typical_it_headcount_range": {
      "min": 10,
      "max": 30,
      "notes": "For a $500M-$5B asset bank or midmarket asset manager. Higher end includes dedicated compliance/audit IT staff."
    }
  },

  "typical_risks": [
    {
      "risk": "Core banking system on legacy platform with high conversion risk",
      "frequency": "common",
      "typical_severity": "critical",
      "typical_cost_impact": "$5M-$30M+ for core conversion",
      "deal_relevance": "Core conversions are the highest-risk IT project in banking. Directly impacts integration feasibility and timeline."
    },
    {
      "risk": "SOX IT control deficiencies or material weaknesses",
      "frequency": "common",
      "typical_severity": "high",
      "typical_cost_impact": "$500K-$3M for remediation",
      "deal_relevance": "Material weaknesses affect financial reporting reliability and may delay or complicate the transaction."
    },
    {
      "risk": "BSA/AML program deficiencies noted by examiners",
      "frequency": "common",
      "typical_severity": "critical",
      "typical_cost_impact": "$500K-$5M for remediation; potential enforcement action exposure",
      "deal_relevance": "Regulatory enforcement actions can delay acquisition approval and impose ongoing costs."
    },
    {
      "risk": "Vendor concentration risk — single vendor for core, digital, cards",
      "frequency": "very_common",
      "typical_severity": "medium",
      "typical_cost_impact": "$200K-$500K/year in vendor lock-in premium",
      "deal_relevance": "Limits strategic flexibility. Vendor contract terms (change of control) may trigger renegotiation."
    },
    {
      "risk": "Cybersecurity posture gaps relative to FFIEC expectations",
      "frequency": "common",
      "typical_severity": "high",
      "typical_cost_impact": "$300K-$1.5M for remediation program",
      "deal_relevance": "Regulatory exam findings on cybersecurity are increasingly common. Require board-level attention."
    },
    {
      "risk": "Manual regulatory reporting processes (Call Report, HMDA, CRA)",
      "frequency": "common",
      "typical_severity": "medium",
      "typical_cost_impact": "$200K-$600K to automate",
      "deal_relevance": "Manual processes increase error risk and consume significant staff time during reporting periods."
    }
  ],

  "core_workflows": [
    {
      "workflow_id": "deposit_operations",
      "name": "Deposit Account Lifecycle",
      "description": "Account opening through servicing, statements, and closing. Foundation of the banking relationship.",
      "steps": [
        {"step": "Application / Account Opening", "systems": ["core_banking", "digital_banking"], "manual_common": false, "manual_note": null},
        {"step": "KYC / CDD / CIP", "systems": ["aml_bsa_compliance", "core_banking"], "manual_common": true, "manual_note": "Enhanced due diligence for higher-risk customers often requires manual review"},
        {"step": "Account Servicing", "systems": ["core_banking", "digital_banking"], "manual_common": false, "manual_note": null},
        {"step": "Transaction Processing", "systems": ["core_banking", "card_management"], "manual_common": false, "manual_note": null},
        {"step": "AML Transaction Monitoring", "systems": ["aml_bsa_compliance"], "manual_common": true, "manual_note": "Alert investigation requires human review"},
        {"step": "Statement Generation", "systems": ["core_banking"], "manual_common": false, "manual_note": null},
        {"step": "Account Closing", "systems": ["core_banking"], "manual_common": true, "manual_note": "Escheatment and abandoned property rules add complexity"}
      ],
      "key_integrations": [
        {"from": "digital_banking", "to": "core_banking", "type": "real_time", "criticality": "critical"},
        {"from": "core_banking", "to": "aml_bsa_compliance", "type": "batch", "criticality": "critical"},
        {"from": "core_banking", "to": "card_management", "type": "real_time", "criticality": "high"},
        {"from": "core_banking", "to": "erp_gl", "type": "batch", "criticality": "high"}
      ]
    },
    {
      "workflow_id": "lending_lifecycle",
      "name": "Lending Lifecycle",
      "description": "Loan origination through servicing and payoff. Applies to commercial, consumer, and mortgage lending.",
      "steps": [
        {"step": "Application / Pre-qualification", "systems": ["loan_origination", "digital_banking"], "manual_common": false, "manual_note": null},
        {"step": "Credit Analysis / Underwriting", "systems": ["loan_origination"], "manual_common": true, "manual_note": "Commercial loans require significant manual credit analysis"},
        {"step": "Decision / Approval", "systems": ["loan_origination"], "manual_common": true, "manual_note": "Authority levels and committee approvals for larger credits"},
        {"step": "Document Preparation / Closing", "systems": ["loan_origination", "document_management"], "manual_common": true, "manual_note": "Legal document review and execution"},
        {"step": "Booking / Funding", "systems": ["core_banking", "loan_origination"], "manual_common": false, "manual_note": null},
        {"step": "Servicing / Payment Processing", "systems": ["loan_servicing", "core_banking"], "manual_common": false, "manual_note": null},
        {"step": "Collections / Workout", "systems": ["loan_servicing"], "manual_common": true, "manual_note": "Delinquent loan management requires judgment and negotiation"},
        {"step": "Payoff / Release", "systems": ["loan_servicing", "core_banking"], "manual_common": false, "manual_note": null}
      ],
      "key_integrations": [
        {"from": "loan_origination", "to": "core_banking", "type": "API", "criticality": "critical"},
        {"from": "core_banking", "to": "loan_servicing", "type": "real_time", "criticality": "critical"},
        {"from": "loan_origination", "to": "document_management", "type": "API", "criticality": "high"},
        {"from": "loan_servicing", "to": "erp_gl", "type": "batch", "criticality": "high"},
        {"from": "loan_origination", "to": "regulatory_reporting", "type": "batch", "criticality": "high"}
      ]
    },
    {
      "workflow_id": "regulatory_compliance",
      "name": "Regulatory Examination & Reporting",
      "description": "Ongoing regulatory compliance including exam preparation, report filing, and audit support.",
      "steps": [
        {"step": "Call Report Preparation", "systems": ["regulatory_reporting", "core_banking", "erp_gl"], "manual_common": true, "manual_note": "Significant data reconciliation and manual adjustments"},
        {"step": "HMDA / CRA Data Collection", "systems": ["loan_origination", "regulatory_reporting"], "manual_common": true, "manual_note": "Data scrubbing and geocoding often manual"},
        {"step": "Exam Preparation / Information Requests", "systems": ["document_management", "core_banking"], "manual_common": true, "manual_note": "Regulatory information requests are extensive"},
        {"step": "MRA / Finding Remediation", "systems": ["itsm_service_desk"], "manual_common": true, "manual_note": "Tracking and remediating exam findings"}
      ],
      "key_integrations": [
        {"from": "core_banking", "to": "regulatory_reporting", "type": "batch", "criticality": "critical"},
        {"from": "loan_origination", "to": "regulatory_reporting", "type": "batch", "criticality": "high"},
        {"from": "erp_gl", "to": "regulatory_reporting", "type": "batch", "criticality": "high"}
      ]
    }
  ],

  "deal_lens_considerations": {
    "growth": [
      "Can the core banking platform support 2-3x asset growth without conversion?",
      "Is the digital banking platform competitive for customer acquisition?",
      "Are APIs available for fintech partnerships and embedded banking?",
      "Can the lending platform support new product lines (SBA, CRE, C&I)?",
      "Is the data infrastructure ready for AI/ML-driven decisioning?",
      "Can the AML system scale with transaction volume growth?"
    ],
    "carve_out": [
      "Is the core banking instance shared with the parent institution?",
      "What regulatory approvals are required for the separation (OCC, FDIC, state)?",
      "How is customer data separated between entities?",
      "What TSA services are needed for shared infrastructure and operations?",
      "Are vendor contracts assignable or do they require new agreements?",
      "How are the bank charter and licenses structured?",
      "Is the FDIC insurance separate or shared?"
    ],
    "platform_add_on": [
      "Are both institutions on the same core banking platform?",
      "If different cores, what is the conversion timeline and cost?",
      "Can digital banking platforms be consolidated?",
      "What is the branch technology overlap and consolidation opportunity?",
      "Are there regulatory concentration or CRA implications?",
      "How compatible are the lending platforms and credit risk models?"
    ],
    "turnaround": [
      "Are there open MRAs, consent orders, or enforcement actions?",
      "What is the SOX IT control environment maturity?",
      "Is the BSA/AML program adequate — any examiner concerns?",
      "What is the cybersecurity posture relative to FFIEC CAT expectations?",
      "Are there deferred technology investments creating operational risk?",
      "What is the state of the core banking platform — supportability and vendor roadmap?"
    ]
  }
}
```

---

#### Template 4: Manufacturing (Discrete, Midmarket)

**File:** `data/industry_templates/manufacturing.json`

```json
{
  "template_id": "manufacturing_discrete_midmarket",
  "industry": "manufacturing",
  "sub_industry": "discrete",
  "size_tier": "midmarket",
  "version": "1.0",
  "last_updated": "2026-02",
  "provenance": "Compiled from Gartner IT Key Metrics 2025 — Manufacturing, Computer Economics IT Spending & Staffing Benchmarks 2024/2025, MESA International MES surveys, ICS-CERT advisories, Rockwell/Siemens OT documentation, ISA/IEC 62443 standards",

  "expected_systems": {
    "industry_critical": [
      {
        "category": "erp_manufacturing",
        "description": "Enterprise resource planning with manufacturing modules — production planning, inventory management, procurement, shop floor control, BOM management, MRP.",
        "common_vendors": ["SAP S/4HANA", "Oracle Cloud ERP", "Infor CloudSuite Industrial (SyteLine)", "Infor M3", "Epicor Kinetic", "IQMS (DELMIAworks)", "Microsoft Dynamics 365 Business Central"],
        "criticality": "critical",
        "typical_cost_range": "$500K-$3M/year",
        "migration_complexity": "high",
        "notes": "ERP is the backbone of manufacturing operations. Heavy customization is common. BOM accuracy and inventory management are critical. Many midmarket manufacturers run older ERP versions."
      },
      {
        "category": "mes",
        "description": "Manufacturing execution system — shop floor scheduling, work instructions, production tracking, WIP visibility, labor tracking, quality data collection.",
        "common_vendors": ["Rockwell Plex", "Siemens Opcenter", "SAP ME/MII", "AVEVA MES", "Aegis FactoryLogix", "42Q", "Tulip"],
        "criticality": "high",
        "typical_cost_range": "$300K-$1.5M implementation; $100K-$500K/year",
        "migration_complexity": "high",
        "notes": "Bridges the gap between ERP planning and shop floor execution. Many midmarket manufacturers lack a formal MES — relying on spreadsheets and paper travelers. MES is the most impactful system for operational improvement."
      },
      {
        "category": "ot_scada",
        "description": "Operational technology — PLCs, SCADA/HMI, DCS, data historians for production equipment control and monitoring.",
        "common_vendors": ["Rockwell Automation (Allen-Bradley/FactoryTalk)", "Siemens (TIA Portal/WinCC)", "Schneider Electric", "Honeywell", "ABB", "OSIsoft PI (AVEVA)"],
        "criticality": "critical",
        "typical_cost_range": "$200K-$2M+ per plant (capital investment)",
        "migration_complexity": "high",
        "notes": "OT systems run production equipment. Downtime = lost production. OT/IT convergence is a major trend but security segmentation is critical. Legacy PLCs running Windows XP/7 are common."
      },
      {
        "category": "qms",
        "description": "Quality management system — document control, nonconformance reports, CAPA, audit management, inspection records, supplier quality.",
        "common_vendors": ["MasterControl", "ETQ (Hexagon)", "Qualio", "SAP QM", "Sparta TrackWise", "Greenlight Guru", "IQS (HQMS)"],
        "criticality": "high",
        "typical_cost_range": "$75K-$400K/year",
        "migration_complexity": "medium",
        "notes": "Required for ISO 9001, IATF 16949, AS9100 certification. Paper-based quality records are a common finding that increases risk."
      }
    ],
    "industry_common": [
      {
        "category": "plm_cad",
        "description": "Product lifecycle management and CAD — product design, BOM management, engineering change orders, revision control.",
        "common_vendors": ["Siemens Teamcenter", "PTC Windchill", "Dassault ENOVIA/3DEXPERIENCE", "Arena PLM (PTC)", "Autodesk Fusion Manage", "SolidWorks PDM"],
        "criticality": "high",
        "typical_cost_range": "$100K-$600K/year",
        "migration_complexity": "medium",
        "notes": "Engineering BOM must sync with manufacturing BOM in ERP. CAD file management and version control are critical. Engineering change control is a key process."
      },
      {
        "category": "cmms_eam",
        "description": "Computerized maintenance management / enterprise asset management — preventive maintenance scheduling, work orders, spare parts, equipment history.",
        "common_vendors": ["IBM Maximo", "SAP PM", "Infor EAM", "UpKeep", "Fiix (Rockwell)", "eMaint (Fluke)"],
        "criticality": "high",
        "typical_cost_range": "$50K-$300K/year",
        "migration_complexity": "medium",
        "notes": "Unplanned downtime is the costliest event in manufacturing. Preventive/predictive maintenance reduces risk. CMMS data provides equipment health visibility."
      },
      {
        "category": "supply_chain_planning",
        "description": "Demand planning, S&OP, inventory optimization, supply planning, ATP/CTP.",
        "common_vendors": ["Kinaxis RapidResponse", "o9 Solutions", "Blue Yonder", "SAP IBP", "Oracle ASCP/Cloud Planning"],
        "criticality": "medium",
        "typical_cost_range": "$100K-$500K/year",
        "migration_complexity": "medium",
        "notes": "Many midmarket manufacturers use ERP MRP plus spreadsheets for planning. Dedicated planning tools are a maturity indicator."
      },
      {
        "category": "ehs",
        "description": "Environment, health, and safety — incident tracking, near-miss reporting, chemical/SDS management, OSHA recordkeeping, environmental compliance.",
        "common_vendors": ["Intelex", "VelocityEHS", "Enablon (Wolters Kluwer)", "Gensuite", "Benchmark ESG"],
        "criticality": "high",
        "typical_cost_range": "$50K-$200K/year",
        "migration_complexity": "low",
        "notes": "OSHA recordkeeping is required. Environmental permits and compliance tracking are critical. Paper-based EHS tracking is a red flag."
      },
      {
        "category": "wms",
        "description": "Warehouse management system — receiving, put-away, picking, packing, shipping, inventory location tracking.",
        "common_vendors": ["SAP EWM", "Oracle WMS", "Manhattan Associates", "Infor WMS", "Often within ERP"],
        "criticality": "medium",
        "typical_cost_range": "$75K-$300K/year",
        "migration_complexity": "medium",
        "notes": "Separate WMS is more common in distribution-heavy manufacturers. Many use ERP inventory modules for basic warehouse operations."
      },
      {
        "category": "shop_floor_data_collection",
        "description": "Barcode scanning, machine data collection, operator terminals, time tracking, labor reporting.",
        "common_vendors": ["Epicor Advanced MES", "Plex", "Tulip", "Custom solutions", "Often within MES"],
        "criticality": "medium",
        "typical_cost_range": "$50K-$200K/year",
        "migration_complexity": "medium",
        "notes": "Automated data collection reduces manual entry errors and provides real-time production visibility."
      }
    ],
    "general_enterprise": [
      {
        "category": "email_collaboration",
        "description": "Email, calendaring, video conferencing, file sharing.",
        "common_vendors": ["Microsoft 365", "Google Workspace"],
        "criticality": "high",
        "typical_cost_range": "$30K-$150K/year",
        "migration_complexity": "low",
        "notes": "M365 dominant. Manufacturing has a mix of office and shop floor users — licensing often tiered."
      },
      {
        "category": "crm",
        "description": "Customer relationship management — sales pipeline, quoting, order management, customer service.",
        "common_vendors": ["Salesforce", "Microsoft Dynamics 365", "HubSpot"],
        "criticality": "medium",
        "typical_cost_range": "$30K-$150K/year",
        "migration_complexity": "low",
        "notes": "Configure-price-quote (CPQ) integration with ERP is important for manufacturers with complex products."
      },
      {
        "category": "identity_access_management",
        "description": "SSO, MFA, directory services. Includes both corporate and shop floor access control.",
        "common_vendors": ["Microsoft Entra ID", "Okta"],
        "criticality": "high",
        "typical_cost_range": "$20K-$100K/year",
        "migration_complexity": "medium",
        "notes": "Shop floor systems may have separate authentication. OT systems often use local accounts — integration with corporate IAM is a maturity indicator."
      },
      {
        "category": "endpoint_security",
        "description": "EDR, antivirus, device management for corporate endpoints. OT endpoint protection is a separate concern.",
        "common_vendors": ["CrowdStrike", "SentinelOne", "Microsoft Defender", "Carbon Black"],
        "criticality": "high",
        "typical_cost_range": "$25K-$100K/year",
        "migration_complexity": "low",
        "notes": "OT endpoints (HMIs, engineering workstations) may not support standard EDR agents. Network-based detection is often needed for OT."
      },
      {
        "category": "backup_disaster_recovery",
        "description": "Data backup and disaster recovery for corporate and production systems.",
        "common_vendors": ["Veeam", "Commvault", "Rubrik", "Datto"],
        "criticality": "high",
        "typical_cost_range": "$40K-$150K/year",
        "migration_complexity": "low",
        "notes": "Production system backup (ERP, MES) critical. OT system backup often neglected — PLC program backup is essential but often informal."
      },
      {
        "category": "itsm_service_desk",
        "description": "IT service management, ticketing, change management.",
        "common_vendors": ["ServiceNow", "Jira Service Management", "Freshservice", "ManageEngine"],
        "criticality": "medium",
        "typical_cost_range": "$15K-$75K/year",
        "migration_complexity": "low",
        "notes": "Manufacturing IT maturity for ITSM often lower than other industries. Informal processes are common at midmarket."
      }
    ]
  },

  "expected_metrics": {
    "it_pct_revenue": {
      "low": 1.5,
      "typical": 2.5,
      "high": 3.5,
      "unit": "%",
      "source": "Gartner IT Key Metrics Data 2025 — Manufacturing",
      "notes": "Manufacturing has the lowest IT spend as % of revenue. OT/capital equipment spending is often separate from the IT budget."
    },
    "it_staff_per_100_employees": {
      "low": 1.5,
      "typical": 3.0,
      "high": 5.0,
      "unit": "ratio",
      "source": "Gartner IT Key Metrics 2025 — Manufacturing; Computer Economics 2024/2025",
      "notes": "Large shop floor workforce dilutes the ratio. IT staff supports both corporate and manufacturing systems."
    },
    "app_count_per_100_employees": {
      "low": 6,
      "typical": 12,
      "high": 20,
      "unit": "count",
      "source": "Productiv SaaS Benchmark Report 2024 — Manufacturing",
      "notes": "Lower than other industries due to shop floor workers who use few applications. Count increases with MES/IoT adoption."
    },
    "it_cost_per_employee": {
      "low": 5000,
      "typical": 8000,
      "high": 12000,
      "unit": "USD",
      "source": "Computer Economics IT Spending & Staffing Benchmarks 2024/2025 — Manufacturing",
      "notes": "Lower per-employee due to large non-IT workforce. Per office-worker cost is more comparable to other industries."
    },
    "security_pct_it_budget": {
      "low": 4,
      "typical": 7,
      "high": 12,
      "unit": "%",
      "source": "Gartner Security & Risk Management Survey 2024",
      "notes": "OT security spending is often separate or emerging. Combined IT+OT security investment trending upward."
    },
    "cloud_adoption_pct": {
      "low": 20,
      "typical": 35,
      "high": 55,
      "unit": "%",
      "source": "Flexera State of the Cloud Report 2024 — Manufacturing",
      "notes": "ERP cloud migration accelerating (Infor CloudSuite, Epicor Cloud). OT systems remain on-prem. Edge computing emerging."
    },
    "outsourcing_pct": {
      "low": 10,
      "typical": 25,
      "high": 40,
      "unit": "%",
      "source": "ISG Outsourcing Index 2024 — Manufacturing",
      "notes": "IT infrastructure management commonly outsourced. OT support rarely outsourced due to plant-specific knowledge requirements."
    },
    "tech_refresh_cycle_years": {
      "low": 4,
      "typical": 6,
      "high": 8,
      "unit": "years",
      "source": "Gartner Infrastructure & Operations Survey 2024",
      "notes": "OT equipment refresh cycles are 10-20+ years. Corporate IT on standard 4-5 year cycles."
    }
  },

  "expected_organization": {
    "typical_roles": [
      {"role": "IT Director / IT Manager", "category": "leadership", "typical_count": "1", "notes": "CIO title less common at midmarket manufacturing. May report to CFO or VP Operations."},
      {"role": "ERP Administrator / Developer", "category": "applications", "typical_count": "1-3", "notes": "Often the most critical IT role. Deep knowledge of manufacturing modules (production, inventory, BOM)."},
      {"role": "Infrastructure / Network Admin", "category": "infrastructure", "typical_count": "1-3", "notes": "Manages corporate network plus plant connectivity. May also manage OT network if IT/OT converged."},
      {"role": "Help Desk / Desktop Support", "category": "service_desk", "typical_count": "1-2", "notes": "Supports office staff and may support shop floor terminals/scanners."},
      {"role": "OT / Controls Engineer", "category": "infrastructure", "typical_count": "1-3", "notes": "May report to plant engineering rather than IT. PLC programming, SCADA configuration, historian management."},
      {"role": "Quality / QMS Administrator", "category": "applications", "typical_count": "0-1", "notes": "QMS system administration. May be in quality department rather than IT."},
      {"role": "DBA / Report Writer", "category": "data", "typical_count": "0-1", "notes": "ERP reporting, production analytics, management dashboards."}
    ],
    "typical_outsourcing": [
      {"function": "Security monitoring / SIEM", "frequency": "common", "typical_model": "MSSP"},
      {"function": "Network management", "frequency": "common", "typical_model": "MSP"},
      {"function": "ERP consulting / development", "frequency": "common", "typical_model": "staff_augmentation"},
      {"function": "Help desk", "frequency": "occasional", "typical_model": "MSP"},
      {"function": "Cloud infrastructure management", "frequency": "occasional", "typical_model": "MSP"},
      {"function": "OT security assessment", "frequency": "occasional", "typical_model": "staff_augmentation"}
    ],
    "typical_it_headcount_range": {
      "min": 5,
      "max": 18,
      "notes": "For a 200-1000 employee manufacturer. Does not include plant engineering/controls staff unless they report to IT."
    }
  },

  "typical_risks": [
    {
      "risk": "OT/IT network convergence without proper segmentation — flat network with production and corporate commingled",
      "frequency": "very_common",
      "typical_severity": "critical",
      "typical_cost_impact": "$200K-$800K for network segmentation project",
      "deal_relevance": "Flat OT/IT network is the top cybersecurity risk in manufacturing. Ransomware can halt production."
    },
    {
      "risk": "Legacy PLC/SCADA systems running unsupported OS (Windows XP, Windows 7) with no patching",
      "frequency": "very_common",
      "typical_severity": "high",
      "typical_cost_impact": "$500K-$5M per plant for OT modernization",
      "deal_relevance": "Cannot be patched, only mitigated through segmentation. Replacement tied to production equipment lifecycle."
    },
    {
      "risk": "ERP system on legacy version requiring major upgrade or replacement",
      "frequency": "common",
      "typical_severity": "high",
      "typical_cost_impact": "$1M-$5M for ERP migration",
      "deal_relevance": "Manufacturing ERP migrations are complex (BOM, routing, costing data). 12-24 month timeline typical."
    },
    {
      "risk": "No MES — production tracking via spreadsheets and paper travelers",
      "frequency": "common",
      "typical_severity": "medium",
      "typical_cost_impact": "$500K-$2M for MES implementation per plant",
      "deal_relevance": "Lack of MES means limited production visibility, manual quality records, and difficulty scaling operations."
    },
    {
      "risk": "Key person dependency on ERP and OT systems knowledge",
      "frequency": "very_common",
      "typical_severity": "high",
      "typical_cost_impact": "$300K-$1M in transition risk",
      "deal_relevance": "Manufacturing IT is highly specialized. Loss of the ERP admin or controls engineer can disrupt operations."
    },
    {
      "risk": "Quality certification risk — paper-based QMS records or gaps in CAPA tracking",
      "frequency": "common",
      "typical_severity": "high",
      "typical_cost_impact": "$150K-$500K for QMS implementation and certification prep",
      "deal_relevance": "Loss of ISO/IATF certification can mean loss of customer contracts."
    }
  ],

  "core_workflows": [
    {
      "workflow_id": "order_to_ship",
      "name": "Order to Ship",
      "description": "Customer order receipt through production scheduling, manufacturing, quality inspection, and shipment. The core value-creation workflow.",
      "steps": [
        {"step": "Order Entry / Quote", "systems": ["erp_manufacturing", "crm"], "manual_common": true, "manual_note": "Complex configured products may require manual quoting and engineering review"},
        {"step": "Production Planning / MRP", "systems": ["erp_manufacturing", "supply_chain_planning"], "manual_common": true, "manual_note": "MRP output often requires manual adjustment for capacity constraints and priorities"},
        {"step": "Work Order Release", "systems": ["erp_manufacturing", "mes"], "manual_common": false, "manual_note": null},
        {"step": "Shop Floor Execution", "systems": ["mes", "ot_scada", "shop_floor_data_collection"], "manual_common": false, "manual_note": null},
        {"step": "Quality Inspection", "systems": ["qms", "mes"], "manual_common": true, "manual_note": "First article and in-process inspection often manual with manual data entry"},
        {"step": "Packing / Shipping", "systems": ["erp_manufacturing", "wms"], "manual_common": false, "manual_note": null},
        {"step": "Invoicing", "systems": ["erp_manufacturing"], "manual_common": false, "manual_note": null}
      ],
      "key_integrations": [
        {"from": "erp_manufacturing", "to": "mes", "type": "API", "criticality": "critical"},
        {"from": "mes", "to": "ot_scada", "type": "real_time", "criticality": "high"},
        {"from": "mes", "to": "qms", "type": "API", "criticality": "high"},
        {"from": "erp_manufacturing", "to": "wms", "type": "API", "criticality": "medium"},
        {"from": "crm", "to": "erp_manufacturing", "type": "API", "criticality": "medium"}
      ]
    },
    {
      "workflow_id": "engineering_change",
      "name": "Engineering Change Management",
      "description": "Product design changes from engineering request through BOM update, production effectivity, and inventory disposition.",
      "steps": [
        {"step": "ECR Initiation", "systems": ["plm_cad"], "manual_common": false, "manual_note": null},
        {"step": "Engineering Review / Approval", "systems": ["plm_cad"], "manual_common": true, "manual_note": "Cross-functional review (engineering, manufacturing, quality, procurement) is typically manual"},
        {"step": "CAD / Design Update", "systems": ["plm_cad"], "manual_common": false, "manual_note": null},
        {"step": "BOM Update in ERP", "systems": ["erp_manufacturing", "plm_cad"], "manual_common": true, "manual_note": "BOM sync between PLM and ERP is often manual at midmarket — key integration gap"},
        {"step": "Production Effectivity / Cutover", "systems": ["erp_manufacturing", "mes"], "manual_common": true, "manual_note": "Managing old/new revision inventory and production cutover requires coordination"},
        {"step": "Inventory Disposition", "systems": ["erp_manufacturing"], "manual_common": true, "manual_note": "Disposition of obsolete inventory (scrap, rework, use-as-is)"}
      ],
      "key_integrations": [
        {"from": "plm_cad", "to": "erp_manufacturing", "type": "API", "criticality": "critical"},
        {"from": "erp_manufacturing", "to": "mes", "type": "API", "criticality": "high"},
        {"from": "plm_cad", "to": "qms", "type": "API", "criticality": "medium"}
      ]
    },
    {
      "workflow_id": "maintenance_operations",
      "name": "Equipment Maintenance & OT Operations",
      "description": "Preventive and reactive maintenance of production equipment, OT system management, and plant reliability.",
      "steps": [
        {"step": "PM Scheduling", "systems": ["cmms_eam"], "manual_common": false, "manual_note": null},
        {"step": "Work Order Execution", "systems": ["cmms_eam"], "manual_common": true, "manual_note": "Maintenance technicians execute and document work — data entry quality varies"},
        {"step": "Spare Parts Management", "systems": ["cmms_eam", "erp_manufacturing"], "manual_common": true, "manual_note": "Spare parts inventory often poorly tracked at midmarket"},
        {"step": "Breakdown / Emergency Response", "systems": ["cmms_eam", "ot_scada"], "manual_common": true, "manual_note": "Emergency maintenance is inherently reactive and manual"},
        {"step": "Equipment History / Reliability Analysis", "systems": ["cmms_eam", "ot_scada"], "manual_common": true, "manual_note": "Mean time between failures and reliability analysis often done in spreadsheets"}
      ],
      "key_integrations": [
        {"from": "cmms_eam", "to": "erp_manufacturing", "type": "API", "criticality": "high"},
        {"from": "ot_scada", "to": "cmms_eam", "type": "batch", "criticality": "medium"},
        {"from": "ot_scada", "to": "data_warehouse_analytics", "type": "batch", "criticality": "medium"}
      ]
    }
  ],

  "deal_lens_considerations": {
    "growth": [
      "Can the ERP handle additional plants, product lines, or business units without re-platforming?",
      "Is MES in place to support production scaling and additional shifts?",
      "Is the OT infrastructure modern enough to support Industry 4.0 / IoT initiatives?",
      "Can the supply chain planning tools handle increased complexity (more SKUs, more suppliers)?",
      "Is product engineering (PLM/CAD) scalable for new product development?",
      "Are quality systems scalable for additional certifications or customer requirements?"
    ],
    "carve_out": [
      "Is the ERP instance shared with the parent company?",
      "What TSA duration is needed for shared manufacturing systems?",
      "Are OT/SCADA systems shared across facilities being separated?",
      "Which vendor contracts (ERP, CAD, OT) require assignment or new agreements?",
      "Is the OT historian shared — how is production data separated?",
      "Are quality certifications (ISO 9001, IATF 16949) at the plant or corporate level?",
      "Is there shared engineering data (CAD files, BOMs) that needs to be separated?"
    ],
    "platform_add_on": [
      "Are both organizations on the same ERP platform?",
      "Can MES be standardized across combined plant footprint?",
      "What is the OT landscape overlap — same PLCs/SCADA vendors?",
      "Can quality management systems be consolidated?",
      "Are there supply chain synergies that require system integration?",
      "How compatible are the product data models (BOMs, routings, costing)?"
    ],
    "turnaround": [
      "What is the OT security posture — is there IT/OT segmentation?",
      "Are production systems running unsupported software (Windows XP, old PLC firmware)?",
      "Is there a MES or is production tracked manually?",
      "What is the ERP version and vendor support status?",
      "Are quality certifications current and at risk?",
      "Is there deferred maintenance on production equipment creating reliability risk?",
      "What is the state of spare parts inventory accuracy?"
    ]
  }
}
```

---

#### Template 5: Technology (SaaS, Midmarket)

**File:** `data/industry_templates/technology.json`

```json
{
  "template_id": "technology_saas_midmarket",
  "industry": "technology",
  "sub_industry": "saas",
  "size_tier": "midmarket",
  "version": "1.0",
  "last_updated": "2026-02",
  "provenance": "Compiled from Gartner IT Key Metrics 2025 — Technology, Computer Economics IT Spending & Staffing Benchmarks 2024/2025, KeyBanc SaaS Survey 2024, OpenView SaaS Benchmarks 2024, Datadog State of DevOps 2024, DORA Accelerate State of DevOps Report 2024",

  "expected_systems": {
    "industry_critical": [
      {
        "category": "product_platform",
        "description": "The SaaS product itself — application code, databases, API layer, multi-tenant infrastructure. This IS the business.",
        "common_vendors": ["Custom-built (AWS, Azure, GCP hosted)", "May leverage PaaS (Heroku, Vercel, Render)"],
        "criticality": "critical",
        "typical_cost_range": "$200K-$2M/year in hosting/infrastructure",
        "migration_complexity": "high",
        "notes": "The product platform is the company's core asset. Architecture maturity (multi-tenant vs. single-tenant, microservices vs. monolith) directly impacts scalability and valuation. Technical debt assessment is critical in diligence."
      },
      {
        "category": "cicd_pipeline",
        "description": "Continuous integration and continuous deployment — source control, build automation, testing automation, deployment pipelines, artifact management.",
        "common_vendors": ["GitHub Actions", "GitLab CI/CD", "Jenkins", "CircleCI", "Azure DevOps", "ArgoCD", "Harness"],
        "criticality": "critical",
        "typical_cost_range": "$30K-$200K/year",
        "migration_complexity": "medium",
        "notes": "Deployment frequency and lead time are DORA metrics that indicate engineering velocity. Mature CI/CD enables rapid feature delivery and is a valuation driver."
      },
      {
        "category": "monitoring_observability",
        "description": "Application performance monitoring, infrastructure monitoring, logging, distributed tracing, alerting, SLA monitoring.",
        "common_vendors": ["Datadog", "New Relic", "Splunk", "Grafana/Prometheus", "PagerDuty", "OpsGenie"],
        "criticality": "critical",
        "typical_cost_range": "$50K-$400K/year",
        "migration_complexity": "medium",
        "notes": "Observability maturity directly impacts incident response and SLA compliance. Datadog costs can grow significantly with data volume."
      },
      {
        "category": "source_control",
        "description": "Code repository, version control, code review, pull request workflows, branch management.",
        "common_vendors": ["GitHub", "GitLab", "Bitbucket", "Azure DevOps Repos"],
        "criticality": "critical",
        "typical_cost_range": "$10K-$80K/year",
        "migration_complexity": "low",
        "notes": "Contains the IP. Repository structure, branching strategy, and code review practices reflect engineering maturity."
      }
    ],
    "industry_common": [
      {
        "category": "cloud_infrastructure",
        "description": "IaaS/PaaS cloud platform — compute, storage, networking, managed services (databases, queues, caches).",
        "common_vendors": ["AWS", "Microsoft Azure", "Google Cloud Platform"],
        "criticality": "critical",
        "typical_cost_range": "$100K-$1.5M/year",
        "migration_complexity": "high",
        "notes": "Cloud spend is often the largest single IT cost for SaaS companies. FinOps maturity (cost optimization) is a key diligence area. Multi-cloud adds complexity."
      },
      {
        "category": "customer_success_platform",
        "description": "Customer health scoring, usage analytics, churn prediction, renewal management, NPS tracking.",
        "common_vendors": ["Gainsight", "Totango", "ChurnZero", "Vitally", "Planhat"],
        "criticality": "high",
        "typical_cost_range": "$30K-$150K/year",
        "migration_complexity": "low",
        "notes": "Customer retention is the #1 SaaS metric. Gross retention rate and net revenue retention are PE focus areas."
      },
      {
        "category": "product_analytics",
        "description": "User behavior tracking, feature adoption analytics, funnel analysis, A/B testing.",
        "common_vendors": ["Amplitude", "Mixpanel", "Pendo", "Heap", "LaunchDarkly (feature flags)", "Segment (CDP)"],
        "criticality": "high",
        "typical_cost_range": "$30K-$200K/year",
        "migration_complexity": "low",
        "notes": "Product-led growth companies rely heavily on product analytics. Feature flag platforms enable progressive rollouts."
      },
      {
        "category": "incident_management",
        "description": "On-call scheduling, incident response, postmortem process, status page, SLA tracking.",
        "common_vendors": ["PagerDuty", "OpsGenie (Atlassian)", "Incident.io", "FireHydrant", "Statuspage"],
        "criticality": "high",
        "typical_cost_range": "$15K-$80K/year",
        "migration_complexity": "low",
        "notes": "Incident response maturity reflects operational reliability. Customer-facing status pages are expected."
      },
      {
        "category": "security_tools",
        "description": "Application security — SAST, DAST, dependency scanning, secret management, vulnerability management, penetration testing.",
        "common_vendors": ["Snyk", "SonarQube", "Veracode", "HashiCorp Vault", "Wiz", "Orca Security"],
        "criticality": "high",
        "typical_cost_range": "$40K-$250K/year",
        "migration_complexity": "low",
        "notes": "SOC 2 compliance drives security tooling investment. Shift-left security (SAST/SCA in CI pipeline) is a maturity indicator."
      },
      {
        "category": "billing_subscription_mgmt",
        "description": "Subscription billing, usage-based billing, revenue recognition, dunning, subscription lifecycle management.",
        "common_vendors": ["Stripe Billing", "Chargebee", "Zuora", "Recurly", "Maxio (SaaSOptics + Chargify)"],
        "criticality": "high",
        "typical_cost_range": "$20K-$150K/year",
        "migration_complexity": "medium",
        "notes": "Billing system accuracy directly impacts ARR reporting. ASC 606 revenue recognition compliance is critical for PE-backed companies."
      },
      {
        "category": "documentation_knowledge",
        "description": "Product documentation, API documentation, internal knowledge base, developer portal.",
        "common_vendors": ["Notion", "Confluence", "ReadMe", "GitBook", "Mintlify"],
        "criticality": "medium",
        "typical_cost_range": "$10K-$50K/year",
        "migration_complexity": "low",
        "notes": "API documentation quality is a developer experience differentiator. Internal knowledge management reflects engineering maturity."
      }
    ],
    "general_enterprise": [
      {
        "category": "crm",
        "description": "Sales pipeline, deal management, forecasting, customer lifecycle tracking.",
        "common_vendors": ["Salesforce", "HubSpot"],
        "criticality": "high",
        "typical_cost_range": "$50K-$300K/year",
        "migration_complexity": "low",
        "notes": "CRM data quality directly impacts pipeline accuracy and forecasting. Salesforce CPQ common for complex pricing."
      },
      {
        "category": "marketing_automation",
        "description": "Lead generation, nurture campaigns, attribution, website analytics, content management.",
        "common_vendors": ["HubSpot", "Marketo (Adobe)", "Pardot (Salesforce)", "6sense", "Demandbase"],
        "criticality": "medium",
        "typical_cost_range": "$30K-$200K/year",
        "migration_complexity": "low",
        "notes": "CAC (customer acquisition cost) efficiency depends on marketing automation maturity. Attribution modeling is a common gap."
      },
      {
        "category": "email_collaboration",
        "description": "Email, calendaring, video conferencing, file sharing, team messaging.",
        "common_vendors": ["Google Workspace", "Microsoft 365", "Slack", "Zoom"],
        "criticality": "high",
        "typical_cost_range": "$30K-$150K/year",
        "migration_complexity": "low",
        "notes": "Google Workspace more common in SaaS/tech than other industries. Slack dominant for team chat."
      },
      {
        "category": "identity_access_management",
        "description": "SSO, MFA, directory services, SCIM provisioning, zero trust architecture.",
        "common_vendors": ["Okta", "Microsoft Entra ID", "Google Identity", "JumpCloud"],
        "criticality": "high",
        "typical_cost_range": "$20K-$100K/year",
        "migration_complexity": "medium",
        "notes": "SSO and MFA enforcement are SOC 2 requirements. Zero trust adoption increasing."
      },
      {
        "category": "hris_payroll",
        "description": "HR information system, payroll, benefits, performance management.",
        "common_vendors": ["Rippling", "Gusto", "Deel", "ADP", "BambooHR", "Workday"],
        "criticality": "medium",
        "typical_cost_range": "$30K-$150K/year",
        "migration_complexity": "low",
        "notes": "Distributed/remote workforce common in SaaS — Deel/Rippling for international teams."
      },
      {
        "category": "erp_gl",
        "description": "General ledger, AP/AR, financial reporting, revenue recognition.",
        "common_vendors": ["NetSuite", "Sage Intacct", "QuickBooks (early stage)"],
        "criticality": "high",
        "typical_cost_range": "$50K-$250K/year",
        "migration_complexity": "medium",
        "notes": "NetSuite and Sage Intacct dominate SaaS midmarket. ASC 606 revenue recognition support is critical."
      }
    ]
  },

  "expected_metrics": {
    "it_pct_revenue": {
      "low": 5.0,
      "typical": 7.0,
      "high": 10.0,
      "unit": "%",
      "source": "Gartner IT Key Metrics Data 2025 — Technology; KeyBanc SaaS Survey 2024",
      "notes": "Technology companies invest most in IT as a core capability. Product hosting costs (COGS) often dominate the IT budget."
    },
    "it_staff_per_100_employees": {
      "low": 6.0,
      "typical": 10.0,
      "high": 15.0,
      "unit": "ratio",
      "source": "Gartner IT Key Metrics 2025 — Technology; Computer Economics 2024/2025",
      "notes": "Highest ratio of any industry because engineering IS the product team. Includes SRE, DevOps, platform engineering."
    },
    "app_count_per_100_employees": {
      "low": 15,
      "typical": 25,
      "high": 40,
      "unit": "count",
      "source": "Productiv SaaS Benchmark Report 2024 — Technology",
      "notes": "SaaS companies use more SaaS tools than any other industry. 'SaaS sprawl' is a common cost concern."
    },
    "it_cost_per_employee": {
      "low": 12000,
      "typical": 18000,
      "high": 25000,
      "unit": "USD",
      "source": "Computer Economics IT Spending & Staffing Benchmarks 2024/2025 — Technology",
      "notes": "Includes cloud hosting costs. Per-employee cost is high due to developer tooling and cloud infrastructure."
    },
    "gross_margin": {
      "low": 65,
      "typical": 75,
      "high": 85,
      "unit": "%",
      "source": "KeyBanc SaaS Survey 2024; OpenView SaaS Benchmarks 2024",
      "notes": "SaaS gross margin is a key PE metric. Hosting costs, customer support, and professional services impact gross margin."
    },
    "net_revenue_retention": {
      "low": 100,
      "typical": 110,
      "high": 130,
      "unit": "%",
      "source": "KeyBanc SaaS Survey 2024; OpenView SaaS Benchmarks 2024",
      "notes": "NRR above 110% indicates strong expansion revenue. Below 100% indicates net contraction — a red flag."
    },
    "cac_payback_months": {
      "low": 12,
      "typical": 18,
      "high": 30,
      "unit": "months",
      "source": "KeyBanc SaaS Survey 2024",
      "notes": "CAC payback period under 18 months is best-in-class. Over 30 months indicates sales efficiency problems."
    },
    "cloud_cost_pct_revenue": {
      "low": 5,
      "typical": 10,
      "high": 20,
      "unit": "%",
      "source": "Flexera State of the Cloud 2024; a16z Cost of Cloud analysis",
      "notes": "Cloud COGS is the largest variable cost for SaaS companies. FinOps maturity directly impacts margins."
    },
    "security_pct_it_budget": {
      "low": 5,
      "typical": 10,
      "high": 15,
      "unit": "%",
      "source": "Gartner Security & Risk Management Survey 2024",
      "notes": "SOC 2 compliance drives baseline investment. Enterprise customers increasingly require SOC 2 Type II and penetration test reports."
    },
    "deployment_frequency": {
      "low": 1,
      "typical": 10,
      "high": 50,
      "unit": "deploys/week",
      "source": "DORA Accelerate State of DevOps Report 2024",
      "notes": "DORA elite performers deploy on-demand (multiple per day). Low deployment frequency indicates CI/CD immaturity or monolith constraints."
    }
  },

  "expected_organization": {
    "typical_roles": [
      {"role": "CTO / VP of Engineering", "category": "leadership", "typical_count": "1", "notes": "CTO owns product engineering. May have a separate VP of Infrastructure / Platform."},
      {"role": "Software Engineers (Frontend, Backend, Fullstack)", "category": "applications", "typical_count": "15-50", "notes": "Core engineering team. Ratio of engineers to total headcount is a key metric."},
      {"role": "SRE / DevOps / Platform Engineers", "category": "infrastructure", "typical_count": "2-6", "notes": "Manages infrastructure, CI/CD, reliability. SRE:developer ratio of 1:8-12 is typical."},
      {"role": "QA / SDET", "category": "applications", "typical_count": "2-5", "notes": "Automated testing. Some organizations embed QA in engineering teams rather than having a separate function."},
      {"role": "Security Engineer / AppSec", "category": "security", "typical_count": "0-2", "notes": "Dedicated security engineer common after SOC 2 compliance. May be combined with SRE."},
      {"role": "IT Admin / Corporate IT", "category": "service_desk", "typical_count": "1-2", "notes": "Internal corporate IT (laptops, SaaS admin, onboarding). Often a small team relative to engineering."},
      {"role": "Data Engineer / Analytics", "category": "data", "typical_count": "1-3", "notes": "Data pipeline, product analytics, customer data platform."},
      {"role": "Engineering Manager / VP Eng", "category": "leadership", "typical_count": "2-5", "notes": "Middle management layer. Span of control 5-8 engineers per manager typical."}
    ],
    "typical_outsourcing": [
      {"function": "Security monitoring / SOC", "frequency": "common", "typical_model": "MSSP"},
      {"function": "Penetration testing / security audits", "frequency": "very_common", "typical_model": "staff_augmentation"},
      {"function": "SOC 2 audit", "frequency": "very_common", "typical_model": "staff_augmentation"},
      {"function": "Offshore/nearshore software development", "frequency": "common", "typical_model": "staff_augmentation"},
      {"function": "IT help desk / device management", "frequency": "occasional", "typical_model": "MSP"},
      {"function": "QA / testing", "frequency": "occasional", "typical_model": "staff_augmentation"}
    ],
    "typical_it_headcount_range": {
      "min": 20,
      "max": 60,
      "notes": "For a 50-250 employee SaaS company. Engineering typically 40-60% of total headcount. This includes all technical staff (engineers, SRE, QA, data)."
    }
  },

  "typical_risks": [
    {
      "risk": "Technical debt in core product — monolithic architecture, poor test coverage, lack of documentation",
      "frequency": "very_common",
      "typical_severity": "high",
      "typical_cost_impact": "$500K-$3M+ for remediation / refactoring",
      "deal_relevance": "Technical debt directly impacts engineering velocity, product roadmap execution, and scalability. Key diligence finding."
    },
    {
      "risk": "Single cloud provider lock-in with proprietary services",
      "frequency": "very_common",
      "typical_severity": "medium",
      "typical_cost_impact": "$200K-$1M for cloud portability",
      "deal_relevance": "Cloud concentration risk affects negotiating leverage and disaster recovery options."
    },
    {
      "risk": "Key person dependency on original architects / founding engineers",
      "frequency": "very_common",
      "typical_severity": "high",
      "typical_cost_impact": "$500K-$2M in transition risk and institutional knowledge loss",
      "deal_relevance": "Founding engineers may leave post-acquisition. Their departure can significantly slow engineering velocity."
    },
    {
      "risk": "SOC 2 gaps or lack of SOC 2 Type II certification",
      "frequency": "common",
      "typical_severity": "high",
      "typical_cost_impact": "$200K-$500K for initial SOC 2 achievement",
      "deal_relevance": "Enterprise customers require SOC 2. Lack of certification limits upmarket sales motion."
    },
    {
      "risk": "Unsustainable cloud cost growth — COGS expanding faster than revenue",
      "frequency": "common",
      "typical_severity": "medium",
      "typical_cost_impact": "$100K-$500K/year in optimization opportunity",
      "deal_relevance": "Cloud cost optimization can improve gross margins by 5-10 percentage points. Direct impact on valuation."
    },
    {
      "risk": "Single-tenant architecture limiting multi-tenant scalability",
      "frequency": "occasional",
      "typical_severity": "high",
      "typical_cost_impact": "$1M-$5M+ for multi-tenant migration",
      "deal_relevance": "Single-tenant SaaS has lower margins, higher operational burden, and limited scalability."
    },
    {
      "risk": "Customer data isolation gaps — shared databases without tenant isolation",
      "frequency": "common",
      "typical_severity": "critical",
      "typical_cost_impact": "$200K-$1M for proper data isolation",
      "deal_relevance": "Data isolation failures can lead to breaches and customer trust issues. Critical for enterprise customers."
    }
  ],

  "core_workflows": [
    {
      "workflow_id": "software_delivery",
      "name": "Software Delivery Lifecycle",
      "description": "Feature development from ideation through deployment and monitoring. The core value-creation workflow for a SaaS company.",
      "steps": [
        {"step": "Product Planning / Backlog", "systems": ["product_management"], "manual_common": true, "manual_note": "Prioritization and roadmap decisions require human judgment"},
        {"step": "Development / Coding", "systems": ["source_control", "documentation_knowledge"], "manual_common": false, "manual_note": null},
        {"step": "Code Review", "systems": ["source_control"], "manual_common": true, "manual_note": "Peer code review is manual but critical for quality"},
        {"step": "Automated Testing", "systems": ["cicd_pipeline"], "manual_common": false, "manual_note": null},
        {"step": "Build / Deploy", "systems": ["cicd_pipeline", "cloud_infrastructure"], "manual_common": false, "manual_note": null},
        {"step": "Monitoring / Validation", "systems": ["monitoring_observability"], "manual_common": false, "manual_note": null},
        {"step": "Incident Response (if issues)", "systems": ["incident_management", "monitoring_observability"], "manual_common": true, "manual_note": "Incident triage and resolution require human judgment"},
        {"step": "Postmortem / Retrospective", "systems": ["documentation_knowledge"], "manual_common": true, "manual_note": "Blameless postmortems are a cultural practice"}
      ],
      "key_integrations": [
        {"from": "source_control", "to": "cicd_pipeline", "type": "real_time", "criticality": "critical"},
        {"from": "cicd_pipeline", "to": "cloud_infrastructure", "type": "real_time", "criticality": "critical"},
        {"from": "monitoring_observability", "to": "incident_management", "type": "real_time", "criticality": "critical"},
        {"from": "source_control", "to": "security_tools", "type": "real_time", "criticality": "high"}
      ]
    },
    {
      "workflow_id": "customer_lifecycle",
      "name": "Customer Lifecycle (Land, Adopt, Expand, Renew)",
      "description": "Customer journey from initial sale through onboarding, adoption, expansion, and renewal. Drives net revenue retention.",
      "steps": [
        {"step": "Sales / Close", "systems": ["crm"], "manual_common": true, "manual_note": null},
        {"step": "Onboarding / Implementation", "systems": ["customer_success_platform", "product_platform"], "manual_common": true, "manual_note": "Customer onboarding often involves implementation team and manual configuration"},
        {"step": "Adoption Monitoring", "systems": ["product_analytics", "customer_success_platform"], "manual_common": false, "manual_note": null},
        {"step": "Support", "systems": ["itsm_service_desk", "product_platform"], "manual_common": true, "manual_note": "Customer support tickets require human resolution"},
        {"step": "Expansion / Upsell", "systems": ["customer_success_platform", "crm", "billing_subscription_mgmt"], "manual_common": true, "manual_note": "Expansion opportunities identified by CS, executed by sales"},
        {"step": "Renewal", "systems": ["customer_success_platform", "billing_subscription_mgmt", "crm"], "manual_common": true, "manual_note": "Renewal management and negotiation"}
      ],
      "key_integrations": [
        {"from": "crm", "to": "billing_subscription_mgmt", "type": "API", "criticality": "critical"},
        {"from": "product_platform", "to": "product_analytics", "type": "real_time", "criticality": "high"},
        {"from": "product_analytics", "to": "customer_success_platform", "type": "API", "criticality": "high"},
        {"from": "billing_subscription_mgmt", "to": "erp_gl", "type": "batch", "criticality": "high"}
      ]
    },
    {
      "workflow_id": "security_compliance",
      "name": "Security & SOC 2 Compliance",
      "description": "Ongoing security operations and SOC 2 compliance activities including vulnerability management, access reviews, and audit evidence collection.",
      "steps": [
        {"step": "Vulnerability Scanning / SAST / SCA", "systems": ["security_tools", "cicd_pipeline"], "manual_common": false, "manual_note": null},
        {"step": "Vulnerability Triage / Remediation", "systems": ["security_tools"], "manual_common": true, "manual_note": "Risk assessment and prioritization of findings requires human judgment"},
        {"step": "Access Review", "systems": ["identity_access_management"], "manual_common": true, "manual_note": "Quarterly access reviews are a SOC 2 requirement"},
        {"step": "Penetration Testing", "systems": ["security_tools"], "manual_common": true, "manual_note": "Annual penetration testing by external firm"},
        {"step": "Evidence Collection / Audit", "systems": ["documentation_knowledge"], "manual_common": true, "manual_note": "SOC 2 audit evidence collection is time-consuming. GRC automation tools help."},
        {"step": "Remediation / Control Improvement", "systems": ["security_tools", "cicd_pipeline"], "manual_common": true, "manual_note": "Audit findings require remediation planning and execution"}
      ],
      "key_integrations": [
        {"from": "security_tools", "to": "cicd_pipeline", "type": "real_time", "criticality": "high"},
        {"from": "security_tools", "to": "monitoring_observability", "type": "API", "criticality": "medium"},
        {"from": "identity_access_management", "to": "product_platform", "type": "real_time", "criticality": "high"}
      ]
    }
  ],

  "deal_lens_considerations": {
    "growth": [
      "Can the product architecture handle 3-5x user/data growth without re-architecture?",
      "What is the deployment frequency and engineering velocity trend?",
      "Is the product multi-tenant or does each customer require a separate instance?",
      "What is the current cloud cost as % of revenue and can it be optimized?",
      "Is the product API-first, enabling integration and platform ecosystem?",
      "What is the engineering team's capacity for new feature development vs. maintenance?"
    ],
    "carve_out": [
      "Is the product infrastructure shared with the parent's other products?",
      "Are there shared engineering teams, CI/CD pipelines, or cloud accounts?",
      "How is customer data separated from the parent's other products?",
      "What TSA services are needed for shared SRE, security, or infrastructure teams?",
      "Are there shared vendor contracts (AWS, monitoring, security tools)?",
      "Is source code in shared repositories that need to be separated?",
      "Are there shared authentication/identity systems for employees?"
    ],
    "platform_add_on": [
      "How compatible are the product architectures (tech stacks, cloud providers)?",
      "Can the products be integrated at the API level for cross-selling?",
      "Is there engineering team overlap or complementary skill sets?",
      "Can CI/CD and infrastructure be consolidated?",
      "Are there shared customer segments that benefit from product bundling?",
      "Can customer data be unified for a 360-degree customer view?"
    ],
    "turnaround": [
      "What is the level of technical debt and its impact on engineering velocity?",
      "Is the product on a supported technology stack with active community/vendor support?",
      "What is the test coverage and how reliable is the deployment pipeline?",
      "Is SOC 2 achieved, and if not, what is the gap?",
      "What is the cloud cost trajectory — is it sustainable at current growth rates?",
      "Are there data privacy or security vulnerabilities that need immediate attention?",
      "What is the customer churn rate and is it driven by product issues?"
    ]
  }
}
```

---

#### Template 6: General / Fallback

**File:** `data/industry_templates/general.json`

This template is used when the company's industry does not match any of the five specific templates, or when industry is unknown. It provides cross-industry averages and general enterprise systems that apply to any company.

```json
{
  "template_id": "general_cross_industry_midmarket",
  "industry": "general",
  "sub_industry": null,
  "size_tier": "midmarket",
  "version": "1.0",
  "last_updated": "2026-02",
  "provenance": "Cross-industry averages compiled from Gartner IT Key Metrics 2025, Computer Economics IT Spending & Staffing Benchmarks 2024/2025, Flexera State of the Cloud Report 2024, ISG Outsourcing Index 2024, Productiv SaaS Benchmark Report 2024",

  "expected_systems": {
    "industry_critical": [],
    "industry_common": [],
    "general_enterprise": [
      {
        "category": "erp_gl",
        "description": "Enterprise resource planning — general ledger, AP/AR, financial reporting, procurement, inventory (if applicable).",
        "common_vendors": ["NetSuite", "SAP", "Microsoft Dynamics 365", "Sage Intacct", "Oracle Cloud ERP", "QuickBooks Enterprise"],
        "criticality": "high",
        "typical_cost_range": "$100K-$500K/year",
        "migration_complexity": "medium",
        "notes": "Core financial system. NetSuite and Sage Intacct common at midmarket. Migration is a 6-18 month project depending on complexity."
      },
      {
        "category": "crm",
        "description": "Customer relationship management — sales pipeline, customer tracking, forecasting, customer service.",
        "common_vendors": ["Salesforce", "HubSpot", "Microsoft Dynamics 365", "Zoho CRM"],
        "criticality": "high",
        "typical_cost_range": "$30K-$200K/year",
        "migration_complexity": "low",
        "notes": "Salesforce dominant at midmarket and up. HubSpot common for SMB and marketing-led organizations."
      },
      {
        "category": "hcm_payroll",
        "description": "Human capital management — payroll, benefits administration, time and attendance, recruiting, performance management.",
        "common_vendors": ["ADP", "Paylocity", "UKG", "Workday", "Paychex", "Rippling", "BambooHR"],
        "criticality": "high",
        "typical_cost_range": "$50K-$250K/year",
        "migration_complexity": "low",
        "notes": "Payroll is critical — errors are highly visible. ADP dominant at midmarket."
      },
      {
        "category": "email_collaboration",
        "description": "Email, calendaring, instant messaging, video conferencing, file sharing.",
        "common_vendors": ["Microsoft 365", "Google Workspace"],
        "criticality": "high",
        "typical_cost_range": "$30K-$200K/year",
        "migration_complexity": "low",
        "notes": "M365 dominant in most industries. Google Workspace more common in tech. Tenant migration in carve-outs is a standard project."
      },
      {
        "category": "identity_access_management",
        "description": "Single sign-on, multi-factor authentication, directory services, user lifecycle management.",
        "common_vendors": ["Microsoft Entra ID (Azure AD)", "Okta", "JumpCloud", "Google Identity"],
        "criticality": "high",
        "typical_cost_range": "$20K-$120K/year",
        "migration_complexity": "medium",
        "notes": "Foundation of security posture. MFA enforcement is baseline expectation. SSO reduces password fatigue and improves security."
      },
      {
        "category": "endpoint_security",
        "description": "Endpoint detection and response, antivirus, device management, mobile device management.",
        "common_vendors": ["CrowdStrike", "SentinelOne", "Microsoft Defender for Endpoint", "Carbon Black"],
        "criticality": "high",
        "typical_cost_range": "$25K-$120K/year",
        "migration_complexity": "low",
        "notes": "EDR is now the baseline — traditional antivirus is no longer sufficient. Agent deployment typically straightforward."
      },
      {
        "category": "backup_disaster_recovery",
        "description": "Data backup, business continuity planning, disaster recovery.",
        "common_vendors": ["Veeam", "Commvault", "Rubrik", "Datto", "Druva"],
        "criticality": "high",
        "typical_cost_range": "$30K-$150K/year",
        "migration_complexity": "low",
        "notes": "RTO and RPO should be defined for critical systems. Annual DR testing is a best practice."
      },
      {
        "category": "itsm_service_desk",
        "description": "IT service management — incident management, change management, service requests, asset management.",
        "common_vendors": ["ServiceNow", "Jira Service Management", "Freshservice", "ManageEngine", "Zendesk"],
        "criticality": "medium",
        "typical_cost_range": "$15K-$80K/year",
        "migration_complexity": "low",
        "notes": "Maturity varies widely at midmarket. Some organizations still use shared inboxes or informal processes."
      },
      {
        "category": "network_infrastructure",
        "description": "Firewalls, switches, wireless access points, VPN, SD-WAN.",
        "common_vendors": ["Palo Alto Networks", "Fortinet", "Cisco Meraki", "Aruba (HPE)"],
        "criticality": "high",
        "typical_cost_range": "$30K-$150K/year",
        "migration_complexity": "medium",
        "notes": "SD-WAN adoption growing for multi-site organizations. Firewall management is often outsourced."
      },
      {
        "category": "bi_analytics",
        "description": "Business intelligence, reporting, dashboards, data visualization.",
        "common_vendors": ["Power BI", "Tableau", "Looker (Google)", "Domo", "Sisense"],
        "criticality": "medium",
        "typical_cost_range": "$20K-$100K/year",
        "migration_complexity": "low",
        "notes": "Power BI dominant at M365 shops. Self-service BI adoption is a maturity indicator."
      }
    ]
  },

  "expected_metrics": {
    "it_pct_revenue": {
      "low": 2.5,
      "typical": 3.5,
      "high": 5.5,
      "unit": "%",
      "source": "Gartner IT Key Metrics Data 2025 — Cross-Industry Average",
      "notes": "Cross-industry average. Actual varies significantly by industry — technology and financial services are highest, manufacturing lowest."
    },
    "it_staff_per_100_employees": {
      "low": 2.0,
      "typical": 4.0,
      "high": 7.0,
      "unit": "ratio",
      "source": "Gartner IT Key Metrics 2025 — Cross-Industry; Computer Economics 2024/2025",
      "notes": "Cross-industry average. Technology companies skew much higher. Manufacturing skews lower."
    },
    "app_count_per_100_employees": {
      "low": 8,
      "typical": 16,
      "high": 28,
      "unit": "count",
      "source": "Productiv SaaS Benchmark Report 2024 — Cross-Industry",
      "notes": "Includes SaaS and on-prem applications. SaaS sprawl is increasingly common."
    },
    "it_cost_per_employee": {
      "low": 7000,
      "typical": 12000,
      "high": 18000,
      "unit": "USD",
      "source": "Computer Economics IT Spending & Staffing Benchmarks 2024/2025 — Cross-Industry",
      "notes": "Cross-industry average. All IT operating expense divided by total headcount."
    },
    "security_pct_it_budget": {
      "low": 5,
      "typical": 9,
      "high": 14,
      "unit": "%",
      "source": "Gartner Security & Risk Management Survey 2024",
      "notes": "Cross-industry average. Regulated industries (financial services, healthcare) typically higher."
    },
    "cloud_adoption_pct": {
      "low": 25,
      "typical": 45,
      "high": 65,
      "unit": "%",
      "source": "Flexera State of the Cloud Report 2024",
      "notes": "Percentage of workloads in public or private cloud. Technology companies highest, manufacturing lowest."
    },
    "outsourcing_pct": {
      "low": 10,
      "typical": 25,
      "high": 45,
      "unit": "%",
      "source": "ISG Outsourcing Index 2024",
      "notes": "Percentage of IT functions outsourced. Smaller companies tend to outsource more."
    },
    "tech_refresh_cycle_years": {
      "low": 3,
      "typical": 5,
      "high": 7,
      "unit": "years",
      "source": "Gartner Infrastructure & Operations Survey 2024",
      "notes": "Standard hardware refresh cycle. End-user devices (laptops) typically 3-4 years. Servers/infrastructure 5-7 years."
    }
  },

  "expected_organization": {
    "typical_roles": [
      {"role": "CIO / IT Director / VP IT", "category": "leadership", "typical_count": "1", "notes": "Title varies by company size and culture. May report to CEO, CFO, or COO."},
      {"role": "Infrastructure / Network Admin", "category": "infrastructure", "typical_count": "1-3", "notes": "Manages servers, network, cloud infrastructure, telecom."},
      {"role": "Application Admin / Developer", "category": "applications", "typical_count": "1-3", "notes": "Supports ERP, CRM, and other business applications."},
      {"role": "Help Desk / Service Desk", "category": "service_desk", "typical_count": "1-3", "notes": "Tier 1 user support. May be outsourced at smaller midmarket."},
      {"role": "Security Analyst / CISO", "category": "security", "typical_count": "0-1", "notes": "Dedicated security role less common at midmarket. Often outsourced or combined with infrastructure."},
      {"role": "DBA / Report Writer", "category": "data", "typical_count": "0-1", "notes": "Database administration and business reporting."},
      {"role": "Project Manager", "category": "project_management", "typical_count": "0-1", "notes": "Dedicated IT PM uncommon at midmarket. Often a shared role."}
    ],
    "typical_outsourcing": [
      {"function": "Security monitoring / SIEM", "frequency": "very_common", "typical_model": "MSSP"},
      {"function": "Help desk / Tier 1 support", "frequency": "common", "typical_model": "MSP"},
      {"function": "Network / infrastructure management", "frequency": "common", "typical_model": "MSP"},
      {"function": "Cloud management", "frequency": "common", "typical_model": "MSP"},
      {"function": "Application development", "frequency": "occasional", "typical_model": "staff_augmentation"},
      {"function": "Backup / DR management", "frequency": "occasional", "typical_model": "co-managed"}
    ],
    "typical_it_headcount_range": {
      "min": 5,
      "max": 20,
      "notes": "For a 200-800 employee midmarket company. Cross-industry average. Actual varies significantly by industry."
    }
  },

  "typical_risks": [
    {
      "risk": "Aging infrastructure — servers, network equipment, or endpoints past refresh cycle",
      "frequency": "common",
      "typical_severity": "medium",
      "typical_cost_impact": "$200K-$800K for infrastructure refresh",
      "deal_relevance": "Deferred capital investment that will appear in post-close budgets."
    },
    {
      "risk": "No formal cybersecurity program — no dedicated security role, missing basic controls",
      "frequency": "common",
      "typical_severity": "high",
      "typical_cost_impact": "$200K-$600K for security program buildout",
      "deal_relevance": "Security gaps create breach exposure and may trigger cyber insurance issues."
    },
    {
      "risk": "Key person dependency — single IT person or small team with no documentation",
      "frequency": "very_common",
      "typical_severity": "high",
      "typical_cost_impact": "$200K-$500K in transition risk",
      "deal_relevance": "Loss of key IT staff post-close can disrupt operations and slow integration."
    },
    {
      "risk": "Shadow IT — undocumented SaaS applications with company data",
      "frequency": "very_common",
      "typical_severity": "medium",
      "typical_cost_impact": "$50K-$200K for SaaS rationalization",
      "deal_relevance": "Unmanaged SaaS creates data governance and cost control issues."
    },
    {
      "risk": "No disaster recovery testing or inadequate business continuity plan",
      "frequency": "common",
      "typical_severity": "high",
      "typical_cost_impact": "$100K-$300K for DR program establishment",
      "deal_relevance": "Untested DR means unknown recovery time in a disaster. Critical for business continuity."
    },
    {
      "risk": "ERP or critical application on unsupported version",
      "frequency": "common",
      "typical_severity": "medium",
      "typical_cost_impact": "$300K-$1.5M for upgrade or migration",
      "deal_relevance": "Unsupported software receives no security patches, creating vulnerability exposure."
    }
  ],

  "core_workflows": [
    {
      "workflow_id": "procure_to_pay",
      "name": "Procure to Pay",
      "description": "Purchase requisition through vendor payment. Universal business workflow applicable to all industries.",
      "steps": [
        {"step": "Purchase Requisition", "systems": ["erp_gl"], "manual_common": true, "manual_note": "Small companies may use email or spreadsheet-based approval"},
        {"step": "Purchase Order", "systems": ["erp_gl"], "manual_common": false, "manual_note": null},
        {"step": "Receiving / Goods Receipt", "systems": ["erp_gl"], "manual_common": true, "manual_note": "Three-way match (PO, receipt, invoice) may be manual"},
        {"step": "Invoice Processing", "systems": ["erp_gl"], "manual_common": true, "manual_note": "AP invoice processing often involves manual data entry"},
        {"step": "Payment", "systems": ["erp_gl"], "manual_common": false, "manual_note": null}
      ],
      "key_integrations": [
        {"from": "erp_gl", "to": "email_collaboration", "type": "API", "criticality": "medium"},
        {"from": "erp_gl", "to": "bi_analytics", "type": "batch", "criticality": "medium"}
      ]
    },
    {
      "workflow_id": "hire_to_retire",
      "name": "Hire to Retire",
      "description": "Employee lifecycle from recruiting and onboarding through termination and offboarding. Includes IT provisioning and deprovisioning.",
      "steps": [
        {"step": "Recruiting / Offer", "systems": ["hcm_payroll"], "manual_common": true, "manual_note": "Interview scheduling and decision-making are manual"},
        {"step": "Onboarding / IT Provisioning", "systems": ["hcm_payroll", "identity_access_management", "itsm_service_desk"], "manual_common": true, "manual_note": "IT provisioning (accounts, devices, access) often manual at midmarket"},
        {"step": "Ongoing HR / Payroll", "systems": ["hcm_payroll"], "manual_common": false, "manual_note": null},
        {"step": "Termination / IT Deprovisioning", "systems": ["hcm_payroll", "identity_access_management"], "manual_common": true, "manual_note": "Timely access revocation is critical for security. Often delayed at midmarket."}
      ],
      "key_integrations": [
        {"from": "hcm_payroll", "to": "identity_access_management", "type": "API", "criticality": "high"},
        {"from": "hcm_payroll", "to": "erp_gl", "type": "batch", "criticality": "high"},
        {"from": "identity_access_management", "to": "email_collaboration", "type": "real_time", "criticality": "high"}
      ]
    },
    {
      "workflow_id": "incident_management",
      "name": "IT Incident Management",
      "description": "IT incident detection, response, and resolution. Foundation of IT operations and service delivery.",
      "steps": [
        {"step": "Incident Detection / Reporting", "systems": ["itsm_service_desk", "endpoint_security", "monitoring_observability"], "manual_common": true, "manual_note": "Users report issues via email, phone, or portal"},
        {"step": "Triage / Assignment", "systems": ["itsm_service_desk"], "manual_common": true, "manual_note": "Ticket routing and priority assessment"},
        {"step": "Investigation / Resolution", "systems": ["itsm_service_desk"], "manual_common": true, "manual_note": "Troubleshooting and resolution require human expertise"},
        {"step": "Closure / Documentation", "systems": ["itsm_service_desk"], "manual_common": true, "manual_note": "Knowledge base article creation often neglected"}
      ],
      "key_integrations": [
        {"from": "endpoint_security", "to": "itsm_service_desk", "type": "API", "criticality": "medium"},
        {"from": "identity_access_management", "to": "itsm_service_desk", "type": "API", "criticality": "medium"}
      ]
    }
  ],

  "deal_lens_considerations": {
    "growth": [
      "Can the ERP and core systems scale with 2-3x revenue growth?",
      "Is the IT infrastructure (network, compute, storage) sized for growth?",
      "Is there an IT leader capable of scaling the function?",
      "Are vendor contracts flexible enough to accommodate growth (no caps, reasonable pricing)?",
      "Is the cybersecurity posture adequate for a larger, more visible organization?"
    ],
    "carve_out": [
      "What systems are shared with the parent company?",
      "What TSA services are needed and for how long?",
      "What is the Day 1 readiness plan for standalone IT operations?",
      "Which vendor contracts need to be assigned or renegotiated?",
      "Is there a dedicated IT team or does the carve-out need to hire?",
      "How is data separated from the parent's systems?"
    ],
    "platform_add_on": [
      "Are the target and acquirer on the same ERP and core business systems?",
      "What is the integration timeline and cost to consolidate systems?",
      "Can email and collaboration be consolidated quickly (quick win)?",
      "Are there identity and access management systems that need to be merged?",
      "What cost synergies are achievable through license consolidation?"
    ],
    "turnaround": [
      "What is the overall IT maturity level — is there a functioning IT organization?",
      "Are there immediate security risks that need remediation?",
      "Is the infrastructure stable or are there reliability issues?",
      "Are critical business applications supported and current?",
      "Is there adequate IT documentation (network diagrams, asset inventory, runbooks)?",
      "What is the IT team morale and retention risk?"
    ]
  }
}
```

---

### Template Loader

**File:** `stores/industry_templates.py`

```python
"""
Industry Template Store

Loads, validates, and provides access to industry template JSON files.
Templates are reference data — versioned, sourced, deterministic. No LLM calls.

Usage:
    from stores.industry_templates import IndustryTemplateStore

    store = IndustryTemplateStore()
    template = store.get_template("insurance", "p_and_c", "midmarket")
    systems = store.get_expected_systems("insurance", "midmarket")
    metrics = store.get_expected_metrics("insurance", "midmarket")
    workflows = store.get_workflows("insurance")
    deal_lens = store.get_deal_lens("insurance", "growth")
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent.parent / "data" / "industry_templates"


@dataclass
class ExpectedSystem:
    """A system expected in a given industry + size tier."""
    category: str
    description: str
    common_vendors: List[str]
    criticality: str  # critical, high, medium
    typical_cost_range: str = ""
    migration_complexity: str = ""
    notes: str = ""


@dataclass
class MetricRange:
    """A benchmark metric with low/typical/high range and source."""
    low: float
    typical: float
    high: float
    unit: str
    source: str
    notes: str = ""


@dataclass
class WorkflowStep:
    """A step within a business workflow."""
    step: str
    systems: List[str]
    manual_common: bool = False
    manual_note: Optional[str] = None


@dataclass
class WorkflowIntegration:
    """An integration between systems within a workflow."""
    from_system: str
    to_system: str
    type: str  # real_time, API, file, batch, manual
    criticality: str  # critical, high, medium


@dataclass
class WorkflowTemplate:
    """A core business workflow definition."""
    workflow_id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    key_integrations: List[WorkflowIntegration]


@dataclass
class IndustryTemplate:
    """Complete industry template with all sections."""
    template_id: str
    industry: str
    sub_industry: Optional[str]
    size_tier: str
    version: str
    last_updated: str
    provenance: str
    expected_systems: Dict[str, List[ExpectedSystem]]
    expected_metrics: Dict[str, MetricRange]
    expected_organization: Dict[str, Any]
    typical_risks: List[Dict[str, Any]]
    core_workflows: List[WorkflowTemplate]
    deal_lens_considerations: Dict[str, List[str]]
    _raw: Dict[str, Any] = field(default_factory=dict, repr=False)


class IndustryTemplateStore:
    """
    Loads and provides access to industry template JSON files.

    Templates are loaded lazily on first access and cached in memory.
    Fallback chain: exact match -> industry-level -> general.
    """

    def __init__(self, template_dir: Optional[Path] = None):
        self._template_dir = template_dir or TEMPLATE_DIR
        self._cache: Dict[str, IndustryTemplate] = {}
        self._loaded = False

    def _ensure_loaded(self) -> None:
        """Load all templates from disk if not already loaded."""
        if self._loaded:
            return
        for json_file in self._template_dir.glob("*.json"):
            try:
                raw = json.loads(json_file.read_text(encoding="utf-8"))
                template = self._parse_template(raw)
                self._cache[template.template_id] = template
                # Also index by industry for fallback
                industry_key = template.industry
                if industry_key not in self._cache:
                    self._cache[f"_industry_{industry_key}"] = template
            except Exception as e:
                logger.error(f"Failed to load template {json_file}: {e}")
        self._loaded = True

    def _parse_template(self, raw: Dict[str, Any]) -> IndustryTemplate:
        """Parse raw JSON into IndustryTemplate dataclass."""
        # Parse expected systems
        expected_systems = {}
        for tier_name, systems_list in raw.get("expected_systems", {}).items():
            expected_systems[tier_name] = [
                ExpectedSystem(
                    category=s["category"],
                    description=s["description"],
                    common_vendors=s["common_vendors"],
                    criticality=s["criticality"],
                    typical_cost_range=s.get("typical_cost_range", ""),
                    migration_complexity=s.get("migration_complexity", ""),
                    notes=s.get("notes", ""),
                )
                for s in systems_list
            ]

        # Parse expected metrics
        expected_metrics = {}
        for key, m in raw.get("expected_metrics", {}).items():
            expected_metrics[key] = MetricRange(
                low=m["low"],
                typical=m["typical"],
                high=m["high"],
                unit=m["unit"],
                source=m["source"],
                notes=m.get("notes", ""),
            )

        # Parse workflows
        workflows = []
        for w in raw.get("core_workflows", []):
            steps = [
                WorkflowStep(
                    step=s["step"],
                    systems=s["systems"],
                    manual_common=s.get("manual_common", False),
                    manual_note=s.get("manual_note"),
                )
                for s in w.get("steps", [])
            ]
            integrations = [
                WorkflowIntegration(
                    from_system=i["from"],
                    to_system=i["to"],
                    type=i["type"],
                    criticality=i["criticality"],
                )
                for i in w.get("key_integrations", [])
            ]
            workflows.append(WorkflowTemplate(
                workflow_id=w["workflow_id"],
                name=w["name"],
                description=w["description"],
                steps=steps,
                key_integrations=integrations,
            ))

        return IndustryTemplate(
            template_id=raw["template_id"],
            industry=raw["industry"],
            sub_industry=raw.get("sub_industry"),
            size_tier=raw.get("size_tier", "midmarket"),
            version=raw.get("version", "1.0"),
            last_updated=raw.get("last_updated", ""),
            provenance=raw.get("provenance", ""),
            expected_systems=expected_systems,
            expected_metrics=expected_metrics,
            expected_organization=raw.get("expected_organization", {}),
            typical_risks=raw.get("typical_risks", []),
            core_workflows=workflows,
            deal_lens_considerations=raw.get("deal_lens_considerations", {}),
            _raw=raw,
        )

    def _resolve_template(
        self, industry: str, sub_industry: Optional[str], size_tier: str
    ) -> IndustryTemplate:
        """
        Resolve the best matching template using the fallback chain:
        1. Exact match: {industry}_{sub_industry}_{size_tier}
        2. Industry + size: {industry}_*_{size_tier} (first match)
        3. Industry-level: any template for this industry
        4. General fallback: general template
        5. Never empty: raise if no general template exists
        """
        self._ensure_loaded()

        # 1. Try exact match
        if sub_industry:
            exact_id = f"{industry}_{sub_industry}_{size_tier}"
            if exact_id in self._cache:
                return self._cache[exact_id]

        # 2. Try industry-level match
        industry_key = f"_industry_{industry}"
        if industry_key in self._cache:
            return self._cache[industry_key]

        # 3. Fallback to general
        general_key = "_industry_general"
        if general_key in self._cache:
            logger.info(
                f"No template for {industry}/{sub_industry}/{size_tier}, "
                f"falling back to general template"
            )
            return self._cache[general_key]

        # 4. Should never reach here if general.json exists
        raise ValueError(
            f"No template found for {industry}/{sub_industry}/{size_tier} "
            f"and no general fallback available"
        )

    # === Public API ===

    def get_template(
        self,
        industry: str,
        sub_industry: Optional[str] = None,
        size_tier: str = "midmarket",
    ) -> IndustryTemplate:
        """
        Load best-matching template.
        Falls back: exact -> industry-level -> general.
        """
        return self._resolve_template(industry, sub_industry, size_tier)

    def get_expected_systems(
        self, industry: str, size_tier: str = "midmarket"
    ) -> List[ExpectedSystem]:
        """
        Get flat list of all expected systems for tech stack comparison.
        Combines industry_critical + industry_common + general_enterprise.
        """
        template = self._resolve_template(industry, None, size_tier)
        all_systems = []
        for tier in ["industry_critical", "industry_common", "general_enterprise"]:
            all_systems.extend(template.expected_systems.get(tier, []))
        return all_systems

    def get_expected_metrics(
        self, industry: str, size_tier: str = "midmarket"
    ) -> Dict[str, MetricRange]:
        """Get benchmark metric ranges for the industry."""
        template = self._resolve_template(industry, None, size_tier)
        return template.expected_metrics

    def get_workflows(self, industry: str) -> List[WorkflowTemplate]:
        """Get core business workflow definitions."""
        template = self._resolve_template(industry, None, "midmarket")
        return template.core_workflows

    def get_deal_lens(self, industry: str, lens: str) -> List[str]:
        """
        Get deal-lens-specific considerations.

        Args:
            industry: Industry code
            lens: One of 'growth', 'carve_out', 'platform_add_on', 'turnaround'

        Returns:
            List of consideration strings. Empty list if lens not found.
        """
        template = self._resolve_template(industry, None, "midmarket")
        return template.deal_lens_considerations.get(lens, [])

    def list_available_templates(self) -> List[Dict[str, str]]:
        """List all available templates with their metadata."""
        self._ensure_loaded()
        return [
            {
                "template_id": t.template_id,
                "industry": t.industry,
                "sub_industry": t.sub_industry or "",
                "size_tier": t.size_tier,
                "version": t.version,
                "last_updated": t.last_updated,
            }
            for key, t in self._cache.items()
            if not key.startswith("_")
        ]
```

---

### Fallback Strategy

The template resolution follows a strict fallback chain to ensure a template is always returned:

| Priority | Match Condition | Example |
|----------|----------------|---------|
| 1 | Exact: `{industry}_{sub_industry}_{size_tier}` | `insurance_p_and_c_midmarket` |
| 2 | Industry-level: any template for the given `industry` | `insurance` (any sub-industry/size) |
| 3 | General fallback: the `general` template | `general_cross_industry_midmarket` |
| 4 | Error | Only if `general.json` is missing (installation error) |

**Default size tier:** If `size_tier` is not provided, default to `"midmarket"` — the most common PE deal size.

**Never return empty:** Every call to `get_template()`, `get_expected_systems()`, `get_expected_metrics()`, `get_workflows()`, and `get_deal_lens()` returns data. The general template provides cross-industry baselines for any unknown industry.

---

### Versioning

- Each template file includes `version` (semver string) and `last_updated` (YYYY-MM) fields.
- Templates are JSON files stored in `data/industry_templates/` — editable by domain experts without code changes.
- Template changes do not require code deployment — only file replacement and application restart (or cache invalidation if hot-reload is implemented).
- Version history is tracked via git (the JSON files are committed to the repository).
- Annual review process: all templates should be reviewed and updated at least annually to reflect current vendor landscapes and benchmark data.

---

## Integration with Existing Modules

### benchmark_library.py Alignment

The template `expected_metrics` and the existing `BENCHMARK_LIBRARY` serve related but distinct purposes:

| Aspect | `BENCHMARK_LIBRARY` | Template `expected_metrics` |
|--------|---------------------|---------------------------|
| Purpose | Point-lookup by metric/industry/size | Complete metric set for an industry context |
| Granularity | Revenue-band size tiers (0-50M, 50-100M) | Spec 01 size tiers (small, midmarket, large) |
| Coverage | 7 metrics, sparse industry coverage | 8+ metrics per template, complete per industry |
| Consumed by | `assess_against_benchmark()` function | Spec 04 (benchmark engine), Spec 05 (UI) |

**Resolution rule:** When both sources have data for the same metric/industry, the benchmark engine (Spec 04) uses the template value as primary and benchmark_library as supplementary context. Template values are curated per-industry; benchmark_library values provide broader coverage.

### industry_application_considerations.py Alignment

The template `expected_systems` incorporates and extends the `expected_applications` from industry_application_considerations.py:

| Aspect | `industry_application_considerations.py` | Template `expected_systems` |
|--------|----------------------------------------|---------------------------|
| Purpose | Discovery agent probing questions | Reference data for comparison |
| Format | Nested dicts with questions, vendors | Structured JSON with costs, complexity |
| Consumed by | Discovery agent prompts | Spec 04 (gap analysis), Spec 05 (UI) |

The two modules are complementary: the considerations module drives the discovery conversation, while the template provides the structured reference data for analysis and rendering.

---

## Benefits

- **Templates as data, not code** — Domain experts can update JSON files without writing Python. No code deployment needed for template changes.
- **Every metric has source citation** — Builds credibility with PE deal teams. Source fields are required and validated.
- **Deterministic rendering** — No LLM variance in "what is expected." The same template produces the same output every time.
- **Reusable across deals** — A midmarket P&C insurance template works for every midmarket P&C insurance deal. Learning accumulates in templates.
- **Fallback chain ensures coverage** — Even for niche industries without specific templates, the general template provides useful baseline data.
- **Extensible** — New industries can be added by creating a new JSON file. No code changes required.

---

## Expectations

| Requirement | Target |
|-------------|--------|
| Template load time | < 100ms (JSON file read + parse) |
| Industry coverage | Insurance, Healthcare, Financial Services, Manufacturing, Technology + General fallback |
| Expected systems per template | 3+ critical, 3+ common, 5+ general enterprise |
| Common vendors per system | 2+ real vendor/product names |
| Metrics per template | 4+ metrics with source citations |
| Workflows per template | 1+ workflows with 3+ steps |
| Deal lens coverage | All 4 lenses (growth, carve_out, platform_add_on, turnaround) |
| Source citation completeness | 100% — every metric has a non-empty source field |
| No LLM calls | Zero LLM invocations in any template operation |

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Benchmark data becomes stale | Medium | Medium | `version` and `last_updated` fields enable staleness detection. Annual review process documented. Template provenance field documents data sources for re-research. |
| Templates don't match specific sub-industry | High | Low | Fallback chain (specific -> industry -> general) ensures coverage. Sub-industry templates can be added incrementally based on deal volume. |
| Expected system lists too long or too short | Medium | Low | Split into three tiers: `industry_critical` (3-5 systems), `industry_common` (3-8 systems), `general_enterprise` (standard set). Tier structure guides focus. |
| Template maintenance burden grows | Medium | Medium | Start with 5+1 templates. Expand based on deal volume data. JSON format enables non-developer contributions. |
| Vendor lists become outdated | Medium | Low | Vendor lists are guidance, not exhaustive. Annual review process updates vendor mentions. Common vendors change slowly at midmarket. |
| Template schema changes break consumers | Low | High | Schema version field enables backward compatibility. Loader code validates required fields and provides defaults for optional fields. |

---

## Results Criteria

### Validation Tests

1. **Schema validation:** Every template JSON file passes schema validation — all required fields present and correctly typed.
2. **Completeness check:** Every template has:
   - `expected_systems` with at least 3 entries in `industry_critical` (except general, which has 0)
   - `expected_metrics` with at least 4 metrics
   - `core_workflows` with at least 1 workflow containing at least 3 steps
   - `deal_lens_considerations` with all 4 lenses (growth, carve_out, platform_add_on, turnaround)
3. **Source citation check:** Every entry in `expected_metrics` has a non-empty `source` field.
4. **Vendor coverage check:** Every entry in `expected_systems` has at least 2 entries in `common_vendors`.

### Loader Tests

5. **Exact match:** `get_template("insurance", "p_and_c", "midmarket")` returns the insurance template with `template_id == "insurance_p_and_c_midmarket"`.
6. **Industry fallback:** `get_template("insurance", "life", "midmarket")` returns the insurance template (no life sub-industry template exists, falls back to industry-level).
7. **General fallback:** `get_template("aerospace", None, "midmarket")` returns the general template.
8. **Default size tier:** `get_template("insurance")` defaults to `size_tier="midmarket"`.
9. **System retrieval:** `get_expected_systems("insurance", "midmarket")` returns a flat list combining all three system tiers.
10. **Metric retrieval:** `get_expected_metrics("insurance", "midmarket")` returns a dict with keys like `"it_pct_revenue"`.
11. **Workflow retrieval:** `get_workflows("insurance")` returns a list containing `WorkflowTemplate` objects.
12. **Deal lens retrieval:** `get_deal_lens("insurance", "growth")` returns a non-empty list of strings.
13. **No LLM calls:** No template operation invokes any LLM API.

### Performance Tests

14. **Load time:** Full template store initialization (all 6 JSON files) completes in under 100ms.
15. **Accessor time:** Individual `get_template()` calls after initialization complete in under 1ms (cache hit).
