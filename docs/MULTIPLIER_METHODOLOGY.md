# Cost Multiplier Methodology

## How We Calculate Integration Costs

**Formula:** `Base Cost × Size × Industry × Geography × IT Maturity`

Each multiplier is derived from underlying considerations that your team evaluates during due diligence. This document explains both the multipliers AND the Layer 2 thinking behind them.

---

# Layer 1: The Multipliers

## Size Multiplier (0.4x - 4.0x)

| Employees | Multiplier |
|-----------|------------|
| <50 | 0.4x |
| 50-100 | 0.6x |
| 100-250 | 0.8x |
| 250-500 | 1.0x (baseline) |
| 500-1,000 | 1.5x |
| 1,000-2,500 | 2.2x |
| 2,500-5,000 | 3.0x |
| 5,000+ | 4.0x |

## Industry Factor (0.9x - 1.5x)

| Industry | Factor |
|----------|--------|
| Financial Services / Banking | 1.5x |
| Healthcare / Life Sciences | 1.4x |
| Government | 1.4x |
| Insurance / Energy | 1.3x |
| Manufacturing | 1.2x |
| Retail / Logistics | 1.1x |
| Technology / Media | 1.0x |
| Professional Services / Education | 0.9x |

## Geography Factor (1.0x - 1.6x)

| Scope | Factor |
|-------|--------|
| Single Country | 1.0x |
| Multi-Country (Same Region) | 1.2x |
| Multi-Region | 1.4x |
| Global | 1.6x |

## IT Maturity Factor (0.8x - 1.6x)

| Maturity | Factor |
|----------|--------|
| Advanced | 0.8x |
| Standard | 1.0x |
| Basic | 1.3x |
| Minimal | 1.6x |

---

# Layer 2: The Considerations

## Size Considerations

### Why does size matter?

More employees = more complexity across every dimension:

| Consideration | Small (<250) | Mid-Market (250-1000) | Enterprise (1000+) |
|---------------|--------------|----------------------|-------------------|
| **User Migration** | Days | Weeks | Months |
| **Change Management** | Email + training | Formal program | Multi-wave rollout |
| **Testing Scope** | Spot check | UAT cycles | Regression suites |
| **Stakeholders** | 2-3 decision makers | Department heads | Steering committee |
| **Governance** | Informal | PMO light | Full PMO + governance |

### Questions to ask:

- [ ] Total headcount (FTE + contractors)?
- [ ] How many offices/locations?
- [ ] How many business units?
- [ ] Shared services or decentralized IT?
- [ ] Union considerations for changes?
- [ ] Seasonal workforce fluctuations?

---

## Industry Considerations

### Financial Services / Banking (1.5x)

**Why 1.5x?** Highest regulatory burden + core system complexity

| Consideration | Impact | Questions to Ask |
|---------------|--------|------------------|
| **SOX Compliance** | Change control, audit trails | What's the SOX scope? How many controls? |
| **PCI-DSS** | If card data, full PCI scope | Do they process/store card data? PCI level? |
| **Core Banking System** | Mainframe often involved | What core banking platform? Age? Customizations? |
| **Regulatory Reporting** | CCAR, DFAST, Basel III | What regulatory reports? Manual or automated? |
| **Trading Systems** | Real-time, low latency | Any trading operations? What platforms? |
| **Data Retention** | 7+ years typically | What's the retention policy? Archive strategy? |

**Red Flags:**
- Multiple core banking systems
- Manual regulatory reporting
- Mainframe dependencies
- No documented DR for critical systems

---

### Healthcare (1.4x)

**Why 1.4x?** PHI protection + clinical system complexity

| Consideration | Impact | Questions to Ask |
|---------------|--------|------------------|
| **HIPAA Scope** | PHI everywhere increases scope | How many systems touch PHI? |
| **EMR/EHR System** | Epic, Cerner = complex | Which EMR? How customized? |
| **Medical Devices** | IoMT integration | Connected medical devices? Who manages? |
| **BAA Requirements** | Every vendor needs BAA | How many vendors have BAAs? |
| **State Regulations** | Vary by state | Which states? Any special requirements? |
| **Clinical Workflows** | Can't disrupt patient care | What's the maintenance window? |

**Red Flags:**
- Multiple EMR systems (M&A history)
- Legacy medical devices (Windows XP)
- No BAA inventory
- Unclear PHI data flows

---

### Life Sciences (1.4x)

**Why 1.4x?** FDA validation + GxP requirements

