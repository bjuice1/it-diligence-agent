# Spec 02: Industry Classification & Taxonomy

**Feature Area:** Business Context
**Status:** Draft
**Dependencies:** Spec 01 (Company Profile Extraction), FactStore, InventoryStore, `app_category_mappings.py`, `industry_application_considerations.py`
**Consumed by:** Spec 01 (populates `CompanyProfile.industry`), Spec 03 (Report Templates), Spec 04 (Benchmark Engine), Spec 05 (UI Views)

---

## Overview

Deterministic industry classification from multiple evidence signals. No LLM calls -- pure rule-based scoring. Same facts produce the same classification every run. The classifier consumes `FactStore` + `InventoryStore` data and produces a structured classification result that is consumed by the rest of the Business Context feature area.

The IT Due Diligence Agent already has significant industry awareness scattered across three locations:

1. **`stores/app_category_mappings.py`** -- 966+ known applications with `category="industry_vertical"` entries tagged by vendor description (Duck Creek = "Insurance software suite", Epic = "Healthcare EHR system", Rockwell = "Industrial automation and MES"). These mappings identify which applications are industry-specific but do not formally map each application to an industry key.
2. **`prompts/shared/industry_application_considerations.py`** -- `INDUSTRY_APPLICATION_CONSIDERATIONS` dict with per-industry trigger word lists, expected applications, compliance drivers, and diligence considerations for healthcare, financial_services, manufacturing, insurance, and more. Includes `detect_industry_from_text()` which counts trigger word hits but has no confidence scoring and no multi-signal aggregation.
3. **`tools_v2/session.py`** -- `INDUSTRY_HIERARCHY` dict defining display names and sub-industries for 16 industry keys. `DealContext` holds `industry`, `sub_industry`, `secondary_industries`, and `industry_confirmed` fields. Auto-detection requires 3+ trigger hits and produces a single string -- no confidence, no evidence trail, no secondary industries.

None of these locations produce a classification object with confidence scoring, evidence provenance, or multi-signal aggregation. The current `detect_industry_from_text()` is a single-signal classifier (trigger words only) with a binary threshold (3+ matches) and no transparency into why a classification was chosen.

This spec introduces a **deterministic multi-signal industry classifier** that:

- Aggregates six ranked evidence signal types into a weighted score per industry
- Produces a structured `IndustryClassification` object with confidence, evidence snippets, and signal breakdown
- Resolves ties and conflicts with explicit, documented rules
- Defaults gracefully when no signals exist
- Integrates with Spec 01's `CompanyProfile` by populating the `industry` `ProfileField` placeholder
- Makes zero LLM calls -- pure Python rule evaluation running in under 500ms

---

## Architecture

### New Files

| File | Purpose |
|------|---------|
| `services/industry_classifier.py` | `IndustryClassifier` service -- the classification engine that reads stores, evaluates signals, produces `IndustryClassification` |
| `stores/industry_taxonomy.py` | `INDUSTRY_TAXONOMY` definitions, `INDUSTRY_APP_INDUSTRY_MAP` (app-to-industry mapping), `REGULATORY_INDUSTRY_MAP`, `VENDOR_INDUSTRY_MAP`, `ROLE_INDUSTRY_MAP`, evidence signal dataclasses |

### Reads (Existing Files -- No Modifications)

| File | What is Read |
|------|-------------|
| `stores/app_category_mappings.py` | `APP_MAPPINGS` dict -- used to identify `category="industry_vertical"` entries and map them to industries via vendor/description text |
| `prompts/shared/industry_application_considerations.py` | `INDUSTRY_APPLICATION_CONSIDERATIONS` -- trigger word lists and expected application configs per industry |
| `stores/fact_store.py` | `FactStore.facts` -- all extracted facts, searched for regulatory keywords, trigger words, job titles, and organization patterns |
| `stores/inventory_store.py` | `InventoryStore` items -- application inventory cross-referenced against app category mappings for industry-vertical detection |

### Output

`IndustryClassification` dataclass consumed by:

- **Spec 01 (`services/profile_extractor.py`)** -- `ProfileExtractor` calls `IndustryClassifier.classify()` to populate `CompanyProfile.industry`, `CompanyProfile.sub_industry`, `CompanyProfile.secondary_industries`, and `CompanyProfile.industry_classification`
- **Spec 03 (Report Templates)** -- selects industry-specific report sections, compliance checklists, and expected-application gap analysis
- **Spec 04 (Benchmark Engine)** -- selects industry-appropriate benchmark cohorts for cost and maturity comparisons
- **Spec 05 (UI Views)** -- displays classification confidence, evidence snippets, and signal breakdown in the interactive dashboard

### Data Flow

```
                    +-----------------------+
                    |    Deal Setup (CLI)   |
                    |  DealContext.industry  |  <- User may specify industry
                    +-----------+-----------+
                                |
                                v
            +-------------------+-------------------+
            |                                       |
            v                                       v
   +------------------+                   +--------------------+
   |    FactStore     |                   |   InventoryStore   |
   | (fact_store.py)  |                   | (inventory_store)  |
   +--------+---------+                   +---------+----------+
            |                                       |
            |  regulatory keywords                  |  application names
            |  trigger words in evidence            |  vendor names
            |  job titles in org facts              |  enrichment.category
            |                                       |
            +-------------------+-------------------+
                                |
                                v
                    +------------------------+
                    |  IndustryClassifier     |  <- NEW (this spec)
                    | (industry_classifier)   |
                    +------------------------+
                    |  Reads:                 |
                    |  - app_category_mappings|
                    |  - industry_app_consid. |
                    |  - INDUSTRY_TAXONOMY    |
                    +------------+-----------+
                                 |
                                 v
                    +------------------------+
                    | IndustryClassification  |  <- NEW (this spec)
                    | - primary_industry      |
                    | - sub_industry          |
                    | - secondary_industries  |
                    | - confidence            |
                    | - evidence_snippets     |
                    | - signal_breakdown      |
                    +------------+-----------+
                                 |
              +------------------+------------------+
              |                  |                  |
              v                  v                  v
        Spec 01:           Spec 03/04:        Spec 05:
        ProfileExtractor   Templates +        UI Views
        populates          Benchmarks         (signal display)
        CompanyProfile
```

### Integration with ProfileExtractor (Spec 01)

The `ProfileExtractor.extract()` method calls the classifier to fill the industry placeholder on `CompanyProfile`:

```python
from services.industry_classifier import IndustryClassifier

class ProfileExtractor:
    def __init__(self, fact_store: FactStore, inventory_store: InventoryStore, deal_context: Any = None):
        self.fact_store = fact_store
        self.inventory_store = inventory_store
        self.deal_context = deal_context
        self._warnings: List[str] = []

    def extract(self) -> CompanyProfile:
        # ... extract other fields ...

        # Industry classification (Spec 02)
        classifier = IndustryClassifier(
            fact_store=self.fact_store,
            inventory_store=self.inventory_store,
        )
        classification = classifier.classify(deal_context=self.deal_context)

        industry_field = ProfileField(
            value=classification.primary_industry,
            confidence=_confidence_to_level(classification.confidence),
            provenance=classification.classification_method,
            source_fact_ids=[e.source_fact_id for e in classification.evidence_snippets],
            source_documents=list(set(
                e.source_document for e in classification.evidence_snippets
                if e.source_document
            )),
            inference_rationale=(
                f"Classified as {classification.primary_industry}"
                f" ({classification.sub_industry or 'no sub-industry'})"
                f" with confidence {classification.confidence:.2f}"
                f" via {classification.classification_method}"
            ),
        )

        profile = CompanyProfile(
            # ... other fields ...
            industry=industry_field,
            # ... other fields ...
        )

        # Attach full classification for downstream consumers
        profile.sub_industry = classification.sub_industry
        profile.secondary_industries = classification.secondary_industries
        profile.industry_classification = classification

        # Propagate warnings
        self._warnings.extend(classification.warnings)

        return profile


def _confidence_to_level(confidence: float) -> str:
    """Convert numeric confidence to ProfileField confidence level."""
    if confidence >= 0.8:
        return "high"
    elif confidence >= 0.5:
        return "medium"
    else:
        return "low"
```

---

## Specification

### 1. Industry Taxonomy

Defined in `stores/industry_taxonomy.py`. The taxonomy is a two-level hierarchy: **primary industry** and **sub-industry**. Every classification must resolve to one of these primary keys. Sub-industry is optional and determined when evidence supports it.

