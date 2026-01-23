"""
Activity Templates V2 - Phase 4: Data & Migration

Phase 4: Data & Migration Workstream
- Structured Data (databases - SQL Server, Oracle, PostgreSQL, MySQL)
- Unstructured Data (file shares, SharePoint, OneDrive)
- Data Archival & Retention
- Migration Tooling & Automation

Each activity template includes:
- name: Activity name
- description: What this activity involves
- activity_type: "implementation", "operational", "license"
- cost_model: How cost is calculated
- timeline_months: Duration range
- requires_tsa: Whether TSA is typically needed
- tsa_duration: TSA duration if applicable
- prerequisites: What must happen first
- outputs: Deliverables
- notes: Implementation considerations

Cost Anchor Sources:
- Database migration services pricing
- Cloud provider migration tools
- Data migration vendor rates
- Historical deal data
"""

from typing import Dict, List

# Import shared modifiers from Phase 1
from tools_v2.activity_templates_v2 import COMPLEXITY_MULTIPLIERS, INDUSTRY_MODIFIERS

# =============================================================================
# PHASE 4: DATABASE SEPARATION
# =============================================================================

DATABASE_TEMPLATES = {
    "parent_dependency": [
        # -----------------------------------------------------------------
        # ASSESSMENT
        # -----------------------------------------------------------------
        {
            "id": "DAT-001",
            "name": "Database landscape assessment",
            "description": "Inventory and assess all databases requiring separation",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (30000, 75000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["Database inventory", "Size analysis", "Technology matrix", "Dependency map"],
        },
        {
            "id": "DAT-002",
            "name": "Database schema analysis",
            "description": "Analyze database schemas for data separation requirements",
            "activity_type": "implementation",
            "phase": "assessment",
            "per_database_cost": (1500, 4000),
            "base_cost": (15000, 40000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["DAT-001"],
            "outputs": ["Schema documentation", "Table ownership", "Data classification", "Separation approach"],
        },
        {
            "id": "DAT-003",
            "name": "Database dependency mapping",
            "description": "Map application and integration dependencies for each database",
            "activity_type": "implementation",
            "phase": "assessment",
            "per_database_cost": (1000, 3000),
            "base_cost": (15000, 35000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["DAT-001"],
            "outputs": ["Dependency matrix", "Application mapping", "Integration inventory"],
        },
        {
            "id": "DAT-004",
            "name": "Data classification and sensitivity analysis",
            "description": "Classify data for compliance and security requirements",
            "activity_type": "implementation",
            "phase": "assessment",
            "per_database_cost": (2000, 5000),
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["DAT-002"],
            "outputs": ["Data classification", "PII inventory", "Compliance requirements", "Handling procedures"],
        },
        {
            "id": "DAT-005",
            "name": "Database separation strategy design",
            "description": "Design database separation approach and target architecture",
            "activity_type": "implementation",
            "phase": "design",
            "base_cost": (40000, 100000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["DAT-001", "DAT-002", "DAT-003", "DAT-004"],
            "outputs": ["Separation strategy", "Target architecture", "Migration approach", "Tooling selection"],
        },
        # -----------------------------------------------------------------
        # SQL SERVER
        # -----------------------------------------------------------------
        {
            "id": "DAT-010",
            "name": "SQL Server database migration - Simple",
            "description": "Migrate simple SQL Server databases (standalone, minimal dependencies)",
            "activity_type": "implementation",
            "phase": "migration",
            "per_database_cost": (3000, 8000),
            "timeline_months": (1, 2),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["DAT-005"],
            "outputs": ["Migrated database", "Validation reports", "Connection string updates"],
            "notes": "Simple = <100GB, minimal stored procedures, few integrations",
        },
        {
            "id": "DAT-011",
            "name": "SQL Server database migration - Complex",
            "description": "Migrate complex SQL Server databases with extensive logic",
            "activity_type": "implementation",
            "phase": "migration",
            "per_database_cost": (10000, 30000),
            "timeline_months": (2, 4),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["DAT-005"],
            "outputs": ["Migrated database", "Stored procedure migration", "Job migration", "Linked server config"],
            "notes": "Complex = >100GB, extensive stored procedures, many integrations",
        },
        {
            "id": "DAT-012",
            "name": "SQL Server Always On/clustering migration",
            "description": "Migrate SQL Server with HA/DR configuration",
            "activity_type": "implementation",
            "phase": "migration",
            "per_database_cost": (15000, 40000),
            "timeline_months": (2, 5),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["DAT-005"],
            "outputs": ["Migrated cluster", "AG configuration", "Failover testing", "DR validation"],
        },
        {
            "id": "DAT-013",
            "name": "SQL Server to Azure SQL migration",
            "description": "Migrate SQL Server to Azure SQL Database or Managed Instance",
            "activity_type": "implementation",
            "phase": "migration",
            "per_database_cost": (8000, 25000),
            "timeline_months": (2, 4),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["DAT-005"],
            "outputs": ["Azure SQL database", "Compatibility fixes", "Performance tuning", "Connection updates"],
        },
        # -----------------------------------------------------------------
        # ORACLE
        # -----------------------------------------------------------------
        {
            "id": "DAT-020",
            "name": "Oracle database migration - Simple",
            "description": "Migrate simple Oracle databases",
            "activity_type": "implementation",
            "phase": "migration",
            "per_database_cost": (5000, 15000),
            "timeline_months": (1, 3),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["DAT-005"],
            "outputs": ["Migrated database", "Schema export/import", "Validation"],
        },
        {
            "id": "DAT-021",
            "name": "Oracle database migration - Complex",
            "description": "Migrate complex Oracle databases with RAC/Data Guard",
            "activity_type": "implementation",
            "phase": "migration",
            "per_database_cost": (20000, 60000),
            "timeline_months": (3, 6),
            "requires_tsa": True,
            "tsa_duration": (6, 12),
            "prerequisites": ["DAT-005"],
            "outputs": ["Migrated database", "RAC configuration", "Data Guard setup", "PL/SQL migration"],
        },
        {
            "id": "DAT-022",
            "name": "Oracle to PostgreSQL migration",
            "description": "Migrate Oracle database to PostgreSQL (cost optimization)",
            "activity_type": "implementation",
            "phase": "migration",
            "per_database_cost": (25000, 75000),
            "timeline_months": (3, 8),
            "requires_tsa": True,
            "tsa_duration": (6, 12),
            "prerequisites": ["DAT-005"],
            "outputs": ["PostgreSQL database", "Schema conversion", "PL/SQL to PL/pgSQL", "Application changes"],
            "notes": "Significant effort but major license cost savings",
        },
        {
            "id": "DAT-023",
            "name": "Oracle to AWS RDS migration",
            "description": "Migrate Oracle to AWS RDS Oracle or Aurora",
            "activity_type": "implementation",
            "phase": "migration",
            "per_database_cost": (15000, 45000),
            "timeline_months": (2, 5),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["DAT-005"],
            "outputs": ["RDS database", "DMS configuration", "Performance validation"],
        },
        # -----------------------------------------------------------------
        # MYSQL/POSTGRESQL/OTHER
        # -----------------------------------------------------------------
        {
            "id": "DAT-030",
            "name": "MySQL/MariaDB database migration",
            "description": "Migrate MySQL or MariaDB databases",
            "activity_type": "implementation",
            "phase": "migration",
            "per_database_cost": (2000, 8000),
            "timeline_months": (1, 2),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["DAT-005"],
            "outputs": ["Migrated database", "Replication setup", "Validation"],
        },
        {
            "id": "DAT-031",
            "name": "PostgreSQL database migration",
            "description": "Migrate PostgreSQL databases",
            "activity_type": "implementation",
            "phase": "migration",
            "per_database_cost": (2000, 8000),
            "timeline_months": (1, 2),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["DAT-005"],
            "outputs": ["Migrated database", "Extension migration", "Validation"],
        },
        {
            "id": "DAT-032",
            "name": "NoSQL database migration (MongoDB, Cosmos)",
            "description": "Migrate NoSQL databases",
            "activity_type": "implementation",
            "phase": "migration",
            "per_database_cost": (5000, 15000),
            "timeline_months": (1, 3),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["DAT-005"],
            "outputs": ["Migrated database", "Collection migration", "Index rebuild"],
        },
        # -----------------------------------------------------------------
        # DATA WAREHOUSE / ANALYTICS
        # -----------------------------------------------------------------
        {
            "id": "DAT-040",
            "name": "Data warehouse separation assessment",
            "description": "Assess data warehouse for separation requirements",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (30000, 80000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["DAT-001"],
            "outputs": ["DW inventory", "Data lineage", "Report inventory", "ETL mapping"],
        },
        {
            "id": "DAT-041",
            "name": "Data warehouse migration",
            "description": "Migrate data warehouse to standalone environment",
            "activity_type": "implementation",
            "phase": "migration",
            "base_cost": (100000, 300000),
            "timeline_months": (3, 8),
            "requires_tsa": True,
            "tsa_duration": (6, 12),
            "prerequisites": ["DAT-040", "DAT-005"],
            "outputs": ["Migrated DW", "ETL migration", "Report migration", "Historical data"],
        },
        {
            "id": "DAT-042",
            "name": "Cloud data platform migration (Snowflake/Databricks)",
            "description": "Migrate to modern cloud data platform",
            "activity_type": "implementation",
            "phase": "migration",
            "base_cost": (75000, 250000),
            "per_tb_cost": (500, 1500),
            "timeline_months": (3, 8),
            "requires_tsa": True,
            "tsa_duration": (6, 12),
            "prerequisites": ["DAT-040"],
            "outputs": ["Cloud data platform", "Data pipelines", "Analytics migration"],
        },
        # -----------------------------------------------------------------
        # VALIDATION & CUTOVER
        # -----------------------------------------------------------------
        {
            "id": "DAT-050",
            "name": "Database migration validation",
            "description": "Validate migrated databases for data integrity",
            "activity_type": "implementation",
            "phase": "testing",
            "per_database_cost": (1500, 4000),
            "base_cost": (15000, 40000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["DAT-010", "DAT-011"],
            "outputs": ["Validation scripts", "Data comparison", "Integrity reports"],
        },
        {
            "id": "DAT-051",
            "name": "Database cutover execution",
            "description": "Execute database cutover with minimal downtime",
            "activity_type": "implementation",
            "phase": "cutover",
            "per_database_cost": (2000, 6000),
            "base_cost": (20000, 50000),
            "timeline_months": (0.25, 0.75),
            "requires_tsa": False,
            "prerequisites": ["DAT-050"],
            "outputs": ["Cutover execution", "Final sync", "Validation", "Rollback plan"],
        },
    ],
}

# =============================================================================
# PHASE 4: FILE DATA (SharePoint, File Shares, OneDrive)
# =============================================================================

FILE_DATA_TEMPLATES = {
    "parent_dependency": [
        # -----------------------------------------------------------------
        # ASSESSMENT
        # -----------------------------------------------------------------
        {
            "id": "FIL-001",
            "name": "File data landscape assessment",
            "description": "Inventory file shares, SharePoint sites, and cloud storage",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["File share inventory", "SharePoint site inventory", "Cloud storage inventory", "Size analysis"],
        },
        {
            "id": "FIL-002",
            "name": "File data ownership analysis",
            "description": "Analyze data ownership and access permissions",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (15000, 40000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["FIL-001"],
            "outputs": ["Ownership matrix", "Permission analysis", "Access patterns", "Orphaned data"],
        },
        {
            "id": "FIL-003",
            "name": "File data classification",
            "description": "Classify file data for sensitivity and retention",
            "activity_type": "implementation",
            "phase": "assessment",
            "per_tb_cost": (500, 1500),
            "base_cost": (15000, 40000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["FIL-001"],
            "outputs": ["Data classification", "Sensitivity labels", "Retention requirements"],
        },
        {
            "id": "FIL-004",
            "name": "File migration strategy design",
            "description": "Design file data migration approach",
            "activity_type": "implementation",
            "phase": "design",
            "base_cost": (25000, 60000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["FIL-001", "FIL-002", "FIL-003"],
            "outputs": ["Migration strategy", "Wave planning", "Tool selection", "Communication plan"],
        },
        # -----------------------------------------------------------------
        # FILE SHARE MIGRATION
        # -----------------------------------------------------------------
        {
            "id": "FIL-010",
            "name": "Windows file share migration",
            "description": "Migrate Windows file shares to new environment",
            "activity_type": "implementation",
            "phase": "migration",
            "per_tb_cost": (200, 600),
            "base_cost": (15000, 40000),
            "timeline_months": (1, 3),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["FIL-004"],
            "outputs": ["Migrated file shares", "Permission mapping", "DFS configuration"],
        },
        {
            "id": "FIL-011",
            "name": "NAS/SAN file migration",
            "description": "Migrate NAS or SAN-based file storage",
            "activity_type": "implementation",
            "phase": "migration",
            "per_tb_cost": (150, 400),
            "base_cost": (20000, 50000),
            "timeline_months": (1, 3),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["FIL-004"],
            "outputs": ["Migrated storage", "Mount point updates", "Performance validation"],
        },
        {
            "id": "FIL-012",
            "name": "File share to cloud migration (Azure Files/FSx)",
            "description": "Migrate file shares to cloud file services",
            "activity_type": "implementation",
            "phase": "migration",
            "per_tb_cost": (300, 800),
            "base_cost": (25000, 60000),
            "timeline_months": (1, 4),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["FIL-004"],
            "outputs": ["Cloud file shares", "Sync configuration", "Access tier setup"],
        },
        # -----------------------------------------------------------------
        # SHAREPOINT MIGRATION
        # -----------------------------------------------------------------
        {
            "id": "FIL-020",
            "name": "SharePoint site inventory and planning",
            "description": "Detailed inventory and migration planning for SharePoint",
            "activity_type": "implementation",
            "phase": "assessment",
            "per_site_cost": (500, 1500),
            "base_cost": (15000, 40000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["FIL-001"],
            "outputs": ["Site inventory", "Content analysis", "Customization inventory", "Migration complexity"],
        },
        {
            "id": "FIL-021",
            "name": "SharePoint Online migration - Standard sites",
            "description": "Migrate standard SharePoint sites",
            "activity_type": "implementation",
            "phase": "migration",
            "per_site_cost": (1500, 4000),
            "timeline_months": (1, 3),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["FIL-020", "FIL-004"],
            "outputs": ["Migrated sites", "Permission mapping", "URL redirects"],
            "notes": "Standard = team sites, communication sites, minimal customization",
        },
        {
            "id": "FIL-022",
            "name": "SharePoint Online migration - Complex sites",
            "description": "Migrate complex SharePoint sites with customizations",
            "activity_type": "implementation",
            "phase": "migration",
            "per_site_cost": (4000, 12000),
            "timeline_months": (2, 5),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["FIL-020", "FIL-004"],
            "outputs": ["Migrated sites", "Workflow migration", "Custom solution migration"],
            "notes": "Complex = custom workflows, InfoPath forms, extensive customization",
        },
        {
            "id": "FIL-023",
            "name": "SharePoint on-premises to Online migration",
            "description": "Migrate SharePoint on-premises to SharePoint Online",
            "activity_type": "implementation",
            "phase": "migration",
            "per_site_cost": (2000, 6000),
            "base_cost": (30000, 80000),
            "timeline_months": (2, 6),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["FIL-020"],
            "outputs": ["Migrated content", "Hybrid configuration", "Search migration"],
        },
        # -----------------------------------------------------------------
        # ONEDRIVE / CLOUD STORAGE
        # -----------------------------------------------------------------
        {
            "id": "FIL-030",
            "name": "OneDrive migration",
            "description": "Migrate OneDrive content to new tenant",
            "activity_type": "implementation",
            "phase": "migration",
            "per_user_cost": (10, 30),
            "base_cost": (15000, 40000),
            "timeline_months": (1, 2),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["FIL-004"],
            "outputs": ["Migrated OneDrive", "Sharing settings", "Sync client update"],
        },
        {
            "id": "FIL-031",
            "name": "Box/Dropbox migration",
            "description": "Migrate from Box or Dropbox to new environment",
            "activity_type": "implementation",
            "phase": "migration",
            "per_user_cost": (15, 40),
            "base_cost": (20000, 50000),
            "timeline_months": (1, 3),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["FIL-004"],
            "outputs": ["Migrated content", "Permission mapping", "External sharing config"],
        },
        {
            "id": "FIL-032",
            "name": "Google Drive migration",
            "description": "Migrate from Google Drive to new environment",
            "activity_type": "implementation",
            "phase": "migration",
            "per_user_cost": (15, 40),
            "base_cost": (20000, 50000),
            "timeline_months": (1, 3),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["FIL-004"],
            "outputs": ["Migrated content", "Format conversion", "Sharing migration"],
        },
        # -----------------------------------------------------------------
        # PERMISSION REMEDIATION
        # -----------------------------------------------------------------
        {
            "id": "FIL-040",
            "name": "Permission mapping and remediation",
            "description": "Map and remediate permissions for migrated data",
            "activity_type": "implementation",
            "phase": "migration",
            "per_tb_cost": (300, 800),
            "base_cost": (20000, 50000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["FIL-010", "FIL-021"],
            "outputs": ["Permission mapping", "Group migration", "Access remediation"],
        },
        {
            "id": "FIL-041",
            "name": "Shortcut and link remediation",
            "description": "Update shortcuts, links, and mapped drives",
            "activity_type": "implementation",
            "phase": "migration",
            "per_user_cost": (5, 15),
            "base_cost": (10000, 30000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["FIL-010"],
            "outputs": ["Updated shortcuts", "Drive mappings", "Link remediation"],
        },
    ],
}

# =============================================================================
# PHASE 4: DATA ARCHIVAL & RETENTION
# =============================================================================

ARCHIVAL_TEMPLATES = {
    "parent_dependency": [
        # -----------------------------------------------------------------
        # ASSESSMENT
        # -----------------------------------------------------------------
        {
            "id": "ARC-001",
            "name": "Data retention requirements analysis",
            "description": "Analyze retention requirements across data types",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["Retention requirements", "Legal holds", "Compliance mapping", "Retention schedule"],
        },
        {
            "id": "ARC-002",
            "name": "Historical data analysis",
            "description": "Analyze historical data requirements for carveout",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (15000, 40000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["ARC-001"],
            "outputs": ["Historical data inventory", "Access requirements", "Archive strategy"],
        },
        {
            "id": "ARC-003",
            "name": "Archive strategy design",
            "description": "Design data archival approach for standalone operations",
            "activity_type": "implementation",
            "phase": "design",
            "base_cost": (25000, 60000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["ARC-001", "ARC-002"],
            "outputs": ["Archive architecture", "Platform selection", "Retention policies"],
        },
        # -----------------------------------------------------------------
        # ARCHIVE IMPLEMENTATION
        # -----------------------------------------------------------------
        {
            "id": "ARC-010",
            "name": "Archive platform deployment",
            "description": "Deploy archive storage platform",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (30000, 80000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["ARC-003"],
            "outputs": ["Archive platform", "Storage tiers", "Access controls"],
        },
        {
            "id": "ARC-011",
            "name": "Email archive migration",
            "description": "Migrate email archives (Enterprise Vault, Mimecast, etc.)",
            "activity_type": "implementation",
            "phase": "migration",
            "per_user_cost": (20, 60),
            "base_cost": (25000, 70000),
            "timeline_months": (2, 4),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["ARC-010"],
            "outputs": ["Migrated email archive", "Search capability", "Legal hold transfer"],
        },
        {
            "id": "ARC-012",
            "name": "File archive migration",
            "description": "Migrate file archives to standalone environment",
            "activity_type": "implementation",
            "phase": "migration",
            "per_tb_cost": (100, 300),
            "base_cost": (15000, 40000),
            "timeline_months": (1, 3),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["ARC-010"],
            "outputs": ["Migrated file archive", "Index migration", "Access validation"],
        },
        {
            "id": "ARC-013",
            "name": "Database archive/historical data extraction",
            "description": "Extract and archive historical database data",
            "activity_type": "implementation",
            "phase": "migration",
            "per_database_cost": (3000, 10000),
            "base_cost": (20000, 50000),
            "timeline_months": (1, 3),
            "requires_tsa": True,
            "tsa_duration": (3, 6),
            "prerequisites": ["ARC-010"],
            "outputs": ["Archived data", "Query capability", "Compliance documentation"],
        },
        # -----------------------------------------------------------------
        # LEGAL HOLD & COMPLIANCE
        # -----------------------------------------------------------------
        {
            "id": "ARC-020",
            "name": "Legal hold transfer",
            "description": "Transfer legal holds to standalone environment",
            "activity_type": "implementation",
            "phase": "migration",
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": True,
            "tsa_duration": (2, 4),
            "prerequisites": ["ARC-001"],
            "outputs": ["Transferred holds", "Custodian mapping", "Chain of custody"],
        },
        {
            "id": "ARC-021",
            "name": "eDiscovery platform setup",
            "description": "Configure eDiscovery capabilities for standalone",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (30000, 80000),
            "timeline_months": (1, 2),
            "requires_tsa": False,
            "prerequisites": ["ARC-003"],
            "outputs": ["eDiscovery platform", "Search configuration", "Export capabilities"],
        },
        {
            "id": "ARC-022",
            "name": "Retention policy implementation",
            "description": "Implement retention policies in new environment",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (15000, 40000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["ARC-001"],
            "outputs": ["Retention policies", "Auto-delete rules", "Compliance labels"],
        },
    ],
    "technical_debt": [
        {
            "id": "ARC-030",
            "name": "Legacy data cleanup",
            "description": "Identify and clean up legacy/orphaned data",
            "activity_type": "implementation",
            "phase": "migration",
            "per_tb_cost": (200, 500),
            "base_cost": (15000, 40000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["Data cleanup", "Storage reclamation", "Compliance validation"],
        },
        {
            "id": "ARC-031",
            "name": "Data deduplication",
            "description": "Deduplicate data before migration",
            "activity_type": "implementation",
            "phase": "migration",
            "per_tb_cost": (100, 300),
            "base_cost": (10000, 30000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["Deduplicated data", "Storage savings", "Migration efficiency"],
        },
    ],
}

# =============================================================================
# PHASE 4: MIGRATION TOOLING & AUTOMATION
# =============================================================================

MIGRATION_TOOLING_TEMPLATES = {
    "parent_dependency": [
        # -----------------------------------------------------------------
        # TOOLING ASSESSMENT
        # -----------------------------------------------------------------
        {
            "id": "MIG-001",
            "name": "Migration tooling assessment",
            "description": "Assess and select migration tools for data workstreams",
            "activity_type": "implementation",
            "phase": "assessment",
            "base_cost": (15000, 40000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": [],
            "outputs": ["Tool evaluation", "Selection criteria", "POC results", "Recommendations"],
        },
        {
            "id": "MIG-002",
            "name": "Migration automation strategy",
            "description": "Design migration automation approach",
            "activity_type": "implementation",
            "phase": "design",
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["MIG-001"],
            "outputs": ["Automation strategy", "Script framework", "Orchestration approach"],
        },
        # -----------------------------------------------------------------
        # TOOL DEPLOYMENT
        # -----------------------------------------------------------------
        {
            "id": "MIG-010",
            "name": "SharePoint migration tool deployment",
            "description": "Deploy SharePoint migration tools (ShareGate, Metalogix, etc.)",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (15000, 40000),
            "timeline_months": (0.25, 0.75),
            "requires_tsa": False,
            "prerequisites": ["MIG-001"],
            "outputs": ["Deployed tool", "Configuration", "License setup"],
        },
        {
            "id": "MIG-011",
            "name": "Database migration tool deployment",
            "description": "Deploy database migration tools (DMS, DMA, etc.)",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (15000, 40000),
            "timeline_months": (0.25, 0.75),
            "requires_tsa": False,
            "prerequisites": ["MIG-001"],
            "outputs": ["Deployed tool", "Connectivity", "Assessment capability"],
        },
        {
            "id": "MIG-012",
            "name": "File migration tool deployment",
            "description": "Deploy file migration tools (Robocopy, Azure File Sync, etc.)",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (10000, 30000),
            "timeline_months": (0.25, 0.5),
            "requires_tsa": False,
            "prerequisites": ["MIG-001"],
            "outputs": ["Deployed tool", "Script library", "Monitoring setup"],
        },
        {
            "id": "MIG-013",
            "name": "Cloud migration tool deployment (Azure Migrate/AWS MGN)",
            "description": "Deploy cloud provider migration tools",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["MIG-001"],
            "outputs": ["Migration appliance", "Discovery agent", "Assessment reports"],
        },
        # -----------------------------------------------------------------
        # MIGRATION ORCHESTRATION
        # -----------------------------------------------------------------
        {
            "id": "MIG-020",
            "name": "Migration wave planning",
            "description": "Plan migration waves across all data workstreams",
            "activity_type": "implementation",
            "phase": "design",
            "base_cost": (25000, 60000),
            "timeline_months": (0.5, 1.5),
            "requires_tsa": False,
            "prerequisites": ["MIG-002"],
            "outputs": ["Wave plan", "Dependencies", "Resource plan", "Communication plan"],
        },
        {
            "id": "MIG-021",
            "name": "Migration runbook development",
            "description": "Develop detailed migration runbooks",
            "activity_type": "implementation",
            "phase": "design",
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["MIG-020"],
            "outputs": ["Runbooks", "Checklists", "Rollback procedures"],
        },
        {
            "id": "MIG-022",
            "name": "Migration monitoring and reporting",
            "description": "Set up migration monitoring and progress reporting",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (15000, 40000),
            "timeline_months": (0.25, 0.75),
            "requires_tsa": False,
            "prerequisites": ["MIG-010", "MIG-011", "MIG-012"],
            "outputs": ["Monitoring dashboard", "Progress reports", "Issue tracking"],
        },
        # -----------------------------------------------------------------
        # VALIDATION & QUALITY
        # -----------------------------------------------------------------
        {
            "id": "MIG-030",
            "name": "Migration validation framework",
            "description": "Develop validation framework for data migrations",
            "activity_type": "implementation",
            "phase": "build",
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["MIG-002"],
            "outputs": ["Validation scripts", "Comparison tools", "Integrity checks"],
        },
        {
            "id": "MIG-031",
            "name": "Data quality remediation",
            "description": "Remediate data quality issues discovered during migration",
            "activity_type": "implementation",
            "phase": "migration",
            "base_cost": (25000, 75000),
            "timeline_months": (1, 3),
            "requires_tsa": False,
            "prerequisites": ["MIG-030"],
            "outputs": ["Clean data", "Quality reports", "Remediation documentation"],
        },
        {
            "id": "MIG-032",
            "name": "Post-migration validation",
            "description": "Execute comprehensive post-migration validation",
            "activity_type": "implementation",
            "phase": "testing",
            "base_cost": (20000, 50000),
            "timeline_months": (0.5, 1),
            "requires_tsa": False,
            "prerequisites": ["MIG-030"],
            "outputs": ["Validation results", "Completeness reports", "Sign-off"],
        },
    ],
}

# =============================================================================
# COMBINED TEMPLATES FOR PHASE 4
# =============================================================================

def get_phase4_templates() -> Dict[str, Dict[str, List[Dict]]]:
    """Get all Phase 4 templates organized by category and workstream."""
    return {
        "parent_dependency": {
            "database": DATABASE_TEMPLATES["parent_dependency"],
            "file_data": FILE_DATA_TEMPLATES["parent_dependency"],
            "archival": ARCHIVAL_TEMPLATES["parent_dependency"],
            "migration_tooling": MIGRATION_TOOLING_TEMPLATES["parent_dependency"],
        },
        "technical_debt": {
            "archival": ARCHIVAL_TEMPLATES.get("technical_debt", []),
        },
    }


def get_phase4_activity_by_id(activity_id: str) -> Dict:
    """Look up a Phase 4 activity by its ID."""
    all_templates = get_phase4_templates()

    for category, workstreams in all_templates.items():
        for workstream, activities in workstreams.items():
            for activity in activities:
                if activity.get("id") == activity_id:
                    return activity

    return None


def calculate_phase4_activity_cost(
    activity: Dict,
    user_count: int = 1000,
    database_count: int = 20,
    storage_tb: int = 50,
    site_count: int = 25,
    complexity: str = "moderate",
    industry: str = "standard",
) -> tuple:
    """
    Calculate cost range for a Phase 4 activity based on quantities and modifiers.

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

    if "per_database_cost" in activity:
        per_low, per_high = activity["per_database_cost"]
        low += per_low * database_count
        high += per_high * database_count
        formula_parts.append(f"{database_count} databases × ${per_low:,}-${per_high:,}")

    if "per_tb_cost" in activity:
        per_low, per_high = activity["per_tb_cost"]
        low += per_low * storage_tb
        high += per_high * storage_tb
        formula_parts.append(f"{storage_tb} TB × ${per_low:,}-${per_high:,}")

    if "per_site_cost" in activity:
        per_low, per_high = activity["per_site_cost"]
        low += per_low * site_count
        high += per_high * site_count
        formula_parts.append(f"{site_count} sites × ${per_low:,}-${per_high:,}")

    formula = " + ".join(formula_parts) if formula_parts else "Unknown cost model"

    # Apply modifiers
    if combined_mult != 1.0:
        low = int(low * combined_mult)
        high = int(high * combined_mult)
        formula += f" × {combined_mult:.2f} ({complexity}/{industry})"

    return (int(low), int(high), formula)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'DATABASE_TEMPLATES',
    'FILE_DATA_TEMPLATES',
    'ARCHIVAL_TEMPLATES',
    'MIGRATION_TOOLING_TEMPLATES',
    'get_phase4_templates',
    'get_phase4_activity_by_id',
    'calculate_phase4_activity_cost',
]
