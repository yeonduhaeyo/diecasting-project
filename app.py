from shiny import App, ui
from modules import page_input, page_process, page_eda, page_preprocess
from pathlib import Path

www_dir = Path(__file__).parent / "www"

# # 스키마 로드
# DATA1 = Path("./data/trainset.csv")
# SCHEMA = schema_utils.build_schema_from_csv(DATA1)

# UI
app_ui = ui.page_navbar(
    ui.nav_panel("🏭 공정 불량 예측", page_input.inputs_layout()),
    ui.nav_panel("⚙️ 공정 설명", page_process.page_process_ui()),
    ui.nav_panel("📊 데이터 탐색", page_eda.page_eda_ui()),
    ui.nav_panel("🧹 전처리 및 모델 설명", page_preprocess.page_preprocess_ui()),
    title="🔧 주조 공정 품질 예측 대시보드",
    id="main_nav",
    bg="#2C3E50",  # 네비게이션 바 색상 (짙은 공장톤)
    inverse=True,  # 다크 스타일 적용
    # theme=ui.theme.bootstrap("cyborg")  # 테마 교체
)

# SERVER
def server(input, output, session):
    page_input.page_input_server(input, output, session)
    page_process.page_process_server(input, output, session)
    page_eda.page_eda_server(input, output, session)
    page_preprocess.page_preprocess_server(input, output, session)
    # page_result.page_result_server(input, output, session)

app = App(app_ui, server, static_assets=www_dir)
