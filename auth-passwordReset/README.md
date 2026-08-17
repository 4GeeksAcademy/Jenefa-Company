# To Run 

## Terminal 1 - Run the API

cd services/api
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2 — web

npm run dev:web