```python
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field


INDUSTRY_TAXONOMY: Dict[str, Dict] = {
    # =========================================================================
    # INSURANCE
    # =========================================================================
    "insurance": {
        "display_name": "Insurance",
        "sub_industries": {
            "p_and_c": {
                "display_name": "Property & Casualty",
                "indicators": [
                    "property", "casualty", "auto insurance", "homeowners",
                    "commercial lines", "personal lines", "workers comp",
                    "general liability", "commercial auto",
                ],
                "app_indicators": [
                    "duck creek", "guidewire", "majesco", "britecore",
                    "insurity", "snapsheet",
                ],
            },
            "life_annuity": {
                "display_name": "Life & Annuity",
                "indicators": [
                    "life insurance", "annuity", "universal life",
                    "term life", "whole life", "variable annuity",
                    "fixed annuity", "death benefit",
                ],
                "app_indicators": [
                    "fineos", "sapiens", "alis", "lidp",
                ],
            },
            "specialty": {
                "display_name": "Specialty (E&S, Surety, Title)",
                "indicators": [
                    "excess and surplus", "E&S", "surplus lines",
                    "surety bond", "title insurance", "professional liability",
                    "directors and officers", "D&O", "errors and omissions",
                ],
                "app_indicators": [],
            },
            "reinsurance": {
                "display_name": "Reinsurance",
                "indicators": [
                    "reinsurance", "retrocession", "treaty",
                    "facultative", "ceded premium", "assumed premium",
                ],
                "app_indicators": ["sapiens"],
            },
            "brokerage_mga": {
                "display_name": "Brokerage / MGA",
                "indicators": [
                    "broker", "MGA", "managing general agent",
                    "wholesale broker", "retail broker", "agency",
                    "book of business", "commission", "binding authority",
                ],
                "app_indicators": [
                    "applied systems", "applied epic", "vertafore",
                    "ams360", "sagitta",
                ],
            },
        },
    },

    # =========================================================================
    # HEALTHCARE
    # =========================================================================
    "healthcare": {
        "display_name": "Healthcare",
        "sub_industries": {
            "provider": {
                "display_name": "Provider (Hospital Systems, Physician Groups)",
                "indicators": [
                    "hospital", "physician", "clinic", "ambulatory",
                    "acute care", "inpatient", "outpatient", "surgery center",
                    "medical group", "health system",
                ],
                "app_indicators": [
                    "epic", "cerner", "meditech", "eclinicalworks",
                    "nextgen healthcare", "allscripts",
                ],
            },
            "payer": {
                "display_name": "Payer (Health Plans, TPA)",
                "indicators": [
                    "health plan", "TPA", "third party administrator",
                    "managed care", "HMO", "PPO", "Medicare Advantage",
                    "Medicaid managed care", "utilization management",
                    "claims adjudication",
                ],
                "app_indicators": ["healthedge", "facets", "amisys"],
            },
            "pharma_biotech": {
                "display_name": "Pharma & Biotech",
                "indicators": [
                    "pharmaceutical", "biotech", "drug development",
                    "clinical trial", "FDA approval", "GxP", "GMP",
                    "drug manufacturing", "API", "formulation",
                ],
                "app_indicators": ["veeva", "medidata", "oracle argus"],
            },
            "medtech_devices": {
                "display_name": "MedTech & Devices",
                "indicators": [
                    "medical device", "FDA 510(k)", "class II device",
                    "class III device", "device manufacturing", "implant",
                    "diagnostic equipment",
                ],
                "app_indicators": ["greenlight guru", "arena plm"],
            },
            "health_services": {
                "display_name": "Health Services (Staffing, Billing, IT)",
                "indicators": [
                    "healthcare staffing", "medical billing", "revenue cycle",
                    "health IT", "healthcare consulting", "locum tenens",
                    "telehealth platform",
                ],
                "app_indicators": ["waystar", "r1 rcm"],
            },
        },
    },

    # =========================================================================
    # FINANCIAL SERVICES
    # =========================================================================
    "financial_services": {
        "display_name": "Financial Services",
        "sub_industries": {
            "banking": {
                "display_name": "Banking (Commercial, Community)",
                "indicators": [
                    "bank", "banking", "commercial bank", "community bank",
                    "credit union", "deposits", "checking", "savings",
                    "FDIC insured", "national bank", "state chartered",
                ],
                "app_indicators": [
                    "fis", "fiserv", "jack henry", "temenos",
                    "finastra", "ncino",
                ],
            },
            "asset_management": {
                "display_name": "Asset Management (PE, Hedge, Wealth)",
                "indicators": [
                    "asset management", "wealth management",
                    "private equity", "hedge fund", "portfolio management",
                    "AUM", "assets under management", "registered investment advisor",
                    "family office",
                ],
                "app_indicators": [
                    "bloomberg", "charles river", "ss&c eze",
                    "black diamond", "orion",
                ],
            },
            "fintech_payments": {
                "display_name": "Fintech & Payments",
                "indicators": [
                    "fintech", "payment processing", "payment gateway",
                    "digital wallet", "mobile payments", "ACH",
                    "money transfer", "neobank",
                ],
                "app_indicators": ["stripe", "square", "adyen", "marqeta"],
            },
            "specialty_finance": {
                "display_name": "Specialty Finance (Leasing, Lending)",
                "indicators": [
                    "leasing", "equipment finance", "auto lending",
                    "consumer lending", "student loans", "factoring",
                    "commercial finance", "asset-based lending",
                ],
                "app_indicators": ["encompass", "blend", "ellie mae"],
            },
        },
    },

    # =========================================================================
    # MANUFACTURING
    # =========================================================================
    "manufacturing": {
        "display_name": "Manufacturing",
        "sub_industries": {
            "discrete": {
                "display_name": "Discrete (Automotive, Electronics, Aerospace)",
                "indicators": [
                    "discrete manufacturing", "assembly", "automotive",
                    "electronics manufacturing", "aerospace manufacturing",
                    "machining", "stamping", "injection molding",
                    "printed circuit board", "OEM",
                ],
                "app_indicators": [
                    "siemens plm", "ptc windchill", "dassault systemes",
                    "catia", "solidworks",
                ],
            },
            "process": {
                "display_name": "Process (Chemicals, Food, Pharma Mfg)",
                "indicators": [
                    "process manufacturing", "chemical manufacturing",
                    "food manufacturing", "batch processing", "formulation",
                    "blending", "refining", "continuous process",
                ],
                "app_indicators": [
                    "aveva", "wonderware", "osisoft pi",
                ],
            },
            "industrial": {
                "display_name": "Industrial (Heavy Equipment, Building Materials)",
                "indicators": [
                    "heavy equipment", "building materials", "industrial",
                    "construction equipment", "mining equipment",
                    "agricultural equipment",
                ],
                "app_indicators": [
                    "rockwell automation", "factorytalk", "plex",
                    "infor cloudsuite industrial",
                ],
            },
        },
    },

    # =========================================================================
    # TECHNOLOGY
    # =========================================================================
    "technology": {
        "display_name": "Technology",
        "sub_industries": {
            "saas_product": {
                "display_name": "SaaS / Product Company",
                "indicators": [
                    "SaaS", "software as a service", "ARR",
                    "annual recurring revenue", "MRR", "churn rate",
                    "product-led growth", "freemium",
                ],
                "app_indicators": [],
            },
            "it_services_consulting": {
                "display_name": "IT Services & Consulting",
                "indicators": [
                    "IT services", "managed services", "IT consulting",
                    "systems integrator", "MSP", "outsourcing",
                    "staff augmentation", "IT staffing",
                ],
                "app_indicators": [],
            },
            "infrastructure_hosting": {
                "display_name": "Infrastructure & Hosting",
                "indicators": [
                    "data center", "hosting", "colocation", "colo",
                    "cloud provider", "IaaS", "PaaS",
                ],
                "app_indicators": [],
            },
        },
    },

    # =========================================================================
    # PROFESSIONAL SERVICES
    # =========================================================================
    "professional_services": {
        "display_name": "Professional Services",
        "sub_industries": {
            "consulting_advisory": {
                "display_name": "Consulting & Advisory",
                "indicators": [
                    "consulting", "advisory", "management consulting",
                    "strategy consulting", "transformation",
                ],
                "app_indicators": [],
            },
            "legal": {
                "display_name": "Legal",
                "indicators": [
                    "law firm", "legal services", "litigation",
                    "corporate law", "partner", "associate attorney",
                ],
                "app_indicators": ["clio", "litify", "relativity"],
            },
            "accounting_tax": {
                "display_name": "Accounting & Tax",
                "indicators": [
                    "CPA firm", "accounting firm", "audit firm",
                    "tax preparation", "bookkeeping", "assurance",
                ],
                "app_indicators": ["caseware", "thomson reuters", "cch"],
            },
            "engineering": {
                "display_name": "Engineering",
                "indicators": [
                    "engineering firm", "civil engineering",
                    "structural engineering", "MEP", "surveying",
                ],
                "app_indicators": ["autodesk", "bentley", "revit"],
            },
        },
    },

    # =========================================================================
    # RETAIL & CONSUMER
    # =========================================================================
    "retail_consumer": {
        "display_name": "Retail & Consumer",
        "sub_industries": {
            "brick_and_mortar": {
                "display_name": "Brick & Mortar",
                "indicators": [
                    "retail stores", "brick and mortar", "physical stores",
                    "point of sale", "POS", "foot traffic",
                    "store operations", "store count",
                ],
                "app_indicators": [
                    "oracle retail", "lightspeed", "revel",
                ],
            },
            "ecommerce": {
                "display_name": "E-Commerce",
                "indicators": [
                    "ecommerce", "e-commerce", "online store",
                    "direct to consumer", "DTC", "fulfillment",
                    "cart abandonment", "conversion rate",
                ],
                "app_indicators": [
                    "shopify", "magento", "bigcommerce",
                ],
            },
            "omnichannel": {
                "display_name": "Omnichannel",
                "indicators": [
                    "omnichannel", "unified commerce",
                    "buy online pick up in store", "BOPIS",
                    "ship from store",
                ],
                "app_indicators": [
                    "manhattan associates", "blue yonder",
                ],
            },
            "consumer_brands": {
                "display_name": "Consumer Brands",
                "indicators": [
                    "consumer brand", "CPG", "consumer packaged goods",
                    "brand management", "retail distribution",
                ],
                "app_indicators": [],
            },
        },
    },

    # =========================================================================
    # ENERGY & UTILITIES
    # =========================================================================
    "energy_utilities": {
        "display_name": "Energy & Utilities",
        "sub_industries": {
            "oil_gas": {
                "display_name": "Oil & Gas",
                "indicators": [
                    "oil and gas", "upstream", "midstream", "downstream",
                    "drilling", "exploration", "refinery", "pipeline",
                    "petroleum", "natural gas",
                ],
                "app_indicators": ["petrel", "openworks", "aries"],
            },
            "utilities": {
                "display_name": "Utilities (Electric, Water, Gas)",
                "indicators": [
                    "electric utility", "water utility", "gas utility",
                    "regulated utility", "rate case", "PUC",
                    "public utility commission", "NERC", "distribution",
                    "transmission", "generation",
                ],
                "app_indicators": [
                    "oracle utilities", "itron", "sensus",
                ],
            },
            "renewables": {
                "display_name": "Renewables",
                "indicators": [
                    "renewable energy", "solar", "wind energy",
                    "battery storage", "EV charging", "clean energy",
                ],
                "app_indicators": [],
            },
        },
    },

    # =========================================================================
    # REAL ESTATE
    # =========================================================================
    "real_estate": {
        "display_name": "Real Estate",
        "sub_industries": {
            "commercial": {
                "display_name": "Commercial Real Estate",
                "indicators": [
                    "commercial real estate", "CRE", "office space",
                    "retail space", "industrial space", "lease management",
                    "tenant", "NOI", "net operating income", "cap rate",
                ],
                "app_indicators": ["yardi", "mri software", "argus"],
            },
            "residential": {
                "display_name": "Residential Real Estate",
                "indicators": [
                    "residential real estate", "homebuilder",
                    "multifamily", "apartment", "HOA",
                    "property management",
                ],
                "app_indicators": ["appfolio", "buildium", "realpage"],
            },
            "reit_property_management": {
                "display_name": "REIT / Property Management",
                "indicators": [
                    "REIT", "real estate investment trust",
                    "property management", "facilities management",
                ],
                "app_indicators": ["yardi", "mri software"],
            },
        },
    },

    # =========================================================================
    # LOGISTICS & DISTRIBUTION
    # =========================================================================
    "logistics_distribution": {
        "display_name": "Logistics & Distribution",
        "sub_industries": {
            "transportation": {
                "display_name": "Transportation (Trucking, Freight, Rail)",
                "indicators": [
                    "trucking", "freight", "rail", "shipping",
                    "carrier", "fleet", "dispatch", "load board",
                    "LTL", "FTL", "intermodal",
                ],
                "app_indicators": [
                    "tms", "mcleod", "trimble", "samsara",
                ],
            },
            "warehousing_3pl": {
                "display_name": "Warehousing & 3PL",
                "indicators": [
                    "warehouse", "3PL", "third party logistics",
                    "fulfillment center", "distribution center",
                    "pick and pack", "inventory management",
                ],
                "app_indicators": [
                    "manhattan associates", "blue yonder", "highjump",
                ],
            },
            "last_mile": {
                "display_name": "Last Mile",
                "indicators": [
                    "last mile", "delivery", "route optimization",
                    "courier", "parcel",
                ],
                "app_indicators": [],
            },
        },
    },

    # =========================================================================
    # MEDIA & ENTERTAINMENT
    # =========================================================================
    "media_entertainment": {
        "display_name": "Media & Entertainment",
        "sub_industries": {
            "publishing": {
                "display_name": "Publishing",
                "indicators": [
                    "publishing", "newspaper", "magazine", "book publisher",
                    "digital publishing", "content management",
                ],
                "app_indicators": [],
            },
            "broadcasting": {
                "display_name": "Broadcasting",
                "indicators": [
                    "broadcasting", "television", "radio",
                    "cable network", "streaming",
                ],
                "app_indicators": [],
            },
            "digital_media": {
                "display_name": "Digital Media",
                "indicators": [
                    "digital media", "ad tech", "programmatic",
                    "content platform", "social media",
                ],
                "app_indicators": [],
            },
        },
    },

    # =========================================================================
    # GENERAL (FALLBACK)
    # =========================================================================
    "general": {
        "display_name": "General / Unclassified",
        "sub_industries": {
            "conglomerate": {
                "display_name": "Conglomerate",
                "indicators": [
                    "conglomerate", "diversified", "holding company portfolio",
                    "multi-division", "business units",
                ],
                "app_indicators": [],
            },
            "holding_company": {
                "display_name": "Holding Company",
                "indicators": [
                    "holding company", "parent company", "subsidiary",
                    "portfolio company",
                ],
                "app_indicators": [],
            },
            "other": {
                "display_name": "Other",
                "indicators": [],
                "app_indicators": [],
            },
        },
    },
}
```

