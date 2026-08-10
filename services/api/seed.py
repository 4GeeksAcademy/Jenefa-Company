"""Idempotent seeder for the HealthCore supplier directory.

Run with:
  uv run seed
  python seed.py
"""

from __future__ import annotations

from constants import SUPPLIERS_SEED
from database import close_db, count_suppliers, find_by_name, insert_seed_record


def seed() -> int:
    """Insert seed suppliers that are not already present (matched by name).

    Returns the number of newly inserted records.
    """
    existing = count_suppliers()
    if existing > 0:
        # Idempotency: skip names already in the store; allow partial re-runs.
        inserted = 0
        for row in SUPPLIERS_SEED:
            if find_by_name(row["name"]) is not None:
                continue
            insert_seed_record(row)
            inserted += 1
        return inserted

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
