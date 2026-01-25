# Infrastructure Update - January 2025 (REVISED v2.1)

## Server Inventory

### Production Servers
- **Web Server 1**: Dell PowerEdge R750, 256GB RAM, Ubuntu 24.04 (RAM UPGRADED)
- **Web Server 2**: Dell PowerEdge R750, 256GB RAM, Ubuntu 24.04 (RAM UPGRADED)
- **Database Server**: Dell PowerEdge R750, 1TB RAM, PostgreSQL 17 (MAJOR UPGRADE)
- **Application Server**: HPE ProLiant DL380, 256GB RAM, Windows Server 2022

### Cloud Resources
- AWS EC2 instances: 25 active (us-east-1) - INCREASED
- Azure VMs: 15 active (East US) - INCREASED
- Total cloud spend: $85,000/month (INCREASED)

## Network Infrastructure

### Firewalls
- Primary: Palo Alto PA-5450 (firmware v11.1)
- Secondary: Palo Alto PA-5450 (firmware v11.1)
- VPN concentrator: Cisco Secure Firewall 3100

### Switches
- Core switches: 6x Cisco Nexus 9300
- Access switches: 32x Cisco Catalyst 9200

## Security Status

### Endpoint Protection
- Antivirus: CrowdStrike Falcon deployed on 600 endpoints (EXPANDED)
- EDR: Active monitoring enabled with threat hunting
- Last scan: January 25, 2025 - 0 critical findings

### Access Control
- MFA enabled for all users (Okta)
- SSO integrated with 50 applications (INCREASED)
- Privileged access management: CyberArk

## Backup Systems

- Primary backup: Veeam Backup & Replication v12.1
- Backup retention: 45 days local, 180 days offsite
- Last successful backup: January 25, 2025
- RPO: 2 hours, RTO: 4 hours
