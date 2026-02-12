# Golden Fixture Schema

**Status:** SPECIFICATION
**Version:** 1.0
**Date:** 2026-02-11
**Owner:** IT DD Agent Team

---

## Overview

This document defines the JSON schema for golden fixture files that represent expected pipeline outputs for test validation. Each fixture corresponds to one M&A deal scenario (e.g., CloudServe, Great Insurance) and contains ground truth data across all 6 IT due diligence domains.

**Purpose:** Provide a machine-readable, version-controlled format for expected outputs that the validation framework can compare against actual pipeline results.

**Scope:** Schema covers inventory counts, costs, risks, findings, completeness scores, and metadata for cross-referencing source documents.

---

## Architecture

### Fixture File Structure

```
tests/golden/
├── cloudserve_expected.json          ← CloudServe deal ground truth
├── great_insurance_expected.json     ← Great Insurance deal ground truth
├── fixture_schema.json                ← JSON Schema definition (this doc)
└── README.md                          ← Instructions for creating fixtures
```

### Data Flow

```
Source Documents (CloudServe Doc 1-6.md)
    ↓
Discovery + Reasoning Pipeline
    ↓
Actual Outputs (inventory_store.json, facts.json, findings.json)
    ↓
[Manual Review + Validation]
    ↓
Golden Fixture (cloudserve_expected.json) ← Created once, version-controlled
    ↓
[Used by validation tests to verify future pipeline runs]
```

---

## Specification

### JSON Schema Definition

