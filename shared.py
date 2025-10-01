# shared.py
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import joblib
import shap
from matplotlib import font_manager as fm
import os

from models.FinalModel.smote_sampler import MajorityVoteSMOTENC

# app.py가 있는 위치를 기준으로 절대 경로 관리
app_dir = Path(__file__).parent
# 데이터 경로
data_dir = app_dir / "data"
models_dir = app_dir / "models"
fonts_dir = app_dir / "www" / "fonts"

def setup_korean_font():
    """로컬 + 리눅스 서버에서 모두 한글 깨짐 방지"""
    font_candidates = []

    # 1. 프로젝트 폰트 (권장)
    font_path = Path(__file__).parent / "www" / "fonts" / "NotoSansKR-Regular.ttf"
    if font_path.exists():
        font_prop = fm.FontProperties(fname=str(font_path))
        plt.rcParams['font.family'] = font_prop.get_name()
        fm.fontManager.addfont(str(font_path))
        print(f"✅ 내부 폰트 적용: {font_prop.get_name()}")
        return

    # 2. 로컬 OS별 기본 폰트
    font_candidates = ["Malgun Gothic", "AppleGothic", "NanumGothic", "Noto Sans KR"]

    for font in font_candidates:
        if font in fm.findSystemFonts(fontpaths=None, fontext='ttf'):
            plt.rcParams['font.family'] = font
            print(f"✅ 시스템 폰트 적용: {font}")
            return

    # 3. fallback
    plt.rcParams['font.family'] = "DejaVu Sans"
    print("⚠️ 한글 폰트를 찾지 못해 DejaVu Sans로 대체합니다.")

    # 마이너스 기호 깨짐 방지
    plt.rcParams['axes.unicode_minus'] = False
setup_korean_font()


# plt.rcParams['axes.unicode_minus'] = False

# Data Load
df = pd.read_csv(data_dir / "train.csv")
df.info()

# 이상치 제거 데이터
df2 = pd.read_csv(data_dir / "outlier_remove_data2.csv")

# Model Load
model = joblib.load(models_dir / "final_model.joblib")

# 각 모델 개별 로드
models = {
    "8412": joblib.load(models_dir / "XGBoost" /"xgb_smote20_mold_8412.pkl"),
    "8573": joblib.load(models_dir / "XGBoost" /"xgb_smote20_mold_8573.pkl"),
    "8600": joblib.load(models_dir / "XGBoost"/ "xgb_smote20_mold_8600.pkl"),
    "8722": joblib.load(models_dir / "XGBoost"/ "xgb_smote20_mold_8722.pkl"),
    "8917": joblib.load(models_dir / "XGBoost"/ "xgb_smote20_mold_8917.pkl"),
}

explainers = {
    "8412": shap.TreeExplainer(models["8412"].named_steps["model"]),
    "8573": shap.TreeExplainer(models["8573"].named_steps["model"]),
    "8600": shap.TreeExplainer(models["8600"].named_steps["model"]),
    "8722": shap.TreeExplainer(models["8722"].named_steps["model"]),
    "8917": shap.TreeExplainer(models["8917"].named_steps["model"]),
}

rf_models = {
    "8412": joblib.load(models_dir / "RandomForest" /"rf_mold_8412.pkl"),
    "8573": joblib.load(models_dir / "RandomForest" /"rf_mold_8573.pkl"),
    "8600": joblib.load(models_dir / "RandomForest" /"rf_mold_8600.pkl"),
    "8722": joblib.load(models_dir / "RandomForest" /"rf_mold_8722.pkl"),
    "8917": joblib.load(models_dir / "RandomForest" /"rf_mold_8917.pkl"),
    
}

# rf_models = {
#     "8412": joblib.load(models_dir / "FinalModel" /"final_rf_mold_8412.pkl"),
#     "8573": joblib.load(models_dir / "FinalModel" /"final_rf_mold_8573.pkl"),
#     "8600": joblib.load(models_dir / "FinalModel" /"final_rf_mold_8600.pkl"),
#     "8722": joblib.load(models_dir / "FinalModel" /"final_rf_mold_8722.pkl"),
#     "8917": joblib.load(models_dir / "FinalModel" /"final_rf_mold_8917.pkl"),
    
# }

rf_explainers = {
    "8412": shap.TreeExplainer(rf_models["8412"].named_steps["model"]),
    "8573": shap.TreeExplainer(rf_models["8573"].named_steps["model"]),
    "8600": shap.TreeExplainer(rf_models["8600"].named_steps["model"]),
    "8722": shap.TreeExplainer(rf_models["8722"].named_steps["model"]),
    "8917": shap.TreeExplainer(rf_models["8917"].named_steps["model"]),
    
}

