"""
Flask CLI commands for auth management.

Usage:
    flask create-admin --email admin@example.com
    flask create-admin --email admin@example.com --password MyPass123
    flask list-users
"""

import click
from flask.cli import with_appcontext


@click.command('create-admin')
@click.option('--email', prompt=True, help='Admin email address')
@click.option('--password', default=None, help='Password (generated if not provided)')
@click.option('--name', default='Admin', help='Display name')
@with_appcontext
def create_admin_command(email, password, name):
    """Create an admin user."""
    from web.services.auth_service import get_auth_service

    auth = get_auth_service()

    # Check if user already exists
    if auth.get_by_email(email):
        click.echo(f"Error: User {email} already exists")
        return

    user, result = auth.create_admin(email, password, name)

    if not user:
        click.echo(f"Error: {result}")
        return

    click.echo(f"Admin user created: {email}")
    if not password:
        click.echo(f"Generated password: {result}")
        click.echo("Please change this password after first login.")


@click.command('list-users')
@click.option('--include-inactive', is_flag=True, help='Include inactive users')
@with_appcontext
def list_users_command(include_inactive):
    """List all users."""
    from web.repositories.user_repository import UserRepository

    repo = UserRepository()
    users = repo.list_all(include_inactive=include_inactive)

    if not users:
        click.echo("No users found.")
        return

    click.echo(f"\n{'Email':<40} {'Name':<20} {'Roles':<20} {'Active'}")
    click.echo("-" * 90)
    for user in users:
        roles = ', '.join(user.roles) if user.roles else '-'
        active = 'Yes' if user.active else 'No'
        click.echo(f"{user.email:<40} {(user.name or '-'):<20} {roles:<20} {active}")
    click.echo(f"\nTotal: {len(users)} users")


@click.command('deactivate-user')
@click.option('--email', prompt=True, help='User email to deactivate')
@with_appcontext
def deactivate_user_command(email):
    """Deactivate a user account."""
    from web.services.auth_service import get_auth_service

    auth = get_auth_service()
    user = auth.get_by_email(email)

    if not user:
        click.echo(f"Error: User {email} not found")
        return

    success, error = auth.deactivate_user(user.id)

    if success:
        click.echo(f"User {email} deactivated")
    else:
        click.echo(f"Error: {error}")


@click.command('activate-user')
@click.option('--email', prompt=True, help='User email to activate')
@with_appcontext
def activate_user_command(email):
    """Activate a user account."""
    from web.services.auth_service import get_auth_service

    auth = get_auth_service()
    user = auth.get_by_email(email)

    if not user:
        click.echo(f"Error: User {email} not found")
        return

    success, error = auth.activate_user(user.id)

    if success:
        click.echo(f"User {email} activated")
    else:
        click.echo(f"Error: {error}")


def register_cli(app):
    """Register CLI commands with Flask app."""
    app.cli.add_command(create_admin_command)
    app.cli.add_command(list_users_command)
    app.cli.add_command(deactivate_user_command)
    app.cli.add_command(activate_user_command)
