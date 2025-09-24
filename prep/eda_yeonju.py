import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

plt.rcParams['font.family'] = 'Malgun Gothic'

df = pd.read_csv("./data/train.csv")

### Data EDA
# 데이터 크기 및 기본 정보
print(df.shape)
print(df.info())
df.head()
df.iloc[:,20:].head()

# 시간 데이터 datetime 타입으로 변환
df["timestamp"] = pd.to_datetime(df["date"] + " " + df["time"], errors="coerce") # 수집시간 및 일자
df["registration_time"] = pd.to_datetime(df["registration_time"]) # 등록 일시

df[["timestamp", "registration_time"]].head()
(df["timestamp"] == df["registration_time"]).all()

# target변수와 수치형 변수, 범주형 변수 나눠서 확인
# target = df["passorfail"]
df_num = df.select_dtypes("number").columns.drop(["passorfail", "day", "month", "weekday"])
df_cat = df.select_dtypes("object").columns.drop(["time", "date"])
df_time = df.select_dtypes("datetime").columns

df[df_num].describe()

# ---------------------------------------------------------------

### 결측치 확인
# 수치형 결측치
missing_num = df[df_num].isnull().sum()
missing_num_ratio = (missing_num / len(df)) * 100
missing_num_df = pd.DataFrame({
    "missing_count": missing_num,
    "missing_ratio(%)": missing_num_ratio
}).sort_values(by="missing_ratio(%)", ascending=False)

# 범주형 결측치
missing_cat = df[df_cat].isnull().sum()
missing_cat_ratio = (missing_cat / len(df)) * 100
missing_cat_df = pd.DataFrame({
    "missing_count": missing_cat,
    "missing_ratio(%)": missing_cat_ratio
}).sort_values(by="missing_ratio(%)", ascending=False)

print("📊 수치형 변수 결측치 현황")
print(missing_num_df[missing_num_df["missing_count"] > 0])
print("\n📊 범주형 변수 결측치 현황")
print(missing_cat_df[missing_cat_df["missing_count"] > 0])

# 행별 결측치 개수
row_na_count = df.isnull().sum(axis=1)
print(row_na_count.value_counts().sort_index())

row_with_17_na = df[row_na_count == 17]   # 결측치 17개인 행
df_dropna = df.drop(index=row_with_17_na.index)
df_dropna.isna().sum()

# upper_mold_temp3, lower_mold_temp3 동시에 결측인 행 확인 -> 313
mask = df["upper_mold_temp3"].isnull() & df["lower_mold_temp3"].isnull()
rows_both_na = df[mask]
print("동시에 결측인 행 개수:", rows_both_na.shape[0])

# molten_volume, 시계열성으로 확인
# 날짜별 결측률
na_vol_day = df["molten_volume"].isnull().groupby(df["timestamp"].dt.date).mean() * 100

plt.figure(figsize=(12,5))
na_vol_day.plot(marker="o", color="red")
plt.title("날짜별 molten_volume 결측률 (%)")
plt.xlabel("Date")
plt.ylabel("결측률 (%)")
plt.grid(True, alpha=0.3)
plt.show()

# 시간대별 결측률
na_vol_hour = df["molten_volume"].isnull().groupby(df["timestamp"].dt.hour).mean() * 100

plt.figure(figsize=(10,5))
na_vol_hour.plot(kind="bar", color="orange")
plt.title("시간대별 molten_volume 결측률 (%)")
plt.xlabel("Hour of Day")
plt.ylabel("결측률 (%)")
plt.show()

# molten_temp vs molten_volume 비교
df_copy = df.copy()
df_copy["molten_temp_na"] = df_copy["molten_temp"].isnull()
df_copy["molten_volume_na"] = df_copy["molten_volume"].isnull()

# 날짜별 결측률
na_day = (
    df_copy.groupby(df_copy["timestamp"].dt.date)[["molten_temp_na", "molten_volume_na"]]
           .mean() * 100
)

plt.figure(figsize=(12,6))
plt.plot(na_day.index, na_day["molten_temp_na"], marker="o", label="molten_temp 결측률")
plt.plot(na_day.index, na_day["molten_volume_na"], marker="o", label="molten_volume 결측률")
plt.title("날짜별 molten_temp vs molten_volume 결측률 (%)")
plt.xlabel("Date")
plt.ylabel("결측률 (%)")
plt.legend()
plt.grid(alpha=0.3)
plt.show()

# 시간대별 결측률
na_hour = (
    df_copy.groupby(df_copy["timestamp"].dt.hour)[["molten_temp_na", "molten_volume_na"]]
           .mean() * 100
)

