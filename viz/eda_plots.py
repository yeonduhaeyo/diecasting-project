import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from pathlib import Path
from matplotlib.dates import AutoDateLocator, DateFormatter
from shared import df as DF_MAIN

# ===== 사용자 설정 =====
CAT_VARS = {"mold_code", "EMS_operation_time", "working", "passorfail", "tryshot_signal", "heating_furnace"}
EXCLUDE_VARS = {"weekday", "month", "name", "id", "line", "mold_name", "time", "date", "emergency_stop", "day"}
NONE_LABEL = "선택 없음"

# Heatmap 전용 제외/정렬
HEATMAP_EXCLUDE = {"passorfail", "mold_code", "id", "line", "name", "date", "time", "weekday", "month", "day"}
HEATMAP_ORDER = [
    # ① 용탕 준비
    "molten_temp", "molten_volume",
    # ② 반고체 슬러리 제조
    "sleeve_temperature", "EMS_operation_time",
    # ③ 사출 & 금형 충전
    "low_section_speed", "high_section_speed", "cast_pressure",
    "biscuit_thickness", "physical_strength",
    # ④ 응고
    "upper_mold_temp1", "upper_mold_temp2", "upper_mold_temp3",
    "lower_mold_temp1", "lower_mold_temp2", "lower_mold_temp3",
    "Coolant_temperature",
]

# ===== 한글 라벨 로드 =====
def _load_var_labels():
    try:
        p = Path(__file__).resolve().parents[1] / "data" / "var_labels.csv"
        if p.exists():
            df = pd.read_csv(p)
            if {"col", "label"}.issubset(df.columns):
                return {str(r["col"]): str(r["label"]) for _, r in df.dropna(subset=["col"]).iterrows()}
    except Exception as e:
        print("[eda_plots] var_labels load error:", e)
    return {}
VAR_LABELS = _load_var_labels()

def k(col: str) -> str:
    return VAR_LABELS.get(col, col)

# ===== 전처리 데이터 로드 =====
def _load_any(name_base: str):
    """data/name_base(.parquet|.csv) 우선순위로 로드"""
    try:
        data_dir = Path(__file__).resolve().parents[1] / "data"
        for name in (f"{name_base}.parquet", f"{name_base}.csv", name_base):
            p = data_dir / name
            if p.exists():
                return pd.read_parquet(p) if p.suffix.lower()==".parquet" else pd.read_csv(p)
    except Exception as e:
        print(f"[eda_plots] load error for {name_base}:", e)
    return None

DF_FIXED  = _load_any("fixeddata")    # (상관관계/변수분포 전처리용)
DF_FIXED3 = _load_any("fixeddata3")   # (공정별 탐색 전용)

# ===== 유틸 =====
def _has(df, col): return (col in df.columns) and (col not in EXCLUDE_VARS)

def _is_num(df, col):
    if col in CAT_VARS: return False
    try: return pd.api.types.is_numeric_dtype(df[col])
    except: return False

def _is_cat(df, col): return not _is_num(df, col)

def detect_date_column(df):
    for c in ("date","Date","DATE","datetime","timestamp","time"):
        if c in df.columns: return c
    for c in df.columns:
        try:
            if pd.api.types.is_datetime64_any_dtype(df[c]): return c
        except: pass
    return None

def ensure_datetime_series(df, col):
    s = df[col]
    return s if pd.api.types.is_datetime64_any_dtype(s) else pd.to_datetime(s, errors="coerce", infer_datetime_format=True)

# ---- passorfail 라벨 매핑(범례/축에 “합/불”로 보이도록) ----
_PF_MAP = {
    0: "합", 0.0: "합", "0": "합", "0.0": "합", "PASS": "합", "pass": "합", "Pass": "합",
    1: "불", 1.0: "불", "1": "불", "1.0": "불", "FAIL": "불", "fail": "불", "Fail": "불",
}
def _pf_series(df):
    if "passorfail" not in df.columns:
        return None
    s = df["passorfail"]
    try:
        return s.map(lambda v: _PF_MAP.get(v, _PF_MAP.get(str(v), str(v))))
    except Exception:
        return s

