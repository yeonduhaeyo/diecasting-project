from shiny import App, ui, render, reactive
from modules import page_input
from pathlib import Path
import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import accuracy_score, recall_score, f1_score
from sklearn.pipeline import Pipeline
from modules import page_input, page_result, page_process
from pathlib import Path

# www 경로를 직접 지정
# 이부분 나중에 setting으로 뺄 것
www_dir = Path(__file__).parent / "www"

DATA1 = Path("./data/data1.csv")
MODEL_PATH = Path("./models/final_model.joblib")
SPLIT_PATH = Path("./models/test_split.joblib")  # 선택(있을 때만 성능표시)

# ===== 스키마 로드 =====
try:
    SCHEMA = page_input.build_schema_from_csv(DATA1)
    schema_msg = f"schema from {DATA1}"
except Exception as e:
    SCHEMA = {"num_specs": [], "cat_specs": []}
    schema_msg = f"[WARN] schema build failed: {e}"

# ===== UI =====
app_ui = ui.page_navbar(
    ui.nav_panel(
        "공정 입력",
        ui.layout_columns(
            # 좌: 입력 카드들
            ui.card(page_input.inputs_layout(SCHEMA)),
            # 우: 예측 배지 + 성능
            ui.TagList(
                ui.card(
                    ui.card_header("예측 결과"),
                    ui.output_ui("pred_badge"),
                    class_="mb-3"
                ),
                ui.card(
                    ui.card_header("모델 성능"),
                    ui.input_switch("show_metrics", "표시 (Accuracy / Recall / F1)", value=False),
                    ui.panel_conditional(
                        "input.show_metrics",
                        ui.br(),
                        ui.output_text("model_name"),
                        ui.output_table("model_metrics"),
                        ui.output_text("metrics_note"),
                    ),
                ),
            ),
            col_widths=[9,3],
        ),
    ),
    ui.nav_panel("공정 입력", page_input.page_input_ui()),
    ui.nav_panel("예측 결과", page_result.page_result_ui()),
    ui.nav_panel("공정 설명", page_process.page_process_ui()),  # 새 페이지 추가
    title="주조 공정 품질 예측",
)

# ===== Helpers =====
def try_load_model():
    if not MODEL_PATH.exists():
        return None, "모델 파일이 없습니다. input.py를 먼저 실행하세요."
    try:
        m = joblib.load(MODEL_PATH)
        return m, "Loaded model."
    except Exception as e:
        return None, f"로딩 실패: {e}"

def try_load_split():
    if not SPLIT_PATH.exists():
        return None, "분할 파일이 없습니다. (선택사항)"
    try:
        s = joblib.load(SPLIT_PATH)  # {'test_x','test_y',...}
        return s, "Loaded split."
    except Exception as e:
        return None, f"split 로딩 실패: {e}"

