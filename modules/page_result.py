from shiny import ui, render, reactive
import pandas as pd
from shared import models, explainers, feature_name_map
from viz.shap_plots import register_shap_plots

# 상태 저장용 (세션 전역 대체)
shap_values_state = reactive.Value(None)
X_input_state = reactive.Value(None)
y_test_state = reactive.Value(None)  # permutation importance용 y_test 필요


def page_result_server(input, output, session):
    # ===== SHAP + Permutation Importance 시각화 등록 =====
    register_shap_plots(
        output,
        shap_values_state,
        X_input_state,
        y_test_state,
        models,
        explainers,
        input
    )
    
    @reactive.event(input.btn_predict)
    def do_predict():
        """버튼 클릭 시 예측 + SHAP 계산"""
        features = {
            # 용탕 준비 및 가열
            "molten_temp": input.molten_temp(),
            "molten_volume": input.molten_volume(),

            # 반고체 슬러리 제조
            "sleeve_temperature": input.sleeve_temperature(),
            "EMS_operation_time": input.EMS_operation_time(),

            # 사출 & 금형 충전
            "cast_pressure": input.cast_pressure(),
            "biscuit_thickness": input.biscuit_thickness(),
            "low_section_speed": input.low_section_speed(),
            "high_section_speed": input.high_section_speed(),
            "physical_strength": input.physical_strength(),

            # 응고
            "upper_mold_temp1": input.upper_mold_temp1(),
            "upper_mold_temp2": input.upper_mold_temp2(),
            "lower_mold_temp1": input.lower_mold_temp1(),
            "lower_mold_temp2": input.lower_mold_temp2(),
            "Coolant_temperature": input.coolant_temp(),

            # 전체 관여 변수
            "facility_operation_cycleTime": input.facility_operation_cycleTime(),
            "production_cycletime": input.production_cycletime(),
            "count": input.count(),
            "working": input.working(),
            "tryshot_signal": "D" if input.tryshot_check() else "A"
        }

        X = pd.DataFrame([features])

        mold_code = input.mold_code()
        model = models.get(mold_code)      # Pipeline
        explainer = explainers.get(mold_code)  # TreeExplainer(xgb_model)

        if model is None or explainer is None:
            return -1

        # ✅ 1) pipeline predict → 원본 X
        pred = model.predict(X)[0]

        # ✅ 2) shap → 변환된 데이터 (전처리 후)
        X_transformed = model.named_steps["preprocessor"].transform(X)
        feature_names = model.named_steps["preprocessor"].get_feature_names_out()
        X_transformed_df = pd.DataFrame(X_transformed, columns=feature_names)

        shap_values = explainer(X_transformed_df)

        # 상태 저장
        shap_values_state.set(shap_values)
        X_input_state.set(X_transformed_df)
        return pred

    # ================== 출력 UI ==================
    @output
    @render.ui
    def pred_result_card():
        if input.btn_predict() == 0:
            return ui.div("실행 버튼을 눌러주세요", class_="p-3 text-center")

        result = do_predict()
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
    @reactive.event(input.btn_predict)
    def pred_summary():
        return f"예측 결과: {do_predict()}"

    # ================== SHAP 기반 경고 ==================
    def shap_based_warning(process: str):
        shap_values = shap_values_state.get()
        X = X_input_state.get()

        if shap_values is None or X is None:
            return ui.card_body(
                ui.p("⚠️ SHAP 계산 불가"),
                class_="text-center text-white",
                style="background-color:#6c757d; border-radius:6px; font-weight:600;"
            )

        contrib = dict(zip(X.columns, shap_values.values[0]))

        # 프로세스별 주요 변수 (전처리된 이름 기준)
        if process == "molten":
            key_vars = ["num__molten_temp", "num__molten_volume"]
        elif process == "slurry":
            key_vars = ["num__sleeve_temperature", "num__EMS_operation_time"]
        elif process == "injection":
            key_vars = ["num__cast_pressure", "num__low_section_speed", "num__high_section_speed"]
        elif process == "solidify":
            key_vars = ["num__upper_mold_temp1", "num__upper_mold_temp2", "num__Coolant_temperature"]
        else:
            key_vars = []

        msgs, score = [], 0
        for v in key_vars:
            val = contrib.get(v, 0)
            pretty_name = feature_name_map.get(v, v)   # 👈 매핑 적용
            if val > 0:
                msgs.append(f"⚠️ {pretty_name}: {val:.3f}")
            else:
                msgs.append(f"✅ {pretty_name}: {val:.3f}")
            score += val

        if score > 0:
            color, header = "#dc3545", "⚠️ 불량 위험 ↑ (SHAP)"
        else:
            color, header = "#198754", "✅ 이상 없음 (SHAP)"

        return ui.card_body(
            ui.h6(header, class_="mb-2"),
            *[ui.p(m, class_="mb-0") for m in msgs],
            class_="text-white text-center",
            style=f"background-color:{color}; border-radius:6px; font-weight:600; overflow: visible;"
        )

    # ================== 공정별 출력 ==================
    @output
    @render.ui
    @reactive.event(input.btn_predict)
    def g1_warn_msg():
        return shap_based_warning("molten")

    @output
    @render.ui
    @reactive.event(input.btn_predict)
    def g2_warn_msg():
        return shap_based_warning("slurry")

    @output
    @render.ui
    @reactive.event(input.btn_predict)
    def g3_warn_msg():
        return shap_based_warning("injection")

    @output
    @render.ui
    @reactive.event(input.btn_predict)
    def g4_warn_msg():
        return shap_based_warning("solidify")
    
    @output
    @render.ui
    @reactive.event(input.btn_predict)
    def overall_warn_msg():
        return shap_based_warning("overall")
    
    # register_shap_plots(output, shap_values_state, X_input_state, input)