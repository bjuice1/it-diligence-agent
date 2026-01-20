# IT Due Diligence Activity Inventory

**Total Activities: 564**
**Phases Complete: 9 of 10**
**Last Updated: January 2026**

---

## Summary by Phase

| Phase | Description | Activities | Cost Range (1,500 users) |
|-------|-------------|------------|--------------------------|
| 1 | Core Infrastructure | 70 | $2.8M - $8.1M |
| 2 | Network & Security | 67 | $2.4M - $6.3M |
| 3 | Applications | 94 | $9.8M - $32.9M |
| 4 | Data & Migration | 61 | $4.6M - $13.3M |
| 5 | Licensing | 53 | $2.8M - $8.9M |
| 6 | Integration (Buyer) | 50 | $2.2M - $6.4M |
| 7 | Operational Run-Rate | 62 | $5.1M - $20.2M (Annual) |
| 8 | Compliance & Regulatory | 57 | $3.0M - $9.7M |
| 9 | Vendor & Contract | 50 | $4.0M - $13.7M |
| **Total One-Time** | | **502** | **$31.6M - $99.2M** |
| **Total Annual** | | **62** | **$5.1M - $20.2M** |

---

## Phase 1: Core Infrastructure (70 Activities)

### Identity Workstream (25 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| IDN-001 | Identity architecture assessment | Determines current IAM state, gaps vs. target, and effort to establish standalone identity management. Critical for Day 1 access. | Base: $25K-$50K | No |
| IDN-002 | Directory services inventory | Maps all AD forests, domains, trusts, and OUs. Essential to understand identity sprawl and migration scope. | Base: $15K-$35K | No |
| IDN-003 | SSO application mapping | Identifies every app using federated auth. Missing apps means broken access post-cutover. | Per app: $500-$1,500 | No |
| IDN-004 | MFA requirements analysis | Documents current MFA coverage and gaps. Security baseline for standalone entity compliance. | Base: $10K-$25K | No |
| IDN-005 | Identity architecture design | Blueprints target IAM platform, integrations, and migration approach. Foundation for all identity work. | Base: $40K-$100K | No |
| IDN-010 | Azure AD tenant provisioning | Stands up new Entra ID tenant with baseline security. Required for M365 and cloud-native apps. | Base: $30K-$75K | No |
| IDN-011 | Okta org provisioning | Configures standalone Okta tenant for SSO/lifecycle. Alternative to Azure AD for identity-first approach. | Base: $35K-$85K | No |
| IDN-012 | On-premises AD forest standup | Builds new AD forest when cloud-only isn't viable. Needed for legacy apps requiring Kerberos/NTLM. | Base: $50K-$120K | No |
| IDN-013 | Hybrid identity configuration | Connects on-prem AD to cloud IdP via sync. Enables single identity across hybrid environment. | Base: $25K-$60K | No |
| IDN-014 | Identity governance setup | Implements access reviews, entitlement management. Addresses compliance requirements for standalone entity. | Base: $20K-$50K | No |
| IDN-020 | User account migration | Moves user accounts to new directory. Users can't log in to new environment without this. | Per user: $15-$40 | Yes (3-6 mo) |
| IDN-021 | Group and distribution list migration | Transfers security groups and DLs. Preserves access rights and email distribution during transition. | Base + per group: $50-$150 | Yes (2-4 mo) |
| IDN-022 | Service account migration | Moves application service accounts. Apps break without their service identities in new directory. | Per account: $500-$2,000 | Yes (3-6 mo) |
| IDN-023 | Password sync/reset coordination | Manages password continuity during migration. Poor execution means locked-out users and help desk surge. | Per user: $2-$8 | Yes (1-2 mo) |
| IDN-030 | SAML/OIDC SSO reconfiguration - Standard | Repoints standard SaaS apps to new IdP. Common apps like Salesforce, Workday need trust relationship updates. | Per app: $2K-$5K | Yes (2-4 mo) |
| IDN-031 | SAML/OIDC SSO reconfiguration - Complex | Handles custom or legacy federated apps. Complex integrations need extensive testing and vendor coordination. | Per app: $5K-$15K | Yes (3-6 mo) |
| IDN-032 | Legacy application authentication | Addresses apps using LDAP, Kerberos, NTLM. These can't use modern federation and need special handling. | Per app: $8K-$25K | Yes (3-6 mo) |
| IDN-033 | MFA enrollment campaign | Enrolls users in new MFA platform. Required before authentication cutover to maintain security posture. | Per user: $5-$15 | No |
| IDN-034 | Conditional access policy implementation | Configures risk-based access controls. Enforces security policies like device compliance and location restrictions. | Base: $20K-$50K | No |
| IDN-040 | Identity parallel running | Operates both identity systems simultaneously. De-risks cutover by validating new environment under production load. | Base: $30K-$75K | Yes (2-4 mo) |
| IDN-041 | Authentication cutover | Switches users to new identity platform. The big bang moment—all authentication moves to standalone systems. | Base: $25K-$60K | No |
| IDN-042 | Post-migration identity support | Provides hypercare after cutover. Resolves access issues, authentication failures, and edge cases. | Base: $20K-$50K | No |
| IDN-043 | Identity decommissioning | Removes accounts from parent systems. Cleans up access and eliminates lingering security exposure. | Base: $15K-$35K | No |

### Email Workstream (22 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| EML-001 | Email environment assessment | Documents current email platform, mailbox counts, and complexity. Basis for migration planning and licensing. | Base: $20K-$45K | No |
| EML-002 | Mailbox inventory and sizing | Counts mailboxes and measures storage. Drives licensing costs and migration timeline estimates. | Base: $10K-$25K | No |
| EML-003 | Shared resource mapping | Identifies shared mailboxes, rooms, equipment. These need special handling during migration. | Base: $8K-$20K | No |
| EML-004 | Mail flow analysis | Maps connectors, transport rules, and routing. Critical for maintaining mail delivery post-separation. | Base: $12K-$30K | No |
| EML-005 | Email security configuration review | Documents spam, malware, and DLP policies. Ensures security posture transfers to new environment. | Base: $10K-$25K | No |
| EML-006 | Email platform design | Architects target email solution and migration approach. Foundation document for all email work. | Base: $25K-$60K | No |
| EML-010 | M365 tenant email configuration | Configures Exchange Online in new tenant. Sets up the destination for migrated mailboxes. | Base: $25K-$60K | No |
| EML-011 | Google Workspace provisioning | Stands up Gmail environment. Alternative to M365 for organizations choosing Google ecosystem. | Base: $25K-$55K | No |
| EML-012 | Domain configuration | Adds and verifies email domains in new tenant. Users keep their email addresses post-migration. | Base + per domain: $1K-$3K | No |
| EML-013 | Mail routing configuration | Sets up connectors and transport rules. Ensures mail flows correctly between systems during transition. | Base: $15K-$40K | No |
| EML-014 | Email security policy configuration | Implements spam, malware, and policy controls. Protects new environment from email-borne threats. | Base: $15K-$40K | No |
| EML-015 | Email archiving and retention setup | Configures legal hold and retention policies. Addresses compliance and eDiscovery requirements. | Base: $20K-$50K | No |
| EML-020 | Mailbox migration - Staged | Moves mailboxes in batches over time. Lower risk approach allowing course correction during migration. | Per user: $20-$50 | Yes (2-4 mo) |
| EML-021 | Mailbox migration - Cutover | Moves all mailboxes at once. Faster but higher risk—used for smaller populations. | Per user: $15-$35 | Yes (1-2 mo) |
| EML-022 | Archive mailbox migration | Moves historical email archives. Required for compliance and user access to old messages. | Per user: $10-$30 | Yes (2-4 mo) |
| EML-023 | Public folder migration | Migrates shared public folder content. Legacy collaboration data users still depend on. | Base: $20K-$60K | Yes (2-4 mo) |
| EML-024 | Shared mailbox migration | Moves team and functional mailboxes. Business processes break without these shared resources. | Per mailbox: $200-$500 | Yes (2-3 mo) |
| EML-025 | Calendar and contact migration | Transfers calendars and contact lists. Users lose meeting history and contacts without this. | Per user: $5-$15 | Yes (1-2 mo) |
| EML-026 | Resource mailbox migration | Moves room and equipment calendars. Meeting room booking breaks without resource mailbox migration. | Per resource: $150-$400 | Yes (1-2 mo) |
| EML-030 | Cross-tenant free/busy configuration | Enables calendar visibility across tenants. Users can see availability during coexistence period. | Base: $15K-$35K | Yes (3-6 mo) |
| EML-031 | Mail forwarding configuration | Routes mail between old and new addresses. Ensures no lost email during transition period. | Base: $8K-$20K | Yes (3-6 mo) |
| EML-032 | Address book synchronization | Syncs GAL between environments. Users can find each other during coexistence. | Base: $10K-$30K | Yes (3-6 mo) |
| EML-040 | MX record cutover | Switches DNS to route mail to new environment. The moment inbound email starts flowing to standalone systems. | Base: $10K-$25K | No |
| EML-041 | Email client reconfiguration | Repoints Outlook/mobile clients to new server. Users can't access new mailbox without client update. | Per user: $5-$20 | No |
| EML-042 | Post-migration email support | Provides hypercare for email issues. Resolves missing mail, calendar problems, and client issues. | Base: $15K-$40K | No |

### Infrastructure Workstream (23 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| INF-001 | Infrastructure discovery and inventory | Catalogs all servers, VMs, and storage. Can't migrate what you don't know exists. | Base: $25K-$60K | No |
| INF-002 | Application-to-infrastructure mapping | Links apps to their underlying infrastructure. Essential for sequencing migrations without breaking apps. | Base: $20K-$50K | No |
| INF-003 | Storage assessment and planning | Measures storage volumes and growth rates. Drives target storage sizing and migration approach. | Base: $15K-$40K | No |
| INF-004 | Backup and DR assessment | Evaluates current backup and recovery capabilities. Identifies gaps before standalone entity goes live. | Base: $15K-$35K | No |
| INF-005 | Target infrastructure architecture design | Blueprints the standalone infrastructure environment. Foundation for all build and migration work. | Base: $40K-$100K | No |
| INF-010 | Cloud landing zone deployment | Builds foundational cloud environment (networking, security, governance). Required before any cloud migrations. | Base: $75K-$200K | No |
| INF-011 | On-premises datacenter buildout | Provisions physical datacenter infrastructure. Required when workloads can't move to cloud. | Base: $150K-$400K | No |
| INF-012 | Network connectivity setup | Establishes connectivity to new environment. VMs can't be reached without network in place. | Base: $30K-$80K | No |
| INF-013 | Security baseline implementation | Configures security controls per enterprise standards. Ensures compliant infrastructure from Day 1. | Base: $25K-$60K | No |
| INF-014 | Monitoring and alerting setup | Deploys monitoring tools and alert rules. Operations team is blind without visibility into systems. | Base: $20K-$50K | No |
| INF-015 | Backup infrastructure deployment | Implements backup solution for new environment. Data loss risk until backup protection is active. | Base: $30K-$80K | No |
| INF-016 | Disaster recovery setup | Configures DR capabilities for critical systems. Business continuity depends on recovery options. | Base: $50K-$150K | No |
| INF-020 | VM migration - Lift and shift | Moves VMs as-is to new environment. Fastest migration approach with minimal application changes. | Per VM: $500-$1,500 | Yes (3-6 mo) |
| INF-021 | VM migration - Replatform | Migrates VMs with OS/platform upgrades. Addresses technical debt during migration. | Per VM: $1K-$3K | Yes (3-6 mo) |
| INF-022 | Physical server migration | Converts physical servers or relocates hardware. More complex than VM migration. | Per server: $2K-$6K | Yes (3-6 mo) |
| INF-023 | Database migration | Moves databases with schema and data integrity. Most sensitive migration—data loss is catastrophic. | Per database: $3K-$15K | Yes (3-6 mo) |
| INF-024 | Storage migration | Transfers data volumes to new storage. Large data volumes take significant time and bandwidth. | Per TB: $200-$600 | Yes (3-6 mo) |
| INF-025 | Application migration | Moves complete application stacks. Validates app functionality in new environment. | Per app: $5K-$25K | Yes (3-6 mo) |
| INF-030 | Operations runbook development | Documents operational procedures for new environment. Operations team needs playbooks for Day 2. | Base: $20K-$50K | No |
| INF-031 | Operations team training | Trains staff on new infrastructure platform. Team can't support what they don't understand. | Base: $15K-$40K | No |
| INF-032 | Support transition | Transfers operational support to steady-state team. Moves from project mode to BAU operations. | Base: $15K-$35K | No |
| INF-033 | Legacy infrastructure decommissioning | Shuts down and removes old systems. Eliminates ongoing costs and security exposure from legacy. | Per server: $200-$500 | No |