def normalize_inputs(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    # working → Y/N 표준화
    if "working" in out.columns:
        mapping = {"가동":"Y","비가동":"N","y":"Y","n":"N","Y":"Y","N":"N",
                   "1":"Y","0":"N","true":"Y","false":"N","True":"Y","False":"N"}
        out["working"] = out["working"].astype(str).map(lambda v: mapping.get(v, v))
    # mold_code 'Other' 대체(스키마 첫 선택지)
    if "mold_code" in out.columns:
        out["mold_code"] = out["mold_code"].astype(str)
        try:
            mold_spec = next(s for s in SCHEMA.get("cat_specs", []) if s["name"]=="mold_code")
            fallback = str(mold_spec["choices"][0]) if mold_spec.get("choices") else None
            if fallback:
                out.loc[out["mold_code"].eq("Other"), "mold_code"] = fallback
        except StopIteration:
            pass
    # 컬럼명 표준화(필요 시 추가)
    rename_map = {
        "facility_operation_cycleTime": "facility_operation_CycleTime",
        "production_cycletime": "production_CycleTime",
    }
    for ui_name, train_name in rename_map.items():
        if ui_name in out.columns and train_name not in out.columns:
            out = out.rename(columns={ui_name: train_name})
    return out

def align_columns_like_training(X: pd.DataFrame, model) -> pd.DataFrame:
    cols = getattr(model, "feature_names_in_", None)
    return X if cols is None else X.reindex(columns=list(cols), fill_value=np.nan)

def current_input_df(input, schema):
    """숫자형은 __num 우선, 없으면 __slider. 범주형은 그대로."""
    row = {}
    for s in schema.get("num_specs", []):
        name = s["name"]
        num_id = f"{name}__num"
        sld_id = f"{name}__slider"
        try:
            v = input[num_id]()  # 숫자 입력 우선
            if v is None:
                v = input[sld_id]()
        except Exception:
            v = input[sld_id]()
        row[name] = v
    for s in schema.get("cat_specs", []):
        row[s["name"]] = input[s["name"]]()
    return normalize_inputs(pd.DataFrame([row]))

# ===== Server =====
def server(input, output, session):
    model, model_msg = try_load_model()
    split, split_msg = try_load_split()

    # --- 숫자 입력 ↔ 슬라이더 동기화(양방향) ---
    for spec in SCHEMA.get("num_specs", []):
        name = spec["name"]
        lo, hi = float(spec["min"]), float(spec["max"])

        # slider -> numeric
        def _make_sync_s_to_n(nm=name):
            @reactive.effect
            @reactive.event(input[f"{nm}__slider"])
            def _sync_s_to_n():
                try:
                    v = float(input[f"{nm}__slider"]())
                    ui.update_numeric(f"{nm}__num", value=v, session=session)
                except Exception:
                    pass
        _make_sync_s_to_n()

        # numeric -> slider (클램프)
        def _make_sync_n_to_s(nm=name, lo_=lo, hi_=hi):
            @reactive.effect
            @reactive.event(input[f"{nm}__num"])
            def _sync_n_to_s():
                try:
                    v = input[f"{nm}__num"]()
                    if v is None:
                        return
                    v = float(v)
                    if np.isnan(v):
                        return
                    v = max(lo_, min(hi_, v))
                    ui.update_slider(f"{nm}__slider", value=v, session=session)
                except Exception:
                    pass
        _make_sync_n_to_s()

    # --- 자동 예측(입력 변경 시 즉시 갱신) ---
    def _predict_now():
        if model is None:
            return None, f"{schema_msg}\n{model_msg}"
        try:
            df1 = current_input_df(input, SCHEMA)
            X1  = align_columns_like_training(df1, model)
            pred = int(model.predict(X1)[0])  # 의사결정은 predict()
            return pred, ""
        except Exception as e:
            return None, f"예측 오류: {e}"

    @output
    @render.ui
    def pred_badge():
        pred, msg = _predict_now()
        if pred is None:
            return ui.div(msg, class_="alert alert-warning")

        if pred == 1:
            # FAIL: 빨강
            return ui.div(
                ui.h3("FAIL (1)", class_="mb-0"),
                class_="p-4 text-center text-white",
                style="background-color:#dc3545;border-radius:16px;font-weight:700;font-size:28px;"
            )
        else:
            # PASS: 파랑
            return ui.div(
                ui.h3("PASS (0)", class_="mb-0"),
                class_="p-4 text-center text-white",
                style="background-color:#0d6efd;border-radius:16px;font-weight:700;font-size:28px;"
            )

    # --- 모델 성능(스위치 ON일 때만) ---
    @output
    @render.text
    def model_name():
        if model is None:
            return model_msg
        try:
            est = model.steps[-1][1] if isinstance(model, Pipeline) else model
            return f"모델: {est.__class__.__name__}"
        except Exception:
            return "모델: (이름 확인 실패)"

    @output
    @render.table
    def model_metrics():
        if not input.show_metrics():
            return pd.DataFrame({"message": ["← 스위치를 켜면 성능이 표시됩니다."]})

        if model is None:
            return pd.DataFrame({"message": ["모델이 없습니다. input.py를 먼저 실행하세요."]})
        if split is None:
            return pd.DataFrame({"message": ["분할 파일이 없어 성능을 계산할 수 없습니다. (선택사항)"]})

        try:
            test_x = split["test_x"].copy()
            test_y = split["test_y"].copy().astype(int)
            test_x = align_columns_like_training(normalize_inputs(test_x), model)

            y_pred = model.predict(test_x)
            acc = float(accuracy_score(test_y, y_pred))
            rec = float(recall_score(test_y, y_pred, zero_division=0))
            f1  = float(f1_score(test_y, y_pred, zero_division=0))
            return pd.DataFrame({"Metric": ["Accuracy","Recall (FAIL=1)","F1 (FAIL=1)"],
                                 "Value":  [acc, rec, f1]})
        except Exception as e:
            return pd.DataFrame({"error":[str(e)]})

    @output
    @render.text
    def metrics_note():
        if not input.show_metrics():
            return ""
        return split_msg
    @reactive.event(input.btn_predict)   # 버튼 클릭 시 실행
    def pred_result():
        lines = [
            f"슬리브 온도(℃): {input.sleeve_temp()}",
            f"냉각수 온도(℃): {input.coolant_temp()}",
            f"형체력: {input.strength()}",
            f"주조 압력: {input.cast_pressure()}",
            f"저속 구간 속도: {input.low_speed()}",
            f"고속 구간 속도: {input.high_speed()}",
        ]
        return "입력값 요약\n" + "\n".join(lines)
    
    # page_input.page_server(input, output, session)
    page_result.page_result_server(input, output, session)
    page_process.page_process_server(input, output, session)

app = App(app_ui, server, static_assets=www_dir)