def _apply_pf_legend(ax):
    leg = ax.get_legend()
    if leg is not None:
        try:
            leg.set_title("품질 결과")
        except Exception:
            pass

# ===== 변수 분포 / 산점도 / 박스플롯 =====
def _plot_single(df, var):
    if (df is None) or (not _has(df, var)):
        fig, ax = plt.subplots(); ax.text(0.5,0.5,"데이터 없음",ha="center",va="center"); ax.axis("off"); return fig
    local = df.copy()
    fig, ax = plt.subplots(figsize=(6,4))
    if "passorfail" in local.columns:
        local["_pf_"] = _pf_series(local)
        hue = "_pf_"
    else:
        hue = None

    if _is_num(local, var):
        sns.histplot(data=local, x=var, hue=hue, multiple="stack", kde=False, ax=ax); ax.set_ylabel("빈도")
    else:
        order = local[var].value_counts(dropna=False).index.tolist()
        sns.countplot(data=local, x=var, order=order, hue=hue, ax=ax); ax.set_ylabel("건수")
        ax.set_xticklabels([k(t.get_text()) for t in ax.get_xticklabels()], rotation=20, ha="right")
    ax.set_title(f"{k(var)} 분포" + (" (품질 결과)" if hue else ""))
    ax.set_xlabel(k(var))
    _apply_pf_legend(ax)
    plt.tight_layout(); return fig

def _plot_scatter(df, xcol, ycol):
    if (df is None) or (not (_has(df,xcol) and _has(df,ycol))):
        fig, ax = plt.subplots(); ax.text(0.5,0.5,"데이터 없음",ha="center",va="center"); ax.axis("off"); return fig
    if not (_is_num(df,xcol) and _is_num(df,ycol)):
        fig, ax = plt.subplots(); ax.text(0.5,0.5,"산점도는 수치형 2개 필요",ha="center",va="center"); ax.axis("off"); return fig
    local = df.copy()
    fig, ax = plt.subplots(figsize=(6,4))
    hue = None
    if "passorfail" in local.columns:
        local["_pf_"] = _pf_series(local); hue = "_pf_"
    sns.scatterplot(data=local, x=xcol, y=ycol, hue=hue, s=20, alpha=0.7, ax=ax)
    ax.set_title(f"{k(xcol)} vs {k(ycol)}" + (" (품질 결과)" if hue else ""))
    ax.set_xlabel(k(xcol)); ax.set_ylabel(k(ycol))
    _apply_pf_legend(ax)
    plt.tight_layout(); return fig

def _plot_box_by_cat(df, num_col, cat_col):
    if (df is None) or (not (_has(df,num_col) and _has(df,cat_col))):
        fig, ax = plt.subplots(); ax.text(0.5,0.5,"데이터 없음",ha="center",va="center"); ax.axis("off"); return fig
    if not (_is_num(df,num_col) and _is_cat(df,cat_col)):
        fig, ax = plt.subplots(); ax.text(0.5,0.5,"박스플롯은 수치×범주 필요",ha="center",va="center"); ax.axis("off"); return fig

    local = df.copy()
    x = cat_col
    order = None
    if cat_col == "passorfail":
        local["_pf_"] = _pf_series(local)
        x = "_pf_"
        order = ["합", "불"]

    fig, ax = plt.subplots(figsize=(7,5))
    sns.boxplot(data=local, x=x, y=num_col, order=order, ax=ax)
    xlabel = "품질 결과" if cat_col == "passorfail" else k(cat_col)
    ax.set_title(f"{xlabel}별 {k(num_col)} 분포")
    ax.set_xlabel(xlabel); ax.set_ylabel(k(num_col))
    ax.set_xticklabels([k(t.get_text()) for t in ax.get_xticklabels()], rotation=15, ha="right")
    plt.tight_layout(); return fig

