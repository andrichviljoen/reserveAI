from __future__ import annotations

from typing import Any

import chainladder as cl
import numpy as np
import pandas as pd

from app.models.schemas import AnalyzeRequest
from app.utils.serialization import sanitize_json


def parse_dates(series: pd.Series, fmt: str):
    s_str = series.astype(str).str.strip()
    if fmt == "YYYYQQ":
        return pd.PeriodIndex(s_str.str[:4] + "Q" + s_str.str[-1:], freq="Q")
    if fmt == "YYYYMM":
        return pd.PeriodIndex(s_str.str[:4] + "-" + s_str.str[4:6], freq="M")
    if fmt == "YYYY":
        return pd.PeriodIndex(s_str.str[:4], freq="Y")
    return pd.to_datetime(series).dt.to_period()


def prepare_triangle(df: pd.DataFrame, lob_selection: str, col_map: dict[str, str], date_format: str, is_cumulative: bool):
    filtered_df = df[df[col_map["lob"]] == lob_selection].copy()
    filtered_df["__origin_mapped"] = parse_dates(filtered_df[col_map["origin"]], date_format)
    filtered_df["__dev_mapped"] = parse_dates(filtered_df[col_map["dev"]], date_format)
    tri = cl.Triangle(
        filtered_df,
        origin="__origin_mapped",
        development="__dev_mapped",
        columns=col_map["value"],
        cumulative=is_cumulative,
    )
    if not is_cumulative:
        tri = tri.incr_to_cum()
    return tri


def fit_bootstrap_model(_tri, n_sims: int, avg_meth: str, d_h: int, d_l: int):
    sims = cl.BootstrapODPSample(n_sims=n_sims, random_state=42).fit_transform(_tri)
    model = cl.Pipeline(
        [
            ("dev", cl.Development(average=avg_meth, drop_high=d_h, drop_low=d_l)),
            ("cl", cl.Chainladder()),
        ]
    ).fit(sims)
    totals = model.named_steps["cl"].ibnr_.sum("origin").values.flatten()
    return model, sims, totals[~np.isnan(totals)]


def _build_triangle(payload: AnalyzeRequest):
    if payload.dataset_name:
        tri = cl.load_sample(payload.dataset_name)
        tri.origin = tri.origin.astype(str)
        return tri, payload.dataset_name

    if not payload.records or not payload.mapping or not payload.line_of_business:
        raise ValueError("Custom analysis needs records + mapping + line_of_business")

    tri = prepare_triangle(
        pd.DataFrame(payload.records),
        payload.line_of_business,
        payload.mapping.model_dump(),
        payload.date_format,
        payload.data_type == "Cumulative",
    )
    return tri, payload.line_of_business


def _build_ave_payload(triangle):
    try:
        val_dates = sorted(triangle.valuation.unique())
        latest_val, prior_val = val_dates[-1], val_dates[-2]
        tri_prior = triangle[triangle.valuation <= prior_val]
        model_prior = cl.Chainladder().fit(cl.TailCurve().fit_transform(tri_prior))
        exp_df = model_prior.full_triangle_.dev_to_val()[model_prior.full_triangle_.dev_to_val().valuation == latest_val].to_frame()
        exp_df.columns = ["Expected"]
        act_df = triangle.latest_diagonal[triangle.origin <= tri_prior.origin.max()].to_frame()
        act_df.columns = ["Actual"]
        ave_final = exp_df.join(act_df, how="inner").dropna()
        ave_final["Variance"] = ave_final["Actual"] - ave_final["Expected"]
        plot_df = ave_final.iloc[::-1].reset_index().rename(columns={"index": "origin"})
        return ave_final, {
            "status": "ok",
            "data": sanitize_json(plot_df.to_dict(orient="records")),
        }
    except Exception as exc:
        return None, {"status": "error", "message": f"Could not calculate AvE: {exc}"}


