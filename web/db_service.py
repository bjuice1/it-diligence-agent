"""
Database Service Layer

Provides a unified interface for data access that works with both
JSON files (legacy) and the PostgreSQL database (new).

This enables:
1. Gradual migration with dual-write
2. Easy switching between storage backends
3. Consistent API for the web interface
"""

import os
from typing import Optional, List, Dict, Any
from datetime import datetime

# Check if database is enabled
USE_DATABASE = os.environ.get('USE_DATABASE', 'false').lower() == 'true'


class FactService:
    """Service for accessing facts."""

    @staticmethod
    def get_all(deal_id: str = None, domain: str = None, entity: str = None) -> List[Dict]:
        """Get all facts, optionally filtered."""
        if USE_DATABASE:
            return FactService._get_all_db(deal_id, domain, entity)
        else:
            return FactService._get_all_json(domain, entity)

    @staticmethod
    def _get_all_db(deal_id: str = None, domain: str = None, entity: str = None) -> List[Dict]:
        """Get facts from database."""
        from web.database import Fact

        query = Fact.query
        if deal_id:
            query = query.filter_by(deal_id=deal_id)
        if domain:
            query = query.filter_by(domain=domain)
        if entity:
            query = query.filter_by(entity=entity)

        return [f.to_dict() for f in query.all()]

    @staticmethod
    def _get_all_json(domain: str = None, entity: str = None) -> List[Dict]:
        """Get facts from current session (JSON-based)."""
        from web.session_store import session_store, get_or_create_session_id
        from flask import session as flask_session

        session_id = flask_session.get('session_id')
        if not session_id:
            return []

        session = session_store.get(session_id)
        if not session:
            return []

        facts = [f.to_dict() for f in session.fact_store.get_all_facts()]

        # Filter
        if domain:
            facts = [f for f in facts if f.get('domain') == domain]
        if entity:
            facts = [f for f in facts if f.get('entity') == entity]

        return facts

    @staticmethod
    def get_by_id(fact_id: str, deal_id: str = None) -> Optional[Dict]:
        """Get a fact by ID."""
        if USE_DATABASE:
            from web.database import Fact
            query = Fact.query.filter_by(id=fact_id)
            if deal_id:
                query = query.filter_by(deal_id=deal_id)
            fact = query.first()
            return fact.to_dict() if fact else None
        else:
            from web.session_store import session_store
            from flask import session as flask_session

            session_id = flask_session.get('session_id')
            if not session_id:
                return None

            session = session_store.get(session_id)
            if not session:
                return None

            fact = session.fact_store.get_fact(fact_id)
            return fact.to_dict() if fact else None

    @staticmethod
    def count(deal_id: str = None, domain: str = None) -> int:
        """Count facts."""
        if USE_DATABASE:
            from web.database import Fact
            query = Fact.query
            if deal_id:
                query = query.filter_by(deal_id=deal_id)
            if domain:
                query = query.filter_by(domain=domain)
            return query.count()
        else:
            facts = FactService._get_all_json(domain=domain)
            return len(facts)

    @staticmethod
    def get_domains(deal_id: str = None) -> List[str]:
        """Get list of unique domains."""
        if USE_DATABASE:
            from web.database import db, Fact
            from sqlalchemy import distinct

            query = db.session.query(distinct(Fact.domain))
            if deal_id:
                query = query.filter(Fact.deal_id == deal_id)
            return [row[0] for row in query.all()]
        else:
            facts = FactService._get_all_json()
            return list(set(f.get('domain', '') for f in facts))


