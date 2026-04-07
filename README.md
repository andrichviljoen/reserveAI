# AI Actuarial Reserving Suite (Decoupled SaaS)

Production-oriented split architecture:
- **Backend**: FastAPI + chainladder + Supabase + OpenAI + python-docx + xlsxwriter
- **Frontend**: React + Vite + Tailwind + Lucide + Recharts

## Backend API
- `POST /auth/signup`
- `POST /auth/login`
- `POST /auth/logout`
- `POST /auth/workspaces/save`
- `GET /auth/workspaces/{user_id}`
- `POST /upload`
- `POST /analyze`
- `POST /generate-report`

## Run

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_BASE` for frontend and `.env` in backend for `SUPABASE_URL`, `SUPABASE_KEY`, and optional `OPENAI_API_KEY`.
