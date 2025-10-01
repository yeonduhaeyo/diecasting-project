# modules/page_preprocess.py
from shiny import ui, render
from modules import service_preprocess as tbl  # 테이블/이미지 모듈 불러오기
import pandas as pd
from viz import preprocess_plots as plots
from modules import service_preprocess as tbl

from shared import df

def page_preprocess_ui():
    return ui.page_fluid(
        ui.h3("데이터 전처리 및 모델링 과정"),

        ui.accordion(

            # 0. 데이터 요약
            ui.accordion_panel(
                "0. 데이터 요약",
                ui.h4("설명"),
                ui.p("➡️ 전체 데이터 크기, 주요 변수 요약, 기본 통계 등"),
                ui.hr(),
                ui.h4("전체 데이터 개요"),
                tbl.data_summary_table,
                ui.hr(),
                
                ui.h4("변수 타입별 분포"),
                ui.output_ui("variable_types_table"),                
                # ui.output_plot("data_types_plot"),
                ui.hr(),
                
                ui.h4("타겟 변수 분포 (passorfail)"),
                ui.p("Pass(정상) / Fail(불량) 분포 확인"),
                ui.output_plot("target_distribution_plot"),
                ui.hr(),
                
                ui.h4("결측치 현황"),
                ui.output_plot("missing_overview_plot"),
                ui.hr(),
                

            ),

            # 1. 가용 변수 선택
            ui.accordion_panel(
                "1. 가용 변수 선택",
                ui.h4("설명"),
                ui.p("➡️ 사용 변수와 제외 변수, 제외 이유를 정리"),
                ui.hr(),
                
                ui.h4("가용 변수"),
                tbl.available_vars_table,
                ui.hr(),
                
                ui.h4("제외 변수"),
                tbl.removed_vars_table,
            ),

            # 2. 데이터 정제
            ui.accordion_panel(
                "2. 데이터 정제",

                # 중복 행 제거
                ui.h4("중복 행 제거"),
                ui.p("time 시간대 정보만 다르고, 동일한 생산 제품 연속적으로 등장한 데이터 10개 행 제거"),
                ui.img(
                    src="duplicate_img.png",
                    style="width:100%; margin:10px auto; display:block;"
                ),
                ui.hr(),
                
                # 행 제거
                ui.h4("행 제거"),
                ui.p("센서 오류 의심 값 및 다수 결측 행 제거"),
                tbl.removed_rows_table,
                ui.img(
                    src="remove_img.png",
                    style="width:100%; max-width:1000px; margin:10px auto; display:block;"
                ),
                ui.hr(),

                # 데이터 타입 변경
                ui.h4("데이터 타입 변경"),
                ui.p("mold_code, EMS_operation_time → 범주형 변환"),
                tbl.dtype_change_table,
                ui.hr(),

                # 결측치 처리
                ui.h4("결측치 처리"),
                ui.p("변수별 결측 처리 방법과 근거"),
                tbl.missing_table_html,
                ui.hr(),

                # 이상치 처리
                ui.h4("이상치 처리"),
                ui.p("0값/비정상값 → 보간 or 대체"),
                tbl.outlier_table_html,
                # ui.output_plot("outlier_plot"),
            ),

            # 3. 모델링 준비
            ui.accordion_panel(
                "3. 모델링 준비",

                ui.h4("데이터 분리"),
                ui.p("➡️ 8:2 비율, 금형 코드 및 불량 라벨(check 변수)에 맞춘 층화 샘플링"),
                # ui.output_plot("split_chart"),
                ui.hr(),

                ui.h4("불량 데이터 오버샘플링"),
                ui.p("➡️ Train 데이터에서 실제 불량 샘플을 금형코드 비율 유지하며 4배 증강"),
                ui.p("➡️ SMOTE 적용, 범주형은 Majority Vote 방식 채움"),
                ui.p("➡️ 결과: 오버샘플링 이후 가불량 대비 실제 불량률 2.6배"),
                ui.output_table("sampling_info"),
                ui.hr(),

                ui.h4("범주형 / 수치형 처리"),
                ui.p("➡️ 수치형: RobustScaler 적용 (이상치 영향 완화)"),
                ui.p("➡️ 범주형: One-hot Encoding 적용"),
                ui.p("➡️ MajorityVoteSMOTENC 활용 → 수치형은 보간, 범주형은 다수결 선택"),
                ui.img(src="majorityvotesmotenc.png",
                       style="width:100%; max-width:500px; margin-bottom:15px;"),
                # ui.output_plot("scaling_before"),
                # ui.output_plot("scaling_after"),
                ui.output_table("encoding_example"),
            ),

            # 4. 최종 모델 도출
            ui.accordion_panel(
                "4. 최종 모델 도출",

                ui.h4("금형 코드별 모델 성능 비교 (RandomForest vs XGBoost)"),

                ui.layout_columns(
                    ui.card(
                        ui.card_header("RandomForest 결과"),
                        tbl.rf_results_imgs
                    ),
                    ui.card(
                        ui.card_header("XGBoost 결과"),
                        tbl.xgb_results_imgs
                    ),
                    col_widths=[6, 6]
                ),

                ui.hr(),

                ui.h4("최종 모델 선정 및 최적 하이퍼파라미터 확인"),
                ui.p("➡️ 금형 코드별 Best Hyperparameter 정리"),
                tbl.best_params_table,

                ui.hr(),

                ui.h4("SHAP 그래프 시각화"),
                ui.p("➡️ 최종 모델에서 주요 Feature 중요도를 SHAP 기반으로 시각화"),

                ui.layout_columns(
                    ui.card(
                        ui.card_header("SHAP Importance"),
                        ui.p("SHAP 값을 기반으로 각 Feature가 예측에 기여한 정도를 해석"),
                        ui.img(src="shap_importance.png",
                               style="width:100%; max-width:500px; margin-bottom:15px;")
                    ),
                    ui.card(
                        ui.card_header("Permutation Importance"),
                        ui.p("Feature 값을 무작위로 섞어 예측 성능 저하 정도로 중요도를 평가"),
                        ui.img(src="permutation_importance.png",
                               style="width:100%; max-width:500px; margin-bottom:15px;")
                    ),
                    col_widths=[6, 6]
                ),
            ),

            id="preprocess_panel",
            open=False,
            multiple=False
        ),
    )


def page_preprocess_server(input, output, session):
    
    # @output
    # @render.table
    # def variable_types_table():
    #     return tbl.get_variable_types()
    
    @output
    @render.ui
    def variable_types_table():
        return ui.HTML(tbl.get_variable_types())
    
    @output
    @render.plot
    def data_types_plot():
        return plots.plot_data_types(df)
    
    @output
    @render.plot
    def missing_overview_plot():
        return plots.plot_missing_overview(df)
    
    @output
    @render.plot
    def target_distribution_plot():
        return plots.plot_target_distribution(df, target_col='passorfail')
    
    @output
    @render.table
    def numeric_stats_table():
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
        # passorfail이 숫자형이라면 제외
        numeric_cols = [col for col in numeric_cols if col != 'passorfail']
        if len(numeric_cols) > 0:
            stats = df[numeric_cols].describe().T
            stats['결측치'] = df[numeric_cols].isnull().sum()
            return stats.round(2)
        else:
            return pd.DataFrame()
        
    @output
    @render.plot
    def missing_plot():
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "결측치 시각화 자리", ha="center", va="center")
        return fig

    @output
    @render.table
    def missing_table():
        import pandas as pd
        return pd.DataFrame({"Column": ["A", "B"], "Missing %": [10, 5]})

