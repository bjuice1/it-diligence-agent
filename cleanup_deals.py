"""Delete old deals and their associated data to free up space."""
import os
os.environ.setdefault('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/it_due_diligence')

from web.database import db, Deal, Fact, Finding, AnalysisRun, Gap
from sqlalchemy import create_engine, text
from datetime import datetime

# Connect to database
engine = create_engine(os.environ['DATABASE_URL'])

with engine.connect() as conn:
    # First, let's see what we have
    print("📊 Current Database State:")
    print("=" * 60)
    
    result = conn.execute(text("SELECT id, name, created_at FROM deals ORDER BY created_at DESC"))
    deals = result.fetchall()
    
    if not deals:
        print("✅ No deals found - database is clean!")
    else:
        for deal in deals:
            deal_id, name, created = deal
            
            # Count associated data
            facts = conn.execute(text("SELECT COUNT(*) FROM facts WHERE deal_id = :id"), {"id": deal_id}).scalar()
            findings = conn.execute(text("SELECT COUNT(*) FROM findings WHERE deal_id = :id"), {"id": deal_id}).scalar()
            runs = conn.execute(text("SELECT COUNT(*) FROM analysis_runs WHERE deal_id = :id"), {"id": deal_id}).scalar()
            
            print(f"\n📁 Deal: {name}")
            print(f"   ID: {deal_id}")
            print(f"   Created: {created}")
            print(f"   - {facts} facts")
            print(f"   - {findings} findings")
            print(f"   - {runs} analysis runs")
    
    print("\n" + "=" * 60)
    
    if deals:
        print(f"\n🗑️  Ready to delete {len(deals)} deal(s) and all associated data")
        print("\nTo proceed with deletion, add '--delete' flag to script")

print("\n✨ Analysis complete!")
