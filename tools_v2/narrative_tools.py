"""
Narrative Tools for Investment Thesis Generation.

These tools are used by narrative agents to produce presentation content
for each domain. The output is structured for direct use in the HTML presentation.

Thread Safety:
    NarrativeStore is designed for concurrent access from multiple narrative agents.
    All mutating operations are protected by an RLock.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
import json
import threading
import os
import tempfile


@dataclass
class DomainNarrative:
    """Narrative content for a single domain slide."""
    domain: str
    so_what: str  # One sentence - the key implication
    considerations: List[str]  # 3-5 bullet points
    narrative: str  # The story - 2-3 paragraphs, candid tone
    cost_summary: str  # Cost impact statement
    key_facts: List[str]  # Fact IDs that support this narrative
    sources: List[str]  # Source document references
    confidence: str  # high, medium, low

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CostNarrative:
    """Cost synthesis narrative for executive presentation."""
    total_range: Dict[str, float]  # {'low': X, 'high': Y}
    by_phase: Dict[str, Dict[str, Any]]  # Day_1, Day_100, Post_100
    by_domain: Dict[str, Dict[str, Any]]  # Per-domain breakdown
    by_owner: Dict[str, Dict[str, Any]]  # buyer vs target
    executive_summary: str  # 2-3 paragraph cost narrative
    key_drivers: List[str]  # Top 3-5 cost drivers
    assumptions: List[str]  # Key assumptions behind estimates
    risks_to_estimates: List[str]  # What could change the numbers

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class NarrativeStore:
    """
    Stores all narrative content for the investment thesis presentation.

    Thread Safety:
        All mutating operations (add_domain_narrative, set_cost_narrative)
        are protected by an RLock for safe concurrent access from parallel agents.
    """

    def __init__(self):
        self.domain_narratives: Dict[str, DomainNarrative] = {}
        self.cost_narrative: Optional[CostNarrative] = None
        self.executive_thesis: Optional[str] = None
        self.open_questions_narrative: Optional[str] = None
        self._lock = threading.RLock()

    def add_domain_narrative(self, narrative: DomainNarrative):
        """Add a domain narrative (thread-safe)."""
        with self._lock:
            self.domain_narratives[narrative.domain] = narrative

    def set_cost_narrative(self, narrative: CostNarrative):
        """Set the cost synthesis narrative (thread-safe)."""
        with self._lock:
            self.cost_narrative = narrative

    def get_domain_narrative(self, domain: str) -> Optional[DomainNarrative]:
        """Get narrative for a specific domain (thread-safe)."""
        with self._lock:
            return self.domain_narratives.get(domain)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (thread-safe)."""
        with self._lock:
            return {
                'domain_narratives': {
                    k: v.to_dict() for k, v in self.domain_narratives.items()
                },
                'cost_narrative': self.cost_narrative.to_dict() if self.cost_narrative else None,
                'executive_thesis': self.executive_thesis,
                'open_questions_narrative': self.open_questions_narrative
            }

    def save(self, path: str):
        """
        Save narrative store to JSON (atomic write).

        Uses a temp file and rename for atomic operation to prevent
        partial writes from corrupting the file.
        """
        try:
            # Ensure directory exists
            dir_path = os.path.dirname(path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)

            # Write to temp file first, then move (atomic)
            fd, temp_path = tempfile.mkstemp(
                dir=dir_path if dir_path else '.',
                suffix='.json'
            )
            
            # Register temp file for cleanup on interrupt
            try:
                from tools_v2.cleanup_handler import register_temp_file, unregister_temp_file
                register_temp_file(temp_path)
            except ImportError:
                pass  # Cleanup handler not available
            try:
                from tools_v2.io_utils import retry_io
                
                @retry_io(max_retries=3, exceptions=(IOError, OSError))
                def _write_file():
                    with os.fdopen(fd, 'w') as f:
                        json.dump(self.to_dict(), f, indent=2)
                
                _write_file()
                os.replace(temp_path, path)  # Atomic on POSIX
                
                # Unregister temp file after successful write
                try:
                    from tools_v2.cleanup_handler import unregister_temp_file
                    unregister_temp_file(temp_path)
                except ImportError:
                    pass
            except Exception:
                # Clean up temp file on error
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
                raise
        except IOError as e:
            raise IOError(f"Failed to save narrative store to {path}: {e}")

    @classmethod
    def load(cls, path: str) -> 'NarrativeStore':
        """
        Load narrative store from JSON.

        Raises:
            IOError: If file cannot be read
            ValueError: If JSON is invalid or data structure is wrong
        """
        try:
            with open(path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {path}: {e}")
        except IOError as e:
            raise IOError(f"Failed to load narrative store from {path}: {e}")

        if not isinstance(data, dict):
            raise ValueError(f"Expected dict in {path}, got {type(data).__name__}")

        store = cls()

        for domain, nar_data in data.get('domain_narratives', {}).items():
            try:
                store.domain_narratives[domain] = DomainNarrative(**nar_data)
            except TypeError as e:
                raise ValueError(f"Invalid DomainNarrative data for {domain}: {e}")

        if data.get('cost_narrative'):
            try:
                store.cost_narrative = CostNarrative(**data['cost_narrative'])
            except TypeError as e:
                raise ValueError(f"Invalid CostNarrative data: {e}")

        store.executive_thesis = data.get('executive_thesis')
        store.open_questions_narrative = data.get('open_questions_narrative')

        return store


# Tool definitions for narrative agents
NARRATIVE_TOOLS = [
    {
        "name": "write_domain_narrative",
        "description": """Write the narrative content for a domain slide in the investment thesis presentation.

This should be written in a candid, partner-level tone - like a Big Four partner explaining
the situation to a PE deal team. Be direct about what works and what doesn't.

The narrative should tell a story, not just list facts. Explain the implications.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "so_what": {
                    "type": "string",
                    "description": "One sentence that captures THE key implication for the buyer. Example: 'Hybrid cloud footprint with aging on-prem. Expect modernization costs within 18 months.'"
                },
                "considerations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "3-5 key considerations. Each should be a complete thought. Include specific details where available (e.g., '47 AWS accounts, $6.7M annual spend')."
                },
                "narrative": {
                    "type": "string",
                    "description": "The story - 2-3 paragraphs explaining the situation candidly. What's there, what the concerns are, what the buyer will deal with. Not salesy, not alarmist - just practical."
                },
                "cost_summary": {
                    "type": "string",
                    "description": "Cost impact statement for this domain. Example: '$1.2M - $3.5M, primarily in Day 100 modernization work.'"
                },
                "key_facts": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Fact IDs (F-XXX-NNN) that support this narrative. These create the evidence chain."
                },
                "sources": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Source documents referenced (e.g., 'IT Inventory.xlsx', 'Cloud Cost Report Q4')."
                },
                "confidence": {
                    "type": "string",
                    "enum": ["high", "medium", "low"],
                    "description": "Confidence in this narrative based on available documentation."
                }
            },
            "required": ["so_what", "considerations", "narrative", "cost_summary", "key_facts", "confidence"]
        }
    },
    {
        "name": "complete_narrative",
        "description": "Signal that the domain narrative is complete.",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "Brief summary of what was covered in this domain's narrative."
                }
            },
            "required": ["summary"]
        }
    }
]


COST_SYNTHESIS_TOOLS = [
    {
        "name": "write_cost_narrative",
        "description": """Write the comprehensive cost synthesis narrative for the investment thesis.

This should aggregate all domain costs into a coherent story about what the integration will cost.
Be specific about what drives the numbers and what assumptions are baked in.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "executive_summary": {
                    "type": "string",
                    "description": "2-3 paragraph narrative explaining the overall cost picture. What's driving costs, what's optional vs required, what depends on buyer decisions."
                },
                "key_drivers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Top 3-5 cost drivers with their approximate impact. Example: 'PAM implementation ($250K-$500K) - critical security gap'"
                },
                "assumptions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Key assumptions behind the estimates. Example: 'Assumes target IT team stays through Day 100'"
                },
                "risks_to_estimates": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "What could change the numbers. Example: 'If colo contracts have early termination penalties, add $500K-$1M'"
                }
            },
            "required": ["executive_summary", "key_drivers", "assumptions", "risks_to_estimates"]
        }
    },
    {
        "name": "complete_cost_synthesis",
        "description": "Signal that the cost synthesis is complete.",
        "input_schema": {
            "type": "object",
            "properties": {
                "total_range_summary": {
                    "type": "string",
                    "description": "Final total cost range statement."
                }
            },
            "required": ["total_range_summary"]
        }
    }
]


