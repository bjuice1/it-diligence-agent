# Identity & Access Management Review Playlist

## Pre-Flight Considerations

**What makes Identity & Access different from other IT domains:**

1. **IAM is the glue for integration** - Day 1 access provisioning, SSO federation, identity consolidation - these are the mechanics that enable (or block) integration. IAM maturity determines integration speed.

2. **MFA is the single most important security control** - If you only ask one security question, ask about MFA. Coverage percentage for all users, and especially for privileged accounts, is predictive of overall security posture.

3. **Privileged access is high-value target** - Admin accounts, service accounts, root/domain admin - these are what attackers want. How they're managed is critical.

4. **Orphaned accounts are liability** - Departed employees, contractors, service accounts for decommissioned systems - these accumulate and create risk. Access reviews and lifecycle management matter.

5. **Cloud IAM is a different beast** - AWS IAM, Azure AD roles, GCP IAM - each cloud has its own identity model. Companies often have poor hygiene in cloud identity even with good on-prem AD practices.

6. **Integration creates new attack surface** - Trust relationships, federated SSO, cross-domain access - these are exactly what attackers exploit during M&A transitions. Plan carefully.

**What we learned building the bespoke tool:**

- "We have MFA" is not enough. Ask: "What percentage of users have MFA enforced? What about privileged users? What about service accounts?"
- Active Directory health is foundational. A messy AD (stale accounts, flat structure, no groups) makes everything harder.
- Privileged Access Management (PAM) adoption separates mature orgs from immature ones. No PAM = significant risk.
- Access reviews either happen consistently or don't happen at all. Ask for evidence of the last review.

---

## Phase 1: Identity Infrastructure

### Prompt 1.1 - Identity Provider Inventory
```
Document all identity providers and directories:

1. Primary identity directory:
   - On-premises Active Directory? (Yes/No)
     - Number of domains and forests
     - Forest/domain functional level
     - Domain controllers (count, locations)
     - AD health indicators (if mentioned)
   - Azure AD / Entra ID? (Yes/No)
     - Tenant configuration (single, multiple)
     - Azure AD Connect or cloud-only?
     - Hybrid identity model?
   - Other directory (LDAP, OpenLDAP, other)

2. Identity providers for SSO:
   - Azure AD / Entra ID
   - Okta
   - Ping Identity
   - OneLogin
   - Google Workspace
   - Other

3. Identity scope:
   - Total user accounts (employees)
   - External identities (contractors, partners, customers)
   - Service accounts
   - Machine identities

Create inventory: Identity System | Type | User Count | Purpose | Notes
```

### Prompt 1.2 - Identity Lifecycle Management
```
Assess identity lifecycle management:

1. Provisioning:
   - How are accounts created? (Manual, automated from HR, IGA tool)
   - Provisioning tool (if any - SailPoint, Saviynt, Azure AD, Okta)
   - Time to provision new employee (days)
   - Who approves access?

2. De-provisioning:
   - How are accounts disabled/removed? (Manual, automated)
   - Time to de-provision departed employee
   - Integration with HR system?
   - Immediate termination process?

3. Access certification:
   - Regular access reviews conducted? (Yes/No)
   - Frequency (quarterly, annually, ad-hoc)
   - Scope (all users, privileged only)
   - Tool used for reviews
   - Last review date

4. Account hygiene:
   - Stale account cleanup process
   - Orphaned accounts known?
   - Service account inventory maintained?

Gaps to flag:
- Manual provisioning/de-provisioning
- No access reviews
- De-provisioning takes >24 hours
- Unknown number of service accounts
```

---

## Phase 2: Authentication

### Prompt 2.1 - Multi-Factor Authentication
```
**CRITICAL ASSESSMENT AREA**

Assess MFA implementation:

1. MFA solution:
   - Primary MFA provider (Microsoft Authenticator, Duo, Okta Verify, RSA, YubiKey, other)
   - MFA methods enabled (Push, TOTP, SMS, hardware token, biometric)

2. MFA coverage - get specific percentages:
   - All users MFA enforced: X%
   - Privileged users MFA enforced: X%
   - Remote access MFA enforced: X%
   - Cloud admin MFA enforced: X%
   - Service accounts with MFA (where applicable)

3. MFA scope:
   - Windows login
   - VPN access
   - Cloud applications (O365, SaaS)
   - On-premises applications
   - Privileged access (admin consoles)

4. MFA gaps:
   - Legacy applications without MFA
   - Exceptions granted
   - Resistance or adoption challenges

Risk rating:
- MFA enforced for all users: Low risk
- MFA enforced for privileged only: Medium risk
- MFA available but not enforced: High risk
- No MFA: Critical risk
```

