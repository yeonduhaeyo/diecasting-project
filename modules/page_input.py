from shiny import ui, render, reactive
import pandas as pd
from typing import Dict, Any

from shared import (
    feature_name_map, feature_name_map_kor,
    rf_models, rf_explainers
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
pred_state = reactive.Value(None)


# ======================
# 카드 UI 컴포넌트
# ======================
def process_card_with_inputs(title: str, img: str, sliders: list, cid: str):
    return ui.card(
        ui.card_header(f"{title}"),
        ui.accordion(
            ui.accordion_panel("변수 입력", *sliders),
            id=f"{cid}_panel",
            open=False
        ),
        ui.div(
            ui.img(
                src=img,
                style="width:150px; height:auto; object-fit:contain; margin-bottom:10px;"
            ),
            style="text-align:center;"
        ),
        ui.div(
            ui.output_ui(f"{cid}_warn_msg_default"),
            ui.output_ui(f"{cid}_warn_msg_pred"),
            class_="p-0 m-0",
            style="max-height:300px; overflow:auto;"
        ),
        class_="mb-2 p-0",  
        style="min-width:100px;"
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
                font-size: 1.1rem;
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
                background-color: #0d6efd;
                border-color: #0d6efd;
                font-weight: 600;
                border-radius: 8px;
                padding: 8px 16px;
            }
            .btn-primary:hover {
                background-color: #0b5ed7;
                border-color: #0b5ed7;
                transform: scale(1.05);
            }
            
            @font-face {
                font-family: 'Noto Sans KR';
                src: url('/fonts/NotoSansKR-Regular.ttf') format('truetype');
                font-weight: normal;
                font-style: normal;
            }
            body {
                font-family: 'Noto Sans KR', sans-serif;
            }
            .table, .card, .accordion, .btn {
                font-family: 'Noto Sans KR', sans-serif;
            }
            
        """)
    return ui.page_fluid(
        custom_style,
        ui.h3("주조 공정 입력"),
        
        # 입력 데이터 요약
        ui.card(
            ui.card_header("입력된 변수 값"),
            ui.output_ui("input_summary_table_default"),  # ✅ 초기 메시지
            ui.output_ui("input_summary_table"),           # ✅ 테이블
            class_="mb-1",
            style="min-width:250px;"
        ),

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

        # 전체 예측 결과 카드
        ui.card(
            ui.card_header("전체 예측 결과"),
            ui.output_ui("pred_result_card_default"),
            ui.output_ui("pred_result_card"),
            ui.input_action_button("btn_predict", "예측 실행", class_="btn btn-primary"),
            class_="mb-3",
            style="min-height:200px; min-width:250px;"
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
    register_shap_plots(
        output,
        shap_values_state,
        X_input_state,
        y_test_state,
        rf_models,
        rf_explainers,
        input
    )
    
    # ✅ 초기 상태: 안내 텍스트
    @output
    @render.ui
    def input_summary_table_default():
        if input.btn_predict() == 0:
            return ui.div(
                "📝 변수를 입력하고 예측 실행 버튼을 누르면 입력값이 표시됩니다",
                class_="text-center p-3",
                style="color:#6c757d; font-size:1rem;"
            )
    
    # ✅ 버튼 클릭 후: 테이블
    @output
    @render.ui
    @reactive.event(input.btn_predict)
    def input_summary_table():
        data = {
            "용탕 온도": input.molten_temp(),
            "용탕 부피": input.molten_volume(),
            "슬리브 온도": input.sleeve_temperature(),
            "EMS 작동시간": input.EMS_operation_time(),
            "주조 압력": input.cast_pressure(),
            "저속 구간 속도": input.low_section_speed(),
            "고속 구간 속도": input.high_section_speed(),
            "형체력": input.physical_strength(),
            "비스킷 두께": input.biscuit_thickness(),
            "상형 온도1": input.upper_mold_temp1(),
            "상형 온도2": input.upper_mold_temp2(),
            "하형 온도1": input.lower_mold_temp1(),
            "하형 온도2": input.lower_mold_temp2(),
            "냉각수 온도": input.coolant_temp(),
            "금형 코드": input.mold_code(),
            "작업 여부": input.working(),
            "생산 횟수": input.count(),
            "설비 가동 사이클타임": input.facility_operation_cycleTime(),
            "생산 사이클타임": input.production_cycletime(),
            "트라이샷 여부": "예" if input.tryshot_check() else "아니오"
        }
        
        df = pd.DataFrame([data])
        
        # ✅ 스타일 적용된 HTML 테이블
        html_table = df.to_html(
            index=False, 
            classes="table table-bordered table-sm table-hover", 
            border=0
        )
        
        styled_html = f"""
        <div style="overflow-x:auto; white-space:nowrap;">
            <style>
                .table-sm th, .table-sm td {{
                    padding: 0.5rem;
                    font-size: 0.9rem;
                    text-align: center;
                }}
                .table-sm th {{
                    background-color: #f8f9fa;
                    font-weight: 600;
                }}
            </style>
            {html_table}
        </div>
        """
        
        return ui.HTML(styled_html)

    @reactive.effect
    @reactive.event(input.btn_predict)
    def close_accordions():
        for panel_id in ["g1_panel", "g2_panel", "g3_panel", "g4_panel", "overall_panel"]:
            ui.update_accordion(panel_id, show=False)

    @output
    @render.ui
    def pred_result_card_default():
        if input.btn_predict() == 0:
            return ui.div(
                "🔍 변수를 입력하고 '예측 실행' 버튼을 눌러주세요",
                class_="p-3 text-center text-white",
                style="background-color:#6c757d;border-radius:12px;font-weight:600;"
            )

    @output
    @render.ui
    @reactive.event(input.btn_predict)
    def pred_result_card():
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

    def warn_msg_factory(process_name, cid, process_label):
        @output(id=f"{cid}_warn_msg_default")
        @render.ui
        def _default():
            if input.btn_predict() == 0:
                return ui.card_body(
                    ui.p("예측을 실행하면", ui.br(), "분석 결과가 표시됩니다"),
                    class_="text-center text-white p-2 m-2",
                    style="background-color:#adb5bd; border-radius:6px; font-weight:600;"
                )

        @output(id=f"{cid}_warn_msg_pred")
        @render.ui
        @reactive.event(input.btn_predict)
        def _pred():
            result = shap_based_warning(
                process_name,
                shap_values_state,
                X_input_state,
                feature_name_map_kor,
                pred_state
            )
            return ui.div(
                result["header"],
                ui.input_action_button(
                    f"{cid}_detail_btn",
                    "상세 결과 보기",
                    class_="btn btn-sm btn-secondary w-100 mt-2 mb-0"
                ),
                class_="p-0 mt-2"
            )

        @reactive.effect
        @reactive.event(input[f"{cid}_detail_btn"])
        def show_modal():
            result = shap_based_warning(
                process_name,
                shap_values_state,
                X_input_state,
                feature_name_map_kor,
                pred_state
            )
            ui.modal_show(
                ui.modal(
                    ui.div(
                        result["details"],
                        style="font-size:2rem;"
                    ),
                    title=f"{process_label} 상세 결과",
                    easy_close=True,
                    footer=ui.input_action_button(
                        f"{cid}_close_modal",
                        "닫기",
                        class_="btn btn-secondary"
                    )
                )
            )
            
        @reactive.effect
        @reactive.event(input[f"{cid}_close_modal"])
        def close_modal():
            ui.modal_remove()

    warn_msg_factory("molten", "g1", "용탕 준비 및 가열")
    warn_msg_factory("slurry", "g2", "반고체 슬러리 제조")
    warn_msg_factory("injection", "g3", "사출 & 금형 충전")
    warn_msg_factory("solidify", "g4", "응고")
    warn_msg_factory("overall", "overall", "전체 과정")