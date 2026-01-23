"""
EOL Reference Data - Real dates, not LLM guesses.

This is the value-add over pure prompt-based analysis.
Maintain this data quarterly or when major vendor announcements happen.
"""
from typing import Optional, Dict, List
from datetime import datetime

# Last updated: 2024-01
EOL_DATABASE = {
    # ==========================================================================
    # SAP
    # ==========================================================================
    "SAP ECC 6.0": {"eol": "2027-12", "status": "Approaching_EOL", "successor": "S/4HANA"},
    "SAP ECC": {"eol": "2027-12", "status": "Approaching_EOL", "successor": "S/4HANA"},
    "SAP S/4HANA 1909": {"eol": "2024-12", "status": "Past_EOL", "successor": "S/4HANA 2023"},
    "SAP S/4HANA 2020": {"eol": "2025-12", "status": "Approaching_EOL", "successor": "S/4HANA 2023"},
    "SAP S/4HANA 2021": {"eol": "2026-12", "status": "Supported", "successor": "S/4HANA 2023"},
    "SAP S/4HANA 2022": {"eol": "2027-12", "status": "Supported", "successor": "S/4HANA 2023"},
    "SAP S/4HANA 2023": {"eol": "2028-12", "status": "Current", "successor": None},
    "SAP Business One": {"eol": "N/A", "status": "Current", "successor": None},

    # ==========================================================================
    # Oracle
    # ==========================================================================
    "Oracle EBS 12.1": {"eol": "2021-12", "status": "Past_EOL", "successor": "Oracle EBS 12.2 or Cloud"},
    "Oracle EBS 12.2": {"eol": "2031-12", "status": "Supported", "successor": "Oracle Fusion Cloud"},
    "Oracle E-Business Suite 12.1": {"eol": "2021-12", "status": "Past_EOL", "successor": "EBS 12.2 or Cloud"},
    "Oracle E-Business Suite 12.2": {"eol": "2031-12", "status": "Supported", "successor": "Oracle Fusion Cloud"},
    "Oracle Database 11g": {"eol": "2020-12", "status": "Past_EOL", "successor": "Oracle 19c/23c"},
    "Oracle Database 12c": {"eol": "2022-03", "status": "Past_EOL", "successor": "Oracle 19c/23c"},
    "Oracle Database 18c": {"eol": "2021-06", "status": "Past_EOL", "successor": "Oracle 19c/23c"},
    "Oracle Database 19c": {"eol": "2027-04", "status": "Supported", "successor": "Oracle 23c"},
    "Oracle Database 21c": {"eol": "2024-04", "status": "Past_EOL", "successor": "Oracle 23c"},
    "Oracle Database 23c": {"eol": "2028-04", "status": "Current", "successor": None},
    "Oracle 11g": {"eol": "2020-12", "status": "Past_EOL", "successor": "Oracle 19c/23c"},
    "Oracle 12c": {"eol": "2022-03", "status": "Past_EOL", "successor": "Oracle 19c/23c"},
    "Oracle 19c": {"eol": "2027-04", "status": "Supported", "successor": "Oracle 23c"},

    # ==========================================================================
    # Microsoft Dynamics
    # ==========================================================================
    "Dynamics AX 2012": {"eol": "2023-10", "status": "Past_EOL", "successor": "Dynamics 365 F&O"},
    "Dynamics AX": {"eol": "2023-10", "status": "Past_EOL", "successor": "Dynamics 365 F&O"},
    "Dynamics GP": {"eol": "2028-04", "status": "Approaching_EOL", "successor": "Dynamics 365 Business Central"},
    "Dynamics NAV": {"eol": "2023-01", "status": "Past_EOL", "successor": "Dynamics 365 Business Central"},
    "Dynamics NAV 2018": {"eol": "2023-01", "status": "Past_EOL", "successor": "Business Central"},
    "Dynamics 365": {"eol": "N/A", "status": "Current", "successor": None},
    "Dynamics 365 F&O": {"eol": "N/A", "status": "Current", "successor": None},
    "Dynamics 365 Business Central": {"eol": "N/A", "status": "Current", "successor": None},

    # ==========================================================================
    # Microsoft Windows Server
    # ==========================================================================
    "Windows Server 2008": {"eol": "2020-01", "status": "Past_EOL", "successor": "Windows Server 2022"},
    "Windows Server 2008 R2": {"eol": "2020-01", "status": "Past_EOL", "successor": "Windows Server 2022"},
    "Windows Server 2012": {"eol": "2023-10", "status": "Past_EOL", "successor": "Windows Server 2022"},
    "Windows Server 2012 R2": {"eol": "2023-10", "status": "Past_EOL", "successor": "Windows Server 2022"},
    "Windows Server 2016": {"eol": "2027-01", "status": "Extended_Support", "successor": "Windows Server 2022"},
    "Windows Server 2019": {"eol": "2029-01", "status": "Supported", "successor": "Windows Server 2022"},
    "Windows Server 2022": {"eol": "2031-10", "status": "Current", "successor": None},

    # ==========================================================================
    # SQL Server
    # ==========================================================================
    "SQL Server 2008": {"eol": "2019-07", "status": "Past_EOL", "successor": "SQL Server 2022"},
    "SQL Server 2012": {"eol": "2022-07", "status": "Past_EOL", "successor": "SQL Server 2022"},
    "SQL Server 2014": {"eol": "2024-07", "status": "Past_EOL", "successor": "SQL Server 2022"},
    "SQL Server 2016": {"eol": "2026-07", "status": "Extended_Support", "successor": "SQL Server 2022"},
    "SQL Server 2017": {"eol": "2027-10", "status": "Extended_Support", "successor": "SQL Server 2022"},
    "SQL Server 2019": {"eol": "2030-01", "status": "Supported", "successor": "SQL Server 2022"},
    "SQL Server 2022": {"eol": "2033-01", "status": "Current", "successor": None},

    # ==========================================================================
    # VMware
    # ==========================================================================
    "vSphere 6.5": {"eol": "2022-10", "status": "Past_EOL", "successor": "vSphere 8"},
    "vSphere 6.7": {"eol": "2023-10", "status": "Past_EOL", "successor": "vSphere 8"},
    "vSphere 7.0": {"eol": "2025-04", "status": "Approaching_EOL", "successor": "vSphere 8"},
    "vSphere 8.0": {"eol": "2028-04", "status": "Current", "successor": None},
    "VMware vSphere 6.5": {"eol": "2022-10", "status": "Past_EOL", "successor": "vSphere 8"},
    "VMware vSphere 6.7": {"eol": "2023-10", "status": "Past_EOL", "successor": "vSphere 8"},
    "VMware vSphere 7": {"eol": "2025-04", "status": "Approaching_EOL", "successor": "vSphere 8"},
    "VMware vSphere 8": {"eol": "2028-04", "status": "Current", "successor": None},

    # ==========================================================================
    # Java
    # ==========================================================================
    "Java 7": {"eol": "2022-07", "status": "Past_EOL", "successor": "Java 21"},
    "Java 8": {"eol": "2030-12", "status": "Extended_Support", "successor": "Java 21"},
    "Java 11": {"eol": "2032-01", "status": "Supported", "successor": "Java 21"},
    "Java 17": {"eol": "2029-09", "status": "Current", "successor": "Java 21"},
    "Java 21": {"eol": "2031-09", "status": "Current", "successor": None},

    # ==========================================================================
    # .NET
    # ==========================================================================
    ".NET Framework 4.5": {"eol": "2022-04", "status": "Past_EOL", "successor": ".NET 8"},
    ".NET Framework 4.6": {"eol": "2022-04", "status": "Past_EOL", "successor": ".NET 8"},
    ".NET Framework 4.7": {"eol": "N/A", "status": "Supported", "successor": ".NET 8"},
    ".NET Framework 4.8": {"eol": "N/A", "status": "Current", "successor": ".NET 8"},
    ".NET Core 3.1": {"eol": "2022-12", "status": "Past_EOL", "successor": ".NET 8"},
    ".NET 5": {"eol": "2022-05", "status": "Past_EOL", "successor": ".NET 8"},
    ".NET 6": {"eol": "2024-11", "status": "Approaching_EOL", "successor": ".NET 8"},
    ".NET 7": {"eol": "2024-05", "status": "Past_EOL", "successor": ".NET 8"},
    ".NET 8": {"eol": "2026-11", "status": "Current", "successor": None},

    # ==========================================================================
    # Python
    # ==========================================================================
    "Python 2.7": {"eol": "2020-01", "status": "Past_EOL", "successor": "Python 3.12"},
    "Python 2": {"eol": "2020-01", "status": "Past_EOL", "successor": "Python 3.12"},
    "Python 3.6": {"eol": "2021-12", "status": "Past_EOL", "successor": "Python 3.12"},
    "Python 3.7": {"eol": "2023-06", "status": "Past_EOL", "successor": "Python 3.12"},
    "Python 3.8": {"eol": "2024-10", "status": "Approaching_EOL", "successor": "Python 3.12"},
    "Python 3.9": {"eol": "2025-10", "status": "Supported", "successor": "Python 3.12"},
    "Python 3.10": {"eol": "2026-10", "status": "Supported", "successor": "Python 3.12"},
    "Python 3.11": {"eol": "2027-10", "status": "Current", "successor": "Python 3.12"},
    "Python 3.12": {"eol": "2028-10", "status": "Current", "successor": None},
}


