# page_input.py
from shiny import ui, render, reactive
import pandas as pd
from typing import Dict, Any

from shared import (
    feature_name_map,
    rf_models, rf_explainers  # ✅ RandomForest 모델/설명자
)
from viz.shap_plots import register_shap_plots
from modules.service_predict import do_predict
from modules.service_warnings import shap_based_warning


# ======================
# 상태 저장용 (세션 전역)
# ======================
shap_values_state = reactive.Value(None)
X_input_state = reactive.Value(None)
y_test_state = reactive.Value(None)  # permutation importance 용


# ======================
# 카드 UI 컴포넌트
# ======================
def overall_process_card(title: str = "전체 과정 관여 변수", cid: str = "overall"):
    sliders = [
        ui.input_select("mold_code", "금형 코드", [8412, 8573, 8600, 8722, 8917]),
        ui.input_select("working", "작업 여부", ["가동", "정지"]),
        ui.input_numeric("count", "생산 횟수", value=0),
        ui.input_numeric("facility_operation_cycleTime", "설비 가동 사이클타임", value=120),
        ui.input_numeric("production_cycletime", "생산 사이클타임", value=150),
        ui.input_checkbox("tryshot_check", "트라이샷 여부", value=False)
    ]

    return ui.card(
        ui.card(
            ui.card_header(title),
            ui.output_ui(f"{cid}_warn_msg"),
            class_="mb-3",
            style="min-height:150px; width:100%;"
        ),
        ui.accordion(
            ui.accordion_panel("변수 입력", *sliders),
            id=f"{cid}_panel", open=[]
        ),
        class_="mb-4",
        style="min-width:250px;"
    )


def process_card_with_inputs(title: str, img: str, sliders: list, cid: str):
    return ui.card(
        ui.card_header(f"{title}"),
        ui.accordion(
            ui.accordion_panel("변수 입력", *sliders),
            id=f"{cid}_panel", open=[]
        ),
        ui.img(
            src=img,
            style="width:100%; height:auto; object-fit:contain; margin-bottom:10px;"
        ),
        ui.card(
            ui.output_ui(f"{cid}_warn_msg"),
            class_="mb-3",
            style="min-height:250px; max-height:400px; width:100%; overflow:auto;"
        ),
        class_="mb-4",
        style="min-width:250px;"
    )


# ======================
# Layout
# ======================
def inputs_layout(schema: Dict[str, Any]):
    return ui.page_fluid(
        ui.h3("주조 공정 입력"),

        ui.card(
            ui.card_header("전체 예측 결과"),
            ui.output_ui("pred_result_card"),
            ui.input_action_button("btn_predict", "예측 실행", class_="btn btn-primary"),
            class_="mb-3",
            style="min-height:200px; min-width:250px;"
        ),

        ui.hr(),
        ui.layout_columns(
            process_card_with_inputs(
                "1) 용탕 준비 및 가열", "molten2.png",
                [
                    ui.input_slider("molten_temp", "용탕 온도 (℃)", 600, 800, 700),
                    ui.input_slider("molten_volume", "용탕 부피", -1, 600, 100)
                ], "g1"
            ),
            process_card_with_inputs(
                "2) 반고체 슬러리 제조", "sleeve2.png",
                [
                    ui.input_slider("sleeve_temperature", "슬리브 온도 (℃)", 0, 1000, 500),
                    ui.input_slider("EMS_operation_time", "EMS 작동시간 (s)", 0, 25, 23)
                ], "g2"
            ),
            process_card_with_inputs(
                "3) 사출 & 금형 충전", "mold2.png",
                [
                    ui.input_slider("cast_pressure", "주조 압력 (bar)", 50, 400, 300),
                    ui.input_slider("low_section_speed", "저속 구간 속도", 0, 200, 100, step=1),
                    ui.input_slider("high_section_speed", "고속 구간 속도", 0, 400, 100, step=1),
                    ui.input_slider("physical_strength", "형체력", 600, 800, 700),
                    ui.input_slider("biscuit_thickness", "비스킷 두께", 1, 50, 25),
                ], "g3"
            ),
            process_card_with_inputs(
                "4) 응고", "cooling2.png",
                [
                    ui.input_slider("upper_mold_temp1", "상형 온도1 (℃)", 0, 400, 160),
                    ui.input_slider("upper_mold_temp2", "상형 온도2 (℃)", 0, 400, 150),
                    ui.input_slider("lower_mold_temp1", "하형 온도1 (℃)", 0, 400, 290),
                    ui.input_slider("lower_mold_temp2", "하형 온도2 (℃)", 0, 400, 180),
                    ui.input_slider("coolant_temp", "냉각수 온도 (℃)", 0, 50, 30)
                ], "g4"
            ),
            overall_process_card(),
            fill=True
        ),

        ui.hr(),
        ui.card(
            ui.card_header("SHAP Force Plot (개별 샘플)"),
            ui.output_plot("shap_force_plot")
        ),
    )


# ======================
# Server
# ======================
def page_input_server(input, output, session):
    # -------- SHAP + Permutation Importance 등록 --------
    register_shap_plots(
        output,
        shap_values_state,
        X_input_state,
        y_test_state,
        rf_models,
        rf_explainers,
        input
    )

    # -------- 결과 카드 --------
    @output
    @render.ui
    def pred_result_card():
        if input.btn_predict() == 0:   # 버튼 안 눌렀을 때 안내
            return ui.div("실행 버튼을 눌러주세요", class_="p-3 text-center")

        result = do_predict(input, shap_values_state, X_input_state, rf_models, rf_explainers)
        if result == -1:
            return ui.div("해당 mold_code에 대한 모델이 없습니다.",
                          class_="p-3 text-center text-white",
                          style="background-color:#6c757d;border-radius:12px;font-weight:700;")
        elif result == 0:
            return ui.div("✅ PASS", class_="p-3 text-center text-white",
                          style="background-color:#0d6efd;border-radius:12px;font-weight:700;")
        else:
            return ui.div("❌ FAIL", class_="p-3 text-center text-white",
                          style="background-color:#dc3545;border-radius:12px;font-weight:700;")

    @output
    @render.text
    @reactive.event(input.btn_predict)   # 버튼 눌렀을 때만 동작
    def pred_summary():
        return f"예측 결과: {do_predict(input, shap_values_state, X_input_state, rf_models, rf_explainers)}"

    # -------- 공정별 경고 UI --------
    @output
    @render.ui
    @reactive.event(input.btn_predict)
    def g1_warn_msg(): return shap_based_warning("molten", shap_values_state, X_input_state, feature_name_map)

    @output
    @render.ui
    @reactive.event(input.btn_predict)
    def g2_warn_msg(): return shap_based_warning("slurry", shap_values_state, X_input_state, feature_name_map)

    @output
    @render.ui
    @reactive.event(input.btn_predict)
    def g3_warn_msg(): return shap_based_warning("injection", shap_values_state, X_input_state, feature_name_map)

    @output
    @render.ui
    @reactive.event(input.btn_predict)
    def g4_warn_msg(): return shap_based_warning("solidify", shap_values_state, X_input_state, feature_name_map)

    @output
    @render.ui
    @reactive.event(input.btn_predict)
    def overall_warn_msg(): return shap_based_warning("overall", shap_values_state, X_input_state, feature_name_map)