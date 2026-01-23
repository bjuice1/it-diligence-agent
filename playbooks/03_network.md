# Network Review Playlist

## Pre-Flight Considerations

**What makes Network different from other IT domains:**

1. **Connectivity = Business operation** - If the network is down, everything is down. Network is foundational - applications, infrastructure, security all depend on it.

2. **Contracts and circuits have long lead times** - Unlike spinning up a cloud VM, network changes (new circuits, WAN redesign) can take 60-120 days. This affects integration timeline planning.

3. **Integration complexity is high** - Merging two networks is one of the hardest Day 1 challenges. IP addressing conflicts, firewall rules, VPN configurations, DNS - all must be resolved before systems can talk.

4. **Hidden dependencies everywhere** - Network diagrams are often outdated or don't exist. The guy who configured the firewall 5 years ago is gone. Tribal knowledge is common.

5. **Security and network are intertwined** - Firewalls, segmentation, VPNs, IDS/IPS - these are network components but have security implications. Don't miss them here or assume Cybersecurity covers it.

6. **Telecom costs are negotiable but sticky** - MPLS circuits, internet, SD-WAN licenses - often in multi-year contracts. Change of control provisions matter.

**What we learned building the bespoke tool:**

- Network documentation quality is typically poor. The more complex the network, the less likely it's documented accurately.
- SD-WAN adoption is a major discriminator. Companies with SD-WAN are easier to integrate than those with traditional MPLS.
- IP address overlap is almost guaranteed in any acquisition. Plan for it.
- The "last mile" to branch offices and remote sites is often the forgotten complexity.

---

## Phase 1: Network Topology Discovery

### Prompt 1.1 - Sites and Locations Inventory
```
Create an inventory of all network locations:

For each site:
- Site name/location
- Site type (Headquarters, Data Center, Regional Office, Branch, Warehouse, Remote)
- Physical address (city/country at minimum)
- Approximate user count
- Connectivity type (MPLS, Internet VPN, SD-WAN, Direct Connect, Leased line)
- Bandwidth (if mentioned)
- Provider/carrier
- Criticality (Critical, High, Medium, Low)

Also identify:
- Total number of sites/locations
- Geographic spread (single country, regional, global)
- Any sites scheduled to close or open

Format as a table: Site Name | Type | Location | Users | Connectivity | Bandwidth | Provider | Criticality
```

### Prompt 1.2 - WAN Architecture Overview
```
Describe the Wide Area Network (WAN) architecture:

1. WAN technology in use:
   - Traditional MPLS
   - SD-WAN (which vendor: Cisco Viptela, VMware VeloCloud, Fortinet, Palo Alto Prisma, other)
   - Internet VPN (site-to-site IPsec)
   - Direct cloud connectivity (AWS Direct Connect, Azure ExpressRoute)
   - Hybrid (combination)

2. Topology:
   - Hub-and-spoke (centralized through HQ/DC)
   - Full mesh
   - Partial mesh
   - Cloud-centric

3. Redundancy:
   - Dual circuits at critical sites?
   - Failover mechanisms
   - SLAs with providers

4. Internet strategy:
   - Centralized internet breakout (all traffic through DC)
   - Local internet breakout at sites
   - Split tunnel VPN

Create a simplified topology description and identify any single points of failure.
```

### Prompt 1.3 - LAN and Data Center Network
```
Document the Local Area Network (LAN) and data center network infrastructure:

1. Core network equipment:
   - Vendor(s) - Cisco, Juniper, Arista, HP/Aruba, other
   - Switch models and age (if mentioned)
   - Router models and age
   - Wireless controllers and access points

2. Data center network:
   - Spine-leaf vs. traditional 3-tier
   - 10G/25G/40G/100G connectivity
   - Network virtualization (NSX, ACI, other)

3. Wireless infrastructure:
   - Vendor (Cisco Meraki, Aruba, Ubiquiti, other)
   - Coverage (all sites, some sites, none)
   - Guest wireless capability

4. Network segmentation:
   - VLANs in use
   - Micro-segmentation
   - Production/Dev/Test separation

Format findings as an inventory table where applicable.
```

---

