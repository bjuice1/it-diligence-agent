"""
Complexity Signals Library

This module provides complexity signals that AI agents should look for
during document analysis. These signals directly affect cost estimates
through the AI weight layer.

Each signal has:
- Pattern: What to look for in documents
- Weight adjustment: How it affects cost estimates
- Questions to ask: Follow-up questions if signal detected
- Red flag indicators: When this becomes critical
"""

# =============================================================================
# COMPLEXITY SIGNALS BY CATEGORY
# =============================================================================

COMPLEXITY_SIGNALS = {
    # =========================================================================
    # INFRASTRUCTURE SIGNALS
    # =========================================================================
    "infrastructure": {
        "high_customization": {
            "weight_adjustment": 1.2,
            "patterns": [
                "custom", "customized", "modified", "bespoke",
                "proprietary scripts", "in-house developed",
                "heavily configured", "non-standard"
            ],
            "description": "High customization increases migration complexity",
            "questions": [
                "How many custom scripts/configurations exist?",
                "Is there documentation for customizations?",
                "Who maintains the custom components?"
            ],
            "red_flags": [
                "No documentation for customizations",
                "Original developer no longer available",
                "Custom code in production without source control"
            ]
        },
        "legacy_systems": {
            "weight_adjustment": 1.3,
            "patterns": [
                "mainframe", "AS/400", "iSeries", "COBOL",
                "Windows 2008", "Windows 2003", "RHEL 5", "RHEL 6",
                "end of life", "EOL", "end of support", "EOS",
                "legacy", "deprecated"
            ],
            "description": "Legacy systems require specialized skills and longer timelines",
            "questions": [
                "What business processes run on legacy systems?",
                "Is there a modernization roadmap?",
                "What skills are required to maintain?"
            ],
            "red_flags": [
                "Core business logic on unsupported systems",
                "No internal skills for legacy platform",
                "Vendor support contract expired"
            ]
        },
        "technical_debt": {
            "weight_adjustment": 1.15,
            "patterns": [
                "technical debt", "deferred maintenance",
                "needs upgrade", "overdue", "backlog",
                "workaround", "temporary fix", "band-aid",
                "known issues", "TODO"
            ],
            "description": "Technical debt adds hidden complexity to integration",
            "questions": [
                "What's the prioritized technical debt backlog?",
                "What's the annual spend on maintenance vs new features?",
                "Are there known stability issues?"
            ],
            "red_flags": [
                "No visibility into technical debt",
                "Frequent production incidents",
                "Key systems on unsupported versions"
            ]
        },
        "single_point_of_failure": {
            "weight_adjustment": 1.2,
            "patterns": [
                "single data center", "one DC", "no redundancy",
                "single server", "no failover", "no DR",
                "single point of failure", "SPOF"
            ],
            "description": "Lack of redundancy requires DR investment",
            "questions": [
                "What's the DR strategy?",
                "What's the acceptable downtime?",
                "Has DR been tested?"
            ],
            "red_flags": [
                "No DR plan exists",
                "DR never tested",
                "Production on single server"
            ]
        },
        "complex_integrations": {
            "weight_adjustment": 1.25,
            "patterns": [
                "point-to-point", "spaghetti", "tightly coupled",
                "direct database", "file transfer", "FTP",
                "custom API", "undocumented interface"
            ],
            "description": "Complex integrations multiply migration effort",
            "questions": [
                "How many system integrations exist?",
                "Is there an integration inventory?",
                "What's the integration architecture?"
            ],
            "red_flags": [
                "No integration documentation",
                "Direct database connections between systems",
                "Undocumented file-based integrations"
            ]
        }
    },

    # =========================================================================
    # APPLICATION SIGNALS
    # =========================================================================
    "applications": {
        "erp_complexity": {
            "weight_adjustment": 1.3,
            "patterns": [
                "dual ERP", "two ERPs", "multiple ERP",
                "SAP customization", "Z-transaction", "custom ABAP",
                "Oracle modifications", "custom forms",
                "heavily modified", "custom modules"
            ],
            "description": "ERP complexity significantly affects integration cost",
            "questions": [
                "How many custom objects/transactions?",
                "What's the upgrade history?",
                "Are modifications documented?"
            ],
            "red_flags": [
                "Dual ERP environment",
                "More than 100 custom objects",
                "No upgrade in 5+ years"
            ]
        },
        "shadow_it": {
            "weight_adjustment": 1.15,
            "patterns": [
                "shadow IT", "departmental systems",
                "spreadsheet", "Access database",
                "undocumented application", "rogue",
                "business-owned", "not managed by IT"
            ],
            "description": "Shadow IT creates hidden migration scope",
            "questions": [
                "Is there a complete application inventory?",
                "What business-critical processes run outside IT?",
                "How is data in shadow systems managed?"
            ],
            "red_flags": [
                "Critical business processes in spreadsheets",
                "No application inventory",
                "Departmental databases with customer data"
            ]
        },
        "vendor_lock_in": {
            "weight_adjustment": 1.1,
            "patterns": [
                "proprietary", "vendor lock-in", "single vendor",
                "no exit clause", "exclusive", "custom connector"
            ],
            "description": "Vendor lock-in limits migration options",
            "questions": [
                "What are the contract terms?",
                "Is data export possible?",
                "What's the migration path?"
            ],
            "red_flags": [
                "No data export capability",
                "Long-term contract with penalties",
                "Proprietary data format"
            ]
        }
    },

    # =========================================================================
    # SECURITY & COMPLIANCE SIGNALS
    # =========================================================================
    "security": {
        "compliance_gaps": {
            "weight_adjustment": 1.25,
            "patterns": [
                "not compliant", "gap", "finding", "audit",
                "remediation", "failed", "exception",
                "waiver", "compensating control"
            ],
            "description": "Compliance gaps require remediation investment",
            "questions": [
                "What frameworks are in scope?",
                "When was last audit?",
                "What are open findings?"
            ],
            "red_flags": [
                "Failed recent audit",
                "Multiple open findings",
                "No compliance program"
            ]
        },
        "security_debt": {
            "weight_adjustment": 1.2,
            "patterns": [
                "vulnerability", "unpatched", "CVE",
                "no EDR", "no SIEM", "no MFA",
                "admin password", "shared credentials",
                "security incident", "breach"
            ],
            "description": "Security gaps require immediate investment",
            "questions": [
                "What's the patching cadence?",
                "Is there vulnerability management?",
                "Has there been a security assessment?"
            ],
            "red_flags": [
                "Recent breach or incident",
                "Critical unpatched vulnerabilities",
                "No security monitoring"
            ]
        },
        "data_sensitivity": {
            "weight_adjustment": 1.15,
            "patterns": [
                "PII", "PHI", "PCI", "credit card",
                "health information", "financial data",
                "personally identifiable", "sensitive",
                "HIPAA", "GDPR", "CCPA"
            ],
            "description": "Sensitive data increases compliance scope",
            "questions": [
                "What sensitive data exists?",
                "Where is it stored?",
                "What protections are in place?"
            ],
            "red_flags": [
                "No data classification",
                "Sensitive data without encryption",
                "No data inventory"
            ]
        }
    },

    # =========================================================================
    # ORGANIZATIONAL SIGNALS
    # =========================================================================
    "organization": {
        "key_person_dependency": {
            "weight_adjustment": 1.2,
            "patterns": [
                "one person knows", "tribal knowledge",
                "key person", "single point", "only",
                "irreplaceable", "institutional knowledge"
            ],
            "description": "Key person dependencies create transition risk",
            "questions": [
                "Who are the critical IT staff?",
                "Is knowledge documented?",
                "What's the retention plan?"
            ],
            "red_flags": [
                "Single person manages critical system",
                "No documentation",
                "Key person planning to leave"
            ]
        },
        "outsourcing_complexity": {
            "weight_adjustment": 1.15,
            "patterns": [
                "outsourced", "offshore", "managed service",
                "MSP", "third party", "contractor",
                "vendor managed"
            ],
            "description": "Outsourcing adds transition complexity",
            "questions": [
                "What's outsourced vs internal?",
                "What are the contract terms?",
                "Can contracts be assigned?"
            ],
            "red_flags": [
                "Critical systems fully outsourced",
                "No internal knowledge of outsourced systems",
                "Contract not assignable"
            ]
        },
        "change_resistance": {
            "weight_adjustment": 1.1,
            "patterns": [
                "resistance", "pushback", "won't change",
                "always done it this way", "political",
                "silos", "not aligned"
            ],
            "description": "Change resistance extends timelines",
            "questions": [
                "What's the change management history?",
                "How are IT decisions made?",
                "What's the IT governance structure?"
            ],
            "red_flags": [
                "Failed IT projects due to resistance",
                "No executive sponsorship for IT",
                "IT not at leadership table"
            ]
        }
    },

    # =========================================================================
    # M&A SPECIFIC SIGNALS
    # =========================================================================
    "ma_integration": {
        "carveout_entanglement": {
            "weight_adjustment": 1.4,
            "patterns": [
                "shared services", "parent company",
                "shared infrastructure", "common systems",
                "entangled", "commingled"
            ],
            "description": "Carveout entanglement significantly increases separation cost",
            "questions": [
                "What's shared with parent?",
                "What needs to be replicated?",
                "What's the TSA scope?"
            ],
            "red_flags": [
                "Core systems shared with parent",
                "No clear separation boundary",
                "Entangled data"
            ]
        },
        "tsa_dependency": {
            "weight_adjustment": 1.2,
            "patterns": [
                "TSA", "transition service", "temporary",
                "parent provided", "shared until"
            ],
            "description": "TSA dependencies create timeline pressure",
            "questions": [
                "What services are in TSA scope?",
                "What's the TSA duration?",
                "What's the exit cost?"
            ],
            "red_flags": [
                "TSA duration too short for separation",
                "High TSA exit fees",
                "Critical services with no standalone option"
            ]
        },
        "prior_ma_history": {
            "weight_adjustment": 1.25,
            "patterns": [
                "prior acquisition", "bolt-on", "roll-up",
                "previously acquired", "merged",
                "never fully integrated"
            ],
            "description": "Incomplete prior integrations add complexity",
            "questions": [
                "What prior M&A activity?",
                "Were prior deals fully integrated?",
                "What technical debt from prior deals?"
            ],
            "red_flags": [
                "Multiple un-integrated acquisitions",
                "Different systems per acquired entity",
                "No single source of truth"
            ]
        }
    }
}


