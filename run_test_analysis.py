"""
Run Two-Phase Analysis with Test Files.

Tests the full two-phase analysis pipeline with:
- Target Company Profile: National Mutual
- Buyer Company Profile: Atlantic International
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_analysis():
    """Run the two-phase analysis with test files."""
    from web.analysis_runner import run_analysis
    from web.task_manager import AnalysisTask, TaskStatus
    from tools_v2.document_store import DocumentStore

    # Test file paths
    target_file = "/Users/JB/Desktop/IT DD Test 2/9.5/it-diligence-agent/data/input/Target Company Profile_ National Mutual.pdf"
    buyer_file = "/Users/JB/Documents/IT/IT DD Test 2/9.5/it-diligence-agent 2/data/input/Buyer Company Profile - Atlantic International.pdf"

    # Verify files exist
    if not os.path.exists(target_file):
        logger.error(f"Target file not found: {target_file}")
        return False
    if not os.path.exists(buyer_file):
        logger.error(f"Buyer file not found: {buyer_file}")
        return False

    logger.info(f"Target file: {target_file}")
    logger.info(f"Buyer file: {buyer_file}")

    # Initialize document store and register documents with entity
    doc_store = DocumentStore.get_instance()
    doc_store.clear()  # Clear any previous data

    # Register target document
    target_doc = doc_store.add_document(
        file_path=target_file,
        entity="target"
    )
    logger.info(f"Registered TARGET document: {target_doc.filename}")

    # Register buyer document
    buyer_doc = doc_store.add_document(
        file_path=buyer_file,
        entity="buyer"
    )
    logger.info(f"Registered BUYER document: {buyer_doc.filename}")

    # Create task
    task = AnalysisTask(
        task_id="test_two_phase_001",
        file_paths=[target_file, buyer_file],
        domains=["infrastructure", "applications", "organization", "cybersecurity", "network", "identity_access"],
        deal_context={
            "target_name": "National Mutual",
            "buyer_name": "Atlantic International",
            "deal_type": "Acquisition",
            "deal_rationale": "Strategic expansion into insurance market"
        }
    )

    # Progress callback
    def progress_callback(update):
        phase = update.get("phase", "unknown")
        phase_display = update.get("phase_display", phase)
        facts = update.get("facts_extracted", 0)
        logger.info(f"Progress: {phase_display} | Facts: {facts}")

    logger.info("=" * 60)
    logger.info("STARTING TWO-PHASE ANALYSIS")
    logger.info("=" * 60)
    logger.info(f"Target: National Mutual")
    logger.info(f"Buyer: Atlantic International")
    logger.info("=" * 60)

    try:
        # Run analysis
        result = run_analysis(task, progress_callback)

        logger.info("=" * 60)
        logger.info("ANALYSIS COMPLETE")
        logger.info("=" * 60)

        if result:
            logger.info(f"Facts file: {result.get('facts_file')}")
            logger.info(f"Findings file: {result.get('findings_file')}")

            # Print summary
            summary = result.get("summary", {})
            logger.info(f"\nSUMMARY:")
            logger.info(f"  Total Facts: {summary.get('total_facts', 0)}")
            logger.info(f"  TARGET Facts: {summary.get('target_facts', 0)}")
            logger.info(f"  BUYER Facts: {summary.get('buyer_facts', 0)}")
            logger.info(f"  Risks: {summary.get('risks', 0)}")
            logger.info(f"  Work Items: {summary.get('work_items', 0)}")

            return True
        else:
            logger.error("Analysis returned no result")
            return False

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_analysis()
    sys.exit(0 if success else 1)