## Phase 2: IP Addressing and DNS

### Prompt 2.1 - IP Address Space Analysis
```
Document IP addressing information:

1. Internal IP ranges:
   - What RFC1918 ranges are in use? (10.x.x.x, 172.16-31.x.x, 192.168.x.x)
   - Is there a documented IP address management (IPAM) system?
   - Any mention of IP conflicts or overlapping ranges?

2. Public IP addresses:
   - Provider-assigned vs. owned (PI space)
   - Number of public IPs
   - ASN if mentioned (for BGP)

3. Potential overlap concerns:
   - Common ranges that may conflict with buyer (10.0.0.0/8, 192.168.x.x)
   - Any indication of IP renumbering history or capability

4. IPv6:
   - Is IPv6 in use or planned?
   - Dual-stack deployment?

Identify HIGH RISK: Any use of common ranges like 10.0.0.0/24, 10.1.0.0/24, 192.168.1.0/24 that almost certainly conflict with any acquirer.
```

### Prompt 2.2 - DNS and Domain Analysis
```
Document DNS infrastructure:

1. Domain names owned:
   - Primary domain(s)
   - Additional domains
   - Domain registrar

2. DNS hosting:
   - Self-hosted (internal DNS servers)
   - Cloud DNS (Route53, Azure DNS, Cloudflare)
   - ISP DNS
   - Hybrid

3. Internal DNS:
   - Active Directory integrated
   - Split-brain DNS (internal vs. external resolution)
   - DNS servers identified

4. DNS dependencies:
   - What relies on specific DNS names?
   - Hardcoded DNS in applications?

5. Email domains:
   - MX records / email provider
   - SPF/DKIM/DMARC configuration

Note: Domain and DNS changes during integration can break authentication, email, and application access. Flag any complexity.
```

---

## Phase 3: Network Security Components

### Prompt 3.1 - Firewall and Perimeter Security
```
Document firewall and perimeter security infrastructure:

1. Firewall inventory:
   - Vendor(s) - Palo Alto, Cisco (ASA/Firepower), Fortinet, Check Point, other
   - Model and version
   - Location (perimeter, internal, cloud)
   - Management (centralized, per-device)

2. Firewall architecture:
   - Internet edge firewalls
   - Internal segmentation firewalls
   - Cloud firewalls (AWS Security Groups, Azure NSGs, cloud-native firewalls)

3. Remote access:
   - VPN solution (vendor, type - SSL VPN, IPsec, client-based)
   - VPN concentrator capacity
   - Always-on VPN or on-demand?
   - Zero Trust / ZTNA in use?

4. Web security:
   - Web proxy / Secure Web Gateway (Zscaler, Netskope, on-prem proxy)
   - URL filtering
   - SSL inspection

5. DDoS protection:
   - Cloud-based (Cloudflare, Akamai, AWS Shield)
   - On-premise appliances
   - ISP-provided

Format as inventory table: Component | Vendor | Model/Version | Location | Notes
```

### Prompt 3.2 - Network Monitoring and Management
```
Document network monitoring and management tools:

1. Network monitoring:
   - Monitoring platform (SolarWinds, PRTG, Datadog, ThousandEyes, Nagios, other)
   - What's monitored (availability, performance, bandwidth)
   - Alerting configured?

2. Log management:
   - Where do network logs go?
   - Retention period
   - SIEM integration (covered in Cybersecurity)

3. Network management:
   - Configuration management (backup configs, change management)
   - IPAM / DDI solution
   - Network automation (Ansible, Terraform, scripts)

4. Visibility gaps:
   - Any mention of blind spots
   - Shadow IT network devices
   - Unmanaged switches/equipment

Assess network operations maturity: Ad-hoc | Basic Monitoring | Proactive Management | Automated Operations
```

---

## Phase 4: Cloud Connectivity

