#!/usr/bin/env python3
"""Write the .env file with dev defaults."""
content = """\
# =============================================================================
# HealthCore Digital - Local Development Environment (NOT FOR PRODUCTION)
# =============================================================================
# This file is .gitignore'd. Never commit secrets to version control.
# =============================================================================

# --- Backend - JWT Auth ---
SECRET_KEY=dev-secret-key-change-in-production-abc123def456
ACCESS_TOKEN_EXPIRE_MINUTES=30
PASSWORD_RESET_EXPIRE_MINUTES=60

# --- Backend - Database (leave blank for local SQLite) ---
INVENTORY_DATABASE_URL=

# --- Backend - Auth DB ---
AUTH_DB_PATH=

# --- Backend - Seed data password ---
INVENTORY_SEED_PASSWORD=dev-seed-password

# --- Backend - Email (disabled in dev) ---
EMAIL_PROVIDER=
RESEND_API_KEY=
SENDGRID_API_KEY=
EMAIL_FROM=HealthCore <onboarding@resend.dev>

# --- Frontend - Internal service discovery (Docker DNS) ---
HC_API_INTERNAL_URL=http://backend:8000

# --- Frontend - Public env vars ---
NEXT_PUBLIC_API_URL=/backend
NEXT_PUBLIC_INCIDENT_API_URL=/backend
NEXT_PUBLIC_INVENTORY_API_URL=/backend

# --- Frontend - CORS / UI origin ---
FRONTEND_BASE_URL=http://localhost:3001
"""
with open("/workspaces/Jenefa-Company/.env", "w") as f:
    f.write(content)
print(".env written successfully")