---

## Phase 2: Network & Security (67 Activities)

### Network Workstream (25 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| NET-001 | Network architecture assessment | Maps current WAN, LAN, and connectivity. Foundation for designing standalone network topology. | Base: $30K-$75K | No |
| NET-002 | WAN circuit inventory | Documents all network circuits and contracts. Identifies what transfers, terminates, or needs replacement. | Base: $15K-$35K | No |
| NET-003 | IP addressing and DNS analysis | Audits IP schemes and DNS zones. Overlapping IPs cause routing failures; DNS errors break applications. | Base: $20K-$45K | No |
| NET-004 | Firewall rule analysis | Reviews firewall policies for separation impact. Identifies rules that need modification or recreation. | Base + per site: $3K-$8K | No |
| NET-005 | Network target architecture design | Architects standalone network environment. Blueprint for all network build and migration activities. | Base: $50K-$125K | No |
| NET-010 | MPLS circuit provisioning | Orders and installs private WAN circuits. Long lead times make this critical path for site connectivity. | Per site: $8K-$20K | Yes (3-6 mo) |
| NET-011 | SD-WAN deployment | Implements software-defined WAN overlay. Modern alternative to MPLS with faster deployment. | Base + per site: $3K-$8K | Yes (2-4 mo) |
| NET-012 | Internet circuit provisioning | Orders dedicated internet connections. Required for cloud access and backup connectivity. | Per site: $2K-$6K | Yes (2-4 mo) |
| NET-013 | WAN circuit migration/cutover | Transitions sites to new network. The moment each location moves off parent network. | Per site: $2K-$5K | Yes (1-3 mo) |
| NET-020 | LAN switch configuration | Configures local network switching. Sites need functional LANs before users can work. | Per site: $5K-$15K | No |
| NET-021 | VLAN segmentation implementation | Implements network segmentation. Separates traffic types for security and performance. | Per site: $3K-$8K | No |
| NET-022 | Wireless infrastructure deployment | Deploys enterprise WiFi. Mobile workforce depends on wireless connectivity. | Per site: $8K-$25K | No |
| NET-023 | Network access control (NAC) implementation | Controls what devices can access network. Prevents unauthorized devices from connecting. | Base: $35K-$90K | No |
| NET-030 | Firewall deployment | Installs perimeter and internal firewalls. Primary network security control for standalone entity. | Base + per site: $5K-$15K | No |
| NET-031 | Firewall rule migration | Recreates firewall policies in new environment. Business apps break without proper firewall rules. | Base: $25K-$75K | Yes (2-4 mo) |
| NET-032 | IDS/IPS implementation | Deploys intrusion detection/prevention. Identifies and blocks network-based attacks. | Base: $30K-$80K | No |
| NET-033 | Network segmentation enforcement | Implements micro-segmentation controls. Limits lateral movement if breach occurs. | Base: $50K-$150K | No |
| NET-040 | DNS infrastructure deployment | Stands up DNS servers for new environment. Name resolution fails without DNS infrastructure. | Base: $20K-$50K | No |
| NET-041 | DNS zone separation | Splits shared DNS zones for standalone entity. Users can't reach resources without DNS records. | Base + per domain: $2K-$5K | Yes (2-4 mo) |
| NET-042 | DHCP infrastructure deployment | Deploys IP address assignment services. Devices can't get network addresses without DHCP. | Base + per site: $1K-$3K | No |
| NET-043 | NTP/time services configuration | Configures time synchronization. Time skew causes authentication failures and log correlation issues. | Base: $5K-$15K | No |
| NET-044 | Certificate services deployment | Builds PKI for internal certificates. Apps and services need certificates for encryption. | Base: $30K-$80K | No |
| NET-050 | Network monitoring deployment | Implements network visibility tools. Ops team can't troubleshoot what they can't see. | Base: $20K-$50K | No |
| NET-051 | Network documentation and runbooks | Documents network design and procedures. Knowledge transfer for ongoing network operations. | Base: $15K-$35K | No |

### Security Workstream (28 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| SEC-001 | Security architecture assessment | Evaluates current security posture and controls. Identifies gaps that standalone entity must address. | Base: $35K-$85K | No |
| SEC-002 | Security tool inventory | Catalogs all security products in use. Determines what transfers, what's shared, what needs replacement. | Base: $15K-$35K | No |
| SEC-003 | Compliance requirements mapping | Maps regulatory and contractual security requirements. Drives must-have controls for standalone entity. | Base: $25K-$60K | No |
| SEC-004 | Security architecture design | Designs security architecture for new environment. Blueprint for all security implementations. | Base: $50K-$120K | No |
| SEC-010 | EDR platform deployment | Deploys endpoint detection and response. Critical threat detection capability for all endpoints. | Base + per endpoint: $10-$30 | Yes (2-4 mo) |
| SEC-011 | Antivirus/antimalware migration | Moves endpoint protection to new platform. Endpoints unprotected without malware defense. | Per endpoint: $5-$15 | Yes (2-4 mo) |
| SEC-012 | Device encryption enforcement | Implements disk encryption on endpoints. Protects data if devices are lost or stolen. | Base + per endpoint: $5-$15 | No |
| SEC-013 | Mobile device management deployment | Deploys MDM for phones and tablets. Controls corporate data on mobile devices. | Base + per device: $10-$25 | Yes (2-4 mo) |
| SEC-014 | Endpoint hardening implementation | Applies security configurations to endpoints. Reduces attack surface on workstations and servers. | Base: $30K-$70K | No |
| SEC-020 | SIEM platform deployment | Implements security event monitoring. Central visibility into security events across environment. | Base: $75K-$200K | Yes (3-6 mo) |
| SEC-021 | Log aggregation configuration | Configures log collection from all sources. SIEM is useless without comprehensive log feeds. | Base: $25K-$60K | No |
| SEC-022 | Security alert tuning | Tunes detection rules to reduce false positives. SOC drowns in noise without proper tuning. | Base: $20K-$50K | No |
| SEC-023 | SOC procedures development | Documents security operations playbooks. Team needs procedures to respond to incidents consistently. | Base: $25K-$60K | No |
| SEC-024 | Security orchestration (SOAR) deployment | Automates security response workflows. Faster response through automated playbook execution. | Base: $50K-$150K | No |
| SEC-030 | Vulnerability scanner deployment | Deploys vulnerability assessment tools. Can't fix vulnerabilities you don't know about. | Base: $30K-$75K | No |
| SEC-031 | Baseline vulnerability assessment | Scans environment to establish vulnerability baseline. Identifies existing security debt. | Base: $20K-$50K | No |
| SEC-032 | Vulnerability remediation program | Establishes process to address vulnerabilities. Ongoing program to reduce security exposure. | Base: $25K-$60K | No |
| SEC-033 | Patch management implementation | Implements systematic patching process. Unpatched systems are primary attack vector. | Base: $30K-$70K | No |
| SEC-040 | Privileged access management (PAM) deployment | Deploys privileged credential management. Controls and audits admin access to critical systems. | Base: $75K-$200K | Yes (3-6 mo) |
| SEC-041 | Service account vault implementation | Secures application service credentials. Prevents credential theft and enables rotation. | Base + per account: $100-$300 | Yes (2-4 mo) |
| SEC-042 | Access review implementation | Implements periodic access certification. Ensures access rights remain appropriate over time. | Base: $25K-$60K | No |
| SEC-043 | Identity governance platform deployment | Deploys IGA for access lifecycle. Automates joiner/mover/leaver and access requests. | Base: $100K-$300K | No |
| SEC-050 | Data loss prevention deployment | Implements DLP to prevent data exfiltration. Protects sensitive data from leaving organization. | Base: $50K-$150K | Yes (3-6 mo) |
| SEC-051 | Data classification implementation | Implements data labeling and classification. DLP and protection policies depend on classification. | Base: $30K-$75K | No |
| SEC-052 | Encryption key management | Deploys enterprise key management. Centralizes and secures cryptographic keys. | Base: $40K-$100K | No |
| SEC-060 | Security gap remediation assessment | Identifies priority security improvements. Focuses limited resources on highest-risk gaps. | Base: $25K-$60K | No |
| SEC-061 | Security quick wins implementation | Implements fast security improvements. Addresses critical gaps before full program completion. | Base: $20K-$50K | No |
| SEC-062 | Penetration testing | Tests security through simulated attacks. Validates controls actually work against real threats. | Base: $40K-$100K | No |

### Perimeter Workstream (14 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| PER-001 | Perimeter security assessment | Reviews current internet edge security. Identifies what protections need replication for standalone. | Base: $25K-$55K | No |
| PER-002 | Perimeter architecture design | Designs internet edge security stack. Blueprint for protecting standalone entity's internet boundary. | Base: $35K-$80K | No |
| PER-010 | VPN infrastructure deployment | Deploys remote access VPN solution. Remote workers can't connect securely without VPN. | Base: $30K-$80K | Yes (2-4 mo) |
| PER-011 | VPN user migration | Moves users to new VPN platform. Remote access breaks during transition without coordination. | Per user: $5-$15 | Yes (2-4 mo) |
| PER-012 | Site-to-site VPN configuration | Creates encrypted tunnels between sites. Secure connectivity for sites without private WAN. | Per site: $3K-$8K | Yes (2-4 mo) |
| PER-013 | Zero trust network access (ZTNA) deployment | Implements identity-based access. Modern alternative to VPN with better security model. | Base + per user: $10-$30 | Yes (2-4 mo) |
| PER-020 | Secure web gateway deployment | Filters and inspects web traffic. Protects users from web-based threats and enforces policy. | Base: $35K-$90K | Yes (2-4 mo) |
| PER-021 | Web proxy configuration | Configures web filtering policies. Controls what websites users can access from corporate network. | Base: $15K-$40K | No |
| PER-022 | Cloud access security broker (CASB) deployment | Provides visibility into cloud app usage. Controls data flowing to/from SaaS applications. | Base: $50K-$150K | Yes (3-6 mo) |
| PER-023 | DNS security deployment | Filters malicious DNS requests. Blocks connections to known-bad domains at DNS layer. | Base: $15K-$40K | No |
| PER-030 | Email security gateway deployment | Deploys email filtering and protection. Blocks spam, malware, and phishing before reaching users. | Base + per user: $3-$10 | Yes (2-4 mo) |
| PER-031 | Email authentication configuration | Configures SPF, DKIM, DMARC records. Prevents email spoofing and improves deliverability. | Base + per domain: $1K-$3K | No |
| PER-032 | Anti-phishing protection deployment | Implements advanced phishing defense. Protects users from credential theft attempts. | Base: $20K-$50K | No |
| PER-040 | SASE platform deployment | Deploys converged network/security platform. Combines SD-WAN, SWG, CASB, ZTNA in unified solution. | Base + per user: $20-$60 | Yes (3-6 mo) |
| PER-041 | Perimeter service migration | Transitions perimeter services to new stack. The cutover from parent security services. | Base: $40K-$100K | Yes (2-4 mo) |

---

## Phase 3: Applications (94 Activities)

