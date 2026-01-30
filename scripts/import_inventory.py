#!/usr/bin/env python3
"""
Quick script to import inventory files.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from stores.inventory_store import InventoryStore
from tools_v2.file_router import ingest_file

def main():
    # Files to import
    files_to_import = [
        "uploads/target/data_room/7e9e96f5_Great_Insurance_Document_2_Application_Inventory.md",
        "uploads/target/data_room/d7cf0106_Great_Insurance_Document_3_Infrastructure_Hosting_Inventory.md",
    ]

    base_path = Path(__file__).parent.parent

    # Create or load inventory store
    store_path = base_path / "data" / "inventory_store.json"
    store = InventoryStore()

    if store_path.exists():
        store.load(store_path)
        print(f"Loaded existing store with {len(store)} items")

    # Import each file
    for file_rel in files_to_import:
        file_path = base_path / file_rel
        if not file_path.exists():
            print(f"File not found: {file_path}")
            continue

        print(f"\nImporting: {file_path.name}")
        result = ingest_file(file_path, store, entity="target")

        print(f"  - Items added: {result.inventory_items_added}")
        print(f"  - Items updated: {result.inventory_items_updated}")

        if result.errors:
            print(f"  - Errors: {result.errors}")

    # Save the store
    store_path.parent.mkdir(parents=True, exist_ok=True)
    store.save(store_path)
    print(f"\nSaved inventory store with {len(store)} total items to {store_path}")

    # Print summary
    apps = store.get_items(inventory_type="application", entity="target")
    infra = store.get_items(inventory_type="infrastructure", entity="target")
    print(f"\nSummary:")
    print(f"  - Applications: {len(apps)}")
    print(f"  - Infrastructure: {len(infra)}")

    # Print first few apps
    if apps:
        print(f"\nFirst 5 applications:")
        for app in apps[:5]:
            print(f"  - {app.name} ({app.data.get('vendor', 'Unknown')}) - ${app.cost or 0:,.0f}")

if __name__ == "__main__":
    main()