**File:** `tests/golden/fixture_schema.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://it-dd-agent.com/schemas/golden-fixture.json",
  "title": "IT DD Golden Fixture",
  "description": "Expected outputs for IT due diligence pipeline validation",
  "type": "object",
  "required": ["metadata", "applications", "infrastructure", "organization"],
  "properties": {
    "metadata": {
      "type": "object",
      "description": "Information about this fixture",
      "required": ["deal_name", "entity", "created_at", "source_documents", "version"],
      "properties": {
        "deal_name": {
          "type": "string",
          "description": "Deal identifier (e.g., 'cloudserve', 'great_insurance')",
          "examples": ["cloudserve", "great_insurance"]
        },
        "entity": {
          "type": "string",
          "enum": ["target", "buyer", "both"],
          "description": "Which entity this fixture validates"
        },
        "created_at": {
          "type": "string",
          "format": "date-time",
          "description": "When this fixture was created (ISO 8601)"
        },
        "source_documents": {
          "type": "array",
          "description": "List of input documents this fixture validates against",
          "items": {
            "type": "string",
            "examples": [
              "Target_CloudServe_Document_1_Executive_IT_Profile.md",
              "Target_CloudServe_Document_2_Application_Inventory.md"
            ]
          }
        },
        "version": {
          "type": "string",
          "description": "Schema version (semver)",
          "pattern": "^\\d+\\.\\d+\\.\\d+$",
          "examples": ["1.0.0"]
        },
        "notes": {
          "type": "string",
          "description": "Free-text notes about this fixture (e.g., intentional gaps)"
        }
      }
    },

    "applications": {
      "type": "object",
      "description": "Expected application inventory results",
      "required": ["count", "total_cost"],
      "properties": {
        "count": {
          "type": "integer",
          "description": "Total number of applications expected",
          "minimum": 0
        },
        "total_cost": {
          "type": "number",
          "description": "Total annual application cost (USD)",
          "minimum": 0
        },
        "by_category": {
          "type": "object",
          "description": "Breakdown by category",
          "additionalProperties": {
            "type": "object",
            "properties": {
              "count": {"type": "integer"},
              "cost": {"type": "number"}
            }
          },
          "examples": [{
            "crm": {"count": 3, "cost": 428000},
            "erp": {"count": 1, "cost": 180000}
          }]
        },
        "by_criticality": {
          "type": "object",
          "description": "Breakdown by criticality level",
          "properties": {
            "critical": {"type": "integer"},
            "high": {"type": "integer"},
            "medium": {"type": "integer"},
            "low": {"type": "integer"}
          }
        },
        "specific_apps": {
          "type": "array",
          "description": "List of specific applications that MUST be present",
          "items": {
            "type": "object",
            "required": ["name", "vendor"],
            "properties": {
              "name": {"type": "string"},
              "vendor": {"type": "string"},
              "cost": {"type": "number"},
              "criticality": {
                "type": "string",
                "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
              }
            }
          },
          "examples": [[
            {
              "name": "Salesforce Sales Cloud",
              "vendor": "Salesforce",
              "cost": 245000,
              "criticality": "HIGH"
            }
          ]]
        },
        "expected_gaps": {
          "type": "array",
          "description": "Intentionally missing data (not a bug)",
          "items": {
            "type": "object",
            "properties": {
              "gap_type": {"type": "string"},
              "reason": {"type": "string"}
            }
          },
          "examples": [[
            {
              "gap_type": "carve_out_dependency",
              "reason": "CloudServe is standalone acquisition, not a carve-out"
            }
          ]]
        }
      }
    },

    "infrastructure": {
      "type": "object",
      "description": "Expected infrastructure inventory results",
      "required": ["count"],
      "properties": {
        "count": {
          "type": "integer",
          "description": "Total number of infrastructure items expected"
        },
        "by_type": {
          "type": "object",
          "description": "Breakdown by infrastructure type",
          "additionalProperties": {"type": "integer"},
          "examples": [{
            "vm": 45,
            "container": 120,
            "serverless": 8
          }]
        },
        "by_environment": {
          "type": "object",
          "properties": {
            "production": {"type": "integer"},
            "staging": {"type": "integer"},
            "development": {"type": "integer"}
          }
        }
      }
    },

    "network": {
      "type": "object",
      "description": "Expected network/cybersecurity results",
      "properties": {
        "firewall_rules_count": {"type": "integer"},
        "vpn_tunnels_count": {"type": "integer"},
        "security_tools": {
          "type": "array",
          "items": {"type": "string"},
          "examples": [["CrowdStrike Falcon", "Wiz", "Okta"]]
        }
      }
    },

    "cybersecurity": {
      "type": "object",
      "description": "Expected cybersecurity posture",
      "properties": {
        "compliance_frameworks": {
          "type": "array",
          "items": {"type": "string"},
          "examples": [["SOC 2 Type II", "ISO 27001"]]
        },
        "vulnerabilities_count": {"type": "integer"}
      }
    },

    "identity": {
      "type": "object",
      "description": "Expected identity & access management",
      "properties": {
        "user_count": {"type": "integer"},
        "sso_provider": {"type": "string"},
        "mfa_enabled": {"type": "boolean"}
      }
    },

    "organization": {
      "type": "object",
      "description": "Expected org structure and headcount",
      "required": ["headcount"],
      "properties": {
        "headcount": {
          "type": "integer",
          "description": "Total IT headcount expected"
        },
        "total_compensation": {
          "type": "number",
          "description": "Total IT compensation (USD)"
        },
        "by_function": {
          "type": "object",
          "description": "Headcount breakdown by function",
          "additionalProperties": {"type": "integer"},
          "examples": [{
            "Applications": 2,
            "Infrastructure": 1,
            "Security": 1
          }]
        },
        "vendors_count": {
          "type": "integer",
          "description": "Number of IT vendors/MSPs"
        }
      }
    },

    "risks": {
      "type": "object",
      "description": "Expected risk findings",
      "properties": {
        "critical": {
          "type": "array",
          "description": "Critical risk IDs that MUST be detected",
          "items": {"type": "string"},
          "examples": [["R-WIZ-CONTRACT-EXPIRING", "R-DUAL-ERP-COMPLEXITY"]]
        },
        "high": {
          "type": "array",
          "items": {"type": "string"}
        },
        "total_count": {
          "type": "integer",
          "description": "Total number of risks expected (any severity)"
        }
      }
    },

    "findings": {
      "type": "object",
      "description": "Expected analysis findings",
      "properties": {
        "work_items_count": {
          "type": "integer",
          "description": "Number of work items (integration tasks) expected"
        },
        "work_items_by_phase": {
          "type": "object",
          "properties": {
            "day_1": {"type": "integer"},
            "day_100": {"type": "integer"},
            "post_100": {"type": "integer"}
          }
        }
      }
    },

    "completeness": {
      "type": "object",
      "description": "Expected data completeness scores",
      "properties": {
        "overall_score": {
          "type": "number",
          "minimum": 0,
          "maximum": 100,
          "description": "Overall completeness percentage"
        },
        "by_domain": {
          "type": "object",
          "description": "Completeness score per domain",
          "additionalProperties": {
            "type": "number",
            "minimum": 0,
            "maximum": 100
          },
          "examples": [{
            "applications": 85,
            "infrastructure": 72,
            "organization": 45
          }]
        }
      }
    }
  }
}
```

