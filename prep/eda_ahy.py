import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ---------------- 0) 데이터 로드 & 기본 정리 ----------------
train = pd.read_csv('./Project5/train.csv')



train['low_section_speed'].describe()
train['high_section_speed'].describe()

#이상값가 nan값 찾기
# 원값 보존
s_raw = pd.to_numeric(train['low_section_speed'], errors='coerce')

# 마스크
mask_high = s_raw >= 1000
mask_nan  = s_raw.isna()

# id와 인덱스 추출
ids_high = train.loc[mask_high, 'id']
ids_nan  = train.loc[mask_nan,  'id']
idx_high = train.index[mask_high]
idx_nan  = train.index[mask_nan]

# 확인
print(">=1000 개수:", mask_high.sum())
print("NaN 개수   :", mask_nan.sum())
print("예시(>=1000):\n", train.loc[mask_high, ['id','low_section_speed']].head())
print("예시(NaN):\n",    train.loc[mask_nan,  ['id','low_section_speed']].head())


### 꺼내고 제거하기


# 숫자형으로 안전 변환
s = pd.to_numeric(train['low_section_speed'], errors='coerce')

# 1000 이상 마스크
mask = s >= 1000

# (대체에 사용할) 중앙값: 1000 미만 값들로 계산
median_valid = s[~mask].median(skipna=True)

# 대체 수행
s.loc[mask] = median_valid

# 원본 데이터프레임에 반영
train['low_section_speed'] = s

# 결과 요약
print("대체에 사용한 중앙값:", median_valid)
print("1000 이상이었던 개수:", mask.sum())
print("\n수정된 low_section_speed describe():")
print(train['low_section_speed'].describe().to_string())

### fail 값만

# 숫자형 변환 + diff 파생
for c in ["low_section_speed", "high_section_speed", "count", "mold_code", "passorfail"]:
    train[c] = pd.to_numeric(train[c], errors="coerce")
train["diff"] = train["high_section_speed"] - train["low_section_speed"]

# 불량 라벨 정리(0/1)
train["passorfail"] = train["passorfail"].round().astype("Int64")

# 분석할 mold_code 5종 (원하던 리스트)
codes = [8917, 8722, 8412, 8573, 8600]
yvars = ["low_section_speed", "high_section_speed", "diff"]

# 관심 데이터만
df = train[train["mold_code"].isin(codes)].copy()

# 5×3 서브플롯
fig, axes = plt.subplots(nrows=len(codes), ncols=len(yvars), figsize=(24, 16))
if len(codes) == 1 and len(yvars) == 1:
    axes = np.array([[axes]])
elif len(codes) == 1:
    axes = np.array([axes])
elif len(yvars) == 1:
    axes = axes[:, np.newaxis]

for i, code in enumerate(codes):
    sub = df[df["mold_code"] == code]

    for j, y in enumerate(yvars):
        ax = axes[i, j]

        # 결측 제거(해당 y, count, passorfail 모두 유효한 행만)
        tmp = sub[["count", y, "passorfail"]].dropna()
        if tmp.empty:
            ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
            ax.set_title(f"mold_code={code} | {y}")
            ax.set_xlabel("count"); ax.set_ylabel(y)
            continue

        # 불량/양품 분리
        fail = tmp[tmp["passorfail"] == 1]
        ok   = tmp[tmp["passorfail"] == 0]

        # 배경으로 양품(연한 회색), 위에 불량(빨강)만 강조
        if not ok.empty:
            ax.scatter(ok["count"].values, ok[y].values, s=6, alpha=0.25)     # 기본색(연한 회색 느낌)
        if not fail.empty:
            ax.scatter(fail["count"].values, fail[y].values, s=12, alpha=0.9, c="red")

        if fail.empty:
            ax.text(0.5, 0.5, "No fail", ha="center", va="center", transform=ax.transAxes)

        ax.set_title(f"mold_code={code} | {y}")
        ax.set_xlabel("count"); ax.set_ylabel(y)

plt.tight_layout()
plt.show()

# (옵션) 불량 개수 요약도 같이 확인
summary = (df[["mold_code","count","low_section_speed","high_section_speed","diff","passorfail"]]
           .dropna()
           .assign(is_fail=lambda d: d["passorfail"]==1)
           .groupby("mold_code")["is_fail"].sum()
           .rename("fail_count"))
print("\nFail count by mold_code:")
print(summary.to_string())

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ---------- 0) 기본 정리 ----------
df = train.copy()

# passorfail 숫자화(0/1)
df['passorfail'] = pd.to_numeric(df['passorfail'], errors='coerce').round().astype('Int64')

# tryshot_signal: 'D'면 D, 아니면 NaN(라벨은 문자열 'NaN'로 통일해 plotting 편하게)
raw = df.get('tryshot_signal', pd.Series(index=df.index, dtype=object)).astype(str).str.strip()
is_D = raw.str.upper().eq('D')
df['tryshot_signal_clean'] = np.where(is_D, 'D', 'NaN')   # 'D' / 'NaN' 라벨

# 분석 대상 mold_code 5종 (원하면 자동 상위 5개로 변경 가능)
codes = [8917, 8722, 8412, 8573, 8600]

# 숫자형 변환
df['mold_code'] = pd.to_numeric(df['mold_code'], errors='coerce').astype('Int64')

# ---------- 1) 불량률 계산 함수 ----------
def fail_rate_by_tryshot(sub: pd.DataFrame) -> pd.DataFrame:
    """sub: 단일 mold_code 데이터프레임"""
    tmp = sub[['tryshot_signal_clean','passorfail']].dropna()
    if tmp.empty:
        return pd.DataFrame({'tryshot_signal_clean':['D','NaN'], 'fail_rate':[np.nan, np.nan], 'n':[0,0]})
    g = (tmp
         .assign(fail=lambda d: (d['passorfail']==1).astype(int))
         .groupby('tryshot_signal_clean', as_index=False)
         .agg(n=('fail','count'), fail=('fail','sum')))
    g['fail_rate'] = g['fail'] / g['n']
    # D/NaN 두 축이 항상 보이도록 보정
    g = g.set_index('tryshot_signal_clean').reindex(['D','NaN'])
    g['n'] = g['n'].fillna(0).astype(int)
    g['fail_rate'] = g['fail_rate']  # NaN 유지 허용
    return g.reset_index()

# ---------- 2) 플롯: 5개의 서브플롯 ----------
fig, axes = plt.subplots(nrows=1, ncols=5, figsize=(18, 3.8))  # 가로로 5개
if isinstance(axes, np.ndarray) and axes.ndim == 1:
    axes = axes
else:
    axes = np.array([axes])

for ax, code in zip(axes, codes):
    sub = df[df['mold_code'] == code].copy()
    res = fail_rate_by_tryshot(sub)
    # 막대그래프 (x: ['D','NaN'], y: fail_rate)
    x = res['tryshot_signal_clean'].tolist()
    y = res['fail_rate'].values.astype(float)
    ax.bar(x, y)  # 색 지정 없음(기본)
    ax.set_ylim(0, 1)  # 불량률 0~1
    ax.set_title(f"mold_code = {code}")
    ax.set_xlabel("tryshot_signal")
    ax.set_ylabel("fail_rate")
    # 샘플 수 주석
    for xi, yi, ni in zip(x, y, res['n']):
        if np.isfinite(yi):
            ax.text(xi, yi + 0.02, f"n={ni}", ha='center', va='bottom', fontsize=9)
        else:
            ax.text(xi, 0.02, f"n={ni}", ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.show()





