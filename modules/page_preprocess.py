from shiny import ui, render

def page_preprocess_ui():
    return ui.page_fluid(
        ui.h3("데이터 전처리 과정"),
        ui.layout_columns(
            ui.card(
                ui.card_header("① 결측치 처리"),
                ui.p("데이터셋의 결측값을 확인하고, 평균 대체 또는 제거 방법을 적용합니다."),
                class_="bg-light"
            ),
            ui.card(
                ui.card_header("② 이상치 탐지"),
                ui.p("통계적 방법(IQR, Z-score 등)을 사용하여 이상치를 탐지하고, 적절히 처리합니다."),
                class_="bg-light"
            ),
            col_widths=[6, 6]  # 2열 레이아웃
        ),
        ui.br(),
        ui.layout_columns(
            ui.card(
                ui.card_header("③ 스케일링"),
                ui.p("수치형 변수는 표준화(StandardScaler) 또는 정규화(MinMaxScaler)를 적용합니다."),
                class_="bg-light"
            ),
            ui.card(
                ui.card_header("④ 범주형 인코딩"),
                ui.p("범주형 변수는 원-핫 인코딩(One-hot encoding) 또는 라벨 인코딩을 적용합니다."),
                class_="bg-light"
            ),
            col_widths=[6, 6]
        ),
        ui.br(),
        ui.card(
            ui.card_header("⑤ 데이터 분할"),
            ui.p("학습/검증/테스트 데이터셋으로 분할하여 모델 학습에 활용합니다."),
            class_="bg-light"
        )
    )


def page_preprocess_server(input, output, session):

    pass