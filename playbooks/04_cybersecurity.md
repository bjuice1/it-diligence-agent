# Cybersecurity Review Playlist

## Pre-Flight Considerations

**What makes Cybersecurity different from other IT domains:**

1. **Material risk to the deal** - Unlike most IT findings that are integration complexity or cost, cybersecurity gaps can be deal-breakers. An undisclosed breach, weak security posture, or compliance gap can result in purchase price adjustments, escrows, or walk-aways.

2. **Often requires specialist assessment** - IT DD covers cybersecurity at a diligence level, but complex situations (previous breaches, highly regulated industries, nation-state threat exposure) may warrant a dedicated cybersecurity firm engagement.

3. **What you see isn't always what you get** - Companies often overstate their security posture. "We use MFA" might mean "MFA is available but only 30% enabled." Probe claims with evidence.

4. **Compliance is not security** - SOC 2 certified doesn't mean secure. ISO 27001 certified doesn't mean secure. These are baselines that may or may not reflect actual security posture. Look at both.

5. **Integration creates new attack surface** - Connecting two networks creates risk. Access provisioning during transition is high-risk. The integration window is when breaches happen.

6. **Incident history matters** - Previous breaches, ransomware events, or near-misses are predictive. Ask directly. Companies may not volunteer this.

**What we learned building the bespoke tool:**

- The security tool inventory (EDR, SIEM, IAM, email security, etc.) tells you about investment but not effectiveness.
- MFA coverage percentage is one of the most important single metrics. Ask for it explicitly.
- Vulnerability management and patching cadence separate mature orgs from immature ones.
- Incident response plans exist on paper but often haven't been tested. "When did you last run a tabletop exercise?" is revealing.
- Third-party/vendor risk management is frequently a gap, especially in smaller companies.

---

## Phase 1: Security Governance and Program Maturity

### Prompt 1.1 - Security Program Overview
```
Assess the overall cybersecurity program:

1. Security leadership:
   - Is there a CISO or security leader? (Title, reporting line)
   - Dedicated security team or IT handles security?
   - Team size (if mentioned)
   - Use of MSSPs or outsourced security?

2. Security governance:
   - Is there a security policy framework?
   - Are policies documented and current?
   - Security awareness training program?
   - Board/executive security reporting?

3. Security strategy:
   - Documented security strategy or roadmap?
   - Security budget (if mentioned)
   - Recent or planned security investments

4. Frameworks and standards:
   - Which frameworks are followed? (NIST CSF, ISO 27001, CIS Controls, COBIT)
   - Are they formally adopted or just referenced?

Assess security program maturity: Ad-hoc | Basic | Developing | Managed | Optimized
```

### Prompt 1.2 - Compliance and Certifications
```
Document security compliance posture:

1. Certifications held:
   - SOC 2 Type I or Type II (scope, date of last report)
   - ISO 27001 (scope, certification body, expiry)
   - PCI DSS (level, scope, QSA)
   - HITRUST (if healthcare)
   - FedRAMP (if government)
   - Other (ISO 27701, SOC 1, etc.)

2. Regulatory compliance:
   - GDPR (applicable? DPO appointed? privacy program?)
   - CCPA/CPRA (applicable?)
   - HIPAA (applicable? BAAs in place?)
   - Industry-specific (FFIEC, NERC CIP, etc.)

3. Compliance gaps:
   - Any known compliance gaps or remediation in progress?
   - Audit findings not yet resolved?
   - Certifications lapsed or at risk?

4. Third-party audits:
   - Penetration testing (frequency, last date, findings)
   - Vulnerability assessments
   - Security audits

Format certifications as table: Certification | Scope | Status | Expiry/Last Report | Notes
```

---

## Phase 2: Security Controls Inventory

### Prompt 2.1 - Endpoint Security
```
Document endpoint security controls:

1. Endpoint protection:
   - EDR/XDR solution (CrowdStrike, SentinelOne, Microsoft Defender, Carbon Black, other)
   - Deployment coverage (% of endpoints)
   - Traditional AV in use or fully EDR?

2. Endpoint management:
   - MDM for mobile devices (Intune, Jamf, VMware Workspace ONE)
   - Device encryption (BitLocker, FileVault) - coverage %
   - USB/removable media controls

3. Patch management:
   - Patching solution (WSUS, SCCM, Intune, third-party)
   - Patch SLA (critical patches within X days)
   - Patch compliance rate (if mentioned)
   - Third-party application patching

4. Configuration management:
   - Hardening standards applied (CIS benchmarks, STIG)
   - Configuration compliance monitoring

Gaps to flag:
- EDR coverage below 95%
- No MDM for mobile devices
- No disk encryption
- Patching SLA > 30 days for critical
```

