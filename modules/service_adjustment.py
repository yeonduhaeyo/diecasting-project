# modules/adjustment_guide.py
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import copy

# -----------------------------------
# 1) 변수 조정 설정 (간소화)
# -----------------------------------
# 변수별 조정 스텝 크기 (표준편차의 15% 기준)
ADJUSTMENT_STEP = {
    "num__production_cycletime": 2.1,
    "num__facility_operation_cycleTime": 1.8,
    "num__molten_volume": 5.6,
    "num__molten_temp": 2.1,
    "num__sleeve_temperature": 14.5,
    "num__cast_pressure": 5.4,
    "num__biscuit_thickness": 3.8,
    "num__low_section_speed": 1.9,
    "num__high_section_speed": 2.3,
    "num__physical_strength": 5.4,
    "num__upper_mold_temp1": 7.3,
    "num__upper_mold_temp2": 4.1,
    "num__lower_mold_temp1": 8.3,
    "num__lower_mold_temp2": 6.7,
    "num__coolant_temp": 0.4,
}

# 양품 샘플들의 평균값 (안전 경계선)
GOOD_SAMPLE_MEANS = {
    "num__production_cycletime": 122.7,
    "num__facility_operation_cycleTime": 121.3,
    "num__molten_volume": 88.9,
    "num__molten_temp": 720.2,
    "num__sleeve_temperature": 446.5,
    "num__cast_pressure": 328.5,
    "num__biscuit_thickness": 49.9,
    "num__low_section_speed": 110.0,
    "num__high_section_speed": 112.7,
    "num__physical_strength": 701.9,
    "num__upper_mold_temp1": 184.9,
    "num__upper_mold_temp2": 163.3,
    "num__lower_mold_temp1": 202.5,
    "num__lower_mold_temp2": 196.3,
    "num__coolant_temp": 32.5,
}

# -----------------------------------
# 2) Rule 위반 보정 함수
# -----------------------------------
def fix_rule_violations(current_sample: pd.Series, 
                       cutoffs: Dict, 
                       data_ranges: Dict) -> Tuple[pd.Series, List[str]]:
    """Rule 위반을 즉시 보정"""
    adjusted_sample = current_sample.copy()
    adjustments = []
    
    for var in current_sample.index:
        if var not in cutoffs:
            continue
            
        current_val = float(current_sample[var])
        cut = cutoffs[var]
        data_range = data_ranges[var]
        
        # 하한선 위반 체크
        if "low" in cut and current_val < cut["low"]:
            target_val = min(cut["low"], data_range["max"])
            adjusted_sample[var] = target_val
            adjustments.append(f"{var}: {current_val:.1f} → {target_val:.1f} (하한선 보정)")
        
        # 상한선 위반 체크  
        if "high" in cut and current_val > cut["high"]:
            target_val = max(cut["high"], data_range["min"])
            adjusted_sample[var] = target_val
            adjustments.append(f"{var}: {current_val:.1f} → {target_val:.1f} (상한선 보정)")
    
    return adjusted_sample, adjustments

# -----------------------------------
# 3) SHAP 기반 우선순위 계산
# -----------------------------------
def calculate_adjustment_priority(shap_contributions: Dict) -> List[Tuple[str, float, str]]:
    """SHAP 기여도로 우선순위 계산 + 조정 방향 자동 결정"""
    priorities = []
    
    for var, shap_val in shap_contributions.items():
        if shap_val > 0:
            # SHAP 값이 양수 → 변수값을 낮춰야 불량률 감소
            direction = "↓"
            priority_score = shap_val
        elif shap_val < 0:
            # SHAP 값이 음수 → 변수값을 높여야 불량률 감소
            direction = "↑"  
            priority_score = abs(shap_val)
        else:
            continue
        
        priorities.append((var, priority_score, direction))
    
    priorities.sort(key=lambda x: x[1], reverse=True)
    return priorities