| Consideration | Impact | Questions to Ask |
|---------------|--------|------------------|
| **FDA 21 CFR Part 11** | Electronic records/signatures | Which systems are Part 11 compliant? |
| **GxP Validation** | IQ/OQ/PQ for changes | What validation documentation exists? |
| **Clinical Trial Systems** | CTMS, EDC, safety | Any clinical operations? Which systems? |
| **Quality Systems** | QMS, CAPA, deviations | What QMS? How integrated? |
| **Supply Chain** | Serialization, track & trace | DSCSA compliance status? |
| **Audit Readiness** | FDA inspections | When was last FDA inspection? Findings? |

**Red Flags:**
- No validation documentation
- Spreadsheet-based quality systems
- Manual batch records
- Recent FDA warning letters

---

### Manufacturing (1.2x)

**Why 1.2x?** OT/IT convergence + shop floor complexity

| Consideration | Impact | Questions to Ask |
|---------------|--------|------------------|
| **OT Environment** | SCADA, PLCs, HMIs | What OT systems? How old? |
| **MES/MOM** | Manufacturing execution | MES platform? Integration to ERP? |
| **ERP Integration** | Shop floor to financials | Real-time or batch integration? |
| **Plant Networks** | Often air-gapped | Network architecture? IT/OT segmentation? |
| **24/7 Operations** | Limited change windows | Plant schedules? Downtime tolerance? |
| **Safety Systems** | SIS, emergency shutdown | Safety system architecture? |

**Red Flags:**
- Flat OT network (no segmentation)
- Windows XP/7 on shop floor
- No OT cybersecurity program
- Tribal knowledge for PLC programming

---

### Government (1.4x)

**Why 1.4x?** FedRAMP + clearance requirements

| Consideration | Impact | Questions to Ask |
|---------------|--------|------------------|
| **FedRAMP** | Cloud authorization | What FedRAMP level needed? |
| **Security Clearances** | Personnel requirements | What clearance levels? How many cleared staff? |
| **NIST 800-171** | CUI protection | Do they handle CUI? Current compliance? |
| **CMMC** | DoD requirements | What CMMC level required? |
| **Contract Vehicles** | GWACs, BPAs | Which contract vehicles? |
| **Agency Requirements** | Vary by agency | Which agencies? Special requirements? |

**Red Flags:**
- No FedRAMP authorized systems
- Clearance gaps in IT staff
- CMMC assessment not started
- Unclear CUI scope

---

### Technology / Software (1.0x - Baseline)

**Why baseline?** Modern stack assumed, but verify

| Consideration | Impact | Questions to Ask |
|---------------|--------|------------------|
| **Cloud Native** | Easier migration | What % cloud vs on-prem? |
| **Tech Stack Age** | Modern = simpler | When was last major platform upgrade? |
| **DevOps Maturity** | CI/CD readiness | What's the deployment process? |
| **Documentation** | Should be good | Is architecture documented? |
| **Technical Debt** | Can be hidden | Known tech debt backlog? |
| **Open Source** | License compliance | Open source inventory? License types? |

**Red Flags:**
- More on-prem than expected
- No CI/CD pipeline
- Undocumented architecture
- GPL code in commercial product

---

## Geography Considerations

### Single Country (1.0x - Baseline)

| Consideration | Questions to Ask |
|---------------|------------------|
| **Data Residency** | Any restrictions on where data lives? |
| **Compliance** | Single regulatory framework |
| **Time Zones** | Generally one or adjacent |
| **Language** | Single language for systems |

---

### Multi-Country Same Region (1.2x)

**Examples:** EU countries, LATAM, APAC

| Consideration | Impact | Questions to Ask |
|---------------|--------|------------------|
| **GDPR (EU)** | Data protection compliance | GDPR compliance status? DPO in place? |
| **Cross-Border Data** | Transfer mechanisms | SCCs in place? Data transfer agreements? |
| **Language** | Multi-language systems | Which languages supported? Translation needs? |
| **Local Regulations** | Country-specific rules | Any country-specific requirements? |
| **Time Zones** | Extended support hours | Support coverage model? |

**Red Flags:**
- No GDPR compliance program
- Data transfers without SCCs
- No local language support
- Single time zone support for multi-TZ operations

---

### Multi-Region (1.4x)

**Examples:** Americas + EMEA, APAC + Europe

| Consideration | Impact | Questions to Ask |
|---------------|--------|------------------|
| **Data Sovereignty** | Multiple jurisdictions | Where does data reside today? |
| **Regional Platforms** | May have separate instances | Same systems globally or regional? |
| **Connectivity** | WAN complexity | Network architecture? MPLS? SD-WAN? |
| **Support Model** | Follow-the-sun needed | 24/7 support? Regional teams? |
| **Compliance Matrix** | Multiple frameworks | Which regulations per region? |

