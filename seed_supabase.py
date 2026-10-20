import os
import json
from sqlalchemy import create_engine, text
from datetime import datetime, timezone

# 1. Read the environment variable directly out of your services/api/.env file
env_path = "/workspaces/Jenefa-Company/services/api/.env"
db_url = None

if os.path.exists(env_path):
    with open(env_path, "r") as f:
        for line in f:
            if line.startswith("TELEMETRY_DATABASE_URL="):
                # Clean up quotes and strip spacing parameters
                db_url = line.split("=", 1)[1].strip().strip('"').strip("'")
                break

if not db_url:
    print("❌ Error: Could not find TELEMETRY_DATABASE_URL inside services/api/.env")
    exit(1)

# 2. Establish connection engine
engine = create_engine(db_url)
now_iso = datetime.now(timezone.utc).isoformat()

events = [
    ("appointment_booked", {"market_region": "market_us", "clinic_location_id": "TEXAS-01", "network_appointment_volume": 1}),
    ("appointment_booked", {"market_region": "market_us", "clinic_location_id": "FLORIDA-02", "network_appointment_volume": 1}),
    ("appointment_noshow_predicted", {"market_region": "market_us", "clinic_location_id": "TEXAS-01"}),
    ("billing_claim_compiled", {"market_region": "market_us", "status": "error", "error": "Invalid Insurance"}),
    ("billing_claim_compiled", {"market_region": "market_uk", "status": "processed"}),
    ("revenue_stream_reconciled", {"currency": "USD", "net_settled_amount": 18450.00})
]

try:
    with engine.connect() as conn:
        for idx, (etype, tags) in enumerate(events, start=900):
            query = text("""
                INSERT INTO telemetry_events (id, event_type, timestamp, service, tags)
                VALUES (:id, :event_type, :timestamp, :service, :tags)
                ON CONFLICT (id) DO NOTHING
            """)
            conn.execute(query, {
                "id": str(idx),
                "event_type": etype,
                "timestamp": now_iso,
                "service": "healthcore-bi-service",
                "tags": json.dumps(tags)
            })
        conn.commit()
    print("🎉 Success! 6 live production rows seeded into your Supabase database directly via your .env URL.")
except Exception as e:
    print(f"❌ Failed to seed database: {e}")