# -----------------------------------
# 4) 1-변수 그리디 조정 (양방향 평균 제약 적용)
# -----------------------------------
def greedy_variable_adjustment(current_sample: pd.Series,
                              model,
                              target_prob: float,
                              priority_list: List[Tuple[str, float, str]],
                              adjustment_steps: Dict,
                              data_ranges: Dict,
                              good_means: Dict,
                              max_iterations: int = 10) -> Tuple[pd.Series, List[str], float]:
    """
    그리디 방식 변수 조정 (양방향 평균 제약 포함)
    
    핵심 로직:
    - 상향 조정(↑): 현재값 < 평균 → 평균 이하까지만 조정 가능
    - 하향 조정(↓): 현재값 > 평균 → 평균 이상까지만 조정 가능
    - 현재값 = 평균: 조정 불가
    """
    
    adjusted_sample = current_sample.copy()
    adjustments = []
    safety_stops = []
    
    current_prob = float(model.predict_proba(adjusted_sample.values.reshape(1, -1))[0, 1])
    
    for var, priority_score, shap_direction in priority_list:
        if current_prob <= target_prob:
            break
            
        if var not in adjustment_steps or var not in data_ranges:
            continue
            
        step_size = adjustment_steps[var]
        data_range = data_ranges[var]
        good_mean = good_means.get(var, None)
        current_val = float(adjusted_sample[var])
        
        # SHAP 방향 결정
        if shap_direction == "↓":
            target_direction = "down"
        else:
            target_direction = "up"
        
        # 기본 데이터 범위 체크
        if target_direction == "up" and current_val >= data_range["max"]:
            continue
        if target_direction == "down" and current_val <= data_range["min"]:
            continue
        
        # ====================================================
        # 양방향 평균 제약 체크
        # ====================================================
        if good_mean is not None:
            # 상향 조정: 현재값이 평균 이상이면 조정 불가
            if target_direction == "up" and current_val >= good_mean:
                safety_stops.append(
                    f"{var}: 상향 조정 불가 (현재값 {current_val:.1f} ≥ 양품평균 {good_mean:.1f})"
                )
                continue
            
            # 하향 조정: 현재값이 평균 이하이면 조정 불가
            if target_direction == "down" and current_val <= good_mean:
                safety_stops.append(
                    f"{var}: 하향 조정 불가 (현재값 {current_val:.1f} ≤ 양품평균 {good_mean:.1f})"
                )
                continue
        
        # ====================================================
        # 단계적 조정 시뮬레이션
        # ====================================================
        best_improvement = 0
        best_new_val = current_val
        test_val = current_val
        
        for step in range(max_iterations):
            if target_direction == "up":
                # 상향 조정: 데이터 최댓값과 양품 평균 중 작은 값까지만
                upper_limit = data_range["max"]
                if good_mean is not None:
                    upper_limit = min(upper_limit, good_mean)
                
                new_val = min(test_val + step_size, upper_limit)
                
                # 양품 평균 도달 시 중단
                if good_mean is not None and new_val >= good_mean:
                    if step > 0:
                        safety_stops.append(
                            f"{var}: 양품평균({good_mean:.1f}) 도달로 {best_new_val:.1f}에서 조정 중단"
                        )
                    break
            
            else:  # target_direction == "down"
                # 하향 조정: 데이터 최솟값과 양품 평균 중 큰 값까지만
                lower_limit = data_range["min"]
                if good_mean is not None:
                    lower_limit = max(lower_limit, good_mean)
                
                new_val = max(test_val - step_size, lower_limit)
                
                # 양품 평균 도달 시 중단
                if good_mean is not None and new_val <= good_mean:
                    if step > 0:
                        safety_stops.append(
                            f"{var}: 양품평균({good_mean:.1f}) 도달로 {best_new_val:.1f}에서 조정 중단"
                        )
                    break
            
            # 예측 확률 계산
            temp_sample = adjusted_sample.copy()
            temp_sample[var] = new_val
            new_prob = float(model.predict_proba(temp_sample.values.reshape(1, -1))[0, 1])
            
            improvement = current_prob - new_prob
            if improvement > best_improvement:
                best_improvement = improvement
                best_new_val = new_val
            elif improvement < 0:
                break
            
            test_val = new_val
            
            # 경계 도달 시 중단
            if (target_direction == "up" and new_val >= upper_limit) or \
               (target_direction == "down" and new_val <= lower_limit):
                break
        
        # 최적 조정 적용 (1% 이상 개선시)
        if best_improvement > 0.01:
            adjusted_sample[var] = best_new_val
            current_prob -= best_improvement
            direction_symbol = "↑" if target_direction == "up" else "↓"
            
            # 양품 평균 정보 추가
            constraint_info = ""
            if good_mean is not None:
                if target_direction == "up":
                    constraint_info = f" (평균 {good_mean:.1f} 이하 유지)"
                else:
                    constraint_info = f" (평균 {good_mean:.1f} 이상 유지)"
            
            adjustments.append(
                f"{var}: {current_val:.1f} → {best_new_val:.1f} {direction_symbol} "
                f"(-{best_improvement:.3f}){constraint_info}"
            )
    
    # 안전장치 정보 추가
    if safety_stops:
        adjustments.extend([f"[제약조건] {msg}" for msg in safety_stops])
    
    return adjusted_sample, adjustments, current_prob

