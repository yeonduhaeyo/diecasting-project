# viz/eda_plots.py — optimized & compact (색상 고정 매핑 반영)
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path
from matplotlib.dates import AutoDateLocator, DateFormatter

# Plotly (HTML로 렌더)
import plotly.graph_objects as go
import plotly.io as pio

from functools import lru_cache
import hashlib

# ===== 사용자 설정 =====
CAT_VARS = {"mold_code", "EMS_operation_time", "working", "passorfail", "tryshot_signal", "heating_furnace"}
EXCLUDE_VARS = {"weekday", "month", "name", "id", "line", "mold_name", "time", "date", "emergency_stop", "day"}
NONE_LABEL = "선택 없음"

# Heatmap 전용 제외/정렬
HEATMAP_EXCLUDE = {"passorfail", "mold_code", "EMS_operation_time", "id", "line", "name", "date", "time", "weekday", "month", "day"}
HEATMAP_ORDER = [
    # ① 용탕 준비
    "molten_temp", "molten_volume",
    # ② 반고체 슬러리 제조
    "sleeve_temperature",
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
    p = Path(__file__).resolve().parents[1] / "data" / "var_labels.csv"
    if p.exists():
        df = pd.read_csv(p)
        if {"col", "label"}.issubset(df.columns):
            return {str(r["col"]): str(r["label"]) for _, r in df.dropna(subset=["col"]).iterrows()}
    return {}
VAR_LABELS = _load_var_labels()
def k(col: str) -> str:
    return VAR_LABELS.get(col, col)

# ===== 데이터 로드 공통 =====
def _load_any(name_base: str):
    """data/name_base(.parquet|.csv) 우선순위 로드"""
    data_dir = Path(__file__).resolve().parents[1] / "data"
    for name in (f"{name_base}.parquet", f"{name_base}.csv", name_base):
        p = data_dir / name
        if p.exists():
            return pd.read_parquet(p) if p.suffix.lower()==".parquet" else pd.read_csv(p)
    return None

from shared import df as DF_MAIN
DF_FIXED  = _load_any("fixeddata")    # 전처리 데이터(변수분포/히트맵)

# ===== 공통 유틸 =====
def _fig_msg(msg: str):
    fig, ax = plt.subplots()
    ax.text(0.5, 0.5, msg, ha="center", va="center")
    ax.axis("off")
    return fig

def _has(df: pd.DataFrame, col: str) -> bool:
    return (df is not None) and (col in df.columns) and (col not in EXCLUDE_VARS)

def _is_num(df: pd.DataFrame, col: str) -> bool:
    if col in CAT_VARS:
        return False
    try:
        return pd.api.types.is_numeric_dtype(df[col])
    except Exception:
        return False

# pass/fail → 합/불
_PF_MAP = {
    0: "합", 0.0: "합", "0": "합", "0.0": "합", "PASS": "합", "pass": "합", "Pass": "합",
    1: "불", 1.0: "불", "1": "불", "1.0": "불", "FAIL": "불", "fail": "불", "Fail": "불",
}
def _ensure_pf_hue(df: pd.DataFrame):
    if (df is None) or ("passorfail" not in df.columns):
        return df, None
    df2 = df.copy()
    df2["_pf_"] = df2["passorfail"].map(lambda v: _PF_MAP.get(v, _PF_MAP.get(str(v), str(v))))
    return df2, "_pf_"

def _legend_as_quality(ax):
    leg = ax.get_legend()
    if leg:
        leg.set_title("품질 결과")

# ===== 변수 분포 / 산점도 / 박스플롯 =====
def _plot_single(df: pd.DataFrame, var: str):
    if not _has(df, var):
        return _fig_msg("데이터 없음")
    local, hue = _ensure_pf_hue(df)
    fig, ax = plt.subplots(figsize=(6,4))
    if _is_num(local, var):
        sns.histplot(data=local, x=var, hue=hue, multiple="stack", kde=False, ax=ax)
        ax.set_ylabel("빈도")
    else:
        order = local[var].value_counts(dropna=False).index.tolist()
        sns.countplot(data=local, x=var, order=order, hue=hue, ax=ax)
        ax.set_ylabel("건수")
        ax.set_xticklabels([k(t.get_text()) for t in ax.get_xticklabels()], rotation=20, ha="right")
    ax.set_title(f"{k(var)} 분포" + (" (품질 결과)" if hue else ""))
    ax.set_xlabel(k(var))
    _legend_as_quality(ax)
    plt.tight_layout()
    return fig

def _plot_scatter(df: pd.DataFrame, xcol: str, ycol: str):
    if not (_has(df, xcol) and _has(df, ycol)):
        return _fig_msg("데이터 없음")
    if not (_is_num(df, xcol) and _is_num(df, ycol)):
        return _fig_msg("산점도는 수치형 2개 필요")
    local, hue = _ensure_pf_hue(df)
    fig, ax = plt.subplots(figsize=(6,4))
    sns.scatterplot(data=local, x=xcol, y=ycol, hue=hue, s=20, alpha=0.7, ax=ax)
    ax.set_title(f"{k(xcol)} vs {k(ycol)}" + (" (품질 결과)" if hue else ""))
    ax.set_xlabel(k(xcol)); ax.set_ylabel(k(ycol))
    _legend_as_quality(ax)
    plt.tight_layout()
    return fig

def _plot_box_by_cat(df: pd.DataFrame, num_col: str, cat_col: str):
    if not (_has(df, num_col) and _has(df, cat_col)):
        return _fig_msg("데이터 없음")
    if not (_is_num(df, num_col) and not _is_num(df, cat_col)):
        return _fig_msg("박스플롯은 수치×범주 필요")
    local = df.copy()
    x = cat_col; order = None
    if cat_col == "passorfail":
        local, _ = _ensure_pf_hue(local)
        x = "_pf_"; order = ["합", "불"]
    fig, ax = plt.subplots(figsize=(7,5))
    sns.boxplot(data=local, x=x, y=num_col, order=order, ax=ax)
    xlabel = "품질 결과" if cat_col == "passorfail" else k(cat_col)
    ax.set_title(f"{xlabel}별 {k(num_col)} 분포")
    ax.set_xlabel(xlabel); ax.set_ylabel(k(num_col))
    ax.set_xticklabels([k(t.get_text()) for t in ax.get_xticklabels()], rotation=15, ha="right")
    plt.tight_layout()
    return fig

def _plot_varpair_or_dist_df(df: pd.DataFrame, var1: str, var2: str):
    if (not var1) or (var1 == NONE_LABEL) or (not var2) or (var2 == NONE_LABEL):
        target = var1 if var1 and var1 != NONE_LABEL else var2
        return _plot_single(df, target) if target and target != NONE_LABEL else _fig_msg("변수를 선택하세요.")
    if _is_num(df, var1) and _is_num(df, var2):
        return _plot_scatter(df, var1, var2)
    if _is_num(df, var1) and not _is_num(df, var2):
        return _plot_box_by_cat(df, num_col=var1, cat_col=var2)
    if not _is_num(df, var1) and _is_num(df, var2):
        return _plot_box_by_cat(df, num_col=var2, cat_col=var1)
    return _fig_msg("범주×범주 조합은 미지원")

def plot_varpair_or_dist_main(var1, var2):
    return _plot_varpair_or_dist_df(DF_MAIN, var1, var2)

def plot_varpair_or_dist_fixed(var1, var2):
    if DF_FIXED is None:
        return _fig_msg("전처리 데이터 없음")
    return _plot_varpair_or_dist_df(DF_FIXED, var1, var2)

# ===== Heatmap =====
def _apply_heatmap_order(cols):
    pref = [c for c in HEATMAP_ORDER if c in cols]
    rest = sorted([c for c in cols if c not in HEATMAP_ORDER])
    return pref + rest

def get_fixed_numeric_cols():
    if DF_FIXED is None:
        return []
    return [c for c in DF_FIXED.columns
            if (c not in HEATMAP_EXCLUDE) and pd.api.types.is_numeric_dtype(DF_FIXED[c])]

def plot_corr_heatmap_fixed_subset(selected_cols):
    if DF_FIXED is None:
        return _fig_msg("전처리 데이터(fixeddata)를 찾을 수 없습니다.")
    if not selected_cols:
        return _fig_msg("왼쪽 체크에서 변수를 선택하고 HIT을 누르세요.")
    valid = [c for c in selected_cols
             if c in DF_FIXED.columns
             and (c not in HEATMAP_EXCLUDE)
             and pd.api.types.is_numeric_dtype(DF_FIXED[c])]
    valid = list(dict.fromkeys(valid))
    if len(valid) < 2:
        return _fig_msg("상관관계는 최소 2개 이상의 수치형 변수가 필요합니다.")
    cols = _apply_heatmap_order(valid)
    corr = DF_FIXED[cols].corr(numeric_only=True).rename(index=k, columns=k)
    n = len(cols)
    fig, ax = plt.subplots(figsize=(max(6, 1 + 0.5*n), max(5, 0.45*n + 3)))
    annot = n <= 18
    sns.heatmap(corr, annot=annot, fmt=".2f", cmap="RdBu_r", center=0, ax=ax)
    ax.set_title("상관관계 Heatmap")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
    plt.tight_layout()
    return fig

# ===== (여기부터) 금형코드 색상 고정 매핑 =====
MOLD_CODE_COLOR_MAP: dict[str, str] = {
    "8722": "#2ca02c",  # green
    "8573": "#9467bd",  # purple
    "8412": "#1f77b4",  # blue
    "8917": "#d62728",  # red
    "8600": "#17becf",  # teal
}
_FALLBACK_COLORS = [
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#ff7f0e",
    "#aec7e8", "#98df8a", "#ff9896", "#c5b0d5", "#c49c94",
]
def _color_for_code(code_label: str) -> str:
    key = str(code_label)
    if key in MOLD_CODE_COLOR_MAP:
        return MOLD_CODE_COLOR_MAP[key]
    h = int(hashlib.sha256(key.encode("utf-8")).hexdigest(), 16)
    return _FALLBACK_COLORS[h % len(_FALLBACK_COLORS)]

# ===== fixeddata3: 경량 로더 & Plotly HTML 시계열 =====
_FIXED3_BASE_COLS = ["mold_code", "date", "time_hour", "time_minute"]

def _fixed3_path():
    data_dir = Path(__file__).resolve().parents[1] / "data"
    for name in ("fixeddata3.parquet","fixeddata3.csv","fixeddata3"):
        p = data_dir / name
        if p.exists():
            return p
    return None

@lru_cache(maxsize=16)
def _load_fixed3_light(tuple_cols: tuple[str, ...]) -> pd.DataFrame | None:
    """fixeddata3에서 필요한 열만 로드 + dtype 최적화 + _t_ 생성 (캐시)"""
    p = _fixed3_path()
    if p is None:
        return None
    cols = list(dict.fromkeys(list(tuple_cols)))
    for c in _FIXED3_BASE_COLS:
        if c not in cols:
            cols.append(c)
    try:
        if p.suffix.lower() == ".parquet":
            df = pd.read_parquet(p, columns=cols)
        else:
            df = pd.read_csv(p, usecols=[c for c in cols if c != "_t_"])
    except Exception as e:
        print("[load_fixed3_light] read error:", e)
        return None

    if "mold_code" in df.columns:
        df["mold_code"] = df["mold_code"].astype("category")

    if "_t_" not in df.columns:
        if "date" not in df.columns:
            return None
        date_s = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
        h = pd.to_numeric(df.get("time_hour", 0), errors="coerce").fillna(0).clip(0,23).astype("int16")
        m = pd.to_numeric(df.get("time_minute", 0), errors="coerce").fillna(0).clip(0,59).astype("int16")
        df["_t_"] = date_s + pd.to_timedelta(h, unit="h") + pd.to_timedelta(m, unit="min")
    return df

def get_mold_code_levels():
    """UI 체크리스트용: fixeddata3의 고유 mold_code 문자열 레벨"""
    df = _load_fixed3_light(tuple())
    if df is None or "mold_code" not in df.columns:
        return []
    vals = pd.unique(df["mold_code"].astype(str).fillna("")).tolist()
    return sorted([v for v in vals if v])

def plot_timeseries_fixed3_plotly_html(yvar: str, codes, start_date=None, end_date=None) -> str:
    """
    단일 y변수 / mold_code별 '실선만' 표시
    - 리샘플/보간 없음: 있는 데이터만 시간순으로 연결
    - 간격이 1시간을 초과하면 선을 '끊어서' 공백으로 보이게 (세그먼트 분할)
    - rangeslider + rangeselector + ALL(reset) 버튼
    반환: Plotly HTML (Shiny @render.ui + ui.HTML 로 렌더)
    """
    import pandas as pd

    fig = go.Figure()
    if not yvar:
        fig.add_annotation(text="세부 변수를 선택하세요.", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return pio.to_html(fig, include_plotlyjs="cdn", full_html=False)

    # 필요한 열만 로드 (_t_ 포함)
    df = _load_fixed3_light((yvar,))
    if df is None or df.empty:
        fig.add_annotation(text="fixeddata3를 읽을 수 없습니다.", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return pio.to_html(fig, include_plotlyjs="cdn", full_html=False)

    # 날짜 범위: 하루만 선택되면 [00:00, 다음날 00:00)로 확장
    start_ts = pd.to_datetime(start_date) if start_date else None
    end_ts   = pd.to_datetime(end_date) if end_date else None
    if start_ts is not None and end_ts is not None and start_ts.normalize() == end_ts.normalize():
        end_ts = end_ts + pd.Timedelta(days=1)

    # 기간 필터
    if start_ts is not None:
        df = df[df["_t_"] >= start_ts]
    if end_ts is not None:
        df = df[df["_t_"] <= end_ts]
    if df.empty:
        fig.add_annotation(text="선택한 기간에 데이터가 없습니다.", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return pio.to_html(fig, include_plotlyjs="cdn", full_html=False)

    # mold_code 필터
    if "mold_code" in df.columns and codes:
        codes = [str(c) for c in codes]
        df["mold_code"] = df["mold_code"].astype(str)
        df = df[df["mold_code"].isin(codes)]
    if df.empty:
        fig.add_annotation(text="선택한 mold_code에 데이터가 없습니다.", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return pio.to_html(fig, include_plotlyjs="cdn", full_html=False)

    # y 숫자화 & 결측 제거
    df[yvar] = pd.to_numeric(df[yvar], errors="coerce")
    df = df.dropna(subset=[yvar, "_t_"])

    GAP = pd.Timedelta(hours=1)

    def _add_segments_for_group(g: pd.DataFrame, code_label: str):
        g = g.sort_values("_t_").reset_index(drop=True)
        ts = pd.to_datetime(g["_t_"])
        ys = pd.to_numeric(g[yvar], errors="coerce")

        col = _color_for_code(str(code_label))  # 고정 색상

        cut = ts.diff() > GAP
        starts = [0] + cut[cut].index.tolist()
        ends = starts[1:] + [len(g)]

        first = True
        for s, e in zip(starts, ends):
            seg_x = ts.iloc[s:e]
            seg_y = ys.iloc[s:e]
            if seg_x.size < 1:
                continue

            # ⚠️ f-string + Plotly placeholder 혼용 금지 → 문자열 연결로 처리
            hovertemplate = (
                (f"금형코드: {code_label}<br>" if code_label else "") +
                "날짜/시간: %{x|%Y-%m-%d %H:%M}<br>" +       # 일반 문자열
                f"{k(yvar)}: " + "%{y:.3g}<extra></extra>"   # 일반 문자열과 f-string을 분리
            )

            fig.add_trace(
                go.Scatter(
                    x=seg_x,
                    y=seg_y,
                    mode="lines",
                    name=str(code_label),
                    legendgroup=str(code_label),
                    showlegend=first,
                    line=dict(color=col, width=2),
                    hovertemplate=hovertemplate,
                    connectgaps=False,
                )
            )
            first = False

    if "mold_code" in df.columns:
        for code, g in df.groupby("mold_code", sort=False):
            _add_segments_for_group(g, code)
    else:
        _add_segments_for_group(df, k(yvar))

    fig.update_layout(
        margin=dict(l=50, r=50, t=60, b=60),
        legend=dict(title="금형코드"),
        title=f"{k(yvar)} 시계열 탐색",
        xaxis=dict(
            title="날짜/시간",
            rangeselector=dict(
                buttons=[
                    dict(count=30, step="minute", stepmode="backward", label="30m"),
                    dict(count=1,  step="hour",   stepmode="backward", label="1h"),
                    dict(count=6,  step="hour",   stepmode="backward", label="6h"),
                    dict(count=12, step="hour",   stepmode="backward", label="12h"),
                    dict(count=1,  step="day",    stepmode="backward", label="1d"),
                    dict(step="all", label="ALL"),
                ]
            ),
            rangeslider=dict(visible=True),
            type="date",
        ),
        yaxis=dict(title=k(yvar), autorange=True, rangemode="normal"),
        template="plotly_white",
    )
    return pio.to_html(fig, include_plotlyjs="cdn", full_html=False)