def _plot_varpair_or_dist_df(df, var1, var2):
    if (not var1) or (var1==NONE_LABEL) or (not var2) or (var2==NONE_LABEL):
        target = var1 if var1 and var1!=NONE_LABEL else var2
        if not target or target==NONE_LABEL:
            fig, ax = plt.subplots(); ax.text(0.5,0.5,"변수를 선택하세요.",ha="center",va="center"); ax.axis("off"); return fig
        return _plot_single(df, target)
    a, b = var1, var2
    if _is_num(df,a) and _is_num(df,b): return _plot_scatter(df,a,b)
    if _is_num(df,a) and _is_cat(df,b): return _plot_box_by_cat(df, num_col=a, cat_col=b)
    if _is_cat(df,a) and _is_num(df,b): return _plot_box_by_cat(df, num_col=b, cat_col=a)
    fig, ax = plt.subplots(); ax.text(0.5,0.5,"범주×범주 조합은 미지원",ha="center",va="center"); ax.axis("off"); return fig

def plot_varpair_or_dist_main(var1, var2): return _plot_varpair_or_dist_df(DF_MAIN, var1, var2)

def plot_varpair_or_dist_fixed(var1, var2):
    if DF_FIXED is None:
        fig, ax = plt.subplots(); ax.text(0.5,0.5,"전처리 데이터 없음",ha="center",va="center"); ax.axis("off"); return fig
    return _plot_varpair_or_dist_df(DF_FIXED, var1, var2)

# ===== Heatmap =====
def _apply_heatmap_order(cols):
    pref = [c for c in HEATMAP_ORDER if c in cols]
    rest = sorted([c for c in cols if c not in HEATMAP_ORDER])
    return pref + rest

def get_fixed_numeric_cols():
    if DF_FIXED is None:
        return []
    cols = []
    for c in DF_FIXED.columns:
        if c in HEATMAP_EXCLUDE:
            continue
        try:
            if pd.api.types.is_numeric_dtype(DF_FIXED[c]):
                cols.append(c)
        except Exception:
            pass
    return cols

def plot_corr_heatmap_fixed_subset(selected_cols):
    if DF_FIXED is None:
        fig, ax = plt.subplots(); ax.text(0.5,0.5,"전처리 데이터(fixeddata)를 찾을 수 없습니다.",ha="center",va="center"); ax.axis("off"); return fig
    if not selected_cols:
        fig, ax = plt.subplots(); ax.text(0.5,0.5,"왼쪽에서 변수를 선택하고 HIT을 누르세요.",ha="center",va="center"); ax.axis("off"); return fig

    valid = []
    for c in selected_cols:
        if c in DF_FIXED.columns and c not in HEATMAP_EXCLUDE:
            try:
                if pd.api.types.is_numeric_dtype(DF_FIXED[c]):
                    valid.append(c)
            except Exception:
                pass
    valid = list(dict.fromkeys(valid))
    if len(valid) < 2:
        fig, ax = plt.subplots(); ax.text(0.5,0.5,"상관관계는 최소 2개 이상의 수치형 변수가 필요합니다.",ha="center",va="center"); ax.axis("off"); return fig

    cols = _apply_heatmap_order(valid)
    corr = DF_FIXED[cols].corr(numeric_only=True)
    corr = corr.rename(index=k, columns=k)

    n = len(cols)
    w = max(6, min(1 + 0.6 * n, 18))
    h = max(5, min(0.5 * n + 4, 18))

    fig, ax = plt.subplots(figsize=(w, h))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r", center=0, ax=ax)
    ax.set_title("상관관계 Heatmap (전처리 데이터 - 선택 변수)")
    plt.tight_layout()
    return fig

