# modules/service_warnings.py
from shiny import ui
import numpy as np
from shared import feature_name_map, feature_name_map_kor

# -----------------------------------
# 1) Cut-off 기준 정의
# -----------------------------------
CUTOFFS = {
    "num__low_section_speed": {"low": 100, "high": 114},
    "num__high_section_speed": {"low": 100},
    "num__coolant_temp": {"low": 20},
    "num__biscuit_thickness": {"low": 42, "high": 56},
    "num__sleeve_temperature": {"low": 128},
    "num__cast_pressure": {"low": 314},
    "num__upper_mold_temp1": {"low": 103},
    "num__upper_mold_temp2": {"low": 80},
    "num__lower_mold_temp1": {"low": 92},
    "num__lower_mold_temp2": {"low": 71},
}

# -----------------------------------
# 2) 실제 데이터 범위 (CSV에서 추출)
# -----------------------------------
DATA_RANGES = {
    "num__production_cycletime": {"min": 60, "max": 500},
    "num__facility_operation_cycleTime": {"min": 60, "max": 500},
    "num__molten_volume": {"min": -1, "max": 600},
    "num__molten_temp": {"min": 70, "max": 750},
    "num__sleeve_temperature": {"min": 20, "max": 1000},
    "num__cast_pressure": {"min": 40, "max": 370},
    "num__biscuit_thickness": {"min": 0, "max": 450},
    "num__low_section_speed": {"min": 0, "max": 200},
    "num__high_section_speed": {"min": 0, "max": 400},
    "num__physical_strength": {"min": 0, "max": 750},
    "num__upper_mold_temp1": {"min": 10, "max": 400},
    "num__upper_mold_temp2": {"min": 10, "max": 250},
    "num__lower_mold_temp1": {"min": 10, "max": 400},
    "num__lower_mold_temp2": {"min": 10, "max": 550},
    "num__coolant_temp": {"min": 10, "max": 50},  # Coolant_temperature -> coolant_temp
}

# 공정별 변수 매핑
PROCESS_VARS = {
    "molten": ["num__molten_temp", "num__molten_volume"],
    "slurry": ["num__sleeve_temperature", "num__EMS_operation_time"],
    "injection": ["num__cast_pressure", "num__low_section_speed",
                  "num__high_section_speed", "num__biscuit_thickness"],
    "solidify": ["num__upper_mold_temp1", "num__upper_mold_temp2",
                 "num__lower_mold_temp1", "num__lower_mold_temp2", "num__coolant_temp"],
    "overall": [
        "num__facility_operation_cycleTime",
        "num__production_cycletime",
        "num__count",
        "cat__working_가동",
        "cat__working_정지",
        "cat__tryshot_signal_A",
        "cat__tryshot_signal_D",
    ],
}

# -----------------------------------
# 2) 개선된 정규화 함수들
# -----------------------------------
def normalize_shap_contribution(shap_value, prediction_prob):
    """SHAP 기여도를 예측 확률 대비 비율로 정규화 (0~1)"""
    if prediction_prob <= 0 or prediction_prob > 1:
        return 0.0
    
    # 불량 방향 기여도만 고려
    positive_contrib = max(0, shap_value)
    
    # 전체 예측 확률 대비 비율
    normalized = positive_contrib / prediction_prob
    
    # 0~1 범위 보장
    return min(normalized, 1.0)

def normalize_rule_severity(var, value):
    """규칙 위반도를 데이터 범위 대비 비율로 정규화 (0~1)"""
    if var not in CUTOFFS or var not in DATA_RANGES:
        return 0.0
    
    cut = CUTOFFS[var]
    data_range = DATA_RANGES[var]
    severity = 0.0
    
    # 하한선 위반
    if "low" in cut and value < cut["low"]:
        denominator = cut["low"] - data_range["min"]
        if denominator > 0:
            severity += (cut["low"] - value) / denominator
    
    # 상한선 위반
    if "high" in cut and value > cut["high"]:
        denominator = data_range["max"] - cut["high"]
        if denominator > 0:
            severity += (value - cut["high"]) / denominator
    
    # 0~1 범위 보장
    return min(severity, 1.0)