**Red Flags:**
- No data residency controls
- Separate ERP per region
- No global network architecture
- Unclear compliance matrix

---

### Global (1.6x)

**All major regions with complex operations**

| Consideration | Impact | Questions to Ask |
|---------------|--------|------------------|
| **China Operations** | Firewall, data localization | Operations in China? Data requirements? |
| **Russia/Sanctions** | OFAC compliance | Any sanctioned country operations? |
| **Data Localization** | Multiple sovereign requirements | Which countries require local data? |
| **24/7 Operations** | True follow-the-sun | How is global support staffed? |
| **Global WAN** | Complex connectivity | Global network architecture? Latency requirements? |
| **Currency/Language** | Multi-everything | How many currencies? Languages? |

**Red Flags:**
- China data not localized
- No sanctions screening
- Single point of failure in global network
- No 24/7 support capability

---

## IT Maturity Considerations

### How to Assess IT Maturity

| Dimension | Advanced (0.8x) | Standard (1.0x) | Basic (1.3x) | Minimal (1.6x) |
|-----------|-----------------|-----------------|--------------|----------------|
| **Infrastructure** | Cloud-native, IaC | Hybrid, some automation | On-prem, manual | Legacy, no virtualization |
| **Security** | Zero trust, SOC | Perimeter + EDR | Firewall + AV | Basic firewall only |
| **Documentation** | Up-to-date, complete | Mostly documented | Tribal knowledge | Nothing written down |
| **ITSM** | ServiceNow, mature processes | Ticketing system | Email/spreadsheet | Reactive only |
| **DR/BCP** | Tested annually, automated | Plan exists, rarely tested | Backup only | No DR plan |
| **Development** | CI/CD, GitOps | Source control, some automation | FTP deployments | Cowboy coding |

### Questions to Assess Maturity:

- [ ] When was the last infrastructure diagram updated?
- [ ] Is there a CMDB? Is it accurate?
- [ ] What's the patch compliance rate?
- [ ] When was DR last tested?
- [ ] What's the mean time to recover from incidents?
- [ ] How are changes deployed to production?
- [ ] Is there a security operations capability?
- [ ] What's the technical debt backlog?

### Red Flags for Low Maturity:

- "Our IT guy knows everything" (tribal knowledge)
- No network diagram
- Backups never tested
- No change management process
- Admin credentials shared
- No inventory of systems
- Expired SSL certs in production

---

# Using This in Due Diligence

## Quick Assessment Checklist

During initial discovery, score each dimension:

| Dimension | Score (1-5) | Notes |
|-----------|-------------|-------|
| Company Size | ___ | Employees: ___ |
| Industry Complexity | ___ | Key factors: ___ |
| Geographic Spread | ___ | Countries: ___ |
| IT Maturity | ___ | Key concerns: ___ |

## Calculating the Multiplier

1. **Size:** Look up in table based on employee count
2. **Industry:** Start with table value, adjust based on Layer 2 findings
3. **Geography:** Based on operational footprint
4. **IT Maturity:** Based on assessment questions

**Example:**
- 800 employees → 1.5x
- Healthcare with 3 EMR systems → 1.4x + 0.2 adjustment = 1.6x
- US + EU operations → 1.2x
- Basic maturity (legacy EMR) → 1.3x
- **Total: 1.5 × 1.6 × 1.2 × 1.3 = 3.74x**

## Adjusting Multipliers

The table values are starting points. Adjust based on findings:

| Finding | Adjustment |
|---------|------------|
| More complex than typical for industry | +0.1 to +0.3 |
| Simpler than typical | -0.1 to -0.2 |
| Major red flag discovered | +0.2 to +0.5 |
| Recent modernization completed | -0.1 to -0.2 |

---

# Appendix: Industry-Specific Checklists

## Healthcare Due Diligence Checklist

- [ ] HIPAA compliance assessment date
- [ ] PHI data flow diagram
- [ ] EMR platform and version
- [ ] Number of clinical applications
- [ ] BAA inventory
- [ ] Medical device inventory
- [ ] Security risk assessment date
- [ ] Breach history

## Financial Services Due Diligence Checklist

- [ ] SOX control inventory
- [ ] PCI-DSS scope and compliance status
- [ ] Core banking platform details
- [ ] Regulatory reporting systems
- [ ] Trading system inventory (if applicable)
- [ ] Data retention compliance
- [ ] Audit findings (last 2 years)

## Manufacturing Due Diligence Checklist

- [ ] OT asset inventory
- [ ] IT/OT network architecture
- [ ] MES/ERP integration documentation
- [ ] Plant cybersecurity assessment
- [ ] Safety system documentation
- [ ] Change window constraints
- [ ] Remote access architecture

