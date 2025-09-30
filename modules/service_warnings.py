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
# 2) 규칙 기반 심각도 계산
# -----------------------------------
def rule_severity(var, value):
    """Cut-off 기준 대비 상대 거리로 심각도 계산"""
    if var not in CUTOFFS:
        return 0.0

    cut = CUTOFFS[var]
    sev = 0.0

    # low cut-off: 값이 낮아질수록 불량 ↑
    if "low" in cut and value < cut["low"]:
        sev += (cut["low"] - value) / (abs(cut["low"]) + 1e-6)

    # high cut-off: 값이 높아질수록 불량 ↑
    if "high" in cut and value > cut["high"]:
        sev += (value - cut["high"]) / (abs(cut["high"]) + 1e-6)

    return sev


# -----------------------------------
# 3) 경고 메시지 생성 함수
# -----------------------------------
def shap_based_warning(process: str,
                       shap_values_state,
                       X_input_state,
                       feature_name_map,
                       pred_state=None):
    """SHAP + Cut-off 융합 기반 공정별 경고 메시지"""
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

    # ====================================
    # A. 모델 신호 (SHAP) - 불량 방향만
    # ====================================
    shap_push = {v: max(0, contrib.get(v, 0)) for v in key_vars}
    
    # 샘플 내 정규화 (비중 파악용)
    total_push = sum(shap_push.values()) + 1e-6
    shap_norm = {v: val / total_push for v, val in shap_push.items()}
    
    # ✅ 공정별 공정한 비교: 최댓값 + 평균 혼합
    # - 최댓값: 가장 심각한 변수 포착
    # - 평균: 전반적 상태 반영
    # - 7:3 비율로 최댓값에 더 가중
    shap_max = max(shap_push.values()) if shap_push else 0.0
    shap_avg = sum(shap_push.values()) / max(len(key_vars), 1)
    shap_score = 0.7 * shap_max + 0.3 * shap_avg

    # ====================================
    # B. 규칙 신호 (Rule) - 임계값 위반도
    # ====================================
    rule_vals = {}
    for v in key_vars:
        if v in X.columns:
            sev = rule_severity(v, float(X.iloc[0][v]))
            rule_vals[v] = sev
    
    # Rule도 정규화 (비중 파악용)
    rule_total = sum(rule_vals.values()) + 1e-6
    rule_norm = {v: val / rule_total for v, val in rule_vals.items()}
    
    # ✅ 공정별 공정한 비교: 최댓값 + 평균 혼합
    rule_max = max(rule_vals.values()) if rule_vals else 0.0
    rule_avg = sum(rule_vals.values()) / max(len(key_vars), 1)
    rule_score = 0.7 * rule_max + 0.3 * rule_avg

    # ====================================
    # C. 가중합 (스케일 안정화) -> min-max 스케일링
    # ====================================
    # 두 신호를 0~1 범위로 클리핑 후 가중합
    shap_clipped = min(shap_score, 1.0)
    rule_clipped = min(rule_score, 1.0)
    
    w_shap, w_rule = 0.6, 0.4
    proc_score = w_shap * shap_clipped + w_rule * rule_clipped

    # ====================================
    # D. 모델 확률 보정
    # ====================================
    if isinstance(pred, (int, float)) and pred not in [-1, 0]:
        proc_score *= float(pred)

    # ====================================
    # E. 의사결정 (두 신호 동시 고려)
    # ====================================
    # 임계값 설정 (조정 가능)
    HIGH_THRESHOLD = 0.3
    
    if shap_clipped > HIGH_THRESHOLD and rule_clipped > HIGH_THRESHOLD:
        color, header = "#ff5733", "⚡ 강한 원인 후보"
        priority = "critical"
    elif shap_clipped > HIGH_THRESHOLD:
        color, header = "#ffc107", "⚠️ 모델 신호 경고 (관찰 필요)"
        priority = "model_alert"
    elif rule_clipped > HIGH_THRESHOLD:
        color, header = "#fd7e14", "⚠️ 기준치 초과 (관찰 필요)"
        priority = "rule_alert"
    else:
        color, header = "#198754", "✅ 이상 없음"
        priority = "normal"

    # ====================================
    # F. Top 변수 리포트 (통합)
    # ====================================
    msgs = []
    
    # 변수별 통합 스코어 계산 (정규화된 값 사용)
    var_combined = {}
    for v in key_vars:
        s_norm = shap_norm.get(v, 0)
        r_norm = rule_norm.get(v, 0)
        combined = w_shap * s_norm + w_rule * r_norm
        var_combined[v] = {
            'combined': combined,
            'shap': shap_push.get(v, 0),
            'rule': rule_vals.get(v, 0)
        }
    
    # Top 3 변수 선택
    top_vars = sorted(var_combined.items(), 
                     key=lambda x: x[1]['combined'], 
                     reverse=True)[:3]
    
    for v, scores in top_vars:
        if scores['combined'] > 0.05:  # 미미한 기여는 제외
            pretty = feature_name_map.get(v, v)
            
            # 신호 타입 표시
            if scores['shap'] > 0.01 and scores['rule'] > 0.01:
                signal_type = "🔴"  # 두 신호 모두
            elif scores['shap'] > 0.01:
                signal_type = "🟡"  # SHAP만
            elif scores['rule'] > 0.01:
                signal_type = "🟠"  # Rule만
            else:
                signal_type = "⚪"
            
            msgs.append(
                f"{signal_type} {pretty}: "
                f"SHAP={scores['shap']:.3f}, Rule={scores['rule']:.3f}"
            )

    # 메시지 없으면 기본값
    if not msgs:
        msgs.append("모든 변수 정상 범위")

    # ====================================
    # G. UI 반환
    # ====================================
    # return ui.card_body(
    #     ui.h6(f"{header} (Score={proc_score:.2f})", class_="mb-2"),
    #     *[ui.p(m, class_="mb-0 text-left", style="font-size:0.9rem;") for m in msgs],
    #     ui.p(
    #         f"📊 SHAP={shap_clipped:.2f} | Rule={rule_clipped:.2f}",
    #         class_="mt-2 mb-0",
    #         style="font-size:0.8rem; opacity:0.8;"
    #     ),
    #     class_="text-white",
    #     style=f"background-color:{color}; border-radius:6px; font-weight:600; padding:1rem;"
    # )
    header_ui = ui.div(
        ui.h6(f"{header}", ui.br() ,f"(Score={proc_score:.2f})", class_="mb-2"),
        class_="text-white text-center",
        style=f"background-color:{color}; border-radius:6px; font-weight:600; padding:0.8rem;"
    )

    details_ui = ui.div(
        *[ui.p(m, class_="mb-0 text-left", style="font-size:1.5rem;") for m in msgs],
        ui.p(
            f"📊 SHAP={shap_clipped:.2f} | Rule={rule_clipped:.2f}",
            class_="mt-2 mb-0",
            style="font-size:0.8rem; opacity:0.8;"
        ),
    )

    return {"header": header_ui, "details": details_ui}