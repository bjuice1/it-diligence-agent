"""
Temporary admin endpoint for database initialization.

This is a ONE-TIME USE endpoint for Railway deployment.
After tables are created, this file should be deleted.
"""

from flask import Blueprint, jsonify, render_template_string
from web.database import db, create_all_tables
from flask import current_app
import traceback

admin_init_bp = Blueprint('admin_init', __name__, url_prefix='/admin')


@admin_init_bp.route('/init-db')
def init_database():
    """
    Initialize database tables.

    ONE-TIME USE: Visit this URL once to create all database tables.
    After successful initialization, delete this file.
    """
    try:
        # HTML template for nice output
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Database Initialization</title>
            <style>
                body {
                    font-family: 'Monaco', 'Courier New', monospace;
                    background: #1a1a1a;
                    color: #00ff00;
                    padding: 40px;
                    line-height: 1.6;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    background: #0d0d0d;
                    padding: 30px;
                    border: 2px solid #00ff00;
                    border-radius: 8px;
                }
                h1 {
                    color: #00ff00;
                    text-align: center;
                }
                .success {
                    color: #00ff00;
                }
                .error {
                    color: #ff0000;
                }
                .info {
                    color: #00bfff;
                }
                pre {
                    background: #000;
                    padding: 15px;
                    border-left: 3px solid #00ff00;
                    overflow-x: auto;
                }
                .warning {
                    background: #332200;
                    border-left: 3px solid #ff9900;
                    padding: 15px;
                    margin: 20px 0;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{{ title }}</h1>
                <pre>{{ output }}</pre>
                {% if success %}
                <div class="warning">
                    <strong>⚠️  IMPORTANT - DELETE THIS ENDPOINT!</strong><br><br>
                    Database initialization is complete. For security:<br>
                    1. Delete the file: <code>web/blueprints/admin_init.py</code><br>
                    2. Remove the blueprint registration from <code>web/app.py</code><br>
                    3. Commit and push the changes<br><br>
                    This endpoint should NOT exist in production!
                </div>
                {% endif %}
            </div>
        </body>
        </html>
        """

        output_lines = []
        output_lines.append("=" * 70)
        output_lines.append("DATABASE INITIALIZATION")
        output_lines.append("=" * 70)
        output_lines.append("")

        # Get database URL (masked for security)
        db_url = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if '@' in db_url:
            parts = db_url.split('@')
            masked_url = parts[0].split(':')[0] + ':****@' + '@'.join(parts[1:])
            output_lines.append(f"Database: {masked_url[:60]}...")
        else:
            output_lines.append(f"Database: {db_url[:60]}...")
        output_lines.append("")

        # Create all tables
        output_lines.append("Creating tables...")
        db.create_all()
        output_lines.append("✓ Tables created successfully")
        output_lines.append("")

        # Verify tables exist
        output_lines.append("Verifying tables...")
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        output_lines.append(f"✓ Found {len(tables)} tables:")
        for table in sorted(tables):
            output_lines.append(f"  - {table}")
        output_lines.append("")

        # Check if default user exists
        output_lines.append("Checking for default admin user...")
        try:
            from web.database import User
            user_count = User.query.count()

            if user_count == 0:
                output_lines.append("Creating default admin user...")
                from web.database import Tenant
                import bcrypt

                # Create default tenant
                tenant = Tenant(
                    name='Default Organization',
                    slug='default',
                    plan='professional',
                    max_users=100,
                    max_deals=1000
                )
                db.session.add(tenant)
                db.session.flush()

                # Create admin user
                password_hash = bcrypt.hashpw(
                    'changeme123'.encode('utf-8'),
                    bcrypt.gensalt()
                ).decode('utf-8')

                admin = User(
                    email='admin@example.com',
                    password_hash=password_hash,
                    name='Admin',
                    roles=['admin', 'analyst'],
                    tenant_id=tenant.id,
                    active=True
                )
                db.session.add(admin)
                db.session.commit()

                output_lines.append("✓ Created admin user:")
                output_lines.append("  Email: admin@example.com")
                output_lines.append("  Password: changeme123")
                output_lines.append("")
                output_lines.append("⚠️  CHANGE THIS PASSWORD IMMEDIATELY!")
            else:
                output_lines.append(f"✓ Found {user_count} existing user(s)")
                output_lines.append("  Skipping default user creation")
        except Exception as e:
            output_lines.append(f"⚠  Could not create default user: {e}")

        output_lines.append("")
        output_lines.append("=" * 70)
        output_lines.append("✅ DATABASE INITIALIZATION COMPLETE!")
        output_lines.append("=" * 70)
        output_lines.append("")
        output_lines.append("Next steps:")
        output_lines.append("1. Verify tables in Railway PostgreSQL dashboard")
        output_lines.append("2. Test login at your app URL")
        output_lines.append("3. DELETE THIS ENDPOINT FOR SECURITY!")

        return render_template_string(
            html_template,
            title="✅ Success",
            output="\n".join(output_lines),
            success=True
        )

    except Exception as e:
        # Error handling
        error_output = []
        error_output.append("=" * 70)
        error_output.append("❌ DATABASE INITIALIZATION FAILED")
        error_output.append("=" * 70)
        error_output.append("")
        error_output.append(f"Error: {str(e)}")
        error_output.append("")
        error_output.append("Traceback:")
        error_output.append(traceback.format_exc())
        error_output.append("")
        error_output.append("=" * 70)
        error_output.append("TROUBLESHOOTING:")
        error_output.append("=" * 70)
        error_output.append("1. Check DATABASE_URL environment variable is set")
        error_output.append("2. Verify PostgreSQL service is running")
        error_output.append("3. Check Railway logs for more details")
        error_output.append("4. Review docs/RAILWAY_DATABASE_FIX.md")

        return render_template_string(
            html_template,
            title="❌ Error",
            output="\n".join(error_output),
            success=False
        ), 500


@admin_init_bp.route('/init-db-status')
def init_status():
    """Check database status without modifying anything."""
    try:
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        from web.database import User
        user_count = User.query.count() if 'users' in tables else 0

        return jsonify({
            'status': 'ok',
            'tables_count': len(tables),
            'tables': sorted(tables),
            'user_count': user_count,
            'database_connected': True
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'database_connected': False
        }), 500
