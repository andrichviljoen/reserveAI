# AI Actuarial Reserving Suite (FastAPI + React)

This codebase now mirrors the Streamlit workflow with a decoupled architecture:
- Supabase auth + cloud workspaces + uploaded file storage
- Chainladder deterministic and bootstrap ODP actuarial engine
- AvE and Barnett-Zehnwirth residual diagnostics
- Word/Excel/Notebook exports
- A(I)ctuary chat via backend OpenAI endpoint

## Backend endpoints
- `POST /auth/signup`
- `POST /auth/login`
- `POST /auth/logout`
- `POST /auth/workspaces/save`
- `GET /auth/workspaces/{user_id}`
- `POST /upload`
- `GET /upload/files/{user_id}`
- `POST /analyze`
- `POST /generate-report`
- `POST /chat`