# =============================================================================
# INDUSTRY-SPECIFIC SIGNALS
# =============================================================================

INDUSTRY_SIGNALS = {
    "healthcare": {
        "patterns": [
            "EMR", "EHR", "Epic", "Cerner", "MEDITECH",
            "HIPAA", "PHI", "clinical", "patient",
            "medical device", "HL7", "FHIR"
        ],
        "considerations": [
            "EMR platform and customization level",
            "HIPAA compliance status",
            "Medical device integration",
            "Clinical workflow dependencies",
            "BAA inventory completeness"
        ],
        "red_flags": [
            "Multiple EMR systems",
            "PHI in unencrypted storage",
            "No BAA inventory",
            "Legacy medical devices (Windows XP)"
        ]
    },
    "financial_services": {
        "patterns": [
            "core banking", "trading", "settlement",
            "SOX", "PCI", "GLBA", "regulatory",
            "mainframe", "batch processing"
        ],
        "considerations": [
            "Core banking platform age",
            "SOX control scope",
            "Trading system latency requirements",
            "Regulatory reporting automation",
            "Mainframe dependencies"
        ],
        "red_flags": [
            "Manual regulatory reporting",
            "SOX findings open",
            "Core banking on unsupported platform",
            "No PCI compliance"
        ]
    },
    "manufacturing": {
        "patterns": [
            "OT", "SCADA", "PLC", "HMI", "MES",
            "shop floor", "plant", "ICS",
            "safety system", "24/7"
        ],
        "considerations": [
            "OT/IT segmentation",
            "MES/ERP integration",
            "Plant network architecture",
            "Safety system compliance",
            "Change window constraints"
        ],
        "red_flags": [
            "Flat OT network",
            "Windows XP on shop floor",
            "No OT security program",
            "Undocumented PLC code"
        ]
    },
    "government": {
        "patterns": [
            "FedRAMP", "FISMA", "NIST", "CUI",
            "clearance", "classified", "CMMC",
            "government", "federal", "agency"
        ],
        "considerations": [
            "FedRAMP authorization status",
            "Clearance requirements",
            "CMMC level needed",
            "CUI handling",
            "Agency-specific requirements"
        ],
        "red_flags": [
            "No FedRAMP authorization",
            "Clearance gaps",
            "CMMC not started",
            "CUI not identified"
        ]
    }
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_complexity_signals_for_domain(domain: str) -> dict:
    """Get complexity signals for a specific domain."""
    return COMPLEXITY_SIGNALS.get(domain, {})


def get_industry_signals(industry: str) -> dict:
    """Get industry-specific signals."""
    return INDUSTRY_SIGNALS.get(industry.lower(), {})


def calculate_ai_weight(detected_signals: list) -> float:
    """
    Calculate the AI weight adjustment based on detected signals.

    Args:
        detected_signals: List of signal keys that were detected

    Returns:
        Combined weight adjustment (multiplicative)
    """
    weight = 1.0

    for signal_key in detected_signals:
        # Find the signal in any category
        for domain, signals in COMPLEXITY_SIGNALS.items():
            if signal_key in signals:
                weight *= signals[signal_key]["weight_adjustment"]
                break

    # Cap at reasonable bounds
    return min(max(weight, 0.8), 2.0)


def get_signal_prompt_injection(domain: str, industry: str = None) -> str:
    """
    Generate prompt text for complexity signals to inject into agent prompts.

    Args:
        domain: The domain being analyzed (infrastructure, applications, etc.)
        industry: Optional industry for industry-specific signals

    Returns:
        Formatted prompt text
    """
    lines = [
        "\n## COMPLEXITY SIGNALS TO WATCH FOR\n",
        "Look for these signals that affect cost estimates:\n"
    ]

    # Add domain signals
    domain_signals = COMPLEXITY_SIGNALS.get(domain, {})
    if domain_signals:
        for signal_name, signal_data in domain_signals.items():
            lines.append(f"\n### {signal_name.replace('_', ' ').title()}")
            lines.append(f"**Weight: {signal_data['weight_adjustment']}x** - {signal_data['description']}")
            lines.append(f"Look for: {', '.join(signal_data['patterns'][:5])}")
            lines.append(f"Red flags: {', '.join(signal_data['red_flags'][:3])}")

    # Add industry signals if specified
    if industry and industry.lower() in INDUSTRY_SIGNALS:
        ind_signals = INDUSTRY_SIGNALS[industry.lower()]
        lines.append(f"\n## INDUSTRY-SPECIFIC ({industry.upper()})\n")
        lines.append(f"Key patterns: {', '.join(ind_signals['patterns'][:5])}")
        lines.append(f"Consider: {', '.join(ind_signals['considerations'][:3])}")
        lines.append(f"Red flags: {', '.join(ind_signals['red_flags'][:3])}")

    return "\n".join(lines)
