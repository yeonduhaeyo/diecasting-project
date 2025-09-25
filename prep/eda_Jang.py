import pandas as pd
import numpy as np

df = pd.read_csv('./data/train1.csv')
df.info()
df.columns
df.head(10000)
df.loc[df["weekday"] == 5]
# 19327에 있는 행 결측치 1개씩 존재, 근데 passorfail은 양품판정.

# line		작업 라인(전자교반 3라인 2호기)	
# name		제품명(TM Carrier RH) , 변속기용 캐리어 부품(우측)
# mold_name	금형명(TM Carrier RH-Semi-Solid DIE-06)
# time		수집 시간 
# date		수집 일자	(2019-01-02 ~ 2019-03-12), 2019년 1월13일,2019년 2월 4,5,6 제외
# count		일자별 생산 번호	
# working	가동 여부	(가동,정지,nan) 결측치 : 1
# emergency_stop	비상 정지 여부	(ON,nan) 결측치 : 1
# molten_temp	용탕 온도 (0,70,7,71,72,73,nan) 결측치 : 2,261
# facility_operation_CycleTime	설비 작동 사이클 시간 
# production_CycleTime	제품 생산 사이클 시간	
# low_section_speed		저속 구간 속도	, 결측치 : 1
# high_section_speed		고속 구간 속도	, 결측치 : 1
# molten_volume		용탕량	, 결측치 : 34,992
# cast_pressure		주조 압력	, 결측치: 1
# biscuit_thickness		비스켓 두께	, 결측치 : 1
# upper_mold_temp1 	상금형 온도1, 결측치:1 	
# upper_mold_temp2 	상금형 온도2 , 결측치:1 	
# upper_mold_temp3 	상금형 온도3 , 결측치:313 	
# lower_mold_temp1 	하금형 온도1 , 결측치:1	
# lower_mold_temp2 	하금형 온도2 , 결측치:1	
# lower_mold_temp3 	하금형 온도3 , 결측치:313	
# sleeve_temperature	슬리브 온도	, 결측치 : 1
# physical_strength		형체력 , 결측치 : 1
# Coolant_temperature	냉각수 온도	, 결측치 : 1
# EMS_operation_time	전자교반 가동 시간 ([23, 25,  0,  3,  6]) 
# registration_time		등록 일시	
# passorfail			양품/불량 판정 (0: 양품, 1: 불량)	
# tryshot_signal		사탕 신호 ([nan, 'D']) , 결측치 : 72,368
# mold_code			    금형 코드 ([8722, 8412, 8573, 8917, 8600])
# heating_furnace		가열로 구분	([nan, 'B', 'A']) , 결측치 : 40,881

import matplotlib.pyplot as plt
import seaborn as sns

# 숫자형 / 범주형 분리
num_cols = df.select_dtypes(include=['int64','float64']).columns
cat_cols = df.select_dtypes(include=['object']).columns

# 숫자형 변수 분포 (히스토그램)
for col in num_cols:
    plt.figure(figsize=(6,4))
    sns.histplot(df[col].dropna(), bins=50, kde=True)
    plt.title(f"Distribution of {col}")
    plt.show()

# 범주형 변수 분포 (막대그래프)
for col in cat_cols:
    plt.figure(figsize=(6,4))
    sns.countplot(y=df[col])
    plt.title(f"Count of {col}")
    plt.show()


df.head()
df["mold_name"].unique()
df['molten_volume'].unique()


# -------------------------------------------------------------------------
# 연속형 변수 분포 확인
import matplotlib.pyplot as plt
import seaborn as sns

# 숫자형 변수만 선택
num_cols = df.select_dtypes(include=['int64','float64']).columns

# 시각화
for col in num_cols:
    plt.figure(figsize=(6,4))
    sns.histplot(df[col].dropna(), bins=50, kde=True)  # kde=True → 분포 곡선
    plt.title(f"Distribution of {col}")
    plt.xlabel(col)
    plt.ylabel("Count")
    plt.show()


df.info()

# 결측치가 있는 행 번호 찾기
missing_idx = df[
    (df['working'].isna()) |
    (df['emergency_stop'].isna()) |
    (df['low_section_speed'].isna()) |
    (df['high_section_speed'].isna()) |
    (df['cast_pressure'].isna()) |
    (df['biscuit_thickness'].isna()) |
    (df['upper_mold_temp1'].isna()) |
    (df['upper_mold_temp2'].isna()) |
    (df['lower_mold_temp1'].isna()) |
    (df['lower_mold_temp2'].isna()) |
    (df['sleeve_temperature'].isna()) |
    (df['physical_strength'].isna()) |
    (df['Coolant_temperature'].isna())
].index

