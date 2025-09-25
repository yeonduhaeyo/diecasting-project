from shiny import ui, render, reactive

def page_result_ui():
    return ui.page_fluid(
        ui.h3("예측 결과 및 공정별 경고"),
        ui.card(ui.output_text_verbatim("pred_summary")),
        ui.layout_columns(
            ui.output_ui("warn_molten"),
            ui.output_ui("warn_slurry"),
            ui.output_ui("warn_injection"),
            ui.output_ui("warn_solidify"),
            col_widths=[3, 3, 3, 3]
        )
    )


def page_result_server(input, output, session):
    # 샘플 예측 로직
    @reactive.event(input.btn_predict)
    def do_predict():
        score = (
            input.sleeve_temp() +
            input.coolant_temp() +
            input.strength() +
            input.cast_pressure()
        )
        return "합격" if score > 1000 else "불합격"

    @output
    @render.text
    @reactive.event(input.btn_predict)
    def pred_summary():
        return f"예측 결과: {do_predict()}"

    # -------- 모달 정의 --------
    def show_modal(title, content):
        return ui.modal(
            ui.h4(title),
            ui.p(content),
            easy_close=True,
            footer=ui.modal_button("닫기")
        )

    # -------- 각 공정 카드 (배경색 조건부 변경) --------
    @output
    @render.ui
    @reactive.event(input.btn_predict)
    def warn_molten():
        if input.sleeve_temp() < 450:
            color, msg = "bg-warning", "⚠️ 용탕 온도 낮음 → 불량 위험 ↑"
        else:
            color, msg = "bg-success", "✅ 이상 없음"
        return ui.card(
            ui.h5("① 용탕 준비"),
            ui.p(msg, style="font-size:14px;"),
            ui.input_action_button("btn_molten", "상세보기", class_="btn-sm btn-light"),
            class_=color
        )

    @output
    @render.ui
    @reactive.event(input.btn_predict)
    def warn_slurry():
        if input.sleeve_temp() < 420:
            color, msg = "bg-danger", "❌ EMS 가동 시간 부족 → 슬러리 불안정"
        else:
            color, msg = "bg-success", "✅ 이상 없음"
        return ui.card(
            ui.h5("② 반고체 슬러리 제조"),
            ui.p(msg, style="font-size:14px;"),
            ui.input_action_button("btn_slurry", "상세보기", class_="btn-sm btn-light"),
            class_=color
        )

    @output
    @render.ui
    @reactive.event(input.btn_predict)
    def warn_injection():
        if input.cast_pressure() < 70:
            color, msg = "bg-warning", "⚠️ 주조 압력 부족 → 충전 불완전"
        else:
            color, msg = "bg-success", "✅ 이상 없음"
        return ui.card(
            ui.h5("③ 사출 & 금형 충전"),
            ui.p(msg, style="font-size:14px;"),
            ui.input_action_button("btn_injection", "상세보기", class_="btn-sm btn-light"),
            class_=color
        )

    @output
    @render.ui
    @reactive.event(input.btn_predict)
    def warn_solidify():
        if input.coolant_temp() > 35:
            color, msg = "bg-warning", "⚠️ 냉각수 온도 높음 → 응고 지연"
        else:
            color, msg = "bg-success", "✅ 이상 없음"
        return ui.card(
            ui.h5("④ 응고"),
            ui.p(msg, style="font-size:14px;"),
            ui.input_action_button("btn_solidify", "상세보기", class_="btn-sm btn-light"),
            class_=color
        )

    # -------- 버튼 클릭 시 모달 띄우기 --------
    @reactive.effect
    @reactive.event(input.btn_molten)
    def _():
        ui.modal_show(show_modal("① 용탕 준비", "용탕 온도, 부피, 가열로 상태가 주요 변수입니다."))

    @reactive.effect
    @reactive.event(input.btn_slurry)
    def _():
        ui.modal_show(show_modal("② 반고체 슬러리 제조", "슬리브 온도와 EMS 가동 시간이 슬러리 안정성에 영향을 줍니다."))

    @reactive.effect
    @reactive.event(input.btn_injection)
    def _():
        ui.modal_show(show_modal("③ 사출 & 금형 충전", "저속/고속 속도, 주입 압력, 비스킷 두께가 충전 안정성을 결정합니다."))

    @reactive.effect
    @reactive.event(input.btn_solidify)
    def _():
        ui.modal_show(show_modal("④ 응고", "상/하 금형 온도와 냉각수 온도가 응고 속도와 품질에 영향을 줍니다."))