#### Taxonomy Design Principles

- **Primary industry keys** use `snake_case` and are stable identifiers referenced by Spec 03 templates, Spec 04 benchmark cohorts, and Spec 05 UI routing. They must never be renamed after release without a migration.
- **Sub-industry keys** are scoped within their parent and are also `snake_case`. They refine the primary industry for template selection and benchmark narrowing.
- **`indicators`** on sub-industries are trigger phrases searched in fact evidence and document content. They supplement (not replace) the broader industry triggers in `INDUSTRY_APPLICATION_CONSIDERATIONS`.
- **`app_indicators`** on sub-industries are normalized application name prefixes matched against inventory items and `APP_MAPPINGS` keys. They are used for sub-industry determination within a primary industry.
- **The `general` industry** is the fallback. Every classification must resolve to a primary industry; `general.other` is the lowest-confidence default.

---

### 2. Evidence Signal Hierarchy

The classifier evaluates six signal types, ranked by reliability. Each signal type produces zero or more `EvidenceSignal` objects, each carrying a confidence value and provenance tag.

Defined in `stores/industry_taxonomy.py`:

```python
@dataclass
class EvidenceSignal:
    """A single piece of evidence pointing to an industry classification."""
    industry: str                  # Primary industry key (e.g., "insurance")
    sub_industry: Optional[str]    # Sub-industry key if determinable (e.g., "p_and_c")
    signal_type: str               # One of the SIGNAL_TYPES keys below
    confidence: float              # 0.0 - 1.0, determined by signal type
    weight: float                  # Multiplier for scoring (default 1.0, increased for repeated signals)
    provenance: str                # "user_specified", "document_sourced", "inferred"
    description: str               # Human-readable description of this signal
    source_fact_id: str = ""       # Fact ID if sourced from a specific fact
    source_document: str = ""      # Document name if traceable
    source_text: str = ""          # The matched text (trigger word, app name, regulatory term, etc.)


# Signal type definitions with base confidence and provenance
SIGNAL_TYPES = {
    "user_specified": {
        "rank": 1,
        "base_confidence": 1.0,
        "provenance": "user_specified",
        "description": "User selected industry during deal setup via DealContext",
    },
    "regulatory": {
        "rank": 2,
        "base_confidence": 0.9,
        "provenance": "document_sourced",
        "description": "Regulatory or compliance framework references in documents",
    },
    "vertical_app": {
        "rank": 3,
        "base_confidence": 0.85,
        "provenance": "document_sourced",
        "description": "Industry-vertical application detected in inventory",
    },
    "trigger_word": {
        "rank": 4,
        "base_confidence": 0.7,
        "provenance": "inferred",
        "description": "Industry trigger words found in document content",
    },
    "vendor_name": {
        "rank": 5,
        "base_confidence": 0.6,
        "provenance": "inferred",
        "description": "Industry-specific vendor name detected in inventory",
    },
    "org_structure": {
        "rank": 6,
        "base_confidence": 0.5,
        "provenance": "inferred",
        "description": "Industry-specific job titles or org patterns in organization facts",
    },
}
```

#### Signal Type 1: User-Specified (confidence: 1.0, provenance: `"user_specified"`)

**Source:** `DealContext.industry` field from `tools_v2/session.py`, set when the user selects an industry during deal setup.

**Procedure:**
1. Check if `deal_context` is provided and `deal_context.industry` is a non-empty string.
2. Validate that the value exists as a key in `INDUSTRY_TAXONOMY`.
3. If valid, produce a single `EvidenceSignal` with `confidence=1.0`, `weight=10.0` (overwhelming weight to ensure it dominates).
4. If `deal_context.sub_industry` is also set, include it on the signal.
5. If `deal_context.industry_confirmed` is `True`, the signal is authoritative. If `False` (auto-detected in a prior session), treat as `confidence=0.95` to allow strong document evidence to surface warnings.

**Always wins when present.** This is the only signal that can produce `classification_method="user_specified"` on the output.

```python
def _collect_user_specified_signals(self, deal_context) -> List[EvidenceSignal]:
    signals = []
    if not deal_context:
        return signals

    industry = getattr(deal_context, 'industry', None)
    if not industry or industry not in INDUSTRY_TAXONOMY:
        return signals

    confirmed = getattr(deal_context, 'industry_confirmed', False)
    sub = getattr(deal_context, 'sub_industry', None)

    signals.append(EvidenceSignal(
        industry=industry,
        sub_industry=sub,
        signal_type="user_specified",
        confidence=1.0 if confirmed else 0.95,
        weight=10.0,
        provenance="user_specified",
        description=f"User specified industry: {industry}" + (f" ({sub})" if sub else ""),
    ))

    # Also carry forward secondary industries from DealContext
    for sec in getattr(deal_context, 'secondary_industries', []):
        if sec in INDUSTRY_TAXONOMY:
            signals.append(EvidenceSignal(
                industry=sec,
                sub_industry=None,
                signal_type="user_specified",
                confidence=0.5,  # Secondary industries get lower confidence
                weight=1.0,
                provenance="user_specified",
                description=f"User specified secondary industry: {sec}",
            ))

    return signals
```

#### Signal Type 2: Regulatory / Compliance Signals (confidence: 0.9, provenance: `"document_sourced"`)

**Source:** All facts in `FactStore`, searched for regulatory and compliance keywords in `item`, `details` (all values), and `evidence.exact_quote`.

**Regulatory-to-industry mapping** (defined in `stores/industry_taxonomy.py`):

```python
REGULATORY_INDUSTRY_MAP: Dict[str, Dict] = {
    # Healthcare
    "hipaa": {"industry": "healthcare", "sub_industry": None},
    "hitech": {"industry": "healthcare", "sub_industry": None},
    "phi": {"industry": "healthcare", "sub_industry": None},
    "protected health information": {"industry": "healthcare", "sub_industry": None},
    "meaningful use": {"industry": "healthcare", "sub_industry": "provider"},
    "mips": {"industry": "healthcare", "sub_industry": "provider"},
    "macra": {"industry": "healthcare", "sub_industry": "provider"},
    "21st century cures": {"industry": "healthcare", "sub_industry": None},
    "cms conditions of participation": {"industry": "healthcare", "sub_industry": "provider"},
    "fda 510(k)": {"industry": "healthcare", "sub_industry": "medtech_devices"},
    "gxp": {"industry": "healthcare", "sub_industry": "pharma_biotech"},

    # Insurance
    "naic": {"industry": "insurance", "sub_industry": None},
    "department of insurance": {"industry": "insurance", "sub_industry": None},
    "doi filing": {"industry": "insurance", "sub_industry": None},
    "state insurance regulation": {"industry": "insurance", "sub_industry": None},
    "risk-based capital": {"industry": "insurance", "sub_industry": None},
    "statutory accounting": {"industry": "insurance", "sub_industry": None},
    "admitted carrier": {"industry": "insurance", "sub_industry": None},
    "surplus lines": {"industry": "insurance", "sub_industry": "specialty"},

    # Financial Services
    "sox": {"industry": "financial_services", "sub_industry": None, "tag": "public_company"},
    "sarbanes-oxley": {"industry": "financial_services", "sub_industry": None, "tag": "public_company"},
    "glba": {"industry": "financial_services", "sub_industry": "banking"},
    "gramm-leach-bliley": {"industry": "financial_services", "sub_industry": "banking"},
    "finra": {"industry": "financial_services", "sub_industry": "asset_management"},
    "sec registration": {"industry": "financial_services", "sub_industry": "asset_management"},
    "occ": {"industry": "financial_services", "sub_industry": "banking"},
    "fdic": {"industry": "financial_services", "sub_industry": "banking"},
    "ffiec": {"industry": "financial_services", "sub_industry": "banking"},
    "bsa": {"industry": "financial_services", "sub_industry": "banking"},
    "aml": {"industry": "financial_services", "sub_industry": "banking"},
    "bank secrecy act": {"industry": "financial_services", "sub_industry": "banking"},

    # PCI-DSS maps to multiple possible industries
    "pci-dss": {"industry": "_multi", "candidates": ["financial_services", "retail_consumer"]},
    "pci dss": {"industry": "_multi", "candidates": ["financial_services", "retail_consumer"]},
    "payment card industry": {"industry": "_multi", "candidates": ["financial_services", "retail_consumer"]},

    # Manufacturing
    "osha": {"industry": "manufacturing", "sub_industry": None},
    "iso 9001": {"industry": "manufacturing", "sub_industry": None},
    "iatf 16949": {"industry": "manufacturing", "sub_industry": "discrete"},
    "as9100": {"industry": "manufacturing", "sub_industry": "discrete"},
    "iso 13485": {"industry": "healthcare", "sub_industry": "medtech_devices"},
    "epa compliance": {"industry": "manufacturing", "sub_industry": "process"},

    # Energy
    "nerc": {"industry": "energy_utilities", "sub_industry": "utilities"},
    "ferc": {"industry": "energy_utilities", "sub_industry": None},
    "puc": {"industry": "energy_utilities", "sub_industry": "utilities"},
    "public utility commission": {"industry": "energy_utilities", "sub_industry": "utilities"},
}
```

