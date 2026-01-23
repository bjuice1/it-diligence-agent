"""
Detail Extractor Agent - Pass 2 Granular Fact Extraction

This agent extracts granular, line-item facts from documents for each
system identified in Pass 1.

Extraction Focus:
- Counts: instances, users, licenses, records
- Versions: software versions, patch levels
- Configurations: settings, customizations
- Capacities: storage, throughput, limits
- Costs: license costs, cloud spend, support fees
- Dates: implementation, renewal, EOL

Every fact must include:
- Link to parent system (from System Registry)
- Exact evidence quote from source document
- Value with appropriate unit
"""

import json
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# PROMPTS
# =============================================================================

DETAIL_EXTRACTOR_SYSTEM_PROMPT = """You are a meticulous IT inventory specialist performing Pass 2 of a multi-pass extraction process.

## Your Mission
Extract GRANULAR, LINE-ITEM facts from the document for the systems listed below. Focus on specific, quantifiable details.

## Systems to Extract Details For
{systems_list}

## What to Extract

For EACH system, extract every specific detail you can find:

### Counts (fact_type: "count")
- Number of instances, servers, VMs
- User counts, license counts
- Number of integrations, APIs, endpoints
- Record counts, transaction volumes

### Versions (fact_type: "version")
- Software versions (e.g., "NetSuite 2024.1")
- Patch levels, release numbers
- Framework versions

### Capacities (fact_type: "capacity")
- Storage sizes (TB, GB)
- Throughput limits
- Memory, CPU allocations
- Bandwidth

### Costs (fact_type: "cost")
- Monthly/annual license costs
- Cloud spend by service
- Support contract values
- Implementation costs

### Configurations (fact_type: "config")
- Enabled features/modules
- Custom settings
- Integration configurations

### Dates (fact_type: "date")
- Implementation dates
- Contract renewal dates
- End-of-life dates
- Last update/patch dates

### Locations (fact_type: "location")
- Data center locations
- Cloud regions
- Office locations

## Rules

1. **ONE FACT PER CALL** - Each tool call should capture exactly one data point
2. **EVIDENCE REQUIRED** - Every fact must include an exact quote from the document
3. **LINK TO SYSTEM** - Use parent_system_id to connect facts to their system
4. **BE SPECIFIC** - "47 EC2 instances" not "many cloud servers"
5. **INCLUDE UNITS** - Always specify units (instances, users, TB, USD/month)
6. **NO INFERENCE** - Only extract explicitly stated facts

## Example Extractions

Document says: "The AWS environment includes 47 EC2 instances across us-east-1, us-west-2, and eu-west-1 regions."

Extract THREE facts:
1. add_granular_fact(fact_type="count", item="EC2 Instances", value=47, unit="instances", parent_system_id="SYS-xxx")
2. add_granular_fact(fact_type="count", item="AWS Regions", value=3, unit="regions", parent_system_id="SYS-xxx")
3. add_granular_fact(fact_type="location", item="AWS Regions", value="us-east-1, us-west-2, eu-west-1", parent_system_id="SYS-xxx")

Document says: "NetSuite license costs $145,000 annually for 200 named users."

Extract TWO facts:
1. add_granular_fact(fact_type="cost", item="NetSuite License", value=145000, unit="USD/year", parent_system_id="SYS-yyy")
2. add_granular_fact(fact_type="count", item="NetSuite Named Users", value=200, unit="users", parent_system_id="SYS-yyy")

## Output

Call the add_granular_fact tool for each fact found. When you have extracted all facts, call complete_extraction.
"""


