"""
FactStore Adapter - Converts production FactStore to Domain Model.

This adapter bridges the gap between the existing production FactStore
(which stores observations from document parsing) and the new domain model
(which uses DDD patterns with aggregates and repositories).

Data Flow:
    FactStore (production) → FactStoreAdapter → Domain Model (experimental)

Created: 2026-02-12 (Integration Layer)
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging

from stores.fact_store import FactStore, Fact
from domain.kernel.entity import Entity
from domain.kernel.observation import Observation
from domain.applications.application import Application
from domain.applications.repository import ApplicationRepository
from domain.infrastructure.infrastructure import Infrastructure
from domain.infrastructure.repository import InfrastructureRepository
from domain.organization.person import Person
from domain.organization.repository import PersonRepository

logger = logging.getLogger(__name__)


class FactStoreAdapter:
    """
    Adapts FactStore (production) to Domain Model (experimental).

    Responsibilities:
    - Reads Facts from production FactStore
    - Converts Facts to domain Observations
    - Groups observations by entity (app/infrastructure)
    - Creates domain model aggregates (Application, Infrastructure)
    - Uses repositories to deduplicate and persist

    Example:
        adapter = FactStoreAdapter()

        # Load applications from FactStore
        fact_store = FactStore(deal_id="deal-123")
        app_repo = ApplicationRepository()

        applications = adapter.load_applications(fact_store, app_repo)
        # Result: List[Application] with deduplication applied
    """

    def __init__(self):
        """Initialize adapter."""
        self.stats = {
            "facts_processed": 0,
            "applications_created": 0,
            "infrastructure_created": 0,
            "people_created": 0,
            "observations_converted": 0,
            "duplicates_merged": 0,
        }

    def load_applications(
        self,
        fact_store: FactStore,
        repository: ApplicationRepository,
        entity_filter: Optional[Entity] = None
    ) -> List[Application]:
        """
        Load applications from FactStore into domain model.

        Process:
        1. Find all application facts in FactStore
        2. Convert each fact to domain Observation
        3. Group observations by (name, vendor, entity)
        4. Use repository.find_or_create() for deduplication
        5. Attach observations to applications

        Args:
            fact_store: Source FactStore with production facts
            repository: ApplicationRepository for deduplication
            entity_filter: Optional filter (Entity.TARGET or Entity.BUYER)

        Returns:
            List of Application aggregates with observations

        Example:
            fact_store = FactStore(deal_id="deal-123")
            app_repo = ApplicationRepository()

            # Load all applications
            apps = adapter.load_applications(fact_store, app_repo)

            # Load only target applications
            target_apps = adapter.load_applications(
                fact_store,
                app_repo,
                entity_filter=Entity.TARGET
            )
        """
        logger.info(f"Loading applications from FactStore (entity_filter={entity_filter})")

        # Get all application facts
        app_facts = self._get_facts_by_domain(fact_store, "applications")

        # Filter by entity if specified
        if entity_filter:
            app_facts = [f for f in app_facts if self._convert_entity(f.entity) == entity_filter]

        logger.info(f"Found {len(app_facts)} application facts to process")

        # Group facts by (name, vendor, entity, deal_id)
        grouped_facts = self._group_application_facts(app_facts)

        applications = []
        seen_ids = set()  # Track unique application IDs

        for key, facts in grouped_facts.items():
            name, vendor, entity, deal_id = key

            # Convert facts to observations
            observations = [self._fact_to_observation(f) for f in facts]

            # Use repository to find or create (deduplication)
            app = repository.find_or_create(
                name=name,
                vendor=vendor,
                entity=entity,
                deal_id=deal_id,
                observations=observations
            )

            # Only add if not already in list (repository deduplicates, but we may process same key multiple times)
            if app.id not in seen_ids:
                applications.append(app)
                seen_ids.add(app.id)
                self.stats["applications_created"] += 1

            self.stats["observations_converted"] += len(observations)

        self.stats["facts_processed"] += len(app_facts)

        logger.info(
            f"Created {len(applications)} applications from {len(app_facts)} facts "
            f"({self.stats['observations_converted']} observations)"
        )

        return applications

    def load_infrastructure(
        self,
        fact_store: FactStore,
        repository: InfrastructureRepository,
        entity_filter: Optional[Entity] = None
    ) -> List[Infrastructure]:
        """
        Load infrastructure from FactStore into domain model.

        Process:
        1. Find all infrastructure facts in FactStore
        2. Convert each fact to domain Observation
        3. Group observations by (name, vendor, entity)
        4. Use repository.find_or_create() for deduplication
        5. Attach observations to infrastructure

        Args:
            fact_store: Source FactStore with production facts
            repository: InfrastructureRepository for deduplication
            entity_filter: Optional filter (Entity.TARGET or Entity.BUYER)

        Returns:
            List of Infrastructure aggregates with observations
        """
        logger.info(f"Loading infrastructure from FactStore (entity_filter={entity_filter})")

        # Get all infrastructure facts
        infra_facts = self._get_facts_by_domain(fact_store, "infrastructure")

        # Filter by entity if specified
        if entity_filter:
            infra_facts = [f for f in infra_facts if self._convert_entity(f.entity) == entity_filter]

        logger.info(f"Found {len(infra_facts)} infrastructure facts to process")

        # Group facts by (name, vendor, entity, deal_id)
        grouped_facts = self._group_infrastructure_facts(infra_facts)

        infrastructures = []
        seen_ids = set()  # Track unique infrastructure IDs

        for key, facts in grouped_facts.items():
            name, vendor, entity, deal_id = key

            # Convert facts to observations
            observations = [self._fact_to_observation(f) for f in facts]

            # Use repository to find or create (deduplication)
            infra = repository.find_or_create(
                name=name,
                vendor=vendor,
                entity=entity,
                deal_id=deal_id,
                observations=observations
            )

            # Only add if not already in list (repository deduplicates, but we may process same key multiple times)
            if infra.id not in seen_ids:
                infrastructures.append(infra)
                seen_ids.add(infra.id)
                self.stats["infrastructure_created"] += 1

            self.stats["observations_converted"] += len(observations)

        self.stats["facts_processed"] += len(infra_facts)

        logger.info(
            f"Created {len(infrastructures)} infrastructure items from {len(infra_facts)} facts "
            f"({self.stats['observations_converted']} observations)"
        )

        return infrastructures

    def load_people(
        self,
        fact_store: FactStore,
        repository: PersonRepository,
        entity_filter: Optional[Entity] = None
    ) -> List[Person]:
        """
        Load people from FactStore into domain model.

        Process:
        1. Find all organization facts in FactStore (person, team, department)
        2. Convert each fact to domain Observation
        3. Group observations by (name, entity) - NO vendor for people
        4. Use repository.find_or_create() for deduplication
        5. Attach observations to people

        Args:
            fact_store: Source FactStore with production facts
            repository: PersonRepository for deduplication
            entity_filter: Optional filter (Entity.TARGET or Entity.BUYER)

        Returns:
            List of Person aggregates with observations

        Example:
            fact_store = FactStore(deal_id="deal-123")
            person_repo = PersonRepository()

            # Load all people
            people = adapter.load_people(fact_store, person_repo)

            # Load only target people
            target_people = adapter.load_people(
                fact_store,
                person_repo,
                entity_filter=Entity.TARGET
            )
        """
        logger.info(f"Loading people from FactStore (entity_filter={entity_filter})")

        # Get all organization facts
        org_facts = self._get_facts_by_domain(fact_store, "organization")

        # Filter by entity if specified
        if entity_filter:
            org_facts = [f for f in org_facts if self._convert_entity(f.entity) == entity_filter]

        logger.info(f"Found {len(org_facts)} organization facts to process")

        # Group facts by (name, entity, deal_id) - NO vendor for people
        grouped_facts = self._group_people_facts(org_facts)

        people = []
        seen_ids = set()  # Track unique person IDs

        for key, facts in grouped_facts.items():
            name, entity, deal_id = key

            # Convert facts to observations
            observations = [self._fact_to_observation(f) for f in facts]

            # Use repository to find or create (deduplication)
            # Note: vendor is ALWAYS None for people
            person = repository.find_or_create(
                name=name,
                entity=entity,
                deal_id=deal_id,
                observations=observations
            )

            # Only add if not already in list
            if person.id not in seen_ids:
                people.append(person)
                seen_ids.add(person.id)
                self.stats["people_created"] += 1

            self.stats["observations_converted"] += len(observations)

        self.stats["facts_processed"] += len(org_facts)

        logger.info(
            f"Created {len(people)} people from {len(org_facts)} facts "
            f"({self.stats['observations_converted']} observations)"
        )

        return people

    def _get_facts_by_domain(self, fact_store: FactStore, domain: str) -> List[Fact]:
        """
        Get all facts for a specific domain.

        Args:
            fact_store: Source FactStore
            domain: Domain name ("applications", "infrastructure", etc.)

        Returns:
            List of Facts matching domain
        """
        return [
            fact for fact in fact_store.facts
            if fact.domain == domain
        ]

    def _group_application_facts(self, facts: List[Fact]) -> Dict[Tuple, List[Fact]]:
        """
        Group application facts by (name, vendor, entity, deal_id).

        This is the deduplication key - all facts with same key
        will be merged into one Application aggregate.

        Args:
            facts: List of application facts

        Returns:
            Dict mapping (name, vendor, entity, deal_id) → List[Fact]
        """
        grouped = {}

        for fact in facts:
            # Extract name from fact.item or fact.details
            name = fact.item or fact.details.get("name", "Unknown")

            # Extract vendor from fact.details
            vendor = fact.details.get("vendor") or fact.details.get("provider", "Unknown")

            # Convert entity
            entity = self._convert_entity(fact.entity)

            # Deal ID
            deal_id = fact.deal_id or "default"

            # Grouping key
            key = (name, vendor, entity, deal_id)

            if key not in grouped:
                grouped[key] = []
            grouped[key].append(fact)

        return grouped

    def _group_infrastructure_facts(self, facts: List[Fact]) -> Dict[Tuple, List[Fact]]:
        """
        Group infrastructure facts by (name, vendor, entity, deal_id).

        Args:
            facts: List of infrastructure facts

        Returns:
            Dict mapping (name, vendor, entity, deal_id) → List[Fact]
        """
        grouped = {}

        for fact in facts:
            # Extract name from fact.item or fact.details
            name = fact.item or fact.details.get("name", "Unknown")

            # Extract vendor from fact.details (may be None for on-prem)
            vendor = fact.details.get("vendor") or fact.details.get("provider")

            # Convert entity
            entity = self._convert_entity(fact.entity)

            # Deal ID
            deal_id = fact.deal_id or "default"

            # Grouping key (vendor can be None for infrastructure)
            key = (name, vendor, entity, deal_id)

            if key not in grouped:
                grouped[key] = []
            grouped[key].append(fact)

        return grouped

    def _group_people_facts(self, facts: List[Fact]) -> Dict[Tuple, List[Fact]]:
        """
        Group people facts by (name, entity, deal_id).

        Note: NO vendor for people - vendor is ALWAYS None.

        Args:
            facts: List of organization facts (person, team, department)

        Returns:
            Dict mapping (name, entity, deal_id) → List[Fact]
        """
        grouped = {}

        for fact in facts:
            # Extract name from fact.item or fact.details
            name = fact.item or fact.details.get("name", "Unknown")

            # Convert entity
            entity = self._convert_entity(fact.entity)

            # Deal ID
            deal_id = fact.deal_id or "default"

            # Grouping key (NO vendor for people)
            key = (name, entity, deal_id)

            if key not in grouped:
                grouped[key] = []
            grouped[key].append(fact)

        return grouped

    def _fact_to_observation(self, fact: Fact) -> Observation:
        """
        Convert FactStore Fact to domain Observation.

        Maps FactStore schema to domain model schema:
        - Fact.evidence → Observation.evidence
        - Fact.category → Observation.source_type (with mapping)
        - Fact.created_at → Observation.extracted_at
        - Fact.entity → Observation.entity (converted to Entity enum)
        - Fact.deal_id → Observation.deal_id
        - Fact.details → Observation.data

        Args:
            fact: Source Fact from FactStore

        Returns:
            Observation compatible with domain model
        """
        # Map fact category to observation source_type
        source_type = self._map_source_type(fact.category, fact.details)

        # Extract confidence (if available, default 0.5)
        confidence = fact.confidence_score if hasattr(fact, 'confidence_score') else 0.5

        # Extract evidence quote
        evidence_text = fact.evidence.get("exact_quote", "") if fact.evidence else ""
        if not evidence_text:
            evidence_text = f"From {fact.category} in {fact.source_document}"

        # Convert entity
        entity = self._convert_entity(fact.entity)

        # Parse timestamp
        try:
            extracted_at = datetime.fromisoformat(fact.created_at)
        except (ValueError, AttributeError):
            extracted_at = datetime.now()

        # Create observation
        return Observation(
            source_type=source_type,
            confidence=confidence,
            evidence=evidence_text,
            extracted_at=extracted_at,
            deal_id=fact.deal_id or "default",
            entity=entity,
            data=fact.details
        )

    def _map_source_type(self, category: str, details: Dict) -> str:
        """
        Map FactStore category to Observation source_type.

        FactStore categories are domain-specific (e.g., "hosting", "compute").
        Observation source_type is extraction-method-specific.

        Heuristic mapping:
        - If details came from table → "table"
        - If details came from LLM → "llm_prose" or "llm_assumption"
        - If manually entered → "manual"
        - Default → "table" (most facts come from tables)

        Args:
            category: FactStore category
            details: Fact details (may have hints)

        Returns:
            One of: "table", "llm_prose", "manual", "llm_assumption"
        """
        # Check for manual entry hint
        if details.get("source") == "manual":
            return "manual"

        # Check for LLM hint
        if details.get("extracted_by") == "llm":
            # Distinguish prose vs assumption
            if details.get("is_assumption", False):
                return "llm_assumption"
            return "llm_prose"

        # Default: assume table extraction (most common)
        return "table"

    def _convert_entity(self, entity_str: str) -> Entity:
        """
        Convert FactStore entity string to domain Entity enum.

        Args:
            entity_str: "target", "buyer", or other

        Returns:
            Entity.TARGET or Entity.BUYER
        """
        entity_lower = entity_str.lower().strip()
        if entity_lower == "target":
            return Entity.TARGET
        elif entity_lower == "buyer":
            return Entity.BUYER
        else:
            # Default to target if ambiguous
            logger.warning(f"Unknown entity '{entity_str}', defaulting to TARGET")
            return Entity.TARGET

    def get_stats(self) -> Dict[str, int]:
        """
        Get adapter statistics.

        Returns:
            Dict with conversion stats
        """
        return self.stats.copy()

    def reset_stats(self):
        """Reset statistics counters."""
        for key in self.stats:
            self.stats[key] = 0
