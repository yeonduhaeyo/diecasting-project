import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

def plot_failrate_cutoff_dual_fast(df, var, font_family='Malgun Gothic'):
    plt.rcParams['font.family'] = font_family
    plt.rcParams['axes.unicode_minus'] = False
    col_vals = df[var].dropna()
    min_val = int(col_vals.min())
    median_val = int(col_vals.median())  # 중앙값 사용
    max_val = int(col_vals.max())
    # 중앙값~최소값 (내림차순)
    thr_lower = np.arange(median_val, min_val - 1, -1)
    # 중앙값~최대값 (오름차순)
    thr_upper = np.arange(median_val, max_val + 1, 1)
    failrates_lower = []
    failrates_upper = []
    for th in thr_lower:
        group = df[df[var] <= th]
        total = len(group)
        if total == 0:
            failrates_lower.append(np.nan)
        else:
            failrates_lower.append(group['passorfail'].value_counts(normalize=True).get(1, 0))
    for th in thr_upper:
        group = df[df[var] >= th]
        total = len(group)
        if total == 0:
            failrates_upper.append(np.nan)
        else:
            failrates_upper.append(group['passorfail'].value_counts(normalize=True).get(1, 0))
    # cut-off 탐지: 불량률 변화가 0.1 이상인 첫 번째 지점
    cutoff_lower = None
    for i in range(1, len(failrates_lower)):
        if not np.isnan(failrates_lower[i-1]) and not np.isnan(failrates_lower[i]):
            if abs(failrates_lower[i] - failrates_lower[i-1]) >= 0.1:
                cutoff_lower = thr_lower[i-1]
                break
    cutoff_upper = None
    for i in range(1, len(failrates_upper)):
        if not np.isnan(failrates_upper[i-1]) and not np.isnan(failrates_upper[i]):
            if abs(failrates_upper[i] - failrates_upper[i-1]) >= 0.1:
                cutoff_upper = thr_upper[i-1]
                break
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    # 중앙값~최소값
    axes[0].plot(thr_lower, failrates_lower, color='red', marker='o', label='불량률')
    axes[0].set_title(f'{var}: 중앙→최소 cut-off')
    axes[0].set_xlabel(f'{var} ≤ 임계값')
    axes[0].set_ylabel('불량률')
    axes[0].set_ylim(0, 1)
    axes[0].legend()
    axes[0].grid(True)
    if cutoff_lower is not None:
        axes[0].axvline(cutoff_lower, color='blue', linestyle='--', linewidth=2, label='cut-off')
        axes[0].legend()
    # 중앙값~최대값
    axes[1].plot(thr_upper, failrates_upper, color='red', marker='o', label='불량률')
    axes[1].set_title(f'{var}: 중앙→최대 cut-off')
    axes[1].set_xlabel(f'{var} ≥ 임계값')
    axes[1].set_ylabel('불량률')
    axes[1].set_ylim(0, 1)
    axes[1].legend()
    axes[1].grid(True)
    if cutoff_upper is not None:
        axes[1].axvline(cutoff_upper, color='blue', linestyle='--', linewidth=2, label='cut-off')
        axes[1].legend()
    plt.tight_layout()
    return fig
