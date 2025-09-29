import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from shared import df   # shared.py에서 df 불러오기

def plot_molten_temp_vs_fail():
    # 필요한 컬럼이 없을 경우 대비
    if "molten_temp" not in df.columns or "passorfail" not in df.columns:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "데이터 없음", ha="center", va="center")
        return fig

    # 온도 구간 나누기
    bins = np.linspace(df["molten_temp"].min(), df["molten_temp"].max(), 6)  # 5개 구간
    df["temp_bin"] = pd.cut(df["molten_temp"], bins)

    # 구간별 불량률 계산
    fail_rate = df.groupby("temp_bin")["passorfail"].mean()

    # 막대그래프 시각화
    fig, ax = plt.subplots(figsize=(8, 5))
    fail_rate.plot(kind="bar", color="skyblue", edgecolor="black", ax=ax)

    # 기준선 표시
    ax.axhline(0.05, color="red", linestyle="--", label="관리 기준선 (불량률 5%)")

    ax.set_xlabel("용탕 온도 구간 (℃)")
    ax.set_ylabel("불량률")
    ax.set_title("용탕 온도 vs 불량률 (구간별)")
    ax.legend()
    plt.xticks(rotation=45, ha="right")

    plt.tight_layout()
    
    return fig