### ERP Workstream (21 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| ERP-001 | ERP landscape assessment | Documents ERP systems, modules, and usage. Foundation for planning most complex separation workstream. | Base: $50K-$125K | No |
| ERP-002 | ERP data segmentation analysis | Determines how to split shared ERP data. Critical for legal entity separation and financial close. | Base: $40K-$100K | No |
| ERP-003 | ERP integration mapping | Maps all ERP interfaces and dependencies. Integrations break without careful migration planning. | Base + per integration: $1K-$3K | No |
| ERP-004 | ERP customization inventory | Catalogs custom code, reports, forms. Custom development must migrate or be rebuilt. | Base: $30K-$80K | No |
| ERP-005 | ERP license entitlement analysis | Determines license transfer rights and gaps. Standalone entity needs valid ERP licenses. | Base: $20K-$50K | No |
| ERP-006 | ERP separation strategy design | Architects ERP separation approach (copy, carve, new build). Highest-stakes decision in most separations. | Base: $75K-$200K | No |
| ERP-010 | SAP system copy and carve | Creates standalone SAP from parent system. Fastest SAP separation path but technically complex. | Base: $200K-$500K | Yes (6-12 mo) |
| ERP-011 | SAP new instance implementation | Builds new SAP from scratch. Clean slate but longest timeline and highest cost. | Base: $500K-$2M | Yes (12-24 mo) |
| ERP-012 | SAP data migration | Extracts and loads business data to new SAP. Financial history and master data required for operations. | Base: $100K-$300K | Yes (6-12 mo) |
| ERP-013 | SAP integration rebuild | Recreates interfaces in new SAP environment. Business processes depend on working integrations. | Base + per integration: $5K-$20K | Yes (6-12 mo) |
| ERP-014 | SAP custom development migration | Migrates ABAP custom code and enhancements. Custom functionality lost without code migration. | Base: $75K-$250K | Yes (6-12 mo) |
| ERP-020 | Oracle EBS/Cloud instance separation | Separates Oracle ERP environment. Similar complexity to SAP with Oracle-specific considerations. | Base: $200K-$600K | Yes (6-12 mo) |
| ERP-021 | Oracle data extraction and migration | Moves Oracle ERP data to standalone system. Critical financial and operational data migration. | Base: $100K-$300K | Yes (6-12 mo) |
| ERP-030 | NetSuite account separation | Creates separate NetSuite instance. Cloud ERP with simpler separation than on-premises. | Base: $75K-$200K | Yes (3-6 mo) |
| ERP-031 | Dynamics 365 F&O tenant separation | Separates Microsoft F&O environment. Cloud-native but still complex data separation. | Base: $100K-$300K | Yes (6-12 mo) |
| ERP-032 | Dynamics GP/NAV migration | Migrates legacy Microsoft ERP. Often opportunity to modernize to D365 during separation. | Base: $50K-$150K | Yes (3-6 mo) |
| ERP-040 | ERP functional testing | Tests all ERP business processes work. Finance, procurement, order-to-cash must all function. | Base: $50K-$150K | No |
| ERP-041 | ERP integration testing | Validates ERP interfaces work end-to-end. Catches integration failures before go-live. | Base: $40K-$100K | No |
| ERP-042 | ERP performance testing | Validates ERP performs under load. Month-end close and peak processing must complete in time. | Base: $30K-$80K | No |
| ERP-043 | ERP user acceptance testing | Business users validate ERP functionality. Final sign-off that system meets business needs. | Base: $25K-$75K | No |
| ERP-044 | ERP cutover planning and execution | Plans and executes ERP go-live. The most critical cutover—business stops without ERP. | Base: $50K-$150K | No |
| ERP-045 | ERP hypercare support | Provides intensive post-go-live support. Resolves issues during critical first weeks of operation. | Base: $40K-$120K | No |

### CRM Workstream (15 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| CRM-001 | CRM landscape assessment | Documents CRM platforms and usage patterns. Basis for customer data separation strategy. | Base: $25K-$60K | No |
| CRM-002 | CRM data ownership analysis | Determines which customer records belong to each entity. Sales can't operate without their customers. | Base: $20K-$50K | No |
| CRM-003 | CRM separation strategy design | Plans CRM split or new implementation approach. Drives timeline and cost for customer data transition. | Base: $30K-$75K | No |
| CRM-010 | Salesforce org provisioning | Creates new Salesforce organization. Destination environment for migrated CRM data. | Base: $40K-$100K | No |
| CRM-011 | Salesforce configuration migration | Moves customizations, workflows, page layouts. Sales processes break without configuration migration. | Base: $50K-$150K | Yes (3-6 mo) |
| CRM-012 | Salesforce data migration | Transfers accounts, contacts, opportunities, history. Sales team loses visibility without customer data. | Base + per record: $0.05-$0.20 | Yes (3-6 mo) |
| CRM-013 | Salesforce integration rebuild | Recreates marketing, ERP, and service integrations. CRM value depends on connected data flows. | Base + per integration: $3K-$12K | Yes (3-6 mo) |
| CRM-014 | Salesforce AppExchange app migration | Moves or replaces third-party apps. Extended CRM functionality depends on these apps. | Per app: $2K-$8K | No |
| CRM-020 | Dynamics 365 CE environment provisioning | Stands up Microsoft CRM environment. Alternative CRM platform for Microsoft-centric shops. | Base: $35K-$90K | No |
| CRM-021 | Dynamics CRM solution migration | Migrates Dynamics customizations and workflows. Custom sales processes encoded in Dynamics solutions. | Base: $40K-$120K | Yes (3-6 mo) |
| CRM-022 | Dynamics CRM data migration | Transfers CRM data to new Dynamics environment. Complete customer relationship history needed. | Base: $30K-$80K | Yes (3-6 mo) |
| CRM-030 | HubSpot account separation | Separates HubSpot marketing and CRM. Mid-market CRM with marketing automation integration. | Base: $20K-$50K | Yes (2-4 mo) |
| CRM-031 | Zoho CRM separation | Separates Zoho CRM instance. SMB CRM platform requiring data and config separation. | Base: $15K-$40K | Yes (2-4 mo) |
| CRM-040 | CRM testing and validation | Validates CRM functions correctly post-migration. Sales process integrity verification. | Base: $25K-$60K | No |
| CRM-041 | CRM user training | Trains sales team on new CRM environment. Productivity depends on user adoption. | Base + per user: $50-$150 | No |
| CRM-042 | CRM cutover and hypercare | Executes CRM transition and provides support. Critical period for sales continuity. | Base: $20K-$50K | No |

### HR/HCM Workstream (17 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| HCM-001 | HR/HCM landscape assessment | Documents HR systems, payroll, benefits, time tracking. Foundation for people systems separation. | Base: $30K-$75K | No |
| HCM-002 | HR data separation analysis | Determines employee data ownership and migration. Can't pay employees without proper HR records. | Base: $20K-$50K | No |
| HCM-003 | Payroll and benefits analysis | Reviews payroll processing and benefits programs. Critical for Day 1—employees must be paid. | Base: $25K-$60K | No |
| HCM-004 | HR/HCM separation strategy design | Plans HR system separation approach. Drives timeline for payroll independence. | Base: $35K-$85K | No |
| HCM-010 | Workday tenant provisioning | Creates new Workday HCM tenant. Enterprise-grade cloud HR platform implementation. | Base: $100K-$300K | Yes (6-12 mo) |
| HCM-011 | Workday configuration and customization | Configures Workday business processes and integrations. HR processes encoded in Workday configuration. | Base: $150K-$400K | Yes (6-12 mo) |
| HCM-012 | Workday data migration | Migrates employee records and history. Complete employee lifecycle data needed for HR operations. | Base + per employee: $100-$300 | Yes (6-12 mo) |
| HCM-020 | ADP implementation | Implements ADP payroll and HR solution. Leading payroll provider for mid-market companies. | Base + per employee: $30-$100 | Yes (3-6 mo) |
| HCM-021 | ADP data migration | Migrates employee data to ADP. Payroll runs depend on accurate employee master data. | Base + per employee: $50-$150 | Yes (3-6 mo) |
| HCM-030 | UKG Pro implementation | Implements UKG workforce management solution. Comprehensive HCM for complex workforce needs. | Base + per employee: $40-$120 | Yes (6-9 mo) |
| HCM-031 | UKG time and attendance setup | Configures time tracking and scheduling. Hourly workers can't be paid without time capture. | Base: $30K-$80K | Yes (3-6 mo) |
| HCM-040 | SAP SuccessFactors tenant provisioning | Creates SuccessFactors HCM environment. Cloud HCM for SAP-centric organizations. | Base: $100K-$250K | Yes (6-12 mo) |
| HCM-041 | SuccessFactors Employee Central migration | Migrates core HR data to SuccessFactors. Employee records and org structure transfer. | Base + per employee: $75-$200 | Yes (6-12 mo) |
| HCM-050 | Payroll provider setup | Establishes standalone payroll processing. Non-negotiable—employees must receive paychecks. | Base + per employee: $20-$60 | Yes (3-6 mo) |
| HCM-051 | Benefits administration setup | Configures benefits enrollment and management. Employees need health insurance and benefits access. | Base + per employee: $15-$50 | Yes (3-6 mo) |
| HCM-052 | 401(k)/retirement plan setup | Establishes retirement plan with new provider. Employee retirement contributions must continue. | Base: $20K-$50K | Yes (3-6 mo) |
| HCM-060 | HR/HCM parallel payroll testing | Runs parallel payroll to validate accuracy. Catches errors before real paychecks are affected. | Base: $20K-$50K | Yes (2-3 mo) |
| HCM-061 | HR/HCM cutover and go-live | Executes HR system transition. The moment employee data moves to standalone systems. | Base: $25K-$60K | No |
| HCM-062 | HR/HCM hypercare support | Provides intensive HR support post-cutover. Resolves payroll and benefits issues immediately. | Base: $20K-$50K | No |

### Custom Applications Workstream (19 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| APP-001 | Custom application portfolio assessment | Inventories all custom and bespoke applications. Many separations discover unknown business-critical apps late. | Base: $30K-$75K | No |
| APP-002 | Application disposition analysis | Decides migrate, retire, replace for each app. Not all apps should move—some should be sunset. | Base + per app: $500-$2K | No |
| APP-003 | Application separation strategy | Plans migration approach for application portfolio. Sequences migrations to minimize business disruption. | Base: $40K-$100K | No |
| APP-010 | Simple application migration | Moves straightforward applications. Basic web apps or tools with minimal dependencies. | Per app: $5K-$15K | Yes (2-4 mo) |
| APP-011 | Moderate application migration | Migrates apps with some complexity. Applications with databases, integrations, or custom code. | Per app: $15K-$50K | Yes (3-6 mo) |
| APP-012 | Complex application migration | Handles highly complex applications. Mission-critical apps with many dependencies and integrations. | Per app: $50K-$150K | Yes (6-12 mo) |
| APP-013 | Legacy application modernization | Modernizes outdated applications during migration. Often necessary when legacy tech can't move as-is. | Per app: $75K-$300K | Yes (6-18 mo) |
| APP-020 | Application retirement - Simple | Decommissions simple applications. Eliminates apps no longer needed by standalone entity. | Per app: $3K-$10K | No |
| APP-021 | Application retirement - Complex | Retires complex apps with data retention needs. Requires data archival and compliance considerations. | Per app: $10K-$35K | Yes (2-4 mo) |
| APP-030 | Integration platform standup | Deploys integration middleware (MuleSoft, Boomi). Foundation for connecting applications in new environment. | Base: $50K-$150K | No |
| APP-031 | API gateway deployment | Implements API management platform. Controls and secures API traffic between applications. | Base: $30K-$80K | No |
| APP-032 | Integration rebuild - Per integration | Recreates application interfaces. Business processes depend on data flowing between systems. | Per integration: $3K-$15K | Yes (3-6 mo) |
| APP-040 | Application testing coordination | Coordinates testing across application portfolio. Ensures all apps work together after migration. | Base: $25K-$75K | No |
| APP-041 | End-to-end process testing | Tests complete business processes across apps. Validates order-to-cash, procure-to-pay work end-to-end. | Base: $30K-$80K | No |
| APP-050 | Application technology assessment | Evaluates app technology stack and health. Identifies technical debt and modernization opportunities. | Base + per app: $2K-$6K | No |
| APP-051 | Application refactoring | Restructures application code for new environment. Necessary when apps need architectural changes to migrate. | Per app: $25K-$100K | Yes (3-6 mo) |

