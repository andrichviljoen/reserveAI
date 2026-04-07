from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schemas import AuthRequest, WorkspaceSaveRequest
from app.services.supabase_client import get_supabase
from app.utils.serialization import sanitize_json

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup")
def signup(payload: AuthRequest):
    try:
        res = get_supabase().auth.sign_up({"email": payload.email, "password": payload.password})
        return sanitize_json(res.__dict__)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/login")
def login(payload: AuthRequest):
    try:
        res = get_supabase().auth.sign_in_with_password({"email": payload.email, "password": payload.password})
        return {"user": sanitize_json(res.user.__dict__), "session": sanitize_json(res.session.__dict__)}
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"Login failed: {exc}") from exc


@router.post("/logout")
def logout():
    get_supabase().auth.sign_out()
    return {"ok": True}


@router.post("/workspaces/save")
def save_workspace(payload: WorkspaceSaveRequest):
    try:
        res = (
            get_supabase()
            .table("workspaces")
            .upsert(
                {
                    "user_id": payload.user_id,
                    "workspace_name": payload.workspace_name,
                    "context_data": payload.context_data,
                },
                on_conflict="user_id,workspace_name",
            )
            .execute()
        )
        return sanitize_json(res.data)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Workspace save failed: {exc}") from exc


@router.get("/workspaces/{user_id}")
def list_workspaces(user_id: str):
    try:
        res = (
            get_supabase()
            .table("workspaces")
            .select("workspace_name, context_data, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return sanitize_json(res.data or [])
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Workspace fetch failed: {exc}") from exc