# -----------------------------------
# 5) 메인 R-SG 알고리즘
# -----------------------------------
def rsg_adjustment_guide(current_sample: pd.Series,
                        model,
                        shap_values: Dict,
                        cutoffs: Dict,
                        data_ranges: Dict,
                        target_prob: float = 0.30) -> Dict:
    """
    Rule-first, SHAP-guided Greedy 변수 조정 가이드
    (양방향 평균 제약 적용)
    """
    
    initial_prob = float(model.predict_proba(current_sample.values.reshape(1, -1))[0, 1])
    
    result = {
        'initial_prob': initial_prob,
        'target_prob': target_prob,
        'success': False,
        'final_prob': initial_prob,
        'rule_adjustments': [],
        'shap_adjustments': [],
        'initial_sample': current_sample.copy(),
        'final_sample': current_sample.copy(),
        'explanation': ""
    }
    
    # 단계 1: Rule 위반 즉시 보정
    adjusted_sample, rule_adjustments = fix_rule_violations(
        current_sample, cutoffs, data_ranges
    )
    
    prob_after_rule = float(model.predict_proba(adjusted_sample.values.reshape(1, -1))[0, 1])
    
    result['rule_adjustments'] = rule_adjustments
    result['final_sample'] = adjusted_sample
    result['final_prob'] = prob_after_rule
    
    # Rule 보정만으로 목표 달성?
    if prob_after_rule <= target_prob:
        result['success'] = True
        result['explanation'] = f"규칙 위반 보정만으로 목표 달성 ({initial_prob:.3f} → {prob_after_rule:.3f})"
        return result
    
    # 단계 2: SHAP 기반 우선순위 계산
    priority_list = calculate_adjustment_priority(shap_values)
    
    # 단계 3: 그리디 조정 (양방향 평균 제약 적용)
    final_sample, shap_adjustments, final_prob = greedy_variable_adjustment(
        adjusted_sample, model, target_prob, priority_list,
        ADJUSTMENT_STEP, data_ranges, GOOD_SAMPLE_MEANS
    )
    
    result['shap_adjustments'] = shap_adjustments
    result['final_sample'] = final_sample
    result['final_prob'] = final_prob
    
    if final_prob <= target_prob:
        result['success'] = True
        result['explanation'] = f"단계별 조정으로 목표 달성 ({initial_prob:.3f} → {final_prob:.3f})"
    else:
        result['explanation'] = f"추가 조정 필요 ({initial_prob:.3f} → {final_prob:.3f}, 목표: {target_prob:.3f})"
    
    return result