def lookup_eol(product_name: str, version: str = "") -> Optional[Dict]:
    """
    Look up EOL info for a product.

    Args:
        product_name: e.g., "SAP ECC", "Oracle Database", "Windows Server"
        version: e.g., "6.0", "19c", "2019"

    Returns:
        Dict with eol, status, successor or None if not found
    """
    # Try exact match with version first
    if version:
        # Try "Product Version" format
        key = f"{product_name} {version}".strip()
        if key in EOL_DATABASE:
            return EOL_DATABASE[key]

        # Try "Product Version" with common variations
        variations = [
            f"{product_name} {version}",
            f"{product_name}{version}",
            f"{product_name} v{version}",
        ]
        for var in variations:
            if var in EOL_DATABASE:
                return EOL_DATABASE[var]

    # Try product name alone
    if product_name in EOL_DATABASE:
        return EOL_DATABASE[product_name]

    # Try fuzzy matching - look for product name in keys
    product_lower = product_name.lower()
    for key, value in EOL_DATABASE.items():
        if product_lower in key.lower():
            # If version specified, try to match it too
            if version and version.lower() in key.lower():
                return value
            elif not version:
                return value

    return None


def get_eol_status(product_name: str, version: str = "") -> str:
    """Get EOL status string for a product."""
    result = lookup_eol(product_name, version)
    if result:
        return result["status"]
    return "Unknown"


