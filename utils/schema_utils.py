# utils/schema_utils.py
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any

def build_schema_from_csv(csv_path: str | Path,
                          max_cat_choices: int = 30,
                          mold_topk: int = 5) -> Dict[str, Any]:
    df = pd.read_csv(csv_path)
    if "passorfail" in df.columns:
        df = df.drop(columns=["passorfail"])

    schema = {"num_specs": [], "cat_specs": []}
    FORCE_CAT = {"mold_code"}
    LOW_CARD_K = 5

    for col in df.columns:
        s = df[col]
        is_force_cat = col in FORCE_CAT
        nunq = s.nunique(dropna=True)
        is_low_card_num = (pd.api.types.is_numeric_dtype(s) and nunq <= LOW_CARD_K)

        if is_force_cat or (not pd.api.types.is_numeric_dtype(s)) or is_low_card_num:
            vals = (s.astype(str).fillna("NaN").replace({"nan":"NaN"})
                      .value_counts(dropna=False).index.tolist())
            choices = vals[:max_cat_choices]
            if col == "mold_code":
                choices = vals[:mold_topk] + ["Other"]
            schema["cat_specs"].append({
                "name": col,
                "choices": [str(x) for x in choices],
                "default": str(choices[0]),
            })
        else:
            s_num = pd.to_numeric(s, errors="coerce")
            if s_num.dropna().empty: continue
            p1, p99 = float(s_num.quantile(0.01)), float(s_num.quantile(0.99))
            lo, hi = (p1, p99) if p1 < p99 else (p99, p1)
            mid = float(s_num.median())
            step = 1.0 if np.allclose(s_num.dropna(), s_num.dropna().round()) else 0.1
            schema["num_specs"].append({
                "name": col, "min": lo, "max": hi, "step": step,
                "default": float(np.clip(mid, lo, hi)),
            })

    return schema
