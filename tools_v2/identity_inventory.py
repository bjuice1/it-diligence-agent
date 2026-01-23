"""
Identity & Access Inventory - Identity Domain Depth

Implements Points 56-70 of the Enhancement Plan:
- IAM architecture inventory
- Identity source mapping
- SSO and MFA coverage analysis
- Privileged access assessment
- Access governance evaluation
- Identity architecture complexity

This module provides structured tracking of identity and access posture.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Set
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class DirectoryType(Enum):
    """Types of directory services."""
    ACTIVE_DIRECTORY = "active_directory"
    AZURE_AD = "azure_ad"
    OKTA = "okta"
    PING = "ping_identity"
    GOOGLE = "google_workspace"
    LDAP = "ldap"
    LOCAL = "local"
    OTHER = "other"


class IdentitySourceRole(Enum):
    """Role of identity source in the architecture."""
    PRIMARY = "primary"              # Authoritative source
    SECONDARY = "secondary"          # Synced from primary
    LEGACY = "legacy"               # Legacy system, migrating off
    APPLICATION = "application"      # App-specific identity


class FederationType(Enum):
    """Types of federation."""
    SAML = "saml"
    OIDC = "oidc"
    WS_FED = "ws_federation"
    NONE = "none"


class MFAMethod(Enum):
    """MFA methods in use."""
    PUSH = "push_notification"
    TOTP = "totp_authenticator"
    SMS = "sms"
    HARDWARE_TOKEN = "hardware_token"
    FIDO2 = "fido2_webauthn"
    PHONE_CALL = "phone_call"
    EMAIL = "email_otp"


class AccountType(Enum):
    """Types of accounts."""
    STANDARD_USER = "standard_user"
    ADMIN = "admin"
    SERVICE_ACCOUNT = "service_account"
    SHARED_ACCOUNT = "shared_account"
    BREAK_GLASS = "break_glass"
    VENDOR = "vendor"


class IdentityComplexity(Enum):
    """Identity architecture complexity level."""
    SIMPLE = "simple"            # Single directory, minimal federation
    MODERATE = "moderate"        # Hybrid with one cloud IdP
    COMPLEX = "complex"          # Multiple forests/tenants, complex federation
    VERY_COMPLEX = "very_complex"  # Multi-org, cross-trust, legacy entanglement


class AccessReviewMaturity(Enum):
    """Maturity of access review processes."""
    MATURE = "mature"            # Automated, regular, high remediation
    DEVELOPING = "developing"    # Some automation, periodic reviews
    BASIC = "basic"              # Manual, ad-hoc reviews
    NONE = "none"                # No formal reviews


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class DirectoryService:
    """A directory service in the identity architecture."""
    directory_id: str
    name: str
    directory_type: DirectoryType
    role: IdentitySourceRole

    # For AD
    forest_name: Optional[str] = None
    domain_count: int = 1
    functional_level: Optional[str] = None

    # For Azure AD / Cloud IdP
    tenant_id: Optional[str] = None
    tenant_name: Optional[str] = None

    # User counts
    total_users: int = 0
    active_users: int = 0
    disabled_users: int = 0

    # Synced/federated
    synced_from: Optional[str] = None  # Directory ID of source
    sync_method: str = ""  # Azure AD Connect, Google Cloud Directory Sync, etc.

    # Shared with parent/third party
    shared_with_parent: bool = False
    requires_separation: bool = False

    notes: str = ""

    def to_dict(self) -> Dict:
        return {
            "directory_id": self.directory_id,
            "name": self.name,
            "type": self.directory_type.value,
            "role": self.role.value,
            "forest_name": self.forest_name,
            "domain_count": self.domain_count,
            "tenant_id": self.tenant_id,
            "users": {
                "total": self.total_users,
                "active": self.active_users,
                "disabled": self.disabled_users
            },
            "sync": {
                "synced_from": self.synced_from,
                "method": self.sync_method
            },
            "shared_with_parent": self.shared_with_parent,
            "requires_separation": self.requires_separation
        }


@dataclass
class FederationConfig:
    """Federation configuration between identity providers."""
    federation_id: str
    source_directory: str  # Directory ID
    target_directory: str  # Directory ID or app name
    federation_type: FederationType
    is_bidirectional: bool = False
    protocol_version: str = ""
    notes: str = ""

    def to_dict(self) -> Dict:
        return {
            "federation_id": self.federation_id,
            "source": self.source_directory,
            "target": self.target_directory,
            "type": self.federation_type.value,
            "bidirectional": self.is_bidirectional
        }


@dataclass
class ApplicationSSO:
    """SSO configuration for an application."""
    app_name: str
    sso_enabled: bool
    sso_type: FederationType = FederationType.NONE
    identity_provider: str = ""
    criticality: str = "medium"  # critical, high, medium, low

    # Coverage
    user_count: int = 0
    percent_using_sso: float = 0.0

    # Local auth fallback
    has_local_auth: bool = False
    local_auth_reason: str = ""

    def to_dict(self) -> Dict:
        return {
            "app_name": self.app_name,
            "sso_enabled": self.sso_enabled,
            "sso_type": self.sso_type.value,
            "identity_provider": self.identity_provider,
            "criticality": self.criticality,
            "coverage": {
                "users": self.user_count,
                "percent_sso": self.percent_using_sso
            },
            "local_auth": {
                "enabled": self.has_local_auth,
                "reason": self.local_auth_reason
            }
        }


@dataclass
class MFACoverage:
    """MFA coverage assessment."""
    total_users: int = 0
    mfa_enabled_users: int = 0
    mfa_enforced_users: int = 0
    methods_in_use: List[MFAMethod] = field(default_factory=list)

    # By category
    admin_mfa_percent: float = 0.0
    standard_user_mfa_percent: float = 0.0
    remote_access_mfa_percent: float = 0.0

    # Gaps
    mfa_exceptions: int = 0
    exception_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "total_users": self.total_users,
            "mfa_enabled": self.mfa_enabled_users,
            "mfa_enforced": self.mfa_enforced_users,
            "overall_percent": (self.mfa_enabled_users / self.total_users * 100) if self.total_users > 0 else 0,
            "methods": [m.value for m in self.methods_in_use],
            "coverage": {
                "admin": self.admin_mfa_percent,
                "standard_user": self.standard_user_mfa_percent,
                "remote_access": self.remote_access_mfa_percent
            },
            "exceptions": {
                "count": self.mfa_exceptions,
                "reasons": self.exception_reasons
            }
        }


@dataclass
class PrivilegedAccount:
    """A privileged or service account."""
    account_id: str
    account_name: str
    account_type: AccountType
    directory: str  # Directory ID
    description: str = ""

    # Privileges
    is_domain_admin: bool = False
    is_local_admin: bool = False
    privilege_scope: str = ""  # global, domain, application-specific

    # Management
    managed_by_pam: bool = False
    pam_solution: str = ""
    password_rotated: bool = False
    last_rotation_date: Optional[date] = None

    # Risk indicators
    is_shared: bool = False
    has_mfa: bool = False
    last_used: Optional[date] = None
    owner: str = ""

    def to_dict(self) -> Dict:
        return {
            "account_id": self.account_id,
            "account_name": self.account_name,
            "type": self.account_type.value,
            "directory": self.directory,
            "privileges": {
                "domain_admin": self.is_domain_admin,
                "local_admin": self.is_local_admin,
                "scope": self.privilege_scope
            },
            "pam": {
                "managed": self.managed_by_pam,
                "solution": self.pam_solution,
                "rotated": self.password_rotated
            },
            "risk": {
                "shared": self.is_shared,
                "has_mfa": self.has_mfa,
                "owner": self.owner
            }
        }


@dataclass
class AccessReviewProcess:
    """Access review and certification process."""
    review_type: str  # user_access, privileged, application
    frequency: str  # monthly, quarterly, annually, ad-hoc
    scope: str  # Description of what's reviewed
    automation_level: str  # fully_automated, semi_automated, manual
    remediation_rate: float = 0.0  # % of flagged items remediated
    last_review_date: Optional[date] = None
    tool_used: str = ""

    def to_dict(self) -> Dict:
        return {
            "type": self.review_type,
            "frequency": self.frequency,
            "scope": self.scope,
            "automation": self.automation_level,
            "remediation_rate": self.remediation_rate,
            "last_review": str(self.last_review_date) if self.last_review_date else None,
            "tool": self.tool_used
        }


@dataclass
class IdentityLifecycle:
    """Identity lifecycle process assessment."""
    has_joiner_process: bool = False
    joiner_automation: str = ""  # hr_driven, manual, ticketing
    avg_provisioning_days: float = 0.0

    has_mover_process: bool = False
    mover_automation: str = ""
    role_change_handled: bool = False

    has_leaver_process: bool = False
    leaver_automation: str = ""
    avg_deprovision_days: float = 0.0
    last_access_review: Optional[date] = None

    # Orphaned accounts
    orphaned_account_count: int = 0
    orphaned_percent: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "joiner": {
                "exists": self.has_joiner_process,
                "automation": self.joiner_automation,
                "avg_days": self.avg_provisioning_days
            },
            "mover": {
                "exists": self.has_mover_process,
                "automation": self.mover_automation,
                "role_change": self.role_change_handled
            },
            "leaver": {
                "exists": self.has_leaver_process,
                "automation": self.leaver_automation,
                "avg_days": self.avg_deprovision_days
            },
            "orphaned": {
                "count": self.orphaned_account_count,
                "percent": self.orphaned_percent
            }
        }


# =============================================================================
# IDENTITY INVENTORY
# =============================================================================

class IdentityInventory:
    """
    Central inventory for identity and access management.

    Implements Points 56-70: Identity & Access Domain Depth.
    """

    def __init__(self):
        self.directories: List[DirectoryService] = []
        self.federations: List[FederationConfig] = []
        self.application_sso: List[ApplicationSSO] = []
        self.mfa_coverage: Optional[MFACoverage] = None
        self.privileged_accounts: List[PrivilegedAccount] = []
        self.access_reviews: List[AccessReviewProcess] = []
        self.lifecycle: Optional[IdentityLifecycle] = None
        self.created_at = datetime.now().isoformat()

    def add_directory(self, directory: DirectoryService):
        """Add a directory service."""
        self.directories.append(directory)

    def add_federation(self, federation: FederationConfig):
        """Add a federation configuration."""
        self.federations.append(federation)

    def add_application_sso(self, app: ApplicationSSO):
        """Add application SSO configuration."""
        self.application_sso.append(app)

    def add_privileged_account(self, account: PrivilegedAccount):
        """Add a privileged account."""
        self.privileged_accounts.append(account)

    def add_access_review(self, review: AccessReviewProcess):
        """Add an access review process."""
        self.access_reviews.append(review)

    # -------------------------------------------------------------------------
    # Point 56-57: IAM Architecture & Identity Source Mapping
    # -------------------------------------------------------------------------

    def get_iam_architecture(self) -> Dict[str, Any]:
        """
        Get IAM architecture inventory.

        Implements Point 56: IAM architecture inventory.
        """
        by_type = {}
        for d in self.directories:
            dtype = d.directory_type.value
            if dtype not in by_type:
                by_type[dtype] = []
            by_type[dtype].append(d.to_dict())

        # Count totals
        total_users = sum(d.total_users for d in self.directories)
        ad_forests = len([d for d in self.directories if d.directory_type == DirectoryType.ACTIVE_DIRECTORY])
        azure_tenants = len([d for d in self.directories if d.directory_type == DirectoryType.AZURE_AD])

        return {
            "total_directories": len(self.directories),
            "by_type": by_type,
            "summary": {
                "total_users": total_users,
                "ad_forests": ad_forests,
                "azure_tenants": azure_tenants,
                "federated_apps": len(self.application_sso)
            },
            "directories": [d.to_dict() for d in self.directories]
        }

    def get_identity_source_map(self) -> Dict[str, Any]:
        """
        Map identity sources and their relationships.

        Implements Point 57: Identity source mapping.
        """
        sources = {"primary": [], "secondary": [], "legacy": [], "application": []}

        for d in self.directories:
            role = d.role.value
            if role in sources:
                sources[role].append({
                    "id": d.directory_id,
                    "name": d.name,
                    "type": d.directory_type.value,
                    "users": d.total_users
                })

        # Build dependency graph
        sync_relationships = []
        for d in self.directories:
            if d.synced_from:
                sync_relationships.append({
                    "source": d.synced_from,
                    "target": d.directory_id,
                    "method": d.sync_method
                })

        return {
            "sources_by_role": sources,
            "primary_source": sources["primary"][0] if sources["primary"] else None,
            "sync_relationships": sync_relationships,
            "federations": [f.to_dict() for f in self.federations],
            "shared_with_parent": [d.to_dict() for d in self.directories if d.shared_with_parent]
        }

    # -------------------------------------------------------------------------
    # Point 58-60: SSO, MFA, and Lifecycle
    # -------------------------------------------------------------------------

    def get_sso_analysis(self) -> Dict[str, Any]:
        """
        Analyze SSO coverage.

        Implements Point 58: SSO coverage analysis.
        """
        total_apps = len(self.application_sso)
        sso_enabled = len([a for a in self.application_sso if a.sso_enabled])

        critical_apps = [a for a in self.application_sso if a.criticality == "critical"]
        critical_with_sso = len([a for a in critical_apps if a.sso_enabled])

        local_auth_apps = [a for a in self.application_sso if a.has_local_auth]

        return {
            "total_applications": total_apps,
            "sso_enabled_count": sso_enabled,
            "sso_percent": (sso_enabled / total_apps * 100) if total_apps > 0 else 0,
            "critical_coverage": {
                "total": len(critical_apps),
                "with_sso": critical_with_sso,
                "percent": (critical_with_sso / len(critical_apps) * 100) if critical_apps else 0
            },
            "local_auth_fallbacks": {
                "count": len(local_auth_apps),
                "apps": [a.app_name for a in local_auth_apps]
            },
            "by_idp": self._group_apps_by_idp(),
            "applications": [a.to_dict() for a in self.application_sso]
        }

    def _group_apps_by_idp(self) -> Dict[str, int]:
        """Group applications by identity provider."""
        by_idp = {}
        for app in self.application_sso:
            if app.sso_enabled:
                idp = app.identity_provider or "unknown"
                by_idp[idp] = by_idp.get(idp, 0) + 1
        return by_idp

    def get_mfa_assessment(self) -> Dict[str, Any]:
        """
        Assess MFA coverage.

        Implements Point 59: MFA coverage assessment.
        """
        if not self.mfa_coverage:
            return {"status": "unknown", "message": "No MFA data available"}

        mfa = self.mfa_coverage
        overall_percent = (mfa.mfa_enabled_users / mfa.total_users * 100) if mfa.total_users > 0 else 0

        # Assess gaps
        gaps = []
        if mfa.admin_mfa_percent < 100:
            gaps.append(f"Admin MFA only {mfa.admin_mfa_percent}% - should be 100%")
        if mfa.remote_access_mfa_percent < 100:
            gaps.append(f"Remote access MFA only {mfa.remote_access_mfa_percent}% - critical gap")
        if overall_percent < 80:
            gaps.append(f"Overall MFA adoption at {overall_percent:.1f}% - below recommended 80%")

        return {
            "coverage": mfa.to_dict(),
            "overall_percent": overall_percent,
            "gaps": gaps,
            "recommendations": self._get_mfa_recommendations(mfa)
        }

    def _get_mfa_recommendations(self, mfa: MFACoverage) -> List[str]:
        """Generate MFA recommendations."""
        recs = []

        if mfa.admin_mfa_percent < 100:
            recs.append("Enforce MFA for all administrator accounts immediately")

        if MFAMethod.SMS in mfa.methods_in_use:
            recs.append("Consider phasing out SMS-based MFA in favor of more secure methods")

        if not any(m in mfa.methods_in_use for m in [MFAMethod.FIDO2, MFAMethod.HARDWARE_TOKEN]):
            recs.append("Consider implementing phishing-resistant MFA (FIDO2/hardware tokens)")

        if mfa.mfa_exceptions > 0:
            recs.append(f"Address {mfa.mfa_exceptions} MFA exceptions")

        return recs

    def get_lifecycle_assessment(self) -> Dict[str, Any]:
        """
        Assess identity lifecycle processes.

        Implements Point 60: Identity lifecycle assessment.
        """
        if not self.lifecycle:
            return {"status": "unknown", "message": "No lifecycle data available"}

        lc = self.lifecycle

        # Calculate maturity
        maturity_score = 0
        if lc.has_joiner_process:
            maturity_score += 1
            if lc.joiner_automation == "hr_driven":
                maturity_score += 1
        if lc.has_mover_process:
            maturity_score += 1
        if lc.has_leaver_process:
            maturity_score += 1
            if lc.avg_deprovision_days <= 1:
                maturity_score += 1

        if maturity_score >= 4:
            maturity = "mature"
        elif maturity_score >= 2:
            maturity = "developing"
        else:
            maturity = "basic"

        # Identify risks
        risks = []
        if lc.avg_deprovision_days > 3:
            risks.append(f"Slow deprovisioning ({lc.avg_deprovision_days} days) creates security risk")
        if lc.orphaned_percent > 5:
            risks.append(f"High orphaned account rate ({lc.orphaned_percent}%)")
        if not lc.role_change_handled:
            risks.append("Role changes not systematically handled - privilege accumulation risk")

        return {
            "maturity": maturity,
            "lifecycle": lc.to_dict(),
            "risks": risks,
            "recommendations": self._get_lifecycle_recommendations(lc)
        }

    def _get_lifecycle_recommendations(self, lc: IdentityLifecycle) -> List[str]:
        """Generate lifecycle recommendations."""
        recs = []

        if not lc.has_joiner_process or lc.joiner_automation == "manual":
            recs.append("Implement HR-driven automated provisioning")

        if lc.avg_deprovision_days > 1:
            recs.append("Reduce deprovisioning time to same-day")

        if lc.orphaned_account_count > 0:
            recs.append(f"Remediate {lc.orphaned_account_count} orphaned accounts")

        return recs

    # -------------------------------------------------------------------------
    # Point 61-64: Privileged Access
    # -------------------------------------------------------------------------

    def get_privileged_account_inventory(self) -> Dict[str, Any]:
        """
        Get privileged account inventory.

        Implements Point 61: Privileged account inventory.
        """
        by_type = {}
        for acct in self.privileged_accounts:
            atype = acct.account_type.value
            if atype not in by_type:
                by_type[atype] = []
            by_type[atype].append(acct.to_dict())

        # Risk indicators
        shared_accounts = [a for a in self.privileged_accounts if a.is_shared]
        unmanaged = [a for a in self.privileged_accounts if not a.managed_by_pam]
        no_mfa = [a for a in self.privileged_accounts if not a.has_mfa and a.account_type == AccountType.ADMIN]

        return {
            "total_privileged": len(self.privileged_accounts),
            "by_type": by_type,
            "risk_indicators": {
                "shared_accounts": len(shared_accounts),
                "not_managed_by_pam": len(unmanaged),
                "admins_without_mfa": len(no_mfa)
            },
            "accounts": [a.to_dict() for a in self.privileged_accounts]
        }

    def get_pam_assessment(self) -> Dict[str, Any]:
        """
        Assess PAM tooling maturity.

        Implements Point 62: PAM tooling assessment.
        """
        managed = [a for a in self.privileged_accounts if a.managed_by_pam]
        total = len(self.privileged_accounts)

        # Get PAM solutions in use
        pam_solutions = set(a.pam_solution for a in managed if a.pam_solution)

        coverage_percent = (len(managed) / total * 100) if total > 0 else 0

        # Assess maturity
        if coverage_percent >= 90 and len(pam_solutions) > 0:
            maturity = "mature"
        elif coverage_percent >= 50:
            maturity = "developing"
        elif len(pam_solutions) > 0:
            maturity = "basic"
        else:
            maturity = "none"

        return {
            "pam_solutions": list(pam_solutions),
            "coverage": {
                "managed_count": len(managed),
                "total_privileged": total,
                "percent": coverage_percent
            },
            "maturity": maturity,
            "recommendations": self._get_pam_recommendations(coverage_percent, maturity)
        }

    def _get_pam_recommendations(self, coverage: float, maturity: str) -> List[str]:
        """Generate PAM recommendations."""
        recs = []

        if maturity == "none":
            recs.append("Implement PAM solution for privileged account management")
        elif coverage < 80:
            recs.append(f"Increase PAM coverage from {coverage:.1f}% to >80%")

        unrotated = [a for a in self.privileged_accounts if not a.password_rotated]
        if unrotated:
            recs.append(f"Enable password rotation for {len(unrotated)} accounts")

        return recs

    def get_admin_access_findings(self) -> Dict[str, Any]:
        """
        Get admin access review findings.

        Implements Point 63: Admin access review findings.
        """
        issues = []

        # Check for excessive permissions
        domain_admins = [a for a in self.privileged_accounts if a.is_domain_admin]
        if len(domain_admins) > 10:
            issues.append({
                "type": "excessive_domain_admins",
                "count": len(domain_admins),
                "recommendation": "Reduce domain admin count - only essential admins should have this role"
            })

        # Check for orphaned accounts
        no_owner = [a for a in self.privileged_accounts if not a.owner]
        if no_owner:
            issues.append({
                "type": "unowned_privileged_accounts",
                "count": len(no_owner),
                "recommendation": "Assign owners to all privileged accounts"
            })

        # Check for shared accounts
        shared = [a for a in self.privileged_accounts if a.is_shared]
        if shared:
            issues.append({
                "type": "shared_privileged_accounts",
                "count": len(shared),
                "accounts": [a.account_name for a in shared],
                "recommendation": "Eliminate shared privileged accounts - use individual accounts with PAM"
            })

        return {
            "total_issues": len(issues),
            "issues": issues,
            "privileged_account_count": len(self.privileged_accounts)
        }

    def get_break_glass_assessment(self) -> Dict[str, Any]:
        """
        Assess break-glass procedures.

        Implements Point 64: Break-glass procedure assessment.
        """
        break_glass = [a for a in self.privileged_accounts if a.account_type == AccountType.BREAK_GLASS]

        exists = len(break_glass) > 0
        properly_managed = all(a.managed_by_pam for a in break_glass) if break_glass else False

        return {
            "has_break_glass": exists,
            "account_count": len(break_glass),
            "properly_managed": properly_managed,
            "recommendations": [] if (exists and properly_managed) else [
                "Establish formal break-glass procedure with documented accounts",
                "Store break-glass credentials securely (PAM or sealed envelope)"
            ]
        }

    # -------------------------------------------------------------------------
    # Point 65-68: Access Governance
    # -------------------------------------------------------------------------

    def get_access_review_practices(self) -> Dict[str, Any]:
        """
        Extract access review practices.

        Implements Point 65: Access review practices.
        """
        if not self.access_reviews:
            return {
                "status": "none",
                "message": "No formal access review process documented",
                "maturity": AccessReviewMaturity.NONE.value
            }

        # Assess maturity
        has_regular = any(r.frequency in ["monthly", "quarterly"] for r in self.access_reviews)
        has_automation = any(r.automation_level in ["fully_automated", "semi_automated"] for r in self.access_reviews)
        avg_remediation = sum(r.remediation_rate for r in self.access_reviews) / len(self.access_reviews)

        if has_regular and has_automation and avg_remediation > 80:
            maturity = AccessReviewMaturity.MATURE
        elif has_regular or has_automation:
            maturity = AccessReviewMaturity.DEVELOPING
        else:
            maturity = AccessReviewMaturity.BASIC

        return {
            "maturity": maturity.value,
            "review_count": len(self.access_reviews),
            "average_remediation_rate": avg_remediation,
            "reviews": [r.to_dict() for r in self.access_reviews],
            "gaps": self._identify_review_gaps()
        }

    def _identify_review_gaps(self) -> List[str]:
        """Identify gaps in access review coverage."""
        gaps = []
        review_types = [r.review_type for r in self.access_reviews]

        if "privileged" not in review_types:
            gaps.append("No privileged access review process")
        if "user_access" not in review_types:
            gaps.append("No regular user access review")
        if "application" not in review_types:
            gaps.append("No application access review")

        return gaps

    def get_rbac_assessment(self) -> Dict[str, Any]:
        """
        Assess RBAC/ABAC maturity.

        Implements Point 66: RBAC/ABAC assessment.
        """
        # This would typically analyze role structures from facts
        # For now, provide structure for assessment

        return {
            "has_rbac": True,  # Would be determined from facts
            "role_count": 0,   # Would be extracted
            "avg_roles_per_user": 0,
            "role_creep_indicators": [],
            "recommendations": [
                "Conduct role rationalization exercise",
                "Implement role mining to identify common access patterns"
            ]
        }

    # -------------------------------------------------------------------------
    # Point 69-70: Architecture Complexity
    # -------------------------------------------------------------------------

    def get_architecture_complexity(self) -> Dict[str, Any]:
        """
        Assess identity architecture complexity.

        Implements Point 69: Identity architecture complexity.
        """
        # Count complexity factors
        factors = {
            "ad_forests": len([d for d in self.directories if d.directory_type == DirectoryType.ACTIVE_DIRECTORY]),
            "azure_tenants": len([d for d in self.directories if d.directory_type == DirectoryType.AZURE_AD]),
            "cloud_idps": len([d for d in self.directories if d.directory_type in [DirectoryType.OKTA, DirectoryType.PING]]),
            "federations": len(self.federations),
            "legacy_directories": len([d for d in self.directories if d.role == IdentitySourceRole.LEGACY])
        }

        # Calculate complexity score
        score = 0
        score += factors["ad_forests"] * 10
        score += factors["azure_tenants"] * 8
        score += factors["cloud_idps"] * 5
        score += factors["federations"] * 3
        score += factors["legacy_directories"] * 15

        # Determine level
        if score >= 50:
            level = IdentityComplexity.VERY_COMPLEX
        elif score >= 30:
            level = IdentityComplexity.COMPLEX
        elif score >= 15:
            level = IdentityComplexity.MODERATE
        else:
            level = IdentityComplexity.SIMPLE

        return {
            "complexity_level": level.value,
            "complexity_score": score,
            "factors": factors,
            "integration_considerations": self._get_integration_considerations(factors, level)
        }

    def _get_integration_considerations(
        self,
        factors: Dict[str, int],
        level: IdentityComplexity
    ) -> List[str]:
        """Get identity integration considerations."""
        considerations = []

        if factors["ad_forests"] > 1:
            considerations.append("Multiple AD forests may require trust consolidation or migration")

        if factors["azure_tenants"] > 1:
            considerations.append("Multiple Azure AD tenants add integration complexity")

        if factors["legacy_directories"] > 0:
            considerations.append("Legacy directories should be prioritized for migration")

        if level in [IdentityComplexity.COMPLEX, IdentityComplexity.VERY_COMPLEX]:
            considerations.append("Complex identity architecture - consider phased integration approach")

        return considerations

    def get_shared_dependencies(self) -> Dict[str, Any]:
        """
        Identify shared identity dependencies.

        Implements Point 70: Identity shared dependencies.
        """
        shared = [d for d in self.directories if d.shared_with_parent]
        requires_separation = [d for d in self.directories if d.requires_separation]

        cross_org_federations = [
            f for f in self.federations
            if "parent" in f.source_directory.lower() or "parent" in f.target_directory.lower()
        ]

        return {
            "shared_directories": len(shared),
            "requires_separation": len(requires_separation),
            "cross_org_federations": len(cross_org_federations),
            "entanglement_level": "high" if shared else "low",
            "shared_details": [d.to_dict() for d in shared],
            "separation_requirements": [d.to_dict() for d in requires_separation],
            "integration_risks": self._get_identity_integration_risks(shared, requires_separation)
        }

    def _get_identity_integration_risks(
        self,
        shared: List[DirectoryService],
        requires_sep: List[DirectoryService]
    ) -> List[str]:
        """Get identity-related integration risks."""
        risks = []

        if shared:
            risks.append("Shared identity infrastructure requires careful separation planning")

        if requires_sep:
            total_users = sum(d.total_users for d in requires_sep)
            risks.append(f"Identity separation needed for {total_users} users")

        return risks

    # -------------------------------------------------------------------------
    # Complete Assessment
    # -------------------------------------------------------------------------

    def get_complete_assessment(self) -> Dict[str, Any]:
        """Get complete identity assessment."""
        return {
            "metadata": {
                "created_at": self.created_at,
                "assessment_date": datetime.now().isoformat()
            },
            "architecture": self.get_iam_architecture(),
            "identity_sources": self.get_identity_source_map(),
            "sso_coverage": self.get_sso_analysis(),
            "mfa_assessment": self.get_mfa_assessment(),
            "lifecycle": self.get_lifecycle_assessment(),
            "privileged_access": self.get_privileged_account_inventory(),
            "pam_maturity": self.get_pam_assessment(),
            "admin_findings": self.get_admin_access_findings(),
            "break_glass": self.get_break_glass_assessment(),
            "access_reviews": self.get_access_review_practices(),
            "complexity": self.get_architecture_complexity(),
            "shared_dependencies": self.get_shared_dependencies()
        }


# =============================================================================
# MODULE TEST
# =============================================================================

if __name__ == "__main__":
    print("=== Identity Inventory Module Test ===\n")

    inventory = IdentityInventory()

    # Add directories
    inventory.add_directory(DirectoryService(
        directory_id="DIR-001",
        name="Corporate AD",
        directory_type=DirectoryType.ACTIVE_DIRECTORY,
        role=IdentitySourceRole.PRIMARY,
        forest_name="corp.acme.com",
        domain_count=3,
        total_users=5000,
        active_users=4500
    ))

    inventory.add_directory(DirectoryService(
        directory_id="DIR-002",
        name="Acme Azure AD",
        directory_type=DirectoryType.AZURE_AD,
        role=IdentitySourceRole.SECONDARY,
        tenant_name="acme.onmicrosoft.com",
        total_users=5000,
        synced_from="DIR-001",
        sync_method="Azure AD Connect"
    ))

    # Add federation
    inventory.add_federation(FederationConfig(
        federation_id="FED-001",
        source_directory="DIR-002",
        target_directory="Salesforce",
        federation_type=FederationType.SAML
    ))

    # Add applications
    inventory.add_application_sso(ApplicationSSO(
        app_name="Salesforce",
        sso_enabled=True,
        sso_type=FederationType.SAML,
        identity_provider="Azure AD",
        criticality="critical",
        user_count=500
    ))

    inventory.add_application_sso(ApplicationSSO(
        app_name="Legacy ERP",
        sso_enabled=False,
        criticality="critical",
        has_local_auth=True,
        local_auth_reason="Legacy system - SSO not supported"
    ))

    # Add MFA coverage
    inventory.mfa_coverage = MFACoverage(
        total_users=5000,
        mfa_enabled_users=4500,
        mfa_enforced_users=4000,
        methods_in_use=[MFAMethod.PUSH, MFAMethod.TOTP],
        admin_mfa_percent=100.0,
        standard_user_mfa_percent=90.0,
        remote_access_mfa_percent=100.0
    )

    # Add privileged accounts
    inventory.add_privileged_account(PrivilegedAccount(
        account_id="PA-001",
        account_name="domain_admin",
        account_type=AccountType.ADMIN,
        directory="DIR-001",
        is_domain_admin=True,
        managed_by_pam=True,
        pam_solution="CyberArk",
        has_mfa=True,
        owner="IT Director"
    ))

    # Add lifecycle
    inventory.lifecycle = IdentityLifecycle(
        has_joiner_process=True,
        joiner_automation="hr_driven",
        avg_provisioning_days=1.5,
        has_leaver_process=True,
        leaver_automation="hr_driven",
        avg_deprovision_days=1.0
    )

    # Print results
    print("1. IAM Architecture")
    arch = inventory.get_iam_architecture()
    print(f"   Total directories: {arch['total_directories']}")
    print(f"   Total users: {arch['summary']['total_users']}")
    print()

    print("2. SSO Coverage")
    sso = inventory.get_sso_analysis()
    print(f"   Total apps: {sso['total_applications']}")
    print(f"   SSO enabled: {sso['sso_percent']:.0f}%")
    print()

    print("3. MFA Assessment")
    mfa = inventory.get_mfa_assessment()
    print(f"   Overall: {mfa['overall_percent']:.0f}%")
    print(f"   Gaps: {mfa['gaps']}")
    print()

    print("4. Architecture Complexity")
    complexity = inventory.get_architecture_complexity()
    print(f"   Level: {complexity['complexity_level']}")
    print(f"   Score: {complexity['complexity_score']}")
    print()

    print("=== Identity Inventory Module Test Complete ===")
