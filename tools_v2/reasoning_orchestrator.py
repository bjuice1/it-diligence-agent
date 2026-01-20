"""
Reasoning Orchestrator

Central coordinator for the three-stage reasoning process.
Integrates with:
- FactStore (input)
- Three-stage reasoning (processing)
- Refinement sessions (iteration)
- Output formatting (delivery)

This is the main entry point for reasoning analysis.

ARCHITECTURE:

    FactStore ──► ORCHESTRATOR ──► Output
        │              │
        │    ┌─────────┼─────────┐
        │    │         │         │
        │    ▼         ▼         ▼
        │  Stage1    Stage2    Stage3
        │  (LLM)    (Rules)    (LLM)
        │    │         │         │
        │    └─────────┼─────────┘
        │              │
        └──────────────┘
              ▲
              │
        Refinement
         Session
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import json

logger = logging.getLogger(__name__)


@dataclass
class OrchestratorConfig:
    """Configuration for the reasoning orchestrator."""

    # Model selection
    stage1_model: str = "claude-sonnet-4-20250514"   # Interpretation
    stage3_model: str = "claude-sonnet-4-20250514"   # Validation

    # Cost controls
    max_llm_cost: float = 1.0  # Maximum $ to spend
    skip_validation: bool = False  # Skip Stage 3 to save cost

    # Caching
    use_cache: bool = True
    cache_dir: Optional[str] = None

    # Output
    output_dir: Optional[str] = None


class ReasoningOrchestrator:
    """
    Orchestrates the complete reasoning process.

    Usage:
        orchestrator = ReasoningOrchestrator()

        # Simple analysis
        result = orchestrator.analyze(fact_store, deal_type="carveout")

        # With refinement
        session = orchestrator.create_refinement_session(fact_store, "carveout")
        session.add_tsa_requirement(...)
        result = orchestrator.apply_refinements(session)
    """

    def __init__(self, config: Optional[OrchestratorConfig] = None):
        self.config = config or OrchestratorConfig()
        self._cache: Dict[str, Any] = {}
        self._current_session = None

    def analyze(
        self,
        fact_store: Any,
        deal_type: str,
        meeting_notes: str = "",
        validate: bool = True,
    ) -> Dict[str, Any]:
        """
        Run complete three-stage analysis.

        Args:
            fact_store: FactStore with extracted facts
            deal_type: "carveout", "acquisition", etc.
            meeting_notes: Additional context
            validate: Whether to run Stage 3 validation

        Returns:
            Complete analysis result
        """
        from tools_v2.three_stage_reasoning import (
            run_three_stage_analysis,
            format_three_stage_output,
        )

        logger.info(f"Starting analysis: deal_type={deal_type}")

        # Run three-stage analysis
        output = run_three_stage_analysis(
            fact_store=fact_store,
            deal_type=deal_type,
            meeting_notes=meeting_notes,
            model=self.config.stage1_model,
        )

        # Format output
        formatted = format_three_stage_output(output)

        result = {
            "output": output,
            "formatted_text": formatted,
            "summary": {
                "deal_type": output.deal_type,
                "total_cost_range": output.total_cost_range,
                "consideration_count": len(output.considerations),
                "activity_count": len(output.activities),
                "tsa_count": len(output.tsa_services),
                "confidence": output.validation.confidence_score,
                "llm_cost": output.total_llm_cost,
            },
        }

        # Save if output dir configured
        if self.config.output_dir:
            self._save_output(result, self.config.output_dir)

        return result

    def analyze_fast(
        self,
        fact_store: Any,
        deal_type: str,
        meeting_notes: str = "",
    ) -> Dict[str, Any]:
        """
        Fast analysis - Stage 1 + Stage 2 only (no validation).

        Use for quick iterations during refinement.
        Cost: ~$0.15-0.20 (one LLM call)
        """
        from tools_v2.three_stage_reasoning import (
            stage1_identify_considerations,
            stage2_match_activities,
        )
        from tools_v2.reasoning_integration import factstore_to_reasoning_format

        facts = factstore_to_reasoning_format(fact_store)

        # Stage 1
        considerations, quant_context, cost = stage1_identify_considerations(
            facts=facts,
            deal_type=deal_type,
            additional_context=meeting_notes,
            model=self.config.stage1_model,
        )

        # Stage 2
        activities, tsa_services = stage2_match_activities(
            considerations=considerations,
            quant_context=quant_context,
            deal_type=deal_type,
        )

        total_low = sum(a.cost_range[0] for a in activities)
        total_high = sum(a.cost_range[1] for a in activities)

        return {
            "mode": "fast",
            "considerations": [asdict(c) for c in considerations],
            "activities": [asdict(a) for a in activities],
            "tsa_services": tsa_services,
            "total_cost_range": (total_low, total_high),
            "llm_cost": cost,
            "validated": False,
        }

    def analyze_with_refinement(
        self,
        fact_store: Any,
        deal_type: str,
        refinements: List[Dict],
        meeting_notes: str = "",
    ) -> Dict[str, Any]:
        """
        Run analysis with pre-specified refinements.

        Useful for applying known adjustments (e.g., seller-specified TSA).

        Args:
            fact_store: FactStore with facts
            deal_type: Deal type
            refinements: List of refinement dicts
            meeting_notes: Additional context
        """
        from tools_v2.refinement_engine import RefinementSession, RefinementInput

        # Create session
        session = RefinementSession.create(
            fact_store=fact_store,
            deal_type=deal_type,
            meeting_notes=meeting_notes,
        )

        # Add refinements
        for ref in refinements:
            session.add_refinement(RefinementInput(**ref))

        # Run analysis (refinements will be applied)
        result = self.analyze(fact_store, deal_type, meeting_notes)

        # Apply refinement adjustments to result
        result = self._apply_refinements_to_result(result, session)

        return result

    def create_refinement_session(
        self,
        fact_store: Any,
        deal_type: str,
        meeting_notes: str = "",
    ):
        """
        Create a refinement session for iterative analysis.

        Returns:
            RefinementSession for adding team inputs
        """
        from tools_v2.refinement_engine import RefinementSession

        session = RefinementSession.create(
            fact_store=fact_store,
            deal_type=deal_type,
            meeting_notes=meeting_notes,
        )

        self._current_session = session
        return session

    def _apply_refinements_to_result(
        self,
        result: Dict,
        session: Any,
    ) -> Dict:
        """Apply refinement session adjustments to result."""
        output = result.get("output")
        if not output:
            return result

        # Apply TSA overrides
        for tsa_override in session.tsa_overrides:
            # Check if already present
            existing = [t for t in output.tsa_services if t.get("service") == tsa_override.get("service")]
            if not existing:
                output.tsa_services.append(tsa_override)

        # Apply activity overrides
        for activity in output.activities:
            if activity.activity_id in session.activity_overrides:
                override = session.activity_overrides[activity.activity_id]
                if "cost_range" in override:
                    activity.cost_range = tuple(override["cost_range"])

        # Recalculate totals
        total_low = sum(a.cost_range[0] for a in output.activities)
        total_high = sum(a.cost_range[1] for a in output.activities)
        output.total_cost_range = (total_low, total_high)

        result["refinements_applied"] = len(session.refinements)
        return result

    def _save_output(self, result: Dict, output_dir: str):
        """Save output to files."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save JSON
        json_path = output_path / f"reasoning_{timestamp}.json"

        # Convert dataclasses for JSON serialization
        def serialize(obj):
            if hasattr(obj, '__dataclass_fields__'):
                return asdict(obj)
            return str(obj)

        with open(json_path, 'w') as f:
            json.dump(result, f, indent=2, default=serialize)

        # Save formatted text
        text_path = output_path / f"reasoning_{timestamp}.txt"
        with open(text_path, 'w') as f:
            f.write(result.get("formatted_text", ""))

        logger.info(f"Saved output to {output_path}")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def quick_analyze(
    fact_store: Any,
    deal_type: str,
    meeting_notes: str = "",
) -> Dict[str, Any]:
    """
    Quick analysis with default settings.

    This is the simplest way to run an analysis.
    """
    orchestrator = ReasoningOrchestrator()
    return orchestrator.analyze(fact_store, deal_type, meeting_notes)


def analyze_with_validation(
    fact_store: Any,
    deal_type: str,
    meeting_notes: str = "",
    model: str = "claude-sonnet-4-20250514",
) -> Dict[str, Any]:
    """
    Full analysis with validation (Stage 1 + 2 + 3).
    """
    config = OrchestratorConfig(
        stage1_model=model,
        stage3_model=model,
    )
    orchestrator = ReasoningOrchestrator(config)
    return orchestrator.analyze(fact_store, deal_type, meeting_notes)


def analyze_fast_iteration(
    fact_store: Any,
    deal_type: str,
    meeting_notes: str = "",
) -> Dict[str, Any]:
    """
    Fast analysis for iteration (Stage 1 + 2 only).

    Use during refinement when you need quick feedback.
    """
    orchestrator = ReasoningOrchestrator()
    return orchestrator.analyze_fast(fact_store, deal_type, meeting_notes)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'ReasoningOrchestrator',
    'OrchestratorConfig',
    'quick_analyze',
    'analyze_with_validation',
    'analyze_fast_iteration',
]
