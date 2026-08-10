"""Idempotent seeder for the HealthCore supplier directory.

Run with:
  uv run seed
  python seed.py
"""

from __future__ import annotations

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
        inserted = seed()
        print(f"Inserted {inserted} records.")
    finally:
        close_db()


if __name__ == "__main__":
    main()
