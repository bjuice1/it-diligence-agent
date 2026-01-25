# Infrastructure Update - January 2025

## Server Inventory

### Production Servers
- **Web Server 1**: Dell PowerEdge R750, 64GB RAM, Ubuntu 22.04
- **Web Server 2**: Dell PowerEdge R750, 64GB RAM, Ubuntu 22.04
- **Database Server**: Dell PowerEdge R750, 256GB RAM, PostgreSQL 15
- **Application Server**: HPE ProLiant DL380, 128GB RAM, Windows Server 2022

### Cloud Resources
- AWS EC2 instances: 12 active (us-east-1)
- Azure VMs: 5 active (East US)
- Total cloud spend: $45,000/month

## Network Infrastructure

### Firewalls
- Primary: Palo Alto PA-5250 (firmware v11.0)
- Secondary: Palo Alto PA-3260 (firmware v11.0)
- VPN concentrator: Cisco ASA 5525-X

### Switches
- Core switches: 4x Cisco Nexus 9300
- Access switches: 24x Cisco Catalyst 9200

## Security Status

### Endpoint Protection
- Antivirus: CrowdStrike Falcon deployed on 450 endpoints
- EDR: Active monitoring enabled
- Last scan: January 20, 2025 - No critical findings

### Access Control
- MFA enabled for all users (Okta)
- SSO integrated with 35 applications
- Privileged access management: CyberArk

## Backup Systems

- Primary backup: Veeam Backup & Replication v12
- Backup retention: 30 days local, 90 days offsite
- Last successful backup: January 24, 2025
- RPO: 4 hours, RTO: 8 hours