**Procedure:**
1. Iterate all facts in `FactStore`.
2. For each fact, build a searchable text block by concatenating: `fact.item`, all string values in `fact.details`, and `fact.evidence.get("exact_quote", "")`.
3. Normalize to lowercase.
4. For each key in `REGULATORY_INDUSTRY_MAP`, check if it appears in the text block (case-insensitive).
5. On match, produce an `EvidenceSignal` with `confidence=0.9`, `weight=1.0`, and provenance `"document_sourced"`.
6. For `_multi` entries (e.g., PCI-DSS), produce one signal per candidate industry with `confidence=0.7` (reduced because ambiguous).
7. For entries with a `tag` key (e.g., SOX -> `public_company`), add the tag to the classification warnings but still count the signal for the mapped industry.
8. Deduplicate: if the same regulatory term matches in multiple facts, produce only one signal but increase `weight` proportionally (1.0 + 0.5 per additional fact, capped at 3.0).

```python
def _collect_regulatory_signals(self) -> List[EvidenceSignal]:
    signals = []
    seen: Dict[str, List[str]] = {}  # reg_key -> [fact_ids]

    for fact in self.fact_store.facts:
        text_block = self._build_fact_text_block(fact).lower()
        for reg_key, mapping in REGULATORY_INDUSTRY_MAP.items():
            if reg_key in text_block:
                seen.setdefault(reg_key, []).append(fact.fact_id)

    for reg_key, fact_ids in seen.items():
        mapping = REGULATORY_INDUSTRY_MAP[reg_key]
        weight = min(3.0, 1.0 + 0.5 * (len(fact_ids) - 1))
        first_fact = self.fact_store.get_fact(fact_ids[0])

        if mapping["industry"] == "_multi":
            for candidate in mapping["candidates"]:
                signals.append(EvidenceSignal(
                    industry=candidate,
                    sub_industry=None,
                    signal_type="regulatory",
                    confidence=0.7,
                    weight=weight,
                    provenance="document_sourced",
                    description=f"Regulatory reference '{reg_key}' (ambiguous: {mapping['candidates']})",
                    source_fact_id=fact_ids[0],
                    source_document=first_fact.source_document if first_fact else "",
                    source_text=reg_key,
                ))
        else:
            signals.append(EvidenceSignal(
                industry=mapping["industry"],
                sub_industry=mapping.get("sub_industry"),
                signal_type="regulatory",
                confidence=0.9,
                weight=weight,
                provenance="document_sourced",
                description=f"Regulatory reference '{reg_key}' found in {len(fact_ids)} fact(s)",
                source_fact_id=fact_ids[0],
                source_document=first_fact.source_document if first_fact else "",
                source_text=reg_key,
            ))

            if mapping.get("tag"):
                self._tags.append(mapping["tag"])

    return signals

def _build_fact_text_block(self, fact) -> str:
    """Build searchable text from a fact's item, details, and evidence."""
    parts = [fact.item or ""]
    if fact.details:
        for val in fact.details.values():
            if isinstance(val, str):
                parts.append(val)
            elif isinstance(val, list):
                parts.extend(str(v) for v in val)
    if fact.evidence:
        parts.append(fact.evidence.get("exact_quote", ""))
        parts.append(fact.evidence.get("source_section", ""))
    return " ".join(parts)
```

#### Signal Type 3: Industry-Vertical Application Detection (confidence: 0.85, provenance: `"document_sourced"`)

**Source:** `InventoryStore` items cross-referenced against `APP_MAPPINGS` from `stores/app_category_mappings.py`.

**Procedure:**
1. Get all items from `InventoryStore` where `inventory_type == "application"`.
2. For each item, extract `data.get("name", "")` and normalize to lowercase.
3. Look up in `APP_MAPPINGS`. If found and `mapping.category == "industry_vertical"`, this is a vertical application.
4. Determine which industry this vertical app belongs to using `INDUSTRY_APP_INDUSTRY_MAP` (defined below).
5. Produce an `EvidenceSignal` with `confidence=0.85`.
6. Count total vertical apps per industry. The weight of each signal increases with count: `weight = 1.0 + 0.3 * (count_for_this_industry - 1)`, capped at `3.0`.
7. Also scan `FactStore` for facts with `domain == "applications"` where `fact.details` contains app names matching vertical apps.

**Application-to-industry mapping** (defined in `stores/industry_taxonomy.py`):

```python
# Maps normalized app names (from APP_MAPPINGS keys where category == "industry_vertical")
# to their industry. This bridges app_category_mappings.py (which has no industry field)
# to the industry taxonomy.
INDUSTRY_APP_INDUSTRY_MAP: Dict[str, Dict[str, str]] = {
    # Healthcare
    "epic": {"industry": "healthcare", "sub_industry": "provider"},
    "cerner": {"industry": "healthcare", "sub_industry": "provider"},
    "meditech": {"industry": "healthcare", "sub_industry": "provider"},
    "allscripts": {"industry": "healthcare", "sub_industry": "provider"},
    "athenahealth": {"industry": "healthcare", "sub_industry": "provider"},
    "veradigm": {"industry": "healthcare", "sub_industry": "provider"},
    "nextgen healthcare": {"industry": "healthcare", "sub_industry": "provider"},
    "eclinicalworks": {"industry": "healthcare", "sub_industry": "provider"},
    "netsmart": {"industry": "healthcare", "sub_industry": "provider"},
    "inovalon": {"industry": "healthcare", "sub_industry": "health_services"},
    "healthstream": {"industry": "healthcare", "sub_industry": "health_services"},

    # Insurance
    "duck creek": {"industry": "insurance", "sub_industry": "p_and_c"},
    "guidewire": {"industry": "insurance", "sub_industry": "p_and_c"},
    "majesco": {"industry": "insurance", "sub_industry": "p_and_c"},
    "insurity": {"industry": "insurance", "sub_industry": "p_and_c"},
    "socotra": {"industry": "insurance", "sub_industry": "p_and_c"},
    "earnix": {"industry": "insurance", "sub_industry": "p_and_c"},
    "sapiens": {"industry": "insurance", "sub_industry": "life_annuity"},
    "vertafore": {"industry": "insurance", "sub_industry": "brokerage_mga"},
    "applied systems": {"industry": "insurance", "sub_industry": "brokerage_mga"},
    "britecore": {"industry": "insurance", "sub_industry": "p_and_c"},
    "snapsheet": {"industry": "insurance", "sub_industry": "p_and_c"},

    # Manufacturing
    "siemens plm": {"industry": "manufacturing", "sub_industry": "discrete"},
    "ptc windchill": {"industry": "manufacturing", "sub_industry": "discrete"},
    "autodesk": {"industry": "manufacturing", "sub_industry": "discrete"},
    "rockwell automation": {"industry": "manufacturing", "sub_industry": "industrial"},
    "aveva": {"industry": "manufacturing", "sub_industry": "process"},
    "dassault systemes": {"industry": "manufacturing", "sub_industry": "discrete"},
    "sap plant maintenance": {"industry": "manufacturing", "sub_industry": None},
    "infor cloudsuite industrial": {"industry": "manufacturing", "sub_industry": "discrete"},
    "plex": {"industry": "manufacturing", "sub_industry": "industrial"},

    # Retail
    "shopify": {"industry": "retail_consumer", "sub_industry": "ecommerce"},
    "magento": {"industry": "retail_consumer", "sub_industry": "ecommerce"},
    "oracle retail": {"industry": "retail_consumer", "sub_industry": "brick_and_mortar"},
    "manhattan associates": {"industry": "retail_consumer", "sub_industry": "omnichannel"},
    "blue yonder": {"industry": "retail_consumer", "sub_industry": "omnichannel"},
    "lightspeed": {"industry": "retail_consumer", "sub_industry": "brick_and_mortar"},
}
```

```python
def _collect_vertical_app_signals(self) -> List[EvidenceSignal]:
    from stores.app_category_mappings import APP_MAPPINGS

    signals = []
    industry_counts: Dict[str, int] = defaultdict(int)

    # Scan InventoryStore for application items
    for item in self.inventory_store.query(inventory_type="application"):
        app_name = (item.data.get("name") or "").strip().lower()
        if not app_name:
            continue

        # Try direct lookup in APP_MAPPINGS
        mapping = APP_MAPPINGS.get(app_name)
        if not mapping:
            # Try alias matching
            for key, m in APP_MAPPINGS.items():
                if app_name in [a.lower() for a in m.aliases]:
                    mapping = m
                    app_name = key  # Normalize to canonical name
                    break

        if not mapping or mapping.category != "industry_vertical":
            continue

        # Map app to industry
        industry_map = INDUSTRY_APP_INDUSTRY_MAP.get(app_name)
        if not industry_map:
            continue

        industry_counts[industry_map["industry"]] += 1

        signals.append(EvidenceSignal(
            industry=industry_map["industry"],
            sub_industry=industry_map.get("sub_industry"),
            signal_type="vertical_app",
            confidence=0.85,
            weight=1.0,  # Will be adjusted after counting
            provenance="document_sourced",
            description=f"Industry-vertical application '{mapping.vendor} {mapping.description}' in inventory",
            source_fact_id="",
            source_document=item.source_file,
            source_text=app_name,
        ))

    # Adjust weights based on count per industry
    for signal in signals:
        count = industry_counts.get(signal.industry, 1)
        signal.weight = min(3.0, 1.0 + 0.3 * (count - 1))

    return signals
```

#### Signal Type 4: Document Content Trigger Words (confidence: 0.7, provenance: `"inferred"`)

**Source:** Trigger word lists from `INDUSTRY_APPLICATION_CONSIDERATIONS` in `prompts/shared/industry_application_considerations.py`. Searched against `evidence.exact_quote` fields across all facts.

**Procedure:**
1. Import `INDUSTRY_APPLICATION_CONSIDERATIONS`.
2. For each industry in the considerations dict, get the `triggers` list.
3. For each fact in `FactStore`, extract `evidence.get("exact_quote", "")`.
4. Count how many times each trigger appears across all evidence quotes.
5. Group counts by industry. **Minimum threshold: 3+ total trigger hits for an industry to register.** This prevents noise (a single mention of "patient" in "be patient with the timeline" from triggering healthcare).
6. Weight by uniqueness: if a trigger is unique to one industry (e.g., "policyholder" only appears in insurance), it gets `weight=1.5`. If it appears in multiple industry trigger lists, `weight=0.8`.
7. Weight by frequency: `weight *= min(3.0, 1.0 + 0.1 * (hit_count - 3))` for counts above the threshold.