print("결측치가 있는 행:", missing_idx)

# 그 행 전체 값 확인
df.loc[missing_idx]

# ---------------------------------------------------------------------------------------

import pandas as pd

# 주요 연속형 변수
features = [
    "molten_temp", "cast_pressure", "biscuit_thickness",
    "upper_mold_temp1","upper_mold_temp2","upper_mold_temp3",
    "lower_mold_temp1","lower_mold_temp2","lower_mold_temp3",
    "sleeve_temperature","physical_strength",
    "Coolant_temperature","EMS_operation_time"
]

# 그룹별 평균 비교
df_grouped = df.groupby("passorfail")[features].mean().T
df_grouped.columns = ["양품(0)", "불량(1)"]
print(df_grouped)

# -------------------------------------------------------------------
import matplotlib.pyplot as plt
import seaborn as sns

for col in features:
    plt.figure(figsize=(6,4))
    sns.boxplot(x="passorfail", y=col, data=df)
    plt.title(f"{col} vs PassOrFail")
    plt.show()

df["cast_pressure"]

# ----------------------------------------------------------
corr = df[features + ["passorfail"]].corr()
plt.figure(figsize=(10,8))
sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f")
plt.title("Correlation with PassOrFail")
plt.show()


# -------------------------------------------------------------
import matplotlib.pyplot as plt
import seaborn as sns

plt.figure(figsize=(7,5))
sns.scatterplot(
    x="cast_pressure", 
    y="biscuit_thickness", 
    hue="passorfail", 
    data=df, 
    alpha=0.5,
    palette={0:"blue", 1:"red"}  # 0=양품(파랑), 1=불량(빨강)
)
plt.title("Cast Pressure vs Biscuit Thickness by PassOrFail")
plt.xlabel("Cast Pressure")
plt.ylabel("Biscuit Thickness")
plt.legend(title="Pass/Fail", labels=["Good(0)","Fail(1)"])
plt.show()

# --------------------------------------------------------------------
# molten_volume 결측 여부 컬럼 추가
df["molten_volume_isnull"] = df["molten_volume"].isna().astype(int)

# 라인별 결측 비율
print(df.groupby("line")["molten_volume_isnull"].mean())

# 금형별 결측 비율
print(df.groupby("mold_code")["molten_volume_isnull"].mean())

# 날짜별 결측 비율
print(df.groupby("date")["molten_volume_isnull"].mean())


# EMS 시간별 불량률 계산
ems_fail_rate = df.groupby("EMS_operation_time")["passorfail"].mean()

print("EMS_operation_time 별 불량률")
print(ems_fail_rate)

# -----------------------------------------------------------------------------------------------------

# cast_pressure
# biscuit_thickness
# EMS_operation_time 

# 데이터 분포, 이상치 전부 상세히 확인해봐야할듯

# [각 변수별 공통 확인항목]

# *각 변수별로 시게열그래프 작성 (시계열로 주기성)

# *히스토그램 그려보기(분포도 확인)

# *양품일 때, 불량일 때 데이터 나눠서 서브플랏 그려보기

# 1. cast_pressure (압력)

df["cast_pressure"]

df["day"]
df["weekday"]
df["month"]

import matplotlib.pyplot as plt
import seaborn as sns

plt.figure(figsize=(7,5))
sns.histplot(df["cast_pressure"].dropna(), bins=50, kde=True)
plt.title("Distribution of Cast Pressure")
plt.xlabel("Cast Pressure")
plt.ylabel("Count")
plt.show()

# 일(day) 단위 평균
import matplotlib.pyplot as plt
import seaborn as sns

plt.figure(figsize=(14,6))
sns.lineplot(data=df, x="day", y="cast_pressure", hue="mold_code", estimator="mean", ci=None)
plt.title("Average Cast Pressure by Day (per Mold Code)")
plt.xlabel("Day")
plt.ylabel("Cast Pressure")
plt.legend(title="Mold Code")
plt.show()


# 요일(weekday) 단위 평균

