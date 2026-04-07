from __future__ import annotations

import base64
import io
from typing import Any

import pandas as pd

from app.services.supabase_client import get_supabase


def save_uploaded_file(user_id: str, file_name: str, file_type: str, file_bytes: bytes) -> Any:
    payload = {
        "user_id": str(user_id),
        "file_name": file_name,
        "file_type": file_type,
        "file_size": len(file_bytes),
        "file_base64": base64.b64encode(file_bytes).decode("utf-8"),
    }
    return get_supabase().table("uploaded_files").insert(payload).execute()


def list_uploaded_files(user_id: str) -> list[dict[str, Any]]:
    res = (
        get_supabase()
        .table("uploaded_files")
        .select("id, file_name, file_base64, created_at")
        .eq("user_id", str(user_id))
        .order("created_at", desc=True)
        .execute()
    )
    return res.data or []


def load_uploaded_dataframe(file_base64: str, file_name: str) -> pd.DataFrame:
    file_bytes = base64.b64decode(file_base64)
    file_buffer = io.BytesIO(file_bytes)
    if file_name.lower().endswith(".csv"):
        return pd.read_csv(file_buffer)
    if file_name.lower().endswith(".xlsx"):
        return pd.read_excel(file_buffer)
    raise ValueError("Unsupported file type. Only CSV and XLSX are supported.")