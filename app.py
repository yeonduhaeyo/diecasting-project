from shiny import App, ui, render, reactive
from modules import page_input, page_result, page_process
from pathlib import Path

# www 경로를 직접 지정
# 이부분 나중에 setting으로 뺄 것
www_dir = Path(__file__).parent / "www"

app_ui = ui.page_navbar(
    ui.nav_panel("공정 입력", page_input.page_input_ui()),
    ui.nav_panel("예측 결과", page_result.page_result_ui()),
    ui.nav_panel("공정 설명", page_process.page_process_ui()),  # 새 페이지 추가
    title="주조 공정 품질 예측",
)

def server(input, output, session):

    @output
    @render.text
    @reactive.event(input.btn_predict)   # 버튼 클릭 시 실행
    def pred_result():
        lines = [
            f"슬리브 온도(℃): {input.sleeve_temp()}",
            f"냉각수 온도(℃): {input.coolant_temp()}",
            f"형체력: {input.strength()}",
            f"주조 압력: {input.cast_pressure()}",
            f"저속 구간 속도: {input.low_speed()}",
            f"고속 구간 속도: {input.high_speed()}",
        ]
        return "입력값 요약\n" + "\n".join(lines)
    
    # page_input.page_server(input, output, session)
    page_result.page_result_server(input, output, session)
    page_process.page_process_server(input, output, session)

app = App(app_ui, server, static_assets=www_dir)
