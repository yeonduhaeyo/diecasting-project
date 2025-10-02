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
                ui.card(
                    ui.card_header("📊 전체 데이터 개요"),
                    tbl.data_summary_table
                ),
                ui.card(
                    ui.card_header("🔎 변수 타입별 분포"),
                    ui.output_ui("variable_types_table")
                ),
                ui.card(
                    ui.card_header("🎯 타겟 변수 분포 (passorfail)"),
                    ui.p("Pass(정상) / Fail(불량) 분포 확인"),
                    ui.output_plot("target_distribution_plot")
                ),
                ui.card(
                    ui.card_header("⚠️ 결측치 현황"),
                    ui.output_plot("missing_overview_plot")
                )
            ),

            # 1. 가용 변수 선택
            ui.accordion_panel(
                "1. 가용 변수 선택",
                ui.card(
                    ui.card_header("✅ 가용 변수"),
                    tbl.available_vars_table
                ),
                ui.card(
                    ui.card_header("🚫 제외 변수"),
                    tbl.removed_vars_table
                )
            ),

            # 2. 데이터 정제
            ui.accordion_panel(
                "2. 데이터 정제",
                ui.card(
                    ui.card_header("🗑️ 중복 행 제거"),
                    ui.p("time 시간대 정보만 다르고 동일 제품이 연속 등장한 데이터 10개 행 제거"),
                    ui.img(src="duplicate_img.png",
                           style="width:100%; margin:10px auto; display:block;")
                ),
                ui.card(
                    ui.card_header("⚠️ 행 제거"),
                    ui.p("센서 오류 의심 값 및 다수 결측 행 제거"),
                    tbl.removed_rows_table,
                    ui.img(src="remove_img.png",
                           style="width:100%; max-width:1000px; margin:10px auto; display:block;"),
                    
                    ui.hr(),
                    
                    ui.p("행 제거 전 후 행 갯수 비교"),
                    ui.p("👉 전 : 73612 / 후 : 73594")
                    
                ),
                ui.card(
                    ui.card_header("🔄 데이터 타입 변경"),
                    ui.p("mold_code, EMS_operation_time → 범주형 변환"),
                    tbl.dtype_change_table
                ),
                ui.card(
                    ui.card_header("❓ 결측치 처리"),
                    tbl.missing_table_html
                ),
                ui.card(
                    ui.card_header("📏 이상치 처리"),
                    tbl.outlier_table_html
                )
            ),

            # 3. 모델링 준비
            ui.accordion_panel(
                "3. 모델링 준비",

                # 데이터 분리

                ui.card(
                    ui.card_header("📂 데이터 분리"),
                    ui.markdown("""
        **방법:** 8:2 비율, 금형코드 + 불량 라벨 기준 층화 샘플링  
        **목적:** 금형별 데이터 편향 방지, 학습 균형 확보
        """),
                    ui.HTML('<div class="alert alert-info" role="alert">층화 샘플링 → 데이터 균형 유지</div>')
                ),

                ui.card(
                    ui.card_header("📈 불량 데이터 오버샘플링"),
                    ui.markdown("""
        - 불량 데이터 4배 증강 (금형 비율 유지)  
        - SMOTE 적용 (범주형은 Majority Vote 방식)  
        """),
                    ui.HTML('<div class="alert alert-danger" role="alert">결과: 실제 불량률 2.6배 ↑</div>')
                ),

                ui.card(
                    ui.card_header("⚙️ 범주형 / 수치형 처리"),
                    ui.markdown("""
        - 수치형 → RobustScaler (이상치 완화)  
        - 범주형 → One-hot Encoding  
        - SMOTENC → 수치형은 보간, 범주형은 다수결 선택
        """),
                    ui.HTML('<div class="alert alert-info" role="alert">범주형·수치형 각각 맞춤 처리</div>')
                ),


                # 금형코드 분리 근거
                ui.card(
                    ui.card_header("📌 금형코드별 모델 분리 근거"),
                    ui.markdown("""
            1. 금형 구조 차이 → 유동·결함 메커니즘 달라짐  
            2. 반고상 주조 특성 → 온도·구조 차이에 따른 불량 양상  
            3. 산업 표준(NADCA PQ²) → 금형별 조건 관리 필요  
            4. 데이터 과학적 근거 → 섞으면 분포 왜곡, 분리 시 패턴 학습 가능  

            👉 결론: 금형코드별 별도 모델 구축이 타당함
            """)
                ),

                # Recall·F2 점수 강조
                ui.card(
                    ui.card_header("⚠️ Recall·F2 중심 모델 목표"),
                    ui.markdown("""
            - Recall = 불량을 놓치지 않고 잡는 능력  
            - Precision = 정상인데 불량으로 잘못 잡는 비율  

            자동차 안전부품은 **미검(FN) 최소화**가 핵심임  
            Accuracy보다 Recall을 우선시해야 함  

            📍 F2-score = Recall에 4배 가중치 → 불량 검출 극대화에 적합  

            👉 결론: Recall·F2 기준 채택은 국제 표준(IATF 16949, ISO 26262)과 Zero Defect 목표에 부합함
            """)
                )
            ),

            # 4. 최종 모델 도출
            ui.accordion_panel(
                "4. 최종 모델 도출",
                ui.card(
                    ui.card_header("📊 모델 평균 성능"),
                    tbl.avg_result_table
                ),
                ui.card(
                    ui.card_header("🔍 몰드 코드별 성능"),
                    tbl.each_result_table
                ),
                ui.card(
                    ui.card_header("⚙️ 최적 하이퍼파라미터"),
                    tbl.best_params_table
                ),
                ui.layout_columns(
                    ui.card(
                        ui.card_header("📌 SHAP Importance"),
                        ui.img(src="shap_importance.png",
                               style="width:100%; max-width:500px; margin-bottom:15px;")
                    ),
                    ui.card(
                        ui.card_header("📌 Permutation Importance"),
                        ui.img(src="permutation_importance.png",
                               style="width:100%; max-width:500px; margin-bottom:15px;")
                    ),
                    col_widths=[6, 6]
                )
            ),

            # 6. 점수화 알고리즘
            ui.accordion_panel("점수화 알고리즘 설명", tbl.shap_markdown),
            
            ui.accordion_panel(
                "변수 조정 가이드",
                tbl.feature_markdown
                
            ),

            id="preprocess_panel",
            open=False,
            multiple=False
        ),
        

            
    
    ui.hr(),
    ui.div(
        ui.download_button(
            "btn_download_prep", 
            "데이터 전처리 보고서 다운로드",
            class_="mb-2",  # margin-bottom 조금 추가
            style="background-color:#2C3E50; color:white; font-weight:600; \
                border-radius:10px; padding:10px 20px; border:none; \
                box-shadow:0 4px 6px rgba(0,0,0,0.2);"
        ),
        ui.download_button(
            "btn_download_model", 
            "예측 모델 분석 보고서 다운로드",
            class_="mb-2",  # margin-bottom 조금 추가
            style="background-color:#2C3E50; color:white; font-weight:600; \
                border-radius:10px; padding:10px 20px; border:none; \
                box-shadow:0 4px 6px rgba(0,0,0,0.2);"
        ),
        style="display:flex; gap:12px;"  # 버튼 간격 띄우기
    )
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
    @render.download(filename="데이터전처리보고서.pdf")  # 다운로드될 때 사용자에게 보이는 파일명
    def btn_download_prep():
        file_path = "www/files/전처리보고서.pdf"  # ✅ 서버에 미리 넣어둔 PDF 경로
        with open(file_path, "rb") as f:
            yield from f  # 파일 내용을 그대로 전송
            
    @output
    @render.download(filename="예측모델분석보고서.pdf")  # 다운로드될 때 사용자에게 보이는 파일명
    def btn_download_model():
        file_path = "www/files/모델보고서.pdf"  # ✅ 서버에 미리 넣어둔 PDF 경로
        with open(file_path, "rb") as f:
            yield from f  # 파일 내용을 그대로 전송