def get_eol_date(product_name: str, version: str = "") -> str:
    """Get EOL date string for a product."""
    result = lookup_eol(product_name, version)
    if result:
        return result["eol"]
    return "Unknown"


def is_eol_risk(product_name: str, version: str = "") -> bool:
    """Check if product is past EOL or approaching EOL."""
    status = get_eol_status(product_name, version)
    return status in ["Past_EOL", "Approaching_EOL", "Extended_Support"]


def get_all_eol_risks(applications: List[Dict]) -> List[Dict]:
    """
    Scan a list of applications and return those with EOL risks.

    Args:
        applications: List of dicts with 'name', 'vendor', 'version' keys

    Returns:
        List of dicts with EOL risk details
    """
    risks = []
    for app in applications:
        name = app.get("name", "")
        vendor = app.get("vendor", "")
        version = app.get("version", "")

        # Try product name with vendor prefix
        lookups = [
            (name, version),
            (f"{vendor} {name}", version),
            (name, ""),
        ]

        for prod, ver in lookups:
            result = lookup_eol(prod, ver)
            if result and result["status"] in ["Past_EOL", "Approaching_EOL", "Extended_Support"]:
                risks.append({
                    "application": name,
                    "vendor": vendor,
                    "version": version,
                    "eol_status": result["status"],
                    "eol_date": result["eol"],
                    "successor": result.get("successor"),
                })
                break

    return risks