### Prompt 2.2 - Network and Perimeter Security
```
Document network security controls (beyond firewall inventory in Network playlist):

1. Intrusion Detection/Prevention:
   - IDS/IPS solution and vendor
   - Coverage (perimeter only, internal)
   - Monitored 24/7?

2. Network segmentation:
   - Are sensitive systems segmented?
   - Network zones defined (DMZ, internal, PCI, etc.)
   - Micro-segmentation in use?

3. Secure web gateway:
   - Web filtering (on-prem proxy, cloud SWG)
   - SSL/TLS inspection
   - URL categorization

4. Email security:
   - Email gateway (Proofpoint, Mimecast, Microsoft Defender, Barracuda)
   - Anti-phishing controls
   - DMARC/DKIM/SPF configured?
   - Email encryption capability

5. DNS security:
   - DNS filtering (Cisco Umbrella, Zscaler, Cloudflare)
   - DNS logging and monitoring

Gaps to flag:
- No email security gateway
- No web filtering
- No network segmentation
- No DMARC configured
```

### Prompt 2.3 - Security Operations and Monitoring
```
Document security operations capabilities:

1. SIEM / Security monitoring:
   - SIEM platform (Splunk, Microsoft Sentinel, Elastic, QRadar, other)
   - Log sources ingested
   - Retention period
   - Correlation rules / use cases

2. Security Operations Center:
   - Internal SOC or outsourced (MSSP)?
   - Coverage hours (24/7, business hours only)
   - MSSP provider if outsourced

3. Threat detection:
   - Threat intelligence feeds
   - Threat hunting capability
   - User behavior analytics (UBA/UEBA)

4. Alert management:
   - Alert volume (if mentioned)
   - Mean time to respond (MTTR)
   - Escalation process

Gaps to flag:
- No SIEM or central log aggregation
- No 24/7 monitoring capability
- No threat intelligence
```

### Prompt 2.4 - Data Protection and Privacy
```
Document data protection controls:

1. Data classification:
   - Data classification scheme in use?
   - Sensitive data inventory (where is PII, PHI, financial data?)
   - Data flow mapping

2. Data Loss Prevention (DLP):
   - DLP solution (Microsoft Purview, Symantec, Forcepoint)
   - Channels covered (email, endpoint, cloud)
   - Policies configured

3. Encryption:
   - Data at rest encryption (databases, file shares, backups)
   - Data in transit encryption (TLS versions)
   - Key management

4. Cloud data security:
   - CASB in use? (Netskope, Microsoft Defender for Cloud Apps, Zscaler)
   - Cloud posture management (CSPM)
   - Shadow IT visibility

5. Privacy program:
   - Privacy officer/DPO
   - Data subject request process
   - Consent management
   - Data retention policies

Gaps to flag:
- No data classification
- Sensitive data not encrypted
- No DLP
- No visibility into cloud data
```

---

## Phase 3: Vulnerability Management

### Prompt 3.1 - Vulnerability Management Program
```
Assess vulnerability management practices:

1. Vulnerability scanning:
   - Scanning tool (Tenable, Qualys, Rapid7, Microsoft Defender)
   - Scope (internal, external, cloud, applications)
   - Frequency (continuous, weekly, monthly)
   - Coverage (% of assets scanned)

2. Vulnerability metrics:
   - Total vulnerability count (by severity)
   - Mean time to remediate (by severity)
   - Aging vulnerabilities (>90 days)
   - Exception/risk acceptance process

3. Remediation SLAs:
   - Critical vulnerabilities: X days
   - High vulnerabilities: X days
   - Medium/Low: X days

4. External exposure:
   - External attack surface monitoring?
   - Known internet-facing vulnerabilities?

5. Application security:
   - SAST/DAST tools in use?
   - Secure SDLC practices
   - Third-party code scanning (SCA)

Risk indicators:
- Critical/high vulnerabilities open > 30 days
- No regular scanning
- Unknown external attack surface
```

### Prompt 3.2 - Penetration Testing History
```
Document penetration testing and security assessments:

1. Penetration testing:
   - Frequency (annual, semi-annual, continuous)
   - Last test date
   - Scope (external, internal, web apps, social engineering)
   - Testing firm

2. Findings summary (if available):
   - Critical/high findings count
   - Are findings remediated?
   - Recurring findings?

3. Red team / adversary simulation:
   - Ever conducted?
   - Results and lessons learned

4. Bug bounty program:
   - Public or private program?
   - Platform (HackerOne, Bugcrowd)

If no recent pentest: Flag as gap. If findings unresolved: Flag severity.
```

---

## Phase 4: Incident Response and Business Continuity

### Prompt 4.1 - Incident Response Capability
```
Assess incident response readiness:

1. Incident response plan:
   - Documented IR plan? (Yes/No)
   - Last updated
   - IR team defined?
   - Roles and responsibilities documented?

2. IR testing:
   - Tabletop exercises (frequency, last date)
   - Technical IR drills
   - Lessons learned documented?

3. IR capabilities:
   - Forensics capability (internal or retainer)
   - Containment procedures
   - Evidence preservation
   - Communication templates

4. External support:
   - IR retainer in place? (provider, scope)
   - Legal counsel for cyber incidents
   - Cyber insurance (covered in contracts)

5. Detection and response metrics:
   - Mean time to detect (MTTD)
   - Mean time to respond (MTTR)
   - Mean time to contain (MTTC)

Gaps to flag:
- No documented IR plan
- IR plan never tested
- No forensics capability
- No IR retainer
```