### SaaS Workstream (22 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| SAS-001 | SaaS discovery and inventory | Catalogs all cloud applications in use. Shadow IT means many SaaS apps are unknown to IT. | Base: $20K-$50K | No |
| SAS-002 | SaaS contract analysis | Reviews SaaS contracts for transfer rights. Many SaaS agreements restrict assignment without consent. | Base + per contract: $500-$1,500 | No |
| SAS-003 | SaaS data classification | Identifies sensitive data in SaaS applications. Drives data handling requirements during separation. | Base + per app: $500-$2K | No |
| SAS-004 | SaaS separation strategy | Plans SaaS transition approach per application. Determines new accounts, transfers, or replacements. | Base: $20K-$50K | No |
| SAS-010 | SaaS account provisioning - Simple | Sets up simple SaaS accounts. Basic apps with straightforward configuration. | Per app: $1K-$3K | Yes (1-3 mo) |
| SAS-011 | SaaS account provisioning - Complex | Provisions complex SaaS with customization. Enterprise apps requiring significant configuration. | Per app: $5K-$20K | Yes (2-4 mo) |
| SAS-012 | SaaS user provisioning | Creates user accounts in new SaaS tenants. Users need access to do their jobs. | Per user: $5-$20 + per app: $500-$2K | Yes (2-4 mo) |
| SAS-013 | SaaS data migration | Moves data between SaaS accounts. Historical data and configurations must transfer. | Per app: $3K-$15K | Yes (2-4 mo) |
| SAS-014 | SaaS SSO reconfiguration | Points SaaS apps to new identity provider. Users can't log in without SSO reconfiguration. | Per app: $1K-$4K | Yes (2-4 mo) |
| SAS-020 | SaaS contract assignment | Transfers SaaS contracts to new entity. Requires vendor consent per contract terms. | Per contract: $1K-$4K | No |
| SAS-021 | SaaS new contract negotiation | Negotiates new SaaS agreements. Required when contracts don't allow assignment. | Per contract: $2K-$8K | No |
| SAS-022 | SaaS contract termination | Terminates unneeded SaaS subscriptions. Eliminates ongoing costs for unused services. | Per contract: $500-$2K | No |
| SAS-030 | SaaS data export | Extracts data from SaaS applications. Required for migration or archival purposes. | Per app: $1K-$5K | Yes (1-3 mo) |
| SAS-031 | SaaS historical data archival | Archives historical SaaS data. Compliance may require retention after migration. | Per app: $2K-$8K | No |
| SAS-032 | SaaS data deletion verification | Confirms data deleted from old accounts. Privacy compliance requires deletion confirmation. | Per app: $500-$2K | No |
| SAS-040 | Collaboration tools migration (Slack/Teams) | Migrates team communication platforms. Chat history and channels critical for team continuity. | Base + per user: $10-$30 | Yes (3-6 mo) |
| SAS-041 | Project management tools migration | Moves project tracking tools. Active projects can't afford data loss or downtime. | Base + per user: $15-$40 | Yes (2-4 mo) |
| SAS-042 | Document management migration | Transfers document repositories. Business documents and collaboration content must migrate. | Base + per user: $10-$25 | Yes (3-6 mo) |
| SAS-043 | Business intelligence tools migration | Migrates BI/analytics platforms. Reports and dashboards business relies on for decisions. | Base: $30K-$100K | Yes (3-6 mo) |
| SAS-050 | SaaS license true-up | Reconciles SaaS license counts. Avoids compliance issues from over/under licensing. | Base + per app: $1K-$4K | No |
| SAS-051 | SaaS license optimization | Right-sizes SaaS subscriptions. Identifies cost savings from unused licenses. | Base: $15K-$40K | No |

---

## Phase 4: Data & Migration (61 Activities)

### Database Workstream (22 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| DAT-001 | Database landscape assessment | Inventories all database instances and types. Can't migrate databases you don't know exist. | Base: $30K-$75K | No |
| DAT-002 | Database schema analysis | Documents database structures and objects. Required for planning migration approach. | Base + per database: $1.5K-$4K | No |
| DAT-003 | Database dependency mapping | Maps application and reporting dependencies. Sequencing migrations requires understanding dependencies. | Base + per database: $1K-$3K | No |
| DAT-004 | Data classification and sensitivity analysis | Identifies PII, financial, and regulated data. Drives security and compliance handling during migration. | Base + per database: $2K-$5K | No |
| DAT-005 | Database separation strategy design | Plans migration approach for database portfolio. Foundation for all data migration work. | Base: $40K-$100K | No |
| DAT-010 | SQL Server database migration - Simple | Moves basic SQL Server databases. Straightforward migrations with minimal complexity. | Per database: $3K-$8K | Yes (2-4 mo) |
| DAT-011 | SQL Server database migration - Complex | Migrates complex SQL Server with dependencies. Large databases with stored procedures and integrations. | Per database: $10K-$30K | Yes (3-6 mo) |
| DAT-012 | SQL Server Always On/clustering migration | Migrates high-availability SQL configurations. Business-critical databases requiring zero downtime. | Per database: $15K-$40K | Yes (3-6 mo) |
| DAT-013 | SQL Server to Azure SQL migration | Moves SQL Server to cloud PaaS. Modernization opportunity with managed database service. | Per database: $8K-$25K | Yes (3-6 mo) |
| DAT-020 | Oracle database migration - Simple | Migrates basic Oracle databases. Simpler Oracle migrations with standard features. | Per database: $5K-$15K | Yes (3-6 mo) |
| DAT-021 | Oracle database migration - Complex | Handles complex Oracle with RAC/partitioning. Enterprise Oracle requiring specialized expertise. | Per database: $20K-$60K | Yes (6-12 mo) |
| DAT-022 | Oracle to PostgreSQL migration | Converts Oracle to open-source PostgreSQL. Eliminates expensive Oracle licensing. | Per database: $25K-$75K | Yes (6-12 mo) |
| DAT-023 | Oracle to AWS RDS migration | Moves Oracle to cloud managed service. Cloud database with reduced operational burden. | Per database: $15K-$45K | Yes (3-6 mo) |
| DAT-030 | MySQL/MariaDB database migration | Migrates MySQL or MariaDB databases. Common open-source database platform migrations. | Per database: $2K-$8K | Yes (2-4 mo) |
| DAT-031 | PostgreSQL database migration | Moves PostgreSQL databases to new environment. Growing enterprise open-source database platform. | Per database: $2K-$8K | Yes (2-4 mo) |
| DAT-032 | NoSQL database migration (MongoDB, Cosmos) | Migrates document/NoSQL databases. Modern applications often use non-relational databases. | Per database: $5K-$15K | Yes (2-4 mo) |
| DAT-040 | Data warehouse separation assessment | Analyzes data warehouse separation approach. Reporting and analytics depend on warehouse availability. | Base: $30K-$80K | No |
| DAT-041 | Data warehouse migration | Moves enterprise data warehouse. Large-scale data migration with ETL and reporting. | Base: $100K-$300K | Yes (6-12 mo) |
| DAT-042 | Cloud data platform migration (Snowflake/Databricks) | Migrates cloud analytics platforms. Modern data stack components require careful migration. | Base + per TB: $500-$1,500 | Yes (6-12 mo) |
| DAT-050 | Database migration validation | Validates data integrity post-migration. Data corruption is catastrophic—must verify. | Base + per database: $1.5K-$4K | No |
| DAT-051 | Database cutover execution | Executes final database transition. The moment applications point to new databases. | Base + per database: $2K-$6K | No |

### File Data Workstream (17 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| FIL-001 | File data landscape assessment | Inventories file shares and cloud storage. Unstructured data often larger than expected. | Base: $20K-$50K | No |
| FIL-002 | File data ownership analysis | Determines who owns which files. Prevents migrating data that shouldn't transfer. | Base: $15K-$40K | No |
| FIL-003 | File data classification | Identifies sensitive files requiring special handling. PII and confidential data need protection during migration. | Base + per TB: $500-$1,500 | No |
| FIL-004 | File migration strategy design | Plans file migration approach and tooling. Large file volumes require careful migration planning. | Base: $25K-$60K | No |
| FIL-010 | Windows file share migration | Moves traditional Windows file shares. Common enterprise file storage requiring permission handling. | Base + per TB: $200-$600 | Yes (2-4 mo) |
| FIL-011 | NAS/SAN file migration | Migrates enterprise storage appliances. Large volumes require network bandwidth and time planning. | Base + per TB: $150-$400 | Yes (2-4 mo) |
| FIL-012 | File share to cloud migration (Azure Files/FSx) | Moves files to cloud storage services. Modernization opportunity for file infrastructure. | Base + per TB: $300-$800 | Yes (3-6 mo) |
| FIL-020 | SharePoint site inventory and planning | Catalogs SharePoint sites and content. SharePoint often contains critical business content. | Base + per site: $500-$1,500 | No |
| FIL-021 | SharePoint Online migration - Standard sites | Migrates basic team and document sites. Standard content migration with metadata preservation. | Per site: $1.5K-$4K | Yes (3-6 mo) |
| FIL-022 | SharePoint Online migration - Complex sites | Migrates heavily customized SharePoint sites. Custom workflows and apps require special handling. | Per site: $4K-$12K | Yes (3-6 mo) |
| FIL-023 | SharePoint on-premises to Online migration | Upgrades on-prem SharePoint to cloud. Combines migration with platform modernization. | Base + per site: $2K-$6K | Yes (3-6 mo) |
| FIL-030 | OneDrive migration | Moves user personal cloud storage. Users lose files and work history without migration. | Base + per user: $10-$30 | Yes (2-4 mo) |
| FIL-031 | Box/Dropbox migration | Migrates third-party cloud storage. Shadow IT storage often contains important data. | Base + per user: $15-$40 | Yes (2-4 mo) |
| FIL-032 | Google Drive migration | Moves Google Workspace storage. Required for organizations leaving Google ecosystem. | Base + per user: $15-$40 | Yes (2-4 mo) |
| FIL-040 | Permission mapping and remediation | Maps and fixes file permissions. Wrong permissions mean broken access or security gaps. | Base + per TB: $300-$800 | No |
| FIL-041 | Shortcut and link remediation | Fixes broken shortcuts after migration. Users frustrated by broken links to moved content. | Base + per user: $5-$15 | No |

### Archival Workstream (13 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| ARC-001 | Data retention requirements analysis | Documents legal and regulatory retention obligations. Compliance requires proper data retention. | Base: $20K-$50K | No |
| ARC-002 | Historical data analysis | Assesses what historical data must transfer. Not all historical data belongs to new entity. | Base: $15K-$40K | No |
| ARC-003 | Archive strategy design | Plans archive infrastructure and processes. Long-term data retention approach for standalone entity. | Base: $25K-$60K | No |
| ARC-010 | Archive platform deployment | Implements archive storage solution. Required infrastructure for data retention compliance. | Base: $30K-$80K | No |
| ARC-011 | Email archive migration | Moves historical email archives. Legal and compliance often require email retention for years. | Base + per user: $20-$60 | Yes (3-6 mo) |
| ARC-012 | File archive migration | Transfers archived file content. Historical documents needed for compliance and reference. | Base + per TB: $100-$300 | Yes (2-4 mo) |
| ARC-013 | Database archive/historical data extraction | Extracts historical data from databases. Old transactions needed for audit and reporting. | Base + per database: $3K-$10K | Yes (3-6 mo) |
| ARC-020 | Legal hold transfer | Moves litigation hold data appropriately. Legal obligations travel with the data. | Base: $20K-$50K | Yes (2-4 mo) |
| ARC-021 | eDiscovery platform setup | Deploys eDiscovery search and collection. Legal needs ability to search and produce data. | Base: $30K-$80K | No |
| ARC-022 | Retention policy implementation | Configures automated retention and disposal. Ensures data lifecycle management compliance. | Base: $15K-$40K | No |
| ARC-030 | Legacy data cleanup | Removes data that shouldn't transfer. Reduces migration scope and eliminates data liability. | Base + per TB: $200-$500 | No |
| ARC-031 | Data deduplication | Eliminates duplicate data before migration. Reduces storage costs and migration time. | Base + per TB: $100-$300 | No |

