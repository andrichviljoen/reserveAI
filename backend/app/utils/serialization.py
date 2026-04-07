from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd


def sanitize_json(value: Any) -> Any:
    """Recursively coerce objects into strict JSON-safe primitives.

    Handles:
    - NaN / +/-Inf -> None
    - Pandas Period/Timestamp/Index -> string/list
    - numpy scalars -> python scalars
    - dict keys -> stringified
    """
    if isinstance(value, dict):
        return {str(k): sanitize_json(v) for k, v in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [sanitize_json(v) for v in value]

    if isinstance(value, (pd.Timestamp, pd.Period, np.datetime64)):
        return str(value)

    if isinstance(value, (pd.Index, pd.Series)):
        return [sanitize_json(v) for v in value.tolist()]

    if isinstance(value, np.ndarray):
        return [sanitize_json(v) for v in value.tolist()]

    if isinstance(value, (np.integer,)):
        return int(value)

    if isinstance(value, (np.floating, float)):
        f = float(value)
        if math.isnan(f) or math.isinf(f):
            return None
        return f

    return value
