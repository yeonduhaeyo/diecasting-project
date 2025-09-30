from shiny import ui, render

def page_preprocess_ui():
    return ui.page_fluid(
        ui.h3("데이터 전처리 과정"),

        ui.accordion(
            # ① 결측치 처리
            ui.accordion_panel(
                "① 결측치 처리",
                ui.p("➡️ 설명: 결측값 확인 및 처리 방법 (평균 대체, 제거 등)"),
                ui.output_plot("missing_plot"),
                ui.output_table("missing_table")
            ),

            # ② 이상치 탐지
            ui.accordion_panel(
                "② 이상치 탐지",
                ui.p("➡️ 설명: IQR, Z-score 등을 이용한 이상치 탐지"),
                ui.output_plot("outlier_plot"),
            ),

            # ③ 스케일링
            ui.accordion_panel(
                "③ 스케일링",
                ui.p("➡️ 설명: StandardScaler, MinMaxScaler 적용 전후 비교"),
                ui.output_plot("scaling_before"),
                ui.output_plot("scaling_after")
            ),

            # ④ 범주형 인코딩
            ui.accordion_panel(
                "④ 범주형 인코딩",
                ui.p("➡️ 설명: One-hot Encoding, Label Encoding 적용"),
                ui.output_table("encoding_example")
            ),

            # ⑤ 데이터 분할
            ui.accordion_panel(
                "⑤ 데이터 분할",
                ui.p("➡️ 설명: Train/Validation/Test 분할"),
                ui.output_plot("split_chart")
            ),
            
            # 최적 예측모델 선정
            ui.accordion_panel(
                "⑥ 최적 예측모델 선정",
                ui.p("➡️ 설명: 총 10개의 예측모델 생성 후 최적 모델 선정"),
                ui.output_plot("split_chart")
            ),

            id="preprocess_panel",
            open=False,        # 초기에 모두 닫힘
            multiple=False     # 한 번에 하나만 열림
        )
    )


def page_preprocess_server(input, output, session):

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