```python
def _collect_trigger_word_signals(self) -> List[EvidenceSignal]:
    from prompts.shared.industry_application_considerations import (
        INDUSTRY_APPLICATION_CONSIDERATIONS
    )

    # Build trigger-to-industry reverse index
    trigger_index: Dict[str, List[str]] = {}  # trigger -> [industry_keys]
    for ind_key, config in INDUSTRY_APPLICATION_CONSIDERATIONS.items():
        for trigger in config.get("triggers", []):
            trigger_lower = trigger.lower()
            trigger_index.setdefault(trigger_lower, []).append(ind_key)

    # Count trigger hits per industry across all fact evidence
    industry_hits: Dict[str, Dict] = defaultdict(lambda: {
        "count": 0,
        "triggers": defaultdict(int),
        "fact_ids": [],
        "documents": set(),
    })

    for fact in self.fact_store.facts:
        quote = (fact.evidence or {}).get("exact_quote", "").lower()
        if not quote:
            continue

        for trigger_lower, industries in trigger_index.items():
            occurrences = quote.count(trigger_lower)
            if occurrences > 0:
                for ind_key in industries:
                    industry_hits[ind_key]["count"] += occurrences
                    industry_hits[ind_key]["triggers"][trigger_lower] += occurrences
                    if fact.fact_id not in industry_hits[ind_key]["fact_ids"]:
                        industry_hits[ind_key]["fact_ids"].append(fact.fact_id)
                    if fact.source_document:
                        industry_hits[ind_key]["documents"].add(fact.source_document)

    signals = []
    for ind_key, data in industry_hits.items():
        if data["count"] < 3:  # Minimum threshold
            continue

        # Find the highest-signal trigger for evidence snippet
        top_trigger = max(data["triggers"], key=data["triggers"].get)
        trigger_uniqueness = len(trigger_index.get(top_trigger, []))
        uniqueness_weight = 1.5 if trigger_uniqueness == 1 else 0.8
        frequency_weight = min(3.0, 1.0 + 0.1 * (data["count"] - 3))

        signals.append(EvidenceSignal(
            industry=ind_key,
            sub_industry=None,
            signal_type="trigger_word",
            confidence=0.7,
            weight=uniqueness_weight * frequency_weight,
            provenance="inferred",
            description=(
                f"{data['count']} trigger word hits for {ind_key} "
                f"across {len(data['fact_ids'])} fact(s). "
                f"Top trigger: '{top_trigger}' ({data['triggers'][top_trigger]}x)"
            ),
            source_fact_id=data["fact_ids"][0] if data["fact_ids"] else "",
            source_document=next(iter(data["documents"]), ""),
            source_text=top_trigger,
        ))

    return signals
```

#### Signal Type 5: Vendor / Product Names (confidence: 0.6, provenance: `"inferred"`)

**Source:** Vendor names in `InventoryStore` application items that are industry-specific but are NOT already covered by `APP_MAPPINGS` (those are handled by Signal Type 3).

**Vendor-to-industry mapping** (defined in `stores/industry_taxonomy.py`):

```python
VENDOR_INDUSTRY_MAP: Dict[str, Dict[str, str]] = {
    # Insurance vendors not in APP_MAPPINGS
    "applied systems": {"industry": "insurance", "sub_industry": "brokerage_mga"},
    "zywave": {"industry": "insurance", "sub_industry": "brokerage_mga"},
    "agency zoom": {"industry": "insurance", "sub_industry": "brokerage_mga"},
    "hawksoft": {"industry": "insurance", "sub_industry": "brokerage_mga"},
    "nexsure": {"industry": "insurance", "sub_industry": "brokerage_mga"},
    "ezlynx": {"industry": "insurance", "sub_industry": "brokerage_mga"},
    "riskconnect": {"industry": "insurance", "sub_industry": None},
    "origami risk": {"industry": "insurance", "sub_industry": None},

    # Healthcare vendors not in APP_MAPPINGS
    "athenahealth": {"industry": "healthcare", "sub_industry": "provider"},
    "healthedge": {"industry": "healthcare", "sub_industry": "payer"},
    "cotiviti": {"industry": "healthcare", "sub_industry": "payer"},
    "availity": {"industry": "healthcare", "sub_industry": "health_services"},
    "change healthcare": {"industry": "healthcare", "sub_industry": "health_services"},
    "phreesia": {"industry": "healthcare", "sub_industry": "provider"},
    "relatient": {"industry": "healthcare", "sub_industry": "provider"},

    # Financial Services vendors not in APP_MAPPINGS
    "q2": {"industry": "financial_services", "sub_industry": "banking"},
    "alkami": {"industry": "financial_services", "sub_industry": "banking"},
    "ncr digital banking": {"industry": "financial_services", "sub_industry": "banking"},
    "verafin": {"industry": "financial_services", "sub_industry": "banking"},
    "actimize": {"industry": "financial_services", "sub_industry": "banking"},
    "axiom": {"industry": "financial_services", "sub_industry": "banking"},
    "black knight": {"industry": "financial_services", "sub_industry": "specialty_finance"},
    "sagent": {"industry": "financial_services", "sub_industry": "specialty_finance"},

    # Manufacturing vendors not in APP_MAPPINGS
    "kepware": {"industry": "manufacturing", "sub_industry": None},
    "ignition": {"industry": "manufacturing", "sub_industry": None},
    "inductive automation": {"industry": "manufacturing", "sub_industry": None},
    "mingo smart factory": {"industry": "manufacturing", "sub_industry": None},
    "plex systems": {"industry": "manufacturing", "sub_industry": "industrial"},
    "epicor": {"industry": "manufacturing", "sub_industry": "discrete"},

    # Real Estate vendors
    "yardi": {"industry": "real_estate", "sub_industry": "commercial"},
    "mri software": {"industry": "real_estate", "sub_industry": "commercial"},
    "appfolio": {"industry": "real_estate", "sub_industry": "residential"},
    "buildium": {"industry": "real_estate", "sub_industry": "residential"},
    "realpage": {"industry": "real_estate", "sub_industry": "residential"},
}
```

**Procedure:**
1. Get all items from `InventoryStore` where `inventory_type == "application"`.
2. For each item, extract `data.get("vendor", "")` normalized to lowercase.
3. Skip if the item was already matched by Signal Type 3 (vertical app detection).
4. Look up in `VENDOR_INDUSTRY_MAP`. On match, produce an `EvidenceSignal` with `confidence=0.6`, `weight=1.0`.
5. Also scan for vendor names in `FactStore` facts where `domain == "applications"` and details contain vendor references.

```python
def _collect_vendor_name_signals(self) -> List[EvidenceSignal]:
    signals = []
    matched_items = set()  # Track items already matched by vertical_app signals

    for item in self.inventory_store.query(inventory_type="application"):
        vendor = (item.data.get("vendor") or "").strip().lower()
        if not vendor:
            continue

        # Skip if already matched by vertical app detection
        app_name = (item.data.get("name") or "").strip().lower()
        if app_name in INDUSTRY_APP_INDUSTRY_MAP:
            continue

        # Check vendor against vendor industry map
        for vendor_key, mapping in VENDOR_INDUSTRY_MAP.items():
            if vendor_key in vendor or vendor in vendor_key:
                signals.append(EvidenceSignal(
                    industry=mapping["industry"],
                    sub_industry=mapping.get("sub_industry"),
                    signal_type="vendor_name",
                    confidence=0.6,
                    weight=1.0,
                    provenance="inferred",
                    description=f"Industry-specific vendor '{vendor}' detected in inventory",
                    source_document=item.source_file,
                    source_text=vendor,
                ))
                break

    return signals
```

#### Signal Type 6: Organization Structure Patterns (confidence: 0.5, provenance: `"inferred"`)

**Source:** Facts with `domain == "organization"` that contain industry-specific job titles, department names, or organizational patterns.

**Role-to-industry mapping** (defined in `stores/industry_taxonomy.py`):

```python
ROLE_INDUSTRY_MAP: Dict[str, Dict[str, str]] = {
    # Insurance
    "actuary": {"industry": "insurance", "sub_industry": None},
    "actuarial": {"industry": "insurance", "sub_industry": None},
    "underwriter": {"industry": "insurance", "sub_industry": None},
    "underwriting": {"industry": "insurance", "sub_industry": None},
    "claims adjuster": {"industry": "insurance", "sub_industry": None},
    "claims examiner": {"industry": "insurance", "sub_industry": None},
    "loss control": {"industry": "insurance", "sub_industry": None},
    "policyholder services": {"industry": "insurance", "sub_industry": None},
    "reinsurance analyst": {"industry": "insurance", "sub_industry": "reinsurance"},

    # Healthcare
    "clinical": {"industry": "healthcare", "sub_industry": "provider"},
    "nurse informaticist": {"industry": "healthcare", "sub_industry": "provider"},
    "chief medical officer": {"industry": "healthcare", "sub_industry": "provider"},
    "chief nursing officer": {"industry": "healthcare", "sub_industry": "provider"},
    "health information management": {"industry": "healthcare", "sub_industry": None},
    "him director": {"industry": "healthcare", "sub_industry": None},
    "hipaa privacy officer": {"industry": "healthcare", "sub_industry": None},
    "clinical informatics": {"industry": "healthcare", "sub_industry": "provider"},
    "medical director": {"industry": "healthcare", "sub_industry": "provider"},
    "director of pharmacy": {"industry": "healthcare", "sub_industry": "provider"},

    # Manufacturing
    "plant manager": {"industry": "manufacturing", "sub_industry": None},
    "mes engineer": {"industry": "manufacturing", "sub_industry": None},
    "production manager": {"industry": "manufacturing", "sub_industry": None},
    "quality manager": {"industry": "manufacturing", "sub_industry": None},
    "manufacturing engineer": {"industry": "manufacturing", "sub_industry": None},
    "ot engineer": {"industry": "manufacturing", "sub_industry": None},
    "scada engineer": {"industry": "manufacturing", "sub_industry": None},
    "plant it manager": {"industry": "manufacturing", "sub_industry": None},
    "process engineer": {"industry": "manufacturing", "sub_industry": "process"},
    "tool and die": {"industry": "manufacturing", "sub_industry": "discrete"},

    # Financial Services
    "chief risk officer": {"industry": "financial_services", "sub_industry": None},
    "bsa officer": {"industry": "financial_services", "sub_industry": "banking"},
    "aml analyst": {"industry": "financial_services", "sub_industry": "banking"},
    "loan officer": {"industry": "financial_services", "sub_industry": "banking"},
    "compliance officer": {"industry": "financial_services", "sub_industry": None},
    "portfolio manager": {"industry": "financial_services", "sub_industry": "asset_management"},
    "trader": {"industry": "financial_services", "sub_industry": "asset_management"},

    # Energy
    "plant operator": {"industry": "energy_utilities", "sub_industry": "utilities"},
    "grid operations": {"industry": "energy_utilities", "sub_industry": "utilities"},
    "drilling engineer": {"industry": "energy_utilities", "sub_industry": "oil_gas"},
    "reservoir engineer": {"industry": "energy_utilities", "sub_industry": "oil_gas"},
}
```