plt.figure(figsize=(10,5))
plt.plot(na_hour.index, na_hour["molten_temp_na"], marker="o", label="molten_temp 결측률")
plt.plot(na_hour.index, na_hour["molten_volume_na"], marker="o", label="molten_volume 결측률")
plt.title("시간대별 molten_temp vs molten_volume 결측률 (%)")
plt.xlabel("Hour of Day")
plt.ylabel("결측률 (%)")
plt.legend()
plt.grid(alpha=0.3)
plt.show()

# ---------------------------------------------------------

### target 분포 확인
print(df["passorfail"].value_counts())
print(df["passorfail"].value_counts(normalize=True) * 100)
sns.countplot(data=df, x="passorfail", palette="Set2")
plt.title("Pass/Fail 분포")
plt.show()


### 수치형 변수
# 히스토그램 - 전체 분포 확인
df[df_num].hist(figsize=(12, 10), bins=30)
plt.tight_layout()
plt.show()

for i in df_num:
    print(i, df[i].nunique())

df["low_section_speed"].hist()
df["low_section_speed"].describe()
df[df["low_section_speed"] > 150]['low_section_speed']

### 범주형 변수
# 막대 그래프 - 전체 분포 확인
cat_cols = df_cat   # 범주형 변수 리스트
n_cols = 4          # 한 줄에 4개
n_rows = (len(cat_cols) + n_cols - 1) // n_cols  # 필요한 행 개수 계산

fig, axes = plt.subplots(n_rows, n_cols, figsize=(4*n_cols, 4*n_rows))
axes = axes.flatten()  # 2차원 배열 → 1차원으로

for i in df_cat:
    print(i, df[i].nunique())
    
for i, col in enumerate(cat_cols):
    sns.countplot(
        data=df, 
        x=col, 
        order=df[col].value_counts().index,
        palette="Set3",
        ax=axes[i]
    )
    axes[i].set_title(f"{col} 분포")
    axes[i].tick_params(axis="x", rotation=45)

# 남는 subplot 칸 삭제
for j in range(i+1, len(axes)):
    fig.delaxes(axes[j])

plt.tight_layout()
plt.show()

# -------------------------------------------------
# 그래프 - > t_test나 등등
# 각자 맡은 변수 + time,date, count, mold_code는 공통적으로 고려
# 1. mold_code별로 카운트가 순서대로 생산
# 2. count가 초기화 될 때 불량률(거의 대부분), 
# 혹은 count가 끝에 부분(그날 해당 몰드에서 생산 끝내려고 할 때) 
# 불량률 올라감


### 담당 컬럼
# 24. sleeve_temperature - 슬리브 온도
# 25. physical_strength - 형체력
# 26. Coolant_temperature - 냉각수 온도

# 33. time, day , month, weekday: o (전체) -> timestamp
# model_code, count -> 어떤 공정인지?
# target : passorfail
df_selected = df[["timestamp", 
                  "sleeve_temperature", "Coolant_temperature", "physical_strength",
                  "mold_code",
                  "count",
                  "passorfail"]].copy()
df_selected = df_selected.dropna()
df_selected.info()

df.iloc[:,20:]

df_selected.head()

# *각 변수별로 시계열그래프 작성 (시계열로 주기성)
cols = ["sleeve_temperature", "Coolant_temperature", "physical_strength"]
# 파생 변수 추가
df_selected["hour"] = df_selected["timestamp"].dt.hour
df_selected["weekday"] = df_selected["timestamp"].dt.dayofweek  # 0=월, 6=일

