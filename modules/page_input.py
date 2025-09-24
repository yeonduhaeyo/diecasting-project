# modules/page_input.py
from shiny import ui

def slider_page_ui():
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
