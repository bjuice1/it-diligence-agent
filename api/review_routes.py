"""
Human Review API Routes

REST API endpoints for the human review workflow:
- Review queue management
- Fact confirmation/correction/rejection
- Validation status queries
- Flag management

These endpoints power the review UI and allow programmatic access.
"""

from flask import Blueprint, request, jsonify, current_app
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from models.validation_models import (
    ValidationFlag, FlagSeverity, FlagCategory, generate_flag_id
)

logger = logging.getLogger(__name__)

# Create Blueprint
review_bp = Blueprint('review', __name__, url_prefix='/api/review')


# =============================================================================
# DEPENDENCY INJECTION
# =============================================================================

def get_validation_store():
    """Get validation store from app context."""
    return current_app.config.get('VALIDATION_STORE')


def get_correction_store():
    """Get correction store from app context."""
    return current_app.config.get('CORRECTION_STORE')


def get_fact_store():
    """Get fact store from app context."""
    return current_app.config.get('FACT_STORE')


def get_correction_pipeline():
    """Get correction pipeline from app context."""
    return current_app.config.get('CORRECTION_PIPELINE')


# =============================================================================
# REVIEW QUEUE ENDPOINTS
# =============================================================================

@review_bp.route('/queue', methods=['GET'])
def get_review_queue():
    """
    Get facts needing human review.

    Query params:
        domain: Filter by domain (optional)
        severity: Minimum severity level (optional)
        limit: Max results (default 100)
        offset: Pagination offset (default 0)

    Returns:
        List of facts needing review with their flags
    """
    validation_store = get_validation_store()
    if not validation_store:
        return jsonify({"error": "Validation store not configured"}), 500

    # Parse query params
    domain = request.args.get('domain')
    severity_str = request.args.get('severity')
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))

    # Parse severity if provided
    min_severity = None
    if severity_str:
        try:
            min_severity = FlagSeverity(severity_str)
        except ValueError:
            pass

    # Get facts needing review
    facts_needing_review = validation_store.get_facts_needing_review(
        domain=domain,
        min_severity=min_severity,
        limit=limit + offset  # Get extra to handle offset
    )

    # Apply offset
    facts_needing_review = facts_needing_review[offset:offset + limit]

    # Format response
    items = []
    for state in facts_needing_review:
        items.append({
            "fact_id": state.fact_id,
            "status": state.status.value,
            "ai_confidence": state.ai_confidence,
            "highest_severity": state.highest_severity.value if state.highest_severity else None,
            "flags_count": len(state.ai_flags),
            "flags": [f.to_dict() for f in state.ai_flags[:3]],  # First 3 flags
            "evidence_verified": state.evidence_verified,
            "evidence_match_score": state.evidence_match_score,
            "human_reviewed": state.human_reviewed
        })

    return jsonify({
        "items": items,
        "total": len(items),
        "offset": offset,
        "limit": limit
    })


@review_bp.route('/queue/<fact_id>', methods=['GET'])
def get_review_item(fact_id: str):
    """
    Get full details for a specific review item.

    Returns:
        Complete fact data with validation state, evidence, and flags
    """
    validation_store = get_validation_store()
    fact_store = get_fact_store()

    if not validation_store:
        return jsonify({"error": "Validation store not configured"}), 500

    # Get validation state
    state = validation_store.get_validation_state(fact_id)
    if not state:
        return jsonify({"error": f"Fact {fact_id} not found"}), 404

    # Get fact data
    fact_data = None
    if fact_store:
        fact = fact_store.get_fact(fact_id) if hasattr(fact_store, 'get_fact') else None
        if fact:
            fact_data = fact.to_dict() if hasattr(fact, 'to_dict') else fact

    # Get correction history
    correction_store = get_correction_store()
    corrections = []
    if correction_store:
        corrections = [
            c.to_dict() for c in correction_store.get_corrections_for_fact(fact_id)
        ]

    return jsonify({
        "fact_id": fact_id,
        "fact": fact_data,
        "validation_state": state.to_dict(),
        "flags": [f.to_dict() for f in state.ai_flags],
        "evidence": {
            "verified": state.evidence_verified,
            "match_score": state.evidence_match_score,
            "matched_text": state.evidence_matched_text
        },
        "corrections": corrections
    })


