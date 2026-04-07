from __future__ import annotations

import base64

from fastapi import APIRouter, HTTPException

from app.models.schemas import UploadRequest, UploadResponse
from app.services.actuarial import parse_upload
from app.services.supabase_client import get_supabase
from app.utils.serialization import sanitize_json

router = APIRouter(tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
def upload(payload: UploadRequest):
    try:
        file_bytes = base64.b64decode(payload.file_base64)
        df = parse_upload(payload.file_name, file_bytes)

        insert = (
            get_supabase()
            .table("uploaded_files")
            .insert(
                {
                    "user_id": payload.user_id,
                    "file_name": payload.file_name,
                    "file_type": payload.file_type,
                    "file_size": len(file_bytes),
                    "file_base64": payload.file_base64,
                }
            )
            .execute()
        )

        preview = sanitize_json(df.head(20).to_dict(orient="records"))
        return UploadResponse(file_id=(insert.data or [{}])[0].get("id"), rows=int(df.shape[0]), columns=df.columns.tolist(), preview=preview)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
