"""
Inventory Adapter - Converts Domain Model to production InventoryStore.

This adapter writes domain model aggregates back to the production InventoryStore
so the web UI can display them.

Data Flow:
    Domain Model (experimental) → InventoryAdapter → InventoryStore (production UI)

Created: 2026-02-12 (Integration Layer)
"""

from typing import List, Dict, Any, Optional
import logging

from stores.inventory_store import InventoryStore
from domain.kernel.entity import Entity
from domain.applications.application import Application
from domain.infrastructure.infrastructure import Infrastructure
from domain.organization.person import Person

logger = logging.getLogger(__name__)


class InventoryAdapter:
    """
    Adapts Domain Model to InventoryStore (production UI).

    Responsibilities:
    - Converts domain aggregates (Application, Infrastructure) to InventoryItems
    - Writes to production InventoryStore
    - Handles entity conversion (Entity enum → string)
    - Tracks source_fact_ids for bidirectional linking

    Example:
        adapter = InventoryAdapter()
        inventory_store = InventoryStore(deal_id="deal-123")

        # Sync applications to inventory
        applications = [app1, app2, app3]
        adapter.sync_applications(applications, inventory_store)

        # Now inventory_store has applications visible in UI
    """

    def __init__(self):
        """Initialize adapter."""
        self.stats = {
            "applications_synced": 0,
            "infrastructure_synced": 0,
            "items_added": 0,
            "items_updated": 0,
        }

    def sync_applications(
        self,
        applications: List[Application],
        inventory_store: InventoryStore,
        source_fact_ids: Optional[Dict[str, List[str]]] = None
    ) -> List[str]:
        """
        Sync applications from domain model to InventoryStore.

        For each Application:
        1. Convert to InventoryStore data format
        2. Check if exists in inventory (by domain ID)
        3. Add or update inventory item

        Args:
            applications: List of Application aggregates
            inventory_store: Target InventoryStore for UI
            source_fact_ids: Optional mapping of app.id → List[fact_id]

        Returns:
            List of inventory item IDs created/updated

        Example:
            apps = [app1, app2, app3]
            inventory = InventoryStore(deal_id="deal-123")

            item_ids = adapter.sync_applications(apps, inventory)
            # item_ids = ["I-APP-a3f291", "I-APP-b4e8f2", ...]
        """
        logger.info(f"Syncing {len(applications)} applications to InventoryStore")

        item_ids = []

        for app in applications:
            # Convert application to inventory data
            data = self._application_to_inventory_data(app)

            # Entity string
            entity_str = self._entity_to_string(app.entity)

            # Source fact IDs (if provided)
            fact_ids = source_fact_ids.get(app.id, []) if source_fact_ids else []

            # Add to inventory
            # InventoryStore.add_item() handles deduplication via content-based ID
            item_id = inventory_store.add_item(
                inventory_type="application",
                data=data,
                entity=entity_str,
                deal_id=app.deal_id,
                source_file="domain_model",  # Mark as coming from domain model
                source_type="domain_model"
            )

            # Update source_fact_ids if provided
            if fact_ids:
                item = inventory_store.get_item(item_id)
                if item:
                    item.source_fact_ids = fact_ids
                    inventory_store.update_item(item_id, {"source_fact_ids": fact_ids})

            item_ids.append(item_id)
            self.stats["applications_synced"] += 1
            self.stats["items_added"] += 1

        logger.info(f"Synced {len(applications)} applications ({len(item_ids)} inventory items)")

        return item_ids

    def sync_infrastructure(
        self,
        infrastructures: List[Infrastructure],
        inventory_store: InventoryStore,
        source_fact_ids: Optional[Dict[str, List[str]]] = None
    ) -> List[str]:
        """
        Sync infrastructure from domain model to InventoryStore.

        Args:
            infrastructures: List of Infrastructure aggregates
            inventory_store: Target InventoryStore for UI
            source_fact_ids: Optional mapping of infra.id → List[fact_id]

        Returns:
            List of inventory item IDs created/updated
        """
        logger.info(f"Syncing {len(infrastructures)} infrastructure items to InventoryStore")

        item_ids = []

        for infra in infrastructures:
            # Convert infrastructure to inventory data
            data = self._infrastructure_to_inventory_data(infra)

            # Entity string
            entity_str = self._entity_to_string(infra.entity)

            # Source fact IDs (if provided)
            fact_ids = source_fact_ids.get(infra.id, []) if source_fact_ids else []

            # Add to inventory
            item_id = inventory_store.add_item(
                inventory_type="infrastructure",
                data=data,
                entity=entity_str,
                deal_id=infra.deal_id,
                source_file="domain_model",
                source_type="domain_model"
            )

            # Update source_fact_ids if provided
            if fact_ids:
                item = inventory_store.get_item(item_id)
                if item:
                    item.source_fact_ids = fact_ids
                    inventory_store.update_item(item_id, {"source_fact_ids": fact_ids})

            item_ids.append(item_id)
            self.stats["infrastructure_synced"] += 1
            self.stats["items_added"] += 1

        logger.info(f"Synced {len(infrastructures)} infrastructure ({len(item_ids)} inventory items)")

        return item_ids

    def sync_people(
        self,
        people: List['Person'],
        inventory_store: InventoryStore,
        source_fact_ids: Optional[Dict[str, List[str]]] = None
    ) -> List[str]:
        """
        Sync people from domain model to InventoryStore.

        Args:
            people: List of Person aggregates
            inventory_store: Target InventoryStore for UI
            source_fact_ids: Optional mapping of person.id → List[fact_id]

        Returns:
            List of inventory item IDs created/updated
        """
        logger.info(f"Syncing {len(people)} people to InventoryStore")

        item_ids = []

        for person in people:
            # Convert person to inventory data
            data = self._person_to_inventory_data(person)

            # Entity string
            entity_str = self._entity_to_string(person.entity)

            # Source fact IDs (if provided)
            fact_ids = source_fact_ids.get(person.id, []) if source_fact_ids else []

            # Add to inventory (organization domain)
            item_id = inventory_store.add_item(
                inventory_type="organization",
                data=data,
                entity=entity_str,
                deal_id=person.deal_id,
                source_file="domain_model",
                source_type="domain_model"
            )

            # Update source_fact_ids if provided
            if fact_ids:
                item = inventory_store.get_item(item_id)
                if item:
                    item.source_fact_ids = fact_ids
                    inventory_store.update_item(item_id, {"source_fact_ids": fact_ids})

            item_ids.append(item_id)
            self.stats["people_synced"] = self.stats.get("people_synced", 0) + 1
            self.stats["items_added"] += 1

        logger.info(f"Synced {len(people)} people ({len(item_ids)} inventory items)")

        return item_ids

    def _application_to_inventory_data(self, app: Application) -> Dict[str, Any]:
        """
        Convert Application aggregate to InventoryStore data dict.

        Maps domain model fields to inventory data format:
        - app.name → data["name"]
        - app.vendor → data["vendor"]
        - Observations → aggregated into data fields

        Args:
            app: Application aggregate

        Returns:
            Dict compatible with InventoryStore
        """
        data = {
            "name": app.name,
            "vendor": app.vendor,
            "domain_id": app.id,  # Store domain ID for reverse lookup
        }

        # Aggregate data from observations
        # Priority: manual > table > llm_prose > llm_assumption
        observations_by_priority = sorted(
            app.observations,
            key=lambda obs: obs.get_priority_score(),
            reverse=True
        )

        # Extract common fields from highest priority observations
        for obs in observations_by_priority:
            obs_data = obs.data

            # Cost
            if "cost" in obs_data and "cost" not in data:
                data["cost"] = obs_data["cost"]

            # Users
            if "users" in obs_data and "users" not in data:
                data["users"] = obs_data["users"]

            # Category
            if "category" in obs_data and "category" not in data:
                data["category"] = obs_data["category"]

            # Version
            if "version" in obs_data and "version" not in data:
                data["version"] = obs_data["version"]

            # Description
            if "description" in obs_data and "description" not in data:
                data["description"] = obs_data["description"]

        # Add observation count
        data["observation_count"] = len(app.observations)

        # Add highest confidence
        if app.observations:
            data["confidence"] = max(obs.confidence for obs in app.observations)
        else:
            data["confidence"] = 0.5

        return data

    def _infrastructure_to_inventory_data(self, infra: Infrastructure) -> Dict[str, Any]:
        """
        Convert Infrastructure aggregate to InventoryStore data dict.

        Args:
            infra: Infrastructure aggregate

        Returns:
            Dict compatible with InventoryStore
        """
        data = {
            "name": infra.name,
            "vendor": infra.vendor,  # May be None for on-prem
            "domain_id": infra.id,  # Store domain ID for reverse lookup
        }

        # Aggregate data from observations
        observations_by_priority = sorted(
            infra.observations,
            key=lambda obs: obs.get_priority_score(),
            reverse=True
        )

        # Extract common fields from highest priority observations
        for obs in observations_by_priority:
            obs_data = obs.data

            # Cost
            if "cost" in obs_data and "cost" not in data:
                data["cost"] = obs_data["cost"]

            # Environment (prod, dev, test)
            if "environment" in obs_data and "environment" not in data:
                data["environment"] = obs_data["environment"]

            # Type (server, database, network, etc.)
            if "type" in obs_data and "type" not in data:
                data["type"] = obs_data["type"]

            # Location (on-prem, AWS, Azure, etc.)
            if "location" in obs_data and "location" not in data:
                data["location"] = obs_data["location"]

            # Description
            if "description" in obs_data and "description" not in data:
                data["description"] = obs_data["description"]

        # Add observation count
        data["observation_count"] = len(infra.observations)

        # Add highest confidence
        if infra.observations:
            data["confidence"] = max(obs.confidence for obs in infra.observations)
        else:
            data["confidence"] = 0.5

        return data

    def _person_to_inventory_data(self, person: 'Person') -> Dict[str, Any]:
        """
        Convert Person aggregate to InventoryStore data dict.

        Args:
            person: Person aggregate

        Returns:
            Dict compatible with InventoryStore
        """
        data = {
            "name": person.name,
            "vendor": None,  # People always have vendor=None
            "domain_id": person.id,  # Store domain ID for reverse lookup
        }

        # Aggregate data from observations
        observations_by_priority = sorted(
            person.observations,
            key=lambda obs: obs.get_priority_score(),
            reverse=True
        )

        # Extract common fields from highest priority observations
        for obs in observations_by_priority:
            obs_data = obs.data

            # Role/title
            if "role" in obs_data and "role" not in data:
                data["role"] = obs_data["role"]

            # Department
            if "department" in obs_data and "department" not in data:
                data["department"] = obs_data["department"]

            # Title
            if "title" in obs_data and "title" not in data:
                data["title"] = obs_data["title"]

        # Add observation count
        data["observation_count"] = len(person.observations)

        # Add highest confidence
        if person.observations:
            data["confidence"] = max(obs.confidence for obs in person.observations)
        else:
            data["confidence"] = 0.5

        return data

    def _entity_to_string(self, entity: Entity) -> str:
        """
        Convert domain Entity enum to InventoryStore entity string.

        Args:
            entity: Entity.TARGET or Entity.BUYER

        Returns:
            "target" or "buyer"
        """
        return entity.value  # Entity enum has .value = "target" or "buyer"

    def get_stats(self) -> Dict[str, int]:
        """
        Get adapter statistics.

        Returns:
            Dict with sync stats
        """
        return self.stats.copy()

    def reset_stats(self):
        """Reset statistics counters."""
        for key in self.stats:
            self.stats[key] = 0
