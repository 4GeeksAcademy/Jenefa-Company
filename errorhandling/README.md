#To Run

Terminal A — API

cd services/api
cp -n .env.example .env
Set SECRET_KEY in .env 
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

## Terminal B — staff UI

cd uis/web
npm install
npm run dev
Open http://localhost:3001