### Migration Tooling Workstream (11 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| MIG-001 | Migration tooling assessment | Evaluates migration tools for the program. Right tools dramatically improve migration speed and quality. | Base: $15K-$40K | No |
| MIG-002 | Migration automation strategy | Plans automation approach for migrations. Manual migration doesn't scale for large environments. | Base: $20K-$50K | No |
| MIG-010 | SharePoint migration tool deployment | Implements SharePoint migration tooling. Tools like ShareGate essential for SharePoint migrations. | Base: $15K-$40K | No |
| MIG-011 | Database migration tool deployment | Deploys database migration tools. DMS, Attunity, or native tools for database moves. | Base: $15K-$40K | No |
| MIG-012 | File migration tool deployment | Implements file transfer automation. Large file volumes require reliable migration tooling. | Base: $10K-$30K | No |
| MIG-013 | Cloud migration tool deployment (Azure Migrate/AWS MGN) | Deploys cloud provider migration tools. Native tools for VM and server migrations to cloud. | Base: $20K-$50K | No |
| MIG-020 | Migration wave planning | Sequences migrations into manageable waves. Controlled approach reduces risk of mass failures. | Base: $25K-$60K | No |
| MIG-021 | Migration runbook development | Documents step-by-step migration procedures. Repeatable processes ensure consistent execution. | Base: $20K-$50K | No |
| MIG-022 | Migration monitoring and reporting | Implements migration tracking and dashboards. Visibility into migration progress and issues. | Base: $15K-$40K | No |
| MIG-030 | Migration validation framework | Creates validation checklists and tests. Ensures data integrity and completeness post-migration. | Base: $20K-$50K | No |
| MIG-031 | Data quality remediation | Fixes data quality issues found during migration. Dirty data causes problems in target systems. | Base: $25K-$75K | No |
| MIG-032 | Post-migration validation | Validates everything works after migration. Final confirmation before declaring migration complete. | Base: $20K-$50K | No |

---

## Phase 5: Licensing (53 Activities)

### Microsoft Licensing Workstream (16 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| LIC-MS-001 | Microsoft licensing assessment | Audits current Microsoft entitlements and usage. Foundation for understanding license transfer and gaps. | Base: $25K-$60K | No |
| LIC-MS-002 | Microsoft EA/enrollment analysis | Reviews Enterprise Agreement terms for transfer rights. Most EAs don't allow partial transfers. | Base: $15K-$40K | No |
| LIC-MS-003 | Microsoft license deployment analysis | Maps deployed licenses to users and devices. Identifies actual usage vs. entitlements. | Base + per user: $5-$15 | No |
| LIC-MS-010 | M365 license strategy design | Plans M365 licensing approach for standalone. Determines SKU mix (E3/E5/F3) for new entity. | Base: $20K-$50K | No |
| LIC-MS-011 | M365 license procurement | Purchases M365 licenses for new tenant. Users need licenses before mailbox migration. | Per user: $150-$400 (annual) | No |
| LIC-MS-012 | M365 license assignment and activation | Assigns licenses to user accounts. Services don't work until licenses are assigned. | Base + per user: $5-$15 | No |
| LIC-MS-020 | Azure subscription strategy | Plans Azure subscription structure. Proper subscription design enables cost tracking and governance. | Base: $15K-$40K | No |
| LIC-MS-021 | Azure subscription transfer/creation | Creates or transfers Azure subscriptions. Required before any Azure resources can move. | Base: $20K-$50K | Yes (2-4 mo) |
| LIC-MS-022 | Azure reserved instance transfer | Transfers prepaid Azure commitments. Significant cost if RIs can't be moved or refunded. | Base: $10K-$30K | No |
| LIC-MS-023 | Azure Hybrid Benefit analysis | Assesses Windows license usage on Azure. Can reduce Azure VM costs by 40%+ with proper licensing. | Base: $10K-$25K | No |
| LIC-MS-030 | Windows Server licensing assessment | Audits Windows Server licensing position. Datacenter vs. Standard licensing significantly impacts cost. | Base: $15K-$40K | No |
| LIC-MS-031 | Windows Server license procurement | Purchases Windows Server licenses. Servers can't legally run Windows without valid licenses. | Per server: $500-$2K | No |
| LIC-MS-032 | CAL procurement and assignment | Obtains Client Access Licenses. Users need CALs to access Windows Server services. | Per user: $30-$100 | No |
| LIC-MS-040 | EA negotiation support | Supports Enterprise Agreement negotiation. New EA terms significantly impact ongoing costs. | Base: $30K-$80K | No |
| LIC-MS-041 | EA partial transfer execution | Executes partial license transfer from parent EA. Complex process requiring Microsoft approval. | Base: $20K-$50K | Yes (3-6 mo) |
| LIC-MS-042 | CSP/NCE migration | Moves to Cloud Solution Provider model. Alternative to EA for smaller organizations. | Base + per user: $10-$30 | No |

### Database Licensing Workstream (11 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| LIC-DB-001 | Oracle licensing assessment | Audits Oracle database licensing position. Oracle licensing errors lead to massive compliance penalties. | Base: $40K-$100K | No |
| LIC-DB-002 | Oracle ULA analysis | Reviews Unlimited License Agreement terms. ULA exit certification timing critical for separation. | Base: $25K-$60K | No |
| LIC-DB-003 | Oracle processor/NUP calculation | Calculates license requirements for new environment. Wrong calculations mean non-compliance or overspend. | Base + per database: $2K-$5K | No |
| LIC-DB-004 | Oracle license negotiation support | Supports Oracle license negotiations. Oracle deals are complex—expert support reduces costs. | Base: $50K-$150K | Yes (6-12 mo) |
| LIC-DB-005 | Oracle license transfer execution | Executes Oracle license transfer process. Oracle approval required—not automatic with M&A. | Base: $25K-$60K | Yes (3-6 mo) |
| LIC-DB-006 | Oracle audit defense preparation | Prepares for potential Oracle audit. Separations often trigger Oracle audit scrutiny. | Base: $30K-$80K | No |
| LIC-DB-010 | SQL Server licensing assessment | Reviews SQL Server licensing position. Core-based licensing significantly impacts costs. | Base: $20K-$50K | No |
| LIC-DB-011 | SQL Server license procurement | Purchases SQL Server licenses. Databases can't run without valid licensing. | Base + per core: $2K-$8K | No |
| LIC-DB-012 | SQL Server edition optimization | Right-sizes SQL editions to workload needs. Enterprise vs. Standard can mean 4x cost difference. | Base + per database: $3K-$10K | No |
| LIC-DB-020 | PostgreSQL/MySQL enterprise support | Obtains enterprise support for open-source databases. Production databases need vendor support. | Base + per database: $2K-$8K | No |
| LIC-DB-021 | MongoDB/NoSQL licensing | Licenses NoSQL database platforms. Enterprise features require commercial licensing. | Base + per database: $5K-$20K | No |

### Infrastructure Licensing Workstream (9 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| LIC-INF-001 | VMware licensing assessment | Reviews VMware licensing and entitlements. Broadcom acquisition changed VMware licensing significantly. | Base: $20K-$50K | No |
| LIC-INF-002 | VMware license procurement | Purchases VMware virtualization licenses. VMs can't run without valid hypervisor licensing. | Base + per CPU: $2K-$6K | No |
| LIC-INF-003 | VMware to alternative platform assessment | Evaluates VMware alternatives (Hyper-V, Nutanix, KVM). Licensing changes make alternatives attractive. | Base: $25K-$60K | No |
| LIC-INF-010 | Backup software licensing assessment | Reviews backup software licensing position. Data protection requires licensed backup software. | Base: $15K-$40K | No |
| LIC-INF-011 | Backup software license procurement | Purchases backup software licenses. Backups fail without proper licensing in new environment. | Base + per VM: $50-$200 | No |
| LIC-INF-020 | Monitoring tools licensing | Licenses monitoring and observability tools. Operations team needs visibility into systems. | Base + per server: $100-$500 | No |
| LIC-INF-021 | ITSM/ServiceNow licensing | Licenses IT service management platform. Help desk and ITSM processes need tooling. | Base + per user: $50-$200 | No |
| LIC-INF-030 | Network equipment licensing | Licenses network devices and features. Many network features require subscription licensing. | Base + per device: $200-$1K | No |
| LIC-INF-031 | Security tools licensing | Licenses security stack components. Endpoint, SIEM, vulnerability scanning all need licenses. | Base + per user: $30-$100 + per endpoint: $20-$80 | No |

### Application Licensing Workstream (13 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| LIC-APP-001 | ERP licensing assessment | Reviews ERP license entitlements and deployment. ERP licensing is typically largest single software cost. | Base: $30K-$80K | No |
| LIC-APP-002 | SAP license transfer negotiation | Negotiates SAP license transfer to new entity. SAP requires contract renegotiation for transfers. | Base: $50K-$150K | Yes (6-12 mo) |
| LIC-APP-003 | Oracle ERP licensing | Addresses Oracle ERP licensing requirements. Oracle ERP licensing complexity rivals database licensing. | Base: $40K-$120K | Yes (6-12 mo) |
| LIC-APP-004 | Dynamics 365 licensing | Procures Microsoft Dynamics 365 licenses. Per-user licensing for ERP and CRM functions. | Base + per user: $100-$300 | No |
| LIC-APP-010 | Salesforce licensing assessment | Reviews Salesforce licensing and editions. Sales Cloud, Service Cloud, Platform licenses vary significantly. | Base: $15K-$40K | No |
| LIC-APP-011 | Salesforce license procurement | Purchases Salesforce licenses for new org. Users need licenses assigned before CRM access. | Base + per user: $150-$400 | No |
| LIC-APP-020 | Specialty software inventory | Catalogs specialized and departmental software. Engineering, design, scientific software often overlooked. | Base + per app: $500-$2K | No |
| LIC-APP-021 | Specialty software license transfer | Transfers specialized software licenses. Many specialty vendors restrict license transfers. | Base + per app: $2K-$8K | Yes (2-4 mo) |
| LIC-APP-022 | Specialty software new procurement | Purchases new specialty software licenses. Required when transfers aren't permitted. | Base + per app: $5K-$25K | No |
| LIC-APP-030 | Development tools licensing | Licenses development environments and tools. Developers need IDE, testing, and build tools. | Base + per developer: $500-$2K | No |
| LIC-APP-031 | DevOps platform licensing | Licenses CI/CD and DevOps toolchain. GitHub, GitLab, Azure DevOps, Jenkins need licensing. | Base + per user: $20-$50 | No |
| LIC-APP-040 | Parent software agreement analysis | Analyzes parent company's volume agreements. Identifies what transfers vs. what's lost. | Base: $25K-$60K | No |
| LIC-APP-041 | Volume discount impact analysis | Quantifies lost volume discount impact. Standalone entity loses parent's purchasing power. | Base: $15K-$40K | No |

### License Compliance Workstream (4 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| LIC-CMP-001 | Software asset management setup | Implements SAM tools and processes. Visibility into software deployments prevents compliance gaps. | Base: $30K-$80K | No |
| LIC-CMP-002 | License compliance remediation | Addresses license compliance gaps found during assessment. Avoids audit penalties and true-ups. | Base: $25K-$75K | No |
| LIC-CMP-003 | License optimization program | Right-sizes licensing to actual usage. Most orgs over-licensed by 20-30%—real savings opportunity. | Base: $30K-$80K | No |
| LIC-CMP-004 | License contract consolidation | Consolidates fragmented license agreements. Simplified contracts reduce administrative burden. | Base: $20K-$50K | No |

---

## Phase 6: Integration - Buyer Side (50 Activities)

### Integration Planning Workstream (7 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| INT-001 | IT integration assessment | Evaluates target IT environment for integration compatibility. Identifies major obstacles before planning. | Base: $50K-$125K | No |
| INT-002 | Technology stack comparison | Compares buyer and target technology stacks. Determines consolidation opportunities and conflicts. | Base: $30K-$75K | No |
| INT-003 | Integration complexity scoring | Scores integration difficulty by domain. Focuses resources on highest-complexity areas. | Base: $20K-$50K | No |
| INT-004 | Synergy identification and validation | Identifies and validates IT cost synergies. Supports deal model assumptions with evidence. | Base: $35K-$85K | No |
| INT-005 | Integration strategy design | Designs overall IT integration approach. Determines absorb vs. preserve decisions by domain. | Base: $50K-$125K | No |
| INT-006 | Integration roadmap development | Creates detailed integration timeline and milestones. Sequences activities for dependencies. | Base: $30K-$75K | No |
| INT-007 | Integration governance setup | Establishes integration decision-making and oversight. Clear governance prevents integration delays. | Base: $25K-$60K | No |

