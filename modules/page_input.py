from shiny import ui, render, reactive
import pandas as pd
from typing import Dict, Any

from shared import (
    feature_name_map, feature_name_map_kor,
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
y_test_state = reactive.Value(None)
pred_state = reactive.Value(None)   # ✅ 예측 결과 저장


# ======================
# 카드 UI 컴포넌트
# ======================
def process_card_with_inputs(title: str, img: str, sliders: list, cid: str):
    return ui.card(
        ui.card_header(f"{title}"),
        ui.accordion(
            ui.accordion_panel("변수 입력", *sliders),
            id=f"{cid}_panel",
            open=False  # ✅ 1) 초기에 닫힌 상태
        ),
        ui.img(
            src=img,
            style="width:100%; height:auto; object-fit:contain; margin-bottom:10px;"
        ),
        ui.card(
            ui.output_ui(f"{cid}_warn_msg"),
            class_="mb-3",
            style="min-height:200px; max-height:300px; overflow:auto;"
        ),
        class_="mb-4",
        style="min-width:250px; min-height:500px;"
    )


# ======================
# Layout
# ======================
def inputs_layout(schema: Dict[str, Any]):
    custom_style = ui.tags.style("""
            /* 전체 카드 공통 */
            .card {
                border-radius: 10px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                transition: transform 0.2s, box-shadow 0.2s;
            }
            .card:hover {
                transform: translateY(-4px);
                box-shadow: 0 8px 20px rgba(0,0,0,0.2);
            }

            /* 카드 헤더 - 메탈 블루 톤 */
            .card-header {
                background-color: #2b3e50;
                color: #f8f9fa;
                font-weight: 600;
                font-size: 1.1rem;  /* ✅ 4) 헤더 글자 크기 증가 */
                border-bottom: 2px solid #1c2833;
            }

            /* 아코디언 버튼 */
            .accordion-button {
                background-color: #f1f3f5;
                color: #212529;
            }
            .accordion-button:not(.collapsed) {
                background-color: #dee2e6;
                color: #2b3e50;
                font-weight: 600;
            }

            /* 액션 버튼 (예측 실행) */
            .btn-primary {
                background-color: #0d6efd;  /* ✅ 1) 주황색 → 파란색 */
                border-color: #0d6efd;
                font-weight: 600;
                border-radius: 8px;
                padding: 8px 16px;
            }
            .btn-primary:hover {
                background-color: #0b5ed7;  /* ✅ 1) hover 색상도 변경 */
                border-color: #0b5ed7;
                transform: scale(1.05);
            }
        """)
    return ui.page_fluid(
        custom_style,
        ui.h3("주조 공정 입력"),

        # 전체 예측 결과 카드
        ui.card(
            ui.card_header("전체 예측 결과"),
            ui.output_ui("pred_result_card"),
            ui.input_action_button("btn_predict", "예측 실행", class_="btn btn-primary"),
            class_="mb-3",
            style="min-height:200px; min-width:250px;"
        ),

        ui.hr(),

        # 공정별 입력 카드들
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
            process_card_with_inputs(
                "기타) 전체 과정 관여 변수", "overall.png",
                [
                    ui.input_select("mold_code", "금형 코드", ["8412", "8573", "8600", "8722", "8917"]),
                    ui.input_select("working", "작업 여부", ["가동", "정지"]),
                    ui.input_numeric("count", "생산 횟수", value=0),
                    ui.input_numeric("facility_operation_cycleTime", "설비 가동 사이클타임", value=120),
                    ui.input_numeric("production_cycletime", "생산 사이클타임", value=150),
                    ui.input_checkbox("tryshot_check", "트라이샷 여부", value=False)
                ], "overall"
            ),
            fill=True
        ),

        ui.hr(),
        ui.card(
            ui.card_header("SHAP 시각화"),
            ui.output_plot("shap_force_plot"),
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

    # ✅ 2) 예측 실행 시 모든 아코디언 패널 닫기
    @reactive.effect
    @reactive.event(input.btn_predict)
    def close_accordions():
        for panel_id in ["g1_panel", "g2_panel", "g3_panel", "g4_panel", "overall_panel"]:
            ui.update_accordion(panel_id, show=False)

    # -------- 결과 카드 --------
    @output
    @render.ui
    def pred_result_card():
        # ✅ 3) 초기 상태: 기본 메시지 표시
        if input.btn_predict() == 0:
            return ui.div(
                "🔍 변수를 입력하고 '예측 실행' 버튼을 눌러주세요",
                class_="p-3 text-center text-white",
                style="background-color:#6c757d;border-radius:12px;font-weight:600;"
            )
        
        # 예측 실행
        pred, proba = do_predict(input, shap_values_state, X_input_state, rf_models, rf_explainers)
        pred_state.set(pred)

        if pred == -1:
            return ui.div(
                "⚠️ 해당 mold_code에 대한 모델이 없습니다.",
                class_="p-3 text-center text-white",
                style="background-color:#6c757d;border-radius:12px;font-weight:700;"
            )
        elif pred == 0:
            return ui.div(
                f"✅ PASS / 불량 확률: {proba:.2%}",
                class_="p-3 text-center text-white",
                style="background-color:#0d6efd;border-radius:12px;font-weight:700;"
            )
        else:
            return ui.div(
                f"❌ FAIL / 불량 확률: {proba:.2%}",
                class_="p-3 text-center text-white",
                style="background-color:#dc3545;border-radius:12px;font-weight:700;"
            )

    # -------- 공정별 경고 UI (초기 상태 추가) --------
    @output
    @render.ui
    def g1_warn_msg():
        # ✅ 3) 초기 상태: 기본 메시지
        if input.btn_predict() == 0:
            return ui.card_body(
                ui.p("예측을 실행하면 분석 결과가 표시됩니다"),
                class_="text-center text-white",
                style="background-color:#adb5bd; border-radius:6px; font-weight:600; padding:2rem;"
            )
        
        return shap_based_warning(
            "molten", 
            shap_values_state, 
            X_input_state, 
            feature_name_map_kor,
            pred_state
        )

    @output
    @render.ui
    def g2_warn_msg():
        if input.btn_predict() == 0:
            return ui.card_body(
                ui.p("예측을 실행하면 분석 결과가 표시됩니다"),
                class_="text-center text-white",
                style="background-color:#adb5bd; border-radius:6px; font-weight:600; padding:2rem;"
            )
        
        return shap_based_warning(
            "slurry", 
            shap_values_state, 
            X_input_state, 
            feature_name_map_kor,
            pred_state
        )

    @output
    @render.ui
    def g3_warn_msg():
        if input.btn_predict() == 0:
            return ui.card_body(
                ui.p("예측을 실행하면 분석 결과가 표시됩니다"),
                class_="text-center text-white",
                style="background-color:#adb5bd; border-radius:6px; font-weight:600; padding:2rem;"
            )
        
        return shap_based_warning(
            "injection", 
            shap_values_state, 
            X_input_state, 
            feature_name_map_kor,
            pred_state
        )

    @output
    @render.ui
    def g4_warn_msg():
        if input.btn_predict() == 0:
            return ui.card_body(
                ui.p("예측을 실행하면 분석 결과가 표시됩니다"),
                class_="text-center text-white",
                style="background-color:#adb5bd; border-radius:6px; font-weight:600; padding:2rem;"
            )
        
        return shap_based_warning(
            "solidify", 
            shap_values_state, 
            X_input_state, 
            feature_name_map_kor,
            pred_state
        )

    @output
    @render.ui
    def overall_warn_msg():
        if input.btn_predict() == 0:
            return ui.card_body(
                ui.p("예측을 실행하면 분석 결과가 표시됩니다"),
                class_="text-center text-white",
                style="background-color:#adb5bd; border-radius:6px; font-weight:600; padding:2rem;"
            )
        
        return shap_based_warning(
            "overall", 
            shap_values_state, 
            X_input_state, 
            feature_name_map_kor,
            pred_state
        )