plt.figure(figsize=(10,5))
sns.barplot(data=df, x="weekday", y="cast_pressure", hue="mold_code", estimator="mean", ci=None)
plt.title("Average Cast Pressure by Weekday (per Mold Code)")
plt.xlabel("Weekday (0=Mon ... 6=Sun)")
plt.ylabel("Cast Pressure")
plt.legend(title="Mold Code")
plt.show()



# 월(month) 단위 평균

plt.figure(figsize=(8,5))
sns.barplot(data=df, x="month", y="cast_pressure", hue="mold_code", estimator="mean", ci=None)
plt.title("Average Cast Pressure by Month (per Mold Code)")
plt.xlabel("Month")
plt.ylabel("Cast Pressure")
plt.legend(title="Mold Code")
plt.show()


import seaborn as sns
import matplotlib.pyplot as plt

g = sns.FacetGrid(df, col="mold_code", col_wrap=3, height=4, sharey=True)
g.map_dataframe(sns.lineplot, x="count", y="cast_pressure", hue="day", estimator="mean", ci=None)
g.add_legend()
g.set_axis_labels("Count", "Cast Pressure")
g.set_titles("Mold Code {col_name}")
plt.show()

import matplotlib.pyplot as plt
import seaborn as sns

# 조건별 데이터 필터링
df_filtered = df[
    ((df["mold_code"] == 8412) & (df["date"].between("2019-01-11","2019-01-12"))) |
    ((df["mold_code"] == 8573) & (df["date"] == "2019-01-03")) |
    ((df["mold_code"] == 8600) & (df["date"] == "2019-01-26")) |
    ((df["mold_code"] == 8722) & (df["date"] == "2019-01-25")) |
    ((df["mold_code"] == 8917) & (df["date"] == "2019-01-24"))
]

# FacetGrid: 금형별 작은 그래프
g = sns.FacetGrid(df_filtered, col="mold_code", col_wrap=3, height=4, sharey=False)

# 파란 라인: 전체 압력 추세
g.map_dataframe(sns.lineplot, x="count", y="cast_pressure", color="steelblue")

# 빨간 점: 불량만 표시
def add_fail_scatter(data, **kwargs):
    fail_points = data[data["passorfail"] == 1]
    plt.scatter(fail_points["count"], fail_points["cast_pressure"], color="red", s=30, label="Fail")

g.map_dataframe(add_fail_scatter)

g.set_axis_labels("Count", "Cast Pressure")
g.set_titles("Mold Code {col_name}")
plt.legend(loc="upper right")
plt.show()

import matplotlib.pyplot as plt
import seaborn as sns

# 조건 + cast_pressure >= 300 필터링
df_filtered = df[
    (
        ((df["mold_code"] == 8412) & (df["date"].between("2019-01-11","2019-01-12"))) |
        ((df["mold_code"] == 8573) & (df["date"] == "2019-01-03")) |
        ((df["mold_code"] == 8600) & (df["date"] == "2019-01-26")) |
        ((df["mold_code"] == 8722) & (df["date"] == "2019-01-25")) |
        ((df["mold_code"] == 8917) & (df["date"] == "2019-01-24"))
    )
    & (df["cast_pressure"] >= 300)   # 🔹 압력 300 이상만
]

# FacetGrid: 금형별 작은 그래프
g = sns.FacetGrid(df_filtered, col="mold_code", col_wrap=3, height=4, sharey=False)

# 파란 라인: 전체 주조 압력 추세
g.map_dataframe(sns.lineplot, x="count", y="cast_pressure", color="steelblue")

# 빨간 점: 불량만 표시
def add_fail_scatter(data, **kwargs):
    fail_points = data[data["passorfail"] == 1]
    plt.scatter(fail_points["count"], fail_points["cast_pressure"],
                color="red", s=30, label="Fail")

g.map_dataframe(add_fail_scatter)

g.set_axis_labels("Count", "Cast Pressure")
g.set_titles("Mold Code {col_name}")
plt.legend(loc="upper right")
plt.show()


import matplotlib.pyplot as plt
import seaborn as sns

# 분석 조건
conditions = {
    8412: ("2019-01-11", "2019-01-12"),
    8573: ("2019-01-03", "2019-01-03"),
    8600: ("2019-01-26", "2019-01-26"),
    8722: ("2019-01-25", "2019-01-25"),
    8917: ("2019-01-24", "2019-01-24"),
}

