# To Run 

## Terminal 1 - Run the API

cd services/api
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

## Terminal 2 — web

npm run dev:web

## Environment variables to set

SECRET_KEY=your-long-random-secret
FRONTEND_BASE_URL=http://localhost:3001
PASSWORD_RESET_EXPIRE_MINUTES=60
EMAIL_PROVIDER=resend
RESEND_API_KEY=re_your_key_here
EMAIL_FROM=HealthCore <onboarding@resend.dev>