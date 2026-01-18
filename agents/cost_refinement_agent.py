"""
Cost Refinement Agent

Orchestrates the 4-stage cost refinement process for work items.
Each work item goes through: Research → Review → Refine → Summary
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from anthropic import Anthropic

from tools.costing_tools import (
    CostEstimationLog,
    CostRefinementStore,
    StageLog,
    get_tools_for_stage,
    execute_costing_tool,
    STAGE1_RESEARCH_TOOLS,
    STAGE2_REVIEW_TOOLS,
    STAGE3_REFINEMENT_TOOLS,
    STAGE4_SUMMARY_TOOLS
)

from prompts.cost_refinement_prompts import (
    STAGE1_SYSTEM_PROMPT,
    STAGE2_SYSTEM_PROMPT,
    STAGE3_SYSTEM_PROMPT,
    STAGE4_SYSTEM_PROMPT,
    build_stage1_prompt,
    build_stage2_prompt,
    build_stage3_prompt,
    build_stage4_prompt
)

logger = logging.getLogger(__name__)


class CostRefinementAgent:
    """
    Agent that refines cost estimates through a 4-stage process.

    Stage 1: Research & Validate - Research typical costs, validate range
    Stage 2: Critical Review - Find gaps, challenge assumptions
    Stage 3: Refine with Ranges - Produce low/mid/high estimates
    Stage 4: Summary - Executive-ready summary
    """

    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self.client = Anthropic()
        self.model = model
        self.max_tokens = 4096

    def _call_claude(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: List[Dict] = None
    ) -> tuple[str, List[Dict], int, int]:
        """
        Make a single API call to Claude.

        Returns:
            tuple: (response_text, tool_calls, input_tokens, output_tokens)
        """
        messages = [{"role": "user", "content": user_prompt}]

        kwargs = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": system_prompt,
            "messages": messages
        }

        if tools:
            kwargs["tools"] = tools

        response = self.client.messages.create(**kwargs)

        # Extract response content
        response_text = ""
        tool_calls = []

        for block in response.content:
            if hasattr(block, 'text'):
                response_text += block.text
            elif block.type == "tool_use":
                tool_calls.append({
                    "tool_name": block.name,
                    "tool_input": block.input
                })

        return (
            response_text,
            tool_calls,
            response.usage.input_tokens,
            response.usage.output_tokens
        )

    def _run_stage(
        self,
        stage_num: int,
        system_prompt: str,
        user_prompt: str,
        tools: List[Dict],
        log: CostEstimationLog
    ) -> Optional[Dict]:
        """
        Run a single stage of the refinement process.

        Returns the tool output data or None if failed.
        """
        stage_names = {
            1: "research",
            2: "review",
            3: "refine",
            4: "summary"
        }
        stage_name = stage_names.get(stage_num, f"stage_{stage_num}")

        stage_log = StageLog(
            stage_name=stage_name,
            stage_number=stage_num
        )
        stage_log.prompt_sent = user_prompt

        try:
            logger.info(f"Running Stage {stage_num}: {stage_name}")

            response_text, tool_calls, input_tokens, output_tokens = self._call_claude(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                tools=tools
            )

            stage_log.tokens_input = input_tokens
            stage_log.tokens_output = output_tokens

            # Process tool calls
            result_data = None
            if tool_calls:
                for tc in tool_calls:
                    result = execute_costing_tool(tc['tool_name'], tc['tool_input'])
                    if result.get('status') == 'recorded':
                        result_data = tc['tool_input']

            stage_log.complete(
                response=response_text,
                tool_calls=tool_calls
            )
            log.add_stage(stage_log)

            return result_data

        except Exception as e:
            logger.error(f"Stage {stage_num} failed: {e}")
            stage_log.error = str(e)
            stage_log.completed_at = datetime.now().isoformat()
            log.add_stage(stage_log)
            return None

    def refine_work_item(
        self,
        work_item: Dict,
        context: str = ""
    ) -> CostEstimationLog:
        """
        Run the full 4-stage refinement process for a single work item.

        Args:
            work_item: Dict containing work item details
            context: Additional context (e.g., deal context, domain summary)

        Returns:
            CostEstimationLog with full audit trail
        """
        log = CostEstimationLog(
            work_item_id=work_item.get('id', 'unknown'),
            work_item_title=work_item.get('title', 'Unknown'),
            original_estimate=work_item.get('cost_estimate_range', 'Not specified')
        )

        logger.info(f"Starting cost refinement for: {work_item.get('title', 'Unknown')}")

        try:
            # ═══════════════════════════════════════════════════════════
            # STAGE 1: Research & Validate
            # ═══════════════════════════════════════════════════════════
            stage1_prompt = build_stage1_prompt(work_item, context)
            stage1_result = self._run_stage(
                stage_num=1,
                system_prompt=STAGE1_SYSTEM_PROMPT,
                user_prompt=stage1_prompt,
                tools=STAGE1_RESEARCH_TOOLS,
                log=log
            )

            if not stage1_result:
                log.finalize(error="Stage 1 (Research) failed to produce output")
                return log

            research_findings = json.dumps(stage1_result, indent=2)

            # ═══════════════════════════════════════════════════════════
            # STAGE 2: Critical Review
            # ═══════════════════════════════════════════════════════════
            stage2_prompt = build_stage2_prompt(work_item, research_findings)
            stage2_result = self._run_stage(
                stage_num=2,
                system_prompt=STAGE2_SYSTEM_PROMPT,
                user_prompt=stage2_prompt,
                tools=STAGE2_REVIEW_TOOLS,
                log=log
            )

            if not stage2_result:
                log.finalize(error="Stage 2 (Review) failed to produce output")
                return log

            review_findings = json.dumps(stage2_result, indent=2)

            # ═══════════════════════════════════════════════════════════
            # STAGE 3: Refine with Ranges
            # ═══════════════════════════════════════════════════════════
            stage3_prompt = build_stage3_prompt(work_item, research_findings, review_findings)
            stage3_result = self._run_stage(
                stage_num=3,
                system_prompt=STAGE3_SYSTEM_PROMPT,
                user_prompt=stage3_prompt,
                tools=STAGE3_REFINEMENT_TOOLS,
                log=log
            )

            if not stage3_result:
                log.finalize(error="Stage 3 (Refine) failed to produce output")
                return log

            refined_estimate = json.dumps(stage3_result, indent=2)

            # ═══════════════════════════════════════════════════════════
            # STAGE 4: Summary
            # ═══════════════════════════════════════════════════════════
            stage4_prompt = build_stage4_prompt(
                work_item, research_findings, review_findings, refined_estimate
            )
            stage4_result = self._run_stage(
                stage_num=4,
                system_prompt=STAGE4_SYSTEM_PROMPT,
                user_prompt=stage4_prompt,
                tools=STAGE4_SUMMARY_TOOLS,
                log=log
            )

            if not stage4_result:
                log.finalize(error="Stage 4 (Summary) failed to produce output")
                return log

            # ═══════════════════════════════════════════════════════════
            # Compile Final Result
            # ═══════════════════════════════════════════════════════════
            final_result = {
                "research": stage1_result,
                "review": stage2_result,
                "refined_estimate": stage3_result,
                "summary": stage4_result
            }

            log.finalize(result=final_result)
            logger.info(f"Cost refinement complete for: {work_item.get('title', 'Unknown')}")

            return log

        except Exception as e:
            logger.error(f"Cost refinement failed: {e}")
            log.finalize(error=str(e))
            return log


def refine_all_work_items(
    work_items: List[Dict],
    output_dir: str,
    context: str = "",
    model: str = "claude-sonnet-4-20250514"
) -> CostRefinementStore:
    """
    Run cost refinement on all work items with cost estimates.

    Args:
        work_items: List of work item dicts from analysis
        output_dir: Directory to save results
        context: Additional context for all items
        model: Claude model to use

    Returns:
        CostRefinementStore with all results and logs
    """
    # Filter to items with cost estimates
    items_to_refine = [
        wi for wi in work_items
        if wi.get('cost_estimate_range') and wi.get('cost_estimate_range') != 'Not specified'
    ]

    if not items_to_refine:
        logger.warning("No work items with cost estimates to refine")
        return CostRefinementStore(run_id=datetime.now().strftime("%Y%m%d_%H%M%S"))

    logger.info(f"Refining costs for {len(items_to_refine)} work items")

    store = CostRefinementStore(
        run_id=datetime.now().strftime("%Y%m%d_%H%M%S")
    )

    agent = CostRefinementAgent(model=model)

    for i, work_item in enumerate(items_to_refine, 1):
        logger.info(f"Processing {i}/{len(items_to_refine)}: {work_item.get('title', 'Unknown')}")

        log = agent.refine_work_item(work_item, context)
        store.add_log(log)

        # Progress update
        if log.success:
            logger.info(f"  ✓ Refined: {work_item.get('title', 'Unknown')}")
        else:
            logger.warning(f"  ✗ Failed: {work_item.get('title', 'Unknown')} - {log.error}")

    # Save results
    results_path = os.path.join(output_dir, "cost_refinement_results.json")
    store.save(results_path)

    # Also save a summary-only version
    summary_path = os.path.join(output_dir, "cost_refinement_summary.json")
    with open(summary_path, 'w') as f:
        summary = {
            "run_id": store.run_id,
            "total_processed": store.work_items_processed,
            "succeeded": store.work_items_succeeded,
            "failed": store.work_items_failed,
            "refined_estimates": [
                {
                    "work_item_id": r.get('work_item_id'),
                    "work_item_title": r.get('work_item_title'),
                    "original_estimate": r.get('original_estimate'),
                    "refined_estimate": r.get('summary', {}).get('final_estimate', {}),
                    "confidence": r.get('summary', {}).get('confidence_level'),
                    "executive_summary": r.get('summary', {}).get('executive_summary')
                }
                for r in store.results
            ]
        }
        json.dump(summary, f, indent=2)

    logger.info(f"Cost refinement complete: {store.work_items_succeeded}/{store.work_items_processed} succeeded")

    return store


# =============================================================================
# CLI for standalone testing
# =============================================================================

if __name__ == "__main__":
    import sys

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Test with a sample work item
    test_work_item = {
        "id": "WI-TEST-001",
        "title": "SAP S/4HANA Migration",
        "domain": "applications",
        "description": "Migrate from SAP ECC 6.0 to S/4HANA. 150 custom ABAP programs identified.",
        "cost_estimate_range": "$3M-$7M",
        "effort_estimate": "18-24 months",
        "phase": "Post_100"
    }

    context = """
    Target company is a mid-market manufacturing company with $500M revenue.
    18-person IT team, single SAP expert with 25 years experience.
    Heavy customization of SAP for manufacturing processes.
    """

    print("=" * 60)
    print("COST REFINEMENT TEST")
    print("=" * 60)

    agent = CostRefinementAgent()
    log = agent.refine_work_item(test_work_item, context)

    print("\n" + "=" * 60)
    print("RESULT")
    print("=" * 60)
    print(f"Success: {log.success}")
    print(f"Total tokens: {log.total_tokens}")
    print(f"Stages completed: {len(log.stages)}")

    if log.final_result:
        print("\nFinal Summary:")
        summary = log.final_result.get('summary', {})
        print(f"  Final Estimate: {summary.get('final_estimate', {})}")
        print(f"  Confidence: {summary.get('confidence_level')}")
        print(f"  Executive Summary: {summary.get('executive_summary')}")

    # Save full log
    with open("/tmp/cost_refinement_test.json", "w") as f:
        f.write(log.to_json())
    print("\nFull log saved to /tmp/cost_refinement_test.json")
