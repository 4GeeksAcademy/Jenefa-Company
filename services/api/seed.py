"""Idempotent seeder for the HealthCore supplier directory.

Run with:
  uv run seed
  python seed.py
"""

from __future__ import annotations

import json
from constants import SUPPLIERS_SEED
from database import close_db, count_suppliers, insert_seed_record


def seed() -> int:
    """Load seed suppliers only when the database is empty.

    Reads `db.json` first. If any supplier rows already exist, skips insertion
    entirely so re-running `uv run seed` never duplicates data.

    Returns the number of newly inserted records.
    """
    if count_suppliers() > 0:
        return 0

    inserted = 0
    for row in SUPPLIERS_SEED:
        insert_seed_record(row)
        inserted += 1
    return inserted


def main() -> None:
    try:
        # ---- VISUAL CONSOLE TERMINAL OUTPUT ----
        print("\n" + "="*60)
        print(f"📋 LOADING SUPPLIERS DIRECTORY DATA ({len(SUPPLIERS_SEED)} Records)")
        print("="*60)
        
        for index, supplier in enumerate(SUPPLIERS_SEED, start=1):
            name = supplier.get("name")
            country = supplier.get("country")
            status = supplier.get("status", "unknown").upper()
            rate = f"{supplier.get('currency')} {supplier.get('monthly_rate'):,.2f}"
            
            # Print a clean, formatted line for every record in the seed list
            print(f" [{index:02d}] {name:<26} | Country: {country:<3} | Rate: {rate:<10} | Status: {status}")
        
        print("="*60)
        
        # Run original database logic
        inserted = seed()
        
        if inserted == 0:
            print("⚠️  Database already contains rows. Skipped duplicating data.")
        else:
            print(f"✅ Success! Newly inserted {inserted} records into the database.")
        print("="*60 + "\n")
        
    finally:
        close_db()


if __name__ == "__main__":
    main()