### Technology Integration Workstream (18 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| INT-010 | Identity integration assessment | Assesses identity systems for integration approach. Determines merge vs. coexistence strategy. | Base: $25K-$60K | No |
| INT-011 | Directory trust/federation setup | Establishes trust between buyer and target directories. Required for Day 1 cross-org access. | Base: $30K-$75K | No (Day 1 Critical) |
| INT-012 | User migration to buyer identity | Migrates target users into buyer identity platform. Final step to unified identity management. | Base + per user: $20-$50 | No |
| INT-013 | SSO integration for target applications | Integrates target apps with buyer SSO. Enables unified authentication across all applications. | Base + per app: $2K-$6K | No |
| INT-014 | Legacy identity decommission | Decommissions target identity infrastructure. Removes cost and complexity of maintaining two systems. | Base: $20K-$50K | No |
| INT-020 | Email integration assessment | Assesses email systems for integration approach. Determines tenant merge vs. coexistence. | Base: $20K-$50K | No |
| INT-021 | Cross-tenant mail flow configuration | Configures mail flow between buyer and target tenants. Enables seamless communication from Day 1. | Base: $15K-$40K | No (Day 1 Critical) |
| INT-022 | Mailbox migration to buyer tenant | Migrates target mailboxes to buyer tenant. Consolidates email into single platform. | Base + per user: $25-$60 | No |
| INT-023 | Email domain consolidation | Consolidates email domains to buyer standard. Simplifies email routing and branding. | Base + per domain: $3K-$8K | No |
| INT-030 | Network interconnection | Connects buyer and target networks. Required for application and data access across organizations. | Base + per site: $3K-$10K | No (Day 1 Critical) |
| INT-031 | Workload migration to buyer platform | Migrates target workloads to buyer infrastructure. Consolidates compute platforms for efficiency. | Base + per VM: $800-$2,500 | No |
| INT-032 | Infrastructure tool consolidation | Consolidates infrastructure management tools. Reduces tool sprawl and licensing costs. | Base: $30K-$80K | No (Cost Synergy) |
| INT-033 | Target datacenter exit | Exits target datacenter facilities. Eliminates facility, power, and equipment costs. | Base: $25K-$75K | No (Cost Synergy) |
| INT-040 | Application portfolio rationalization | Rationalizes combined application portfolio. Identifies redundant apps for retirement. | Base + per app: $500-$1,500 | No (Cost Synergy) |
| INT-041 | ERP integration/consolidation | Integrates or consolidates ERP systems. Most complex integration—drives business process alignment. | Base: $200K-$750K | No |
| INT-042 | CRM integration/consolidation | Integrates or consolidates CRM systems. Enables unified customer view across organizations. | Base: $75K-$250K | No |
| INT-043 | Application retirement execution | Retires redundant applications from portfolio. Removes licensing and support costs. | Base + per app: $5K-$15K | No (Cost Synergy) |
| INT-044 | SaaS account consolidation | Consolidates duplicate SaaS subscriptions. Eliminates redundant SaaS spend. | Base + per app: $2K-$8K | No (Cost Synergy) |

### Synergy Workstream (8 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| SYN-001 | IT cost synergy tracking setup | Establishes synergy tracking mechanisms and reporting. Demonstrates synergy capture to deal sponsors. | Base: $20K-$50K | No |
| SYN-002 | License consolidation execution | Executes software license consolidation. Realizes volume discounts and eliminates duplicates. | Base: $30K-$80K | No (Cost Synergy) |
| SYN-003 | Vendor consolidation execution | Consolidates overlapping vendor relationships. Increases leverage and reduces admin overhead. | Base: $25K-$60K | No (Cost Synergy) |
| SYN-004 | Infrastructure consolidation | Consolidates data center and cloud infrastructure. Major synergy driver through facility and compute savings. | Base: $50K-$150K | No (Cost Synergy) |
| SYN-005 | IT organization optimization | Optimizes combined IT organization structure. Eliminates duplicate roles while maintaining capabilities. | Base: $40K-$100K | No (Cost Synergy) |
| SYN-010 | Cross-sell technology enablement | Enables technology for cross-selling opportunities. Supports revenue synergy capture through systems. | Base: $30K-$80K | No (Revenue Synergy) |
| SYN-011 | Data platform integration | Integrates analytics and data platforms. Enables combined reporting and advanced analytics. | Base: $75K-$200K | No (Capability Synergy) |
| SYN-012 | Technology capability transfer | Transfers technology capabilities between organizations. Shares best practices and innovations. | Base: $40K-$120K | No (Capability Synergy) |

### Day 1 Readiness Workstream (12 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| D1-001 | Day 1 requirements gathering | Gathers all Day 1 business requirements. Ensures nothing critical is missed for deal close. | Base: $20K-$50K | No (Day 1 Critical) |
| D1-002 | Day 1 checklist development | Creates comprehensive Day 1 readiness checklist. Structured approach prevents Day 1 failures. | Base: $15K-$35K | No (Day 1 Critical) |
| D1-003 | Day 1 dress rehearsal | Conducts mock Day 1 execution. Identifies gaps before they become real problems. | Base: $20K-$50K | No (Day 1 Critical) |
| D1-010 | Day 1 network connectivity | Ensures network connectivity between organizations. Users need to access both environments from Day 1. | Base: $30K-$80K | No (Day 1 Critical) |
| D1-011 | Day 1 communication systems | Enables cross-organization communication. Email and phone must work from Day 1. | Base: $15K-$40K | No (Day 1 Critical) |
| D1-020 | Day 1 access provisioning | Provisions user access across organizations. Employees need access to systems from Day 1. | Base + per user: $10-$30 | No (Day 1 Critical) |
| D1-021 | Day 1 shared services access | Enables access to shared services (HR, Finance systems). Employees need to process transactions. | Base: $20K-$50K | No (Day 1 Critical) |
| D1-030 | Day 1 support model | Establishes Day 1 IT support model. Users need someone to call when things don't work. | Base: $15K-$40K | No (Day 1 Critical) |
| D1-031 | Day 1 war room setup | Sets up integration command center. Central coordination point for Day 1 issues. | Base: $10K-$30K | No (Day 1 Critical) |
| D1-032 | Day 1 execution and support | Executes Day 1 plan with active support. Hands-on presence resolves issues in real-time. | Base: $25K-$75K | No (Day 1 Critical) |
| D1-040 | Post-Day 1 stabilization | Stabilizes environment in weeks following Day 1. Addresses issues discovered post-close. | Base: $30K-$80K | No |
| D1-041 | Integration transition to BAU | Transitions integration activities to steady-state. Moves from project mode to operations. | Base: $20K-$50K | No |

### TSA Management Workstream (5 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| TSA-001 | TSA requirements definition | Defines IT TSA service requirements. Clear scope prevents disputes during TSA period. | Base: $25K-$60K | No |
| TSA-002 | TSA negotiation support | Supports TSA negotiation with seller. IT input ensures realistic terms and pricing. | Base: $30K-$80K | No |
| TSA-003 | TSA governance setup | Establishes TSA governance and SLAs. Structured oversight ensures service levels are met. | Base: $20K-$50K | No |
| TSA-004 | TSA exit planning | Plans exit from TSA services. Orderly exit avoids service disruptions. | Base: $25K-$60K | No |
| TSA-005 | TSA exit execution | Executes TSA exit activities. Transitions services off TSA to standalone or buyer systems. | Base: $40K-$100K | No |

---

## Phase 7: Operational Run-Rate (62 Activities)

**Note:** Phase 7 costs are ANNUAL/RECURRING, not one-time separation costs.

### Infrastructure Operations Workstream (13 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| OPS-INF-001 | Cloud infrastructure (IaaS) | Annual cloud VM and storage costs. Largest recurring infrastructure line item for cloud-first orgs. | Per VM: $600-$1,800/yr | No |
| OPS-INF-002 | Cloud platform services (PaaS) | Annual managed platform services (databases, containers, serverless). Growing cost category. | Base: $50K-$200K/yr | No |
| OPS-INF-003 | On-premises datacenter | Annual facility, power, and equipment costs. Significant fixed cost base for on-prem shops. | Per rack: $15K-$50K/yr | No |
| OPS-INF-010 | Colocation services | Annual colocation facility costs. Alternative to owned datacenters with shared facility model. | Per cabinet: $12K-$36K/yr | No |
| OPS-INF-011 | Disaster recovery infrastructure | Annual DR environment costs. Required for business continuity but often underestimated. | Base + per VM: $200-$600/yr | No |
| OPS-INF-012 | Backup infrastructure | Annual backup storage and software costs. Data growth drives increasing backup costs. | Per TB: $300-$1,200/yr | No |
| OPS-INF-020 | Network operations (WAN) | Annual WAN circuit and management costs. Connects distributed sites to datacenter/cloud. | Per site: $8K-$24K/yr | No |
| OPS-INF-021 | Network operations (LAN) | Annual LAN operations and equipment costs. Local network at each physical site. | Per site: $5K-$15K/yr | No |
| OPS-INF-022 | Internet connectivity | Annual internet bandwidth costs. Critical for cloud and SaaS connectivity. | Per Mbps: $50-$200/yr | No |
| OPS-INF-023 | SD-WAN services | Annual SD-WAN service subscription. Modern alternative to traditional MPLS networks. | Per site: $6K-$18K/yr | No |
| OPS-INF-030 | Infrastructure monitoring | Annual monitoring platform costs. Visibility into infrastructure health and performance. | Base + per device: $20-$80/yr | No |
| OPS-INF-031 | Log management and SIEM | Annual log aggregation and security monitoring. Required for security and compliance. | Per GB/day: $5K-$15K/yr | No |

### Application Support Workstream (13 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| OPS-APP-001 | SaaS application management | Annual SaaS admin and configuration costs. Management overhead for cloud applications. | Per app: $2K-$8K/yr | No |
| OPS-APP-002 | Custom application support | Annual custom app maintenance and enhancement. Proprietary apps require dedicated support. | Per app: $15K-$60K/yr | No |
| OPS-APP-003 | ERP operations (SAP) | Annual SAP Basis and functional support. SAP requires specialized expensive resources. | Base: $200K-$800K/yr | No |
| OPS-APP-004 | ERP operations (Oracle) | Annual Oracle ERP operations support. Similar to SAP in complexity and cost. | Base: $150K-$600K/yr | No |
| OPS-APP-010 | Web application hosting | Annual web app hosting and CDN costs. Customer-facing apps need reliable hosting. | Per app: $8K-$24K/yr | No |
| OPS-APP-011 | API management | Annual API gateway and management costs. APIs require security and lifecycle management. | Base: $30K-$100K/yr | No |
| OPS-APP-012 | Mobile application support | Annual mobile app maintenance and updates. Mobile apps need continuous updates for OS changes. | Per app: $15K-$50K/yr | No |
| OPS-APP-020 | Database administration | Annual DBA services and management. Databases need ongoing performance tuning and maintenance. | Per database: $5K-$20K/yr | No |
| OPS-APP-021 | Database licensing (Oracle) | Annual Oracle database license support. 22% of license cost—significant ongoing expense. | Per processor: $25K-$100K/yr | No |
| OPS-APP-022 | Database licensing (SQL Server) | Annual SQL Server license and support. More predictable than Oracle but still material. | Per core: $3K-$15K/yr | No |
| OPS-APP-040 | Application monitoring (APM) | Annual APM platform costs. Deep visibility into application performance and errors. | Base + per app: $1K-$4K/yr | No |
| OPS-APP-041 | Synthetic monitoring | Annual synthetic monitoring checks. Proactive detection before users report problems. | Per check: $500-$2K/yr | No |
| OPS-APP-042 | Real user monitoring | Annual RUM tracking costs. Actual user experience data for performance optimization. | Per user session: $0.50-$2/yr | No |

