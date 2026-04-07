from __future__ import annotations

import base64

from fastapi import APIRouter, HTTPException

from app.models.schemas import UploadRequest, UploadResponse
from app.services.storage import list_uploaded_files, load_uploaded_dataframe, save_uploaded_file
from app.utils.serialization import sanitize_json

router = APIRouter(tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
def upload(payload: UploadRequest):
    try:
        file_bytes = base64.b64decode(payload.file_base64)
        save_res = save_uploaded_file(payload.user_id, payload.file_name, payload.file_type, file_bytes)
        df = load_uploaded_dataframe(payload.file_base64, payload.file_name)
        return UploadResponse(
            file_id=(save_res.data or [{}])[0].get("id"),
            rows=int(df.shape[0]),
            columns=df.columns.tolist(),
            preview=sanitize_json(df.head(20).to_dict(orient="records")),
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/upload/files/{user_id}")
def files(user_id: str):
    return sanitize_json(list_uploaded_files(user_id))
