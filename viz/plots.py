# viz/plots.py
from shared import df
import matplotlib.pyplot as plt

def plot_molten_temp():
    fig, ax = plt.subplots()
    df["molten_temp"].hist(ax=ax, bins=30, color="steelblue", edgecolor="black")
    ax.set_title("용탕 온도 분포")
    ax.set_xlabel("Temperature (℃)")
    ax.set_ylabel("Count")
    return fig