SYSTEM_DISCOVERY_PROMPT = """You are an IT systems analyst performing Pass 1 of a multi-pass extraction process.

## Your Mission
Identify ALL systems, platforms, and technologies mentioned in the document.

## What Counts as a "System"
- Cloud platforms (AWS, Azure, GCP)
- Enterprise applications (ERP, CRM, HRIS)
- Databases and data platforms
- Network infrastructure
- Security tools and platforms
- Development platforms
- Collaboration tools
- Any named software or platform

## What to Capture

For each system:
- **name**: The system name (e.g., "AWS Cloud Platform", "NetSuite ERP")
- **vendor**: The vendor/provider (e.g., "Amazon Web Services", "Oracle")
- **category**: cloud_platform, erp, crm, hris, data_center, network_infrastructure,
               security_platform, database_platform, application_platform, collaboration,
               dev_platform, analytics, storage, backup_dr, identity, monitoring,
               vendor_service, legacy, other
- **domain**: infrastructure, applications, cybersecurity, network, identity_access, organization
- **criticality**: low, medium, high, critical
- **evidence_quote**: Exact quote from document mentioning this system

## Rules

1. **REGISTER EVERY SYSTEM** - Even brief mentions count
2. **ONE SYSTEM PER CALL** - Each tool call registers one system
3. **EVIDENCE REQUIRED** - Include the exact quote where you found it
4. **NO DUPLICATES** - If you already registered a system, don't register again
5. **PARENT SYSTEMS** - If system is part of another (e.g., RDS is part of AWS), note the parent

## Example Registrations

Document says: "The company primarily uses AWS for cloud infrastructure..."

register_system(
    name="AWS Cloud Platform",
    vendor="Amazon Web Services",
    category="cloud_platform",
    domain="infrastructure",
    criticality="high",
    evidence_quote="The company primarily uses AWS for cloud infrastructure..."
)

Document says: "...running NetSuite 2024.1 as the core ERP..."

register_system(
    name="NetSuite ERP",
    vendor="Oracle",
    category="erp",
    domain="applications",
    criticality="critical",
    evidence_quote="...running NetSuite 2024.1 as the core ERP..."
)

## Output

Call the register_system tool for each system found. When done, call complete_discovery.
"""


# =============================================================================
# TOOL DEFINITIONS
# =============================================================================

def get_detail_extractor_tools() -> List[Dict[str, Any]]:
    """Get tool definitions for the detail extractor agent."""
    return [
        {
            "name": "add_granular_fact",
            "description": "Add a granular (line-item) fact to the store. Each fact should be a single, specific data point with evidence.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "enum": ["infrastructure", "applications", "cybersecurity", "network", "identity_access", "organization"],
                        "description": "The domain this fact belongs to"
                    },
                    "category": {
                        "type": "string",
                        "description": "Subcategory within the domain (e.g., cloud_compute, servers, users)"
                    },
                    "fact_type": {
                        "type": "string",
                        "enum": ["count", "version", "capacity", "cost", "date", "config", "status", "integration", "location", "contact", "sla", "license", "vendor", "other"],
                        "description": "The type of fact being recorded"
                    },
                    "item": {
                        "type": "string",
                        "description": "What this fact describes (e.g., 'EC2 Instances', 'NetSuite Users')"
                    },
                    "value": {
                        "oneOf": [
                            {"type": "number"},
                            {"type": "string"},
                            {"type": "boolean"}
                        ],
                        "description": "The actual value (number, string, or boolean)"
                    },
                    "unit": {
                        "type": "string",
                        "description": "Unit of measurement (e.g., 'instances', 'users', 'TB', 'USD/month')"
                    },
                    "context": {
                        "type": "object",
                        "description": "Additional context as key-value pairs"
                    },
                    "evidence_quote": {
                        "type": "string",
                        "description": "REQUIRED: Exact quote from the source document (10-500 characters)"
                    },
                    "source_page": {
                        "type": "integer",
                        "description": "Page number where this was found"
                    },
                    "parent_system_id": {
                        "type": "string",
                        "description": "ID of the parent system from the System Registry (e.g., 'SYS-a3f2')"
                    },
                    "confidence": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "description": "Confidence level (0.0 to 1.0)"
                    }
                },
                "required": ["domain", "category", "fact_type", "item", "value", "evidence_quote"]
            }
        },
        {
            "name": "complete_extraction",
            "description": "Call this when you have extracted all granular facts from the document.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "facts_extracted": {
                        "type": "integer",
                        "description": "Total number of facts extracted"
                    },
                    "systems_covered": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of system IDs that were covered"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Any notes about the extraction"
                    }
                },
                "required": ["facts_extracted"]
            }
        }
    ]