**Procedure:**
1. Get all facts where `domain == "organization"`.
2. For each fact, build a searchable text block from `item`, `details`, and `evidence`.
3. Normalize to lowercase.
4. For each key in `ROLE_INDUSTRY_MAP`, check for substring match.
5. On match, produce an `EvidenceSignal` with `confidence=0.5`, `weight=1.0`.
6. Deduplicate: same role pattern in multiple facts produces one signal with increased weight (same logic as regulatory signals).

```python
def _collect_org_structure_signals(self) -> List[EvidenceSignal]:
    signals = []
    seen: Dict[str, List[str]] = {}  # role_key -> [fact_ids]

    org_facts = [f for f in self.fact_store.facts if f.domain == "organization"]

    for fact in org_facts:
        text_block = self._build_fact_text_block(fact).lower()
        for role_key, mapping in ROLE_INDUSTRY_MAP.items():
            if role_key in text_block:
                seen.setdefault(role_key, []).append(fact.fact_id)

    for role_key, fact_ids in seen.items():
        mapping = ROLE_INDUSTRY_MAP[role_key]
        weight = min(3.0, 1.0 + 0.5 * (len(fact_ids) - 1))
        first_fact = self.fact_store.get_fact(fact_ids[0])

        signals.append(EvidenceSignal(
            industry=mapping["industry"],
            sub_industry=mapping.get("sub_industry"),
            signal_type="org_structure",
            confidence=0.5,
            weight=weight,
            provenance="inferred",
            description=f"Industry-specific role '{role_key}' in {len(fact_ids)} org fact(s)",
            source_fact_id=fact_ids[0],
            source_document=first_fact.source_document if first_fact else "",
            source_text=role_key,
        ))

    return signals
```

---

### 3. Scoring Algorithm

The classifier aggregates all signals into a weighted score per industry and produces a ranked classification.

Defined in `services/industry_classifier.py`:

```python
import logging
from typing import List, Dict, Optional, Tuple, Any
from collections import defaultdict
from dataclasses import dataclass, field

from stores.fact_store import FactStore
from stores.inventory_store import InventoryStore
from stores.industry_taxonomy import (
    INDUSTRY_TAXONOMY,
    INDUSTRY_APP_INDUSTRY_MAP,
    REGULATORY_INDUSTRY_MAP,
    VENDOR_INDUSTRY_MAP,
    ROLE_INDUSTRY_MAP,
    SIGNAL_TYPES,
    EvidenceSignal,
)

logger = logging.getLogger(__name__)


@dataclass
class EvidenceSnippet:
    """Top-N evidence item included in the classification output for transparency."""
    text: str                     # The quote, app name, regulatory term, or role title
    signal_type: str              # "user_specified", "regulatory", "vertical_app", etc.
    source_document: str          # Document name for traceability
    source_fact_id: str           # Fact ID for traceability
    confidence: float             # This signal's confidence value


@dataclass
class IndustryClassification:
    """Complete industry classification result."""
    primary_industry: str                   # "insurance", "healthcare", etc.
    sub_industry: Optional[str]             # "p_and_c", "provider", etc. or None
    secondary_industries: List[str]         # Industries scoring >50% of primary
    confidence: float                       # 0.0 - 1.0 overall confidence
    evidence_snippets: List[EvidenceSnippet]  # Top 5 supporting evidence items
    classification_method: str              # "rule_based" or "user_specified"
    signal_breakdown: Dict[str, float]      # Per signal-type aggregate scores
    warnings: List[str]                     # Conflicts, ambiguities, low-confidence notes


class IndustryClassifier:
    """
    Deterministic industry classifier using multi-signal evidence aggregation.

    Same inputs always produce the same classification. No LLM calls.
    """

    # Maximum possible score for a single industry is used to normalize confidence.
    # Theoretical max: user_specified (1.0 * 10.0) + 3 regulatory (0.9 * 3.0 each)
    # + 5 vertical apps (0.85 * 3.0 each) + trigger words (0.7 * 4.5)
    # + 3 vendor names (0.6 * 1.0 each) + 3 org roles (0.5 * 3.0 each)
    # = 10.0 + 8.1 + 12.75 + 3.15 + 1.8 + 4.5 = ~40.3
    # In practice, a strong classification without user input scores 5-15.
    MAX_PRACTICAL_SCORE = 15.0

    def __init__(self, fact_store: FactStore, inventory_store: InventoryStore):
        self.fact_store = fact_store
        self.inventory_store = inventory_store
        self._tags: List[str] = []  # Tags like "public_company" from SOX detection

    def classify(self, deal_context: Any = None) -> IndustryClassification:
        """
        Run industry classification.

        Args:
            deal_context: Optional DealContext from tools_v2/session.py.
                          If present and industry is set, it takes highest priority.

        Returns:
            IndustryClassification with primary, secondary, confidence, and evidence.
        """
        self._tags = []

        # Collect all signals
        signals: List[EvidenceSignal] = []
        signals.extend(self._collect_user_specified_signals(deal_context))
        signals.extend(self._collect_regulatory_signals())
        signals.extend(self._collect_vertical_app_signals())
        signals.extend(self._collect_trigger_word_signals())
        signals.extend(self._collect_vendor_name_signals())
        signals.extend(self._collect_org_structure_signals())

        logger.info(f"Industry classifier collected {len(signals)} total signals")

        # Score
        industry_scores: Dict[str, float] = defaultdict(float)
        industry_evidence: Dict[str, List[EvidenceSignal]] = defaultdict(list)
        signal_type_scores: Dict[str, Dict[str, float]] = defaultdict(
            lambda: defaultdict(float)
        )

        for signal in signals:
            score = signal.confidence * signal.weight
            industry_scores[signal.industry] += score
            industry_evidence[signal.industry].append(signal)
            signal_type_scores[signal.industry][signal.signal_type] += score

        # Sort by score descending
        ranked = sorted(industry_scores.items(), key=lambda x: -x[1])

        if not ranked:
            return self._empty_classification()

        primary_key, primary_score = ranked[0]

        # Determine secondary industries (>50% of primary score)
        secondary = [
            r[0] for r in ranked[1:]
            if r[1] > 0.5 * primary_score
        ]

        # Compute overall confidence (normalized against practical max)
        overall_confidence = min(1.0, primary_score / self.MAX_PRACTICAL_SCORE)

        # Determine sub-industry
        sub_industry = self._determine_sub_industry(
            primary_key, industry_evidence[primary_key]
        )

        # Build evidence snippets (top 5 by confidence * weight)
        evidence_snippets = self._top_evidence(
            industry_evidence[primary_key], limit=5
        )

        # Determine classification method
        has_user_signal = any(
            s.signal_type == "user_specified" and s.industry == primary_key
            for s in signals
        )
        classification_method = "user_specified" if has_user_signal else "rule_based"

        # Build signal breakdown for the primary industry
        breakdown = dict(signal_type_scores.get(primary_key, {}))

        # Build warnings
        warnings = self._build_warnings(
            ranked, signals, deal_context, primary_key, overall_confidence
        )

        classification = IndustryClassification(
            primary_industry=primary_key,
            sub_industry=sub_industry,
            secondary_industries=secondary,
            confidence=overall_confidence,
            evidence_snippets=evidence_snippets,
            classification_method=classification_method,
            signal_breakdown=breakdown,
            warnings=warnings,
        )

        logger.info(
            f"Classification result: {primary_key}"
            f" ({sub_industry or 'no sub'})"
            f" confidence={overall_confidence:.2f}"
            f" method={classification_method}"
            f" secondary={secondary}"
        )

        return classification

    def _empty_classification(self) -> IndustryClassification:
        """Return default classification when no signals are found."""
        return IndustryClassification(
            primary_industry="general",
            sub_industry="other",
            secondary_industries=[],
            confidence=0.3,
            evidence_snippets=[],
            classification_method="rule_based",
            signal_breakdown={},
            warnings=["No industry signals detected in data room documents or inventory"],
        )

    def _top_evidence(
        self, signals: List[EvidenceSignal], limit: int = 5
    ) -> List[EvidenceSnippet]:
        """Select the top N evidence signals, ranked by confidence * weight."""
        ranked = sorted(signals, key=lambda s: s.confidence * s.weight, reverse=True)
        snippets = []
        for s in ranked[:limit]:
            snippets.append(EvidenceSnippet(
                text=s.description,
                signal_type=s.signal_type,
                source_document=s.source_document,
                source_fact_id=s.source_fact_id,
                confidence=s.confidence,
            ))
        return snippets

    def _build_warnings(
        self,
        ranked: List[Tuple[str, float]],
        signals: List[EvidenceSignal],
        deal_context: Any,
        primary_key: str,
        confidence: float,
    ) -> List[str]:
        """Build warning messages for the classification."""
        warnings = []

        # Tie warning: top 2 within 10%
        if len(ranked) >= 2:
            top_score = ranked[0][1]
            second_score = ranked[1][1]
            if top_score > 0 and (top_score - second_score) / top_score < 0.10:
                warnings.append(
                    f"Close classification: '{ranked[0][0]}' ({top_score:.2f}) "
                    f"and '{ranked[1][0]}' ({second_score:.2f}) are within 10%. "
                    f"Both listed as primary + secondary."
                )

        # User-specified conflicts with evidence
        user_industry = getattr(deal_context, 'industry', None) if deal_context else None
        if user_industry and user_industry != primary_key:
            # Check if evidence (non-user signals) point to a different industry
            non_user_scores: Dict[str, float] = defaultdict(float)
            for s in signals:
                if s.signal_type != "user_specified":
                    non_user_scores[s.industry] += s.confidence * s.weight
            if non_user_scores:
                evidence_top = max(non_user_scores, key=non_user_scores.get)
                if evidence_top != user_industry:
                    warnings.append(
                        f"User-specified industry '{user_industry}' differs from "
                        f"document evidence which suggests '{evidence_top}'. "
                        f"User specification takes precedence."
                    )

        # Low confidence warning
        if confidence < 0.5:
            warnings.append(
                f"Low classification confidence ({confidence:.2f}). "
                f"Limited industry-specific signals in the data room."
            )

        # Tags
        if "public_company" in self._tags:
            warnings.append(
                "SOX/Sarbanes-Oxley references detected, suggesting a public company "
                "or public-company subsidiary. SOX compliance considerations apply."
            )

        return warnings
```

---

### 4. Tie-Break Rules

The scoring algorithm handles ties and edge cases with the following deterministic rules:

