# modules/page_input.py
from shiny import ui
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List

# ==============================
# 1) 공정 그룹 정의 (CSV의 정확한 컬럼명 사용)
# ==============================
PROCESS_GROUPS: Dict[str, Dict[str, Any]] = {
    "g1": {
        "title": "1) 용탕 준비 및 가열",
        "toggle_id": "g1_on",
        "columns": [
            "molten_temp",
            "molten_volume",
        ],
    },
    "g2": {
        "title": "2) 반고체화(전자교반) in sleeve",
        "toggle_id": "g2_on",
        "columns": [
            "sleeve_temperature",
            "EMS_operation_time",
        ],
    },
    "g3": {
        "title": "3) mold에 주입",
        "toggle_id": "g3_on",
        "columns": [
            "cast_pressure",
            "biscuit_thickness",
            "low_section_speed",
            "high_section_speed",
            "physical_strength",
        ],
    },
    "g4": {
        "title": "4) 응고 및 냉각",
        "toggle_id": "g4_on",
        "columns": [
            "upper_mold_temp1",
            "upper_mold_temp2",
            "lower_mold_temp1",
            "lower_mold_temp2",
            "Coolant_temperature",
        ],
    },
    "g5": {
        "title": "5) 전체 과정 관여",
        "toggle_id": "g5_on",
        "columns": [
            "count",
            "working",
            "facility_operation_CycleTime",
            "production_CycleTime",
            "tryshot_signal",
            "mold_code",  # 범주형 강제
        ],
    },
}

# ==============================
# 2) 스키마 생성 : data1.csv에서 자동 범위/선택지 추출
# ==============================
def build_schema_from_csv(csv_path: str | Path,
                          max_cat_choices: int = 30,
                          mold_topk: int = 5) -> Dict[str, Any]:
    df = pd.read_csv(csv_path)
    if "passorfail" in df.columns:
        df = df.drop(columns=["passorfail"])

    schema = {"num_specs": [], "cat_specs": []}
    FORCE_CAT = {"mold_code"}
    LOW_CARD_K = 5  # 숫자라도 고유값<=5면 범주 처리

    # 각 그룹에서 언급한 컬럼만 대상으로(불필요한 컬럼 제외 목적)
    allowed_cols: List[str] = sum([v["columns"] for v in PROCESS_GROUPS.values()], [])
    cols = [c for c in df.columns if c in set(allowed_cols)]

    for col in cols:
        s = df[col]
        is_force_cat = col in FORCE_CAT
        nunq = s.nunique(dropna=True)
        is_low_card_num = (pd.api.types.is_numeric_dtype(s) and nunq <= LOW_CARD_K)

        # --- 범주형 ---
        if is_force_cat or (not pd.api.types.is_numeric_dtype(s)) or is_low_card_num:
            vals = (
                s.astype(str).fillna("NaN").replace({"nan": "NaN"})
                .value_counts(dropna=False).index.tolist()
            )
            if col == "mold_code":
                choices = vals[:mold_topk]
                if "Other" not in choices:
                    choices += ["Other"]
            else:
                choices = vals[:max_cat_choices]

            if choices:
                schema["cat_specs"].append({
                    "name": col,
                    "choices": [str(x) for x in choices],
                    "default": str(choices[0]),
                })
            continue

        # --- 숫자형(슬라이더) ---
        s_num = pd.to_numeric(s, errors="coerce")
        if s_num.dropna().empty:
            continue
        p1, p99 = float(s_num.quantile(0.01)), float(s_num.quantile(0.99))
        lo, hi = (p1, p99) if p1 < p99 else (p99, p1)
        if not np.isfinite(lo) or not np.isfinite(hi) or lo == hi:
            lo, hi = float(s_num.min()), float(s_num.max())
        mid = float(s_num.median())
        step = 1.0 if np.allclose(s_num.dropna(), s_num.dropna().round()) else 0.1

        schema["num_specs"].append({
            "name": col,
            "min": lo, "max": hi, "step": step,
            "default": float(np.clip(mid, lo, hi)),
        })

    # 보기 좋게 정렬(주요 범주형이 위로)
    schema["cat_specs"].sort(
        key=lambda x: (x["name"] != "working", x["name"] != "mold_code", x["name"])
    )
    return schema

# ==============================
# 3) 개별 입력 위젯 생성
# ==============================
def _num_slider(spec: Dict[str, Any]):
    return ui.input_slider(
        spec["name"], spec["name"],
        min=float(spec["min"]), max=float(spec["max"]),
        value=float(spec["default"]), step=float(spec["step"])
    )

def _cat_select(spec: Dict[str, Any]):
    return ui.input_selectize(
        spec["name"], spec["name"],
        choices=[str(x) for x in spec["choices"]],
        selected=str(spec["default"])
    )

# 스키마에서 컬럼명으로 spec을 찾는 헬퍼
def _find_num_spec(schema: Dict[str, Any], name: str):
    for s in schema.get("num_specs", []):
        if s["name"] == name:
            return s
    return None

def _find_cat_spec(schema: Dict[str, Any], name: str):
    for s in schema.get("cat_specs", []):
        if s["name"] == name:
            return s
    return None

# ==============================
# 4) 그룹형 UI(아코디언 + ON/OFF)
# ==============================
def slider_page_ui(schema: Dict[str, Any]):
    def section_for_group(gkey: str):
        ginfo = PROCESS_GROUPS[gkey]
        title = ginfo["title"]
        toggle_id = ginfo["toggle_id"]
        cols = ginfo["columns"]

        # 이 그룹에서 실제 data1.csv에 존재하는 컬럼만 추려서 위젯 생성
        widgets = []
        for c in cols:
            ns = _find_num_spec(schema, c)
            if ns is not None:
                widgets.append(_num_slider(ns))
                continue
            cs = _find_cat_spec(schema, c)
            if cs is not None:
                widgets.append(_cat_select(cs))
                continue
            # 스키마에 없으면 해당 컬럼은 생성하지 않음(자동 스킵)

        if not widgets:
            body = ui.p("(이 그룹에 생성할 입력이 없습니다. CSV의 컬럼명이 정확한지 확인하세요.)")
        else:
            # 2열로 배치
            half = (len(widgets) + 1) // 2
            body = ui.row(
                ui.column(6, *widgets[:half]),
                ui.column(6, *widgets[half:]),
            )

        # 아코디언 패널 + 상단 토글 + 토글에 따른 표시
        return ui.accordion_panel(
            title,
            ui.input_switch(toggle_id, "ON/OFF", value=True),
            ui.panel_conditional(
                f"input.{toggle_id}",
                body
            ),
        )

    # 모든 그룹 패널 생성
    panels = [section_for_group(k) for k in PROCESS_GROUPS.keys()]

    return ui.page_fluid(
        ui.h3("주조 공정 변수 입력 (그룹별 ON/OFF)"),
        ui.accordion(*panels, multiple=True, open=[p for p in range(len(panels))]),

        ui.hr(),
        ui.input_action_button("btn_predict", "현재 입력값 예측", class_="btn-primary"),
        ui.br(), ui.br(),
        ui.h5("단일 예측 결과 (모델 predict() 사용)"),
        ui.output_text_verbatim("pred_summary"),
    )
