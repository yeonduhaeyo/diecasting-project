# modules/page_input.py
from shiny import ui
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List

# 공정 그룹(데이터 컬럼명과 정확히 일치해야 생성됨)
PROCESS_GROUPS: Dict[str, Dict[str, Any]] = {
    "g1": {"title": "1) 용탕 준비 및 가열",
           "columns": ["molten_temp","molten_volume"]},
    "g2": {"title": "2) 반고체화(전자교반) in sleeve",
           "columns": ["sleeve_temperature","EMS_operation_time"]},
    "g3": {"title": "3) mold에 주입",
           "columns": ["cast_pressure","biscuit_thickness",
                       "low_section_speed","high_section_speed","physical_strength"]},
    "g4": {"title": "4) 응고 및 냉각",
           "columns": ["upper_mold_temp1","upper_mold_temp2",
                       "lower_mold_temp1","lower_mold_temp2","Coolant_temperature"]},
    "g5": {"title": "[전체 과정 관여]",
           "columns": ["count","working","facility_operation_CycleTime",
                       "production_CycleTime","tryshot_signal","mold_code"]},
}

def build_schema_from_csv(csv_path: str | Path,
                          max_cat_choices: int = 30,
                          mold_topk: int = 5) -> Dict[str, Any]:
    df = pd.read_csv(csv_path)
    if "passorfail" in df.columns:
        df = df.drop(columns=["passorfail"])

    schema = {"num_specs": [], "cat_specs": []}
    FORCE_CAT = {"mold_code"}
    LOW_CARD_K = 5

    allowed_cols: List[str] = sum([v["columns"] for v in PROCESS_GROUPS.values()], [])
    cols = [c for c in df.columns if c in set(allowed_cols)]

    for col in cols:
        s = df[col]
        is_force_cat = col in FORCE_CAT
        nunq = s.nunique(dropna=True)
        is_low_card_num = (pd.api.types.is_numeric_dtype(s) and nunq <= LOW_CARD_K)

        # --- 범주형 ---
        if is_force_cat or (not pd.api.types.is_numeric_dtype(s)) or is_low_card_num:
            vals = (s.astype(str).fillna("NaN").replace({"nan":"NaN"})
                    .value_counts(dropna=False).index.tolist())
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

        # --- 숫자형 ---
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
            "name": col, "min": lo, "max": hi, "step": step,
            "default": float(np.clip(mid, lo, hi)),
        })

    # 보기 좋게 정렬
    schema["cat_specs"].sort(
        key=lambda x: (x["name"] != "working", x["name"] != "mold_code", x["name"])
def page_input_ui():
    return ui.page_fluid(
        ui.h3("주조 공정 변수 입력"),
        ui.row(
            ui.column(6, ui.input_slider("sleeve_temp",  "슬리브 온도 (℃)",        400, 600, 500)),
            ui.column(6, ui.input_slider("coolant_temp", "냉각수 온도 (℃)",      20,  40,  30)),
            ui.column(6, ui.input_slider("strength",     "형체력",                600, 800, 700)),
            ui.column(6, ui.input_slider("cast_pressure","주조 압력",              50,  120,  80)),
            ui.column(6, ui.input_slider("low_speed",    "저속 구간 속도",        0.1, 1.0, 0.5, step=0.05)),
            ui.column(6, ui.input_slider("high_speed",   "고속 구간 속도",        1.0, 5.0, 3.0, step=0.1)),
        ),
        ui.hr(),
        ui.input_action_button("btn_predict", "예측"),
        ui.br(),
        ui.output_text_verbatim("pred_result")
    )
    return schema

def _num_pair_vertical(spec: Dict[str, Any]):
    """슬라이더 바로 아래 숫자 입력(연동용)"""
    name = spec["name"]
    return ui.TagList(
        ui.input_slider(
            f"{name}__slider", name,
            min=float(spec["min"]), max=float(spec["max"]),
            value=float(spec["default"]), step=float(spec["step"])
        ),
        ui.input_numeric(
            f"{name}__num", "값(직접입력)",
            value=float(spec["default"]),
            min=float(spec["min"]), max=float(spec["max"]),
            step=float(spec["step"]),
        ),
        ui.hr()
    )

def _cat_select(spec: Dict[str, Any]):
    return ui.TagList(
        ui.input_selectize(
            spec["name"], spec["name"],
            choices=[str(x) for x in spec["choices"]],
            selected=str(spec["default"])
        ),
        ui.hr()
    )

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

def group_card(schema: Dict[str, Any], gkey: str):
    ginfo = PROCESS_GROUPS[gkey]
    cols = ginfo["columns"]

    widgets = []
    for c in cols:
        ns = _find_num_spec(schema, c)
        if ns is not None:
            widgets.append(_num_pair_vertical(ns)); continue
        cs = _find_cat_spec(schema, c)
        if cs is not None:
            widgets.append(_cat_select(cs)); continue

    body = (
        ui.p("(이 그룹에 생성할 입력이 없습니다. CSV 컬럼명을 확인하세요.)")
        if not widgets else ui.TagList(*widgets)
    )

    return ui.card(
        ui.card_header(ui.h6(ginfo["title"], class_="mb-0")),
        body,
        class_="h-100"
    )

def inputs_layout(schema: Dict[str, Any]):
    """상단 4개 그룹을 가로 4열 카드로, 전체 과정(g5) 카드는 하단에 배치"""
    row_cards = ui.row(
        ui.column(3, group_card(schema, "g1")),
        ui.column(3, group_card(schema, "g2")),
        ui.column(3, group_card(schema, "g3")),
        ui.column(3, group_card(schema, "g4")),
    )
    whole_process = ui.row(
        ui.column(12, group_card(schema, "g5"))
    )
    return ui.TagList(row_cards, ui.hr(), whole_process)