| Scenario | Rule |
|----------|------|
| **Top 2 industries within 10% of each other** | Classify the higher-scoring industry as primary. Add the second industry to `secondary_industries`. Add a warning noting the close scores. Example: insurance 4.2 and technology 3.9 -> primary: `insurance`, secondary: `["technology"]`, warning present. |
| **No signals found** | Return `{primary_industry: "general", sub_industry: "other", confidence: 0.3, warnings: ["No industry signals detected..."]}`. Never return an empty or null classification. |
| **User-specified conflicts with evidence** | User-specified always wins (due to weight=10.0). Document evidence is still collected and if it points to a different industry, a warning is added: "User-specified industry differs from document evidence." The evidence is preserved in `signal_breakdown` for transparency. |
| **Single signal type dominates** | Valid classification. The `signal_breakdown` dict shows that only one signal type contributed, which consumers can inspect. No special handling needed. |
| **Multiple sub-industries tie within primary** | Use the sub-industry with more signals. If exactly tied, prefer the sub-industry whose signals have higher average confidence. If still tied, leave `sub_industry` as `None` (use the broad primary label). |

---

### 5. Sub-Industry Determination

Once the primary industry is determined, the classifier attempts to narrow to a sub-industry.

```python
def _determine_sub_industry(
    self, primary_industry: str, signals: List[EvidenceSignal]
) -> Optional[str]:
    """
    Determine sub-industry from signals within the primary industry.

    Returns:
        Sub-industry key or None if indeterminate.
    """
    taxonomy_entry = INDUSTRY_TAXONOMY.get(primary_industry, {})
    sub_industries = taxonomy_entry.get("sub_industries", {})

    if not sub_industries:
        return None

    # Count signals per sub-industry
    sub_scores: Dict[str, float] = defaultdict(float)
    sub_counts: Dict[str, int] = defaultdict(int)

    for signal in signals:
        if signal.sub_industry and signal.sub_industry in sub_industries:
            sub_scores[signal.sub_industry] += signal.confidence * signal.weight
            sub_counts[signal.sub_industry] += 1

    # Also check sub-industry indicators against fact evidence
    for sub_key, sub_config in sub_industries.items():
        indicators = sub_config.get("indicators", [])
        app_indicators = sub_config.get("app_indicators", [])

        # Search facts for sub-industry indicators
        for fact in self.fact_store.facts:
            text_block = self._build_fact_text_block(fact).lower()
            for indicator in indicators:
                if indicator.lower() in text_block:
                    sub_scores[sub_key] += 0.3
                    sub_counts[sub_key] += 1

        # Search inventory for sub-industry app indicators
        for item in self.inventory_store.query(inventory_type="application"):
            app_name = (item.data.get("name") or "").strip().lower()
            for app_ind in app_indicators:
                if app_ind.lower() in app_name:
                    sub_scores[sub_key] += 0.5
                    sub_counts[sub_key] += 1

    if not sub_scores:
        return None

    # Rank sub-industries by score
    ranked_subs = sorted(sub_scores.items(), key=lambda x: -x[1])

    # If top sub-industry has a clear lead (>50% more than second), use it
    if len(ranked_subs) == 1:
        return ranked_subs[0][0]

    top_score = ranked_subs[0][1]
    second_score = ranked_subs[1][1] if len(ranked_subs) > 1 else 0

    if top_score > 0 and (second_score == 0 or top_score > second_score * 1.5):
        return ranked_subs[0][0]

    # Tie: prefer the one with more individual signals
    if sub_counts[ranked_subs[0][0]] > sub_counts[ranked_subs[1][0]]:
        return ranked_subs[0][0]

    # Still tied: prefer the one with higher average confidence
    avg_0 = top_score / max(1, sub_counts[ranked_subs[0][0]])
    avg_1 = second_score / max(1, sub_counts[ranked_subs[1][0]])
    if avg_0 > avg_1:
        return ranked_subs[0][0]

    # Truly indeterminate -- return None (use broad primary label)
    return None
```

#### Industry-Specific Sub-Industry Logic

For the top PE target industries, specific sub-industry resolution logic applies:

**Insurance:**
- P&C vs Life is primarily determined by application type: Duck Creek, Guidewire, Majesco, BriteCore, Insurity -> `p_and_c`; FINEOS, Sapiens ALIS -> `life_annuity`
- Brokerage/MGA is determined by Applied Systems, Vertafore, AMS360 presence plus trigger words like "broker", "MGA", "binding authority"
- If both P&C and Life apps are present, default to `p_and_c` (more common in PE acquisitions) with a warning

**Healthcare:**
- Provider vs Payer is determined by EMR presence (Epic, Cerner -> `provider`) vs health plan systems (HealthEdge, Facets -> `payer`)
- Org structure signals like "chief medical officer", "nurse informaticist" -> `provider`
- Trigger words like "claims adjudication", "utilization management" -> `payer`

**Financial Services:**
- Banking vs Asset Management is determined by core banking systems (FIS, Fiserv, Jack Henry -> `banking`) vs portfolio management systems (Bloomberg, Charles River -> `asset_management`)
- Regulatory signals differentiate: FDIC/OCC -> `banking`, SEC/FINRA -> `asset_management`

**Manufacturing:**
- Discrete vs Process is determined by app types: PLM/CAD tools (Siemens, PTC, Dassault -> `discrete`), process control (AVEVA, OSIsoft PI -> `process`)
- Org signals: "tool and die" -> `discrete`, "process engineer" -> `process`

---

### 6. Output Schema

The complete output schema is defined in `services/industry_classifier.py`:

```python
@dataclass
class IndustryClassification:
    """
    Complete industry classification result.

    Produced by IndustryClassifier.classify(). Consumed by:
    - ProfileExtractor (Spec 01) to populate CompanyProfile.industry
    - Report templates (Spec 03) for industry-specific sections
    - Benchmark engine (Spec 04) for cohort selection
    - UI views (Spec 05) for classification display
    """
    primary_industry: str
    """
    Primary industry key from INDUSTRY_TAXONOMY.
    Always populated. Value is a snake_case key like "insurance",
    "healthcare", "financial_services", "manufacturing", "technology",
    "professional_services", "retail_consumer", "energy_utilities",
    "real_estate", "logistics_distribution", "media_entertainment",
    or "general".
    """

    sub_industry: Optional[str]
    """
    Sub-industry key within the primary industry. Optional.
    None when evidence is insufficient to narrow below the primary level.
    Examples: "p_and_c", "provider", "banking", "discrete".
    """

    secondary_industries: List[str]
    """
    Industries scoring >50% of the primary industry score.
    Captures mixed-industry companies (e.g., insurtech = insurance + technology).
    Empty list when the primary industry dominates.
    """

    confidence: float
    """
    Overall classification confidence, 0.0 to 1.0.
    - >= 0.8: High confidence (multiple corroborating signals)
    - 0.5 - 0.79: Medium confidence (some signals present)
    - < 0.5: Low confidence (sparse data)
    - 0.3: Default/fallback (no signals)
    """

    evidence_snippets: List[EvidenceSnippet]
    """
    Top 5 evidence items supporting the primary classification,
    ranked by confidence * weight. Each snippet includes the source
    text, signal type, document name, and fact ID for traceability.
    """

    classification_method: str
    """
    "rule_based" when classification is derived from document/inventory signals.
    "user_specified" when the user set the industry via DealContext.
    """

    signal_breakdown: Dict[str, float]
    """
    Aggregate score per signal type for the primary industry.
    Keys are SIGNAL_TYPES keys: "user_specified", "regulatory",
    "vertical_app", "trigger_word", "vendor_name", "org_structure".
    Values are the sum of (confidence * weight) for all signals
    of that type pointing to the primary industry.
    Enables transparency: consumers can see WHICH signal types
    contributed most to the classification.
    """

    warnings: List[str]
    """
    Human-readable warning messages. Examples:
    - "User-specified industry differs from document evidence"
    - "Close classification: 'insurance' and 'technology' are within 10%"
    - "Low classification confidence (0.35)"
    - "SOX references detected, suggesting public company"
    """


@dataclass
class EvidenceSnippet:
    """
    A single evidence item included in the classification output.
    Provides traceability from classification back to source data.
    """
    text: str
    """Human-readable description of the evidence signal."""

    signal_type: str
    """Signal type key: "regulatory", "vertical_app", "trigger_word", etc."""

    source_document: str
    """Document filename this evidence was found in. Empty if not traceable."""

    source_fact_id: str
    """FactStore fact ID (e.g., F-CYBER-003). Empty if from inventory only."""

    confidence: float
    """This individual signal's confidence value (0.0 - 1.0)."""
```

---

### 7. Integration with CompanyProfile (Spec 01)

The classifier is called by `ProfileExtractor` to populate the `industry` `ProfileField` on `CompanyProfile`. This replaces the placeholder defined in Spec 01 at line 218-219:

```python
# --- Industry (placeholder -- Spec 02 fills this in) ---
industry: ProfileField               # str value - industry key (e.g., "healthcare")
```

After Spec 02 integration, the `CompanyProfile` gains these additional fields:

```python
@dataclass
class CompanyProfile:
    # ... existing fields from Spec 01 ...

    # --- Industry (populated by Spec 02 IndustryClassifier) ---
    industry: ProfileField               # str value - primary industry key
    sub_industry: Optional[str] = None   # Sub-industry key or None
    secondary_industries: List[str] = field(default_factory=list)  # Secondary industry keys
    industry_classification: Optional[Any] = None  # Full IndustryClassification object
```

The `ProfileExtractor._extract_industry()` method implements the integration:

```python
def _extract_industry(self) -> Tuple[ProfileField, Optional[str], List[str], IndustryClassification]:
    """
    Extract industry using the IndustryClassifier (Spec 02).

    Returns:
        Tuple of (industry_field, sub_industry, secondary_industries, classification)
    """
    from services.industry_classifier import IndustryClassifier

    classifier = IndustryClassifier(
        fact_store=self.fact_store,
        inventory_store=self.inventory_store,
    )
    classification = classifier.classify(deal_context=self.deal_context)

    # Convert to ProfileField
    industry_field = ProfileField(
        value=classification.primary_industry,
        confidence=_confidence_to_level(classification.confidence),
        provenance=classification.classification_method,
        source_fact_ids=[
            e.source_fact_id for e in classification.evidence_snippets
            if e.source_fact_id
        ],
        source_documents=list(set(
            e.source_document for e in classification.evidence_snippets
            if e.source_document
        )),
        inference_rationale=(
            f"Classified as {classification.primary_industry}"
            + (f" / {classification.sub_industry}" if classification.sub_industry else "")
            + f" with confidence {classification.confidence:.2f}"
            + f" via {classification.classification_method}."
            + (f" Secondary: {', '.join(classification.secondary_industries)}"
               if classification.secondary_industries else "")
        ),
    )

    # Add warnings to extraction warnings
    self._warnings.extend(classification.warnings)

    return (
        industry_field,
        classification.sub_industry,
        classification.secondary_industries,
        classification,
    )
```

---

### 8. Compatibility with Existing Industry Infrastructure

This spec does NOT modify existing files. It adds new files and is consumed by `ProfileExtractor`. However, the existing industry infrastructure continues to function independently:

