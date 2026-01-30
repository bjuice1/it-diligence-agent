"""
Inventory Type Detector

Auto-detects inventory type from table column headers.
Returns type and confidence score.

Supported types:
- application: Software systems
- infrastructure: Servers, VMs, network devices
- organization: Teams, roles, headcount
- vendor: Contracts, MSAs
"""

import re
from typing import Tuple, List, Dict, Set
from dataclasses import dataclass


# Header patterns that strongly indicate each inventory type
# Format: {pattern: weight} where pattern is regex and weight is 0.0-1.0

APPLICATION_HEADERS = {
    # Strong indicators (0.8-1.0)
    r"^application[s]?$": 1.0,
    r"^app[s]?$": 0.9,
    r"^software$": 0.9,
    r"^system[s]?$": 0.7,
    r"^application.?name$": 1.0,
    r"^app.?name$": 0.9,

    # Medium indicators (0.5-0.7)
    r"^vendor$": 0.5,
    r"^version$": 0.6,
    r"^license": 0.5,
    r"^saas$": 0.6,
    r"^hosting$": 0.5,
    r"^deployment$": 0.5,
    r"criticality": 0.4,

    # Weak indicators (0.2-0.4)
    r"user.?count": 0.4,
    r"annual.?cost": 0.3,
    r"support": 0.2,
}

INFRASTRUCTURE_HEADERS = {
    # Strong indicators
    r"^server[s]?$": 1.0,
    r"^hostname[s]?$": 1.0,
    r"^host$": 0.9,
    r"^vm[s]?$": 0.9,
    r"^virtual.?machine": 0.9,
    r"^device[s]?$": 0.7,
    r"^asset[s]?$": 0.6,

    # Medium indicators
    r"^ip$": 0.6,
    r"^ip.?address": 0.7,
    r"^os$": 0.6,
    r"^operating.?system": 0.7,
    r"^environment$": 0.5,
    r"^cpu$": 0.6,
    r"^memory$": 0.6,
    r"^ram$": 0.6,
    r"^storage$": 0.5,
    r"^disk$": 0.5,
    r"^location$": 0.3,
    r"^datacenter": 0.6,
    r"^data.?center": 0.6,

    # Weak indicators
    r"^role$": 0.2,  # Could also be org
    r"^type$": 0.2,
}

ORGANIZATION_HEADERS = {
    # Strong indicators
    r"^role[s]?$": 0.8,
    r"^title[s]?$": 0.8,
    r"^job.?title": 0.9,
    r"^position[s]?$": 0.8,
    r"^team[s]?$": 0.7,
    r"^department[s]?$": 0.7,
    r"^headcount$": 1.0,
    r"^fte$": 1.0,
    r"^employee": 0.8,
    r"^staff": 0.8,

    # Medium indicators
    r"^name$": 0.3,  # Ambiguous
    r"^manager$": 0.6,
    r"^reports.?to": 0.7,
    r"^direct.?reports": 0.7,
    r"^salary": 0.6,
    r"^compensation": 0.6,
    r"^location$": 0.3,

    # Weak indicators
    r"responsibilities": 0.4,
    r"skills": 0.3,
}

VENDOR_HEADERS = {
    # Strong indicators
    r"^vendor[s]?$": 0.9,  # Also in application
    r"^vendor.?name": 1.0,
    r"^supplier[s]?$": 0.9,
    r"^contract[s]?$": 0.9,
    r"^contract.?name": 1.0,
    r"^msa$": 1.0,
    r"^sow$": 0.8,

    # Medium indicators
    r"^start.?date": 0.5,
    r"^end.?date": 0.6,
    r"^expir": 0.6,
    r"^renewal": 0.7,
    r"^acv$": 0.8,
    r"^tcv$": 0.8,
    r"^annual.?value": 0.7,
    r"^total.?value": 0.7,
    r"^contract.?value": 0.8,
    r"auto.?renew": 0.6,
    r"termination": 0.5,

    # Weak indicators
    r"^owner$": 0.3,
    r"^services$": 0.4,
}

