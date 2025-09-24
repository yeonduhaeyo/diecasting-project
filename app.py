# app.py
from shiny import App, ui, render, reactive
from modules import page_input

app_ui = ui.page_navbar(
    ui.nav_panel("공정 입력", page_input.slider_page_ui()),
    title="주조 공정 품질 예측",
)

def server(input, output, session):

    @output
    @render.text
    @reactive.event(input.btn_predict)   # 버튼 클릭 시에만 실행
    def pred_result():
        # 슬라이더 값들만 읽어서 출력
        lines = [
            f"슬리브 온도(℃): {input.sleeve_temp()}",
            f"냉각수 온도(℃): {input.coolant_temp()}",
            f"형체력: {input.strength()}",
            f"주조 압력: {input.cast_pressure()}",
            f"저속 구간 속도: {input.low_speed()}",
            f"고속 구간 속도: {input.high_speed()}",
        ]
        return "입력값 요약\n" + "\n".join(lines)

app = App(app_ui, server)