### Prompt 4.1 - Cloud Network Integration
```
Document network connectivity to cloud environments:

1. AWS connectivity:
   - Direct Connect (dedicated, hosted)
   - VPN (site-to-site, client)
   - Transit Gateway in use?
   - VPC architecture (single, multi-VPC, multi-account)

2. Azure connectivity:
   - ExpressRoute (private peering, Microsoft peering)
   - VPN Gateway
   - Virtual WAN
   - VNet architecture

3. GCP / Other cloud:
   - Cloud Interconnect
   - VPN
   - Shared VPC

4. Multi-cloud / hybrid:
   - How are clouds connected to each other?
   - On-prem to cloud routing
   - DNS resolution across environments

5. SaaS connectivity:
   - Direct internet
   - Through proxy/CASB
   - Private connectivity (e.g., Salesforce Private Connect)

Identify any bottlenecks or complexity in cloud connectivity.
```

---

## Phase 5: Network Contracts and Providers

### Prompt 5.1 - Telecom and Network Contracts
```
Inventory all network-related contracts:

1. WAN/MPLS circuits:
   - Provider
   - Contract term and end date
   - Monthly cost (if mentioned)
   - Sites covered
   - Termination terms

2. Internet circuits:
   - Provider per site
   - Bandwidth
   - Contract terms

3. SD-WAN:
   - Vendor
   - License model (per-device, per-bandwidth)
   - Contract term
   - Support included?

4. Cloud connectivity:
   - Direct Connect / ExpressRoute costs
   - Committed bandwidth
   - Port fees

5. Managed services:
   - Managed network services provider
   - Scope of services
   - Contract term

For each contract:
- Provider | Service | Sites | Term End | Monthly/Annual Cost | Notes

Flag:
- Contracts expiring within 12 months
- Change of control clauses
- Auto-renewal terms
- Minimum commit shortfalls
```

---

## Phase 6: Network Risks and Integration Considerations

### Prompt 6.1 - Network Integration Complexity Assessment
```
Assess network integration complexity for M&A:

1. IP Address overlap risk:
   - Likelihood of IP conflicts (High/Medium/Low)
   - Renumbering complexity
   - NAT requirements

2. Day 1 connectivity requirements:
   - What systems need to communicate across entities on Day 1?
   - What's the minimum viable connectivity?
   - How quickly can it be established?

3. Network technology compatibility:
   - Same WAN vendors or different?
   - Same firewall platforms or different?
   - Will equipment be retained or replaced?

4. DNS and domain integration:
   - Domain consolidation approach
   - Email domain changes
   - Active Directory integration needs

5. Remote access:
   - How will employees access both environments?
   - VPN consolidation or federation?

Rate overall network integration complexity: Low | Medium | High | Very High
```

### Prompt 6.2 - Network Risks Summary
```
Synthesize network-specific risks:

For each risk:
- Risk title
- Description
- Severity (Critical/High/Medium/Low)
- Category:
  - Day 1 Risk (blocks immediate operations)
  - Integration Complexity
  - Cost Exposure
  - Security Gap
  - Operational Risk
- Evidence (source quote)
- Mitigation approach

Common network risks to check:
- Single points of failure (single ISP, single circuit)
- EOL network equipment
- Inadequate bandwidth for growth
- No network segmentation
- IP overlap requiring renumbering
- Contract lock-in or unfavorable terms
- Missing network documentation
- Skills concentration (one network person)
```

### Prompt 6.3 - Network Follow-up Questions
```
Generate follow-up questions for network gaps:

For each question:
- Question text
- Why it matters
- Priority (Must have / Important / Nice to have)
- Who should answer

Essential questions if not answered:
- Complete network diagram (logical and physical)
- IP addressing scheme documentation
- Firewall rule documentation
- Circuit inventory with contracts
- VPN configuration details
- Network equipment inventory with age/support status
- Change management process for network changes
```

---

## Output Checklist

After running this playlist, you should have:
- [ ] Sites and locations inventory with connectivity details
- [ ] WAN architecture understanding (MPLS, SD-WAN, VPN)
- [ ] LAN and data center network equipment inventory
- [ ] IP addressing analysis with overlap risk assessment
- [ ] DNS infrastructure documentation
- [ ] Firewall and security device inventory
- [ ] Cloud connectivity architecture
- [ ] Network contracts with key dates and costs
- [ ] Network integration complexity assessment
- [ ] Prioritized risk list
- [ ] Follow-up questions
