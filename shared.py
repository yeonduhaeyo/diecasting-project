# shared.py
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import joblib
import shap

from models.FinalModel.smote_sampler import MajorityVoteSMOTENC

# app.py가 있는 위치를 기준으로 절대 경로 관리
app_dir = Path(__file__).parent
# 데이터 경로
data_dir = app_dir / "data"
models_dir = app_dir / "models"

# 한글 폰트 설정 (Windows 기준: 맑은 고딕)
plt.rcParams['font.family'] = 'Malgun Gothic'
# 음수 기호 깨짐 방지
plt.rcParams['axes.unicode_minus'] = False

# Data Load
df = pd.read_csv(data_dir / "train.csv")

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
    "num__coolant_temp": "냉각수 온도(℃)",   # ✅ Coolant_temperature → 소문자 통일
    "num__facility_operation_cycleTime": "설비 가동 사이클타임",
    "num__production_cycletime": "생산 사이클타임",
    "num__count": "생산 횟수",
    "cat__working_가동": "작업 여부=가동",
    "cat__working_정지": "작업 여부=정지",
    "cat__tryshot_signal_A": "트라이샷 신호=A",
    "cat__tryshot_signal_D": "트라이샷 신호=D",
}