---

# Methodology Concerns & Limitations

## What This Methodology Does Well

| Strength | Explanation |
|----------|-------------|
| **Consistent baseline** | Same inputs → same outputs, every time |
| **Defensible logic** | Every multiplier has documented rationale |
| **Scalable** | Works across deal sizes and industries |
| **Transparent** | Client can see exactly how we got the number |

## What This Methodology Does NOT Capture

| Limitation | Why It Matters | Mitigation |
|------------|----------------|------------|
| **Vendor-specific pricing** | SAP vs Oracle vs NetSuite have different cost structures | Use AI research layer to adjust for specific vendors discovered |
| **Deal-specific complexity** | "47 custom SAP modules" isn't in the formula | AI weight layer identifies complexity signals from documents |
| **Negotiation leverage** | Large buyers get discounts | Note in report that estimates assume standard pricing |
| **Internal capability** | Client may have skills to do work cheaper | Adjust if client has strong internal IT team |
| **Timing/urgency** | Rush jobs cost more | Add 1.2-1.5x for compressed timelines |
| **Scope creep** | Projects grow | Estimates assume defined scope; actuals often 20-30% higher |

## Known Biases in the Methodology

| Bias | Direction | Why |
|------|-----------|-----|
| **Conservatism** | Estimates may be high | We'd rather over-estimate than under-estimate |
| **Mid-market anchor** | May underestimate enterprise complexity | Base costs from mid-market data; enterprise deals often more complex |
| **US-centric** | May miss regional cost differences | Labor costs vary globally; adjust for offshore delivery |
| **Point-in-time** | Costs change over time | Database reflects Jan 2026 pricing; inflation/market shifts not captured |

## When to Override the Formula

The formula is a starting point. Override when:

| Situation | Action |
|-----------|--------|
| **Recent similar deal** | Use actual data from comparable transaction |
| **Client has internal estimate** | Reconcile differences, document reasoning |
| **Major red flag discovered** | Add 20-50% contingency, explain in report |
| **Unusually simple situation** | Reduce by 10-20% with justification |
| **Compressed timeline** | Add 20-50% for rush delivery |
| **Known vendor relationship** | Adjust based on existing pricing agreements |

## Confidence Levels

Not all estimates are equal. Be explicit about confidence:

| Confidence | When to Use | How to Communicate |
|------------|-------------|-------------------|
| **High** | Standard activity, good data, similar past deals | "Based on comparable transactions, we estimate..." |
| **Medium** | Some unknowns, limited comparable data | "Preliminary estimate pending further discovery..." |
| **Low** | Significant unknowns, novel situation | "Order of magnitude estimate only; refine after..." |

## Questions Clients Will Ask (And Honest Answers)

**Q: "How accurate are these estimates?"**
> A: "These are planning estimates based on industry benchmarks, typically within +/- 30% for well-defined scope. Actual costs depend on vendor selection, scope finalization, and execution approach. We recommend budgeting to the high end of the range."

**Q: "Why is your estimate different from [other advisor]?"**
> A: "Different methodologies and assumptions. Our approach is documented - here's exactly how we calculated it. We're happy to reconcile if you share their methodology."

**Q: "Can you guarantee these numbers?"**
> A: "No - these are estimates for planning purposes. Actual costs require vendor quotes and detailed scoping. We can help you get to that level of precision in the next phase."

**Q: "What if the actual cost is higher?"**
> A: "We've documented our assumptions. If scope changes or we discover complexity not visible in due diligence, costs will adjust. That's why we provide ranges, not point estimates."

## Improving the Methodology Over Time

This is a living system. Improve it by:

1. **Tracking actuals vs estimates** - After deals close, compare predicted vs actual costs
2. **Adding deal-specific learnings** - "We missed X in this deal, add to checklist"
3. **Updating base costs annually** - Market rates change
4. **Expanding industry playbooks** - More depth = better estimates
5. **Refining multipliers** - If consistently over/under, adjust factors

## Red Flags That Should Trigger Manual Review

Don't trust the formula blindly when you see:

- [ ] No IT leadership in target (who knows the systems?)
- [ ] M&A history with incomplete integration (hidden complexity)
- [ ] Recent security breach (remediation scope unknown)
- [ ] Key vendor contract expiring soon (forced migration?)
- [ ] Founder-led IT decisions (unconventional architecture)
- [ ] "We're different" claims (sometimes true)
- [ ] Offshore development with unclear documentation
- [ ] Private equity bolt-on history (duct tape architecture)

---

*Document Version: 1.1*
*Last Updated: January 2026*
