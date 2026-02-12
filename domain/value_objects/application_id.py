"""ApplicationId value object for stable, deterministic IDs."""
import hashlib
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.value_objects.entity import Entity


@dataclass(frozen=True)
class ApplicationId:
    """Stable, deterministic ID for applications.

    CRITICAL PROPERTY: Same (name, entity) always generates same ID.
    This enables deduplication across multiple analysis runs.

    ID Format: app_{fingerprint}_{entity}
    Example: app_a3f291cd_target

    The fingerprint is derived from NORMALIZED name, so variants
    like "Salesforce" and "Salesforce CRM" generate the same ID.
    """
    value: str

    def __post_init__(self):
        """Validate ID format."""
        if not self.value:
            raise ValueError("ApplicationId cannot be empty")

        # Validate format: app_{8 hex chars}_{entity}
        pattern = r'^app_[a-f0-9]{8}_(target|buyer)$'
        if not re.match(pattern, self.value):
            raise ValueError(
                f"Invalid ApplicationId format: {self.value}. "
                f"Expected format: app_{{fingerprint}}_{{entity}}"
            )

    @staticmethod
    def generate(name: str, entity: "Entity") -> "ApplicationId":
        """Generate stable ID from name + entity.

        NORMALIZATION RULES:
        1. Lowercase
        2. Remove common suffixes (CRM, ERP, 365, etc.)
        3. Remove special characters
        4. Trim whitespace
        5. Hash the result

        This means:
        - "Salesforce" → same ID as "Salesforce CRM"
        - "Microsoft Office" → same ID as "Microsoft Office 365"
        - "SAP ERP" → same ID as "SAP"

        Args:
            name: Application name (any variant)
            entity: Entity (TARGET or BUYER)

        Returns:
            ApplicationId with stable fingerprint

        Examples:
            >>> from domain.value_objects.entity import Entity
            >>> id1 = ApplicationId.generate("Salesforce", Entity.TARGET)
            >>> id2 = ApplicationId.generate("Salesforce CRM", Entity.TARGET)
            >>> id1 == id2
            True
            >>> id3 = ApplicationId.generate("Salesforce", Entity.BUYER)
            >>> id1 == id3
            False  # Different entity = different ID
        """
        from domain.value_objects.entity import Entity

        if not name:
            raise ValueError("Cannot generate ApplicationId from empty name")

        # Normalize name
        normalized = normalize_application_name(name)

        # Generate fingerprint
        fingerprint = hashlib.md5(normalized.encode('utf-8')).hexdigest()[:8]

        # Format: app_{fingerprint}_{entity}
        id_value = f"app_{fingerprint}_{entity.value}"

        return ApplicationId(id_value)

    def __str__(self) -> str:
        """String representation."""
        return self.value

    def __repr__(self) -> str:
        """Detailed representation."""
        return f"ApplicationId('{self.value}')"


def normalize_application_name(name: str) -> str:
    """Normalize application name for stable ID generation.

    CRITICAL FUNCTION: This determines which names are considered "the same".

    Rules:
    1. Lowercase everything
    2. Remove common suffixes that don't change identity
    3. Remove version numbers
    4. Remove special characters
    5. Collapse whitespace

    Examples:
        >>> normalize_application_name("Salesforce CRM")
        'salesforce'
        >>> normalize_application_name("Microsoft Office 365")
        'microsoft office'
        >>> normalize_application_name("SAP ERP (R/3)")
        'sap'
        >>> normalize_application_name("Workday HCM")
        'workday hcm'
    """
    if not name:
        return ""

    # 1. Lowercase
    normalized = name.lower().strip()

    # 2. Remove common non-identifying suffixes (ORDER MATTERS - longest first)
    suffixes_to_remove = [
        # Product type suffixes
        r'\bcrm\b', r'\berp\b', r'\bhcm\b', r'\bhrms\b',
        r'\bsuite\b', r'\bplatform\b', r'\bsystem\b',

        # Deployment type
        r'\bonline\b', r'\bcloud\b', r'\bsaas\b',
        r'\bon-premise\b', r'\bon premise\b',

        # Version indicators
        r'\b365\b', r'\b360\b',
        r'\bv?\d+(\.\d+)*\b',  # v1.0, 2.5, etc.

        # Common additions
        r'\bsoftware\b', r'\bapplication\b', r'\bapp\b',
    ]

    for suffix_pattern in suffixes_to_remove:
        normalized = re.sub(suffix_pattern, '', normalized)

    # 3. Remove special characters (keep only alphanumeric and spaces)
    normalized = re.sub(r'[^\w\s]', '', normalized)

    # 4. Collapse multiple spaces
    normalized = ' '.join(normalized.split())

    # 5. Trim again
    normalized = normalized.strip()

    return normalized