### IT Staffing Workstream (14 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| OPS-STF-001 | CIO/IT leadership | Annual IT executive leadership costs. CIO provides strategic direction and governance. | Base: $300K-$600K/yr | No |
| OPS-STF-002 | IT management layer | Annual IT management team costs. Managers coordinate teams and drive execution. | Per manager: $150K-$250K/yr | No |
| OPS-STF-003 | Enterprise architecture | Annual enterprise architect costs. Strategic technology planning and standards. | Per architect: $175K-$300K/yr | No |
| OPS-STF-010 | Infrastructure engineers | Annual infrastructure team costs. Maintains servers, storage, and cloud environments. | Per FTE: $120K-$180K/yr | No |
| OPS-STF-011 | Network engineers | Annual network team costs. Maintains WAN, LAN, and connectivity. | Per FTE: $110K-$170K/yr | No |
| OPS-STF-012 | Security engineers | Annual security team costs. Manages security tools and responds to threats. | Per FTE: $130K-$200K/yr | No |
| OPS-STF-020 | Application developers | Annual development team costs. Builds and maintains applications. | Per FTE: $120K-$200K/yr | No |
| OPS-STF-021 | Application support analysts | Annual app support team costs. Handles incidents and user support for applications. | Per FTE: $80K-$130K/yr | No |
| OPS-STF-022 | QA/Testing engineers | Annual QA team costs. Ensures application quality through testing. | Per FTE: $90K-$150K/yr | No |
| OPS-STF-030 | Help desk staff (L1) | Annual L1 help desk costs. First-line user support for common issues. | Per FTE: $50K-$80K/yr | No |
| OPS-STF-031 | Desktop support (L2) | Annual desktop support costs. Hands-on device support and troubleshooting. | Per FTE: $65K-$100K/yr | No |
| OPS-STF-032 | IT service desk manager | Annual service desk management. Oversees help desk operations and SLAs. | Per FTE: $100K-$150K/yr | No |
| OPS-STF-050 | IT project managers | Annual IT PM costs. Manages IT projects and initiatives. | Per FTE: $110K-$170K/yr | No |
| OPS-STF-051 | IT business analysts | Annual BA costs. Translates business requirements to technical specs. | Per FTE: $90K-$140K/yr | No |

### Managed Services Workstream (10 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| OPS-MSP-001 | Full IT managed services | Annual fully outsourced IT costs. Alternative to internal IT staff for smaller orgs. | Per user: $150-$400/mo | No |
| OPS-MSP-002 | Infrastructure managed services | Annual infrastructure MSP costs. Outsourced server and cloud management. | Per device: $50-$150/mo | No |
| OPS-MSP-003 | Application managed services | Annual application MSP costs. Outsourced app support and maintenance. | Per app: $2K-$10K/mo | No |
| OPS-MSP-010 | Managed detection and response (MDR) | Annual MDR service costs. Outsourced threat detection and response capabilities. | Per endpoint: $15-$50/mo | No |
| OPS-MSP-011 | Managed SOC services | Annual outsourced SOC costs. 24x7 security monitoring without internal team. | Base: $10K-$40K/mo | No |
| OPS-MSP-012 | Managed firewall services | Annual managed firewall costs. Outsourced firewall management and monitoring. | Per device: $200-$600/mo | No |
| OPS-MSP-020 | Help desk outsourcing | Annual outsourced help desk costs. Alternative to internal L1 support staff. | Per user: $8-$25/mo | No |
| OPS-MSP-021 | Desktop management outsourcing | Annual outsourced desktop management. Remote device management and support. | Per device: $20-$50/mo | No |
| OPS-MSP-030 | NOC services | Annual network operations center costs. 24x7 network monitoring and response. | Base: $15K-$50K/mo | No |
| OPS-MSP-031 | 24x7 on-call support | Annual after-hours support costs. Coverage outside business hours for emergencies. | Base: $8K-$25K/mo | No |

### Support Contracts Workstream (12 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| OPS-SUP-001 | Microsoft Premier/Unified Support | Annual Microsoft support contract. Access to Microsoft engineers for escalations. | Per user: $20-$60/yr | No |
| OPS-SUP-002 | Oracle support (SW) | Annual Oracle software support. Required for patches and Oracle support access. | 22% of license: Per license | No |
| OPS-SUP-003 | SAP Enterprise Support | Annual SAP support contract. Required for SAP updates and support access. | 22% of license: Per license | No |
| OPS-SUP-010 | Cisco SmartNet | Annual Cisco support contract. Hardware replacement and software updates. | Per device: $300-$2K/yr | No |
| OPS-SUP-011 | VMware SnS | Annual VMware support subscription. Required for updates and VMware support. | Per socket: $800-$3K/yr | No |
| OPS-SUP-012 | Dell ProSupport | Annual Dell hardware support. Break-fix and parts replacement coverage. | Per device: $200-$800/yr | No |
| OPS-SUP-013 | HPE support | Annual HPE hardware support. Similar to Dell for HP equipment. | Per device: $300-$1.2K/yr | No |
| OPS-SUP-020 | Software assurance (SA) | Annual Microsoft SA enrollment. Version upgrade rights and benefits. | 25% of license: Per license | No |
| OPS-SUP-021 | Third-party software maintenance | Annual vendor software maintenance. Updates and vendor support access. | 18-22% of license: Per license | No |
| OPS-SUP-022 | Open source support (RHEL, etc.) | Annual enterprise Linux support. Commercial support for open-source platforms. | Per server: $1K-$3K/yr | No |
| OPS-SUP-030 | Telecom carrier support | Annual telecom carrier support contracts. SLA-backed circuit support. | Per circuit: $500-$2K/yr | No |
| OPS-SUP-031 | ISP and connectivity support | Annual ISP support contracts. Internet connectivity SLA and support. | Base: $5K-$20K/yr | No |

---

## Phase 8: Compliance & Regulatory (57 Activities)

### Data Privacy Workstream (13 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| CMP-PRV-001 | Privacy program assessment | Evaluates current privacy program maturity. Identifies gaps against regulatory requirements. | Base: $30K-$80K | No |
| CMP-PRV-002 | Data inventory and mapping | Maps personal data across systems. Required for DSR response and compliance reporting. | Base + per system: $1K-$4K | No |
| CMP-PRV-003 | Privacy program establishment | Builds standalone privacy program capabilities. New entity needs own privacy governance. | Base: $50K-$150K | No |
| CMP-PRV-010 | GDPR compliance assessment | Assesses GDPR compliance gaps. EU operations require GDPR compliance. | Base: $40K-$100K | No |
| CMP-PRV-011 | GDPR remediation and implementation | Addresses GDPR compliance gaps. Fines up to 4% of global revenue for non-compliance. | Base: $75K-$250K | No |
| CMP-PRV-012 | Data Protection Officer appointment | Appoints required DPO role. GDPR requires DPO for certain organizations. | Base: $20K-$60K | No |
| CMP-PRV-013 | EU representative appointment | Appoints EU representative for non-EU companies. GDPR requirement for non-EU entities. | Base: $10K-$30K | No |
| CMP-PRV-014 | International data transfer mechanisms | Implements SCCs or other transfer mechanisms. Required for EU-US data flows post-Schrems II. | Base: $30K-$80K | No |
| CMP-PRV-020 | CCPA/CPRA compliance assessment | Assesses California privacy law compliance. CCPA/CPRA applies to most companies with CA customers. | Base: $25K-$70K | No |
| CMP-PRV-021 | CCPA/CPRA remediation | Addresses California privacy compliance gaps. Required for consumer rights and opt-out. | Base: $50K-$150K | No |
| CMP-PRV-022 | US state privacy law compliance | Addresses expanding US state privacy laws. Multiple states now have privacy laws. | Base: $30K-$90K | No |
| CMP-PRV-030 | Privacy management platform | Implements privacy management tooling. Automates DSR handling and privacy operations. | Base + per module: $15K-$50K | No |
| CMP-PRV-031 | Consent management implementation | Implements cookie consent and preference management. Required for GDPR and CCPA compliance. | Base + per site: $2K-$8K | No |

### Industry Regulation Workstream (13 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| CMP-SOX-001 | SOX IT controls assessment | Assesses IT general controls for SOX compliance. Public companies require SOX 404 compliance. | Base: $50K-$150K | No |
| CMP-SOX-002 | SOX ITGC remediation | Remediates IT control deficiencies. Control gaps can result in material weakness findings. | Base: $75K-$250K | No |
| CMP-SOX-003 | SOX control documentation | Documents IT controls and evidence. Auditors require detailed control documentation. | Base + per system: $3K-$10K | No |
| CMP-SOX-004 | SOX segregation of duties analysis | Analyzes SoD conflicts in financial systems. Key control area for audit scrutiny. | Base + per system: $5K-$20K | No |
| CMP-HIP-001 | HIPAA security assessment | Assesses HIPAA Security Rule compliance. Healthcare companies must protect PHI. | Base: $40K-$120K | No |
| CMP-HIP-002 | HIPAA remediation program | Addresses HIPAA compliance gaps. HHS enforcement has increased significantly. | Base: $75K-$300K | No |
| CMP-HIP-003 | BAA management | Manages Business Associate Agreements. Required for vendors handling PHI. | Base + per vendor: $500-$2K | No |
| CMP-PCI-001 | PCI-DSS scope assessment | Determines PCI compliance scope. Scope reduction can significantly reduce compliance costs. | Base: $30K-$80K | No |
| CMP-PCI-002 | PCI-DSS remediation | Remediates PCI control gaps. Required to process card payments. | Base: $50K-$200K | No |
| CMP-PCI-003 | PCI-DSS certification (QSA) | Obtains PCI certification via QSA audit. Annual requirement for larger merchants. | Base: $40K-$150K | No |
| CMP-FIN-001 | GLBA compliance assessment | Assesses GLBA Safeguards Rule compliance. Financial institutions must protect customer data. | Base: $30K-$80K | No |
| CMP-FIN-002 | GLBA/financial services remediation | Addresses financial services compliance gaps. Regulatory enforcement has intensified. | Base: $50K-$150K | No |
| CMP-FIN-003 | NYDFS cybersecurity compliance | Addresses NYDFS 500 requirements. NY-regulated financial companies have strict requirements. | Base: $50K-$150K | No |

### Security Compliance Workstream (12 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| CMP-SOC-001 | SOC 2 readiness assessment | Assesses readiness for SOC 2 audit. Customer contracts increasingly require SOC 2. | Base: $30K-$80K | No |
| CMP-SOC-002 | SOC 2 control implementation | Implements controls for SOC 2 compliance. Foundation for successful audit outcome. | Base: $75K-$250K | No |
| CMP-SOC-003 | SOC 2 Type I audit | Completes point-in-time SOC 2 audit. First step toward SOC 2 attestation. | Base: $40K-$100K | No |
| CMP-SOC-004 | SOC 2 Type II audit | Completes period-of-time SOC 2 audit. Full SOC 2 attestation customers require. | Base: $60K-$150K | No |
| CMP-ISO-001 | ISO 27001 gap assessment | Assesses gaps against ISO 27001 standard. International security framework for global companies. | Base: $35K-$90K | No |
| CMP-ISO-002 | ISO 27001 ISMS implementation | Implements Information Security Management System. Structured approach to security management. | Base: $100K-$350K | No |
| CMP-ISO-003 | ISO 27001 certification audit | Obtains ISO 27001 certification. Three-year certification with annual surveillance. | Base: $30K-$80K | No |
| CMP-NST-001 | NIST CSF assessment | Assesses against NIST Cybersecurity Framework. Widely adopted security maturity framework. | Base: $30K-$80K | No |
| CMP-NST-002 | NIST CSF implementation | Implements NIST CSF improvements. Systematic security program improvement. | Base: $75K-$250K | No |
| CMP-NST-003 | NIST 800-53 control assessment | Assesses against NIST 800-53 controls. Required for federal and many state contracts. | Base: $40K-$120K | No |
| CMP-CRT-001 | HITRUST assessment | Completes HITRUST certification assessment. Healthcare industry preferred security framework. | Base: $75K-$250K | No |
| CMP-CRT-002 | FedRAMP authorization support | Supports FedRAMP authorization process. Required to sell cloud services to federal agencies. | Base: $200K-$750K | No |

### Audit Readiness Workstream (9 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| CMP-AUD-001 | IT audit universe development | Defines scope of IT audit coverage. Risk-based audit planning prioritizes resources. | Base: $25K-$60K | No |
| CMP-AUD-002 | IT internal audit capability | Establishes internal IT audit function. Required for SOX and governance oversight. | Base: $50K-$150K | No |
| CMP-AUD-003 | Control self-assessment program | Implements control owner self-assessment. First line of defense for control effectiveness. | Base: $30K-$80K | No |
| CMP-AUD-010 | External audit readiness assessment | Prepares for external audit examination. Proactive preparation improves audit outcomes. | Base: $25K-$70K | No |
| CMP-AUD-011 | Audit evidence repository setup | Establishes centralized audit evidence management. Organized evidence reduces audit friction. | Base: $20K-$60K | No |
| CMP-AUD-012 | Audit support during examination | Provides support during audit fieldwork. Responsive support keeps audit on schedule. | Base: $30K-$100K | No |
| CMP-AUD-020 | Continuous control monitoring | Implements automated control testing. Early detection of control failures. | Base + per control: $500-$2K | No |
| CMP-AUD-021 | GRC platform implementation | Implements governance, risk, compliance platform. Centralizes compliance management. | Base + per module: $20K-$75K | No |

