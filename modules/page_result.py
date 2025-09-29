from shiny import ui, render, reactive
import pandas as pd
from pathlib import Path
from shared import model

def page_result_server(input, output, session):

    @reactive.event(input.btn_predict)
    def do_predict():
        # 입력값 모으기 (UI 이름 → 학습 컬럼명 매핑)
        features = {
            "molten_temp": input.molten_temp(),
            "molten_volume": input.molten_volume(),
            "sleeve_temperature": input.sleeve_temperature(),
            "EMS_operation_time": input.EMS_operation_time(),
            "cast_pressure": input.cast_pressure(),
            "biscuit_thickness": input.biscuit_thickness(),  # UI에 없으니 임시 기본값 (추후 추가 가능)
            "low_section_speed": input.low_section_speed(),
            "high_section_speed": input.high_section_speed(),
            "physical_strength": input.physical_strength(),
            "upper_mold_temp1": input.upper_mold_temp1(),
            "upper_mold_temp2": input.upper_mold_temp2(),
            "lower_mold_temp1": input.lower_mold_temp1(),
            "lower_mold_temp2": input.lower_mold_temp2(),
            "Coolant_temperature": input.coolant_temp(),
            "facility_operation_cycleTime": 120,  # 기본값
            "production_cycletime": 150,          # 기본값
            "count": input.count(),
            "working": input.working(),
            "mold_code": input.mold_code()
        }

        # DataFrame으로 변환
        X = pd.DataFrame([features])
        pred = model.predict(X)[0]
        print(pred)
        return pred

    # @output
    # @render.ui
    # def pred_result_card():
    #     pred = do_predict()
    #     if pred == 1:  # 예: 불량
    #         return ui.div(
    #             "❌ 불량 발생 가능성이 높습니다!",
    #             style="color: white; background-color: red; padding:10px; border-radius:8px; font-weight:bold;"
    #         )
    #     else:  # 양품
    #         return ui.div(
    #             "✅ 양품으로 예측되었습니다!",
    #             style="color: white; background-color: green; padding:10px; border-radius:8px; font-weight:bold;"
    #         )
            
    @output
    @render.ui
    def pred_result_card():
        # 버튼 클릭 횟수 (처음엔 0)
        if input.btn_predict() == 0:
            return ui.div(
                ui.p("실행 버튼을 눌러주세요", class_="mb-0"),
                class_="p-3 text-center text-dark",
                style="background-color:#f8f9fa;border-radius:12px;font-weight:700;"
            )

        # 버튼이 눌렸다면 → 예측 실행
        result = do_predict()
        if result == 0:
            return ui.div(
                ui.p("PASS", class_="mb-0"),
                class_="p-3 text-center text-white",
                style="background-color:#0d6efd;border-radius:12px;font-weight:700;"
            )
        else:
            return ui.div(
                ui.p("FAIL", class_="mb-0"),
                class_="p-3 text-center text-white",
                style="background-color:#dc3545;border-radius:12px;font-weight:700;"
            )

    @output
    @render.text
    @reactive.event(input.btn_predict)
    def pred_summary():
        return f"예측 결과: {do_predict()}"

    # ===== 공정별 경고 카드들 (기존 그대로) =====
    def show_modal(title, content):
        return ui.modal(ui.h4(title), ui.p(content), easy_close=True,
                        footer=ui.modal_button("닫기"))

    @output
    @render.ui
    @reactive.event(input.btn_predict)
    def warn_molten():
        if input.sleeve_temp() < 450:
            color, msg = "bg-warning", "⚠️ 용탕 온도 낮음 → 불량 위험 ↑"
        else:
            color, msg = "bg-success", "✅ 이상 없음"
        return ui.card(ui.h5("① 용탕 준비"), ui.p(msg),
                       ui.input_action_button("btn_molten", "상세보기", class_="btn-sm btn-light"),
                       class_=color)

    @output
    @render.ui
    @reactive.event(input.btn_predict)
    def warn_slurry():
        if input.sleeve_temp() < 420:
            color, msg = "bg-danger", "❌ EMS 가동 시간 부족 → 슬러리 불안정"
        else:
            color, msg = "bg-success", "✅ 이상 없음"
        return ui.card(ui.h5("② 반고체 슬러리 제조"), ui.p(msg),
                       ui.input_action_button("btn_slurry", "상세보기", class_="btn-sm btn-light"),
                       class_=color)

    @output
    @render.ui
    @reactive.event(input.btn_predict)
    def warn_injection():
        if input.cast_pressure() < 70:
            color, msg = "bg-warning", "⚠️ 주조 압력 부족 → 충전 불완전"
        else:
            color, msg = "bg-success", "✅ 이상 없음"
        return ui.card(ui.h5("③ 사출 & 금형 충전"), ui.p(msg),
                       ui.input_action_button("btn_injection", "상세보기", class_="btn-sm btn-light"),
                       class_=color)

    @output
    @render.ui
    @reactive.event(input.btn_predict)
    def warn_solidify():
        if input.coolant_temp() > 35:
            color, msg = "bg-warning", "⚠️ 냉각수 온도 높음 → 응고 지연"
        else:
            color, msg = "bg-success", "✅ 이상 없음"
        return ui.card(ui.h5("④ 응고"), ui.p(msg),
                       ui.input_action_button("btn_solidify", "상세보기", class_="btn-sm btn-light"),
                       class_=color)