class FindingService:
    """Service for accessing findings (risks, work items, etc.)."""

    @staticmethod
    def get_all(deal_id: str = None, finding_type: str = None, domain: str = None) -> List[Dict]:
        """Get all findings, optionally filtered."""
        if USE_DATABASE:
            return FindingService._get_all_db(deal_id, finding_type, domain)
        else:
            return FindingService._get_all_json(finding_type, domain)

    @staticmethod
    def _get_all_db(deal_id: str = None, finding_type: str = None, domain: str = None) -> List[Dict]:
        """Get findings from database."""
        from web.database import Finding

        query = Finding.query
        if deal_id:
            query = query.filter_by(deal_id=deal_id)
        if finding_type:
            query = query.filter_by(finding_type=finding_type)
        if domain:
            query = query.filter_by(domain=domain)

        return [f.to_dict() for f in query.all()]

    @staticmethod
    def _get_all_json(finding_type: str = None, domain: str = None) -> List[Dict]:
        """Get findings from current session (JSON-based)."""
        from web.session_store import session_store
        from flask import session as flask_session

        session_id = flask_session.get('session_id')
        if not session_id:
            return []

        session = session_store.get(session_id)
        if not session:
            return []

        findings = []

        if finding_type is None or finding_type == 'risk':
            findings.extend([
                {**r.to_dict(), 'finding_type': 'risk'}
                for r in session.reasoning_store.risks
            ])

        if finding_type is None or finding_type == 'work_item':
            findings.extend([
                {**w.to_dict(), 'finding_type': 'work_item'}
                for w in session.reasoning_store.work_items
            ])

        if finding_type is None or finding_type == 'recommendation':
            findings.extend([
                {**r.to_dict(), 'finding_type': 'recommendation'}
                for r in session.reasoning_store.recommendations
            ])

        if finding_type is None or finding_type == 'strategic_consideration':
            findings.extend([
                {**s.to_dict(), 'finding_type': 'strategic_consideration'}
                for s in session.reasoning_store.strategic_considerations
            ])

        # Filter by domain
        if domain:
            findings = [f for f in findings if f.get('domain') == domain]

        return findings

    @staticmethod
    def get_risks(deal_id: str = None, severity: str = None) -> List[Dict]:
        """Get all risks."""
        findings = FindingService.get_all(deal_id=deal_id, finding_type='risk')
        if severity:
            findings = [f for f in findings if f.get('severity') == severity]
        return findings

    @staticmethod
    def get_work_items(deal_id: str = None, phase: str = None) -> List[Dict]:
        """Get all work items."""
        findings = FindingService.get_all(deal_id=deal_id, finding_type='work_item')
        if phase:
            findings = [f for f in findings if f.get('phase') == phase]
        return findings

    @staticmethod
    def get_by_id(finding_id: str, deal_id: str = None) -> Optional[Dict]:
        """Get a finding by ID."""
        if USE_DATABASE:
            from web.database import Finding
            query = Finding.query.filter_by(id=finding_id)
            if deal_id:
                query = query.filter_by(deal_id=deal_id)
            finding = query.first()
            return finding.to_dict() if finding else None
        else:
            # Search in session
            from web.session_store import session_store
            from flask import session as flask_session

            session_id = flask_session.get('session_id')
            if not session_id:
                return None

            session = session_store.get(session_id)
            if not session:
                return None

            # Check each store
            for risk in session.reasoning_store.risks:
                if risk.finding_id == finding_id:
                    return {**risk.to_dict(), 'finding_type': 'risk'}

            for wi in session.reasoning_store.work_items:
                if wi.finding_id == finding_id:
                    return {**wi.to_dict(), 'finding_type': 'work_item'}

            for rec in session.reasoning_store.recommendations:
                if rec.finding_id == finding_id:
                    return {**rec.to_dict(), 'finding_type': 'recommendation'}

            for sc in session.reasoning_store.strategic_considerations:
                if sc.finding_id == finding_id:
                    return {**sc.to_dict(), 'finding_type': 'strategic_consideration'}

            return None

    @staticmethod
    def count(deal_id: str = None, finding_type: str = None) -> int:
        """Count findings."""
        if USE_DATABASE:
            from web.database import Finding
            query = Finding.query
            if deal_id:
                query = query.filter_by(deal_id=deal_id)
            if finding_type:
                query = query.filter_by(finding_type=finding_type)
            return query.count()
        else:
            findings = FindingService._get_all_json(finding_type=finding_type)
            return len(findings)


class DealService:
    """Service for managing deals."""

    @staticmethod
    def get_all(owner_id: str = None) -> List[Dict]:
        """Get all deals."""
        if USE_DATABASE:
            from web.database import Deal
            query = Deal.query
            if owner_id:
                query = query.filter_by(owner_id=owner_id)
            return [d.to_dict() for d in query.order_by(Deal.created_at.desc()).all()]
        else:
            # No deal management in JSON mode
            return []

    @staticmethod
    def get_by_id(deal_id: str) -> Optional[Dict]:
        """Get a deal by ID."""
        if USE_DATABASE:
            from web.database import Deal
            deal = Deal.query.filter_by(id=deal_id).first()
            return deal.to_dict() if deal else None
        else:
            return None

    @staticmethod
    def create(target_name: str, buyer_name: str = '', deal_type: str = 'acquisition',
               owner_id: str = None, context: Dict = None) -> Optional[Dict]:
        """Create a new deal."""
        if USE_DATABASE:
            from web.database import db, Deal
            deal = Deal(
                target_name=target_name,
                buyer_name=buyer_name,
                deal_type=deal_type,
                owner_id=owner_id,
                context=context or {},
            )
            db.session.add(deal)
            db.session.commit()
            return deal.to_dict()
        else:
            return None

    @staticmethod
    def get_current_deal_id() -> Optional[str]:
        """Get the current active deal ID from session or first available."""
        from flask import session as flask_session

        # Check session for active deal
        deal_id = flask_session.get('active_deal_id')
        if deal_id and USE_DATABASE:
            return deal_id

        # Get first deal if database is enabled
        if USE_DATABASE:
            from web.database import Deal
            deal = Deal.query.order_by(Deal.created_at.desc()).first()
            if deal:
                return deal.id

        return None


class UserService:
    """Service for managing users."""

    @staticmethod
    def get_all() -> List[Dict]:
        """Get all users."""
        if USE_DATABASE:
            from web.database import User
            return [u.to_dict() for u in User.query.all()]
        else:
            from web.models.user import get_user_store
            return [u.to_dict() for u in get_user_store().list_users()]

    @staticmethod
    def get_by_id(user_id: str) -> Optional[Dict]:
        """Get a user by ID."""
        if USE_DATABASE:
            from web.database import User
            user = User.query.filter_by(id=user_id).first()
            return user.to_dict() if user else None
        else:
            from web.models.user import get_user_store
            user = get_user_store().get_by_id(user_id)
            return user.to_dict() if user else None

    @staticmethod
    def get_by_email(email: str) -> Optional[Dict]:
        """Get a user by email."""
        if USE_DATABASE:
            from web.database import User
            user = User.query.filter_by(email=email.lower()).first()
            return user.to_dict() if user else None
        else:
            from web.models.user import get_user_store
            user = get_user_store().get_by_email(email)
            return user.to_dict() if user else None


# Export services
__all__ = ['FactService', 'FindingService', 'DealService', 'UserService', 'USE_DATABASE']
