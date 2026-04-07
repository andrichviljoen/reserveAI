from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schemas import AnalyzeRequest
from app.services.actuarial import analyze

router = APIRouter(tags=["analysis"])


@router.post("/analyze")
def run_analysis(payload: AnalyzeRequest):
    try:
        return analyze(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
