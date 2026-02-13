"""
Temporary blueprint to add missing investigation_reason column
DELETE THIS FILE AFTER RUNNING ONCE
"""
from flask import Blueprint, jsonify
from web.database import db

schema_fix_bp = Blueprint('schema_fix', __name__)

@schema_fix_bp.route('/admin/fix-schema-investigation-reason', methods=['GET'])
def fix_schema():
    """Add missing investigation_reason column to inventory_items"""
    try:
        # Check if column exists
        result = db.session.execute(db.text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='inventory_items'
            AND column_name='investigation_reason'
        """))

        if result.fetchone():
            return jsonify({
                'status': 'success',
                'message': 'Column investigation_reason already exists',
                'action': 'none'
            })

        # Add the column
        db.session.execute(db.text("""
            ALTER TABLE inventory_items
            ADD COLUMN investigation_reason TEXT DEFAULT ''
        """))

        db.session.commit()

        # Verify
        result = db.session.execute(db.text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='inventory_items'
            AND column_name='investigation_reason'
        """))

        if result.fetchone():
            return jsonify({
                'status': 'success',
                'message': 'Column investigation_reason added successfully',
                'action': 'added',
                'next_steps': 'DELETE web/blueprints/schema_fix.py and remove from app.py'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Column added but verification failed'
            }), 500

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
