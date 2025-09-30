from shiny import ui
from shared import feature_name_map

def shap_based_warning(process: str, shap_values_state, X_input_state, feature_name_map):
    """SHAP 값을 기반으로 공정별 경고 메시지 생성"""
    shap_values = shap_values_state.get()
    X = X_input_state.get()

    # ✅ SHAP 값/입력 데이터 없는 경우
    if shap_values is None or X is None:
        return ui.card_body(
            ui.p("⚠️ SHAP 계산 불가"),
            class_="text-center text-white",
            style="background-color:#6c757d; border-radius:6px; font-weight:600;"
        )

    # ✅ SHAP 기여도 추출 (binary classification 대응)
    if hasattr(shap_values, "values"):
        vals = shap_values.values[0]
        if vals.ndim == 2 and vals.shape[1] == 2:   # (n_features, 2)
            vals = vals[:, 1]   # ✅ 불량(클래스 1) 기준 선택
        contrib = dict(zip(X.columns, vals))
    elif isinstance(shap_values, (list, tuple)):
        contrib = dict(zip(X.columns, shap_values[0]))
    else:
        return ui.card_body(
            ui.p("⚠️ SHAP 형식 오류"),
            class_="text-center text-white",
            style="background-color:#6c757d; border-radius:6px; font-weight:600;"
        )

    # ✅ 공정별 주요 변수 매핑
    if process == "molten":
        key_vars = ["num__molten_temp", "num__molten_volume"]
    elif process == "slurry":
        key_vars = ["num__sleeve_temperature", "num__EMS_operation_time"]
    elif process == "injection":
        key_vars = ["num__cast_pressure", "num__low_section_speed", "num__high_section_speed"]
    elif process == "solidify":
        key_vars = ["num__upper_mold_temp1", "num__upper_mold_temp2", "num__Coolant_temperature"]
    elif process == "overall":
        key_vars = ["num__count"]   # 전체 공정 → 모든 변수
    else:
        key_vars = []

    # ✅ 메시지 및 점수 계산
    msgs, score = [], 0
    for v in key_vars:
        val = contrib.get(v, 0)
        pretty_name = feature_name_map.get(v, v)
        if val > 0:
            msgs.append(f"⚠️ {pretty_name}: {val:.3f}")
        else:
            msgs.append(f"✅ {pretty_name}: {val:.3f}")
        score += val

    # ✅ 색상 및 타이틀 설정
    if score > 0:
        color, header = "#dc3545", "⚠️ 불량 위험 ↑ (SHAP)"
    else:
        color, header = "#198754", "✅ 이상 없음 (SHAP)"

    return ui.card_body(
        ui.h6(header, class_="mb-2"),
        *[ui.p(m, class_="mb-0") for m in msgs],
        class_="text-white text-center",
        style=f"background-color:{color}; border-radius:6px; font-weight:600; overflow:visible;"
    )