@review_bp.route('/stats', methods=['GET'])
def get_review_stats():
    """
    Get review queue statistics.

    Returns:
        Statistics about flagged and reviewed facts
    """
    validation_store = get_validation_store()
    if not validation_store:
        return jsonify({"error": "Validation store not configured"}), 500

    return jsonify({
        "total_flagged": validation_store.count_needing_review(),
        "total_reviewed": validation_store.count_reviewed(),
        "by_domain": validation_store.get_stats_by_domain(),
        "by_severity": validation_store.get_stats_by_severity(),
        "overall_confidence": validation_store.get_overall_confidence()
    })


# =============================================================================
# REVIEW ACTION ENDPOINTS
# =============================================================================

@review_bp.route('/<fact_id>/confirm', methods=['POST'])
def confirm_fact(fact_id: str):
    """
    Confirm a fact as correct.

    Request body:
        reviewer: Username of reviewer
        notes: Optional notes

    Returns:
        Confirmation status
    """
    validation_store = get_validation_store()
    if not validation_store:
        return jsonify({"error": "Validation store not configured"}), 500

    data = request.json or {}
    reviewer = data.get('reviewer', 'anonymous')
    notes = data.get('notes')

    try:
        validation_store.mark_human_confirmed(
            fact_id=fact_id,
            reviewer=reviewer,
            notes=notes
        )

        logger.info(f"Fact {fact_id} confirmed by {reviewer}")

        return jsonify({
            "status": "confirmed",
            "fact_id": fact_id,
            "reviewer": reviewer,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error confirming fact {fact_id}: {e}")
        return jsonify({"error": str(e)}), 500


@review_bp.route('/<fact_id>/correct', methods=['POST'])
def correct_fact(fact_id: str):
    """
    Apply a correction to a fact.

    Request body:
        corrected_fields: Dict of field -> new value
        reason: Reason for correction
        corrected_by: Username
        new_evidence: Optional new evidence quote

    Returns:
        Correction result with ripple effects
    """
    correction_pipeline = get_correction_pipeline()
    if not correction_pipeline:
        return jsonify({"error": "Correction pipeline not configured"}), 500

    data = request.json or {}

    # Validate required fields
    if 'corrected_fields' not in data:
        return jsonify({"error": "corrected_fields is required"}), 400
    if 'reason' not in data:
        return jsonify({"error": "reason is required"}), 400

    try:
        result = correction_pipeline.apply_correction(
            fact_id=fact_id,
            corrected_fields=data['corrected_fields'],
            reason=data['reason'],
            corrected_by=data.get('corrected_by', 'anonymous'),
            new_evidence=data.get('new_evidence')
        )

        if result.success:
            return jsonify({
                "status": "corrected",
                "correction_id": result.correction_id,
                "original_value": result.original_value,
                "corrected_value": result.corrected_value,
                "ripple_effects": [e.to_dict() for e in result.derived_values_updated],
                "new_flags": [f.to_dict() for f in result.new_flags_created],
                "message": result.message
            })
        else:
            return jsonify({
                "status": "failed",
                "message": result.message
            }), 400

    except Exception as e:
        logger.error(f"Error correcting fact {fact_id}: {e}")
        return jsonify({"error": str(e)}), 500


@review_bp.route('/<fact_id>/reject', methods=['POST'])
def reject_fact(fact_id: str):
    """
    Reject a fact as invalid.

    Request body:
        reviewer: Username
        reason: Reason for rejection

    Returns:
        Rejection status
    """
    validation_store = get_validation_store()
    if not validation_store:
        return jsonify({"error": "Validation store not configured"}), 500

    data = request.json or {}

    if 'reason' not in data:
        return jsonify({"error": "reason is required"}), 400

    try:
        validation_store.mark_human_rejected(
            fact_id=fact_id,
            reviewer=data.get('reviewer', 'anonymous'),
            reason=data['reason']
        )

        logger.info(f"Fact {fact_id} rejected: {data['reason']}")

        return jsonify({
            "status": "rejected",
            "fact_id": fact_id,
            "reason": data['reason'],
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error rejecting fact {fact_id}: {e}")
        return jsonify({"error": str(e)}), 500


@review_bp.route('/<fact_id>/skip', methods=['POST'])
def skip_fact(fact_id: str):
    """
    Skip a fact (defer for later review).

    Returns:
        Skip status
    """
    # For now, just acknowledge the skip
    # Could track skipped items separately in the future
    return jsonify({
        "status": "skipped",
        "fact_id": fact_id,
        "timestamp": datetime.now().isoformat()
    })


# =============================================================================
# FLAG MANAGEMENT ENDPOINTS
# =============================================================================

@review_bp.route('/<fact_id>/flag', methods=['POST'])
def add_manual_flag(fact_id: str):
    """
    Add a manual flag to a fact.

    Request body:
        severity: Flag severity (info, warning, error, critical)
        message: Flag message
        suggestion: Optional suggestion

    Returns:
        Created flag
    """
    validation_store = get_validation_store()
    if not validation_store:
        return jsonify({"error": "Validation store not configured"}), 500

    data = request.json or {}

    if 'message' not in data:
        return jsonify({"error": "message is required"}), 400

    try:
        severity = FlagSeverity(data.get('severity', 'warning'))
    except ValueError:
        severity = FlagSeverity.WARNING

    flag = ValidationFlag(
        flag_id=generate_flag_id(),
        severity=severity,
        category=FlagCategory.MANUAL,
        message=data['message'],
        suggestion=data.get('suggestion')
    )

    validation_store.add_flag(fact_id, flag, source="manual")

    logger.info(f"Manual flag added to {fact_id}: {data['message']}")

    return jsonify({
        "flag_id": flag.flag_id,
        "fact_id": fact_id,
        "severity": severity.value,
        "message": data['message']
    })


@review_bp.route('/<fact_id>/flag/<flag_id>/resolve', methods=['POST'])
def resolve_flag(fact_id: str, flag_id: str):
    """
    Resolve a flag.

    Request body:
        resolved_by: Username
        note: Resolution note

    Returns:
        Resolution status
    """
    validation_store = get_validation_store()
    if not validation_store:
        return jsonify({"error": "Validation store not configured"}), 500

    data = request.json or {}

    success = validation_store.resolve_flag(
        fact_id=fact_id,
        flag_id=flag_id,
        resolved_by=data.get('resolved_by', 'anonymous'),
        note=data.get('note')
    )

    if success:
        return jsonify({
            "status": "resolved",
            "flag_id": flag_id,
            "resolved_by": data.get('resolved_by', 'anonymous')
        })
    else:
        return jsonify({"error": "Flag not found"}), 404


# =============================================================================
# VALIDATION STATUS ENDPOINTS
# =============================================================================

@review_bp.route('/validation/status', methods=['GET'])
def get_validation_status():
    """
    Get overall validation status.

    Returns:
        Overall confidence and domain states
    """
    validation_store = get_validation_store()
    if not validation_store:
        return jsonify({"error": "Validation store not configured"}), 500

    domain_states = validation_store.get_all_domain_states()
    cross_domain = validation_store.get_cross_domain_state()

    return jsonify({
        "overall_confidence": validation_store.get_overall_confidence(),
        "domains": {
            domain: state.to_dict() for domain, state in domain_states.items()
        },
        "cross_domain": cross_domain.to_dict() if cross_domain else None
    })


@review_bp.route('/validation/status/<domain>', methods=['GET'])
def get_domain_status(domain: str):
    """
    Get validation status for a specific domain.

    Returns:
        Domain validation state
    """
    validation_store = get_validation_store()
    if not validation_store:
        return jsonify({"error": "Validation store not configured"}), 500

    state = validation_store.get_domain_state(domain)

    return jsonify({
        "domain": domain,
        "state": state.to_dict()
    })


@review_bp.route('/validation/flags', methods=['GET'])
def get_all_flags():
    """
    Get all validation flags.

    Query params:
        unresolved_only: Only show unresolved flags (default true)
        severity: Minimum severity level

    Returns:
        List of flags
    """
    validation_store = get_validation_store()
    if not validation_store:
        return jsonify({"error": "Validation store not configured"}), 500

    unresolved_only = request.args.get('unresolved_only', 'true').lower() == 'true'
    severity_str = request.args.get('severity')

    min_severity = None
    if severity_str:
        try:
            min_severity = FlagSeverity(severity_str)
        except ValueError:
            pass

    flags = validation_store.get_all_flags(
        unresolved_only=unresolved_only,
        min_severity=min_severity
    )

    return jsonify({
        "flags": [f.to_dict() for f in flags],
        "total": len(flags)
    })


@review_bp.route('/validation/audit/<fact_id>', methods=['GET'])
def get_audit_trail(fact_id: str):
    """
    Get audit trail for a fact.

    Returns:
        Complete history of changes to this fact
    """
    correction_store = get_correction_store()
    validation_store = get_validation_store()

    if not correction_store or not validation_store:
        return jsonify({"error": "Stores not configured"}), 500

    # Get corrections
    corrections = correction_store.get_corrections_for_fact(fact_id)

    # Get validation state
    state = validation_store.get_validation_state(fact_id)

    return jsonify({
        "fact_id": fact_id,
        "corrections": [
            {
                "correction": c.to_dict(),
                "ripple_effects": [
                    e.to_dict() for e in correction_store.get_ripple_effects(c.correction_id)
                ]
            }
            for c in corrections
        ],
        "validation_state": state.to_dict() if state else None
    })


# =============================================================================
# BULK OPERATIONS
# =============================================================================

@review_bp.route('/bulk/confirm', methods=['POST'])
def bulk_confirm():
    """
    Confirm multiple facts at once.

    Request body:
        fact_ids: List of fact IDs
        reviewer: Username

    Returns:
        Results for each fact
    """
    validation_store = get_validation_store()
    if not validation_store:
        return jsonify({"error": "Validation store not configured"}), 500

    data = request.json or {}
    fact_ids = data.get('fact_ids', [])
    reviewer = data.get('reviewer', 'anonymous')

    results = []
    for fact_id in fact_ids:
        try:
            validation_store.mark_human_confirmed(
                fact_id=fact_id,
                reviewer=reviewer
            )
            results.append({"fact_id": fact_id, "status": "confirmed"})
        except Exception as e:
            results.append({"fact_id": fact_id, "status": "error", "error": str(e)})

    return jsonify({
        "results": results,
        "confirmed": sum(1 for r in results if r["status"] == "confirmed"),
        "failed": sum(1 for r in results if r["status"] == "error")
    })


# =============================================================================
# HELPER FUNCTION TO REGISTER ROUTES
# =============================================================================

def register_review_routes(app, validation_store, correction_store, fact_store, correction_pipeline):
    """
    Register review routes with the Flask app.

    Args:
        app: Flask application
        validation_store: ValidationStore instance
        correction_store: CorrectionStore instance
        fact_store: FactStore instance
        correction_pipeline: CorrectionPipeline instance
    """
    # Store dependencies in app config
    app.config['VALIDATION_STORE'] = validation_store
    app.config['CORRECTION_STORE'] = correction_store
    app.config['FACT_STORE'] = fact_store
    app.config['CORRECTION_PIPELINE'] = correction_pipeline

    # Register blueprint
    app.register_blueprint(review_bp)

    logger.info("Review routes registered")
