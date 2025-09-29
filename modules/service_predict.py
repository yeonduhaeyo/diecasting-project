# service_predict.py
import pandas as pd
from shiny import reactive
from shared import models, explainers


# ======================
# 상태 저장 (shap 결과/입력데이터)
# ======================
shap_values_state = reactive.Value(None)
X_input_state = reactive.Value(None)


def do_predict(input, shap_values_state, X_input_state, models, explainers):
    """
    버튼 클릭 시 실행되는 예측 함수
    - 입력값 수집 → 모델 예측 → SHAP 계산 → 상태 저장
    """

    # ✅ 입력값 수집
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

        # 전체 과정 관여 변수
        "facility_operation_cycleTime": input.facility_operation_cycleTime(),
        "production_cycletime": input.production_cycletime(),
        "count": input.count(),
        "working": input.working(),
        "tryshot_signal": "D" if input.tryshot_check() else "A"
    }

    X = pd.DataFrame([features])

    # ✅ 모델 및 explainer 불러오기
    mold_code = input.mold_code()
    model = models.get(mold_code)
    explainer = explainers.get(mold_code)

    if model is None or explainer is None:
        return -1   # 예외 처리: 해당 mold_code 모델 없음

    # ✅ 1) 예측
    try:
        pred = model.predict(X)[0]
    except Exception as e:
        print(f"[ERROR] Prediction failed: {e}")
        return -1

    # ✅ 2) 전처리 후 데이터 변환
    try:
        X_transformed = model.named_steps["preprocessor"].transform(X)
        feature_names = model.named_steps["preprocessor"].get_feature_names_out()
        X_transformed_df = pd.DataFrame(X_transformed, columns=feature_names)
    except Exception as e:
        print(f"[ERROR] Preprocessing failed: {e}")
        return pred   # 예측은 됐으니 결과만 반환

    # ✅ 3) SHAP 계산
    try:
        shap_values = explainer(X_transformed_df)
    except Exception as e:
        print(f"[ERROR] SHAP calculation failed: {e}")
        shap_values = None

    # ✅ 4) 상태 저장
    shap_values_state.set(shap_values)
    X_input_state.set(X_transformed_df)

    return pred