def analyze(payload: AnalyzeRequest) -> dict[str, Any]:
    triangle, dataset_name = _build_triangle(payload)

    det_model = cl.Pipeline(
        [
            ("dev", cl.Development(average=payload.averaging_method, drop_high=payload.drop_high, drop_low=payload.drop_low)),
            ("cl", cl.Chainladder()),
        ]
    ).fit(triangle)
    lrs = triangle.link_ratio.to_frame()
    resids_obj = det_model.named_steps["dev"].std_residuals_

    try:
        boot_model, sims, sim_totals = fit_bootstrap_model(
            triangle,
            payload.bootstrap_simulations,
            payload.averaging_method,
            payload.drop_high,
            payload.drop_low,
        )
        bootstrap_error = None
    except Exception:
        boot_model, sims, sim_totals, bootstrap_error = None, None, np.array([]), "Data too sparse for bootstrap simulations."

    ave_df, ave_payload = _build_ave_payload(triangle)
    first_age = None
    ldf_distribution = []
    if boot_model is not None:
        try:
            sim_ldfs = boot_model.named_steps["dev"].ldf_
            act_ldf = det_model.named_steps["dev"].ldf_.drop_duplicates()
            first_age = str(act_ldf.columns[0])
            ldf_distribution = [{"value": float(v)} for v in sim_ldfs.T.loc[act_ldf.columns[0]].tolist()]
        except Exception:
            pass

    response = {
        "dataset": dataset_name,
        "parameters": payload.model_dump(),
        "metrics": {
            "total_ibnr": float(det_model.named_steps["cl"].ibnr_.sum()),
            "total_ultimate": float(det_model.named_steps["cl"].ultimate_.sum()),
            "bootstrap_mean_ibnr": float(np.mean(sim_totals)) if len(sim_totals) else None,
            "bootstrap_percentile": float(np.percentile(sim_totals, payload.confidence_level)) if len(sim_totals) else None,
            "risk_margin": (float(np.percentile(sim_totals, payload.confidence_level) - np.mean(sim_totals)) if len(sim_totals) else None),
        },
        "tables": {
            "triangle": triangle.to_frame().reset_index().to_dict(orient="records"),
            "link_ratios": lrs.reset_index().to_dict(orient="records"),
            "ultimate": det_model.named_steps["cl"].ultimate_.to_frame().reset_index().to_dict(orient="records"),
            "ibnr": det_model.named_steps["cl"].ibnr_.to_frame().reset_index().to_dict(orient="records"),
            "ave": ave_df.reset_index().to_dict(orient="records") if ave_df is not None else [],
        },
        "diagnostics": {
            "ave": ave_payload,
            "residuals": {
                "by_dev": resids_obj.T.reset_index().to_dict(orient="records"),
                "by_origin": resids_obj.reset_index().to_dict(orient="records"),
                "by_valuation": resids_obj.dev_to_val().T.reset_index().to_dict(orient="records"),
                "scatter": resids_obj.unstack().reset_index().to_dict(orient="records"),
            },
            "bootstrap": {
                "error": bootstrap_error,
                "ldf_histogram": {"age": first_age, "data": ldf_distribution},
                "sim_totals": [{"ibnr": float(v)} for v in sim_totals.tolist()],
            },
        },
        "context_data": {
            "dataset": dataset_name,
            "averaging_method": payload.averaging_method,
            "method_ui_selection": payload.method,
            "deterministic_results": {
                "total_ibnr": float(det_model.named_steps["cl"].ibnr_.sum()),
                "total_ult": float(det_model.named_steps["cl"].ultimate_.sum()),
                "ibnr_by_origin": det_model.named_steps["cl"].ibnr_.to_dict(),
            },
            "link_ratio_data": {"max_ldf": float(lrs.max().max()), "min_ldf": float(lrs.min().min())},
            "bootstrap_results": {
                "mean_ibnr": float(np.mean(sim_totals)) if len(sim_totals) else None,
                "p95_ibnr": float(np.percentile(sim_totals, 95)) if len(sim_totals) else None,
                "error": bootstrap_error,
            },
            "ave_analysis": ave_df.to_dict() if ave_df is not None else {},
        },
    }
    return sanitize_json(response)