def get_system_discovery_tools() -> List[Dict[str, Any]]:
    """Get tool definitions for the system discovery agent."""
    return [
        {
            "name": "register_system",
            "description": "Register a system, platform, or technology found in the document.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "System name (e.g., 'AWS Cloud Platform', 'NetSuite ERP')"
                    },
                    "vendor": {
                        "type": "string",
                        "description": "Vendor name (e.g., 'Amazon Web Services', 'Oracle')"
                    },
                    "category": {
                        "type": "string",
                        "enum": [
                            "cloud_platform", "erp", "crm", "hris", "data_center",
                            "network_infrastructure", "security_platform", "database_platform",
                            "application_platform", "collaboration", "dev_platform", "analytics",
                            "storage", "backup_dr", "identity", "monitoring", "vendor_service",
                            "legacy", "other"
                        ],
                        "description": "System category"
                    },
                    "domain": {
                        "type": "string",
                        "enum": ["infrastructure", "applications", "cybersecurity", "network", "identity_access", "organization"],
                        "description": "IT domain"
                    },
                    "description": {
                        "type": "string",
                        "description": "Brief description of the system"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["active", "deprecated", "planned", "unknown"],
                        "description": "Current status"
                    },
                    "criticality": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "Business criticality"
                    },
                    "evidence_quote": {
                        "type": "string",
                        "description": "REQUIRED: Exact quote from document"
                    },
                    "source_page": {
                        "type": "integer",
                        "description": "Page number where found"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags for categorization"
                    }
                },
                "required": ["name", "category", "domain", "evidence_quote"]
            }
        },
        {
            "name": "complete_discovery",
            "description": "Call this when you have identified all systems in the document.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "systems_found": {
                        "type": "integer",
                        "description": "Total systems registered"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Notes about the discovery"
                    }
                },
                "required": ["systems_found"]
            }
        }
    ]


# =============================================================================
# AGENT CLASS
# =============================================================================