# -----------------------------------
# 3) 경고 메시지 생성 함수 (개선됨)
# -----------------------------------
def shap_based_warning(process: str,
                       shap_values_state,
                       X_input_state,
                       feature_name_map,
                       pred_state=None):
    """SHAP + Cut-off 융합 기반 공정별 경고 메시지 (개선된 정규화)"""
    shap_values = shap_values_state.get()
    X = X_input_state.get()
    pred = pred_state.get() if pred_state is not None else None

    # ✅ 값 없는 경우
    if shap_values is None or X is None:
        return ui.card_body(
            ui.p("⚠️ SHAP 계산 불가"),
            class_="text-center text-white",
            style="background-color:#6c757d; border-radius:6px; font-weight:600;"
        )

    # ✅ SHAP 기여도 추출
    if hasattr(shap_values, "values"):
        vals = shap_values.values[0]
        if vals.ndim == 2 and vals.shape[1] == 2:
            vals = vals[:, 1]  # 불량 클래스(1) 기준
        contrib = dict(zip(X.columns, vals))
    else:
        return ui.card_body(
            ui.p("⚠️ SHAP 형식 오류"),
            class_="text-center text-white",
            style="background-color:#6c757d; border-radius:6px; font-weight:600;"
        )

    key_vars = PROCESS_VARS.get(process, [])
    
    # 예측 확률 가져오기 (SHAP 정규화용)
    prediction_prob = float(pred) if isinstance(pred, (int, float)) and pred > 0 else 0.8

    # ====================================
    # A. 개선된 SHAP 신호 처리
    # ====================================
    shap_normalized = {}
    for v in key_vars:
        if v in contrib:
            shap_raw = contrib[v]
            shap_norm = normalize_shap_contribution(shap_raw, prediction_prob)
            shap_normalized[v] = shap_norm
        else:
            shap_normalized[v] = 0.0
    
    # 공정별 SHAP 스코어 (정규화된 값으로 계산)
    shap_values_list = list(shap_normalized.values())
    shap_max = max(shap_values_list) if shap_values_list else 0.0
    shap_avg = sum(shap_values_list) / max(len(key_vars), 1)
    shap_score = 0.7 * shap_max + 0.3 * shap_avg  # 이미 0~1 범위

    # ====================================
    # B. 개선된 Rule 신호 처리
    # ====================================
    rule_normalized = {}
    for v in key_vars:
        if v in X.columns:
            current_value = float(X.iloc[0][v])
            rule_norm = normalize_rule_severity(v, current_value)
            rule_normalized[v] = rule_norm
        else:
            rule_normalized[v] = 0.0
    
    # 공정별 Rule 스코어 (정규화된 값으로 계산)
    rule_values_list = list(rule_normalized.values())
    rule_max = max(rule_values_list) if rule_values_list else 0.0
    rule_avg = sum(rule_values_list) / max(len(key_vars), 1)
    rule_score = 0.7 * rule_max + 0.3 * rule_avg  # 이미 0~1 범위

    # ====================================
    # C. 통합 스코어 (클리핑 불필요)
    # ====================================
    w_shap, w_rule = 0.5, 0.5
    proc_score = w_shap * shap_score + w_rule * rule_score

    # ====================================
    # D. 의사결정 (개선된 임계값)
    # ====================================
    HIGH_THRESHOLD = 0.15
    
    if shap_score > HIGH_THRESHOLD and rule_score > HIGH_THRESHOLD:
        color, header = "#ff5733", "⚡ 강한 원인 후보"
        priority = "critical"
    elif shap_score > HIGH_THRESHOLD:
        color, header = "#ffc107", "⚠️ 모델 신호 경고 (관찰 필요)"
        priority = "model_alert"
    elif rule_score > HIGH_THRESHOLD:
        color, header = "#fd7e14", "⚠️ 기준치 초과 (관찰 필요)"
        priority = "rule_alert"
    else:
        color, header = "#198754", "✅ 이상 없음"
        priority = "normal"

    # ====================================
    # E. 변수별 통합 분석 (개선됨)
    # ====================================
    msgs = []
    var_combined = {}
    
    # 변수별 상대적 중요도 계산 (정규화된 값 기준)
    total_shap = sum(shap_normalized.values()) + 1e-6
    total_rule = sum(rule_normalized.values()) + 1e-6
    
    for v in key_vars:
        # 각 신호별 상대적 기여도
        shap_relative = shap_normalized[v] / total_shap
        rule_relative = rule_normalized[v] / total_rule
        
        # 통합 상대적 중요도
        combined_relative = w_shap * shap_relative + w_rule * rule_relative
        
        var_combined[v] = {
            'combined_relative': combined_relative,
            'shap_normalized': shap_normalized[v],
            'rule_normalized': rule_normalized[v],
            'shap_relative': shap_relative,
            'rule_relative': rule_relative
        }
    
    # Top 3 변수 선택 (상대적 중요도 기준)
    top_vars = sorted(var_combined.items(), 
                     key=lambda x: x[1]['combined_relative'], 
                     reverse=True)[:3]
    
    for v, scores in top_vars:
        if scores['combined_relative'] > 0.05:  # 5% 이상 기여하는 변수만
            pretty = feature_name_map.get(v, v)
            
            # 신호 타입 표시 (절대값 기준)
            shap_abs = scores['shap_normalized']
            rule_abs = scores['rule_normalized']
            
            if shap_abs > 0.1 and rule_abs > 0.1:
                signal_type = "🔴"  # 두 신호 모두 강함
            elif shap_abs > 0.1:
                signal_type = "🟡"  # SHAP만 강함
            elif rule_abs > 0.1:
                signal_type = "🟠"  # Rule만 강함
            else:
                signal_type = "⚪"  # 약한 신호
            
            msgs.append(
                f"{signal_type} {pretty}: "
                f"SHAP={shap_abs:.2f}({scores['shap_relative']:.1%}), "
                f"Rule={rule_abs:.2f}({scores['rule_relative']:.1%})"
            )

    # 메시지 없으면 기본값
    if not msgs:
        msgs.append("모든 변수 정상 범위")

    # ====================================
    # F. UI 반환
    # ====================================
    header_ui = ui.div(
        ui.h6(f"{header}", ui.br(), f"(Score={proc_score:.2f})", class_="mb-2"),
        class_="text-white text-center",
        style=f"background-color:{color}; border-radius:6px; font-weight:600; padding:0.8rem;"
    )

    details_ui = ui.div(
        *[ui.p(m, class_="mb-0 text-left", style="font-size:1.2rem;") for m in msgs],
        ui.p(
            f"📊 SHAP={shap_score:.2f} | Rule={rule_score:.2f} | Pred={prediction_prob:.2f}",
            class_="mt-2 mb-0",
            style="font-size:0.8rem; opacity:0.8;"
        ),
    )

    return {"header": header_ui, "details": details_ui}

# -----------------------------------
# 4) 데이터 범위 업데이트 함수
# -----------------------------------
def update_data_ranges(new_ranges):
    """외부에서 실제 데이터 범위를 업데이트하는 함수"""
    global DATA_RANGES
    DATA_RANGES.update(new_ranges)
    print(f"데이터 범위 업데이트 완료: {len(new_ranges)}개 변수")