### mold_code별 시계열 데이터 분석
def plot_mold_trend(df, mold_code, freq="1h"):
    """
    mold_code별 시계열 데이터 분석 (추세 + 세부 + 불량 강조)
    
    Parameters
    ----------
    df : DataFrame (columns: timestamp, sleeve_temperature, Coolant_temperature, physical_strength, count, passorfail, mold_code)
    mold_code : int or str
        분석할 mold_code
    freq : str
        리샘플링 주기 (예: "1h", "1d")
    """
    
    # 데이터 필터링
    df_sub = df[df["mold_code"] == mold_code].copy()
    if df_sub.empty:
        print(f"mold_code={mold_code} 데이터 없음")
        return
    
    df_resampled = df_sub.resample(freq, on="timestamp").mean().reset_index()
    
    plt.figure(figsize=(14,5))
    plt.plot(df_resampled["timestamp"], df_resampled["sleeve_temperature"], label="sleeve_temperature", color="blue")
    plt.plot(df_resampled["timestamp"], df_resampled["Coolant_temperature"], label="Coolant_temperature", color="green")
    plt.plot(df_resampled["timestamp"], df_resampled["physical_strength"], label="physical_strength", color="red")
    plt.plot(df_resampled["timestamp"], df_resampled["count"], label="count", color="orange", linestyle="--")
    plt.legend(loc="upper left", bbox_to_anchor=(1.02, 1))
    plt.title(f"[추세] mold_code={mold_code} ({freq} 평균)")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()
    
    # 세부 비교 (subplot)
    fig, axes = plt.subplots(2, 1, figsize=(14,8), sharex=True)

    # (센서값)
    axes[0].plot(df_sub["timestamp"], df_sub["sleeve_temperature"], color="blue", linewidth=0.7, label="sleeve_temperature")
    axes[0].plot(df_sub["timestamp"], df_sub["Coolant_temperature"], color="green", linewidth=0.7, label="Coolant_temperature")
    axes[0].plot(df_sub["timestamp"], df_sub["physical_strength"], color="red", linewidth=0.7, label="physical_strength")
    axes[0].set_ylabel("Sensor Values")
    axes[0].legend(loc="upper left", bbox_to_anchor=(1.02, 1))
    axes[0].grid(alpha=0.3)

    # (count)
    axes[1].plot(df_sub["timestamp"], df_sub["count"], color="orange", linewidth=0.7)
    axes[1].set_ylabel("Count (Daily shot #)")
    axes[1].set_xlabel("Timestamp")
    axes[1].grid(alpha=0.3)

    plt.suptitle(f"[세부] mold_code={mold_code} (센서 vs count)", y=1.02)
    plt.tight_layout()
    plt.show()
    
    # 불량 강조
    cols = ["sleeve_temperature", "Coolant_temperature", "physical_strength"]
    for col in cols:
        plt.figure(figsize=(14, 8))
        sns.scatterplot(data=df_sub, x="timestamp", y=col,
                        hue="passorfail", palette={0:"blue", 1:"red"},
                        s=10, alpha=0.6)
        plt.title(f"[불량 강조] {col} vs passorfail (mold_code={mold_code})")
        plt.xlabel("Timestamp")
        plt.ylabel(col)
        plt.legend(title="Pass/Fail", loc="upper left", bbox_to_anchor=(1.02, 1))
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.show()

plot_mold_trend(df_selected, mold_code=8412, freq="1h")

df_selected.head()
### 특정 날짜 시계열 데이터 분석
targets = {
    8412: ("2019-01-11", "2019-01-12"),
    8573: ("2019-01-03", "2019-01-03"),
    8600: ("2019-01-26", "2019-01-26"),
    8722: ("2019-01-25", "2019-01-25"),
    8917: ("2019-01-24", "2019-01-24"),
}

# 컬럼별 색상 고정 팔레트
color_map = {
    "sleeve_temperature": "blue",
    "Coolant_temperature": "green",
    "physical_strength": "red"
}

for mc, (start, end) in targets.items():
    mask = (
        (df_selected["mold_code"] == mc) &
        (df_selected["timestamp"].dt.date >= pd.to_datetime(start).date()) &
        (df_selected["timestamp"].dt.date <= pd.to_datetime(end).date())
    )
    df_sub = df_selected[mask]

    if df_sub.empty:
        print(f"mold_code={mc}, {start}~{end} 데이터 없음")
        continue

    print(f"=== mold_code: {mc}, 기간: {start} ~ {end} ===")
    for col in cols:
        fig, ax1 = plt.subplots(figsize=(14,6))

        # 센서 데이터 (왼쪽 y축)
        sns.lineplot(
            data=df_sub, x="timestamp", y=col,
            linewidth=0.8, alpha=0.8, color=color_map.get(col, "gray"), ax=ax1
        )
        ax1.set_ylabel(col, color=color_map.get(col, "gray"))
        ax1.tick_params(axis="y", labelcolor=color_map.get(col, "gray"))
        ax1.grid(alpha=0.3)

        # count (오른쪽 y축)
        ax2 = ax1.twinx()
        sns.lineplot(
            data=df_sub, x="timestamp", y="count",
            linewidth=0.8, alpha=0.7, color="orange", ax=ax2
        )
        ax2.set_ylabel("Count", color="orange")
        ax2.tick_params(axis="y", labelcolor="orange")

        # 타이틀
        plt.title(f"{col} + Count 시계열 (mold_code={mc}, {start}~{end})")
        fig.tight_layout()
        plt.show()
        

