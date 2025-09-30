import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# **새로운 매개변수: vars_to_hide 추가**
def plot_failrate_cutoff_dual_fast(df, var, font_family='Malgun Gothic', ma_window=5, vars_to_hide=None):
    if vars_to_hide is None:
        vars_to_hide = [] # 기본값은 빈 리스트

    plt.rcParams['font.family'] = font_family
    plt.rcParams['axes.unicode_minus'] = False
    
    col_vals = df[var].dropna()
    if col_vals.empty:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.text(0.5, 0.5, '데이터 없음', ha='center', va='center', fontsize=14)
        return fig
        
    min_val = int(col_vals.min())
    median_val = int(col_vals.median())
    max_val = int(col_vals.max())
    
    # 임계값 배열 생성
    thr_lower = np.arange(median_val, min_val - 1, -1) # 중앙값 -> 최소값 (내림차순)
    thr_upper = np.arange(median_val, max_val + 1, 1)  # 중앙값 -> 최대값 (오름차순)

    # ------------------ 불량률 계산 ------------------
    def calculate_failrates(thr_arr, direction):
        failrates = []
        for th in thr_arr:
            if direction == 'lower':
                group = df[df[var] <= th]
            else: # direction == 'upper'
                group = df[df[var] >= th]
            
            total = len(group)
            if total < 5:  # 데이터 부족 시 NaN 처리
                failrates.append(np.nan)
            else:
                failrates.append(group['passorfail'].value_counts(normalize=True).get(1, 0))
        return failrates

    failrates_lower = calculate_failrates(thr_lower, 'lower')
    failrates_upper = calculate_failrates(thr_upper, 'upper')

    # ------------------ Cut-off 탐지 로직 (기울기 기반) ------------------
    
    def find_cutoff(thr_arr, failrate_arr, ma_window):
        # 1. 1차 탐지: Raw 불량률 변화가 0.1 이상인 첫 번째 지점 (우선순위)
        cutoff = None
        for i in range(1, len(failrate_arr)):
            if not np.isnan(failrate_arr[i-1]) and not np.isnan(failrate_arr[i]):
                if abs(failrate_arr[i] - failrate_arr[i-1]) >= 0.1:
                    cutoff = thr_arr[i-1]
                    return cutoff # 1차 탐지 성공 시 즉시 반환

        # 2. 1차 탐지 실패 시: 이동 평균(MA) 기반 '기울기' 탐지 (0.025 기준)
        
        failrate_series = pd.Series(failrate_arr)
        # 5점 MA 계산
        ma_failrates = failrate_series.rolling(window=ma_window, min_periods=1, center=True).mean() 
        
        # MA 값이 유효한 인덱스만 추출
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
                cutoff = thr_arr[arr_index] 
                return cutoff
        
        return None # Cut-off를 찾지 못한 경우

    cutoff_lower = find_cutoff(thr_lower, failrates_lower, ma_window)
    cutoff_upper = find_cutoff(thr_upper, failrates_upper, ma_window)

    # ------------------ 그래프 생성 및 시각화 ------------------
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    
    # 헬퍼 함수: 그래프 그리기
    # **새로운 매개변수: hide_cutoff_line 추가**
    def plot_failrate(ax, thr_arr, failrate_arr, cutoff, title_suffix, hide_cutoff_line=False):
        failrate_series = pd.Series(failrate_arr)
        ma_failrates = failrate_series.rolling(window=ma_window, min_periods=1, center=True).mean() 

        # Raw 불량률
        ax.plot(thr_arr, failrate_arr, color='red', marker='o', linestyle='-', alpha=0.7, label='Raw 불량률')
        
        # 이동 평균선
        ax.plot(thr_arr, ma_failrates.tolist(), color='orange', linestyle='--', alpha=0.6, label=f'{ma_window}-점 MA') 
        
        ax.set_title(f'{var}: {title_suffix}')
        ax.set_xlabel(f'{var} 임계값')
        ax.set_ylabel('불량률')
        ax.set_ylim(0, 1)
        ax.grid(True, linestyle=':', alpha=0.6)
        
        # **수정된 로직:** hide_cutoff_line이 False이고 cutoff가 있을 때만 파란 선 표시
        if cutoff is not None and not hide_cutoff_line:
            # Cut-off 선
            ax.axvline(cutoff, color='blue', linestyle='--', linewidth=2, label=f'Cut-off ({cutoff})') # linestyle='--' -> '-'로 변경 (실선으로 명확히)
        
        ax.legend(loc='upper right')

    # **여기서 vars_to_hide 목록을 확인하여 hide_cutoff_line 전달**
    hide = var in vars_to_hide
    
    # 중앙값~최소값 그래프 (X <= 임계값)
    plot_failrate(axes[0], thr_lower, failrates_lower, cutoff_lower, 
                  '하한 분석: 임계값 이하 불량률 (X ≤ 임계값)', hide)
    
    # 중앙값~최대값 그래프 (X >= 임계값)
    plot_failrate(axes[1], thr_upper, failrates_upper, cutoff_upper, 
                  '상한 분석: 임계값 이상 불량률 (X ≥ 임계값)', hide)

    plt.tight_layout()
    return fig