### Prompt 2.2 - Password and Authentication Policies
```
Document authentication policies:

1. Password policy:
   - Minimum length
   - Complexity requirements
   - Rotation period (or no rotation per NIST guidance)
   - Password history
   - Lockout policy

2. Authentication methods beyond MFA:
   - Passwordless authentication in use?
   - Windows Hello for Business
   - FIDO2 security keys
   - Certificate-based authentication

3. Single Sign-On (SSO):
   - SSO implemented? (Yes/No)
   - SSO provider
   - Applications integrated with SSO (count, key apps)
   - Applications NOT integrated (gap)

4. Legacy authentication:
   - NTLM still in use?
   - Basic authentication enabled?
   - Legacy protocols (SMBv1, etc.)

Gaps to flag:
- Password rotation <90 days (outdated practice)
- No SSO for major applications
- Legacy authentication still enabled
```

---

## Phase 3: Authorization and Access Control

### Prompt 3.1 - Access Control Model
```
Assess access control implementation:

1. Access control model:
   - Role-Based Access Control (RBAC)?
   - Attribute-Based Access Control (ABAC)?
   - Group-based (AD groups)?
   - Individual permissions?

2. Role management:
   - Roles defined for key systems? (ERP, CRM, etc.)
   - Role documentation
   - Role proliferation concerns (too many roles)
   - Segregation of duties enforced?

3. Privileged access:
   - How many domain admins?
   - How many local admins?
   - Cloud admin accounts count
   - Privileged access inventory maintained?

4. Access request process:
   - How do users request access?
   - Approval workflow
   - Logging/auditability
   - Self-service capabilities

Gaps to flag:
- Everyone is admin
- No role structure
- No approval process for access
- Unknown privileged account count
```

### Prompt 3.2 - Privileged Access Management
```
**CRITICAL ASSESSMENT AREA**

Assess privileged access management:

1. PAM solution:
   - PAM tool in use? (CyberArk, BeyondTrust, Delinea, HashiCorp Vault, AWS Secrets Manager, other)
   - Scope of PAM deployment

2. Privileged account controls:
   - Privileged accounts inventoried?
   - Credentials vaulted?
   - Password rotation (automated or manual)
   - Session recording?
   - Just-in-time access?

3. Service accounts:
   - Service account inventory
   - Service account owners assigned?
   - Service account password management
   - Shared service accounts?

4. Privileged access monitoring:
   - Privileged session monitoring
   - Alerts on privileged activity
   - Privileged access analytics

5. Break-glass procedures:
   - Emergency access process
   - Break-glass accounts
   - Audit trail for emergency access

Risk rating:
- Full PAM deployment: Low risk
- Partial PAM (vaulting only): Medium risk
- No PAM but good processes: Medium-High risk
- No PAM and poor practices: Critical risk
```

---

## Phase 4: Cloud Identity

### Prompt 4.1 - Cloud IAM Assessment
```
Assess cloud identity and access management:

1. Azure AD / Entra ID (if used):
   - Tenant configuration
   - Conditional Access policies
   - PIM (Privileged Identity Management) enabled?
   - Identity Protection enabled?
   - B2B/B2C identity scenarios?

2. AWS IAM (if used):
   - IAM users vs. federated access
   - IAM roles structure
   - Service control policies (SCPs)
   - AWS Organizations
   - Root account security

3. GCP IAM (if used):
   - Organization structure
   - Project-level IAM
   - Service accounts
   - Workload identity federation

4. SaaS application access:
   - How is access managed for SaaS apps?
   - SSO integrated or standalone credentials?
   - Admin access to SaaS apps

Gaps to flag:
- IAM users with access keys instead of federated access
- No conditional access policies
- Root/break-glass accounts not secured
- SaaS apps with standalone credentials
```

### Prompt 4.2 - Federation and Trust
```
Document identity federation and trust relationships:

1. Federation configuration:
   - Federation with cloud providers (Azure AD, AWS, GCP)
   - Federation with partners/customers
   - Federation protocol (SAML, OIDC, WS-Fed)

2. Trust relationships:
   - AD forest trusts
   - Cross-tenant trusts
   - Partner organization trusts

3. External identity scenarios:
   - Customer identity (CIAM)
   - Partner/B2B access
   - Contractor access

4. Integration considerations:
   - Can identity be federated with buyer?
   - Conflicting domains?
   - UPN/email domain overlap?

Integration risk assessment:
- Simple (single AD, standard federation): Low complexity
- Moderate (multi-forest, existing federation): Medium complexity
- Complex (multiple IdPs, custom CIAM): High complexity
```

