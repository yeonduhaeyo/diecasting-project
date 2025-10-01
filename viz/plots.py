import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from typing import List, Optional, Tuple, Dict, Any

# ====================================================================
# Cut-off 분석 및 시각화 함수
# ====================================================================

def plot_failrate_cutoff_dual_fast(df: pd.DataFrame, var: str, ma_window: int = 5, vars_to_hide: Optional[List[str]] = None) -> plt.Figure:
    """
    공정 변수(var)에 대한 하한/상한 분석을 수행하고, Raw 데이터 기반 Cut-off(1차)와 
    MA 기반 Cut-off(2차)를 모두 탐지 및 시각화합니다.

    Args:
        df: 입력 데이터프레임. 반드시 'passorfail' 컬럼을 포함해야 합니다.
        var: 분석할 공정 변수 컬럼 이름 (예: 'sleeve_temperature').
        font_family: Matplotlib에서 사용할 폰트.
        ma_window: 이동 평균(MA) 계산에 사용할 윈도우 크기.
        vars_to_hide: Cut-off 라인을 숨길 변수 목록.

    Returns:
        Matplotlib Figure 객체.
    """
    if vars_to_hide is None:
        vars_to_hide = []

    # # 폰트 설정
    # plt.rcParams['font.family'] = font_family
    # plt.rcParams['axes.unicode_minus'] = False
    
    col_vals = df[var].dropna()
    if col_vals.empty:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.text(0.5, 0.5, '데이터 없음', ha='center', va='center', fontsize=14)
        return fig
        
    # 임계값 범위 설정
    try:
        min_val = int(col_vals.min())
        median_val = int(col_vals.median())
        max_val = int(col_vals.max())
    except ValueError:
        # 데이터가 숫자가 아닐 경우 (매우 드물지만 안전장치)
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.text(0.5, 0.5, '숫자 데이터 필요', ha='center', va='center', fontsize=14)
        return fig

    # 임계값 배열 생성 (중앙값 기준)
    thr_lower = np.arange(median_val, min_val - 1, -1)  # 중앙값 -> 최소값 (하한 분석)
    thr_upper = np.arange(median_val, max_val + 1, 1)   # 중앙값 -> 최대값 (상한 분석)

    # ------------------ 불량률 계산 ------------------
    def calculate_failrates(thr_arr: np.ndarray, direction: str) -> List[Optional[float]]:
        failrates: List[Optional[float]] = []
        for th in thr_arr:
            if direction == 'lower':
                group = df[df[var] <= th]
            else: # direction == 'upper'
                group = df[df[var] >= th]
            
            total = len(group)
            if total < 5:  # 데이터 부족 시 NaN 처리
                failrates.append(np.nan)
            else:
                # 불량률 (passorfail = 1) 계산
                rate = group['passorfail'].value_counts(normalize=True).get(1, 0)
                failrates.append(rate)
        return failrates

    failrates_lower = calculate_failrates(thr_lower, 'lower')
    failrates_upper = calculate_failrates(thr_upper, 'upper')

    # ------------------ Cut-off 탐지 로직 (분리) ------------------
    
    def find_cutoff_raw(thr_arr: np.ndarray, failrate_arr: List[Optional[float]]) -> Optional[int]:
        """1차 탐지: Raw 불량률 변화가 0.1 이상인 첫 번째 지점"""
        for i in range(1, len(failrate_arr)):
            rate_curr = failrate_arr[i]
            rate_prev = failrate_arr[i-1]
            
            if rate_prev is not None and rate_curr is not None:
                if abs(rate_curr - rate_prev) >= 0.1:
                    return thr_arr[i-1] # 변화가 시작되기 전의 임계값
        return None

    def find_cutoff_ma(thr_arr: np.ndarray, failrate_arr: List[Optional[float]], ma_window: int) -> Optional[int]:
        """2차 탐지: 이동 평균(MA) 기반 기울기 0.025 이상인 첫 번째 지점"""
        failrate_series = pd.Series(failrate_arr)
        # 5점 MA 계산
        ma_failrates = failrate_series.rolling(window=ma_window, min_periods=1, center=True).mean() 
        
        valid_indices = ma_failrates.dropna().index.tolist()
        if len(valid_indices) < 2:
            return None

        # MA 곡선의 기울기를 계산합니다.
        ma_values = ma_failrates.iloc[valid_indices].values
        ma_slope_raw = np.diff(ma_values)
        
        # 기울기(절대값)가 0.025 이상인 지점 탐지
        for j in range(len(ma_slope_raw)):
            arr_index = valid_indices[j] 
            
            slope = abs(ma_slope_raw[j])
            
            if slope >= 0.025: # 2차 탐지 기준 0.025
                # 임계값: 기울기가 0.025 이상이 되기 시작한 지점 (arr_index)
                return thr_arr[arr_index] 
        
        return None

    # Cut-off 탐지 실행
    cutoff_raw_lower = find_cutoff_raw(thr_lower, failrates_lower)
    cutoff_ma_lower = find_cutoff_ma(thr_lower, failrates_lower, ma_window)

    cutoff_raw_upper = find_cutoff_raw(thr_upper, failrates_upper)
    cutoff_ma_upper = find_cutoff_ma(thr_upper, failrates_upper, ma_window)


    # ------------------ 그래프 생성 및 시각화 ------------------
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    
    def plot_failrate(ax: plt.Axes, thr_arr: np.ndarray, failrate_arr: List[Optional[float]], 
                      cutoff_raw: Optional[int], cutoff_ma: Optional[int], 
                      title_suffix: str, hide_cutoff_line: bool):
        
        failrate_series = pd.Series(failrate_arr)
        ma_failrates = failrate_series.rolling(window=ma_window, min_periods=1, center=True).mean() 

        # Raw 불량률 (빨간색)
        ax.plot(thr_arr, failrate_arr, color='#4B4B4B', marker='o', linestyle='-', alpha=0.7, label='불량률')
        
        # 이동 평균선 (주황색)
        ax.plot(thr_arr, ma_failrates.tolist(), color='blue', linestyle='-', alpha=0.6, label=f'{ma_window}-점 MA') 
        
        ax.set_title(f'{var}: {title_suffix}', fontsize=12)
        ax.set_xlabel(f'{var} 임계값', fontsize=10)
        ax.set_ylabel('불량률', fontsize=10)
        ax.set_ylim(0, 1.05)
        ax.grid(True, linestyle=':', alpha=0.6)
        
        # ⭐️ 1차 Cut-off 시각화 (빨간불: 붕괴 마지노선)
        if cutoff_raw is not None and not hide_cutoff_line:
            ax.axvline(cutoff_raw, color='red', linestyle='--', linewidth=2, 
                       label=f'불량율 기반 Cut-off ({cutoff_raw})') 
                       
        # ⭐️ 2차 Cut-off 시각화 (노란불: 예방적 경고)
        if cutoff_ma is not None and not hide_cutoff_line:
            # 1차 Cut-off와 2차 Cut-off가 동일하지 않고, 2차 Cut-off가 1차보다 덜 위험할 때만 표시
            if cutoff_ma != cutoff_raw:
                ax.axvline(cutoff_ma, color='gold', linestyle='--', linewidth=2, 
                           label=f'MA 주의 Cut-off ({cutoff_ma})')
        
        # 범례 표시
        ax.legend(loc='upper right', fontsize=8)


    # **vars_to_hide 목록을 확인하여 hide_cutoff_line 전달**
    hide = var in vars_to_hide
    
    # 중앙값~최소값 그래프 (X <= 임계값)
    plot_failrate(axes[0], thr_lower, failrates_lower, cutoff_raw_lower, cutoff_ma_lower,
                  '하한 분석: 임계값 이하 불량률 (X ≤ 임계값)', hide)
    
    # 중앙값~최대값 그래프 (X >= 임계값)
    plot_failrate(axes[1], thr_upper, failrates_upper, cutoff_raw_upper, cutoff_ma_upper,
                  '상한 분석: 임계값 이상 불량률 (X ≥ 임계값)', hide)

    plt.tight_layout()
    return fig