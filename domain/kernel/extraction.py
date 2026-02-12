"""
Extraction coordinator - Prevents double-counting.

CRITICAL: Prevents apps and infra from both extracting same entity from same doc.

Created: 2026-02-12 (Worker 1 - Kernel Foundation, Task-007)
"""

from typing import Dict, Set, Optional


class ExtractionCoordinator:
    """
    Prevents double-extraction from same source.

    Example problem this solves:
      - Document: "IT Landscape.pdf" page 5
      - Contains: "Salesforce CRM - $50K/year"
      - Application domain: Extracts as app
      - Infrastructure domain: Might try to extract as SaaS infrastructure
      - Result: Double-counted cost!

    This coordinator tracks what's been extracted to prevent overlap.

    Usage:
        coordinator = ExtractionCoordinator()

        # Application domain extracts
        if not coordinator.already_extracted("doc-123", "salesforce", "application"):
            app = extract_application(...)
            coordinator.mark_extracted("doc-123", "salesforce", "application")

        # Infrastructure domain checks
        if coordinator.already_extracted_by_any_domain("doc-123", "salesforce"):
            # Skip - already extracted by application domain
            pass
    """

    def __init__(self):
        """Initialize extraction coordinator."""
        # Key: "doc_id:domain", Value: set of extracted entity names
        self._extracted: Dict[str, Set[str]] = {}

    def mark_extracted(
        self,
        doc_id: str,
        entity_name: str,
        domain: str
    ) -> None:
        """
        Mark entity as extracted from document by domain.

        Args:
            doc_id: Document identifier (e.g., "doc-123", "IT_Landscape.pdf")
            entity_name: Entity name (e.g., "Salesforce", "AWS EC2")
            domain: Domain that extracted it (e.g., "application", "infrastructure")

        Example:
            coordinator.mark_extracted(
                "doc-123",
                "Salesforce CRM",
                "application"
            )
        """
        key = f"{doc_id}:{domain}"
        if key not in self._extracted:
            self._extracted[key] = set()

        # Store lowercased for case-insensitive matching
        self._extracted[key].add(entity_name.lower())

    def already_extracted(
        self,
        doc_id: str,
        entity_name: str,
        domain: str
    ) -> bool:
        """
        Check if entity already extracted from document by THIS domain.

        Args:
            doc_id: Document identifier
            entity_name: Entity name
            domain: Domain to check

        Returns:
            True if already extracted by this domain, False otherwise

        Example:
            # Check if application domain already extracted "Salesforce"
            if coordinator.already_extracted("doc-123", "Salesforce", "application"):
                # Skip - already extracted
                pass
        """
        key = f"{doc_id}:{domain}"
        return entity_name.lower() in self._extracted.get(key, set())

    def already_extracted_by_any_domain(
        self,
        doc_id: str,
        entity_name: str
    ) -> bool:
        """
        Check if entity extracted by ANY domain (cross-domain check).

        This is the key method for preventing double-counting.

        Args:
            doc_id: Document identifier
            entity_name: Entity name

        Returns:
            True if extracted by any domain, False otherwise

        Example:
            # Infrastructure domain checks before extracting
            if coordinator.already_extracted_by_any_domain("doc-123", "Salesforce"):
                # Skip - application domain already extracted this
                logger.info("Skipping Salesforce - already extracted by another domain")
            else:
                # Safe to extract
                infra = extract_infrastructure(...)
        """
        entity_lower = entity_name.lower()

        for domain_key, entities in self._extracted.items():
            # Check if this document has entities
            if doc_id in domain_key:
                if entity_lower in entities:
                    return True

        return False

    def get_extracting_domain(
        self,
        doc_id: str,
        entity_name: str
    ) -> Optional[str]:
        """
        Get which domain extracted this entity (for conflict resolution).

        Args:
            doc_id: Document identifier
            entity_name: Entity name

        Returns:
            Domain name if found, None otherwise

        Example:
            domain = coordinator.get_extracting_domain("doc-123", "Salesforce")
            if domain:
                logger.info(f"Salesforce already extracted by {domain} domain")
                # Returns: "application"
        """
        entity_lower = entity_name.lower()

        for domain_key, entities in self._extracted.items():
            if doc_id in domain_key and entity_lower in entities:
                # Extract domain from key "doc_id:domain" → "domain"
                return domain_key.split(':')[-1]

        return None

    def get_extracted_count(self, doc_id: str, domain: str) -> int:
        """
        Get count of entities extracted from document by domain.

        Args:
            doc_id: Document identifier
            domain: Domain name

        Returns:
            Count of extracted entities

        Example:
            count = coordinator.get_extracted_count("doc-123", "application")
            print(f"Extracted {count} applications from doc-123")
        """
        key = f"{doc_id}:{domain}"
        return len(self._extracted.get(key, set()))

    def get_all_extracted(self, doc_id: str) -> Dict[str, int]:
        """
        Get extraction counts by domain for a document.

        Args:
            doc_id: Document identifier

        Returns:
            Dictionary mapping domain → count

        Example:
            counts = coordinator.get_all_extracted("doc-123")
            # Returns: {"application": 15, "infrastructure": 8, "organization": 12}
        """
        counts = {}

        for domain_key, entities in self._extracted.items():
            if doc_id in domain_key:
                domain = domain_key.split(':')[-1]
                counts[domain] = len(entities)

        return counts

    def clear_document(self, doc_id: str) -> None:
        """
        Clear all extraction records for a document.

        Args:
            doc_id: Document identifier

        Example:
            # Re-import document (clear previous extraction)
            coordinator.clear_document("doc-123")
        """
        keys_to_remove = [
            key for key in self._extracted.keys()
            if doc_id in key
        ]

        for key in keys_to_remove:
            del self._extracted[key]

    def clear_all(self) -> None:
        """Clear all extraction records."""
        self._extracted.clear()

    def __len__(self) -> int:
        """Return total number of extracted entities across all documents."""
        return sum(len(entities) for entities in self._extracted.values())

    def __repr__(self) -> str:
        """Return string representation for debugging."""
        total = len(self)
        docs = len(set(key.split(':')[0] for key in self._extracted.keys()))
        return f"ExtractionCoordinator({total} entities from {docs} documents)"
