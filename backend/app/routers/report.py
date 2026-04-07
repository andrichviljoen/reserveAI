from __future__ import annotations

from fastapi import APIRouter

from app.models.schemas import ChatRequest, ChatResponse, ReportRequest, ReportResponse
from app.services.reporting import chat_completion, generate_excel, generate_notebook_context, generate_word

router = APIRouter(tags=["reporting"])


@router.post("/generate-report", response_model=ReportResponse)
def generate_report(payload: ReportRequest):
    if payload.report_type == "word":
        name, media, f64 = generate_word(payload.context_data, payload.actuary_notes, payload.openai_api_key)
    elif payload.report_type == "excel":
        name, media, f64 = generate_excel(payload.context_data, payload.actuary_notes, payload.openai_api_key)
    else:
        name, media, f64 = generate_notebook_context(payload.context_data, payload.actuary_notes)
    return ReportResponse(file_name=name, media_type=media, file_base64=f64)


@router.post("/chat", response_model=ChatResponse)
def ai_chat(payload: ChatRequest):
    content = chat_completion(
        payload.context_data,
        payload.actuary_notes,
        payload.messages,
        payload.openai_api_key,
    )
    return ChatResponse(content=content)