---

### Example Fixture: CloudServe

**File:** `tests/golden/cloudserve_expected.json`

```json
{
  "metadata": {
    "deal_name": "cloudserve",
    "entity": "target",
    "created_at": "2026-02-11T11:30:00Z",
    "source_documents": [
      "Target_CloudServe_Document_1_Executive_IT_Profile.md",
      "Target_CloudServe_Document_2_Application_Inventory.md",
      "Target_CloudServe_Document_3_Infrastructure_Hosting_Inventory.md",
      "Target_CloudServe_Document_4_Network_Cybersecurity_Inventory.md",
      "Target_CloudServe_Document_5_Identity_Access_Management.md",
      "Target_CloudServe_Document_6_Organization_Vendor_Inventory.md"
    ],
    "version": "1.0.0",
    "notes": "CloudServe is a SaaS platform company. No carve-out dependencies expected. Datadog is primary observability tool (not Splunk)."
  },

  "applications": {
    "count": 38,
    "total_cost": 2331500,
    "by_category": {
      "infrastructure": {"count": 9, "cost": 150000},
      "crm": {"count": 3, "cost": 428000},
      "erp": {"count": 1, "cost": 180000},
      "finance": {"count": 4, "cost": 200000},
      "hcm": {"count": 2, "cost": 144000},
      "collaboration": {"count": 3, "cost": 168000},
      "devops": {"count": 9, "cost": 170000},
      "productivity": {"count": 3, "cost": 36000},
      "security": {"count": 5, "cost": 598000},
      "database": {"count": 1, "cost": 285000},
      "bi_analytics": {"count": 1, "cost": 32500}
    },
    "by_criticality": {
      "critical": 11,
      "high": 15,
      "medium": 9,
      "low": 3
    },
    "specific_apps": [
      {
        "name": "Salesforce Sales Cloud",
        "vendor": "Salesforce",
        "cost": 245000,
        "criticality": "HIGH"
      },
      {
        "name": "NetSuite",
        "vendor": "Oracle",
        "cost": 180000,
        "criticality": "CRITICAL"
      },
      {
        "name": "Okta",
        "vendor": "Okta",
        "cost": 98000,
        "criticality": "CRITICAL"
      },
      {
        "name": "Datadog",
        "vendor": "Datadog",
        "cost": 150000,
        "criticality": "CRITICAL"
      }
    ],
    "expected_gaps": [
      {
        "gap_type": "carve_out_dependency",
        "reason": "CloudServe is standalone acquisition, not a carve-out scenario"
      }
    ]
  },

  "infrastructure": {
    "count": 120,
    "by_type": {
      "container": 85,
      "serverless": 12,
      "managed_service": 23
    },
    "by_environment": {
      "production": 45,
      "staging": 35,
      "development": 40
    }
  },

  "network": {
    "firewall_rules_count": 42,
    "vpn_tunnels_count": 4,
    "security_tools": [
      "CrowdStrike Falcon",
      "Wiz",
      "Okta"
    ]
  },

  "cybersecurity": {
    "compliance_frameworks": [
      "SOC 2 Type II",
      "ISO 27001"
    ],
    "vulnerabilities_count": 0
  },

  "identity": {
    "user_count": 412,
    "sso_provider": "Okta",
    "mfa_enabled": true
  },

  "organization": {
    "headcount": 45,
    "total_compensation": 6750000,
    "by_function": {
      "Engineering": 28,
      "DevOps": 8,
      "Security": 4,
      "IT Operations": 3,
      "Leadership": 2
    },
    "vendors_count": 12
  },

  "risks": {
    "critical": [
      "R-WIZ-CONTRACT-EXPIRING",
      "R-DATADOG-HIGH-COST",
      "R-DUAL-ERP-POTENTIAL"
    ],
    "high": [
      "R-SALESFORCE-COST",
      "R-SNOWFLAKE-GROWTH"
    ],
    "total_count": 25
  },

  "findings": {
    "work_items_count": 18,
    "work_items_by_phase": {
      "day_1": 6,
      "day_100": 8,
      "post_100": 4
    }
  },

  "completeness": {
    "overall_score": 87,
    "by_domain": {
      "applications": 95,
      "infrastructure": 88,
      "network": 82,
      "cybersecurity": 85,
      "identity": 90,
      "organization": 78
    }
  }
}
```

---

## Verification Strategy

### Schema Validation Testing

