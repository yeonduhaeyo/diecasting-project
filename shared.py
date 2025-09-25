# shared.py
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

# app.py가 있는 위치를 기준으로 절대 경로 관리
app_dir = Path(__file__).parent
# 데이터 경로
data_dir = app_dir / "data"

# 한글 폰트 설정 (Windows 기준: 맑은 고딕)
plt.rcParams['font.family'] = 'Malgun Gothic'
# 음수 기호 깨짐 방지
plt.rcParams['axes.unicode_minus'] = False

# Data Load
df = pd.read_csv(data_dir / "train.csv")