def _validate_domain_narrative_input(tool_input: Dict[str, Any]) -> Optional[str]:
    """
    Validate write_domain_narrative tool input.

    Returns:
        Error message if validation fails, None if valid.
    """
    # Check required fields
    required_fields = ['so_what', 'considerations', 'narrative', 'cost_summary', 'confidence']
    missing = [f for f in required_fields if f not in tool_input]
    if missing:
        return f"Missing required fields: {', '.join(missing)}"

    # Validate types
    if not isinstance(tool_input.get('so_what'), str) or not tool_input['so_what'].strip():
        return "so_what must be a non-empty string"

    if not isinstance(tool_input.get('considerations'), list):
        return "considerations must be a list"

    if len(tool_input['considerations']) == 0:
        return "considerations must have at least one item"

    if not isinstance(tool_input.get('narrative'), str) or not tool_input['narrative'].strip():
        return "narrative must be a non-empty string"

    if not isinstance(tool_input.get('cost_summary'), str):
        return "cost_summary must be a string"

    # Validate confidence enum
    valid_confidence = ['high', 'medium', 'low']
    if tool_input.get('confidence') not in valid_confidence:
        return f"confidence must be one of: {', '.join(valid_confidence)}"

    # Validate optional list fields
    if 'key_facts' in tool_input and not isinstance(tool_input['key_facts'], list):
        return "key_facts must be a list"

    if 'sources' in tool_input and not isinstance(tool_input['sources'], list):
        return "sources must be a list"

    return None