for mold, (start, end) in conditions.items():
    # mold_code + 날짜 범위 + cast_pressure ≥ 300 필터링
    df_sel = df[
        (df["mold_code"] == mold) &
        (df["date"].between(start, end)) &
        (df["cast_pressure"] >= 300)
    ]
    
    # 시각화
    plt.figure(figsize=(12,5))
    sns.lineplot(data=df_sel, x="count", y="cast_pressure", color="steelblue", label="Cast Pressure")
    
    # 불량점 표시
    fail_points = df_sel[df_sel["passorfail"] == 1]
    plt.scatter(fail_points["count"], fail_points["cast_pressure"], color="red", s=30, label="Fail")
    
    plt.title(f"Cast Pressure by Count (Mold Code {mold}, {start}~{end})")
    plt.xlabel("Count (Production Sequence)")
    plt.ylabel("Cast Pressure")
    plt.legend()
    plt.grid(True)
    plt.show()


# 2. biscuit_thickness

plt.figure(figsize=(8,5))
sns.histplot(
    data=df,
    x="biscuit_thickness",
    hue="passorfail",
    bins=50,
    kde=False,
    palette={0:"blue", 1:"red"},
    alpha=0.6,
    multiple="layer"
)

plt.yscale("log")   # y축 로그 스케일
plt.title("Biscuit Thickness Distribution by Pass/Fail (Log Scale)")
plt.xlabel("Biscuit Thickness")
plt.ylabel("Count (log scale)")
plt.legend(title="Pass/Fail", labels=["Fail (1)", "Good (0)"])
plt.show()

# 3. EMS_operation_time 
df["EMS_operation_time"].unique()

plt.figure(figsize=(8,5))
sns.histplot(
    data=df,
    x="EMS_operation_time",
    hue="passorfail",
    multiple="dodge",   # 양품/불량 막대를 나란히 비교
    shrink=0.8,
    palette={0:"blue", 1:"red"}
)

plt.title("EMS Operation Time Distribution by Pass/Fail")
plt.xlabel("EMS Operation Time")
plt.ylabel("Count")
plt.show()

plt.figure(figsize=(8,5))
sns.histplot(
    data=df,
    x="EMS_operation_time",
    hue="passorfail",
    multiple="dodge",
    shrink=0.8,
    palette={0:"blue", 1:"red"}
)

plt.yscale("log")  # y축 로그 스케일
plt.title("EMS Operation Time Distribution by Pass/Fail (Log Scale)")
plt.xlabel("EMS Operation Time")
plt.ylabel("Count (log scale)")
plt.show()

# --------------------------------------------------------------------------

import matplotlib.pyplot as plt
import seaborn as sns

# 조건 정의 (mold_code: (start_date, end_date))
conditions = {
    8412: ("2019-01-11", "2019-01-12"),
    8573: ("2019-01-03", "2019-01-03"),
    8600: ("2019-01-26", "2019-01-26"),
    8722: ("2019-01-25", "2019-01-25"),
    8917: ("2019-01-24", "2019-01-24"),
}

# mold_code별 개별 시각화
for mold, (start, end) in conditions.items():
    df_sel = df[
        (df["mold_code"] == mold) &
        (df["date"].between(start, end))
    ]
    
    plt.figure(figsize=(12,5))
    sns.lineplot(data=df_sel, x="count", y="biscuit_thickness", color="teal", label="Biscuit Thickness")
    
    # 불량만 빨간 점으로 표시
    fail_points = df_sel[df_sel["passorfail"] == 1]
    plt.scatter(fail_points["count"], fail_points["biscuit_thickness"], color="red", s=30, label="Fail")
    
    plt.title(f"Biscuit Thickness by Count (Mold Code {mold}, {start}~{end})")
    plt.xlabel("Count (Production Sequence)")
    plt.ylabel("Biscuit Thickness")
    plt.legend()
    plt.grid(True)
    plt.show()

# ----------------------------------------------------------------------------------------

import matplotlib.pyplot as plt
import seaborn as sns

# 조건 정의 (mold_code: (start_date, end_date))
conditions = {
    8412: ("2019-01-11", "2019-01-12"),
    8573: ("2019-01-03", "2019-01-03"),
    8600: ("2019-01-26", "2019-01-26"),
    8722: ("2019-01-25", "2019-01-25"),
    8917: ("2019-01-24", "2019-01-24"),
}