# Negative indicators - headers that suggest this is NOT an inventory table
NON_INVENTORY_HEADERS = {
    r"^notes?$",
    r"^comments?$",
    r"^description$",
    r"^summary$",
    r"^findings?$",
    r"^risks?$",
    r"^recommendations?$",
    r"^action.?items?$",
    r"^status$",
    r"^priority$",
    r"^date$",
    r"^id$",
    r"^#$",
    r"^\d+$",
}

# Minimum thresholds
MIN_CONFIDENCE = 0.3  # Below this, return "unknown"
MIN_HEADERS_MATCHED = 2  # Need at least 2 matching headers


def detect_inventory_type(headers: List[str]) -> Tuple[str, float]:
    """
    Auto-detect inventory type from column headers.

    Args:
        headers: List of column header strings

    Returns:
        Tuple of (inventory_type, confidence)
        - inventory_type: "application", "infrastructure", "organization",
                         "vendor", or "unknown"
        - confidence: 0.0-1.0 confidence score
    """
    if not headers:
        return ("unknown", 0.0)

    # Normalize headers
    normalized = [h.lower().strip() for h in headers]

    # Check for non-inventory patterns
    non_inventory_count = sum(
        1 for h in normalized
        if any(re.match(pat, h) for pat in NON_INVENTORY_HEADERS)
    )
    if non_inventory_count >= len(normalized) * 0.5:
        return ("unknown", 0.0)

    # Score each type
    scores = {
        "application": _calculate_type_score(normalized, APPLICATION_HEADERS),
        "infrastructure": _calculate_type_score(normalized, INFRASTRUCTURE_HEADERS),
        "organization": _calculate_type_score(normalized, ORGANIZATION_HEADERS),
        "vendor": _calculate_type_score(normalized, VENDOR_HEADERS),
    }

    # Find best match
    best_type = max(scores, key=scores.get)
    best_score = scores[best_type]

    # Check minimum threshold
    if best_score < MIN_CONFIDENCE:
        return ("unknown", best_score)

    # Normalize confidence to 0-1 range
    confidence = min(1.0, best_score)

    return (best_type, confidence)


def _calculate_type_score(
    headers: List[str],
    patterns: Dict[str, float]
) -> float:
    """
    Calculate score for a specific inventory type.

    Uses weighted pattern matching with diminishing returns
    for multiple matches.
    """
    total_score = 0.0
    matches = 0

    for header in headers:
        best_match_weight = 0.0

        for pattern, weight in patterns.items():
            if re.search(pattern, header, re.IGNORECASE):
                best_match_weight = max(best_match_weight, weight)

        if best_match_weight > 0:
            matches += 1
            # Diminishing returns for additional matches
            total_score += best_match_weight * (0.7 ** max(0, matches - 2))

    # Require minimum matches
    if matches < MIN_HEADERS_MATCHED:
        total_score *= 0.5

    # Normalize by header count (more headers = more chances to match)
    # But cap the penalty
    header_factor = min(1.0, 5 / len(headers)) if headers else 0
    total_score *= (0.5 + 0.5 * header_factor)

    return total_score


def detect_with_details(headers: List[str]) -> Dict:
    """
    Detect inventory type with detailed scoring breakdown.

    Returns dict with:
    - type: detected type
    - confidence: confidence score
    - scores: dict of all type scores
    - matched_headers: which headers matched
    """
    inv_type, confidence = detect_inventory_type(headers)

    normalized = [h.lower().strip() for h in headers]

    # Get all scores
    scores = {
        "application": _calculate_type_score(normalized, APPLICATION_HEADERS),
        "infrastructure": _calculate_type_score(normalized, INFRASTRUCTURE_HEADERS),
        "organization": _calculate_type_score(normalized, ORGANIZATION_HEADERS),
        "vendor": _calculate_type_score(normalized, VENDOR_HEADERS),
    }

    # Find matched headers for winning type
    matched = []
    patterns = {
        "application": APPLICATION_HEADERS,
        "infrastructure": INFRASTRUCTURE_HEADERS,
        "organization": ORGANIZATION_HEADERS,
        "vendor": VENDOR_HEADERS,
    }.get(inv_type, {})

    for header in normalized:
        for pattern in patterns:
            if re.search(pattern, header, re.IGNORECASE):
                matched.append(header)
                break

    return {
        "type": inv_type,
        "confidence": confidence,
        "scores": scores,
        "matched_headers": matched,
        "total_headers": len(headers),
    }


