# viz/preprocess_plots.py
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

from shared import name_map_kor

def plot_data_types(train_df):
    """데이터 타입별 변수 개수 시각화"""
    fig, ax = plt.subplots(figsize=(8, 5))
    
    type_counts = train_df.dtypes.value_counts()
    colors = sns.color_palette("Set2", len(type_counts))
    
    ax.bar(range(len(type_counts)), type_counts.values, color=colors)
    ax.set_xticks(range(len(type_counts)))
    ax.set_xticklabels([str(t) for t in type_counts.index], rotation=45, ha='right')
    ax.set_ylabel('변수 개수')
    ax.set_title('데이터 타입별 변수 분포')
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    return fig

def plot_missing_overview(train_df):
    """결측치 상위 10개 변수만 시각화 (한글 컬럼명, 내림차순 위에서 아래로)"""
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # 결측치 개수 계산
    missing = train_df.isnull().sum()
    missing = missing[missing > 0].sort_values(ascending=False).head(10)
    
    if len(missing) > 0:
        # 순서 뒤집기 (큰 값이 위로 오게)
        missing = missing[::-1]
        
        # ✅ 한글 이름 매핑 적용
        labels_kor = [name_map_kor.get(col, col) for col in missing.index]
        
        ax.barh(range(len(missing)), missing.values, color='coral')
        ax.set_yticks(range(len(missing)))
        ax.set_yticklabels(labels_kor, fontsize=10)
        ax.set_xlabel('결측치 개수')
        ax.set_title('결측치 상위 10개 변수')
        ax.grid(axis='x', alpha=0.3)
    else:
        ax.text(0.5, 0.5, '결측치 없음', ha='center', va='center', fontsize=14)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
    
    plt.tight_layout()
    return fig


def plot_target_distribution(train_df, target_col='passorfail'):
    """타겟 변수 분포 시각화 (0=Pass, 1=Fail 기준)"""

    fig, ax = plt.subplots(figsize=(6, 5))

    if target_col in train_df.columns:
        # ✅ 카테고리로 변환 (항상 0,1 두 개 레벨 유지)
        categories = pd.CategoricalDtype(categories=[0, 1], ordered=True)
        target = train_df[target_col].astype(categories)

        target_counts = target.value_counts().sort_index()

        labels = ['Pass (정상)', 'Fail (불량)']
        colors = ['#2ecc71', '#e74c3c']  # 초록, 빨강

        # ✅ 막대 그리기
        bars = ax.bar(range(len(target_counts)), target_counts.values, color=colors)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels([
            f'{labels[i]}\n({cnt:,}개, {cnt/len(train_df)*100:.1f}%)'
            for i, cnt in enumerate(target_counts.values)
        ])
        ax.set_ylabel('샘플 개수')
        ax.set_title(f'{target_col} 변수 분포')
        ax.grid(axis='y', alpha=0.3)

        # ✅ 막대 위 값 표시
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2., height,
                    f'{int(height):,}', ha='center', va='bottom')
    else:
        ax.text(0.5, 0.5, f'{target_col} 컬럼을 찾을 수 없습니다',
                ha='center', va='center', fontsize=14)

    plt.tight_layout()
    return fig