def execute_narrative_tool(
    tool_name: str,
    tool_input: Dict[str, Any],
    narrative_store: NarrativeStore,
    domain: str
) -> Dict[str, Any]:
    """
    Execute a narrative tool and update the store.

    Args:
        tool_name: Name of the tool to execute
        tool_input: Input parameters from Claude
        narrative_store: Store to update
        domain: Domain this narrative is for

    Returns:
        Dict with status and message
    """
    if tool_name == "write_domain_narrative":
        # Validate input
        error = _validate_domain_narrative_input(tool_input)
        if error:
            return {"status": "error", "message": f"Validation failed: {error}"}

        try:
            narrative = DomainNarrative(
                domain=domain,
                so_what=tool_input['so_what'],
                considerations=tool_input['considerations'],
                narrative=tool_input['narrative'],
                cost_summary=tool_input['cost_summary'],
                key_facts=tool_input.get('key_facts', []),
                sources=tool_input.get('sources', []),
                confidence=tool_input['confidence']
            )
            narrative_store.add_domain_narrative(narrative)
            return {
                "status": "success",
                "message": f"Domain narrative for {domain} recorded."
            }
        except Exception as e:
            return {"status": "error", "message": f"Failed to create narrative: {e}"}

    elif tool_name == "complete_narrative":
        summary = tool_input.get('summary', 'No summary provided')
        return {
            "status": "complete",
            "message": f"Narrative complete: {summary}"
        }

    elif tool_name == "write_cost_narrative":
        # Cost narrative is set by the cost synthesis agent
        return {
            "status": "success",
            "message": "Cost narrative recorded."
        }

    elif tool_name == "complete_cost_synthesis":
        summary = tool_input.get('total_range_summary', 'No summary provided')
        return {
            "status": "complete",
            "message": f"Cost synthesis complete: {summary}"
        }

    else:
        return {
            "status": "error",
            "message": f"Unknown tool: {tool_name}"
        }