# -----------------------------------
# 6) 조정 결과 출력 함수
# -----------------------------------
def print_adjustment_summary(result: Dict, feature_name_map: Dict):
    """조정 결과를 사용자 친화적으로 출력"""
    
    print("=" * 70)
    print("🎯 불량률 개선 조정 가이드")
    print("=" * 70)
    
    # 현황 요약
    print(f"\n📊 목표: 불량확률 {result['target_prob']:.1%} 이하 달성")
    print(f"   현재: {result['initial_prob']:.1%} → 조정 후: {result['final_prob']:.1%}")
    
    if result['success']:
        print("   ✅ 결과: 목표 달성!")
    else:
        print("   ⚠️  결과: 추가 조정 필요")
    
    # 규칙 기반 조정
    if result['rule_adjustments']:
        print("\n" + "=" * 70)
        print("🔧 1단계: 필수 조정 (규칙 위반 해결)")
        print("=" * 70)
        for adj in result['rule_adjustments']:
            var, change = adj.split(': ', 1)
            pretty_name = feature_name_map.get(var, var)
            print(f"  • {pretty_name}: {change}")
    
    # SHAP 기반 조정
    if result['shap_adjustments']:
        print("\n" + "=" * 70)
        print("🎯 2단계: AI 기반 최적화 (SHAP + 양방향 평균 제약)")
        print("=" * 70)
        for adj in result['shap_adjustments']:
            if adj.startswith('[제약조건]'):
                print(f"  ⚠️  {adj[7:]}")
            else:
                var, change = adj.split(': ', 1)
                pretty_name = feature_name_map.get(var, var)
                print(f"  • {pretty_name}: {change}")
    
    # 조정 없음
    if not result['rule_adjustments'] and not result['shap_adjustments']:
        print("\n✅ 조정 필요 없음: 모든 변수가 정상 범위 내")
    
    print("\n" + "=" * 70)

# -----------------------------------
# 7) 사용 예시
# -----------------------------------
def example_usage():
    """실제 사용 예시"""
    print("【R-SG 알고리즘 사용 예시 (양방향 평균 제약 적용)】\n")
    
    # 가상 데이터
    current_sample = pd.Series({
        'num__cast_pressure': 350,      # 평균(328.5)보다 높음 → 하향 조정 가능
        'num__coolant_temp': 25,        # 평균(32.5)보다 낮음 → 상향 조정 가능
        'num__low_section_speed': 105,  # 평균(110.0)보다 낮음
        'num__biscuit_thickness': 55,   # 평균(49.9)보다 높음
    })
    
    shap_values = {
        'num__cast_pressure': 0.25,        # 양수 → 낮춰야 함 (↓)
        'num__coolant_temp': -0.15,        # 음수 → 높여야 함 (↑)
        'num__low_section_speed': -0.05,   # 음수 → 높여야 함 (↑)
        'num__biscuit_thickness': 0.08,    # 양수 → 낮춰야 함 (↓)
    }
    
    feature_name_map = {
        'num__cast_pressure': '사출압력',
        'num__coolant_temp': '냉각온도',
        'num__low_section_speed': '저속구간속도',
        'num__biscuit_thickness': '비스킷두께'
    }
    
    print("📋 현재 샘플:")
    for var, val in current_sample.items():
        pretty_name = feature_name_map.get(var, var)
        mean_val = GOOD_SAMPLE_MEANS.get(var, 0)
        comparison = ">" if val > mean_val else "<" if val < mean_val else "="
        print(f"  {pretty_name}: {val} {comparison} 평균 {mean_val}")
    
    print("\n📊 SHAP 기여도 및 조정 방향:")
    for var, shap_val in shap_values.items():
        pretty_name = feature_name_map.get(var, var)
        direction = "↓ (낮추기)" if shap_val > 0 else "↑ (높이기)"
        current_val = current_sample[var]
        mean_val = GOOD_SAMPLE_MEANS.get(var, 0)
        
        # 조정 가능 여부 판단
        can_adjust = False
        if shap_val > 0 and current_val > mean_val:  # 낮춰야 하는데 평균보다 높음
            can_adjust = True
            constraint = f"평균({mean_val}) 이상까지만"
        elif shap_val < 0 and current_val < mean_val:  # 높여야 하는데 평균보다 낮음
            can_adjust = True
            constraint = f"평균({mean_val}) 이하까지만"
        else:
            constraint = "조정 불가 (평균 제약)"
        
        status = "✓" if can_adjust else "✗"
        print(f"  {status} {pretty_name}: {shap_val:+.3f} → {direction} | {constraint}")
    
    print("\n" + "=" * 70)
    print("\n💡 실제 사용 시:")
    print("result = rsg_adjustment_guide(current_sample, model, shap_values, CUTOFFS, DATA_RANGES)")
    print("print_adjustment_summary(result, feature_name_map)")

if __name__ == "__main__":
    example_usage()