# shared.py에 추가
rf_preprocessors = {
    "8412": rf_models["8412"].named_steps["preprocess"],
    "8573": rf_models["8573"].named_steps["preprocess"],
    "8600": rf_models["8600"].named_steps["preprocess"],
    "8722": rf_models["8722"].named_steps["preprocess"],
    "8917": rf_models["8917"].named_steps["preprocess"],
}

# 전처리된 컬럼명 → 원래 변수명
feature_name_map = {
    "num__molten_temp": "molten_temp",
    "num__molten_volume": "molten_volume",
    "num__sleeve_temperature": "sleeve_temperature",
    "num__EMS_operation_time": "EMS_operation_time",
    "num__cast_pressure": "cast_pressure",
    "num__biscuit_thickness": "biscuit_thickness",
    "num__low_section_speed": "low_section_speed",
    "num__high_section_speed": "high_section_speed",
    "num__physical_strength": "physical_strength",
    "num__upper_mold_temp1": "upper_mold_temp1",
    "num__upper_mold_temp2": "upper_mold_temp2",
    "num__lower_mold_temp1": "lower_mold_temp1",
    "num__lower_mold_temp2": "lower_mold_temp2",
    "num__Coolant_temperature": "Coolant_temperature",
    "num__facility_operation_cycleTime": "facility_operation_cycleTime",
    "num__production_cycletime": "production_cycletime",
    "num__count": "count",
    "cat__working_가동": "working=가동",
    "cat__working_정지": "working=정지",
    "cat__tryshot_signal_A": "tryshot_signal=A",
    "cat__tryshot_signal_D": "tryshot_signal=D",
}

feature_name_map_kor = {
    "num__molten_temp": "용탕 온도(℃)",
    "num__molten_volume": "용탕 부피",
    "num__sleeve_temperature": "슬리브 온도(℃)",
    "num__EMS_operation_time": "EMS 작동시간(s)",
    "num__cast_pressure": "주조 압력(bar)",
    "num__biscuit_thickness": "비스킷 두께(mm)",
    "num__low_section_speed": "저속 구간 속도",
    "num__high_section_speed": "고속 구간 속도",
    "num__physical_strength": "형체력",
    "num__upper_mold_temp1": "상형 온도1(℃)",
    "num__upper_mold_temp2": "상형 온도2(℃)",
    "num__lower_mold_temp1": "하형 온도1(℃)",
    "num__lower_mold_temp2": "하형 온도2(℃)",
    "num__coolant_temp": "냉각수 온도(℃)",
    "num__facility_operation_cycleTime": "설비 가동 사이클타임",
    "num__production_cycletime": "생산 사이클타임",
    "num__count": "생산 횟수",
    "cat__working_가동": "작업 여부=가동",
    "cat__working_정지": "작업 여부=정지",
    "cat__tryshot_signal_A": "트라이샷 신호=A",
    "cat__tryshot_signal_D": "트라이샷 신호=D",
}

name_map_kor = {
    # 메타/식별자
    "id": "행 ID",
    "line": "작업 라인",
    "name": "제품명",
    "mold_name": "금형명",
    "time": "수집 시간",
    "date": "수집 일자",
    "registration_time": "등록 일시",

    # 생산 관련
    "count": "생산 횟수",
    "working": "작업 여부",
    "emergency_stop": "비상정지 여부",
    "passorfail": "양/불 판정 결과",
    "tryshot_signal": "트라이샷 여부",
    "mold_code": "금형 코드",
    "heating_furnace": "가열로 구분",

    # 공정 변수
    "molten_temp": "용탕 온도",
    "molten_volume": "용탕 부피",
    "sleeve_temperature": "슬리브 온도",
    "EMS_operation_time": "EMS 작동시간",
    "cast_pressure": "주조 압력(bar)",
    "biscuit_thickness": "비스킷 두께(mm)",
    "low_section_speed": "저속 구간 속도",
    "high_section_speed": "고속 구간 속도",
    "physical_strength": "형체력",

    # 금형 온도
    "upper_mold_temp1": "상형 온도1",
    "upper_mold_temp2": "상형 온도2",
    "upper_mold_temp3": "상형 온도3",
    "lower_mold_temp1": "하형 온도1",
    "lower_mold_temp2": "하형 온도2",
    "lower_mold_temp3": "하형 온도3",

    # 냉각 관련
    "Coolant_temperature": "냉각수 온도",

    # 사이클 관련
    "facility_operation_cycleTime": "설비 가동 사이클타임",
    "production_cycletime": "생산 사이클타임",

    # 파생 변수
    "day": "일",
    "month": "월",
    "weekday": "요일"
}