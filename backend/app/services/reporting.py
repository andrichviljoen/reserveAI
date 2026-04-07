from __future__ import annotations

import base64
import io
import json
from typing import Any

import pandas as pd
from docx import Document
from openai import OpenAI


def _ai_text(prompt: str, openai_api_key: str | None) -> str:
    if not openai_api_key:
        return "AI commentary unavailable: no API key supplied."
    client = OpenAI(api_key=openai_api_key)
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content or ""


def generate_word(context_data: dict[str, Any], notes: str, openai_api_key: str | None) -> tuple[str, str, str]:
    narrative = _ai_text(
        "Write an exhaustive actuarial reserve report with executive summary, diagnostics, exclusions, and uncertainty."
        f" Context: {json.dumps(context_data)}. Notes: {notes}",
        openai_api_key,
    )
    doc = Document()
    doc.add_heading("Exhaustive Actuarial Reserve Report", 0)
    doc.add_paragraph(narrative)
    buff = io.BytesIO()
    doc.save(buff)
    return "Exhaustive_Actuarial_Report.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", base64.b64encode(buff.getvalue()).decode("utf-8")


def generate_excel(context_data: dict[str, Any], notes: str, openai_api_key: str | None) -> tuple[str, str, str]:
    commentary = _ai_text(
        "Provide concise actuarial workbook commentary in four sections."
        f" Context: {json.dumps(context_data)}. Notes: {notes}",
        openai_api_key,
    )
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        pd.DataFrame(context_data.get("tables", {}).get("triangle", [])).to_excel(writer, sheet_name="Development_Analysis", index=False)
        pd.DataFrame(context_data.get("tables", {}).get("ultimate", [])).to_excel(writer, sheet_name="Reserving_Results", index=False)
        pd.DataFrame([{"commentary": commentary}]).to_excel(writer, sheet_name="Commentary", index=False)
    return "Actuarial_Analysis_Master.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", base64.b64encode(output.getvalue()).decode("utf-8")


def generate_notebook_context(context_data: dict[str, Any], notes: str) -> tuple[str, str, str]:
    text = f"DATA:\n{json.dumps(context_data, indent=2)}\n\nNOTES:\n{notes}"
    return "notebook_source.txt", "text/plain", base64.b64encode(text.encode("utf-8")).decode("utf-8")
