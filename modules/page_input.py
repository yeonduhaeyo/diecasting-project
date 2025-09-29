from shiny import ui, reactive
from typing import Dict, Any


# -------------------------------
# 전체 과정 관여 변수 (맨 위 한 줄)
# -------------------------------
def overall_panel(schema: Dict[str, Any]):
    return ui.accordion(
        ui.accordion_panel(
            "전체 과정 관여 변수",
            ui.row(
                ui.column(3, ui.input_select("mold_code", "금형 코드", [8412, 8573, 8600, 8722, 8971])),
                ui.column(3, ui.input_select("working", "작업 여부", ["가동", "정지"])),
                ui.column(3, ui.input_numeric("count", "생산 횟수", value=0)),
                ui.column(3, ui.input_checkbox("tryshot_check", "트라이샷 여부", value=False))
            )
        ),
        id="overall_panel", open=[]
    )


# -------------------------------
# 공정별 카드 (이미지 + 결과카드 + 입력 accordion)
# -------------------------------
def process_card_with_inputs(title: str, img: str, sliders: list, cid: str):
    return ui.card(
        # 공정 이미지
        ui.img(
            src=img,
            style="width:100%; height:auto; object-fit:contain; margin-bottom:10px;"
            ),

        # 공정 결과 카드 (고정 크기)
        ui.card(
            ui.card_header(f"{title}"),
            ui.div(
                ui.input_action_button(
                    f"{cid}_explain_btn",
                    "공정 설명 보기",
                    class_="btn btn-outline-primary btn-sm",  # 작고 깔끔한 버튼
                    style="width:80%; border-radius:6px; font-weight:600;"
                    ),
                class_="text-center"  # 버튼을 카드 중앙에 정렬
                ),
            class_="mb-3",
            style="min-height:150px; max-height:150px; width:100%;"
            ),
        
        

        # 변수 입력 accordion
        ui.accordion(
            ui.accordion_panel("변수 입력", *sliders),
            id=f"{cid}_panel", open=[]
        ),

        class_="mb-4",
        style="min-width:250px;"
    )


# -------------------------------
# 메인 입력 레이아웃
# -------------------------------
def inputs_layout(schema: Dict[str, Any]):
    return ui.page_fluid(
        ui.h3("주조 공정 입력"),

        overall_panel(schema),

        ui.hr(),

        # 공정 카드들 + 전체 결과 카드
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

            # 전체 예측 결과 카드
            ui.card(
                ui.card_header("전체 예측 결과"),
                ui.output_ui("pred_result_card"),
                ui.input_action_button("btn_predict", "예측 실행", class_="btn btn-primary"),
                class_="mb-3",
                style="min-height:400px; min-width:250px;"
            ),

            fill=True
        )
    )


# -------------------------------
# 서버 (공정별 결과 업데이트 자리)
# -------------------------------
def page_input_server(input, output, session):

    @reactive.effect
    @reactive.event(input.g1_explain_btn)
    def _():
        ui.update_navs("main_nav", "공정 설명")    # 상위 탭 열기
        ui.update_navs("process_nav", "① 용탕 준비 및 가열")  # 하위 탭 열기

    @reactive.effect
    @reactive.event(input.g2_explain_btn)
    def _():
        ui.update_navs("main_nav", "공정 설명")
        ui.update_navs("process_nav", "② 반고체 슬러리 제조")

    @reactive.effect
    @reactive.event(input.g3_explain_btn)
    def _():
        ui.update_navs("main_nav", "공정 설명")
        ui.update_navs("process_nav", "③ 사출 & 금형 충전")

    @reactive.effect
    @reactive.event(input.g4_explain_btn)
    def _():
        ui.update_navs("main_nav", "공정 설명")
        ui.update_navs("process_nav", "④ 응고")
    # # ===== 모달 트리거 =====
    # @reactive.effect
    # @reactive.event(input.btn_molten)
    # def _():
    #     ui.modal_show(show_modal("① 용탕 준비", "용탕 온도, 부피, 가열로 상태가 주요 변수입니다."))

    # @reactive.effect
    # @reactive.event(input.btn_slurry)
    # def _():
    #     ui.modal_show(show_modal("② 반고체 슬러리 제조", "슬리브 온도와 EMS 가동 시간이 슬러리 안정성에 영향을 줍니다."))

    # @reactive.effect
    # @reactive.event(input.btn_injection)
    # def _():
    #     ui.modal_show(show_modal("③ 사출 & 금형 충전", "저속/고속 속도, 주입 압력, 비스킷 두께가 충전 안정성을 결정합니다."))

    # @reactive.effect
    # @reactive.event(input.btn_solidify)
    # def _():
    #     ui.modal_show(show_modal("④ 응고", "상/하 금형 온도와 냉각수 온도가 응고 속도와 품질에 영향을 줍니다."))
