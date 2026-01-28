"""
Discovery Audit Logger

Creates detailed .md logs for each discovery run to provide:
- Audit trail for partners/stakeholders
- Debugging information
- Proof of work completed
- Traceability of extracted facts

Each discovery run generates a log file:
  {domain}_discovery_log_{timestamp}.md
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class ToolCallRecord:
    """Record of a single tool call during discovery."""
    iteration: int
    tool_name: str
    tool_input: Dict[str, Any]
    result: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class DiscoveryLogEntry:
    """Complete log entry for a discovery run."""
    domain: str
    timestamp: str
    document_name: str
    document_length: int

    # Execution tracking
    tool_calls: List[ToolCallRecord] = field(default_factory=list)
    iterations: int = 0

    # Results summary
    facts_extracted: int = 0
    facts_accepted: int = 0
    facts_flagged: int = 0
    facts_rejected: int = 0
    gaps_flagged: int = 0

    # Validation details
    rejected_items: List[Dict[str, str]] = field(default_factory=list)
    flagged_items: List[Dict[str, str]] = field(default_factory=list)

    # Metrics
    api_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost: float = 0.0
    execution_time: float = 0.0

    # Output files
    facts_file: Optional[str] = None
    findings_file: Optional[str] = None


class DiscoveryLogger:
    """
    Captures and logs discovery agent execution for audit trail.

    Usage:
        logger = DiscoveryLogger(domain="applications", output_dir=Path("output/logs"))
        logger.start(document_name="apps.md", document_length=5000)

        # During discovery:
        logger.log_tool_call(iteration=1, tool_name="create_inventory_entry",
                           tool_input={...}, result={...})

        # At end:
        logger.finish(metrics=agent.metrics, fact_store=fact_store)
        log_path = logger.save()
    """

    def __init__(self, domain: str, output_dir: Optional[Path] = None):
        self.domain = domain
        self.output_dir = output_dir or Path("output/logs")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.log_entry: Optional[DiscoveryLogEntry] = None
        self.start_time: Optional[datetime] = None
        self._current_iteration = 0

    def start(self, document_name: str, document_length: int):
        """Start logging a new discovery run."""
        self.start_time = datetime.now()
        self.log_entry = DiscoveryLogEntry(
            domain=self.domain,
            timestamp=self.start_time.isoformat(),
            document_name=document_name,
            document_length=document_length,
        )
        logger.info(f"Started discovery logging for {self.domain}")

    def set_iteration(self, iteration: int):
        """Update current iteration number."""
        self._current_iteration = iteration
        if self.log_entry:
            self.log_entry.iterations = max(self.log_entry.iterations, iteration)

    def log_tool_call(self, tool_name: str, tool_input: Dict[str, Any],
                      result: Dict[str, Any], iteration: Optional[int] = None):
        """Log a tool call and its result."""
        if not self.log_entry:
            return

        iter_num = iteration if iteration is not None else self._current_iteration

        record = ToolCallRecord(
            iteration=iter_num,
            tool_name=tool_name,
            tool_input=tool_input,
            result=result
        )
        self.log_entry.tool_calls.append(record)

        # Track validation outcomes for inventory entries
        if tool_name == "create_inventory_entry":
            status = result.get("status", "")
            if status == "success":
                self.log_entry.facts_extracted += 1
                if result.get("needs_review"):
                    self.log_entry.facts_flagged += 1
                    self.log_entry.flagged_items.append({
                        "item": tool_input.get("item", "unknown"),
                        "fact_id": result.get("fact_id", ""),
                        "reason": result.get("message", "flagged for review")
                    })
                else:
                    self.log_entry.facts_accepted += 1
            elif status == "rejected":
                self.log_entry.facts_rejected += 1
                self.log_entry.rejected_items.append({
                    "item": tool_input.get("item", "unknown"),
                    "reason": result.get("message", "rejected")
                })
            elif status == "duplicate":
                pass  # Don't count duplicates

        elif tool_name == "flag_gap":
            if result.get("status") == "success":
                self.log_entry.gaps_flagged += 1

    def finish(self, metrics: Any = None, facts_file: str = None,
               findings_file: str = None):
        """Finalize the log entry with metrics and output files."""
        if not self.log_entry:
            return

        if self.start_time:
            self.log_entry.execution_time = (
                datetime.now() - self.start_time
            ).total_seconds()

        if metrics:
            self.log_entry.api_calls = getattr(metrics, 'api_calls', 0)
            self.log_entry.input_tokens = getattr(metrics, 'input_tokens', 0)
            self.log_entry.output_tokens = getattr(metrics, 'output_tokens', 0)
            self.log_entry.estimated_cost = getattr(metrics, 'estimated_cost', 0.0)

        self.log_entry.facts_file = facts_file
        self.log_entry.findings_file = findings_file

    def save(self) -> Optional[Path]:
        """Save the log to a markdown file and return the path."""
        if not self.log_entry:
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.domain}_discovery_log_{timestamp}.md"
        filepath = self.output_dir / filename

        content = self._format_markdown()

        with open(filepath, 'w') as f:
            f.write(content)

        logger.info(f"Saved discovery log: {filepath}")
        return filepath

    def _format_markdown(self) -> str:
        """Format the log entry as markdown."""
        if not self.log_entry:
            return ""

        e = self.log_entry
        lines = []

        # Header
        lines.append(f"# {e.domain.upper()} Discovery Log")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now().isoformat()}")
        lines.append("")

        # Summary Box
        lines.append("---")
        lines.append("## Run Summary")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| **Domain** | {e.domain} |")
        lines.append(f"| **Document** | {e.document_name} |")
        lines.append(f"| **Document Size** | {e.document_length:,} chars |")
        lines.append(f"| **Start Time** | {e.timestamp} |")
        lines.append(f"| **Duration** | {e.execution_time:.1f} seconds |")
        lines.append(f"| **Iterations** | {e.iterations} |")
        lines.append(f"| **API Calls** | {e.api_calls} |")
        lines.append(f"| **Tokens (in/out)** | {e.input_tokens:,} / {e.output_tokens:,} |")
        lines.append(f"| **Estimated Cost** | ${e.estimated_cost:.4f} |")
        lines.append("")

        # Extraction Results
        lines.append("---")
        lines.append("## Extraction Results")
        lines.append("")
        lines.append(f"| Status | Count |")
        lines.append(f"|--------|-------|")
        lines.append(f"| **Total Extracted** | {e.facts_extracted} |")
        lines.append(f"| ✅ Accepted | {e.facts_accepted} |")
        lines.append(f"| ⚠️ Flagged for Review | {e.facts_flagged} |")
        lines.append(f"| ❌ Rejected | {e.facts_rejected} |")
        lines.append(f"| 📋 Gaps Identified | {e.gaps_flagged} |")
        lines.append("")

        # Flagged Items
        if e.flagged_items:
            lines.append("---")
            lines.append("## Items Flagged for Review")
            lines.append("")
            lines.append("| Item | Fact ID | Reason |")
            lines.append("|------|---------|--------|")
            for item in e.flagged_items[:20]:  # Limit to first 20
                lines.append(f"| {item['item'][:30]} | {item['fact_id']} | {item['reason'][:50]} |")
            if len(e.flagged_items) > 20:
                lines.append(f"| ... | ... | +{len(e.flagged_items) - 20} more |")
            lines.append("")

        # Rejected Items
        if e.rejected_items:
            lines.append("---")
            lines.append("## Rejected Items")
            lines.append("")
            lines.append("| Item | Reason |")
            lines.append("|------|--------|")
            for item in e.rejected_items[:20]:
                lines.append(f"| {item['item'][:30]} | {item['reason'][:60]} |")
            if len(e.rejected_items) > 20:
                lines.append(f"| ... | +{len(e.rejected_items) - 20} more |")
            lines.append("")

        # Tool Call Log (Summary)
        lines.append("---")
        lines.append("## Tool Call Summary")
        lines.append("")

        # Group by tool name
        tool_counts: Dict[str, int] = {}
        for tc in e.tool_calls:
            tool_counts[tc.tool_name] = tool_counts.get(tc.tool_name, 0) + 1

        lines.append("| Tool | Call Count |")
        lines.append("|------|------------|")
        for tool, count in sorted(tool_counts.items()):
            lines.append(f"| {tool} | {count} |")
        lines.append("")

        # Detailed Tool Calls (condensed)
        lines.append("---")
        lines.append("## Extraction Detail")
        lines.append("")
        lines.append("```")

        for tc in e.tool_calls:
            if tc.tool_name == "create_inventory_entry":
                item = tc.tool_input.get("item", "?")[:40]
                category = tc.tool_input.get("category", "?")
                status = tc.result.get("status", "?")
                fact_id = tc.result.get("fact_id", "")
                flag = " [REVIEW]" if tc.result.get("needs_review") else ""
                lines.append(f"[{tc.iteration:02d}] {fact_id}: {item} ({category}) - {status}{flag}")
            elif tc.tool_name == "flag_gap":
                desc = tc.tool_input.get("description", "?")[:50]
                lines.append(f"[{tc.iteration:02d}] GAP: {desc}")
            elif tc.tool_name == "complete_discovery":
                lines.append(f"[{tc.iteration:02d}] COMPLETE_DISCOVERY")

        lines.append("```")
        lines.append("")

        # Output Files
        lines.append("---")
        lines.append("## Output Files")
        lines.append("")
        if e.facts_file:
            lines.append(f"- **Facts:** `{e.facts_file}`")
        if e.findings_file:
            lines.append(f"- **Findings:** `{e.findings_file}`")
        if not e.facts_file and not e.findings_file:
            lines.append("- *(No output files recorded)*")
        lines.append("")

        # Footer
        lines.append("---")
        lines.append(f"*Log generated by IT Due Diligence Agent v2*")

        return "\n".join(lines)


# Convenience function to create a logger for a domain
def create_discovery_logger(domain: str, output_dir: Optional[Path] = None) -> DiscoveryLogger:
    """Create a discovery logger for the specified domain."""
    return DiscoveryLogger(domain=domain, output_dir=output_dir)
