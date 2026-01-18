"""
Cost Estimation Tools

Provides structured output schemas for the 4-stage cost refinement process.
Each stage has specific tools for capturing its output in a consistent format.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# TOOL DEFINITIONS
# =============================================================================

STAGE1_RESEARCH_TOOLS = [
    {
        "name": "record_research_findings",
        "description": "Record the research findings for a cost estimate validation",
        "input_schema": {
            "type": "object",
            "properties": {
                "is_range_reasonable": {
                    "type": "boolean",
                    "description": "Whether the original estimate range is reasonable"
                },
                "market_range": {
                    "type": "object",
                    "description": "Typical market range for this type of work",
                    "properties": {
                        "low": {"type": "number"},
                        "high": {"type": "number"},
                        "currency": {"type": "string", "default": "USD"}
                    }
                },
                "cost_drivers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Key cost drivers for this type of work"
                },
                "implied_assumptions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Assumptions the original estimate is likely based on"
                },
                "factors_higher": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Factors that could push costs higher"
                },
                "factors_lower": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Factors that could push costs lower"
                },
                "research_notes": {
                    "type": "string",
                    "description": "Additional research notes and reasoning"
                }
            },
            "required": ["is_range_reasonable", "cost_drivers", "implied_assumptions"]
        }
    }
]

STAGE2_REVIEW_TOOLS = [
    {
        "name": "record_critical_review",
        "description": "Record the critical review findings for a cost estimate",
        "input_schema": {
            "type": "object",
            "properties": {
                "gaps_identified": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "gap": {"type": "string"},
                            "impact": {"type": "string", "enum": ["high", "medium", "low"]},
                            "estimated_cost_impact": {"type": "string"}
                        }
                    },
                    "description": "Gaps or missing items in the estimate"
                },
                "risky_assumptions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "assumption": {"type": "string"},
                            "risk_level": {"type": "string", "enum": ["high", "medium", "low"]},
                            "what_if_wrong": {"type": "string"}
                        }
                    },
                    "description": "Assumptions that seem risky or unvalidated"
                },
                "understated_areas": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "area": {"type": "string"},
                            "why_understated": {"type": "string"},
                            "potential_additional_cost": {"type": "string"}
                        }
                    },
                    "description": "Areas where costs may be understated"
                },
                "overstated_areas": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "area": {"type": "string"},
                            "why_overstated": {"type": "string"},
                            "potential_savings": {"type": "string"}
                        }
                    },
                    "description": "Areas where costs may be overstated"
                },
                "missing_dependencies": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Dependencies or prerequisites not costed"
                },
                "overall_assessment": {
                    "type": "string",
                    "enum": ["estimate_low", "estimate_reasonable", "estimate_high"],
                    "description": "Overall assessment of the estimate"
                },
                "review_notes": {
                    "type": "string",
                    "description": "Additional review notes"
                }
            },
            "required": ["gaps_identified", "risky_assumptions", "overall_assessment"]
        }
    }
]

STAGE3_REFINEMENT_TOOLS = [
    {
        "name": "record_refined_estimate",
        "description": "Record the refined cost estimate with low/mid/high ranges",
        "input_schema": {
            "type": "object",
            "properties": {
                "low_estimate": {
                    "type": "object",
                    "properties": {
                        "amount": {"type": "number"},
                        "currency": {"type": "string", "default": "USD"},
                        "assumptions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Assumptions for this estimate"
                        },
                        "scenario": {
                            "type": "string",
                            "description": "What scenario leads to this estimate"
                        }
                    },
                    "required": ["amount", "assumptions", "scenario"]
                },
                "mid_estimate": {
                    "type": "object",
                    "properties": {
                        "amount": {"type": "number"},
                        "currency": {"type": "string", "default": "USD"},
                        "assumptions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Assumptions for this estimate"
                        },
                        "scenario": {
                            "type": "string",
                            "description": "What scenario leads to this estimate"
                        }
                    },
                    "required": ["amount", "assumptions", "scenario"]
                },
                "high_estimate": {
                    "type": "object",
                    "properties": {
                        "amount": {"type": "number"},
                        "currency": {"type": "string", "default": "USD"},
                        "assumptions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Assumptions for this estimate"
                        },
                        "scenario": {
                            "type": "string",
                            "description": "What scenario leads to this estimate"
                        }
                    },
                    "required": ["amount", "assumptions", "scenario"]
                },
                "range_logic": {
                    "type": "string",
                    "description": "Explanation of how the ranges were determined"
                },
                "key_variables": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "variable": {"type": "string"},
                            "impact_on_cost": {"type": "string"},
                            "current_assumption": {"type": "string"}
                        }
                    },
                    "description": "Key variables that drive the range"
                },
                "confidence_in_range": {
                    "type": "string",
                    "enum": ["high", "medium", "low"],
                    "description": "Confidence level in the refined range"
                }
            },
            "required": ["low_estimate", "mid_estimate", "high_estimate", "range_logic", "confidence_in_range"]
        }
    }
]

STAGE4_SUMMARY_TOOLS = [
    {
        "name": "record_cost_summary",
        "description": "Record the final cost estimation summary",
        "input_schema": {
            "type": "object",
            "properties": {
                "final_estimate": {
                    "type": "object",
                    "properties": {
                        "low": {"type": "number"},
                        "mid": {"type": "number"},
                        "high": {"type": "number"},
                        "currency": {"type": "string", "default": "USD"},
                        "recommended": {
                            "type": "string",
                            "enum": ["low", "mid", "high"],
                            "description": "Which estimate to use for planning"
                        }
                    },
                    "required": ["low", "mid", "high", "recommended"]
                },
                "confidence_level": {
                    "type": "string",
                    "enum": ["high", "medium", "low"],
                    "description": "Overall confidence in the estimate"
                },
                "confidence_rationale": {
                    "type": "string",
                    "description": "Why this confidence level"
                },
                "top_cost_drivers": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "driver": {"type": "string"},
                            "estimated_impact": {"type": "string"},
                            "controllable": {"type": "boolean"}
                        }
                    },
                    "maxItems": 5,
                    "description": "Top cost drivers"
                },
                "top_risks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "risk": {"type": "string"},
                            "likelihood": {"type": "string", "enum": ["high", "medium", "low"]},
                            "cost_impact_if_realized": {"type": "string"}
                        }
                    },
                    "maxItems": 5,
                    "description": "Top risks to the estimate"
                },
                "assumptions_to_validate": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "assumption": {"type": "string"},
                            "how_to_validate": {"type": "string"},
                            "impact_if_wrong": {"type": "string"}
                        }
                    },
                    "maxItems": 5,
                    "description": "Key assumptions that should be validated"
                },
                "executive_summary": {
                    "type": "string",
                    "description": "2-3 sentence executive summary of the cost estimate"
                }
            },
            "required": ["final_estimate", "confidence_level", "top_cost_drivers", "top_risks", "executive_summary"]
        }
    }
]


# =============================================================================
# LOGGING STRUCTURES
# =============================================================================

@dataclass
class StageLog:
    """Log entry for a single refinement stage"""
    stage_name: str
    stage_number: int
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    prompt_sent: str = ""
    response_received: str = ""
    tool_calls: List[Dict] = field(default_factory=list)
    tokens_input: int = 0
    tokens_output: int = 0
    error: Optional[str] = None

    def complete(self, response: str, tool_calls: List[Dict] = None):
        self.completed_at = datetime.now().isoformat()
        self.response_received = response
        self.tool_calls = tool_calls or []

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class CostEstimationLog:
    """Complete log for a work item's cost refinement process"""
    work_item_id: str
    work_item_title: str
    original_estimate: str
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    stages: List[StageLog] = field(default_factory=list)
    final_result: Optional[Dict] = None
    total_tokens: int = 0
    success: bool = False
    error: Optional[str] = None

    def add_stage(self, stage: StageLog):
        self.stages.append(stage)
        self.total_tokens += stage.tokens_input + stage.tokens_output

    def finalize(self, result: Dict = None, error: str = None):
        self.completed_at = datetime.now().isoformat()
        if error:
            self.error = error
            self.success = False
        else:
            self.final_result = result
            self.success = True

    def to_dict(self) -> Dict:
        return {
            "work_item_id": self.work_item_id,
            "work_item_title": self.work_item_title,
            "original_estimate": self.original_estimate,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total_stages": len(self.stages),
            "total_tokens": self.total_tokens,
            "success": self.success,
            "error": self.error,
            "stages": [s.to_dict() for s in self.stages],
            "final_result": self.final_result
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


@dataclass
class CostRefinementStore:
    """Store for all cost refinement results"""
    run_id: str
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    work_items_processed: int = 0
    work_items_succeeded: int = 0
    work_items_failed: int = 0
    logs: List[CostEstimationLog] = field(default_factory=list)
    results: List[Dict] = field(default_factory=list)

    def add_log(self, log: CostEstimationLog):
        self.logs.append(log)
        self.work_items_processed += 1
        if log.success:
            self.work_items_succeeded += 1
            if log.final_result:
                self.results.append({
                    "work_item_id": log.work_item_id,
                    "work_item_title": log.work_item_title,
                    "original_estimate": log.original_estimate,
                    **log.final_result
                })
        else:
            self.work_items_failed += 1

    def to_dict(self) -> Dict:
        return {
            "run_id": self.run_id,
            "started_at": self.started_at,
            "completed_at": datetime.now().isoformat(),
            "summary": {
                "total_processed": self.work_items_processed,
                "succeeded": self.work_items_succeeded,
                "failed": self.work_items_failed
            },
            "results": self.results,
            "detailed_logs": [log.to_dict() for log in self.logs]
        }

    def save(self, filepath: str):
        """Save the store to a JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Cost refinement results saved to {filepath}")


# =============================================================================
# TOOL EXECUTION HELPERS
# =============================================================================

def execute_costing_tool(tool_name: str, tool_input: Dict) -> Dict:
    """
    Execute a costing tool and return the result.
    Since costing tools are just for structured output capture,
    we simply validate and return the input.
    """
    # Validate tool_input is a dict
    if not isinstance(tool_input, dict):
        logger.error(f"Invalid tool input for {tool_name}: expected dict, got {type(tool_input)}")
        return {
            "status": "error",
            "message": f"Invalid input type: {type(tool_input).__name__}"
        }

    return {
        "status": "recorded",
        "tool_name": tool_name,
        "data": tool_input
    }


def get_tools_for_stage(stage: int) -> List[Dict]:
    """Get the appropriate tools for a refinement stage"""
    tools_map = {
        1: STAGE1_RESEARCH_TOOLS,
        2: STAGE2_REVIEW_TOOLS,
        3: STAGE3_REFINEMENT_TOOLS,
        4: STAGE4_SUMMARY_TOOLS
    }
    return tools_map.get(stage, [])
