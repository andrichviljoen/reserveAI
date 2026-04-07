from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class AuthRequest(BaseModel):
    email: str
    password: str


class WorkspaceSaveRequest(BaseModel):
    user_id: str
    workspace_name: str
    context_data: dict[str, Any]


class UploadRequest(BaseModel):
    user_id: str
    file_name: str
    file_type: str
    file_base64: str


class UploadResponse(BaseModel):
    file_id: Any | None = None
    rows: int
    columns: list[str]
    preview: list[dict[str, Any]]


class DataMapping(BaseModel):
    lob: str
    origin: str
    dev: str
    value: str


class AnalyzeRequest(BaseModel):
    dataset_name: str | None = None
    records: list[dict[str, Any]] | None = None
    line_of_business: str | None = None
    mapping: DataMapping | None = None
    date_format: Literal["YYYYQQ", "YYYYMM", "YYYY", "Standard Datetime"] = "YYYYQQ"
    data_type: Literal["Incremental", "Cumulative"] = "Cumulative"
    method: Literal["Deterministic Chain Ladder", "Bootstrap ODP"] = "Deterministic Chain Ladder"
    averaging_method: Literal["volume", "simple"] = "volume"
    drop_high: int = Field(default=0, ge=0, le=2)
    drop_low: int = Field(default=0, ge=0, le=2)
    bootstrap_simulations: int = Field(default=5000, ge=100, le=20000)
    confidence_level: int = Field(default=75, ge=50, le=99)


class ReportRequest(BaseModel):
    report_type: Literal["word", "excel", "notebook"]
    context_data: dict[str, Any]
    actuary_notes: str = ""
    openai_api_key: str | None = None


class ReportResponse(BaseModel):
    file_name: str
    media_type: str
    file_base64: str


class ChatRequest(BaseModel):
    context_data: dict[str, Any]
    actuary_notes: str = ""
    messages: list[dict[str, str]] = Field(default_factory=list)
    openai_api_key: str | None = None


class ChatResponse(BaseModel):
    content: str
