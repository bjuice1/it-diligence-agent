# Infrastructure Update - January 2025 (REVISION 3)

## Server Inventory

### Production Servers
- **Web Server 1**: Dell PowerEdge R750, 128GB RAM, Ubuntu 24.04 (UPGRADED)
- **Web Server 2**: Dell PowerEdge R750, 128GB RAM, Ubuntu 24.04 (UPGRADED)
- **Database Server**: Dell PowerEdge R750, 512GB RAM, PostgreSQL 16 (UPGRADED)
- **Application Server**: HPE ProLiant DL380, 256GB RAM, Windows Server 2022
- **NEW: API Gateway Server**: Dell PowerEdge R650, 64GB RAM, Ubuntu 22.04

### Cloud Resources
- AWS EC2 instances: 22 active (us-east-1) - INCREASED FROM 18
- Azure VMs: 12 active (East US) - INCREASED FROM 8
- Total cloud spend: $78,000/month (INCREASED FROM $62,000)

## Network Infrastructure

### Firewalls
- Primary: Palo Alto PA-5450 (firmware v11.2) - UPDATED FROM v11.1
- Secondary: Palo Alto PA-5450 (firmware v11.2) - UPDATED FROM v11.1
- VPN concentrator: Cisco Secure Firewall 3100

### Switches
- Core switches: 8x Cisco Nexus 9300 (EXPANDED FROM 6)
- Access switches: 40x Cisco Catalyst 9200 (EXPANDED FROM 32)

## Security Status

### Endpoint Protection
- Antivirus: CrowdStrike Falcon deployed on 580 endpoints (EXPANDED FROM 520)
- EDR: Active monitoring enabled
- Last scan: January 25, 2025 - 0 findings (RESOLVED from 2 medium)

### Access Control
- MFA enabled for all users (Okta)
- SSO integrated with 48 applications (INCREASED FROM 42)
- Privileged access management: CyberArk
- NEW: Zero Trust Network Access implemented

## Backup Systems

- Primary backup: Veeam Backup & Replication v12.2 (UPGRADED FROM v12.1)
- Backup retention: 60 days local, 365 days offsite (INCREASED)
- Last successful backup: January 25, 2025 14:30
- RPO: 1 hour (IMPROVED FROM 2), RTO: 2 hours (IMPROVED FROM 4)

## NEW: Disaster Recovery

- DR Site: AWS us-west-2
- Replication: Real-time async
- Last DR test: January 20, 2025 - PASSED
- Failover time: < 15 minutes