# mold_code별 개별 시각화
for mold, (start, end) in conditions.items():
    df_sel = df[
        (df["mold_code"] == mold) &
        (df["date"].between(start, end))
    ]
    
    plt.figure(figsize=(12,5))
    sns.lineplot(data=df_sel, x="count", y="EMS_operation_time", color="purple", label="EMS Operation Time")
    
    # 불량만 빨간 점으로 표시
    fail_points = df_sel[df_sel["passorfail"] == 1]
    plt.scatter(fail_points["count"], fail_points["EMS_operation_time"], color="red", s=30, label="Fail")
    
    plt.title(f"EMS Operation Time by Count (Mold Code {mold}, {start}~{end})")
    plt.xlabel("Count (Production Sequence)")
    plt.ylabel("EMS Operation Time")
    plt.legend()
    plt.grid(True)
    plt.show()

# ------------------------------------------------------------------------------
import seaborn as sns
import matplotlib.pyplot as plt

# molten_volume & biscuit_thickness 둘 다 결측 없는 행만 추출
df_mv_bt = df[["molten_volume", "biscuit_thickness", "passorfail"]].dropna()

# 전체 상관계수
corr_total = df_mv_bt[["molten_volume", "biscuit_thickness"]].corr().iloc[0,1]

# 그룹별 상관계수
corr_by_group = df_mv_bt.groupby("passorfail")[["molten_volume", "biscuit_thickness"]].corr().iloc[0::2,-1]

print("전체 상관계수:", corr_total)
print("\n불량/양품 그룹별 상관계수:")
print(corr_by_group)

# 시각화
plt.figure(figsize=(7,5))
sns.scatterplot(
    data=df_mv_bt,
    x="molten_volume",
    y="biscuit_thickness",
    hue="passorfail",
    alpha=0.5,
    palette={0:"blue", 1:"red"}
)
plt.title(f"Molten Volume vs Biscuit Thickness\nTotal Corr={corr_total:.2f}")
plt.xlabel("Molten Volume")
plt.ylabel("Biscuit Thickness")
plt.legend(title="Pass/Fail")
plt.show()

# 선택할 컬럼 리스트
cols = [
    "line", "name", "mold_name", "time", "date", "count", "working", "emergency_stop",
    "molten_temp", "facility_operation_CycleTime", "production_CycleTime",
    "low_section_speed", "high_section_speed", "molten_volume", "cast_pressure",
    "biscuit_thickness", "upper_mold_temp1", "upper_mold_temp2", "upper_mold_temp3",
    "lower_mold_temp1", "lower_mold_temp2", "lower_mold_temp3", "sleeve_temperature",
    "physical_strength", "Coolant_temperature", "EMS_operation_time", "registration_time",
    "passorfail", "tryshot_signal", "mold_code", "heating_furnace"
]

# 해당 컬럼만 추출
df_selected = df[cols]

# CSV 파일로 저장
output_path = "./selected_variables3.csv"
df_selected.to_csv(output_path, index=False, encoding="utf-8-sig")

print(f"CSV 파일이 저장되었습니다: {output_path}")


# cast_pressure
# biscuit_thickness
# EMS_operation_time 

df["cast_pressure"].isna().sum()
df["biscuit_thickness"].isna().sum()
df["EMS_operation_time"].isna().sum()

import pandas as pd

# train 데이터 불러오기
train = pd.read_csv("data\\test1.csv")

# 모든 칼럼 정의
all_columns = [
    "line", "name", "mold_name", "time", "date", "count", "working", "emergency_stop",
    "molten_temp", "facility_operation_CycleTime", "production_CycleTime",
    "low_section_speed", "high_section_speed", "molten_volume", "cast_pressure",
    "biscuit_thickness", "upper_mold_temp1", "upper_mold_temp2", "upper_mold_temp3",
    "lower_mold_temp1", "lower_mold_temp2", "lower_mold_temp3", "sleeve_temperature",
    "physical_strength", "Coolant_temperature", "EMS_operation_time", "registration_time",
    "passorfail", "tryshot_signal", "mold_code", "heating_furnace"
]

# 누락된 칼럼이 있으면 빈 값으로 추가
for col in all_columns:
    if col not in train.columns:
        train[col] = ""

# 칼럼 순서 맞추기
train = train[all_columns]

# NaN → 빈칸("")으로 변환
train = train.fillna("")

# CSV 저장
train.to_csv("casting_process_train_all_columns.csv", index=False, encoding="utf-8-sig")

print("CSV 파일 생성 완료: casting_process_train_all_columns.csv")