---

## Phase 5: Identity Monitoring and Compliance

### Prompt 5.1 - Identity Monitoring
```
Assess identity and access monitoring:

1. Authentication monitoring:
   - Failed login monitoring
   - Impossible travel detection
   - Anomalous login alerts
   - Brute force detection

2. Privileged activity monitoring:
   - Admin activity logging
   - Alerts on sensitive operations
   - Privileged session recording

3. Identity threat detection:
   - Azure AD Identity Protection (or equivalent)
   - UEBA for identity
   - Compromised credential detection

4. Audit logging:
   - Authentication logs retained (duration)
   - Authorization change logs
   - Log centralization (SIEM)

Gaps to flag:
- No authentication monitoring
- No privileged activity logging
- Logs not centralized
```

### Prompt 5.2 - Identity Compliance
```
Assess identity-related compliance:

1. Regulatory requirements:
   - SOX controls for identity (if applicable)
   - HIPAA access controls (if applicable)
   - PCI-DSS access requirements (if applicable)
   - Industry-specific requirements

2. Access certification:
   - Evidence of access reviews
   - Reviewer attestation
   - Remediation of inappropriate access

3. Segregation of duties:
   - SoD rules defined
   - Violations monitoring
   - Compensating controls

4. Audit findings:
   - Recent identity/access audit findings
   - Remediation status

Compliance gaps to flag:
- No access reviews (regulatory violation for many)
- No SoD controls
- Unresolved audit findings
```

---

## Phase 6: Risks and Integration Considerations

### Prompt 6.1 - Identity and Access Risks
```
Synthesize identity and access risks:

For each risk:
- Risk title
- Description
- Severity (Critical/High/Medium/Low)
- Category:
  - Security Risk (breach potential)
  - Compliance Gap (regulatory exposure)
  - Integration Complexity
  - Operational Risk
- Evidence (source quote)
- Mitigation approach

Priority risks to identify:
1. MFA not enforced (Critical)
2. No PAM for privileged accounts (High)
3. Orphaned/stale accounts (Medium-High)
4. No access reviews (Medium-High)
5. No service account management (High)
6. Over-provisioned access (Medium)
7. No SSO for key applications (Medium)
8. Poor cloud IAM hygiene (High)
```

### Prompt 6.2 - Identity Integration Considerations
```
Assess identity integration complexity for M&A:

1. Day 1 access requirements:
   - What access do buyer employees need immediately?
   - What access do target employees need to buyer systems?
   - Minimum connectivity for integration

2. Identity consolidation approach:
   - Merge into buyer's directory?
   - Federation between organizations?
   - Hybrid period duration?

3. Technical considerations:
   - UPN/domain conflicts
   - Same IdP vendor? (easier)
   - Different IdP vendors? (federation required)
   - Conditional access policy alignment

4. Access management alignment:
   - Role alignment between organizations
   - Access request process alignment
   - Privileged access model alignment

Integration complexity rating: Low | Medium | High | Very High

Key integration workstreams to plan:
- [List specific integration tasks]
```

### Prompt 6.3 - Identity Follow-up Questions
```
Generate identity-focused follow-up questions:

For each question:
- Question text
- Why it matters
- Priority (Must have / Important / Nice to have)
- Who should answer

Essential questions:
1. What is your MFA coverage percentage? (All users, privileged users, remote access)
2. How do you manage privileged access? Do you use a PAM solution?
3. When was your last access review, and what was remediated?
4. How many service accounts exist, and who owns them?
5. How do you handle terminations - what's the de-provisioning process and timeline?
6. What applications are NOT integrated with SSO?
7. Do you have any AD forest trusts or external federation?
8. How many domain admin / global admin accounts exist?
```

---

## Output Checklist

After running this playlist, you should have:
- [ ] Identity provider and directory inventory
- [ ] Identity lifecycle management assessment
- [ ] MFA implementation details with coverage percentages
- [ ] Authentication policy documentation
- [ ] Access control model assessment
- [ ] Privileged access management evaluation
- [ ] Cloud IAM assessment (AWS, Azure, GCP)
- [ ] Federation and trust relationship inventory
- [ ] Identity monitoring capabilities assessment
- [ ] Identity compliance status
- [ ] Prioritized risk list with severity
- [ ] Identity integration complexity assessment
- [ ] Follow-up questions for management sessions