### Policy & Procedures Workstream (10 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| CMP-POL-001 | IT governance framework establishment | Establishes IT governance structure and processes. Foundation for IT decision-making and oversight. | Base: $40K-$100K | No |
| CMP-POL-002 | IT policy framework development | Creates comprehensive IT policy framework. Policies define acceptable behavior and requirements. | Base: $50K-$150K | No |
| CMP-POL-010 | Information security policy suite | Develops security policies and standards. Required baseline for security program. | Base: $40K-$120K | No |
| CMP-POL-011 | Security procedures and standards | Creates operational security procedures. Detailed guidance for security operations. | Base: $30K-$80K | No |
| CMP-POL-012 | Incident response plan development | Develops incident response playbooks. Prepared response reduces breach impact. | Base: $35K-$100K | No |
| CMP-POL-013 | Business continuity / DR planning | Creates BC/DR plans and procedures. Ensures business resilience to disruptions. | Base: $50K-$150K | No |
| CMP-POL-020 | IT operations policies and procedures | Develops IT operations procedures. Standardized processes improve consistency. | Base: $30K-$80K | No |
| CMP-POL-021 | Data management policies | Creates data governance policies. Defines data ownership and handling requirements. | Base: $30K-$80K | No |
| CMP-POL-022 | Vendor management policy | Develops vendor management policies. Structured approach to third-party oversight. | Base: $25K-$70K | No |
| CMP-POL-030 | Security awareness program | Implements security awareness training. Reduces human-caused security incidents. | Base + per user: $10-$30 | No |
| CMP-POL-031 | Role-based compliance training | Delivers role-specific compliance training. Targeted training for high-risk roles. | Base: $20K-$60K | No |

---

## Phase 9: Vendor & Contract (50 Activities)

### Contract Analysis Workstream (9 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| VND-CON-001 | IT contract inventory | Catalogs all IT vendor contracts. Foundation for understanding vendor obligations. | Base + per contract: $200-$600 | No |
| VND-CON-002 | Contract categorization and prioritization | Categorizes contracts by criticality and risk. Focuses effort on highest-impact contracts. | Base: $15K-$40K | No |
| VND-CON-003 | Contract spend analysis | Analyzes vendor spend across contracts. Identifies cost drivers and optimization opportunities. | Base: $20K-$50K | No |
| VND-CON-010 | Assignment clause analysis | Reviews contract assignment provisions. Many contracts restrict or prohibit assignment. | Base + per contract: $300-$1K | No |
| VND-CON-011 | License transfer rights analysis | Analyzes license transferability. License transfers often require vendor consent. | Base + per contract: $500-$1.5K | No |
| VND-CON-012 | Change of control analysis | Reviews change of control provisions. M&A can trigger contract renegotiation rights. | Base: $20K-$50K | No |
| VND-CON-020 | Termination rights and costs analysis | Analyzes termination provisions and costs. Early termination fees can be significant. | Base + per contract: $200-$600 | No |
| VND-CON-021 | Minimum commitment analysis | Reviews minimum purchase commitments. Unused commitments become stranded costs. | Base: $15K-$40K | No |
| VND-CON-022 | Data return and deletion provisions | Reviews data handling at contract end. Ensures data is properly returned or deleted. | Base + per contract: $200-$500 | No |

### Vendor Transition Workstream (9 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| VND-TRN-001 | Vendor notification planning | Plans vendor communication strategy. Coordinated notifications prevent confusion. | Base: $15K-$40K | No |
| VND-TRN-002 | Critical vendor engagement | Engages strategic vendors early. Key vendors need proactive relationship management. | Base + per vendor: $2K-$6K | No |
| VND-TRN-003 | Vendor notification execution | Executes vendor notifications at close. Vendors need to know new billing/contact info. | Base + per vendor: $200-$500 | No |
| VND-TRN-010 | Vendor account setup | Creates new vendor accounts. New entity needs own vendor relationships. | Base + per vendor: $300-$1K | No |
| VND-TRN-011 | Vendor portal and access migration | Migrates vendor portal access. Maintains visibility into vendor systems and orders. | Base + per vendor: $100-$400 | No |
| VND-TRN-012 | Support contract transition | Transitions support contracts to new entity. Ensures continuous support coverage. | Base + per contract: $500-$2K | Yes (3-6 mo) |
| VND-TRN-020 | Vendor relationship manager assignment | Assigns VRM for strategic vendors. Named relationship management improves service. | Base: $10K-$30K | No |
| VND-TRN-021 | Vendor governance establishment | Establishes vendor governance processes. Structured oversight of vendor performance. | Base: $20K-$50K | No |
| VND-TRN-022 | Strategic vendor QBR establishment | Sets up quarterly business reviews. Regular strategic reviews drive value. | Base + per vendor: $1K-$3K | No |

### Contract Negotiation Workstream (10 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| VND-NEG-001 | Contract negotiation strategy | Develops negotiation approach by vendor. Strategic planning improves negotiation outcomes. | Base: $25K-$60K | No |
| VND-NEG-002 | New master agreement negotiation | Negotiates new master agreements. Some vendors require entirely new contracts. | Base + per contract: $5K-$20K | Yes (3-9 mo) |
| VND-NEG-003 | Contract assignment negotiation | Negotiates contract assignment with vendors. Requires vendor consent in most cases. | Base + per contract: $2K-$8K | Yes (2-6 mo) |
| VND-NEG-004 | Statement of work negotiation | Negotiates project and service SOWs. Detailed scope prevents disputes. | Base + per contract: $1K-$4K | No |
| VND-NEG-010 | Contract amendment negotiation | Negotiates contract amendments. Modifies terms for new entity requirements. | Base + per contract: $1.5K-$5K | No |
| VND-NEG-011 | Contract renewal negotiation | Negotiates contract renewals. Opportunity to improve terms at renewal. | Base + per contract: $2K-$8K | No |
| VND-NEG-012 | Volume/pricing renegotiation | Renegotiates pricing for new volumes. Smaller entity may lose volume discounts. | Base + per contract: $2K-$6K | No |
| VND-NEG-020 | Contract termination execution | Executes contract terminations. Formal process to end vendor relationships. | Base + per contract: $1K-$3K | No |
| VND-NEG-021 | Early termination fee negotiation | Negotiates ETF reduction or waiver. Can significantly reduce separation costs. | Base + per contract: $2K-$8K | No |
| VND-NEG-022 | Vendor exit and data extraction | Manages vendor exit and data retrieval. Ensures data is recovered before contract ends. | Base + per vendor: $2K-$8K | No |

### Third-Party Risk Workstream (10 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| VND-RSK-001 | Third-party risk program establishment | Builds standalone TPRM program. Required for regulatory compliance and due diligence. | Base: $40K-$100K | No |
| VND-RSK-002 | Vendor risk tiering | Tiers vendors by risk level. Focuses oversight on highest-risk vendors. | Base + per vendor: $100-$400 | No |
| VND-RSK-003 | Critical vendor due diligence | Conducts detailed critical vendor assessments. Deep dive on vendors that could impact operations. | Base + per vendor: $2K-$8K | No |
| VND-RSK-004 | Vendor security assessment | Assesses vendor security posture. Validates vendor security meets requirements. | Base + per vendor: $1.5K-$5K | No |
| VND-RSK-010 | Vendor compliance verification | Verifies vendor compliance certifications. Confirms vendors meet regulatory requirements. | Base + per vendor: $500-$2K | No |
| VND-RSK-011 | Contract security requirements | Defines security requirements for contracts. Standardizes vendor security obligations. | Base: $20K-$50K | No |
| VND-RSK-012 | Business associate agreement management | Manages BAAs for HIPAA compliance. Required for vendors handling PHI. | Base + per contract: $500-$1.5K | No |
| VND-RSK-020 | Vendor monitoring program | Implements ongoing vendor monitoring. Continuous visibility into vendor risk posture. | Base: $30K-$80K | No |
| VND-RSK-021 | TPRM platform implementation | Implements third-party risk management platform. Automates vendor risk workflows. | Base: $50K-$150K | No |
| VND-RSK-022 | Vendor incident response planning | Plans response to vendor incidents. Prepared for vendor breaches or outages. | Base: $15K-$40K | No |

### Procurement Workstream (12 Activities)

| ID | Activity | So What | Cost Model | TSA |
|----|----------|---------|------------|-----|
| VND-PRO-001 | IT procurement function establishment | Establishes standalone IT procurement. New entity needs purchasing capabilities. | Base: $30K-$80K | No |
| VND-PRO-002 | Procurement system setup | Implements procurement system. Enables purchase orders and approvals. | Base: $25K-$75K | No |
| VND-PRO-003 | Vendor master data setup | Creates vendor master records. Foundation for vendor payments and management. | Base + per vendor: $50-$200 | No |
| VND-PRO-010 | Strategic sourcing initiative | Conducts strategic sourcing by category. Leverages competition to reduce costs. | Base + per category: $10K-$30K | No |
| VND-PRO-011 | RFP development and execution | Develops and runs RFP processes. Structured procurement for major purchases. | Base + per RFP: $5K-$20K | No |
| VND-PRO-012 | Vendor selection and onboarding | Selects and onboards new vendors. Replaces parent company vendor relationships. | Base + per vendor: $1K-$4K | No |
| VND-PRO-020 | IT spend optimization assessment | Identifies IT spend optimization opportunities. Finds savings in current spend patterns. | Base: $30K-$80K | No |
| VND-PRO-021 | Vendor consolidation analysis | Analyzes vendor consolidation opportunities. Reduces vendor count and complexity. | Base: $20K-$50K | No |
| VND-PRO-022 | Cost optimization execution | Executes identified cost optimizations. Realizes savings from optimization analysis. | Base: $25K-$75K | No |
| VND-PRO-030 | Contract lifecycle management setup | Establishes CLM processes. Structured contract management from creation to expiry. | Base: $30K-$80K | No |
| VND-PRO-031 | CLM platform implementation | Implements CLM platform. Automates contract workflows and alerts. | Base: $50K-$150K | No |
| VND-PRO-032 | Contract migration to CLM | Migrates contracts to CLM system. Centralizes contract repository for visibility. | Base + per contract: $100-$400 | No |

---

## Phase 10: Validation & Refinement (Capstone)

Phase 10 is the capstone module that provides:
- **Unified Activity Catalog** - Cross-phase activity lookup
- **Deal Scenario Estimation** - Pre-built profiles for common deal types
- **Cost Model Calibration** - Tools to align estimates with actuals
- **Executive Summary Generation** - Automated reporting

Available deal profiles: `carveout_small`, `carveout_medium`, `carveout_large`, `carveout_enterprise`, `bolt_on_small`, `bolt_on_medium`, `standalone`, `integration_full`

---

## Cost Model Legend

| Model Type | Description | Example |
|------------|-------------|---------|
| Base | Fixed cost range | Base: $25K-$50K |
| Per user | Scales with user count | Per user: $15-$40 |
| Per app | Scales with application count | Per app: $2K-$8K |
| Per VM | Scales with virtual machine count | Per VM: $500-$1,500 |
| Per server | Scales with physical/logical servers | Per server: $2K-$6K |
| Per database | Scales with database count | Per database: $3K-$15K |
| Per TB | Scales with storage volume | Per TB: $200-$600 |
| Per site | Scales with physical locations | Per site: $5K-$15K |
| Per endpoint | Scales with devices | Per endpoint: $10-$30 |
| Per integration | Scales with integration count | Per integration: $3K-$12K |

## Modifiers

| Complexity | Multiplier |
|------------|------------|
| Simple | 0.7x |
| Moderate | 1.0x |
| Complex | 1.5x |
| Highly Complex | 2.0x |

| Industry | Multiplier |
|----------|------------|
| Standard | 1.0x |
| Financial Services | 1.3x |
| Healthcare | 1.25x |
| Government | 1.4x |
| Retail | 1.1x |
| Manufacturing | 1.15x |

---

*Document Version: 1.0*
*Classification: PwC Internal - Proprietary Knowledge Base*