### Prompt 4.2 - Incident History
```
**IMPORTANT: This is a sensitive area. Document carefully.**

Review any disclosed incident history:

1. Security incidents (past 3 years):
   - Any reported breaches?
   - Ransomware events?
   - Data exfiltration?
   - Business email compromise?
   - Regulatory notifications made?

2. Near-misses or contained incidents:
   - Phishing campaigns that succeeded partially?
   - Malware detected and contained?
   - Unauthorized access attempts?

3. Remediation:
   - Were root causes identified?
   - What was remediated?
   - Were controls improved post-incident?

4. Ongoing investigations:
   - Any current incidents or investigations?
   - Law enforcement involvement?

Note: Undisclosed breaches discovered post-close are a material risk. If documents don't address incident history, this should be a direct management question.
```

---

## Phase 5: Third-Party and Supply Chain Risk

### Prompt 5.1 - Third-Party Risk Management
```
Assess vendor and third-party security risk management:

1. Vendor risk program:
   - Formal third-party risk management program? (Yes/No)
   - Risk assessment process for new vendors
   - Vendor classification/tiering

2. Critical vendor inventory:
   - Who has access to sensitive data or systems?
   - Cloud providers and their security posture
   - Outsourced IT/development vendors
   - Data processors

3. Vendor assessments:
   - Security questionnaires required?
   - SOC 2 reports reviewed?
   - Right to audit clauses?
   - Continuous monitoring?

4. Vendor incidents:
   - Any vendor breaches affecting the company?
   - Solarwinds, Log4j exposure?
   - Response to major supply chain events?

Gaps to flag:
- No third-party risk program
- Unknown vendor access to sensitive data
- No vendor security requirements
```

---

## Phase 6: Security Risks Summary

### Prompt 6.1 - Cybersecurity Risks for Due Diligence
```
Synthesize all findings into cybersecurity-specific risks:

For each risk:
- Risk title
- Description
- Severity (Critical/High/Medium/Low)
- Category:
  - Breach Risk (could lead to data breach)
  - Compliance Gap (regulatory exposure)
  - Operational Risk (could cause outage)
  - Integration Risk (complicates integration)
  - Financial Risk (unbudgeted remediation)
- Evidence (source quote)
- Recommended mitigation

Priority order for severity:
1. Active threats or unremediated incidents (Critical)
2. Missing foundational controls - no EDR, no MFA, no patching (Critical/High)
3. Compliance gaps affecting deal or ongoing operations (High)
4. Security debt requiring investment (Medium/High)
5. Best practice gaps (Medium/Low)

Always flag:
- MFA not enforced (especially for privileged access)
- EDR coverage gaps
- Unpatched critical vulnerabilities
- Previous breaches not fully remediated
- No incident response capability
```

### Prompt 6.2 - Security Posture Score
```
Provide an overall security posture assessment:

Rate each area (1-5, where 5 is mature):
- Governance and program maturity: X/5
- Identity and access management: X/5 (detailed in IAM playlist)
- Endpoint security: X/5
- Network security: X/5
- Data protection: X/5
- Vulnerability management: X/5
- Security operations: X/5
- Incident response: X/5
- Third-party risk: X/5

Overall security posture: Weak | Below Average | Average | Above Average | Strong

Key strengths:
- [List top 3 strengths]

Critical gaps requiring immediate attention:
- [List top 3 gaps]

Estimated remediation investment: Low (<$100K) | Medium ($100K-$500K) | High ($500K-$1M) | Very High (>$1M)
```

### Prompt 6.3 - Security Follow-up Questions
```
Generate security-focused follow-up questions:

For each question:
- Question text
- Why it matters (what risk does it address)
- Priority (Must have before close / Important for planning / Nice to have)
- Who should answer (CISO, IT, Legal, Management)

Essential questions if not answered:
1. Has the company experienced any security incidents or breaches in the past 3 years?
2. What is the current MFA coverage percentage for all users? For privileged users?
3. When was the last penetration test, and what were the findings?
4. What is the vulnerability remediation SLA and current compliance rate?
5. Is there cyber insurance? What are the coverage limits and exclusions?
6. Who has access to the most sensitive data, and how is that access controlled?
7. What third parties have access to production systems or sensitive data?
```

---

## Output Checklist

After running this playlist, you should have:
- [ ] Security program maturity assessment
- [ ] Compliance certifications inventory with status
- [ ] Endpoint security controls inventory and coverage
- [ ] Network security controls inventory
- [ ] Security operations and monitoring assessment
- [ ] Data protection controls inventory
- [ ] Vulnerability management program assessment
- [ ] Penetration testing history and findings status
- [ ] Incident response readiness assessment
- [ ] Incident history (if disclosed)
- [ ] Third-party risk management assessment
- [ ] Overall security posture rating
- [ ] Prioritized risk list with severity
- [ ] Follow-up questions for management sessions
