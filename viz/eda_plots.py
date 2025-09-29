import matplotlib.pyplot as plt
import seaborn as sns
from shared import df

def plot_dist(var):
    if var not in df.columns or "passorfail" not in df.columns:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "데이터 없음", ha="center", va="center")
        return fig
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.histplot(data=df, x=var, hue="passorfail", multiple="stack", kde=False,
                 palette={0: "skyblue", 1: "salmon"}, ax=ax)
    ax.set_title(f"{var} 분포 (PASS/FAIL)")
    return fig

def plot_corr_heatmap():
    corr = df.corr(numeric_only=True)
    fig, ax = plt.subplots(figsize=(14, 10))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r", center=0, ax=ax)
    ax.set_title("상관관계 Heatmap")
    return fig

def plot_proc_vs_result(var):
    """공정 변수 vs 품질 결과 (Boxplot)"""
    if var not in df.columns or "passorfail" not in df.columns:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "데이터 없음", ha="center", va="center")
        return fig
    
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.boxplot(
        data=df,
        x="passorfail",
        y=var,
        ax=ax
    )
    ax.set_title(f"{var} vs 품질 결과")
    ax.set_xlabel("품질 결과 (0=PASS, 1=FAIL)")
    ax.set_ylabel(var)
    plt.tight_layout()
    return fig