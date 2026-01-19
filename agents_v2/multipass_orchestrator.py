"""
Multi-Pass Extraction Orchestrator

This module coordinates the three-pass extraction process:
- Pass 1: System Discovery (identify all platforms, vendors, systems)
- Pass 2: Detail Extraction (extract counts, versions, configs for each system)
- Pass 3: Validation & Reconciliation (verify consistency)

The orchestrator manages the flow between passes and ensures data
consistency across the extraction pipeline.
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
import logging

# Import stores and engines
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools_v2.system_registry import SystemRegistry, System
from tools_v2.granular_facts_store import GranularFactsStore, GranularFact
from tools_v2.validation_engine import ValidationEngine, ValidationReport
from tools_v2.excel_exporter import export_to_excel, export_to_csv

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

# Pass iteration limits
PASS_1_MAX_ITERATIONS = 50
PASS_2_MAX_ITERATIONS = 100
PASS_3_MAX_ITERATIONS = 50

# Minimum extraction thresholds
MIN_SYSTEMS = 3
MIN_GRANULAR_FACTS = 50
MIN_VALIDATION_PASS_RATE = 0.85


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class PassResult:
    """Result from a single extraction pass."""
    pass_number: int
    pass_name: str
    status: str  # success, partial, failed
    items_extracted: int
    duration_seconds: float
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractionResult:
    """Complete result from all three passes."""
    session_id: str
    system_registry: SystemRegistry
    granular_facts_store: GranularFactsStore
    validation_report: ValidationReport
    pass_results: List[PassResult]
    total_duration_seconds: float
    status: str  # success, partial, failed
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def total_systems(self) -> int:
        return self.system_registry.total_systems

    @property
    def total_facts(self) -> int:
        return self.granular_facts_store.total_facts

    @property
    def validation_passed(self) -> bool:
        return self.validation_report.is_valid

    def to_summary(self) -> Dict[str, Any]:
        """Generate summary dictionary."""
        return {
            "session_id": self.session_id,
            "status": self.status,
            "total_systems": self.total_systems,
            "total_granular_facts": self.total_facts,
            "validation_pass_rate": f"{self.validation_report.pass_rate:.1%}",
            "validation_passed": self.validation_passed,
            "total_duration_seconds": round(self.total_duration_seconds, 2),
            "passes": [
                {
                    "name": p.pass_name,
                    "status": p.status,
                    "items": p.items_extracted,
                    "duration": round(p.duration_seconds, 2)
                }
                for p in self.pass_results
            ],
            "created_at": self.created_at
        }


# =============================================================================
# MULTI-PASS ORCHESTRATOR
# =============================================================================

class MultiPassOrchestrator:
    """
    Orchestrates the three-pass extraction process.

    Usage:
        orchestrator = MultiPassOrchestrator(session_id="my-session")
        result = orchestrator.run_extraction(documents, existing_fact_store)

        # Export results
        orchestrator.export_to_excel(result, Path("output/inventory.xlsx"))
    """

    def __init__(
        self,
        session_id: str,
        output_dir: Optional[Path] = None,
        llm_client: Any = None,
        model: str = "claude-3-5-haiku-20241022"
    ):
        """
        Initialize the orchestrator.

        Args:
            session_id: Unique identifier for this extraction session
            output_dir: Directory for saving results
            llm_client: Anthropic client for LLM calls
            model: Model to use for extraction
        """
        self.session_id = session_id
        self.output_dir = Path(output_dir) if output_dir else Path(f"sessions/{session_id}")
        self.llm_client = llm_client
        self.model = model

        # Initialize stores
        self.system_registry = SystemRegistry()
        self.granular_facts_store = GranularFactsStore()
        self.validation_engine = ValidationEngine()

        # Pass results
        self.pass_results: List[PassResult] = []

    def run_extraction(
        self,
        documents: List[Dict[str, Any]],
        existing_fact_store: Any = None,
        skip_pass_1: bool = False,
        skip_pass_2: bool = False,
        skip_pass_3: bool = False
    ) -> ExtractionResult:
        """
        Execute all three passes in sequence.

        Args:
            documents: List of document dicts with 'name' and 'content' keys
            existing_fact_store: Optional existing FactStore for reconciliation
            skip_pass_1: Skip system discovery (use existing registry)
            skip_pass_2: Skip detail extraction
            skip_pass_3: Skip validation

        Returns:
            ExtractionResult with all data and statistics
        """
        start_time = time.time()

        print("\n" + "=" * 70)
        print("MULTI-PASS EXTRACTION")
        print(f"Session: {self.session_id}")
        print(f"Documents: {len(documents)}")
        print("=" * 70)

        # Pass 1: System Discovery
        if not skip_pass_1:
            self._run_pass_1(documents)
        else:
            print("\n[PASS 1] Skipped - using existing system registry")

        # Pass 2: Detail Extraction
        if not skip_pass_2:
            self._run_pass_2(documents)
        else:
            print("\n[PASS 2] Skipped - using existing granular facts")

        # Pass 3: Validation
        if not skip_pass_3:
            validation_report = self._run_pass_3(existing_fact_store)
        else:
            print("\n[PASS 3] Skipped")
            validation_report = ValidationReport()

        # Calculate total duration
        total_duration = time.time() - start_time

        # Determine overall status
        if self.system_registry.total_systems < MIN_SYSTEMS:
            status = "partial"
        elif self.granular_facts_store.total_facts < MIN_GRANULAR_FACTS:
            status = "partial"
        elif validation_report.pass_rate < MIN_VALIDATION_PASS_RATE:
            status = "partial"
        else:
            status = "success"

        # Create result
        result = ExtractionResult(
            session_id=self.session_id,
            system_registry=self.system_registry,
            granular_facts_store=self.granular_facts_store,
            validation_report=validation_report,
            pass_results=self.pass_results,
            total_duration_seconds=total_duration,
            status=status
        )

        # Print summary
        self._print_summary(result)

        # Auto-save
        self._save_results(result)

        return result

    def _run_pass_1(self, documents: List[Dict[str, Any]]) -> PassResult:
        """
        Pass 1: System Discovery

        Identify all major systems, platforms, and technologies.
        """
        print("\n" + "-" * 70)
        print("PASS 1: SYSTEM DISCOVERY")
        print("Identifying all systems, platforms, and technologies...")
        print("-" * 70)

        start_time = time.time()
        errors = []
        warnings = []

        try:
            # Process each document
            for doc in documents:
                doc_name = doc.get('name', 'Unknown')
                content = doc.get('content', '')

                print(f"\n  Processing: {doc_name}")

                # Extract systems from document
                systems_found = self._extract_systems_from_document(
                    content, doc_name
                )

                print(f"    → Found {len(systems_found)} systems")

        except Exception as e:
            logger.error(f"Pass 1 error: {e}")
            errors.append(str(e))

        duration = time.time() - start_time

        # Create pass result
        result = PassResult(
            pass_number=1,
            pass_name="System Discovery",
            status="success" if not errors else "partial",
            items_extracted=self.system_registry.total_systems,
            duration_seconds=duration,
            errors=errors,
            warnings=warnings,
            metadata={
                "categories": self.system_registry.categories,
                "domains": self.system_registry.domains
            }
        )

        self.pass_results.append(result)

        print(f"\n  ✓ Pass 1 complete: {result.items_extracted} systems in {duration:.1f}s")

        return result

    def _run_pass_2(self, documents: List[Dict[str, Any]]) -> PassResult:
        """
        Pass 2: Detail Extraction

        For each system, extract counts, versions, configurations, costs.
        """
        print("\n" + "-" * 70)
        print("PASS 2: DETAIL EXTRACTION")
        print("Extracting counts, versions, configurations, costs...")
        print("-" * 70)

        start_time = time.time()
        errors = []
        warnings = []

        try:
            # Get all systems that need details
            systems = self.system_registry.get_systems_needing_details()

            if not systems:
                systems = self.system_registry.get_all_systems()

            print(f"\n  Systems to process: {len(systems)}")

            # Process each document for each system
            for doc in documents:
                doc_name = doc.get('name', 'Unknown')
                content = doc.get('content', '')

                print(f"\n  Processing: {doc_name}")

                # Extract details for all systems
                facts_found = self._extract_details_from_document(
                    content, doc_name, systems
                )

                print(f"    → Extracted {len(facts_found)} granular facts")

        except Exception as e:
            logger.error(f"Pass 2 error: {e}")
            errors.append(str(e))

        duration = time.time() - start_time

        # Update system detail status
        for system in self.system_registry.get_all_systems():
            fact_count = len(self.granular_facts_store.get_facts_by_system(system.system_id))
            if fact_count > 0:
                self.system_registry.mark_detail_complete(system.system_id, fact_count)

        # Create pass result
        result = PassResult(
            pass_number=2,
            pass_name="Detail Extraction",
            status="success" if not errors else "partial",
            items_extracted=self.granular_facts_store.total_facts,
            duration_seconds=duration,
            errors=errors,
            warnings=warnings,
            metadata={
                "facts_by_domain": self.granular_facts_store.count_by_domain(),
                "facts_by_type": self.granular_facts_store.count_by_type()
            }
        )

        self.pass_results.append(result)

        print(f"\n  ✓ Pass 2 complete: {result.items_extracted} facts in {duration:.1f}s")

        return result

    def _run_pass_3(self, existing_fact_store: Any = None) -> ValidationReport:
        """
        Pass 3: Validation & Reconciliation

        Cross-check details against summaries, flag inconsistencies.
        """
        print("\n" + "-" * 70)
        print("PASS 3: VALIDATION & RECONCILIATION")
        print("Verifying consistency and completeness...")
        print("-" * 70)

        start_time = time.time()

        # Get summary facts if available
        summary_facts = []
        if existing_fact_store:
            summary_facts = list(existing_fact_store.facts) if hasattr(existing_fact_store, 'facts') else []

        # Run validation
        validation_report = self.validation_engine.validate_all(
            self.system_registry,
            self.granular_facts_store,
            summary_facts
        )

        duration = time.time() - start_time

        # Create pass result
        result = PassResult(
            pass_number=3,
            pass_name="Validation",
            status="success" if validation_report.is_valid else "partial",
            items_extracted=validation_report.total_checks,
            duration_seconds=duration,
            errors=[r.message for r in validation_report.get_failures()],
            warnings=[r.message for r in validation_report.get_warnings()[:10]],
            metadata={
                "pass_rate": f"{validation_report.pass_rate:.1%}",
                "passed": validation_report.pass_count,
                "warnings": validation_report.warn_count,
                "failures": validation_report.fail_count
            }
        )

        self.pass_results.append(result)

        print(f"\n  ✓ Pass 3 complete: {validation_report.pass_count} passed, "
              f"{validation_report.warn_count} warnings, "
              f"{validation_report.fail_count} failures")

        return validation_report

    # =========================================================================
    # EXTRACTION HELPERS (to be called by LLM agents)
    # =========================================================================

    def _extract_systems_from_document(
        self,
        content: str,
        doc_name: str
    ) -> List[str]:
        """
        Extract systems from document content.

        In production, this would call the LLM with the system discovery prompt.
        For now, this is a placeholder that shows the structure.
        """
        # This is where the LLM would be called to extract systems
        # The LLM would use the register_system tool

        # Placeholder: Parse common patterns
        systems_found = []

        # Common system patterns to look for
        patterns = [
            ("AWS", "cloud_platform", "Amazon Web Services", "infrastructure"),
            ("Azure", "cloud_platform", "Microsoft", "infrastructure"),
            ("GCP", "cloud_platform", "Google", "infrastructure"),
            ("NetSuite", "erp", "Oracle", "applications"),
            ("SAP", "erp", "SAP", "applications"),
            ("Salesforce", "crm", "Salesforce", "applications"),
            ("Workday", "hris", "Workday", "applications"),
            ("Active Directory", "identity", "Microsoft", "identity_access"),
            ("Okta", "identity", "Okta", "identity_access"),
        ]

        content_lower = content.lower()
        for name, category, vendor, domain in patterns:
            if name.lower() in content_lower:
                system_id = self.system_registry.add_system(
                    name=name,
                    vendor=vendor,
                    category=category,
                    domain=domain,
                    source_document=doc_name,
                    evidence_quote=f"Found reference to {name} in document"
                )
                systems_found.append(system_id)

        return systems_found

    def _extract_details_from_document(
        self,
        content: str,
        doc_name: str,
        systems: List[System]
    ) -> List[str]:
        """
        Extract granular details for systems from document content.

        In production, this would call the LLM with the detail extraction prompt.
        For now, this is a placeholder that shows the structure.
        """
        # This is where the LLM would be called to extract details
        # The LLM would use the add_granular_fact tool

        facts_found = []

        # Placeholder: Look for numeric patterns
        import re

        # Pattern: number followed by common units
        patterns = [
            (r'(\d+)\s*(?:EC2\s*)?instances?', 'count', 'EC2 Instances', 'instances'),
            (r'(\d+)\s*servers?', 'count', 'Servers', 'servers'),
            (r'(\d+)\s*users?', 'count', 'Users', 'users'),
            (r'(\d+)\s*(?:TB|terabytes?)', 'capacity', 'Storage', 'TB'),
            (r'\$(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:k|K|thousand)?', 'cost', 'Cost', 'USD'),
            (r'version\s*(\d+(?:\.\d+)*)', 'version', 'Software Version', None),
        ]

        for pattern, fact_type, item, unit in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches[:5]:  # Limit matches
                value = match.replace(',', '')
                try:
                    value = float(value) if '.' in str(value) else int(value)
                except:
                    pass

                fact_id = self.granular_facts_store.add_fact(
                    domain="infrastructure",
                    category="general",
                    fact_type=fact_type,
                    item=item,
                    value=value,
                    unit=unit,
                    source_document=doc_name,
                    evidence_quote=f"Found: {match}"
                )
                facts_found.append(fact_id)

        return facts_found

    # =========================================================================
    # OUTPUT METHODS
    # =========================================================================

    def _print_summary(self, result: ExtractionResult):
        """Print extraction summary."""
        print("\n" + "=" * 70)
        print("EXTRACTION COMPLETE")
        print("=" * 70)

        print(f"\n  Status: {result.status.upper()}")
        print(f"  Duration: {result.total_duration_seconds:.1f}s")

        print("\n  Results:")
        print(f"    Systems discovered: {result.total_systems}")
        print(f"    Granular facts: {result.total_facts}")
        print(f"    Validation pass rate: {result.validation_report.pass_rate:.1%}")

        print("\n  Pass Details:")
        for p in result.pass_results:
            print(f"    {p.pass_name}: {p.items_extracted} items ({p.duration_seconds:.1f}s)")

        if result.validation_report.fail_count > 0:
            print(f"\n  ⚠ {result.validation_report.fail_count} validation failures - review required")

    def _save_results(self, result: ExtractionResult):
        """Save all results to files."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Save system registry
        self.system_registry.save(self.output_dir / "system_registry.json")

        # Save granular facts
        self.granular_facts_store.save(self.output_dir / "granular_facts.json")

        # Save validation report
        from tools_v2.validation_engine import save_validation_report
        save_validation_report(
            result.validation_report,
            self.output_dir / "validation_report.json"
        )

        # Save summary
        with open(self.output_dir / "extraction_summary.json", 'w') as f:
            json.dump(result.to_summary(), f, indent=2)

        print(f"\n  Results saved to: {self.output_dir}")

    def export_excel(self, result: ExtractionResult, output_path: Path) -> Path:
        """Export results to Excel workbook."""
        return export_to_excel(
            result.system_registry,
            result.granular_facts_store,
            result.validation_report,
            output_path
        )

    def export_csv(self, result: ExtractionResult, output_dir: Path) -> Dict[str, Path]:
        """Export results to CSV files."""
        return export_to_csv(
            result.system_registry,
            result.granular_facts_store,
            result.validation_report,
            output_dir
        )

    # =========================================================================
    # LOADING
    # =========================================================================

    @classmethod
    def load_from_session(cls, session_dir: Path) -> 'MultiPassOrchestrator':
        """Load orchestrator state from a previous session."""
        session_dir = Path(session_dir)

        # Extract session_id from directory name
        session_id = session_dir.name

        orchestrator = cls(session_id=session_id, output_dir=session_dir)

        # Load system registry
        registry_path = session_dir / "system_registry.json"
        if registry_path.exists():
            orchestrator.system_registry = SystemRegistry.load(registry_path)

        # Load granular facts
        facts_path = session_dir / "granular_facts.json"
        if facts_path.exists():
            orchestrator.granular_facts_store = GranularFactsStore.load(facts_path)

        return orchestrator


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def run_multipass_extraction(
    documents: List[Dict[str, Any]],
    session_id: str = None,
    output_dir: Path = None,
    existing_fact_store: Any = None
) -> ExtractionResult:
    """
    Convenience function to run multi-pass extraction.

    Args:
        documents: List of document dicts with 'name' and 'content'
        session_id: Optional session identifier
        output_dir: Optional output directory
        existing_fact_store: Optional existing FactStore for reconciliation

    Returns:
        ExtractionResult with all data
    """
    if not session_id:
        session_id = f"extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    orchestrator = MultiPassOrchestrator(
        session_id=session_id,
        output_dir=output_dir
    )

    return orchestrator.run_extraction(
        documents,
        existing_fact_store=existing_fact_store
    )
