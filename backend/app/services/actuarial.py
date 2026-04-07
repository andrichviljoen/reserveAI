from __future__ import annotations

import io
from typing import Any

import chainladder as cl
import numpy as np
import pandas as pd

from app.models.schemas import AnalyzeRequest
from app.utils.serialization import sanitize_json


def _parse_dates(series: pd.Series, fmt: str):
    s_str = series.astype(str).str.strip()
    if fmt == "YYYYQQ":
        return pd.PeriodIndex(s_str.str[:4] + "Q" + s_str.str[-1:], freq="Q")
    if fmt == "YYYYMM":
        return pd.PeriodIndex(s_str.str[:4] + "-" + s_str.str[4:6], freq="M")
    if fmt == "YYYY":
        return pd.PeriodIndex(s_str.str[:4], freq="Y")
    return pd.to_datetime(series).dt.to_period()


def _triangle_from_request(payload: AnalyzeRequest):
    if payload.dataset_name:
        tri = cl.load_sample(payload.dataset_name)
        tri.origin = tri.origin.astype(str)
        return tri, payload.dataset_name

    if not payload.records or not payload.mapping or not payload.line_of_business:
        raise ValueError("For custom data, records + mapping + line_of_business are required.")

    df = pd.DataFrame(payload.records)
    m = payload.mapping
    filtered_df = df[df[m.lob] == payload.line_of_business].copy()
    filtered_df["__origin_mapped"] = _parse_dates(filtered_df[m.origin], payload.date_format)
    filtered_df["__dev_mapped"] = _parse_dates(filtered_df[m.dev], payload.date_format)
    is_cumulative = payload.data_type == "Cumulative"

    tri = cl.Triangle(
        filtered_df,
        origin="__origin_mapped",
        development="__dev_mapped",
        columns=m.value,
        cumulative=is_cumulative,
    )
    if not is_cumulative:
        tri = tri.incr_to_cum()
    return tri, payload.line_of_business


def analyze(payload: AnalyzeRequest) -> dict[str, Any]:
    triangle, dataset = _triangle_from_request(payload)

    det_model = cl.Pipeline(
        [
            ("dev", cl.Development(average=payload.averaging_method, drop_high=payload.drop_high, drop_low=payload.drop_low)),
            ("cl", cl.Chainladder()),
        ]
    ).fit(triangle)

    lrs = triangle.link_ratio.to_frame()
    resids_obj = det_model.named_steps["dev"].std_residuals_

    boot_model, sim_totals = None, np.array([])
    try:
        sims = cl.BootstrapODPSample(n_sims=payload.bootstrap_simulations, random_state=42).fit_transform(triangle)
        boot_model = cl.Pipeline(
            [
                ("dev", cl.Development(average=payload.averaging_method, drop_high=payload.drop_high, drop_low=payload.drop_low)),
                ("cl", cl.Chainladder()),
            ]
        ).fit(sims)
        totals = boot_model.named_steps["cl"].ibnr_.sum("origin").values.flatten()
        sim_totals = totals[~np.isnan(totals)]
    except Exception:
        sim_totals = np.array([])

    det_ibnr = float(det_model.named_steps["cl"].ibnr_.sum())
    det_ult = float(det_model.named_steps["cl"].ultimate_.sum())

    response = {
        "dataset": dataset,
        "parameters": {
            "averaging_method": payload.averaging_method,
            "drop_high": payload.drop_high,
            "drop_low": payload.drop_low,
            "bootstrap_simulations": payload.bootstrap_simulations,
            "method": payload.method,
        },
        "metrics": {
            "total_ibnr": det_ibnr,
            "total_ultimate": det_ult,
            "bootstrap_mean_ibnr": float(np.mean(sim_totals)) if len(sim_totals) else None,
            "bootstrap_percentile": float(np.percentile(sim_totals, payload.confidence_level)) if len(sim_totals) else None,
        },
        "tables": {
            "triangle": triangle.to_frame().reset_index().to_dict(orient="records"),
            "link_ratios": lrs.reset_index().to_dict(orient="records"),
            "ultimate": det_model.named_steps["cl"].ultimate_.to_frame().reset_index().to_dict(orient="records"),
            "ibnr": det_model.named_steps["cl"].ibnr_.to_frame().reset_index().to_dict(orient="records"),
        },
        "charts": {
            "triangle_development": {
                "type": "line",
                "xKey": "development",
                "series": [c for c in triangle.to_frame().columns],
                "data": triangle.to_frame().reset_index().to_dict(orient="records"),
            },
            "bootstrap_distribution": {
                "type": "histogram",
                "data": [{"ibnr": float(v)} for v in sim_totals[:5000]],
            },
            "residual_scatter": {
                "type": "scatter",
                "data": resids_obj.unstack().reset_index().to_dict(orient="records"),
            },
        },
        "context_data": {
            "deterministic_results": {
                "total_ibnr": det_ibnr,
                "total_ult": det_ult,
                "ibnr_by_origin": det_model.named_steps["cl"].ibnr_.to_dict(),
            },
            "link_ratio_data": {
                "max_ldf": float(lrs.max().max()),
                "min_ldf": float(lrs.min().min()),
            },
            "bootstrap_results": {
                "mean_ibnr": float(np.mean(sim_totals)) if len(sim_totals) else None,
                "p95_ibnr": float(np.percentile(sim_totals, 95)) if len(sim_totals) else None,
                "error": None if len(sim_totals) else "Data too sparse for bootstrap simulations.",
            },
        },
    }

    return sanitize_json(response)


def parse_upload(file_name: str, file_bytes: bytes) -> pd.DataFrame:
    buff = io.BytesIO(file_bytes)
    if file_name.lower().endswith(".csv"):
        return pd.read_csv(buff)
    if file_name.lower().endswith(".xlsx"):
        return pd.read_excel(buff)
    raise ValueError("Unsupported file type. Use CSV or XLSX.")
