"""
Industry Application Considerations Repository

This module provides industry-specific application considerations for the
discovery agent. When an industry is detected, the agent uses this to:
1. Ask relevance questions to confirm applicability
2. Probe for expected application types specific to that industry
3. Ask management/integration questions
4. Flag gaps against industry expectations (not just generic "missing")

Usage:
    from prompts.shared.industry_application_considerations import (
        get_industry_considerations,
        detect_industry_from_text,
        inject_industry_into_discovery_prompt,
        assess_industry_application_gaps
    )
"""

from typing import Dict, List, Optional, Tuple

# =============================================================================
# INDUSTRY APPLICATION CONSIDERATIONS
# =============================================================================

INDUSTRY_APPLICATION_CONSIDERATIONS = {

    # =========================================================================
    # HEALTHCARE
    # =========================================================================
    "healthcare": {
        "display_name": "Healthcare",
        "triggers": [
            "hospital", "clinic", "medical", "healthcare", "health system",
            "physician", "patient", "clinical", "ambulatory", "acute care",
            "EMR", "EHR", "Epic", "Cerner", "MEDITECH", "athenahealth",
            "HIPAA", "PHI", "protected health information"
        ],

        "relevance_questions": [
            "Do they provide direct patient care or clinical services?",
            "Do they store or process Protected Health Information (PHI)?",
            "Are they a covered entity or business associate under HIPAA?",
            "What type of healthcare (hospital, clinic, specialty, post-acute)?"
        ],

        "expected_applications": {
            "emr_ehr": {
                "name": "Electronic Medical/Health Record",
                "purpose": "Clinical documentation, orders, patient care workflows",
                "common_vendors": ["Epic", "Cerner (Oracle Health)", "MEDITECH", "athenahealth", "eClinicalWorks", "NextGen", "Allscripts"],
                "questions": [
                    "What EMR/EHR system is used?",
                    "Is it deployed on-prem, hosted, or SaaS?",
                    "How heavily customized is the build?",
                    "What's the current version and upgrade status?"
                ],
                "integration_points": ["Practice management", "Revenue cycle", "Lab systems", "Imaging"],
                "compliance_drivers": ["HIPAA", "Meaningful Use", "MIPS/MACRA"],
                "gap_risk": "critical"
            },
            "practice_management": {
                "name": "Practice Management / Scheduling",
                "purpose": "Patient scheduling, registration, front-office workflows",
                "common_vendors": ["Often integrated with EMR", "Athena", "AdvancedMD", "Kareo"],
                "questions": [
                    "Is practice management integrated with EMR or separate?",
                    "How is patient scheduling managed?",
                    "What's the check-in/registration workflow?"
                ],
                "integration_points": ["EMR", "Revenue cycle", "Patient portal"],
                "gap_risk": "high"
            },
            "revenue_cycle": {
                "name": "Revenue Cycle Management",
                "purpose": "Billing, claims, collections, denial management",
                "common_vendors": ["Epic", "Cerner", "Waystar", "Availity", "Change Healthcare", "R1 RCM"],
                "questions": [
                    "Is billing integrated with EMR or separate system?",
                    "What clearinghouse is used for claims?",
                    "How are denials managed and worked?"
                ],
                "integration_points": ["EMR", "Practice management", "Payer systems"],
                "gap_risk": "high"
            },
            "pacs_imaging": {
                "name": "PACS / Medical Imaging",
                "purpose": "Medical image storage, viewing, distribution",
                "common_vendors": ["GE Healthcare", "Philips", "Fujifilm", "Agfa", "Change Healthcare"],
                "questions": [
                    "What PACS system is used for imaging?",
                    "Is there a vendor-neutral archive (VNA)?",
                    "How is imaging integrated with EMR?"
                ],
                "integration_points": ["EMR", "Radiology workflow", "Specialty systems"],
                "gap_risk": "high_if_imaging_services"
            },
            "lab_information_system": {
                "name": "Laboratory Information System (LIS)",
                "purpose": "Lab order management, results, specimen tracking",
                "common_vendors": ["Cerner PathNet", "Epic Beaker", "Sunquest", "Orchard"],
                "questions": [
                    "Is lab in-house or reference lab?",
                    "What LIS is used?",
                    "How do lab results flow to EMR?"
                ],
                "integration_points": ["EMR", "Instruments", "Reference labs"],
                "gap_risk": "high_if_lab_services"
            },
            "patient_portal": {
                "name": "Patient Portal",
                "purpose": "Patient access to records, messaging, scheduling",
                "common_vendors": ["MyChart (Epic)", "Cerner Patient Portal", "athenaPatient", "Healow"],
                "questions": [
                    "What patient portal is offered?",
                    "What features are enabled (messaging, scheduling, bill pay)?",
                    "What's the patient adoption rate?"
                ],
                "compliance_drivers": ["HIPAA", "21st Century Cures Act (Information Blocking)"],
                "gap_risk": "medium"
            },
            "telehealth": {
                "name": "Telehealth / Virtual Care",
                "purpose": "Video visits, remote patient monitoring",
                "common_vendors": ["Teladoc", "Amwell", "Doxy.me", "Epic Video Visit", "Zoom for Healthcare"],
                "questions": [
                    "What telehealth platform is used?",
                    "Is it integrated with the EMR?",
                    "What's the telehealth visit volume?"
                ],
                "compliance_drivers": ["HIPAA", "State telehealth regs"],
                "gap_risk": "medium"
            }
        },

        "management_questions": [
            "How does data flow between clinical and financial systems?",
            "Is there a health information exchange (HIE) connection?",
            "What's the interoperability strategy (FHIR, HL7)?",
            "How is PHI access logged and monitored?",
            "What's the BAA inventory for vendors with PHI access?"
        ],

        "compliance_drivers": ["HIPAA", "HITECH", "21st Century Cures", "State privacy laws", "CMS Conditions of Participation"],

        "diligence_considerations": {
            "key_questions": [
                "When was the last HIPAA risk assessment and what were the findings?",
                "Have there been any PHI breaches or OCR complaints in the past 3 years?",
                "What is the BAA inventory status - are all vendors covered?",
                "Is the EMR current on support or facing end-of-life?",
                "What is the IT security posture relative to HIPAA requirements?",
                "Are there any outstanding CMS survey deficiencies?"
            ],
            "red_flags": [
                "No documented HIPAA risk assessment in past 2 years",
                "History of PHI breaches or OCR investigations",
                "EMR system on extended support or end-of-life",
                "Incomplete BAA inventory - vendors handling PHI without BAAs",
                "No dedicated privacy/security officer",
                "Paper-based processes with PHI",
                "Unencrypted PHI in transit or at rest",
                "No audit logging for PHI access",
                "Multiple disparate EMR systems not integrated"
            ],
            "cost_implications": {
                "emr_replacement": "EMR replacement/migration: $5M-$50M+ depending on size",
                "emr_upgrade": "Major EMR upgrade: $1M-$10M",
                "hipaa_remediation": "HIPAA gap remediation: $200K-$1M",
                "security_program": "Security program buildout: $300K-$800K",
                "integration_work": "Clinical system integration: $500K-$3M",
                "breach_exposure": "Average healthcare breach cost: $10M+"
            },
            "integration_considerations": [
                "EMR migrations are high-risk, multi-year projects",
                "Clinical workflow disruption can impact patient care and revenue",
                "Physician adoption/change management is critical success factor",
                "BAAs may need to be novated or re-executed post-transaction",
                "State health data laws may impose additional requirements",
                "HIE connections may need to be re-established"
            ],
            "what_good_looks_like": [
                "Current HIPAA risk assessment with remediation plan",
                "Modern, supported EMR platform (Epic, Cerner)",
                "Designated privacy and security officers",
                "Complete BAA inventory with tracking",
                "Encryption at rest and in transit for all PHI",
                "Regular security awareness training",
                "Clean audit history with regulators"
            ]
        }
    },

    # =========================================================================
    # FINANCIAL SERVICES
    # =========================================================================
    "financial_services": {
        "display_name": "Financial Services",
        "triggers": [
            "bank", "banking", "credit union", "lending", "mortgage",
            "wealth management", "asset management", "investment",
            "trading", "brokerage", "securities", "capital markets",
            "SOX", "GLBA", "FINRA", "SEC", "OCC", "FDIC",
            "core banking", "loan origination"
        ],

        "relevance_questions": [
            "What type of financial services (banking, lending, wealth, trading)?",
            "Are they regulated by federal banking regulators (OCC, FDIC, Fed)?",
            "Do they have broker-dealer operations (FINRA)?",
            "Is this a registered investment advisor (SEC/state)?",
            "Do they handle cardholder data (PCI scope)?"
        ],

        "expected_applications": {
            "core_banking": {
                "name": "Core Banking System",
                "purpose": "Deposit accounts, general ledger, customer master",
                "common_vendors": ["FIS", "Fiserv", "Jack Henry", "Temenos", "Finastra", "nCino"],
                "questions": [
                    "What core banking platform is used?",
                    "How old is the platform and what version?",
                    "Is it on-prem, hosted, or SaaS?",
                    "How customized is the implementation?"
                ],
                "integration_points": ["Digital banking", "Lending", "GL", "Regulatory reporting"],
                "compliance_drivers": ["SOX", "BSA/AML", "GLBA"],
                "gap_risk": "critical"
            },
            "loan_origination": {
                "name": "Loan Origination System (LOS)",
                "purpose": "Loan application, underwriting, closing",
                "common_vendors": ["Encompass (ICE)", "Blend", "nCino", "Finastra"],
                "questions": [
                    "What LOS is used for each loan type?",
                    "How is underwriting automated vs. manual?",
                    "How does LOS integrate with core and servicing?"
                ],
                "integration_points": ["Core banking", "Loan servicing", "Credit bureaus", "Doc prep"],
                "compliance_drivers": ["TRID", "HMDA", "Fair lending"],
                "gap_risk": "critical_if_lending"
            },
            "loan_servicing": {
                "name": "Loan Servicing System",
                "purpose": "Payment processing, escrow, collections",
                "common_vendors": ["Black Knight MSP", "Sagent", "FICS"],
                "questions": [
                    "What system handles loan servicing?",
                    "Is servicing in-house or subserviced?",
                    "How is escrow managed?"
                ],
                "compliance_drivers": ["RESPA", "CFPB servicing rules"],
                "gap_risk": "critical_if_servicing"
            },
            "digital_banking": {
                "name": "Digital Banking (Online/Mobile)",
                "purpose": "Customer-facing online and mobile banking",
                "common_vendors": ["Q2", "Alkami", "NCR Digital Banking", "Fiserv"],
                "questions": [
                    "What digital banking platform is used?",
                    "What features are enabled?",
                    "How does it integrate with core?"
                ],
                "integration_points": ["Core banking", "Bill pay", "P2P", "Card systems"],
                "gap_risk": "high"
            },
            "trading_systems": {
                "name": "Trading / Order Management",
                "purpose": "Trade execution, order routing, position management",
                "common_vendors": ["Bloomberg", "Refinitiv", "Charles River", "SS&C Eze"],
                "questions": [
                    "What trading platform is used?",
                    "What asset classes are traded?",
                    "How is best execution monitored?"
                ],
                "compliance_drivers": ["SEC", "FINRA", "MiFID II (if applicable)"],
                "gap_risk": "critical_if_trading"
            },
            "treasury_management": {
                "name": "Treasury / Cash Management",
                "purpose": "Cash positioning, liquidity management, FX",
                "common_vendors": ["Kyriba", "GTreasury", "FIS", "ION Treasury"],
                "questions": [
                    "What treasury management system is used?",
                    "How is cash positioning managed?",
                    "What's the bank connectivity approach?"
                ],
                "integration_points": ["ERP/GL", "Banking portals", "Trading"],
                "gap_risk": "medium"
            },
            "aml_compliance": {
                "name": "AML / BSA Compliance",
                "purpose": "Transaction monitoring, KYC, SAR filing",
                "common_vendors": ["Actimize", "SAS", "Verafin", "Oracle FCCM"],
                "questions": [
                    "What AML transaction monitoring system is used?",
                    "How is KYC/CDD managed?",
                    "What's the SAR filing process?"
                ],
                "compliance_drivers": ["BSA", "AML", "OFAC"],
                "gap_risk": "critical"
            },
            "regulatory_reporting": {
                "name": "Regulatory Reporting",
                "purpose": "Call reports, HMDA, CRA, stress testing",
                "common_vendors": ["Axiom (Wolters Kluwer)", "Workiva", "AxiomSL"],
                "questions": [
                    "How is regulatory reporting managed?",
                    "What reports are filed (Call Report, HMDA, CRA)?",
                    "How automated vs. manual is the process?"
                ],
                "compliance_drivers": ["FFIEC", "CFPB", "SEC"],
                "gap_risk": "high"
            }
        },

        "management_questions": [
            "How is data reconciled between core and downstream systems?",
            "What's the SOX control environment for IT?",
            "How is segregation of duties enforced in systems?",
            "What's the change management process for production systems?",
            "How is market data managed and licensed?"
        ],

        "compliance_drivers": ["SOX", "GLBA", "BSA/AML", "PCI-DSS", "FFIEC guidance", "FINRA", "SEC", "State regulators"],

        "diligence_considerations": {
            "key_questions": [
                "What were the results of the most recent regulatory exam (OCC, FDIC, state)?",
                "Are there any open MRAs (Matters Requiring Attention) or consent orders?",
                "What is the status of SOX IT controls - any material weaknesses?",
                "When was the last BSA/AML independent review and what were findings?",
                "Is the core banking system current or facing end-of-life?",
                "What is the PCI compliance status and scope?"
            ],
            "red_flags": [
                "Open consent orders or enforcement actions",
                "Material weaknesses in IT controls",
                "Core banking system on extended support or unsupported",
                "BSA/AML program deficiencies noted by examiners",
                "Failed or qualified SOX audits",
                "PCI non-compliance or recent cardholder data breach",
                "Manual regulatory reporting processes",
                "Inadequate segregation of duties in key systems",
                "No formal IT risk management program",
                "FFIEC cybersecurity assessment gaps"
            ],
            "cost_implications": {
                "core_banking_replacement": "Core banking replacement: $10M-$100M+ (multi-year)",
                "core_upgrade": "Major core upgrade: $2M-$15M",
                "sox_remediation": "SOX IT control remediation: $500K-$3M",
                "bsa_aml_program": "BSA/AML program enhancement: $500K-$2M",
                "regulatory_remediation": "Consent order remediation: $2M-$20M+",
                "digital_banking": "Digital banking platform: $1M-$10M",
                "security_program": "Cybersecurity program buildout: $500K-$2M"
            },
            "integration_considerations": [
                "Core banking conversions are high-risk, 18-36 month projects",
                "Regulatory approval often required for bank M&A",
                "Charter and licensing implications for ownership changes",
                "Customer notification requirements for privacy/GLBA",
                "Contract assignment restrictions on core vendor agreements",
                "Data migration and reconciliation is complex and audit-sensitive"
            ],
            "what_good_looks_like": [
                "Clean regulatory exam history",
                "Modern, supported core banking platform",
                "SOX IT controls with no material weaknesses",
                "Mature BSA/AML program with independent validation",
                "FFIEC cybersecurity assessment at target maturity",
                "Documented IT risk management program",
                "Strong vendor management program",
                "Automated regulatory reporting"
            ]
        }
    },

    # =========================================================================
    # MANUFACTURING
    # =========================================================================
    "manufacturing": {
        "display_name": "Manufacturing",
        "triggers": [
            "manufacturing", "factory", "plant", "production", "shop floor",
            "assembly", "fabrication", "machining", "OEM", "discrete",
            "process manufacturing", "batch", "MES", "SCADA", "PLC",
            "lean", "six sigma", "ISO 9001"
        ],

        "relevance_questions": [
            "Do they have manufacturing/production facilities?",
            "What type of manufacturing (discrete, process, batch, mixed)?",
            "How many plants/facilities?",
            "Are they subject to environmental/safety regulations?",
            "Do they have OT/industrial control systems?"
        ],

        "expected_applications": {
            "mes": {
                "name": "Manufacturing Execution System (MES)",
                "purpose": "Shop floor scheduling, work instructions, production tracking, WIP",
                "common_vendors": ["Rockwell Plex", "SAP ME/MII", "Siemens Opcenter", "AVEVA", "Aegis FactoryLogix", "42Q"],
                "questions": [
                    "What system manages shop floor execution?",
                    "How are work orders tracked through production?",
                    "Is production data captured automatically or manually?",
                    "How does MES connect to ERP?"
                ],
                "integration_points": ["ERP", "QMS", "SCADA/OT", "PLM"],
                "gap_risk": "medium"
            },
            "ehs": {
                "name": "Environmental Health & Safety (EHS)",
                "purpose": "Incident tracking, compliance management, training, chemical/SDS management",
                "common_vendors": ["Intelex", "VelocityEHS", "Enablon (Wolters Kluwer)", "Gensuite", "Benchmark ESG"],
                "questions": [
                    "What system tracks safety incidents and near-misses?",
                    "How is environmental compliance managed?",
                    "Is chemical inventory / SDS management in place?",
                    "How is safety training tracked?"
                ],
                "compliance_drivers": ["OSHA", "EPA", "State environmental"],
                "gap_risk": "high"
            },
            "qms": {
                "name": "Quality Management System (QMS)",
                "purpose": "Document control, NCRs, CAPA, audits, inspection",
                "common_vendors": ["MasterControl", "ETQ", "Qualio", "SAP QM", "Sparta TrackWise", "Greenlight Guru"],
                "questions": [
                    "What system manages quality documentation?",
                    "How are nonconformances and CAPAs tracked?",
                    "Is document control integrated or standalone?",
                    "How are supplier quality issues managed?"
                ],
                "compliance_drivers": ["ISO 9001", "IATF 16949", "AS9100", "Customer audits"],
                "gap_risk": "high"
            },
            "plm": {
                "name": "Product Lifecycle Management (PLM)",
                "purpose": "Product design, BOM management, engineering change",
                "common_vendors": ["Siemens Teamcenter", "PTC Windchill", "Dassault ENOVIA", "Arena PLM", "Autodesk Fusion"],
                "questions": [
                    "What system manages product design and BOMs?",
                    "How are engineering changes controlled?",
                    "How does PLM connect to ERP for BOM sync?"
                ],
                "integration_points": ["CAD", "ERP", "MES"],
                "gap_risk": "medium"
            },
            "ot_scada": {
                "name": "OT / SCADA / Industrial Control",
                "purpose": "Production equipment control, monitoring, data historian",
                "common_vendors": ["Rockwell", "Siemens", "Schneider Electric", "Honeywell", "ABB", "GE", "OSIsoft PI"],
                "questions": [
                    "What controls production equipment (PLCs, DCS)?",
                    "Is there a historian for production data?",
                    "How is OT network segmented from IT?",
                    "What's the patching/update approach for OT systems?"
                ],
                "security_considerations": ["OT/IT segmentation", "Legacy OS", "Patching constraints", "Remote access"],
                "gap_risk": "context_dependent"
            },
            "cmms_eam": {
                "name": "CMMS / Enterprise Asset Management",
                "purpose": "Equipment maintenance, work orders, spare parts",
                "common_vendors": ["IBM Maximo", "SAP PM", "Infor EAM", "UpKeep", "Fiix", "eMaint"],
                "questions": [
                    "What system manages equipment maintenance?",
                    "Is preventive maintenance scheduled automatically?",
                    "How is spare parts inventory managed?"
                ],
                "integration_points": ["ERP", "OT/SCADA", "Procurement"],
                "gap_risk": "medium"
            },
            "supply_chain_planning": {
                "name": "Supply Chain Planning",
                "purpose": "Demand planning, S&OP, inventory optimization",
                "common_vendors": ["Kinaxis", "o9 Solutions", "Blue Yonder", "SAP IBP", "Oracle ASCP"],
                "questions": [
                    "What's used for demand planning and forecasting?",
                    "Is there a formal S&OP process and supporting system?",
                    "How is inventory optimization managed?"
                ],
                "integration_points": ["ERP", "CRM", "WMS"],
                "gap_risk": "medium"
            }
        },

        "management_questions": [
            "How do MES and ERP integrate for production planning?",
            "Is there real-time visibility from shop floor to ERP?",
            "Who manages OT systems - IT or plant engineering?",
            "What's the change management process for production systems?",
            "How is production data used for reporting and analytics?"
        ],

        "compliance_drivers": ["OSHA", "EPA", "ISO 9001", "IATF 16949 (auto)", "Customer quality requirements"],

        "diligence_considerations": {
            "key_questions": [
                "What quality certifications are held (ISO 9001, IATF 16949, AS9100)?",
                "When were the last certification audits and what were the findings?",
                "Are there any open OSHA citations or EPA violations?",
                "What is the OT/IT security posture - is OT network segmented?",
                "How old are the production control systems (PLCs, SCADA)?",
                "Is there a documented EHS program with tracking?"
            ],
            "red_flags": [
                "Loss of quality certification or failed surveillance audits",
                "Open OSHA citations or EPA consent orders",
                "Flat network with OT and IT commingled",
                "Production systems running unsupported OS (Windows XP)",
                "No formal EHS management system",
                "Critical production knowledge held by single individuals",
                "No documented OT asset inventory",
                "Legacy PLCs with no upgrade path",
                "Paper-based quality records",
                "No MES - reliance on spreadsheets for production tracking"
            ],
            "cost_implications": {
                "mes_implementation": "MES implementation: $500K-$3M per plant",
                "erp_manufacturing": "Manufacturing ERP implementation: $1M-$10M",
                "ot_security": "OT security program: $200K-$800K",
                "ot_modernization": "OT/SCADA modernization: $500K-$5M per plant",
                "ehs_system": "EHS system implementation: $100K-$500K",
                "qms_implementation": "QMS implementation: $150K-$500K",
                "certification_remediation": "Quality certification remediation: $100K-$400K"
            },
            "integration_considerations": [
                "OT systems often have long change windows tied to production schedules",
                "Quality certifications may need to be re-audited post-transaction",
                "Customer quality approvals may need to be re-obtained",
                "Production disruption risk during any system changes",
                "Tribal knowledge in plant operations is common",
                "Union considerations for technology changes"
            ],
            "what_good_looks_like": [
                "Current quality certifications with clean audit history",
                "Segmented OT network with documented architecture",
                "Modern MES integrated with ERP",
                "Documented EHS program with incident tracking",
                "OT asset inventory with lifecycle management",
                "Defined OT patching and change management process",
                "Real-time production visibility",
                "Quality records in electronic QMS"
            ]
        }
    },

    # =========================================================================
    # AVIATION / AEROSPACE MRO
    # =========================================================================
    "aviation_mro": {
        "display_name": "Aviation / Aerospace MRO",
        "triggers": [
            "MRO", "maintenance repair overhaul", "aviation", "aerospace",
            "aircraft", "airline", "Part 145", "Part 121", "Part 135",
            "FAA", "EASA", "airworthiness", "component repair",
            "engine overhaul", "airframe", "avionics"
        ],

        "relevance_questions": [
            "Do they perform aircraft/component maintenance (MRO)?",
            "What FAA certifications do they hold (Part 145, Part 121, Part 135)?",
            "Do they work on commercial, military, or general aviation?",
            "Do they have defense/government contracts?",
            "Do they handle ITAR-controlled articles or technical data?"
        ],

        "expected_applications": {
            "mro_system": {
                "name": "MRO / Aviation Maintenance System",
                "purpose": "Work orders, component tracking, repair history, airworthiness",
                "common_vendors": ["AMOS", "Ramco Aviation", "Quantum MRO", "IFS Maintenix", "TRAX", "Rusada Envision", "Commsoft OASES"],
                "questions": [
                    "What MRO system is used for work order management?",
                    "How is component traceability maintained?",
                    "Does it track back-to-birth history for life-limited parts?",
                    "How are airworthiness releases (8130-3/EASA Form 1) generated?"
                ],
                "integration_points": ["ERP", "QMS", "Tech pubs", "Inventory"],
                "compliance_drivers": ["FAA Part 145", "EASA Part 145", "Customer requirements"],
                "gap_risk": "critical"
            },
            "qms": {
                "name": "Quality Management System (AS9100/AS9110)",
                "purpose": "Document control, NCRs, CAPA, audits, supplier quality",
                "common_vendors": ["MasterControl", "ETQ", "Qualio", "IQS", "AssurX"],
                "questions": [
                    "What QMS supports AS9100D/AS9110C compliance?",
                    "How are nonconformances and CAPAs tracked?",
                    "Is document control integrated or separate from MRO?",
                    "How is supplier quality managed (OASIS, scorecards)?"
                ],
                "compliance_drivers": ["AS9100D", "AS9110C", "Nadcap", "Customer audits"],
                "gap_risk": "critical"
            },
            "technical_publications": {
                "name": "Technical Publications Management",
                "purpose": "OEM manuals, ADs, service bulletins, revision control",
                "common_vendors": ["Flatirons", "ATP", "Web Manuals", "Custom/OEM portals"],
                "questions": [
                    "How are OEM technical publications managed?",
                    "Is there a system for tracking AD compliance?",
                    "How are revision updates pushed to technicians?",
                    "How is task card creation linked to tech data?"
                ],
                "compliance_drivers": ["FAA", "OEM requirements"],
                "gap_risk": "high"
            },
            "component_tracking": {
                "name": "Component / Serialized Parts Tracking",
                "purpose": "Serial number tracking, time/cycle tracking, life limits",
                "common_vendors": ["Often within MRO system", "Standalone: Component Control"],
                "questions": [
                    "How are serialized parts tracked through repair?",
                    "Is there back-to-birth traceability for life-limited parts?",
                    "How are time/cycle updates managed?",
                    "How is BER (Beyond Economical Repair) determined?"
                ],
                "compliance_drivers": ["FAA", "OEM", "Customer"],
                "gap_risk": "critical"
            },
            "inventory_management": {
                "name": "Aviation Inventory / Materials",
                "purpose": "Parts inventory, rotables, consignment, core tracking",
                "common_vendors": ["Often within MRO/ERP", "Standalone aviation inventory systems"],
                "questions": [
                    "What system manages parts inventory?",
                    "How is consignment inventory tracked?",
                    "How are rotable exchanges managed?",
                    "How is shelf-life and certification status tracked?"
                ],
                "integration_points": ["MRO", "ERP", "Procurement"],
                "gap_risk": "high"
            },
            "export_control": {
                "name": "Export Control / ITAR Tracking",
                "purpose": "ITAR/EAR compliance, technology classification, access control",
                "common_vendors": ["OCR Services", "Amber Road (E2open)", "Manual processes common"],
                "questions": [
                    "How is ITAR-controlled data identified and segregated?",
                    "Is there a system for tracking US persons access?",
                    "How are export license requirements tracked?",
                    "How is technology transfer controlled?"
                ],
                "compliance_drivers": ["ITAR", "EAR", "DFARS"],
                "gap_risk": "critical_if_defense"
            },
            "customer_portal": {
                "name": "Customer Portal / AOG Support",
                "purpose": "Customer work order visibility, AOG requests, quotes",
                "common_vendors": ["Often custom or within MRO system"],
                "questions": [
                    "Do customers have portal access to work order status?",
                    "How are AOG requests handled and tracked?",
                    "How are quotes and approvals managed?"
                ],
                "gap_risk": "medium"
            }
        },

        "management_questions": [
            "How do MRO and QMS systems integrate?",
            "Is there an ERP, and how does it connect to MRO?",
            "How is traceability data passed between systems?",
            "What audits are performed (AS9100, DCMA, FAA, customer)?",
            "How is access to defense work segregated from commercial?",
            "How are technician certifications and authorizations tracked?"
        ],

        "compliance_drivers": ["FAA Part 145", "EASA Part 145", "AS9100D", "AS9110C", "Nadcap", "ITAR", "DFARS (if defense)", "Customer requirements"],

        "diligence_considerations": {
            "key_questions": [
                "What FAA/EASA certifications are held and what is their scope?",
                "When was the last FAA inspection and what were the findings?",
                "Is AS9100D/AS9110C certification current? Last audit results?",
                "What percentage of revenue is defense/government vs commercial?",
                "Are there any open corrective actions from FAA, DCMA, or customers?",
                "Do they handle ITAR-controlled articles or technical data?",
                "What is the CMMC requirement timeline if defense work exists?",
                "How is part traceability maintained - is back-to-birth achievable?",
                "Are there any Nadcap certifications and what is their status?"
            ],
            "red_flags": [
                "FAA certificate at risk or under enhanced surveillance",
                "Open FAA enforcement actions or civil penalties",
                "Loss or suspension of AS9100/AS9110 certification",
                "DCMA corrective action requests (CARs) open",
                "No MRO system - reliance on paper or spreadsheets",
                "Traceability gaps - inability to trace parts back-to-birth",
                "ITAR work without Technology Control Plan (TCP)",
                "Defense revenue but no CMMC plan or timeline",
                "Customer escapes (quality issues found by customer)",
                "No document control system for technical data",
                "Single-person dependency for quality or compliance functions",
                "Paper-based work orders or quality records"
            ],
            "cost_implications": {
                "mro_system": "MRO system implementation: $500K-$2M+",
                "qms_implementation": "AS9100/AS9110 QMS implementation: $200K-$600K",
                "cmmc_certification": "CMMC Level 2 readiness and certification: $200K-$500K",
                "itar_compliance": "ITAR compliance program (TCP, controls): $100K-$300K",
                "faa_remediation": "FAA finding remediation: $50K-$500K depending on scope",
                "traceability_remediation": "Traceability system remediation: $200K-$800K",
                "nadcap_certification": "Nadcap certification (per special process): $50K-$150K"
            },
            "integration_considerations": [
                "FAA certificates are facility-specific - ownership change requires notification",
                "EASA approvals may require re-application with new ownership",
                "AS9100/AS9110 certificates need re-audit for scope or ownership changes",
                "Customer approvals (Boeing, Airbus, airlines) may require re-qualification",
                "Defense contracts may require novation for ownership transfer",
                "ITAR licenses are entity-specific - new licenses needed post-transaction",
                "OEM authorizations (P&W, GE, etc.) may have change of control provisions",
                "Technical data rights and licenses need careful review",
                "Technician certifications and authorizations are not transferable"
            ],
            "what_good_looks_like": [
                "FAA Part 145 certificate in good standing with clean inspection history",
                "Current AS9100D/AS9110C certification with no major findings",
                "Integrated MRO system with full traceability",
                "Electronic QMS with document control",
                "Clear separation of defense and commercial work if ITAR applies",
                "CMMC assessment completed or scheduled (if defense)",
                "Documented TCP and ITAR training program (if applicable)",
                "Nadcap certifications current for special processes",
                "Customer scorecards showing good performance",
                "Dedicated quality and compliance function"
            ]
        }
    },

    # =========================================================================
    # DEFENSE CONTRACTORS
    # =========================================================================
    "defense_contractor": {
        "display_name": "Defense Contractor",
        "triggers": [
            "defense contractor", "DoD", "Department of Defense", "military",
            "prime contractor", "subcontractor", "DFARS", "NIST 800-171",
            "CMMC", "CUI", "controlled unclassified", "classified",
            "security clearance", "ITAR", "government contract"
        ],

        "relevance_questions": [
            "Do they have active DoD/defense contracts?",
            "Are they a prime or subcontractor?",
            "Do they handle CUI (Controlled Unclassified Information)?",
            "Do they handle classified information?",
            "What CMMC level is required by contracts?",
            "Do they have ITAR-controlled technical data or articles?"
        ],

        "expected_applications": {
            "cui_management": {
                "name": "CUI Management / Data Protection",
                "purpose": "CUI identification, marking, protection, access control",
                "common_vendors": ["Microsoft 365 GCC/GCC High", "Virtru", "Vera", "Custom implementations"],
                "questions": [
                    "How is CUI identified and marked?",
                    "What systems store/process CUI?",
                    "How is CUI access controlled and logged?",
                    "Is there a CUI inventory?"
                ],
                "compliance_drivers": ["DFARS 252.204-7012", "NIST 800-171", "CMMC"],
                "gap_risk": "critical"
            },
            "cmmc_grc": {
                "name": "CMMC/NIST 800-171 GRC Platform",
                "purpose": "Control assessment, POA&M tracking, evidence management",
                "common_vendors": ["Exostar CMMC Platform", "Summit 7", "Coalfire", "Archer", "ServiceNow GRC"],
                "questions": [
                    "What tool is used for NIST 800-171/CMMC compliance tracking?",
                    "Is there a current SSP (System Security Plan)?",
                    "How is POA&M status tracked?",
                    "How is evidence collected for assessments?"
                ],
                "compliance_drivers": ["CMMC", "NIST 800-171"],
                "gap_risk": "high"
            },
            "cleared_environment": {
                "name": "Classified / Cleared Systems",
                "purpose": "Classified information processing, SCIF systems",
                "common_vendors": ["Various - government-approved configurations"],
                "questions": [
                    "Do they process classified information?",
                    "Is there a SCIF or cleared facility?",
                    "What classified systems are in use?",
                    "How is the classified environment managed?"
                ],
                "compliance_drivers": ["NISPOM", "ICD 503", "DCSA"],
                "gap_risk": "critical_if_classified"
            },
            "contract_management": {
                "name": "Government Contract Management",
                "purpose": "Contract tracking, CLIN management, mods, deliverables",
                "common_vendors": ["Deltek Costpoint", "Unanet", "Procas", "Custom"],
                "questions": [
                    "What system tracks government contracts?",
                    "How are contract mods and CLINs managed?",
                    "How are deliverables tracked against contract requirements?"
                ],
                "compliance_drivers": ["FAR", "DFARS", "Contract-specific"],
                "gap_risk": "high"
            },
            "project_accounting": {
                "name": "Project/Contract Accounting",
                "purpose": "Cost accounting, timekeeping, indirect rates, billing",
                "common_vendors": ["Deltek Costpoint", "Unanet", "Jamis", "PROCAS"],
                "questions": [
                    "What system handles government contract accounting?",
                    "Is the system compliant with DCAA requirements?",
                    "How is timekeeping managed?",
                    "How are indirect rates calculated and applied?"
                ],
                "compliance_drivers": ["FAR Part 31", "CAS", "DCAA"],
                "gap_risk": "critical"
            },
            "itar_export_control": {
                "name": "ITAR / Export Control Management",
                "purpose": "Classification, licensing, technology transfer control",
                "common_vendors": ["OCR Services", "Amber Road (E2open)", "Manual processes"],
                "questions": [
                    "How are ITAR/EAR classifications determined?",
                    "What system tracks export licenses?",
                    "How is technology transfer controlled?",
                    "How is US persons verification performed?"
                ],
                "compliance_drivers": ["ITAR", "EAR", "DDTC"],
                "gap_risk": "critical_if_itar"
            },
            "supply_chain_compliance": {
                "name": "Supply Chain Compliance / SCRM",
                "purpose": "Supplier verification, flow-down, prohibited sources",
                "common_vendors": ["Exostar", "SAM.gov integration", "Custom"],
                "questions": [
                    "How is supplier compliance verified (SAM, debarment)?",
                    "How are flow-down requirements tracked?",
                    "How is Section 889 compliance managed?",
                    "Is there a SCRM program?"
                ],
                "compliance_drivers": ["DFARS", "Section 889", "CMMC flow-down"],
                "gap_risk": "high"
            },
            "incident_reporting": {
                "name": "Cyber Incident Reporting",
                "purpose": "DFARS 7012 incident reporting, forensics, DIBNET",
                "common_vendors": ["Manual process / DIBNET portal"],
                "questions": [
                    "Is there a documented cyber incident response plan?",
                    "Are they registered in DIBNET for incident reporting?",
                    "How is forensic evidence preserved?",
                    "What's the process for 72-hour reporting?"
                ],
                "compliance_drivers": ["DFARS 252.204-7012"],
                "gap_risk": "critical"
            }
        },

        "management_questions": [
            "How is the CUI boundary defined (system vs. enclave)?",
            "Are commercial and government IT environments segregated?",
            "Who owns CMMC compliance - IT, security, contracts?",
            "What's the timeline and status for CMMC certification?",
            "How are subcontractors assessed for compliance?",
            "How is security clearance status tracked for personnel?"
        ],

        "compliance_drivers": ["DFARS 252.204-7012", "NIST 800-171", "CMMC", "ITAR", "FAR/DFARS", "NISPOM (if classified)"],

        "diligence_considerations": {
            "key_questions": [
                "What is the current NIST 800-171 compliance status (self-assessment score)?",
                "Is there a System Security Plan (SSP) and Plan of Action & Milestones (POA&M)?",
                "What CMMC level is required by current/future contracts?",
                "What is the timeline for CMMC certification requirements?",
                "Do they handle CUI - what types and in what systems?",
                "Do they have classified work or facility clearance?",
                "What is the ITAR scope - defense articles, technical data?",
                "Have there been any DCSA or DCMA compliance findings?",
                "How is the CUI boundary defined and controlled?",
                "What is the cyber incident history and reporting status?"
            ],
            "red_flags": [
                "No SSP or POA&M documented",
                "Self-assessment score significantly below 110 (full compliance)",
                "CMMC certification required but C3PAO not engaged",
                "CUI in systems not meeting NIST 800-171 requirements",
                "No defined CUI boundary or inventory",
                "ITAR technical data without Technology Control Plan",
                "Non-US persons with access to CUI or ITAR data",
                "Commercial cloud (non-GCC/GCC High) used for CUI",
                "No cyber incident response plan",
                "History of reportable cyber incidents",
                "DCSA findings or vulnerabilities open",
                "Subcontractors not assessed for flow-down compliance",
                "Classified work but FSO position vacant or untrained",
                "No dedicated compliance function for government contracts"
            ],
            "cost_implications": {
                "cmmc_level_2": "CMMC Level 2 certification readiness: $200K-$500K",
                "cmmc_level_3": "CMMC Level 3 certification readiness: $500K-$2M+",
                "cui_enclave": "CUI enclave implementation: $300K-$1M",
                "gcc_high_migration": "M365 GCC High migration: $100K-$400K + licensing delta",
                "ssp_poam_development": "SSP and POA&M development: $75K-$200K",
                "itar_compliance": "ITAR compliance program: $100K-$300K",
                "security_controls": "Security control implementation (MFA, SIEM, etc.): $150K-$500K",
                "incident_response": "Incident response program: $50K-$150K",
                "classified_facility": "Classified facility (SCIF) buildout: $500K-$2M+"
            },
            "integration_considerations": [
                "Government contracts may require novation - approval takes 6-12 months",
                "CMMC certification timeline may create deal risk if deadlines approach",
                "Facility clearances (FCL) require DCSA approval for ownership changes",
                "Foreign ownership (FOCI) mitigation may be required",
                "Key personnel with clearances are critical to retain",
                "CUI boundary may need to be re-scoped post-integration",
                "ITAR licenses and agreements are entity-specific",
                "Subcontractor flow-down requirements continue to new owner",
                "Cyber incident reporting obligations transfer to acquirer"
            ],
            "what_good_looks_like": [
                "Current SSP with NIST 800-171 self-assessment score >100",
                "POA&M with realistic remediation timeline",
                "CMMC C3PAO engaged or assessment scheduled",
                "Defined CUI boundary with documented data flows",
                "GCC or GCC High environment for CUI processing",
                "Established cyber incident response plan with DIBNET registration",
                "ITAR compliance program with TCP and training",
                "Dedicated compliance function (FSO if classified)",
                "Subcontractor compliance tracked and verified",
                "Clean DCSA/DCMA audit history"
            ]
        }
    },

    # =========================================================================
    # LIFE SCIENCES / PHARMA
    # =========================================================================
    "life_sciences": {
        "display_name": "Life Sciences / Pharmaceutical",
        "triggers": [
            "pharmaceutical", "pharma", "biotech", "life sciences",
            "drug", "clinical trial", "FDA", "GxP", "GMP", "GLP", "GCP",
            "21 CFR Part 11", "validation", "LIMS", "laboratory"
        ],

        "relevance_questions": [
            "Do they manufacture or develop drugs/biologics?",
            "Are they subject to FDA GxP regulations?",
            "Do they conduct clinical trials?",
            "Do they have laboratory operations?",
            "What stage are they (R&D, clinical, commercial)?"
        ],

        "expected_applications": {
            "lims": {
                "name": "Laboratory Information Management System (LIMS)",
                "purpose": "Sample management, test execution, results, COAs",
                "common_vendors": ["LabWare", "Thermo SampleManager", "LabVantage", "Benchling"],
                "questions": [
                    "What LIMS is used?",
                    "Is it validated per 21 CFR Part 11?",
                    "How does it integrate with instruments?",
                    "How are electronic signatures implemented?"
                ],
                "compliance_drivers": ["21 CFR Part 11", "GLP", "GMP"],
                "gap_risk": "critical"
            },
            "qms_gxp": {
                "name": "GxP Quality Management System",
                "purpose": "Document control, deviations, CAPA, change control",
                "common_vendors": ["Veeva Vault", "MasterControl", "TrackWise", "Dot Compliance"],
                "questions": [
                    "What QMS is used for GxP compliance?",
                    "How are deviations and CAPAs managed?",
                    "Is there electronic signature capability?",
                    "How is change control managed?"
                ],
                "compliance_drivers": ["21 CFR Part 11", "GMP", "GLP"],
                "gap_risk": "critical"
            },
            "clinical_trial": {
                "name": "Clinical Trial Management System (CTMS)",
                "purpose": "Study management, site management, enrollment tracking",
                "common_vendors": ["Veeva Vault CTMS", "Medidata Rave", "Oracle Siebel CTMS", "Bioclinica"],
                "questions": [
                    "What system manages clinical trials?",
                    "How is site/investigator management handled?",
                    "How does it integrate with EDC?"
                ],
                "compliance_drivers": ["GCP", "21 CFR Part 11"],
                "gap_risk": "critical_if_clinical"
            },
            "edc": {
                "name": "Electronic Data Capture (EDC)",
                "purpose": "Clinical trial data collection, eCRF",
                "common_vendors": ["Medidata Rave", "Veeva Vault EDC", "Oracle InForm", "Castor"],
                "questions": [
                    "What EDC system is used?",
                    "Is it validated?",
                    "How is data integrated with CTMS and safety?"
                ],
                "compliance_drivers": ["GCP", "21 CFR Part 11"],
                "gap_risk": "critical_if_clinical"
            },
            "pharmacovigilance": {
                "name": "Pharmacovigilance / Safety",
                "purpose": "Adverse event tracking, signal detection, regulatory reporting",
                "common_vendors": ["Oracle Argus", "Veeva Vault Safety", "ArisGlobal"],
                "questions": [
                    "What system manages adverse events?",
                    "How is regulatory safety reporting handled?",
                    "Is there signal detection capability?"
                ],
                "compliance_drivers": ["FDA", "EMA", "GVP"],
                "gap_risk": "critical_if_commercial"
            },
            "regulatory_submissions": {
                "name": "Regulatory Information Management",
                "purpose": "Submission tracking, dossier management, eCTD",
                "common_vendors": ["Veeva Vault RIM", "IQVIA RIM", "Lorenz"],
                "questions": [
                    "What system manages regulatory submissions?",
                    "How is eCTD publishing handled?",
                    "How are commitments tracked?"
                ],
                "compliance_drivers": ["FDA", "EMA", "ICH"],
                "gap_risk": "high"
            },
            "manufacturing_batch": {
                "name": "Batch Manufacturing / MES",
                "purpose": "Batch records, electronic batch records, process control",
                "common_vendors": ["Emerson Syncade", "Rockwell PharmaSuite", "Werum PAS-X", "SAP MES"],
                "questions": [
                    "How are batch records managed (paper vs. electronic)?",
                    "Is there a validated MES?",
                    "How is batch release handled?"
                ],
                "compliance_drivers": ["GMP", "21 CFR Part 11"],
                "gap_risk": "critical_if_manufacturing"
            },
            "computer_system_validation": {
                "name": "CSV / Validation Management",
                "purpose": "System validation lifecycle, IQ/OQ/PQ, periodic review",
                "common_vendors": ["Kneat", "ValGenesis", "MasterControl", "Manual/SharePoint"],
                "questions": [
                    "How is computer system validation managed?",
                    "Is there a validation master plan?",
                    "How are periodic reviews conducted?",
                    "What's the validated system inventory?"
                ],
                "compliance_drivers": ["21 CFR Part 11", "GAMP 5", "EU Annex 11"],
                "gap_risk": "critical"
            }
        },

        "management_questions": [
            "What's the validated system inventory?",
            "How is CSV managed across the system portfolio?",
            "How is data integrity ensured (ALCOA+)?",
            "What's the approach to electronic signatures?",
            "How are system interfaces validated?",
            "Is there a computerized system validation (CSV) team?"
        ],

        "compliance_drivers": ["21 CFR Part 11", "GMP", "GLP", "GCP", "EU Annex 11", "GAMP 5", "Data integrity guidance"],

        "diligence_considerations": {
            "key_questions": [
                "What is the FDA/EMA inspection history - any 483s or warning letters?",
                "Is there a validated system inventory and what is CSV status?",
                "What stage is the product portfolio (R&D, clinical, commercial)?",
                "Are there any open FDA observations or commitments?",
                "What is the data integrity program status?",
                "How are electronic records and signatures managed (Part 11)?",
                "What clinical trial systems are in use and what is validation status?",
                "Are there any pending regulatory submissions?"
            ],
            "red_flags": [
                "FDA warning letters or consent decrees",
                "Multiple 483 observations in recent inspections",
                "Data integrity findings from regulators",
                "No validated system inventory",
                "Critical GxP systems not validated",
                "Paper-based batch records in commercial manufacturing",
                "No formal CSV program or dedicated resources",
                "LIMS or QMS not Part 11 compliant",
                "Clinical systems with data integrity gaps",
                "No audit trail on GxP systems",
                "Inadequate backup/recovery for GxP data"
            ],
            "cost_implications": {
                "csv_program": "CSV program establishment: $300K-$800K",
                "lims_implementation": "LIMS implementation (validated): $500K-$2M",
                "qms_implementation": "GxP QMS implementation: $400K-$1.5M",
                "part_11_remediation": "Part 11 compliance remediation: $200K-$800K",
                "data_integrity": "Data integrity remediation program: $300K-$1M",
                "ebr_implementation": "Electronic batch records: $1M-$5M",
                "warning_letter": "Warning letter remediation: $2M-$20M+",
                "clinical_systems": "Clinical trial system implementation: $500K-$3M"
            },
            "integration_considerations": [
                "FDA establishment registration may need updating post-transaction",
                "Product licenses (NDAs, ANDAs, BLAs) require ownership transfer notification",
                "Clinical trial transfers require regulatory notification",
                "Validated state must be maintained through transition",
                "CSV documentation must be preserved and accessible",
                "Change control is critical during integration",
                "Contract manufacturing agreements may have change of control provisions",
                "Product supply continuity during transition is critical"
            ],
            "what_good_looks_like": [
                "Clean FDA inspection history (no 483s or minor only)",
                "Complete validated system inventory",
                "Mature CSV program with dedicated resources",
                "Part 11 compliant systems with audit trails",
                "Electronic batch records in manufacturing",
                "Documented data integrity program",
                "Modern validated LIMS and QMS",
                "Validation documentation complete and accessible",
                "Periodic review program for validated systems"
            ]
        }
    },

    # =========================================================================
    # RETAIL
    # =========================================================================
    "retail": {
        "display_name": "Retail",
        "triggers": [
            "retail", "store", "e-commerce", "ecommerce", "POS", "point of sale",
            "omnichannel", "brick and mortar", "fulfillment", "merchandise",
            "PCI", "cardholder", "payment"
        ],

        "relevance_questions": [
            "Do they have retail stores (brick and mortar)?",
            "Do they have e-commerce operations?",
            "Do they process card payments (PCI scope)?",
            "How many store locations?",
            "What channels (stores, online, marketplace, wholesale)?"
        ],

        "expected_applications": {
            "pos": {
                "name": "Point of Sale (POS)",
                "purpose": "In-store transactions, checkout, payments",
                "common_vendors": ["Oracle Retail", "NCR", "Toshiba", "Square", "Shopify POS", "Lightspeed"],
                "questions": [
                    "What POS system is used?",
                    "How many terminals across locations?",
                    "How does POS integrate with inventory and ERP?",
                    "What payment processors are used?"
                ],
                "compliance_drivers": ["PCI-DSS"],
                "gap_risk": "critical_if_stores"
            },
            "ecommerce_platform": {
                "name": "E-commerce Platform",
                "purpose": "Online storefront, cart, checkout, product catalog",
                "common_vendors": ["Shopify", "Salesforce Commerce Cloud", "Adobe Commerce (Magento)", "BigCommerce", "SAP Commerce"],
                "questions": [
                    "What e-commerce platform is used?",
                    "Is it SaaS or self-hosted?",
                    "How customized is the implementation?",
                    "How does it integrate with inventory and fulfillment?"
                ],
                "compliance_drivers": ["PCI-DSS", "CCPA/GDPR"],
                "gap_risk": "critical_if_ecommerce"
            },
            "order_management": {
                "name": "Order Management System (OMS)",
                "purpose": "Order orchestration, fulfillment routing, inventory visibility",
                "common_vendors": ["Manhattan", "IBM Sterling", "Fluent Commerce", "Kibo"],
                "questions": [
                    "What manages order orchestration across channels?",
                    "How is inventory allocated across channels?",
                    "How is BOPIS/ship-from-store managed?"
                ],
                "integration_points": ["E-commerce", "POS", "WMS", "ERP"],
                "gap_risk": "high_if_omnichannel"
            },
            "merchandising": {
                "name": "Merchandising / Assortment Planning",
                "purpose": "Assortment planning, allocation, pricing, promotions",
                "common_vendors": ["Oracle Retail", "Blue Yonder", "Mi9 Retail", "SAP Retail"],
                "questions": [
                    "What system handles merchandising and planning?",
                    "How is pricing managed?",
                    "How are promotions managed across channels?"
                ],
                "gap_risk": "medium"
            },
            "loyalty_crm": {
                "name": "Loyalty / CRM",
                "purpose": "Customer data, loyalty program, personalization",
                "common_vendors": ["Salesforce", "Oracle CrowdTwist", "Punchh", "Yotpo"],
                "questions": [
                    "Is there a loyalty program and what system manages it?",
                    "How is customer data unified across channels?",
                    "How is personalization delivered?"
                ],
                "compliance_drivers": ["CCPA", "GDPR"],
                "gap_risk": "medium"
            },
            "inventory_management": {
                "name": "Inventory Management",
                "purpose": "Inventory tracking, replenishment, store inventory",
                "common_vendors": ["Oracle", "SAP", "Manhattan", "Blue Yonder", "Often in ERP"],
                "questions": [
                    "What system manages inventory across locations?",
                    "Is inventory real-time or batch updated?",
                    "How is store inventory accuracy managed?"
                ],
                "integration_points": ["ERP", "WMS", "POS", "E-commerce"],
                "gap_risk": "high"
            }
        },

        "management_questions": [
            "How is inventory synchronized across channels?",
            "What's the PCI scope and how is it managed?",
            "How is the customer unified across touchpoints?",
            "What's the technology approach for stores (thin client, local)?",
            "How are promotions coordinated across channels?"
        ],

        "compliance_drivers": ["PCI-DSS", "CCPA", "GDPR", "State privacy laws"],

        "diligence_considerations": {
            "key_questions": [
                "What is the PCI compliance status and scope?",
                "When was the last PCI assessment (SAQ or ROC)?",
                "How is cardholder data segmented and protected?",
                "What is the e-commerce platform age and customization level?",
                "How many stores and what is the technology per store?",
                "What is the inventory accuracy across channels?",
                "How is customer data privacy managed (CCPA, state laws)?"
            ],
            "red_flags": [
                "PCI compliance gaps or failed assessments",
                "Cardholder data breach history",
                "Highly customized legacy e-commerce platform",
                "POS systems on unsupported OS or software versions",
                "No omnichannel inventory visibility",
                "Fragmented customer data across channels",
                "No documented privacy program for CCPA/GDPR",
                "Manual inventory reconciliation processes",
                "Store technology varies significantly across locations",
                "E-commerce platform without PCI-compliant hosting"
            ],
            "cost_implications": {
                "ecommerce_replatform": "E-commerce platform replacement: $1M-$10M",
                "pos_replacement": "POS system replacement: $5K-$20K per store",
                "pci_remediation": "PCI remediation program: $200K-$800K",
                "oms_implementation": "Order management system: $500K-$3M",
                "inventory_system": "Inventory management system: $300K-$2M",
                "privacy_program": "Privacy compliance program: $100K-$400K",
                "data_breach_cost": "Average retail data breach: $3M+"
            },
            "integration_considerations": [
                "Store technology refresh may be needed for standardization",
                "E-commerce platform may have re-platforming risk",
                "PCI scope needs to be clearly defined during transition",
                "Customer data migration has privacy implications",
                "Loyalty program data is often a key asset",
                "Vendor contracts (POS, e-commerce) may have change of control clauses",
                "Franchise vs corporate store technology may differ"
            ],
            "what_good_looks_like": [
                "Current PCI compliance (ROC or SAQ as appropriate)",
                "Modern cloud-based e-commerce platform",
                "Standardized POS across all locations",
                "Real-time inventory visibility across channels",
                "Unified customer data platform",
                "Documented privacy program with CCPA/GDPR compliance",
                "Omnichannel fulfillment capability (BOPIS, ship-from-store)"
            ]
        }
    },

    # =========================================================================
    # LOGISTICS / DISTRIBUTION
    # =========================================================================
    "logistics": {
        "display_name": "Logistics / Distribution",
        "triggers": [
            "logistics", "distribution", "warehouse", "3PL", "freight",
            "transportation", "trucking", "shipping", "supply chain",
            "WMS", "TMS", "fleet", "last mile"
        ],

        "relevance_questions": [
            "Do they operate warehouses/distribution centers?",
            "Do they manage transportation/freight?",
            "Are they a 3PL or operate for their own products?",
            "Do they have a fleet of vehicles?",
            "What modes of transport (truck, air, ocean, rail)?"
        ],

        "expected_applications": {
            "wms": {
                "name": "Warehouse Management System (WMS)",
                "purpose": "Receiving, putaway, picking, packing, shipping",
                "common_vendors": ["Manhattan", "Blue Yonder", "SAP EWM", "Oracle WMS", "Körber", "Deposco"],
                "questions": [
                    "What WMS is used?",
                    "How many DCs/warehouses?",
                    "What automation is integrated (conveyors, AS/RS, robots)?",
                    "How does WMS integrate with ERP and TMS?"
                ],
                "integration_points": ["ERP", "TMS", "Automation/MHE", "Carrier systems"],
                "gap_risk": "critical"
            },
            "tms": {
                "name": "Transportation Management System (TMS)",
                "purpose": "Routing, carrier selection, freight audit, tracking",
                "common_vendors": ["Oracle TMS", "Blue Yonder", "MercuryGate", "Kuebix", "project44"],
                "questions": [
                    "What TMS is used?",
                    "How is carrier selection and rating handled?",
                    "Is there freight audit and payment?",
                    "How is shipment visibility provided?"
                ],
                "integration_points": ["WMS", "ERP", "Carrier APIs"],
                "gap_risk": "high"
            },
            "fleet_management": {
                "name": "Fleet Management / Telematics",
                "purpose": "Vehicle tracking, driver management, maintenance, ELD",
                "common_vendors": ["Samsara", "Geotab", "Omnitracs", "Trimble", "KeepTruckin"],
                "questions": [
                    "What fleet management/telematics system is used?",
                    "How is ELD compliance managed?",
                    "How is fleet maintenance tracked?",
                    "Is there driver safety monitoring?"
                ],
                "compliance_drivers": ["FMCSA ELD mandate", "DOT Hours of Service"],
                "gap_risk": "critical_if_fleet"
            },
            "yard_management": {
                "name": "Yard Management System (YMS)",
                "purpose": "Trailer tracking, dock scheduling, yard visibility",
                "common_vendors": ["C3 Solutions", "Descartes", "4SIGHT", "Often in WMS"],
                "questions": [
                    "How is yard activity managed?",
                    "Is there dock door scheduling?",
                    "How is trailer inventory tracked?"
                ],
                "gap_risk": "medium"
            },
            "route_optimization": {
                "name": "Route Optimization / Last Mile",
                "purpose": "Delivery routing, driver dispatch, customer ETAs",
                "common_vendors": ["Descartes", "Bringg", "Onfleet", "Route4Me", "OptimoRoute"],
                "questions": [
                    "How is delivery routing optimized?",
                    "Is there real-time dispatch capability?",
                    "How are customer delivery windows managed?"
                ],
                "gap_risk": "high_if_delivery"
            },
            "customs_trade": {
                "name": "Customs / Trade Compliance",
                "purpose": "Import/export compliance, customs brokerage, tariff classification",
                "common_vendors": ["Descartes", "Amber Road (E2open)", "Integration Point"],
                "questions": [
                    "How is customs compliance managed?",
                    "Is there a customs broker relationship?",
                    "How are tariff classifications determined?"
                ],
                "compliance_drivers": ["CBP", "Trade regulations"],
                "gap_risk": "critical_if_international"
            }
        },

        "management_questions": [
            "How do WMS and TMS integrate?",
            "How is carrier performance tracked and managed?",
            "What's the visibility strategy (internal and customer-facing)?",
            "How is warehouse automation managed and integrated?",
            "What's the approach to customer integrations (EDI, API)?"
        ],

        "compliance_drivers": ["DOT/FMCSA", "Customs/CBP", "CTPAT", "FDA (if food/pharma)", "Hazmat"],

        "diligence_considerations": {
            "key_questions": [
                "What WMS is used and how old/customized is it?",
                "Is there ELD compliance for fleet operations?",
                "What is the CTPAT certification status (if applicable)?",
                "How is customs brokerage and trade compliance managed?",
                "What level of warehouse automation exists?",
                "What is the customer EDI/integration capability?",
                "How is carrier compliance and performance tracked?"
            ],
            "red_flags": [
                "WMS is legacy or highly customized",
                "No ELD compliance or using non-compliant devices",
                "DOT safety violations or poor CSA scores",
                "Manual customs filing processes",
                "Warehouse automation with obsolete controls",
                "No TMS - manual carrier selection and tracking",
                "Customer integrations via manual processes or email",
                "Fleet without telematics or driver safety monitoring",
                "No yard management - trailers lost in yards",
                "Temperature monitoring gaps for cold chain"
            ],
            "cost_implications": {
                "wms_replacement": "WMS replacement: $500K-$5M per DC",
                "tms_implementation": "TMS implementation: $300K-$1.5M",
                "fleet_telematics": "Fleet telematics rollout: $300-$500 per vehicle + system",
                "warehouse_automation": "Warehouse automation: $2M-$20M+ per facility",
                "eld_compliance": "ELD compliance program: $200-$500 per driver",
                "customs_system": "Trade compliance system: $200K-$800K",
                "customer_integration": "EDI/API integration platform: $200K-$600K"
            },
            "integration_considerations": [
                "WMS conversions are high-risk operational projects",
                "Customer EDI connections need to be maintained through transition",
                "Carrier contracts and rates may need renegotiation",
                "DOT authority transfers may be required for asset-based carriers",
                "CTPAT certification may need to be re-validated",
                "Customs bonds and broker relationships",
                "3PL customer contracts may have change of control provisions"
            ],
            "what_good_looks_like": [
                "Modern WMS with RF/mobile capability",
                "TMS with carrier connectivity and optimization",
                "Full ELD compliance with integrated fleet management",
                "CTPAT certified (if applicable)",
                "Customer integration via API/EDI platform",
                "Real-time shipment visibility",
                "Carrier compliance and performance tracking",
                "Automated customs filing capability"
            ]
        }
    },

    # =========================================================================
    # ENERGY / UTILITIES
    # =========================================================================
    "energy_utilities": {
        "display_name": "Energy / Utilities",
        "triggers": [
            "utility", "electric", "gas", "water", "energy",
            "power generation", "transmission", "distribution",
            "SCADA", "NERC CIP", "smart grid", "meter", "outage"
        ],

        "relevance_questions": [
            "What type of utility (electric, gas, water, multi)?",
            "Do they have generation assets?",
            "Do they operate transmission or distribution?",
            "Are they subject to NERC CIP?",
            "How many customers/meters?"
        ],

        "expected_applications": {
            "scada_ems": {
                "name": "SCADA / EMS / DMS",
                "purpose": "Grid monitoring, control, outage management",
                "common_vendors": ["GE", "Siemens", "ABB", "Schneider Electric", "OSI"],
                "questions": [
                    "What SCADA/EMS system monitors operations?",
                    "How is OT network segmented?",
                    "What's the NERC CIP compliance status?",
                    "How is remote access to OT managed?"
                ],
                "compliance_drivers": ["NERC CIP"],
                "security_considerations": ["Critical infrastructure", "OT/IT segmentation", "Supply chain"],
                "gap_risk": "critical"
            },
            "outage_management": {
                "name": "Outage Management System (OMS)",
                "purpose": "Outage detection, crew dispatch, restoration tracking",
                "common_vendors": ["Oracle", "GE", "Schneider", "ABB"],
                "questions": [
                    "What system manages outage response?",
                    "How is it integrated with SCADA and AMI?",
                    "How is crew dispatch managed?"
                ],
                "gap_risk": "high"
            },
            "ami_mdm": {
                "name": "AMI / Meter Data Management",
                "purpose": "Smart meter data collection, validation, estimation",
                "common_vendors": ["Itron", "Landis+Gyr", "Oracle MDM", "Siemens"],
                "questions": [
                    "What AMI/smart meter infrastructure is deployed?",
                    "What MDM system processes meter data?",
                    "How does meter data flow to billing?"
                ],
                "integration_points": ["CIS/Billing", "Analytics", "Customer portal"],
                "gap_risk": "high"
            },
            "cis_billing": {
                "name": "Customer Information System (CIS) / Billing",
                "purpose": "Customer accounts, billing, rates, payments",
                "common_vendors": ["Oracle CC&B", "SAP IS-U", "Hansen", "Cayenta"],
                "questions": [
                    "What CIS/billing system is used?",
                    "How complex is the rate structure?",
                    "How old is the system?"
                ],
                "gap_risk": "critical"
            },
            "asset_management": {
                "name": "Enterprise Asset Management",
                "purpose": "Asset registry, maintenance, work management",
                "common_vendors": ["IBM Maximo", "SAP EAM", "Oracle EAM", "Infor"],
                "questions": [
                    "What system manages utility assets?",
                    "How is predictive maintenance implemented?",
                    "How does it integrate with GIS?"
                ],
                "integration_points": ["GIS", "SCADA", "Work management"],
                "gap_risk": "high"
            },
            "gis": {
                "name": "Geographic Information System (GIS)",
                "purpose": "Network model, asset location, mapping",
                "common_vendors": ["Esri", "GE Smallworld", "Schneider ArcFM"],
                "questions": [
                    "What GIS system is used?",
                    "Is it the system of record for network model?",
                    "How current is the data?"
                ],
                "gap_risk": "high"
            }
        },

        "management_questions": [
            "How is NERC CIP compliance managed?",
            "What's the OT security program?",
            "How is the OT/IT boundary defined?",
            "What's the grid modernization roadmap?",
            "How is critical infrastructure protected?"
        ],

        "compliance_drivers": ["NERC CIP", "State PUC", "EPA", "FERC", "Pipeline safety (gas)"],

        "diligence_considerations": {
            "key_questions": [
                "What is the NERC CIP compliance status and audit history?",
                "Are there any open violations or mitigation plans?",
                "What is the OT/IT segmentation architecture?",
                "How old are SCADA and control systems?",
                "What is the AMI deployment status and roadmap?",
                "What is the CIS/billing system age and status?",
                "Are there any pending rate cases or PUC proceedings?"
            ],
            "red_flags": [
                "NERC CIP violations or open mitigation plans",
                "OT network not segmented from IT",
                "SCADA systems on unsupported platforms",
                "No OT security monitoring capability",
                "CIS/billing system on unsupported platform",
                "Manual meter reading with no AMI roadmap",
                "No documented OT asset inventory",
                "Critical infrastructure without redundancy",
                "Remote access to OT without proper controls",
                "Supply chain security gaps for OT components"
            ],
            "cost_implications": {
                "nerc_remediation": "NERC CIP compliance remediation: $2M-$10M",
                "ot_security": "OT security program: $1M-$5M",
                "scada_modernization": "SCADA/EMS modernization: $5M-$50M+",
                "ami_deployment": "AMI deployment: $200-$400 per meter + MDM",
                "cis_replacement": "CIS/billing replacement: $10M-$100M+",
                "gis_modernization": "GIS modernization: $2M-$10M",
                "grid_modernization": "Grid modernization program: $50M-$500M+"
            },
            "integration_considerations": [
                "NERC registration may need to be updated for ownership change",
                "State PUC approval typically required for utility M&A",
                "Critical infrastructure security clearances may be required",
                "OT systems require specialized integration expertise",
                "Customer migration has regulatory notification requirements",
                "Rate base and regulatory assets need careful valuation",
                "Union considerations for utility operations"
            ],
            "what_good_looks_like": [
                "Clean NERC CIP audit history",
                "Documented OT/IT segmentation with network diagrams",
                "OT security monitoring and incident response",
                "Modern SCADA/EMS with vendor support",
                "AMI deployment with MDM integration",
                "Supported CIS/billing platform",
                "OT asset inventory with lifecycle management",
                "Documented change management for OT systems"
            ]
        }
    },

    # =========================================================================
    # INSURANCE
    # =========================================================================
    "insurance": {
        "display_name": "Insurance",
        "triggers": [
            "insurance", "carrier", "underwriting", "claims", "policy",
            "premium", "actuarial", "reinsurance", "P&C", "life insurance",
            "annuity", "broker", "MGA", "TPA"
        ],

        "relevance_questions": [
            "What type of insurance (P&C, life, health, specialty)?",
            "Are they a carrier, MGA, broker, or TPA?",
            "What lines of business?",
            "What distribution channels (direct, agent, broker)?",
            "What states/jurisdictions are they licensed in?"
        ],

        "expected_applications": {
            "policy_admin": {
                "name": "Policy Administration System",
                "purpose": "Policy issuance, endorsements, renewals, billing",
                "common_vendors": ["Guidewire PolicyCenter", "Duck Creek", "Majesco", "Sapiens", "EIS"],
                "questions": [
                    "What policy admin system is used?",
                    "Is it modern or legacy?",
                    "How is it configured per line of business?",
                    "How are endorsements and renewals processed?"
                ],
                "gap_risk": "critical"
            },
            "claims": {
                "name": "Claims Management System",
                "purpose": "Claims intake, adjudication, payments, litigation",
                "common_vendors": ["Guidewire ClaimCenter", "Duck Creek Claims", "Snapsheet", "Mitchell"],
                "questions": [
                    "What claims system is used?",
                    "How is claims intake handled (FNOL)?",
                    "How is subrogation managed?",
                    "What's the level of automation/straight-through processing?"
                ],
                "gap_risk": "critical"
            },
            "underwriting": {
                "name": "Underwriting Workbench",
                "purpose": "Risk assessment, pricing, submissions management",
                "common_vendors": ["Guidewire", "Duck Creek", "Sequel", "Custom"],
                "questions": [
                    "What system supports underwriting?",
                    "How automated is the underwriting process?",
                    "How is pricing/rating handled?"
                ],
                "gap_risk": "high"
            },
            "rating_engine": {
                "name": "Rating Engine",
                "purpose": "Premium calculation, rating algorithms",
                "common_vendors": ["Guidewire", "Duck Creek", "Insurity", "Earnix", "Custom"],
                "questions": [
                    "What rating engine is used?",
                    "How are rates managed and updated?",
                    "Is it integrated with policy admin?"
                ],
                "gap_risk": "high"
            },
            "actuarial": {
                "name": "Actuarial / Reserving Systems",
                "purpose": "Loss reserving, pricing analysis, capital modeling",
                "common_vendors": ["Milliman Arius", "Willis Towers Watson ResQ", "SAS", "Excel-heavy"],
                "questions": [
                    "What actuarial systems are used?",
                    "How is loss reserving performed?",
                    "What data flows from claims to actuarial?"
                ],
                "gap_risk": "high"
            },
            "agency_portal": {
                "name": "Agent/Broker Portal",
                "purpose": "Quote submission, policy service, commission tracking",
                "common_vendors": ["Guidewire ProducerEngage", "Duck Creek", "Custom portals"],
                "questions": [
                    "How do agents/brokers interact with systems?",
                    "What self-service capabilities exist?",
                    "How are commissions tracked?"
                ],
                "gap_risk": "medium"
            },
            "reinsurance": {
                "name": "Reinsurance Management",
                "purpose": "Treaty/facultative tracking, cessions, recoveries",
                "common_vendors": ["SOLIS", "Sequel", "Custom"],
                "questions": [
                    "How is reinsurance managed?",
                    "What system tracks cessions and recoveries?",
                    "How are treaty terms maintained?"
                ],
                "gap_risk": "high_if_reinsurance"
            }
        },

        "management_questions": [
            "How integrated is the policy-billing-claims ecosystem?",
            "What's the data architecture for analytics and reporting?",
            "How is state filing and compliance managed?",
            "What's the technology modernization roadmap?",
            "How is document management handled?"
        ],

        "compliance_drivers": ["State DOI", "NAIC", "SOX (if public)", "State data privacy"],

        "diligence_considerations": {
            "key_questions": [
                "What is the policy admin system age and modernization status?",
                "Are there any open state DOI market conduct or financial exam findings?",
                "What is the claims system automation level?",
                "How are rates filed and managed across states?",
                "What is the loss ratio and combined ratio trend?",
                "Is there any runoff business or discontinued lines?",
                "What is the reinsurance program and system support?"
            ],
            "red_flags": [
                "Policy admin system is legacy mainframe with no modernization plan",
                "Open DOI findings or consent orders",
                "High claims leakage due to manual processes",
                "Rate filing managed manually or in spreadsheets",
                "No modern rating engine - rates hard-coded",
                "Claims system without fraud detection capability",
                "Actuarial processes heavily spreadsheet-dependent",
                "No digital agent/broker portal",
                "Multiple policy admin systems across lines",
                "Data quality issues affecting reporting and analytics"
            ],
            "cost_implications": {
                "policy_admin": "Policy admin system replacement: $10M-$100M+",
                "claims_system": "Claims system replacement: $5M-$50M",
                "rating_engine": "Rating engine implementation: $1M-$5M",
                "digital_platform": "Digital/agent portal: $2M-$10M",
                "data_warehouse": "Data warehouse/analytics platform: $2M-$10M",
                "core_integration": "Core system integration work: $3M-$15M",
                "legacy_modernization": "Legacy modernization program: $20M-$100M+"
            },
            "integration_considerations": [
                "State DOI approval required for insurance M&A",
                "Form and rate filings may need re-filing under new entity",
                "Producer appointments may need to be re-processed",
                "Reinsurance treaties may have change of control provisions",
                "Policy admin conversions are multi-year, high-risk projects",
                "Run-off business creates long-tail obligations",
                "AM Best and rating agency considerations"
            ],
            "what_good_looks_like": [
                "Modern policy admin platform (Guidewire, Duck Creek)",
                "Integrated policy-billing-claims ecosystem",
                "Automated rating with modern rating engine",
                "Clean DOI exam history",
                "Digital capabilities for agents and customers",
                "Data warehouse with analytics capability",
                "Automated regulatory reporting",
                "Fraud detection and SIU integration"
            ]
        }
    },

    # =========================================================================
    # CONSTRUCTION / ENGINEERING
    # =========================================================================
    "construction": {
        "display_name": "Construction / Engineering",
        "triggers": [
            "construction", "contractor", "builder", "engineering",
            "architect", "project management", "estimating", "BIM",
            "jobsite", "subcontractor", "AEC"
        ],

        "relevance_questions": [
            "What type of construction (commercial, residential, civil, industrial)?",
            "Are they a GC, specialty contractor, or owner?",
            "Do they self-perform work or subcontract?",
            "What's the typical project size and duration?",
            "Do they have equipment fleet?"
        ],

        "expected_applications": {
            "project_management": {
                "name": "Construction Project Management",
                "purpose": "Project tracking, scheduling, collaboration, documentation",
                "common_vendors": ["Procore", "Autodesk Construction Cloud", "Oracle Primavera P6", "CMiC", "Sage 300 CRE"],
                "questions": [
                    "What project management platform is used?",
                    "How is scheduling managed (CPM)?",
                    "How do field and office collaborate?",
                    "How is project documentation managed?"
                ],
                "gap_risk": "critical"
            },
            "estimating": {
                "name": "Estimating / Takeoff",
                "purpose": "Cost estimation, quantity takeoff, bid preparation",
                "common_vendors": ["Sage Estimating", "ProEst", "PlanSwift", "Bluebeam", "HCSS HeavyBid"],
                "questions": [
                    "What estimating system is used?",
                    "How is takeoff performed (manual vs. digital)?",
                    "How do estimates flow to project accounting?"
                ],
                "gap_risk": "high"
            },
            "project_accounting": {
                "name": "Construction Accounting / Job Costing",
                "purpose": "Job costing, WIP, billing (AIA), certified payroll",
                "common_vendors": ["Sage 300 CRE", "Vista by Viewpoint", "CMiC", "Foundation", "Procore Financials"],
                "questions": [
                    "What construction accounting system is used?",
                    "How is job costing managed?",
                    "How is AIA billing handled?",
                    "How is WIP calculated?"
                ],
                "compliance_drivers": ["Certified payroll (if prevailing wage)", "Bonding"],
                "gap_risk": "critical"
            },
            "bim": {
                "name": "BIM / Design Coordination",
                "purpose": "3D modeling, clash detection, design coordination",
                "common_vendors": ["Autodesk Revit", "Navisworks", "Tekla", "Trimble"],
                "questions": [
                    "Is BIM used on projects?",
                    "What level of BIM maturity?",
                    "How is model coordination managed?"
                ],
                "gap_risk": "context_dependent"
            },
            "field_management": {
                "name": "Field Management / Daily Reports",
                "purpose": "Daily logs, time tracking, safety, quality",
                "common_vendors": ["Procore", "PlanGrid", "Fieldwire", "Raken"],
                "questions": [
                    "How is field data captured?",
                    "How is time tracked in the field?",
                    "How are daily reports managed?"
                ],
                "gap_risk": "medium"
            },
            "ehs_construction": {
                "name": "Construction Safety / EHS",
                "purpose": "Safety tracking, incidents, training, inspections",
                "common_vendors": ["Procore Safety", "SafetyCulture", "Intelex", "iAuditor"],
                "questions": [
                    "How is jobsite safety managed?",
                    "How are incidents tracked?",
                    "How is safety training documented?"
                ],
                "compliance_drivers": ["OSHA"],
                "gap_risk": "high"
            },
            "equipment_management": {
                "name": "Equipment / Fleet Management",
                "purpose": "Equipment tracking, maintenance, utilization",
                "common_vendors": ["HCSS Equipment360", "B2W", "Tenna", "Built-in ERP modules"],
                "questions": [
                    "How is equipment tracked and managed?",
                    "How is equipment costed to jobs?",
                    "How is maintenance scheduled?"
                ],
                "gap_risk": "high_if_equipment"
            }
        },

        "management_questions": [
            "How do estimating, PM, and accounting systems integrate?",
            "How is subcontractor management handled?",
            "What's the approach to project document management?",
            "How is change order management handled?",
            "How are closeout and warranty tracked?"
        ],

        "compliance_drivers": ["OSHA", "Prevailing wage/Davis-Bacon", "Bonding requirements", "Licensing"],

        "diligence_considerations": {
            "key_questions": [
                "What project management and accounting systems are used?",
                "Is there integration between estimating, PM, and accounting?",
                "What is the backlog and WIP accuracy?",
                "How is job costing managed and reported?",
                "What is the bonding capacity and relationship?",
                "Are there any open OSHA violations?",
                "How is prevailing wage / certified payroll managed (if applicable)?",
                "What is the equipment fleet status and management?"
            ],
            "red_flags": [
                "Project management via spreadsheets",
                "No integration between estimating and accounting",
                "WIP schedule accuracy issues",
                "Job cost reporting delayed or unreliable",
                "Open OSHA citations or high EMR",
                "Bonding capacity constrained or surety concerns",
                "Certified payroll managed manually",
                "No project document management system",
                "Equipment fleet with deferred maintenance",
                "Estimating knowledge concentrated in few individuals",
                "High subcontractor claims or disputes"
            ],
            "cost_implications": {
                "construction_erp": "Construction ERP implementation: $500K-$3M",
                "project_management": "Project management platform (Procore): $200K-$800K",
                "estimating_system": "Estimating system: $100K-$500K",
                "document_management": "Project document management: $100K-$400K",
                "equipment_system": "Equipment management system: $100K-$300K",
                "safety_program": "Safety program/system: $50K-$200K",
                "integration_work": "System integration work: $200K-$600K"
            },
            "integration_considerations": [
                "Contractor licenses may need transfer or re-application",
                "Bonding requires surety approval of new ownership",
                "Project-specific insurance may have assignment restrictions",
                "Owner contracts may have change of control provisions",
                "Subcontractor relationships are often relationship-based",
                "Estimating knowledge transfer is critical",
                "WIP and backlog valuation requires careful analysis",
                "Lien rights and retainage positions"
            ],
            "what_good_looks_like": [
                "Integrated construction ERP (Sage, Vista, CMiC)",
                "Modern project management platform (Procore, ACC)",
                "Connected estimating-to-accounting workflow",
                "Real-time job cost visibility",
                "Strong safety record with low EMR",
                "Adequate bonding capacity with good surety relationship",
                "Automated certified payroll (if applicable)",
                "Project document management with mobile access",
                "Equipment fleet management with maintenance tracking"
            ]
        }
    },

    # =========================================================================
    # FOOD & BEVERAGE MANUFACTURING
    # =========================================================================
    "food_beverage": {
        "display_name": "Food & Beverage Manufacturing",
        "triggers": [
            "food", "beverage", "CPG", "consumer packaged goods",
            "food manufacturing", "food processing", "brewery", "dairy",
            "meat", "bakery", "FSMA", "HACCP", "SQF", "BRC"
        ],

        "relevance_questions": [
            "What type of food/beverage products?",
            "Are they subject to FDA FSMA?",
            "What food safety certifications (SQF, BRC, FSSC 22000)?",
            "Do they manufacture or just distribute?",
            "Do they have cold chain requirements?"
        ],

        "expected_applications": {
            "erp_food": {
                "name": "Food/Beverage ERP",
                "purpose": "Recipe/formula management, lot tracking, production",
                "common_vendors": ["SAP", "Microsoft Dynamics", "Infor M3/CloudSuite", "DEACOM", "Aptean"],
                "questions": [
                    "What ERP is used?",
                    "Is it a food/beverage-specific solution?",
                    "How are recipes/formulas managed?",
                    "How is lot traceability maintained?"
                ],
                "compliance_drivers": ["FSMA", "Allergen labeling"],
                "gap_risk": "critical"
            },
            "food_safety_qms": {
                "name": "Food Safety / HACCP Management",
                "purpose": "HACCP plans, CCPs, food safety records, audits",
                "common_vendors": ["SafetyChain", "Icicle", "FoodLogiQ", "CMX (ComplianceMetrix)"],
                "questions": [
                    "How are HACCP plans managed?",
                    "How are CCPs monitored and documented?",
                    "How is food safety audit readiness maintained?",
                    "How are supplier food safety records managed?"
                ],
                "compliance_drivers": ["FSMA", "HACCP", "SQF/BRC/FSSC"],
                "gap_risk": "critical"
            },
            "traceability": {
                "name": "Lot Traceability / Recall Management",
                "purpose": "Forward/backward trace, mock recalls, recall execution",
                "common_vendors": ["Often in ERP", "FoodLogiQ", "RFXCEL", "TraceLink"],
                "questions": [
                    "How is lot traceability maintained (one-up, one-back)?",
                    "Can a mock recall be completed in required timeframe?",
                    "How is traceability data shared with customers?"
                ],
                "compliance_drivers": ["FSMA 204", "Customer requirements"],
                "gap_risk": "critical"
            },
            "batch_process_control": {
                "name": "Batch Processing / Recipe Management",
                "purpose": "Batch execution, recipe management, process control",
                "common_vendors": ["Rockwell", "Siemens", "Wonderware", "Often in MES"],
                "questions": [
                    "How is batch production controlled?",
                    "How are recipes versioned and deployed?",
                    "How is batch data captured?"
                ],
                "gap_risk": "high"
            },
            "labeling_compliance": {
                "name": "Labeling / Spec Management",
                "purpose": "Label generation, allergen management, nutrition facts",
                "common_vendors": ["Esko", "NiceLabel", "Loftware", "Genesis R&D"],
                "questions": [
                    "How are product labels managed?",
                    "How is allergen information controlled?",
                    "How are nutrition facts calculated?"
                ],
                "compliance_drivers": ["FDA labeling", "FALCPA"],
                "gap_risk": "high"
            },
            "supplier_management": {
                "name": "Supplier Quality / Compliance",
                "purpose": "Supplier approval, COAs, audits, specifications",
                "common_vendors": ["TraceGains", "FoodLogiQ", "Repositrak", "Often manual"],
                "questions": [
                    "How are suppliers qualified and approved?",
                    "How are COAs collected and validated?",
                    "How are supplier specifications managed?"
                ],
                "compliance_drivers": ["FSMA PCHF", "GFSI schemes"],
                "gap_risk": "high"
            }
        },

        "management_questions": [
            "How is end-to-end traceability achieved?",
            "How are allergens controlled through production?",
            "What's the food safety culture and management commitment?",
            "How are temperature/cold chain requirements monitored?",
            "How is recall readiness tested?"
        ],

        "compliance_drivers": ["FDA FSMA", "HACCP", "SQF", "BRC", "FSSC 22000", "State regulations", "Customer requirements"],

        "diligence_considerations": {
            "key_questions": [
                "What food safety certifications are held (SQF, BRC, FSSC 22000)?",
                "When was the last certification audit and what were the findings?",
                "Has there been any FDA inspections or warning letters?",
                "What is the recall history and mock recall performance?",
                "How is lot traceability maintained - can they trace one-up, one-back?",
                "What is the HACCP plan status and CCP monitoring approach?",
                "How is allergen control managed through production?",
                "Are there any open customer corrective actions?"
            ],
            "red_flags": [
                "Loss of GFSI certification or critical audit findings",
                "FDA warning letters or 483 observations",
                "Product recalls in the past 3 years",
                "Cannot complete mock recall in 4 hours or less",
                "Traceability gaps - cannot trace one-up, one-back",
                "Manual HACCP records without real-time CCP monitoring",
                "Allergen control gaps or undeclared allergen history",
                "No food safety management system",
                "Paper-based supplier COA management",
                "Temperature monitoring gaps in cold chain",
                "Major customer audit failures or loss of customer approvals"
            ],
            "cost_implications": {
                "food_erp": "Food/beverage ERP implementation: $1M-$5M",
                "traceability_system": "Traceability system: $200K-$800K",
                "food_safety_system": "Food safety management system: $150K-$500K",
                "haccp_monitoring": "Automated CCP monitoring: $100K-$400K",
                "certification_remediation": "GFSI certification remediation: $100K-$400K",
                "recall_cost": "Average food recall cost: $10M+",
                "supplier_management": "Supplier compliance system: $100K-$300K"
            },
            "integration_considerations": [
                "Food safety certifications need to be maintained through transition",
                "Customer approvals may require re-audit post-transaction",
                "FDA registration needs to be updated for ownership change",
                "FSMA requirements continue through change of ownership",
                "Supplier approvals and specifications need to be preserved",
                "Lot traceability data must be maintained through transition",
                "Recipe and formulation IP needs protection"
            ],
            "what_good_looks_like": [
                "Current GFSI certification (SQF, BRC, FSSC) with high score",
                "Clean FDA inspection history",
                "Automated lot traceability with <4 hour mock recall",
                "Real-time CCP monitoring with alerts",
                "Documented allergen control program",
                "Electronic HACCP records and food safety system",
                "Supplier compliance management with COA validation",
                "Strong food safety culture with trained team",
                "No significant recalls"
            ]
        }
    },

    # =========================================================================
    # PROFESSIONAL SERVICES
    # =========================================================================
    "professional_services": {
        "display_name": "Professional Services",
        "triggers": [
            "professional services", "consulting", "law firm", "legal",
            "accounting firm", "CPA", "engineering firm", "architecture",
            "staffing", "recruiting", "marketing agency"
        ],

        "relevance_questions": [
            "What type of professional services?",
            "Is work project-based or ongoing engagements?",
            "How is work delivered (onsite, remote, deliverable-based)?",
            "What's the billing model (T&M, fixed fee, retainer)?",
            "How many billable professionals?"
        ],

        "expected_applications": {
            "psa": {
                "name": "Professional Services Automation (PSA)",
                "purpose": "Project management, resource management, time/billing",
                "common_vendors": ["Kantata (Mavenlink)", "Certinia (FinancialForce)", "Autotask", "ConnectWise"],
                "questions": [
                    "What PSA or project management system is used?",
                    "How are projects tracked and managed?",
                    "How does it integrate with financials?"
                ],
                "gap_risk": "high"
            },
            "time_expense": {
                "name": "Time & Expense Tracking",
                "purpose": "Time capture, expense reporting, approvals",
                "common_vendors": ["Often in PSA", "Replicon", "BigTime", "Harvest", "NetSuite"],
                "questions": [
                    "How is time tracked?",
                    "What's the timesheet compliance rate?",
                    "How are expenses captured and approved?"
                ],
                "gap_risk": "critical"
            },
            "resource_management": {
                "name": "Resource Management / Staffing",
                "purpose": "Resource planning, utilization, skills management",
                "common_vendors": ["Kantata", "Retain", "Tempus", "Often in PSA"],
                "questions": [
                    "How is resource planning done?",
                    "How is utilization tracked?",
                    "How are skills and availability managed?"
                ],
                "gap_risk": "medium"
            },
            "crm_pipeline": {
                "name": "CRM / Pipeline Management",
                "purpose": "Opportunity tracking, proposals, client management",
                "common_vendors": ["Salesforce", "HubSpot", "Microsoft Dynamics", "Pipedrive"],
                "questions": [
                    "What CRM is used?",
                    "How is pipeline tracked?",
                    "How are proposals managed?"
                ],
                "gap_risk": "medium"
            },
            "document_management": {
                "name": "Document / Knowledge Management",
                "purpose": "Work product storage, templates, knowledge base",
                "common_vendors": ["SharePoint", "Box", "Google Drive", "iManage (legal)", "NetDocuments (legal)"],
                "questions": [
                    "How is client work product managed?",
                    "Is there a knowledge management system?",
                    "How are templates and methodologies maintained?"
                ],
                "gap_risk": "medium"
            },
            "matter_management": {
                "name": "Matter Management (Legal)",
                "purpose": "Matter tracking, conflicts, client/matter data",
                "common_vendors": ["Clio", "PracticePanther", "CosmoLex", "Thomson Reuters"],
                "questions": [
                    "What system manages matters/engagements?",
                    "How are conflicts checked?",
                    "How is matter profitability tracked?"
                ],
                "gap_risk": "critical_if_legal"
            }
        },

        "management_questions": [
            "How is utilization measured and managed?",
            "What's the time-to-billing cycle?",
            "How is project profitability tracked?",
            "How is client data protected?",
            "What's the approach to SOC 2 / client security requirements?"
        ],

        "compliance_drivers": ["Client requirements", "SOC 2 (often)", "Industry-specific (legal ethics, CPA standards)"],

        "diligence_considerations": {
            "key_questions": [
                "What is the time tracking and billing system?",
                "What is the utilization rate and how is it measured?",
                "Is there a PSA platform or project management system?",
                "How is project profitability tracked in real-time?",
                "What is the SOC 2 or security compliance status?",
                "How is client confidential data protected?",
                "What is the time-to-invoice cycle?",
                "How are matters/engagements managed (for legal/accounting)?"
            ],
            "red_flags": [
                "Time tracking via spreadsheets or manual entry",
                "No real-time visibility into project profitability",
                "Utilization tracking is lagging or inaccurate",
                "No PSA - project management disconnected from financials",
                "Long time-to-invoice cycle (>30 days)",
                "No SOC 2 when serving enterprise clients",
                "Client data not segregated or protected",
                "Knowledge management is ad-hoc or person-dependent",
                "No conflict checking system (for legal)",
                "Multiple disconnected systems for time, billing, projects"
            ],
            "cost_implications": {
                "psa_implementation": "PSA platform implementation: $200K-$1M",
                "time_billing": "Time and billing system: $100K-$500K",
                "resource_management": "Resource management system: $100K-$300K",
                "soc2_certification": "SOC 2 certification: $100K-$300K",
                "document_management": "Document/knowledge management: $100K-$400K",
                "matter_management": "Matter management (legal): $150K-$500K",
                "system_integration": "System integration work: $100K-$400K"
            },
            "integration_considerations": [
                "Client relationships are often partner/principal-dependent",
                "Engagement letters may have assignment restrictions",
                "SOC 2 certification needs to be maintained through transition",
                "Work product and IP ownership needs to be clear",
                "Professional licensing (CPA, bar admission) is individual-based",
                "Client data migration has confidentiality implications",
                "Non-compete and non-solicit agreements with key staff"
            ],
            "what_good_looks_like": [
                "Integrated PSA platform (Kantata, Certinia)",
                "Real-time time tracking with high compliance",
                "Project profitability visible during engagement",
                "Short time-to-invoice cycle (<15 days)",
                "SOC 2 Type 2 certified",
                "Knowledge management system with templates",
                "Resource management with skills tracking",
                "Client data protection with access controls"
            ]
        }
    },

    # =========================================================================
    # EDUCATION (K-12 and Higher Ed)
    # =========================================================================
    "education": {
        "display_name": "Education",
        "triggers": [
            "education", "school", "university", "college", "K-12",
            "higher education", "student", "campus", "academic",
            "LMS", "SIS", "FERPA"
        ],

        "relevance_questions": [
            "What type of institution (K-12, higher ed, for-profit)?",
            "Public or private?",
            "How many students/campuses?",
            "Do they have online/distance learning?",
            "Do they have research operations?"
        ],

        "expected_applications": {
            "sis": {
                "name": "Student Information System (SIS)",
                "purpose": "Student records, enrollment, grades, transcripts",
                "common_vendors": ["Ellucian Banner/Colleague", "Workday Student", "PowerSchool", "Infinite Campus", "Oracle PeopleSoft"],
                "questions": [
                    "What SIS is used?",
                    "How old is the system?",
                    "How integrated is it with other campus systems?",
                    "How is student data privacy managed?"
                ],
                "compliance_drivers": ["FERPA"],
                "gap_risk": "critical"
            },
            "lms": {
                "name": "Learning Management System (LMS)",
                "purpose": "Course delivery, assignments, grades, content",
                "common_vendors": ["Canvas", "Blackboard", "Moodle", "D2L Brightspace", "Google Classroom"],
                "questions": [
                    "What LMS is used?",
                    "What's the adoption rate among faculty?",
                    "How is it integrated with SIS?"
                ],
                "gap_risk": "high"
            },
            "financial_aid": {
                "name": "Financial Aid Management",
                "purpose": "Aid packaging, disbursement, compliance",
                "common_vendors": ["Often in SIS", "Regent", "CampusLogic"],
                "questions": [
                    "What system manages financial aid?",
                    "How is Title IV compliance managed?",
                    "How is aid packaging automated?"
                ],
                "compliance_drivers": ["Title IV", "State aid programs"],
                "gap_risk": "critical_if_higher_ed"
            },
            "crm_enrollment": {
                "name": "CRM / Enrollment Management",
                "purpose": "Recruitment, admissions, student success",
                "common_vendors": ["Salesforce Education Cloud", "Slate", "TargetX", "Ellucian CRM"],
                "questions": [
                    "What CRM is used for enrollment?",
                    "How is the enrollment funnel managed?",
                    "Is there student success/retention tracking?"
                ],
                "gap_risk": "medium"
            },
            "research_admin": {
                "name": "Research Administration",
                "purpose": "Grants, compliance, effort reporting, IRB",
                "common_vendors": ["Cayuse", "InfoEd", "Kuali", "Huron"],
                "questions": [
                    "How are grants and sponsored research managed?",
                    "What system handles research compliance?",
                    "How is effort reporting managed?"
                ],
                "compliance_drivers": ["OMB Uniform Guidance", "NSF", "NIH"],
                "gap_risk": "critical_if_research"
            },
            "advancement": {
                "name": "Advancement / Fundraising",
                "purpose": "Donor management, campaigns, alumni relations",
                "common_vendors": ["Blackbaud", "Ellucian Advance", "Salesforce"],
                "questions": [
                    "What system manages advancement/fundraising?",
                    "How is donor data integrated with other systems?",
                    "How are campaigns managed?"
                ],
                "gap_risk": "medium"
            }
        },

        "management_questions": [
            "How is FERPA compliance managed?",
            "How is student data integrated across systems?",
            "What's the identity management approach for students/faculty/staff?",
            "How is academic technology supported?",
            "What's the cybersecurity posture for student data?"
        ],

        "compliance_drivers": ["FERPA", "Title IV (financial aid)", "State education regulations", "Accreditation"],

        "diligence_considerations": {
            "key_questions": [
                "What SIS is used and what is its age and status?",
                "What is the accreditation status and next review?",
                "Is there Title IV participation and what is compliance status?",
                "How is FERPA compliance managed?",
                "What is the LMS platform and faculty adoption?",
                "What is the enrollment trend and technology support for recruitment?",
                "Are there any open compliance findings from accreditors or ED?",
                "What research systems exist (if research institution)?"
            ],
            "red_flags": [
                "SIS is legacy or unsupported platform",
                "Accreditation on warning or probation",
                "Title IV compliance findings or heightened oversight",
                "FERPA violations or complaints",
                "Low LMS adoption or outdated platform",
                "Declining enrollment without recruitment technology",
                "Research compliance issues (if applicable)",
                "Financial aid processing is manual or error-prone",
                "Student data exposed or breach history",
                "No disaster recovery for student records"
            ],
            "cost_implications": {
                "sis_replacement": "SIS replacement: $5M-$30M (higher ed)",
                "sis_k12": "SIS replacement (K-12): $500K-$3M",
                "lms_implementation": "LMS implementation: $500K-$2M",
                "crm_enrollment": "Enrollment CRM: $300K-$1M",
                "financial_aid": "Financial aid system: $500K-$2M",
                "research_admin": "Research administration system: $500K-$3M",
                "security_program": "Student data security program: $200K-$600K"
            },
            "integration_considerations": [
                "Accreditation approval may be required for ownership changes",
                "Title IV participation is institution-specific",
                "State authorizations may need to be re-obtained",
                "Student records must be preserved regardless of outcome",
                "Faculty contracts and tenure considerations",
                "Research grants may have assignment restrictions",
                "Athletic conference membership (if applicable)"
            ],
            "what_good_looks_like": [
                "Modern SIS with vendor support",
                "Clean accreditation status with no findings",
                "Title IV compliance with no heightened oversight",
                "Documented FERPA compliance program",
                "Modern LMS with high faculty adoption",
                "CRM for enrollment management",
                "Integrated financial aid processing",
                "Student data protected with encryption and access controls"
            ]
        }
    },

    # =========================================================================
    # HOSPITALITY
    # =========================================================================
    "hospitality": {
        "display_name": "Hospitality",
        "triggers": [
            "hotel", "hospitality", "resort", "casino", "restaurant",
            "food service", "lodging", "property management", "PMS",
            "guest", "reservation"
        ],

        "relevance_questions": [
            "What type of hospitality (hotels, restaurants, casinos)?",
            "How many properties/locations?",
            "Are they franchised or managed properties?",
            "Do they have F&B operations?",
            "Do they have a loyalty program?"
        ],

        "expected_applications": {
            "pms": {
                "name": "Property Management System (PMS)",
                "purpose": "Reservations, guest check-in/out, room management",
                "common_vendors": ["Oracle Opera", "Mews", "Cloudbeds", "Infor HMS", "Agilysys"],
                "questions": [
                    "What PMS is used?",
                    "Is it cloud-based or on-prem?",
                    "How integrated is it with other hotel systems?",
                    "How is it configured per property?"
                ],
                "gap_risk": "critical"
            },
            "crs": {
                "name": "Central Reservation System (CRS)",
                "purpose": "Multi-property reservations, distribution, channel management",
                "common_vendors": ["SynXis", "Sabre", "Pegasus", "Often in PMS"],
                "questions": [
                    "What CRS is used?",
                    "How is distribution/channel management handled?",
                    "How are rates synchronized across channels?"
                ],
                "gap_risk": "high_if_multi_property"
            },
            "pos_hospitality": {
                "name": "Restaurant POS / F&B",
                "purpose": "Restaurant transactions, kitchen management, tabs",
                "common_vendors": ["Oracle Simphony", "Toast", "Aloha", "Square"],
                "questions": [
                    "What POS is used for F&B?",
                    "How does it integrate with PMS for room charges?",
                    "How is inventory managed?"
                ],
                "compliance_drivers": ["PCI-DSS"],
                "gap_risk": "high_if_fb"
            },
            "revenue_management": {
                "name": "Revenue Management System (RMS)",
                "purpose": "Pricing optimization, demand forecasting",
                "common_vendors": ["IDeaS", "Duetto", "Rainmaker"],
                "questions": [
                    "What revenue management system is used?",
                    "How automated is pricing?",
                    "How does it connect to PMS and CRS?"
                ],
                "gap_risk": "medium"
            },
            "loyalty": {
                "name": "Loyalty / Guest Management",
                "purpose": "Loyalty program, guest profiles, personalization",
                "common_vendors": ["Salesforce", "Oracle Loyalty", "Cendyn", "Custom"],
                "questions": [
                    "Is there a loyalty program?",
                    "How is guest data unified across properties?",
                    "How is personalization delivered?"
                ],
                "gap_risk": "medium"
            },
            "spa_golf": {
                "name": "Spa / Golf / Activities Management",
                "purpose": "Spa scheduling, golf tee times, activities booking",
                "common_vendors": ["SpaSoft", "Book4Time", "EZLinks (golf)", "Often in PMS"],
                "questions": [
                    "What systems manage spa/golf/activities?",
                    "How do they integrate with PMS?",
                    "How are charges posted to guest folio?"
                ],
                "gap_risk": "medium_if_amenities"
            }
        },

        "management_questions": [
            "How is guest data shared across properties?",
            "What's the PCI scope and compliance approach?",
            "How is technology managed at property vs. corporate level?",
            "How is the tech stack standardized across properties?",
            "What's the approach to franchise vs. managed properties?"
        ],

        "compliance_drivers": ["PCI-DSS", "State gaming regulations (if casino)", "Health department (F&B)", "Privacy regulations"],

        "diligence_considerations": {
            "key_questions": [
                "What PMS is used and is it standardized across properties?",
                "What is the PCI compliance status and scope?",
                "How is revenue management handled?",
                "Is there a loyalty program and what system supports it?",
                "What is the technology governance model (corporate vs property)?",
                "How are franchise vs managed properties handled differently?",
                "What is the F&B technology stack?",
                "Are there gaming operations and what is compliance status (if casino)?"
            ],
            "red_flags": [
                "Different PMS across properties with no integration",
                "PCI compliance gaps or recent cardholder data incidents",
                "No revenue management system - manual pricing",
                "Guest data fragmented across properties",
                "POS systems on unsupported platforms",
                "No standardization across franchise properties",
                "Gaming compliance issues or regulatory findings (if casino)",
                "Property networks not segmented or secured",
                "No corporate IT oversight of property technology",
                "Legacy on-premise PMS with no cloud roadmap"
            ],
            "cost_implications": {
                "pms_replacement": "PMS replacement: $500K-$2M per property (full-service)",
                "pms_standardization": "PMS standardization program: $5M-$30M (multi-property)",
                "pos_replacement": "F&B POS replacement: $100K-$500K per property",
                "revenue_management": "Revenue management system: $200K-$800K",
                "loyalty_platform": "Loyalty platform: $500K-$3M",
                "pci_remediation": "PCI remediation: $200K-$800K",
                "network_segmentation": "Property network segmentation: $50K-$150K per property"
            },
            "integration_considerations": [
                "Management agreements may have technology provisions",
                "Franchise agreements may restrict or require certain systems",
                "Brand standards may mandate specific technology",
                "OTA and channel manager connections need to be maintained",
                "Guest data belongs to the property/brand - migration is complex",
                "Loyalty program is often a key asset",
                "Gaming licenses are property and entity-specific (if casino)",
                "Union considerations at properties"
            ],
            "what_good_looks_like": [
                "Standardized PMS across portfolio",
                "Current PCI compliance (ROC or SAQ as appropriate)",
                "Revenue management system with dynamic pricing",
                "Unified guest profile across properties",
                "Loyalty program with integrated technology",
                "Standardized F&B POS",
                "Corporate IT governance with property support model",
                "Secure, segmented property networks"
            ]
        }
    }
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def detect_industry_from_text(text: str) -> List[Tuple[str, int]]:
    """
    Detect likely industries from document text based on trigger patterns.

    Args:
        text: Document text to analyze

    Returns:
        List of (industry_key, match_count) tuples, sorted by match count descending
    """
    text_lower = text.lower()
    matches = []

    for industry_key, config in INDUSTRY_APPLICATION_CONSIDERATIONS.items():
        triggers = config.get("triggers", [])
        match_count = sum(1 for trigger in triggers if trigger.lower() in text_lower)
        if match_count > 0:
            matches.append((industry_key, match_count))

    # Sort by match count descending
    matches.sort(key=lambda x: x[1], reverse=True)
    return matches


def get_industry_considerations(industry: str) -> Optional[Dict]:
    """
    Get the full considerations config for an industry.

    Args:
        industry: Industry key (e.g., "healthcare", "manufacturing")

    Returns:
        Industry configuration dict or None if not found
    """
    return INDUSTRY_APPLICATION_CONSIDERATIONS.get(industry.lower())


def get_all_industries() -> List[Dict]:
    """
    Get list of all defined industries with their display names.

    Returns:
        List of dicts with industry_key and display_name
    """
    return [
        {"key": key, "display_name": config["display_name"]}
        for key, config in INDUSTRY_APPLICATION_CONSIDERATIONS.items()
    ]


def inject_industry_into_discovery_prompt(
    base_prompt: str,
    industry: str,
    include_relevance: bool = True,
    include_expected_apps: bool = True,
    include_management: bool = True
) -> str:
    """
    Inject industry-specific considerations into the applications discovery prompt.

    Args:
        base_prompt: The base applications discovery prompt
        industry: Detected industry key
        include_relevance: Include relevance questions section
        include_expected_apps: Include expected applications section
        include_management: Include management questions section

    Returns:
        Enhanced prompt with industry context
    """
    config = get_industry_considerations(industry)
    if not config:
        return base_prompt

    industry_section = f"""

## INDUSTRY-SPECIFIC CONSIDERATIONS: {config['display_name'].upper()}

This target company has been identified as operating in the **{config['display_name']}** industry.
In addition to the standard application inventory, probe for the following industry-specific applications and considerations.

"""

    if include_relevance and config.get("relevance_questions"):
        industry_section += """### RELEVANCE QUESTIONS
First, determine which of these considerations apply:
"""
        for q in config["relevance_questions"]:
            industry_section += f"- {q}\n"
        industry_section += "\n"

    if include_expected_apps and config.get("expected_applications"):
        industry_section += """### EXPECTED INDUSTRY APPLICATIONS
Look for and document these industry-specific application types:

"""
        for app_key, app_config in config["expected_applications"].items():
            industry_section += f"""**{app_config['name']}**
- Purpose: {app_config['purpose']}
- Common vendors: {', '.join(app_config.get('common_vendors', ['Various'])[:5])}
- Questions to ask:
"""
            for q in app_config.get("questions", [])[:3]:
                industry_section += f"  - {q}\n"

            if app_config.get("compliance_drivers"):
                industry_section += f"- Compliance relevance: {', '.join(app_config['compliance_drivers'])}\n"

            gap_risk = app_config.get("gap_risk", "medium")
            industry_section += f"- Gap risk if missing: {gap_risk}\n\n"

    if include_management and config.get("management_questions"):
        industry_section += """### MANAGEMENT & INTEGRATION QUESTIONS
"""
        for q in config["management_questions"]:
            industry_section += f"- {q}\n"
        industry_section += "\n"

    if config.get("compliance_drivers"):
        industry_section += f"""### COMPLIANCE DRIVERS
Key compliance frameworks for this industry: {', '.join(config['compliance_drivers'])}

"""

    # Insert before the WORKFLOW section of the base prompt
    if "## WORKFLOW" in base_prompt:
        insertion_point = base_prompt.find("## WORKFLOW")
        return base_prompt[:insertion_point] + industry_section + base_prompt[insertion_point:]
    else:
        return base_prompt + industry_section


def assess_industry_application_gaps(
    discovered_apps: List[Dict],
    industry: str
) -> List[Dict]:
    """
    Compare discovered applications against industry expectations and identify gaps.

    Args:
        discovered_apps: List of discovered application inventory entries
        industry: Industry key

    Returns:
        List of gap assessments with risk ratings
    """
    config = get_industry_considerations(industry)
    if not config:
        return []

    expected = config.get("expected_applications", {})
    gaps = []

    # Build lookup of discovered apps by category and name
    discovered_lookup = {}
    for app in discovered_apps:
        cat = app.get("category", "").lower()
        name = app.get("item", "").lower()
        vendor = app.get("vendor", "").lower()
        discovered_lookup[f"{cat}:{name}"] = app
        discovered_lookup[f"vendor:{vendor}"] = app

    for app_key, app_config in expected.items():
        # Check if this expected app type was found
        found = False
        found_app = None

        # Check by common vendor names
        for vendor in app_config.get("common_vendors", []):
            if f"vendor:{vendor.lower()}" in discovered_lookup:
                found = True
                found_app = discovered_lookup[f"vendor:{vendor.lower()}"]
                break

        # Check by name patterns
        if not found:
            app_name_lower = app_config["name"].lower()
            for key in discovered_lookup:
                if app_name_lower in key or app_key in key:
                    found = True
                    found_app = discovered_lookup[key]
                    break

        if not found:
            gap_risk = app_config.get("gap_risk", "medium")

            # Skip conditional gaps if we don't have enough context
            if "_if_" in gap_risk:
                gap_risk = "conditional"

            gaps.append({
                "expected_application": app_config["name"],
                "purpose": app_config["purpose"],
                "gap_risk": gap_risk,
                "compliance_drivers": app_config.get("compliance_drivers", []),
                "status": "not_found",
                "recommendation": f"Probe further for {app_config['name']} or equivalent system"
            })
        else:
            # App found - still note it for completeness
            gaps.append({
                "expected_application": app_config["name"],
                "purpose": app_config["purpose"],
                "gap_risk": "none",
                "status": "found",
                "found_as": found_app.get("item") if found_app else "matched",
                "compliance_drivers": app_config.get("compliance_drivers", [])
            })

    return gaps


def get_industry_prompt_summary(industry: str) -> str:
    """
    Get a concise summary of industry considerations for inclusion in prompts.

    Args:
        industry: Industry key

    Returns:
        Formatted summary string
    """
    config = get_industry_considerations(industry)
    if not config:
        return ""

    summary = f"""
**Industry: {config['display_name']}**
Key application types to look for: {', '.join([app['name'] for app in list(config['expected_applications'].values())[:5]])}
Compliance drivers: {', '.join(config.get('compliance_drivers', [])[:5])}
"""
    return summary


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'INDUSTRY_APPLICATION_CONSIDERATIONS',
    'detect_industry_from_text',
    'get_industry_considerations',
    'get_all_industries',
    'inject_industry_into_discovery_prompt',
    'assess_industry_application_gaps',
    'get_industry_prompt_summary'
]
