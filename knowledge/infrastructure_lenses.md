# Infrastructure Domain: Comprehensive Consideration Library

## PURPOSE
This library contains the accumulated knowledge of IT M&A due diligence. Each section represents a distinct analytical lens. When analyzing infrastructure, the agent should systematically apply each lens to ensure nothing is missed.

---

# SECTION 1: CURRENT STATE ASSESSMENT LENSES

## LENS 1.1: HOSTING MODEL ANALYSIS

**What we're looking for:**
Where do systems live and what does that mean for the deal?

**Patterns that matter:**

| Pattern | Implication | Typical Cost Impact |
|---------|-------------|---------------------|
| 100% on-prem, owned DC | Maximum control, maximum responsibility | DC exit costs if consolidating |
| Colo with 2+ years remaining | Lease liability or leverage for renegotiation | $50-200K/year typical |
| Colo expiring < 12 months | Hard deadline, may drive timeline | Migration acceleration cost |
| Heavy AWS, buyer is Azure | Platform migration or multi-cloud complexity | 20-40% lift to migrate |
| Cloud-native (containers, K8s) | Modern but needs skilled team | Premium labor rates |
| Mainframe present | Specialized skills, long timeline | $500K-$5M+ depending on scope |
| Parent company shared DC | Separation complexity, TSA likely | TSA + migration costs |

**Red flags:**
- "Hosted by parent company" - separation work required
- "Our IT guy manages the servers" - key person risk, no documentation
- "We're in the process of migrating to cloud" - in-flight project risk
- Single data center, no DR - business continuity risk

---

## LENS 1.2: COMPUTE & SERVER ANALYSIS

**EOL/EOS Reference Table:**

| Technology | End of Support | Risk Level |
|------------|---------------|------------|
| Windows Server 2012 R2 | Oct 2023 | CRITICAL |
| Windows Server 2016 | Jan 2027 | MEDIUM |
| Windows Server 2019 | Jan 2029 | LOW |
| RHEL 6/7 | PASSED | CRITICAL |
| VMware 6.5/6.7 | Oct 2022 | CRITICAL |
| VMware 7.0 | Apr 2025 | MEDIUM |
| SQL Server 2014 | Jul 2024 | CRITICAL |
| SQL Server 2016 | Jul 2026 | MEDIUM |

---

## LENS 1.3: STORAGE & DR

**Backup & DR assessment:**

| Capability | Good | Concerning | Red Flag |
|------------|------|------------|----------|
| RPO | < 1 hour | 1-24 hours | > 24 hours |
| RTO | < 4 hours | 4-24 hours | > 24 hours |
| DR Testing | Quarterly+ | Annually | Never |

---

# SECTION 2: COST REFERENCE

| Work Package | Typical Range |
|--------------|---------------|
| Discovery & Assessment | $50K - $200K |
| AD/IAM Integration | $75K - $300K |
| Network Integration | $50K - $250K |
| Server Migration | $100K - $1M+ |
| Storage Migration | $75K - $500K |
| Cloud Migration | $100K - $2M+ |
| DC Exit | $100K - $1M |

**Labor rates:**

| Role | Blended Rate |
|------|-------------|
| Project Manager | $175/hr |
| Solution Architect | $225/hr |
| Infrastructure Engineer | $150/hr |
| Cloud Engineer | $175/hr |
| Security Engineer | $185/hr |