# ===== 공정별 탐색 (fixeddata3 전용) =====
def _prep_ts_from_fixed3(start_date, end_date):
    if DF_FIXED3 is None:
        return None
    dcol = detect_date_column(DF_FIXED3) or "date"
    if dcol not in DF_FIXED3.columns:
        return None

    tmp = DF_FIXED3.copy()
    date_s = pd.to_datetime(tmp[dcol], errors="coerce", infer_datetime_format=True).dt.normalize()
    h = pd.to_numeric(tmp.get("time_hour", 0), errors="coerce").fillna(0).astype(int).clip(0, 23)
    m = pd.to_numeric(tmp.get("time_minute", 0), errors="coerce").fillna(0).astype(int).clip(0, 59)

    tmp["_t_"] = date_s + pd.to_timedelta(h, unit="h") + pd.to_timedelta(m, unit="m")
    tmp = tmp.dropna(subset=["_t_"])

    if start_date: tmp = tmp[tmp["_t_"] >= pd.to_datetime(start_date)]
    if end_date:   tmp = tmp[tmp["_t_"] <= pd.to_datetime(end_date)]

    return tmp

def get_mold_code_levels():
    if DF_FIXED3 is None or "mold_code" not in DF_FIXED3.columns:
        return []
    vals = pd.unique(DF_FIXED3["mold_code"].astype(str).fillna("")).tolist()
    vals = [v for v in vals if v != ""]
    return sorted(vals)

def plot_timeseries_fixed3_by_codes(y_var: str, codes: list, start_date=None, end_date=None):
    tmp = _prep_ts_from_fixed3(start_date, end_date)
    if tmp is None or tmp.empty:
        fig, ax = plt.subplots(); ax.text(0.5,0.5,"fixeddata3에서 시간 축을 만들 수 없습니다.",ha="center",va="center"); ax.axis("off"); return fig

    if y_var not in tmp.columns:
        fig, ax = plt.subplots(); ax.text(0.5,0.5,"선택한 변수가 존재하지 않습니다.",ha="center",va="center"); ax.axis("off"); return fig
    tmp[y_var] = pd.to_numeric(tmp[y_var], errors="coerce")

    hue = None
    if "mold_code" in tmp.columns:
        tmp["mold_code"] = tmp["mold_code"].astype(str)
        if codes:
            tmp = tmp[tmp["mold_code"].isin([str(c) for c in codes])]
        hue = "mold_code"

    if "_t_" not in tmp.columns:
        fig, ax = plt.subplots(); ax.text(0.5,0.5,"시간 축(_t_)을 만들 수 없습니다.",ha="center",va="center"); ax.axis("off"); return fig
    tmp = tmp.set_index("_t_")

    import numpy as np
    s = tmp[y_var].copy()
    if np.isfinite(s).sum() == 0:
        fig, ax = plt.subplots(); ax.text(0.5,0.5,"선택한 변수에 유효한 숫자 데이터가 없습니다.",ha="center",va="center"); ax.axis("off"); return fig

    if hue:
        frames = []
        for code, g in tmp.groupby(hue):
            ser = pd.to_numeric(g[y_var], errors="coerce")
            rs = ser.resample("T").mean()
            df_rs = rs.to_frame(name=y_var).reset_index()
            df_rs[hue] = code
            frames.append(df_rs)
        plot_df = pd.concat(frames, ignore_index=True)
    else:
        rs = s.resample("T").mean()
        plot_df = rs.to_frame(name=y_var).reset_index()

    fig, ax = plt.subplots(figsize=(11, 5))
    if hue:
        sns.lineplot(data=plot_df, x="_t_", y=y_var, hue=hue, ax=ax)
        leg = ax.legend(loc="upper left", bbox_to_anchor=(0.0, 1.02), frameon=True)
        if leg: leg.set_title("mold_code")
    else:
        sns.lineplot(data=plot_df, x="_t_", y=y_var, ax=ax)

    ax.set_title(f"{k(y_var)} 시계열 그래프")
    ax.set_xlabel("날짜/시간"); ax.set_ylabel(k(y_var))
    ax.tick_params(axis="x", labelsize=8); ax.tick_params(axis="y", labelsize=9)
    ax.xaxis.set_major_locator(AutoDateLocator(minticks=5, maxticks=12))
    ax.xaxis.set_major_formatter(DateFormatter("%m-%d %H:%M"))
    plt.tight_layout()
    return fig
