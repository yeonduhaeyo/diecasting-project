# utils/model_utils.py
import joblib
import pandas as pd
import numpy as np
from pathlib import Path

def try_load_model(path: Path):
    if not path.exists():
        return None, "모델 파일이 없습니다."
    try:
        return joblib.load(path), "Loaded model."
    except Exception as e:
        return None, f"로딩 실패: {e}"

def try_load_split(path: Path):
    if not path.exists():
        return None, "분할 파일이 없습니다. (선택사항)"
    try:
        return joblib.load(path), "Loaded split."
    except Exception as e:
        return None, f"split 로딩 실패: {e}"

def normalize_inputs(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "working" in out.columns:
        mapping = {"가동":"Y","비가동":"N","y":"Y","n":"N","Y":"Y","N":"N",
                   "1":"Y","0":"N","true":"Y","false":"N","True":"Y","False":"N"}
        out["working"] = out["working"].astype(str).map(lambda v: mapping.get(v, v))
    return out

def align_columns_like_training(X: pd.DataFrame, model) -> pd.DataFrame:
    cols = getattr(model, "feature_names_in_", None)
    return X if cols is None else X.reindex(columns=list(cols), fill_value=np.nan)