**Unit test:** `tests/unit/test_fixture_schema.py`

```python
import jsonschema
import json
from pathlib import Path

def test_cloudserve_fixture_validates():
    """CloudServe fixture matches schema."""
    schema = json.loads(Path("tests/golden/fixture_schema.json").read_text())
    fixture = json.loads(Path("tests/golden/cloudserve_expected.json").read_text())

    # Should not raise ValidationError
    jsonschema.validate(instance=fixture, schema=schema)

def test_invalid_fixture_rejected():
    """Fixture missing required fields is rejected."""
    schema = json.loads(Path("tests/golden/fixture_schema.json").read_text())
    invalid_fixture = {"metadata": {}}  # Missing required fields

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=invalid_fixture, schema=schema)
```

---

### Manual Verification

**Steps to create a new fixture:**

1. Run discovery pipeline on source documents
2. Review outputs manually for accuracy
3. Create fixture JSON with expected values from validated outputs
4. Run schema validation: `jsonschema -i cloudserve_expected.json fixture_schema.json`
5. Commit fixture to version control

**Steps to update existing fixture:**

1. Determine if change is intentional (e.g., improved extraction) or regression
2. If intentional: update fixture with new expected values, document in PR
3. If regression: fix pipeline, keep fixture unchanged
4. Re-run schema validation after update

---

## Benefits

### Why JSON Schema

1. **Machine-readable validation:** Automated checks prevent malformed fixtures
2. **Type safety:** Catches errors like string where integer expected
3. **Documentation:** Schema serves as spec for what fields are allowed
4. **Tooling support:** IDE autocomplete, linters, validators

### Why Per-Deal Fixtures

1. **Independence:** CloudServe changes don't break Great Insurance validation
2. **Specificity:** Each deal has unique expected outputs (different app counts, costs)
3. **Maintainability:** Update one fixture without cascading changes

### Alternatives Considered

**Alternative 1:** Single monolithic fixture with all deals
- **Rejected:** Hard to maintain, changes to one deal affect all validations

**Alternative 2:** No schema, just JSON files
- **Rejected:** No validation of fixture format, errors detected too late

**Alternative 3:** Python dataclasses instead of JSON
- **Rejected:** Less tool support, harder for non-Python users to edit

---

## Expectations

### Success Metrics

1. **Coverage:** Fixtures exist for all test deals (CloudServe, Great Insurance minimum)
2. **Accuracy:** Fixture values match validated pipeline outputs (manual review confirms)
3. **Completeness:** All 6 domains represented in every fixture
4. **Maintainability:** Fixture updates take <30 minutes per deal

### Acceptance Criteria

- [x] `fixture_schema.json` validates with jsonschema library
- [x] `cloudserve_expected.json` validates against schema
- [x] Schema covers all 6 IT DD domains
- [x] Example fixture demonstrates all schema features
- [x] Documentation exists for creating new fixtures (see `04-test-data-documentation.md`)

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Fixture drift:** Expected values become stale as pipeline improves | High | Version fixtures, review on every schema change |
| **Over-specification:** Too many specific apps listed, brittle | Medium | Only specify critical apps, use counts for rest |
| **Schema evolution:** Adding fields breaks old fixtures | Medium | Use JSON Schema `additionalProperties: true`, semantic versioning |
| **Manual fixture creation errors:** Typos, wrong values | High | Schema validation catches format errors, peer review for values |

---

## Results Criteria

### Definition of Done

1. **Schema file exists:** `tests/golden/fixture_schema.json` is valid JSON Schema Draft 2020-12
2. **CloudServe fixture exists:** `cloudserve_expected.json` validates against schema
3. **Schema coverage:** All required fields enforce presence of critical data
4. **Example complete:** CloudServe example demonstrates all schema sections
5. **Tooling works:** `jsonschema` CLI can validate fixtures

### Verification Commands

```bash
# Validate schema itself is valid JSON Schema
jsonschema --help  # Ensure tool installed

# Validate CloudServe fixture against schema
jsonschema -i tests/golden/cloudserve_expected.json tests/golden/fixture_schema.json

# Expected output: (no errors = success)
```

---

## Cross-References

- **01-test-validation-architecture.md:** FixtureLoader uses this schema for validation
- **03-validation-assertions.md:** Assertions compare actual outputs to fixture fields
- **04-test-data-documentation.md:** Instructions for creating fixtures following this schema
- **06-migration-rollout.md:** Rollout plan includes creating fixtures for existing deals