| Existing Component | Relationship to Spec 02 |
|-------------------|------------------------|
| `INDUSTRY_HIERARCHY` in `tools_v2/session.py` | Spec 02's `INDUSTRY_TAXONOMY` is a superset. The taxonomy keys are compatible with `INDUSTRY_HIERARCHY` keys. `DealContext.set_industry()` validation uses `INDUSTRY_HIERARCHY.keys()`, which will continue to work. New taxonomy keys (e.g., `logistics_distribution`) not in `INDUSTRY_HIERARCHY` will be accepted by the classifier but will not validate in `DealContext.set_industry()` until that dict is updated. |
| `detect_industry_from_text()` in `industry_application_considerations.py` | Continues to function for real-time detection during interactive CLI sessions. Spec 02's classifier is a batch operation that runs after discovery, producing a richer result. The CLI can use `detect_industry_from_text()` for quick hints and the classifier for final classification. |
| `INDUSTRY_APPLICATION_CONSIDERATIONS` | Read-only dependency. The classifier uses the `triggers` lists from this dict for Signal Type 4 (trigger words). No modifications to the dict. |
| `APP_MAPPINGS` in `app_category_mappings.py` | Read-only dependency. The classifier uses `category == "industry_vertical"` entries for Signal Type 3. No modifications to the mappings dict. |

---

## Benefits

1. **Deterministic.** Same `FactStore` + `InventoryStore` inputs produce the same `IndustryClassification` output on every run. No LLM variance, no temperature drift, no prompt sensitivity. Classification is a pure function.

2. **Transparent.** Every classification includes up to 5 evidence snippets showing the specific signals (application names, regulatory terms, trigger words, job titles) that drove the classification. The `signal_breakdown` dict shows aggregate scores per signal type. Analysts can inspect WHY the system classified a company as insurance vs. healthcare.

3. **Multi-signal.** Does not rely on any single indicator. A company with Duck Creek in its application inventory, NAIC references in its documents, "actuary" in its org chart, and "underwriting" in its fact evidence will receive a high-confidence insurance classification from four independent signal types. Single-signal classifications receive proportionally lower confidence.

4. **Graceful degradation.** Always produces a result. Sparse data rooms receive a `general/other` classification with `confidence=0.3` and a clear warning. Ambiguous data rooms receive a primary + secondary classification with warnings about the close scores. The system never fails or returns null.

5. **Extensible.** Adding a new industry requires one taxonomy entry in `INDUSTRY_TAXONOMY`, optionally adding entries to `INDUSTRY_APP_INDUSTRY_MAP`, `REGULATORY_INDUSTRY_MAP`, `VENDOR_INDUSTRY_MAP`, and `ROLE_INDUSTRY_MAP`. No changes to the scoring algorithm.

6. **User-respecting.** When an analyst specifies an industry during deal setup, that specification is respected with confidence 1.0. Document evidence that contradicts the user selection is preserved and surfaced as a warning, not silently discarded.

---

## Expectations

### Performance

- Classification completes in **<500ms** for a typical data room (200-500 facts, 50-200 inventory items). Pure Python, no API calls, no disk I/O beyond the in-memory stores.
- Memory overhead is negligible: signal collection iterates facts once per signal type (6 passes), producing a list of lightweight `EvidenceSignal` dataclass instances.

### Accuracy Targets

| Scenario | Expected Result |
|----------|----------------|
| Insurance company with 2+ vertical apps (Duck Creek, Guidewire) and insurance-related documents | `primary_industry: "insurance"`, `confidence >= 0.8` |
| Healthcare provider with EMR (Epic/Cerner) and HIPAA references | `primary_industry: "healthcare"`, `confidence >= 0.8` |
| Financial services firm with core banking system and SOX/GLBA references | `primary_industry: "financial_services"`, `confidence >= 0.8` |
| Manufacturing company with MES/SCADA systems and ISO 9001 references | `primary_industry: "manufacturing"`, `confidence >= 0.8` |
| Technology company with SaaS metrics and no vertical apps | `primary_industry: "technology"`, `confidence >= 0.5` (fewer specific signals for tech) |
| Top-5 PE industries (insurance, healthcare, financial_services, manufacturing, technology) | Classified with `confidence > 0.8` when relevant apps + documents are present |
| Empty data room (no facts, no inventory) | `primary_industry: "general"`, `sub_industry: "other"`, `confidence: 0.3`, warning present |

### Determinism

- Three consecutive runs with identical `FactStore` and `InventoryStore` contents produce **byte-identical** `IndustryClassification` output (same primary, sub, secondary, confidence float value, same evidence snippets in same order, same warnings).
- Determinism is achieved by: (a) no randomness in any signal collector, (b) stable sort keys (confidence * weight, with fact_id as tiebreaker), (c) no timestamp-dependent logic in classification.

### Tie-Break Behavior

- Tie-breaks produce `primary + secondary`, never random selection.
- User-specified industry always respected with `confidence=1.0`.

---

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|------------|
| **Industry-specific apps not in mappings** | Unknown apps contribute 0 signal, potentially reducing confidence for correctly-identified industries | Medium | Unknown apps do not negatively impact classification -- they simply contribute no signal. `INDUSTRY_APP_INDUSTRY_MAP` can be extended in a Spec 02 revision to add new mappings. The `app_category_mappings.py` file already contains 966+ entries covering the most common vertical applications. |
| **Mixed-industry companies (insurtech, healthtech, fintech)** | Classifier may oscillate between two industries or pick the wrong primary | Medium | `secondary_industries` list explicitly handles this. Companies with strong signals for two industries get both listed. The tie-break rule (within 10%) produces a warning. Consumers (Spec 03 templates) can use both primary and secondary to generate relevant content. |
| **No industry signals at all (very sparse data room)** | Classification defaults to "general" which provides no analytical value | Low | Default to `general/other` with `confidence=0.3` and clear warning. This is the honest answer. Consumers should check confidence before making industry-specific decisions. Profile extraction warnings surface this to analysts. |
| **Document trigger words are noisy** | False positives from words like "patient" (as in "be patient") or "plant" (as in "plant the seed") | Medium | Minimum threshold of 3+ trigger hits for any industry to register. Weight by co-occurrence (multiple different triggers for the same industry are stronger than one trigger repeated). Trigger words are the fourth-ranked signal type (confidence=0.7), so they cannot override stronger signals from regulatory terms or vertical applications. |
| **Regulatory terms in non-relevant context** | A fact mentioning "HIPAA training is not required" still triggers the HIPAA -> healthcare signal | Low | This is acceptable -- the mention of HIPAA at all suggests healthcare relevance, even in a negative context. The confidence level (0.9) appropriately reflects that regulatory references are strong indicators regardless of whether the company is compliant. |
| **New industries not in taxonomy** | A company in an industry not defined in `INDUSTRY_TAXONOMY` (e.g., agriculture, mining) will be classified as "general" | Low | The taxonomy covers the top industries seen in PE due diligence. Adding a new industry is a single dict entry plus optional mapping entries -- no algorithm changes. The `general` fallback with low confidence honestly communicates the gap. |
| **Inconsistency with existing `INDUSTRY_HIERARCHY` in `tools_v2/session.py`** | New taxonomy keys added in Spec 02 may not be accepted by `DealContext.set_industry()` | Low | Spec 02 taxonomy keys are a superset of existing hierarchy keys. The five core industries (insurance, healthcare, financial_services, manufacturing, retail/retail_consumer) map directly. Newly introduced keys will need `INDUSTRY_HIERARCHY` to be updated for CLI selection but will work in the classifier immediately. |

---

## Results Criteria

All criteria must pass against deterministic test fixtures before this spec is considered complete.

### Test Fixture 1: Insurance Company

**Setup:**
- InventoryStore contains applications: Duck Creek, Guidewire, Applied Epic, Microsoft 365
- FactStore contains facts with:
  - `evidence.exact_quote` mentioning "policyholder", "underwriting", "loss ratio", "combined ratio"
  - Regulatory references: "NAIC", "Department of Insurance filing"
  - Organization fact with "Chief Actuary", "VP of Underwriting"

**Expected:**
- `primary_industry`: `"insurance"`
- `sub_industry`: `"p_and_c"` (Duck Creek and Guidewire are P&C indicators)
- `confidence`: `> 0.8`
- `evidence_snippets`: includes regulatory, vertical_app, and org_structure signals
- `classification_method`: `"rule_based"`
- `warnings`: empty list (no conflicts)

### Test Fixture 2: Healthcare Provider

**Setup:**
- InventoryStore contains applications: Epic, Workday, Microsoft 365
- FactStore contains facts with:
  - `evidence.exact_quote` mentioning "patient care", "clinical documentation", "medical records"
  - Regulatory references: "HIPAA", "PHI"
  - Organization fact with "Chief Medical Officer", "Nurse Informaticist"

**Expected:**
- `primary_industry`: `"healthcare"`
- `sub_industry`: `"provider"` (Epic + CMO + patient care)
- `confidence`: `> 0.8`
- `classification_method`: `"rule_based"`

### Test Fixture 3: Empty Data Room

**Setup:**
- InventoryStore is empty
- FactStore has only generic infrastructure facts with no industry signals

**Expected:**
- `primary_industry`: `"general"`
- `sub_industry`: `"other"`
- `confidence`: `0.3`
- `evidence_snippets`: empty list
- `warnings`: contains "No industry signals detected"

### Test Fixture 4: Conflict / Mixed Industry (Insurtech)

**Setup:**
- InventoryStore contains: Duck Creek, AWS, Kubernetes, Jenkins, Datadog
- FactStore contains insurance triggers ("underwriting", "claims") and technology triggers ("SaaS", "ARR", "deployment pipeline")

**Expected:**
- `primary_industry`: `"insurance"` (vertical app Duck Creek + insurance triggers outweigh generic tech triggers)
- `secondary_industries`: contains `"technology"`
- `confidence`: `> 0.5`
- `warnings`: may contain close-score warning if tech signals are strong

### Test Fixture 5: User-Specified Industry

**Setup:**
- DealContext with `industry="manufacturing"`, `industry_confirmed=True`
- InventoryStore contains: Epic (healthcare vertical app)
- FactStore contains healthcare triggers ("HIPAA", "patient")

**Expected:**
- `primary_industry`: `"manufacturing"` (user-specified wins)
- `confidence`: `1.0` (user-specified is always 1.0 after normalization)
- `classification_method`: `"user_specified"`
- `warnings`: contains "User-specified industry 'manufacturing' differs from document evidence which suggests 'healthcare'"

### Test Fixture 6: Determinism

**Setup:** Any of the above fixtures.

**Procedure:** Run `IndustryClassifier.classify()` three consecutive times with identical inputs.

**Expected:** All three runs produce identical `IndustryClassification` objects:
- Same `primary_industry`
- Same `sub_industry`
- Same `secondary_industries` (same list, same order)
- Same `confidence` (exact float equality)
- Same `evidence_snippets` (same items, same order)
- Same `signal_breakdown` (same keys and values)
- Same `warnings` (same items, same order)