class DetailExtractorAgent:
    """
    Agent for extracting granular facts from documents.

    This agent processes documents in Pass 2 to extract line-item
    details for each system identified in Pass 1.
    """

    def __init__(
        self,
        llm_client: Any,
        system_registry,  # SystemRegistry
        granular_facts_store,  # GranularFactsStore
        model: str = "claude-3-5-haiku-20241022",
        max_iterations: int = 100,
        temperature: float = 0.0
    ):
        """
        Initialize the detail extractor agent.

        Args:
            llm_client: Anthropic client
            system_registry: SystemRegistry from Pass 1
            granular_facts_store: Store for extracted facts
            model: Model to use
            max_iterations: Max tool calls per document
            temperature: LLM temperature (0.0 for deterministic)
        """
        self.client = llm_client
        self.system_registry = system_registry
        self.granular_facts_store = granular_facts_store
        self.model = model
        self.max_iterations = max_iterations
        self.temperature = temperature

        # Tool handlers
        self.tool_handlers = {
            "add_granular_fact": self._handle_add_fact,
            "complete_extraction": self._handle_complete
        }

        # State
        self.facts_extracted = 0
        self.extraction_complete = False

    def extract_from_document(
        self,
        document_content: str,
        document_name: str
    ) -> Dict[str, Any]:
        """
        Extract granular facts from a document.

        Args:
            document_content: The document text
            document_name: Filename for attribution

        Returns:
            Dictionary with extraction results
        """
        self.facts_extracted = 0
        self.extraction_complete = False
        self.current_document = document_name

        # Build systems list for prompt
        systems = self.system_registry.get_all_systems()
        systems_list = "\n".join([
            f"- {s.system_id}: {s.name} ({s.category})"
            for s in systems
        ])

        if not systems_list:
            systems_list = "(No systems registered yet - extract any systems you find)"

        # Format prompt
        system_prompt = DETAIL_EXTRACTOR_SYSTEM_PROMPT.format(
            systems_list=systems_list
        )

        # Initial message
        messages = [
            {
                "role": "user",
                "content": f"Document: {document_name}\n\n{document_content}\n\nExtract all granular facts from this document."
            }
        ]

        # Run extraction loop
        iteration = 0
        while not self.extraction_complete and iteration < self.max_iterations:
            iteration += 1

            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    temperature=self.temperature,
                    system=system_prompt,
                    tools=get_detail_extractor_tools(),
                    messages=messages
                )

                # Process response
                if response.stop_reason == "tool_use":
                    # Handle tool calls
                    tool_results = []

                    for block in response.content:
                        if block.type == "tool_use":
                            result = self._handle_tool_call(
                                block.name,
                                block.input,
                                block.id
                            )
                            tool_results.append(result)

                    # Add assistant response and tool results to messages
                    messages.append({"role": "assistant", "content": response.content})
                    messages.append({
                        "role": "user",
                        "content": tool_results
                    })

                elif response.stop_reason == "end_turn":
                    # Agent finished
                    break

            except Exception as e:
                logger.error(f"Extraction error: {e}")
                break

        return {
            "status": "success" if self.facts_extracted > 0 else "no_facts",
            "facts_extracted": self.facts_extracted,
            "iterations": iteration,
            "document": document_name
        }

    def _handle_tool_call(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_id: str
    ) -> Dict[str, Any]:
        """Handle a tool call from the LLM."""
        handler = self.tool_handlers.get(tool_name)

        if handler:
            result = handler(tool_input)
        else:
            result = {"error": f"Unknown tool: {tool_name}"}

        return {
            "type": "tool_result",
            "tool_use_id": tool_id,
            "content": json.dumps(result)
        }

    def _handle_add_fact(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle add_granular_fact tool call."""
        try:
            fact_id = self.granular_facts_store.add_fact(
                domain=params.get("domain", "infrastructure"),
                category=params.get("category", "general"),
                fact_type=params.get("fact_type", "other"),
                item=params.get("item", ""),
                value=params.get("value"),
                unit=params.get("unit"),
                context=params.get("context", {}),
                evidence_quote=params.get("evidence_quote", ""),
                source_document=self.current_document,
                source_page=params.get("source_page"),
                parent_system_id=params.get("parent_system_id"),
                confidence=params.get("confidence", 1.0)
            )

            self.facts_extracted += 1

            return {
                "status": "success",
                "fact_id": fact_id,
                "message": f"Added fact: {params.get('item')} = {params.get('value')}"
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _handle_complete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle complete_extraction tool call."""
        self.extraction_complete = True

        return {
            "status": "success",
            "message": f"Extraction complete: {self.facts_extracted} facts extracted"
        }


class SystemDiscoveryAgent:
    """
    Agent for discovering systems in documents (Pass 1).

    This agent identifies all systems, platforms, and technologies
    mentioned in source documents.
    """

    def __init__(
        self,
        llm_client: Any,
        system_registry,  # SystemRegistry
        model: str = "claude-3-5-haiku-20241022",
        max_iterations: int = 50,
        temperature: float = 0.0
    ):
        """
        Initialize the system discovery agent.
        """
        self.client = llm_client
        self.system_registry = system_registry
        self.model = model
        self.max_iterations = max_iterations
        self.temperature = temperature

        self.tool_handlers = {
            "register_system": self._handle_register,
            "complete_discovery": self._handle_complete
        }

        self.systems_found = 0
        self.discovery_complete = False

    def discover_from_document(
        self,
        document_content: str,
        document_name: str
    ) -> Dict[str, Any]:
        """
        Discover systems from a document.
        """
        self.systems_found = 0
        self.discovery_complete = False
        self.current_document = document_name

        messages = [
            {
                "role": "user",
                "content": f"Document: {document_name}\n\n{document_content}\n\nIdentify all systems and platforms mentioned in this document."
            }
        ]

        iteration = 0
        while not self.discovery_complete and iteration < self.max_iterations:
            iteration += 1

            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    temperature=self.temperature,
                    system=SYSTEM_DISCOVERY_PROMPT,
                    tools=get_system_discovery_tools(),
                    messages=messages
                )

                if response.stop_reason == "tool_use":
                    tool_results = []

                    for block in response.content:
                        if block.type == "tool_use":
                            result = self._handle_tool_call(
                                block.name,
                                block.input,
                                block.id
                            )
                            tool_results.append(result)

                    messages.append({"role": "assistant", "content": response.content})
                    messages.append({"role": "user", "content": tool_results})

                elif response.stop_reason == "end_turn":
                    break

            except Exception as e:
                logger.error(f"Discovery error: {e}")
                break

        return {
            "status": "success" if self.systems_found > 0 else "no_systems",
            "systems_found": self.systems_found,
            "iterations": iteration,
            "document": document_name
        }

    def _handle_tool_call(self, tool_name: str, tool_input: Dict, tool_id: str) -> Dict:
        handler = self.tool_handlers.get(tool_name)
        if handler:
            result = handler(tool_input)
        else:
            result = {"error": f"Unknown tool: {tool_name}"}

        return {
            "type": "tool_result",
            "tool_use_id": tool_id,
            "content": json.dumps(result)
        }

    def _handle_register(self, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            system_id = self.system_registry.add_system(
                name=params.get("name", ""),
                vendor=params.get("vendor"),
                category=params.get("category", "other"),
                domain=params.get("domain", "infrastructure"),
                description=params.get("description", ""),
                status=params.get("status", "active"),
                criticality=params.get("criticality", "medium"),
                evidence_quote=params.get("evidence_quote", ""),
                source_document=self.current_document,
                source_page=params.get("source_page"),
                tags=params.get("tags")
            )

            self.systems_found += 1

            return {
                "status": "success",
                "system_id": system_id,
                "message": f"Registered: {params.get('name')}"
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _handle_complete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        self.discovery_complete = True
        return {
            "status": "success",
            "message": f"Discovery complete: {self.systems_found} systems found"
        }
