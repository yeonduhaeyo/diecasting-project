
#안녕하세요 관리 PM을 맡게된 임지원입니다. 

# 오늘 할일:
# 데이터 각 변수들 분포 확인, 갯수 확인 -> 특성확인
# 변수간 관계 확인
# 합불량 그룹간 차이 확인
# 보고서를 작성한다는 생각으로 정리할것

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv("./data/train.csv")
df

### Data EDA
# 데이터 크기 및 기본 정보
print(df.shape)
print(df.info())
print(df.describe(include="all"))

# 결측치 확인
print(df.isnull().sum())


df_num = df.select_dtypes("number").columns
df_cat = df.select_dtypes("object").columns

df_num
df_cat

### 수치형 변수 확인
# 히스토그램
df[df_num].hist(figsize=(12, 10), bins=30)
plt.tight_layout()
plt.show()

# 박스플롯으로 이상치 확인
plt.figure(figsize=(12, 6))
sns.boxplot(data=df[df_num])
plt.xticks(rotation=90)
plt.show()

### 범주형 변수 분포 확인
for col in df_cat:
    plt.figure(figsize=(8, 5))
    order = df[col].value_counts().index
    sns.countplot(data=df, x=col, order=order, palette="Set2")
    plt.title(f"{col} 값 분포")
    plt.xticks(rotation=45)
    plt.show()
        

df_cat
