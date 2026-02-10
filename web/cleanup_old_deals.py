"""
Cleanup script for old deals - can be run as Flask CLI command.

Usage:
    flask cleanup-deals --list              # List all deals
    flask cleanup-deals --delete-all        # Delete ALL deals
    flask cleanup-deals --delete <deal_id>  # Delete specific deal
"""

import click
from flask.cli import with_appcontext
from web.database import db, Deal, Fact, Finding, AnalysisRun, Gap, Document
from sqlalchemy import text


@click.group()
def cleanup():
    """Database cleanup commands."""
    pass


@cleanup.command('list-deals')
@with_appcontext
def list_deals():
    """List all deals and their data size."""
    click.echo("\n" + "=" * 80)
    click.echo("📊 DEALS IN DATABASE")
    click.echo("=" * 80)

    deals = Deal.query.order_by(Deal.created_at.desc()).all()

    if not deals:
        click.echo("✅ No deals found - database is clean!")
        return

    total_facts = 0
    total_findings = 0
    total_runs = 0

    for deal in deals:
        facts_count = Fact.query.filter_by(deal_id=deal.id, deleted_at=None).count()
        findings_count = Finding.query.filter_by(deal_id=deal.id, deleted_at=None).count()
        runs_count = AnalysisRun.query.filter_by(deal_id=deal.id).count()
        docs_count = Document.query.filter_by(deal_id=deal.id).count()

        total_facts += facts_count
        total_findings += findings_count
        total_runs += runs_count

        click.echo(f"\n📁 {deal.name}")
        click.echo(f"   ID: {deal.id}")
        click.echo(f"   Created: {deal.created_at}")
        click.echo(f"   📄 {docs_count} documents")
        click.echo(f"   🔍 {facts_count} facts")
        click.echo(f"   ⚠️  {findings_count} findings")
        click.echo(f"   🔄 {runs_count} analysis runs")

    click.echo("\n" + "=" * 80)
    click.echo(f"📊 TOTALS: {len(deals)} deals | {total_facts} facts | {total_findings} findings | {total_runs} runs")
    click.echo("=" * 80 + "\n")


@cleanup.command('delete-deal')
@click.argument('deal_id')
@click.option('--force', is_flag=True, help='Skip confirmation prompt')
@with_appcontext
def delete_deal(deal_id, force):
    """Delete a specific deal and all associated data."""
    deal = Deal.query.get(deal_id)

    if not deal:
        click.echo(f"❌ Deal {deal_id} not found!")
        return

    # Count what will be deleted
    facts_count = Fact.query.filter_by(deal_id=deal.id).count()
    findings_count = Finding.query.filter_by(deal_id=deal.id).count()
    runs_count = AnalysisRun.query.filter_by(deal_id=deal.id).count()
    docs_count = Document.query.filter_by(deal_id=deal.id).count()

    click.echo(f"\n🗑️  About to DELETE:")
    click.echo(f"   Deal: {deal.name}")
    click.echo(f"   - {docs_count} documents")
    click.echo(f"   - {facts_count} facts")
    click.echo(f"   - {findings_count} findings")
    click.echo(f"   - {runs_count} analysis runs")

    if not force:
        if not click.confirm('\n⚠️  This cannot be undone. Proceed?'):
            click.echo("❌ Aborted")
            return

    # Delete (CASCADE will handle related records)
    try:
        db.session.delete(deal)
        db.session.commit()
        click.echo(f"✅ Deleted deal '{deal.name}' and all associated data")
    except Exception as e:
        db.session.rollback()
        click.echo(f"❌ Error deleting deal: {e}")


@cleanup.command('delete-all-deals')
@click.option('--force', is_flag=True, help='Skip confirmation prompt')
@with_appcontext
def delete_all_deals(force):
    """Delete ALL deals and associated data."""
    deals = Deal.query.all()

    if not deals:
        click.echo("✅ No deals to delete!")
        return

    total_facts = db.session.query(Fact).count()
    total_findings = db.session.query(Finding).count()
    total_runs = db.session.query(AnalysisRun).count()
    total_docs = db.session.query(Document).count()

    click.echo(f"\n🗑️  About to DELETE ALL DATA:")
    click.echo(f"   {len(deals)} deals")
    click.echo(f"   {total_docs} documents")
    click.echo(f"   {total_facts} facts")
    click.echo(f"   {total_findings} findings")
    click.echo(f"   {total_runs} analysis runs")

    if not force:
        click.echo("\n⚠️  THIS WILL DELETE EVERYTHING IN THE DATABASE!")
        if not click.confirm('Are you absolutely sure?'):
            click.echo("❌ Aborted")
            return

    try:
        # Delete all deals (CASCADE handles the rest)
        for deal in deals:
            db.session.delete(deal)

        db.session.commit()
        click.echo(f"\n✅ Deleted {len(deals)} deals and all associated data")
        click.echo("✅ Database is now clean!")
    except Exception as e:
        db.session.rollback()
        click.echo(f"❌ Error during cleanup: {e}")


def register_commands(app):
    """Register cleanup commands with Flask app."""
    app.cli.add_command(cleanup)
