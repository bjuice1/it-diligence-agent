"""
Analysis Runner - Pipeline Orchestration for Streamlit

Orchestrates the full analysis pipeline including discovery,
reasoning, synthesis, VDR generation, and report generation.

Steps 26-38 of the alignment plan.
"""

import json
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from pathlib import Path
from enum import Enum


# =============================================================================
# RESULT CLASSES
# =============================================================================

class AnalysisPhase(Enum):
    """Current phase of analysis."""
    LOADING = "loading"
    DISCOVERY = "discovery"
    REASONING = "reasoning"
    SYNTHESIS = "synthesis"
    VDR = "vdr"
    REPORTING = "reporting"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class PhaseResult:
    """Result from a single phase."""
    phase: AnalysisPhase
    success: bool
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0


@dataclass
class AnalysisResult:
    """Complete analysis result."""
    # Status
    status: str = "pending"  # pending, running, complete, error
    timestamp: str = ""

    # Phase results
    phases: Dict[str, PhaseResult] = field(default_factory=dict)

    # Counts
    fact_count: int = 0
    gap_count: int = 0
    risk_count: int = 0
    work_item_count: int = 0
    recommendation_count: int = 0
    strategic_count: int = 0
    vdr_request_count: int = 0
    facts_by_domain: Dict[str, int] = field(default_factory=dict)

    # File paths
    facts_file: Optional[str] = None
    findings_file: Optional[str] = None
    vdr_file: Optional[str] = None
    html_report_file: Optional[str] = None
    presentation_file: Optional[str] = None
    coverage_file: Optional[str] = None
    synthesis_file: Optional[str] = None
    narrative_file: Optional[str] = None

    # Object references (for in-memory access)
    fact_store: Any = None
    reasoning_store: Any = None
    coverage_results: Any = None
    synthesis_results: Any = None
    vdr_results: Any = None
    narrative_data: Any = None

    # Errors
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    traceback: Optional[str] = None

    # Metadata
    document_length: int = 0
    deal_id: Optional[str] = None

    def is_complete(self) -> bool:
        """Check if analysis completed successfully."""
        return self.status == "complete"

    def is_error(self) -> bool:
        """Check if analysis failed."""
        return self.status == "error"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary (without object references)."""
        return {
            "status": self.status,
            "timestamp": self.timestamp,
            "fact_count": self.fact_count,
            "gap_count": self.gap_count,
            "risk_count": self.risk_count,
            "work_item_count": self.work_item_count,
            "recommendation_count": self.recommendation_count,
            "strategic_count": self.strategic_count,
            "vdr_request_count": self.vdr_request_count,
            "facts_by_domain": self.facts_by_domain,
            "facts_file": self.facts_file,
            "findings_file": self.findings_file,
            "vdr_file": self.vdr_file,
            "html_report_file": self.html_report_file,
            "presentation_file": self.presentation_file,
            "errors": self.errors,
            "warnings": self.warnings,
            "document_length": self.document_length,
            "deal_id": self.deal_id,
        }


# =============================================================================
# PROGRESS CALLBACK TYPE
# =============================================================================

ProgressCallback = Callable[[float, str, Optional[AnalysisPhase]], None]


# =============================================================================
# ANALYSIS RUNNER
# =============================================================================

class AnalysisRunner:
    """
    Orchestrates the full analysis pipeline.

    Provides:
    - Discovery phase (fact extraction with Haiku)
    - Reasoning phase (risk/work item analysis with Sonnet)
    - Coverage analysis
    - Synthesis phase
    - VDR generation
    - Report generation (HTML + Investment Thesis)
    - Narrative generation (optional)
    """

    def __init__(
        self,
        target_name: str,
        deal_type: str = "bolt_on",
        buyer_name: Optional[str] = None,
        domains: Optional[List[str]] = None,
        output_dir: Optional[Path] = None,
    ):
        """
        Initialize the analysis runner.

        Args:
            target_name: Name of the target company
            deal_type: Type of deal (bolt_on or carve_out)
            buyer_name: Name of buyer company (optional)
            domains: List of domains to analyze (default: all)
            output_dir: Output directory for results
        """
        self.target_name = target_name
        self.deal_type = deal_type
        self.buyer_name = buyer_name
        self.domains = domains or [
            "infrastructure", "network", "cybersecurity",
            "applications", "identity_access", "organization"
        ]

        # Set output directory
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            try:
                from config_v2 import OUTPUT_DIR, FACTS_DIR, FINDINGS_DIR
                self.output_dir = OUTPUT_DIR
                self.facts_dir = FACTS_DIR
                self.findings_dir = FINDINGS_DIR
            except ImportError:
                self.output_dir = Path("output")
                self.facts_dir = self.output_dir / "facts"
                self.findings_dir = self.output_dir / "findings"

        # Ensure directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.facts_dir.mkdir(parents=True, exist_ok=True)
        self.findings_dir.mkdir(parents=True, exist_ok=True)

        # State
        self.result = AnalysisResult()
        self._progress_callback: Optional[ProgressCallback] = None

    def set_progress_callback(self, callback: ProgressCallback):
        """Set callback for progress updates."""
        self._progress_callback = callback

    def _update_progress(
        self,
        percent: float,
        message: str,
        phase: Optional[AnalysisPhase] = None
    ):
        """Update progress via callback."""
        if self._progress_callback:
            self._progress_callback(percent, message, phase)

    # -------------------------------------------------------------------------
    # Main Run Methods
    # -------------------------------------------------------------------------

    def run(
        self,
        document_text: str,
        include_narrative: bool = False,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> AnalysisResult:
        """
        Run the full analysis pipeline.

        Args:
            document_text: Combined document text with entity markers
            include_narrative: Whether to generate LLM narratives
            progress_callback: Optional callback for progress updates

        Returns:
            AnalysisResult with all results and file paths
        """
        if progress_callback:
            self.set_progress_callback(progress_callback)

        self.result = AnalysisResult(
            status="running",
            timestamp=datetime.now().strftime("%Y%m%d_%H%M%S"),
        )
        self.result.document_length = len(document_text)

        try:
            # Phase 1: Discovery
            self._run_discovery(document_text)

            # Phase 2: Reasoning
            self._run_reasoning()

            # Phase 3: Coverage (skipped - matching logic needs improvement)
            # self._run_coverage()

            # Phase 4: Synthesis
            self._run_synthesis()

            # Phase 5: VDR Generation
            self._run_vdr_generation()

            # Phase 6: Report Generation
            self._run_report_generation()

            # Phase 7: Narrative (optional)
            if include_narrative:
                self._run_narrative_generation()

            # Complete
            self._update_progress(1.0, "Analysis complete!", AnalysisPhase.COMPLETE)
            self.result.status = "complete"

        except Exception as e:
            import traceback
            self.result.status = "error"
            self.result.errors.append(str(e))
            self.result.traceback = traceback.format_exc()
            self._update_progress(0.0, f"Error: {e}", AnalysisPhase.ERROR)

        return self.result

    def run_discovery_only(
        self,
        document_text: str,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> AnalysisResult:
        """Run only the discovery phase."""
        if progress_callback:
            self.set_progress_callback(progress_callback)

        self.result = AnalysisResult(
            status="running",
            timestamp=datetime.now().strftime("%Y%m%d_%H%M%S"),
        )
        self.result.document_length = len(document_text)

        try:
            self._run_discovery(document_text)
            self.result.status = "complete"
            self._update_progress(1.0, "Discovery complete!", AnalysisPhase.COMPLETE)

        except Exception as e:
            import traceback
            self.result.status = "error"
            self.result.errors.append(str(e))
            self.result.traceback = traceback.format_exc()

        return self.result

    def run_from_facts(
        self,
        facts_file: Path,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> AnalysisResult:
        """Run reasoning and synthesis from existing facts file."""
        if progress_callback:
            self.set_progress_callback(progress_callback)

        self.result = AnalysisResult(
            status="running",
            timestamp=datetime.now().strftime("%Y%m%d_%H%M%S"),
        )

        try:
            # Load facts
            from stores.fact_store import FactStore
            self.result.fact_store = FactStore.load(str(facts_file))
            self.result.facts_file = str(facts_file)
            self.result.fact_count = len(self.result.fact_store.facts)
            self.result.gap_count = len(self.result.fact_store.gaps)

            # Run remaining phases
            self._run_reasoning()
            self._run_synthesis()
            self._run_vdr_generation()
            self._run_report_generation()

            self.result.status = "complete"
            self._update_progress(1.0, "Analysis complete!", AnalysisPhase.COMPLETE)

        except Exception as e:
            import traceback
            self.result.status = "error"
            self.result.errors.append(str(e))
            self.result.traceback = traceback.format_exc()

        return self.result

    # -------------------------------------------------------------------------
    # Phase Implementations
    # -------------------------------------------------------------------------

    def _run_discovery(self, document_text: str):
        """Run the discovery phase (fact extraction)."""
        self._update_progress(0.1, "Starting discovery phase...", AnalysisPhase.DISCOVERY)

        if len(document_text) < 500:
            self.result.warnings.append(
                f"Document text very short ({len(document_text)} chars)"
            )

        if len(document_text) == 0:
            raise ValueError("No document text to analyze")

        # Import and run discovery
        from main_v2 import run_parallel_discovery

        self._update_progress(0.15, "Running parallel discovery agents...", AnalysisPhase.DISCOVERY)

        fact_store = run_parallel_discovery(
            document_text=document_text,
            domains=self.domains,
            max_workers=3,
            target_name=self.target_name,
        )

        # Store results
        self.result.fact_store = fact_store
        self.result.fact_count = len(fact_store.facts)
        self.result.gap_count = len(fact_store.gaps)
        self.result.facts_by_domain = {
            d: len([f for f in fact_store.facts if f.domain == d])
            for d in self.domains
        }

        # Save facts
        facts_file = self.facts_dir / f"facts_{self.result.timestamp}.json"
        fact_store.save(str(facts_file))
        self.result.facts_file = str(facts_file)

        self._update_progress(
            0.4,
            f"Discovery complete: {self.result.fact_count} facts, {self.result.gap_count} gaps",
            AnalysisPhase.DISCOVERY
        )

    def _run_reasoning(self):
        """Run the reasoning phase (risk/work item analysis)."""
        self._update_progress(0.45, "Starting reasoning phase...", AnalysisPhase.REASONING)

        if self.result.fact_store is None:
            raise ValueError("No fact store available for reasoning")

        # Import and run reasoning
        from main_v2 import run_parallel_reasoning, merge_reasoning_stores
        from tools_v2.session import DealContext

        # Build deal context
        deal_context = {
            "target_name": self.target_name,
            "deal_type": self.deal_type,
            "buyer_name": self.buyer_name,
        }

        # Create DealContext for formatted prompt
        dc = DealContext(
            target_name=self.target_name,
            deal_type=self.deal_type,
            buyer_name=self.buyer_name,
        )
        deal_context["_prompt_context"] = dc.to_prompt_context()

        self._update_progress(0.5, "Running parallel reasoning agents...", AnalysisPhase.REASONING)

        reasoning_results = run_parallel_reasoning(
            fact_store=self.result.fact_store,
            domains=self.domains,
            deal_context=deal_context,
            max_workers=3,
        )

        # Merge stores
        merged_store = merge_reasoning_stores(self.result.fact_store, reasoning_results)

        # Store results
        self.result.reasoning_store = merged_store
        self.result.risk_count = len(merged_store.risks)
        self.result.work_item_count = len(merged_store.work_items)
        self.result.recommendation_count = len(merged_store.recommendations)
        self.result.strategic_count = len(merged_store.strategic_considerations)

        # Save findings
        findings_file = self.findings_dir / f"findings_{self.result.timestamp}.json"
        merged_store.save(str(findings_file))
        self.result.findings_file = str(findings_file)

        self._update_progress(
            0.7,
            f"Reasoning complete: {self.result.risk_count} risks, {self.result.work_item_count} work items",
            AnalysisPhase.REASONING
        )

    def _run_synthesis(self):
        """Run the synthesis phase (cross-domain analysis)."""
        self._update_progress(0.72, "Running synthesis...", AnalysisPhase.SYNTHESIS)

        # Synthesis is embedded in the reasoning merge for now
        # Future: Add explicit synthesis pass

        self._update_progress(0.75, "Synthesis complete", AnalysisPhase.SYNTHESIS)

    def _run_vdr_generation(self):
        """Run VDR request generation."""
        self._update_progress(0.78, "Generating VDR requests...", AnalysisPhase.VDR)

        from main_v2 import run_vdr_generation

        vdr_results = run_vdr_generation(
            self.result.fact_store,
            self.result.reasoning_store
        )

        # Store results
        self.result.vdr_results = vdr_results
        self.result.vdr_request_count = vdr_results.get("vdr_pack", {}).get("total_requests", 0)

        # Save VDR
        vdr_file = self.output_dir / f"vdr_requests_{self.result.timestamp}.json"
        with open(vdr_file, "w") as f:
            json.dump(vdr_results, f, indent=2)
        self.result.vdr_file = str(vdr_file)

        self._update_progress(
            0.82,
            f"VDR complete: {self.result.vdr_request_count} requests",
            AnalysisPhase.VDR
        )

    def _run_report_generation(self):
        """Run report generation (HTML + Investment Thesis)."""
        self._update_progress(0.85, "Generating reports...", AnalysisPhase.REPORTING)

        from tools_v2.html_report import generate_html_report
        from tools_v2.presentation import generate_presentation

        # Generate HTML report
        html_report_file = generate_html_report(
            fact_store=self.result.fact_store,
            reasoning_store=self.result.reasoning_store,
            output_dir=self.output_dir,
            timestamp=self.result.timestamp,
            target_name=self.target_name,
        )
        self.result.html_report_file = str(html_report_file)

        self._update_progress(0.90, "Generating investment thesis...", AnalysisPhase.REPORTING)

        # Generate Investment Thesis
        presentation_file = generate_presentation(
            fact_store=self.result.fact_store,
            reasoning_store=self.result.reasoning_store,
            output_dir=self.output_dir,
            target_name=self.target_name,
            timestamp=self.result.timestamp,
        )
        self.result.presentation_file = str(presentation_file)

        self._update_progress(0.95, "Reports generated", AnalysisPhase.REPORTING)

    def _run_narrative_generation(self):
        """Run LLM narrative generation."""
        self._update_progress(0.96, "Generating narratives...", AnalysisPhase.REPORTING)

        # TODO: Integrate narrative agents
        # For now, narrative generation is optional and not fully integrated

        self._update_progress(0.98, "Narratives complete", AnalysisPhase.REPORTING)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def run_analysis(
    document_text: str,
    target_name: str,
    deal_type: str = "bolt_on",
    buyer_name: Optional[str] = None,
    domains: Optional[List[str]] = None,
    include_narrative: bool = False,
    progress_callback: Optional[ProgressCallback] = None,
) -> AnalysisResult:
    """
    Run the full analysis pipeline.

    Convenience function that creates an AnalysisRunner and runs it.
    """
    runner = AnalysisRunner(
        target_name=target_name,
        deal_type=deal_type,
        buyer_name=buyer_name,
        domains=domains,
    )

    return runner.run(
        document_text=document_text,
        include_narrative=include_narrative,
        progress_callback=progress_callback,
    )


def run_discovery_only(
    document_text: str,
    target_name: str,
    domains: Optional[List[str]] = None,
    progress_callback: Optional[ProgressCallback] = None,
) -> AnalysisResult:
    """Run only the discovery phase."""
    runner = AnalysisRunner(
        target_name=target_name,
        domains=domains,
    )

    return runner.run_discovery_only(
        document_text=document_text,
        progress_callback=progress_callback,
    )


def run_from_existing_facts(
    facts_file: Path,
    target_name: str,
    deal_type: str = "bolt_on",
    buyer_name: Optional[str] = None,
    progress_callback: Optional[ProgressCallback] = None,
) -> AnalysisResult:
    """Run reasoning and synthesis from existing facts file."""
    runner = AnalysisRunner(
        target_name=target_name,
        deal_type=deal_type,
        buyer_name=buyer_name,
    )

    return runner.run_from_facts(
        facts_file=facts_file,
        progress_callback=progress_callback,
    )
