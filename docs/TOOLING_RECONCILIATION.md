# Security Tooling Reconciliation

## Summary

The discovery phase identified security tooling from **both** the target company and buyer profiles. This document clarifies which tools belong to which entity.

---

## Confirmed Tooling

### Target Company (National Underwriters)
**Source**: `target_profile_20260106_165831.md` lines 137-141

| Category | Tool | Status |
|----------|------|--------|
| Firewall | **Palo Alto Networks** | ✓ Confirmed |
| Endpoint Protection | **Microsoft Defender** | ✓ Confirmed |
| SIEM | **Microsoft Sentinel** | ✓ Confirmed |
| MFA | **Microsoft Authenticator** | ✓ Confirmed |
| IAM | **Okta Identity** | ✓ Confirmed |
| Directory | **Active Directory (Windows Server 2016)** | ✓ Confirmed |

### Buyer (Great Corporation)
**Source**: `buyer_profile_20260106_165831.md` lines 110-113

| Category | Tool | Status |
|----------|------|--------|
| Firewall | **Fortinet** | ✓ Confirmed |
| Endpoint Protection | **Microsoft Defender** | ✓ Confirmed |
| SIEM | **LogRhythm** | ✓ Confirmed |
| MFA | **Ping Identity** | ✓ Confirmed |

---

## Conflicts Identified

| Category | Target Has | Buyer Has | Integration Implication |
|----------|-----------|-----------|------------------------|
| Firewall | Palo Alto Networks | Fortinet | Platform decision required |
| SIEM | Microsoft Sentinel | LogRhythm | Data migration and consolidation |
| MFA | Microsoft Authenticator | Ping Identity | User migration required |
| **No Conflict** | Microsoft Defender | Microsoft Defender | Already aligned |

---

## Incorrect References to Correct

The following references in generated outputs incorrectly attribute **buyer tools** to the **target company**:

### In `facts/facts_*.json`:
- ❌ "Security Tools include: Fortinet Firewall, Microsoft Defender, LogRhythm SIEM, Ping Identity MFA"
  - Should specify this is buyer tooling, not target

### In `narratives_*.json`:
- ❌ "Security tooling appears standard enterprise (Fortinet firewalls, Microsoft Defender, LogRhythm SIEM, Ping MFA)"
  - Target actually has: Palo Alto, MS Defender, MS Sentinel, MS Authenticator

### In `investment_thesis_*.html`:
- ✓ "Palo Alto firewalls providing security and Microsoft Authenticator handling MFA" - CORRECT for target
- ❌ "Fortinet firewall exists" - INCORRECT, this is buyer's firewall

---

## Resolution

For the investment thesis presentation (focused on target company):
1. **Target tooling** should be prominently featured
2. **Buyer tooling** should only appear in "Integration Considerations" context
3. Add explicit "Target vs Buyer" comparison where relevant

### Correct Target Security Stack Description:
> "The target operates Palo Alto Networks firewalls, Microsoft Defender for endpoint protection, Microsoft Sentinel for SIEM, and Microsoft Authenticator for MFA. Identity is managed through Okta with Active Directory (Windows Server 2016) providing directory services."

### Integration Context:
> "The buyer's security stack differs in several areas: Fortinet (vs Palo Alto), LogRhythm (vs Sentinel), and Ping Identity (vs Microsoft Authenticator). Microsoft Defender is aligned across both organizations."