for col in cols:
    fig, axes = plt.subplots(2, 1, figsize=(14,8), sharex=True)

    # Pass
    sns.lineplot(
        data=df_selected[df_selected["passorfail"] == 0],
        x="timestamp", y=col,
        linewidth=0.6, alpha=0.7,
        color=color_map[col], ax=axes[0]
    )
    axes[0].set_title(f"{col} - Pass (전체 데이터)")
    axes[0].grid(alpha=0.3)

    # Fail
    sns.lineplot(
        data=df_selected[df_selected["passorfail"] == 1],
        x="timestamp", y=col,
        linewidth=0.8, alpha=0.9,
        color=color_map[col], ax=axes[1]
    )
    axes[1].set_title(f"{col} - Fail (전체 데이터)")
    axes[1].grid(alpha=0.3)

    plt.xlabel("Timestamp")
    plt.tight_layout()
    plt.show()



# mold_code별 Pass/Fail 갯수
count_df = pd.crosstab(
    df_selected["mold_code"],
    df_selected["passorfail"]
)

count_df.columns = ["Pass(0)", "Fail(1)"]

# mold_code별 Pass/Fail 비율
ratio_df = pd.crosstab(
    df_selected["mold_code"],
    df_selected["passorfail"],
    normalize="index"
)
ratio_df.columns = ["Pass(0)", "Fail(1)"]

# --- 시각화 (2개 subplot) ---
fig, axes = plt.subplots(1, 2, figsize=(14,6))

# ① 절대 갯수
count_df.plot(
    kind="bar", stacked=True,
    color=["steelblue", "tomato"],
    ax=axes[0], alpha=0.85
)
axes[0].set_title("Mold Code별 Pass/Fail 갯수")
axes[0].set_xlabel("Mold Code")
axes[0].set_ylabel("샘플 수")
axes[0].grid(axis="y", alpha=0.3)

# ② 비율
ratio_df.plot(
    kind="bar", stacked=True,
    color=["steelblue", "tomato"],
    ax=axes[1], alpha=0.85
)
axes[1].set_title("Mold Code별 Pass/Fail 비율")
axes[1].set_xlabel("Mold Code")
axes[1].set_ylabel("비율")
axes[1].grid(axis="y", alpha=0.3)

plt.tight_layout()
plt.show()
        
# 큰 그림 먼저: 전체 추세/주기성을 먼저 본다.
# 비교하기: mold_code, passorfail 등 그룹별 차이를 비교한다.
# 줌인하기: 특정 날/시간에 이상한 패턴이 보이면 그 날을 따로 뽑아서 확인한다.
# 도메인 연결: 현장의 맥락(작업 교대, 주말 휴무, 설비 정지 등)과 연결지어 해석한다

# ==========================================================
# 📌 시계열 데이터 해석 프레임워크 (EDA 가이드)
# ==========================================================
# 1) 추세 (Trend)
#    - 시간이 지남에 따라 값이 증가/감소하는 경향이 있는지 확인
#    - 예: 장비 온도가 꾸준히 상승 → 과열 문제 가능
#    - 확인 방법: 전체 라인 플롯, 주 단위 평균 그래프

# 2) 주기성 (Seasonality)
#    - 하루(24시간), 주간(요일), 월별 등 주기적으로 반복되는 패턴이 있는지 확인
#    - 예: 교대 시간대마다 온도 하락, 주말마다 생산량 감소
#    - 확인 방법: 시간(hour), 요일(weekday) 단위 집계/시각화

# 3) 변동성 (Volatility)
#    - 값의 변동 폭이 일정한지, 아니면 불안정하게 흔들리는지 확인
#    - 변동이 크면 공정 불안정/센서 이상 가능성
#    - 확인 방법: 표준편차 계산, 시계열 라인플롯의 진폭 관찰

# 4) 이상치 (Outlier / Anomaly)
#    - 특정 시점에 갑자기 튀는 값(peak, drop)이 있는지 확인
#    - 예: 물리적 강도가 순간적으로 급락 후 불량률 증가
#    - 확인 방법: Boxplot, Scatterplot, 시계열에서 급격한 변동 탐지

# 5) 그룹별 차이 (Group Difference)
#    - mold_code, passorfail 등 그룹별로 시계열 양상이 다른지 확인
#    - 예: 특정 mold_code는 특정 시간대에 불량률 ↑
#    - 확인 방법: hue 옵션으로 그룹 구분 시각화, 교차분석
# ==========================================================