def suggest_inventory_type(headers: List[str]) -> List[Tuple[str, float]]:
    """
    Get ranked list of possible inventory types.

    Returns list of (type, confidence) tuples sorted by confidence.
    """
    normalized = [h.lower().strip() for h in headers]

    scores = [
        ("application", _calculate_type_score(normalized, APPLICATION_HEADERS)),
        ("infrastructure", _calculate_type_score(normalized, INFRASTRUCTURE_HEADERS)),
        ("organization", _calculate_type_score(normalized, ORGANIZATION_HEADERS)),
        ("vendor", _calculate_type_score(normalized, VENDOR_HEADERS)),
    ]

    # Sort by score descending
    scores.sort(key=lambda x: x[1], reverse=True)

    return scores


# Common header aliases for field mapping
# Header aliases - combined for all fields, will match regardless of type
# The "name" field appears in multiple types, so combine all possible aliases
HEADER_ALIASES = {
    # Name field (used by application, infrastructure, organization)
    "name": [
        "name", "app", "app name", "application name", "application", "software", "system",
        "hostname", "server", "server name", "host", "device", "asset"
    ],

    # Application fields
    "vendor": ["vendor", "vendor name", "publisher", "manufacturer"],
    "version": ["version", "ver", "release", "build"],
    "hosting": ["hosting", "deployment", "hosted", "deployment type"],
    "cost": ["cost", "annual cost", "yearly cost", "license cost", "price", "spend"],
    "users": ["users", "user count", "# users", "licenses", "seats"],
    "criticality": ["criticality", "priority", "importance", "tier"],

    # Infrastructure fields
    "type": ["type", "server type", "device type", "category"],
    "os": ["os", "operating system", "os version"],
    "ip": ["ip", "ip address", "ipv4", "address"],
    "environment": ["environment", "env", "tier"],
    "location": ["location", "datacenter", "data center", "site", "region"],
    "cpu": ["cpu", "cores", "vcpu", "processors"],
    "memory": ["memory", "ram", "gb ram"],
    "storage": ["storage", "disk", "gb storage", "capacity"],

    # Organization fields
    "role": ["role", "title", "job title", "position"],
    "team": ["team", "group", "department", "org"],
    "headcount": ["headcount", "count", "# of", "number"],
    "fte": ["fte", "full time equivalent"],
    "reports_to": ["reports to", "manager", "supervisor", "reporting line"],

    # Vendor fields
    "vendor_name": ["vendor", "vendor name", "supplier", "provider"],
    "contract_type": ["contract type", "type", "agreement type"],
    "start_date": ["start date", "start", "effective date", "begin"],
    "end_date": ["end date", "end", "expiration", "expiry", "term end"],
    "acv": ["acv", "annual contract value", "annual value", "yearly value"],
    "tcv": ["tcv", "total contract value", "total value"],
}


def map_headers_to_schema(
    headers: List[str],
    inventory_type: str
) -> Dict[str, str]:
    """
    Map actual headers to schema field names.

    Args:
        headers: Actual column headers from table
        inventory_type: Detected inventory type

    Returns:
        Dict mapping schema field -> actual header
    """
    from stores.inventory_schemas import get_all_fields

    schema_fields = get_all_fields(inventory_type)
    header_map = {}

    normalized = {h.lower().strip(): h for h in headers}

    for field in schema_fields:
        # Try exact match first
        if field in normalized:
            header_map[field] = normalized[field]
            continue

        # Try aliases
        aliases = HEADER_ALIASES.get(field, [])
        for alias in aliases:
            if alias in normalized:
                header_map[field] = normalized[alias]
                break

    return header_map
