from shiny import ui, render
from viz.eda_plots import plot_dist, plot_corr_heatmap, plot_proc_vs_result
from shared import df

# 공정별 변수 그룹 정의
PROCESS_VARS = {
    "① 용탕 준비": ["molten_temp", "molten_volume"],
    "② 반고체 슬러리 제조": ["sleeve_temperature", "EMS_operation_time"],
    "③ 사출 & 금형 충전": ["low_section_speed", "high_section_speed", "cast_pressure", "biscuit_thickness", "physical_strength"],
    "④ 응고": ["upper_mold_temp1", "upper_mold_temp2", "upper_mold_temp3",
             "lower_mold_temp1", "lower_mold_temp2", "lower_mold_temp3",
             "Coolant_temperature"]
}


def page_eda_ui():
    return ui.page_fluid(
        ui.h3("데이터 탐색"),

        ui.navset_tab(
            ui.nav_panel(
                "변수 분포",
                ui.layout_sidebar(
                    ui.sidebar(
                        ui.input_radio_buttons(
                            "var_type",
                            "변수 유형 선택",
                            choices={"numeric": "수치형", "categorical": "범주형"},
                            selected="numeric"
                        ),
                        ui.output_ui("var_selector")   # 동적 UI 출력
                    ),
                    ui.card(
                        ui.card_header("변수 분포"),
                        ui.output_plot("dist_plot", width="100%", height="500px")
                    )
                )
            ),

            ui.nav_panel(
                "상관관계",
                ui.card(
                    ui.card_header("상관관계 Heatmap"),
                    ui.output_plot("corr_heatmap", width="100%", height="800px")
                )
            ),

            ui.nav_panel(
                "공정별 탐색",
                ui.layout_sidebar(
                    ui.sidebar(
                        ui.input_select(
                            "process_select",
                            "공정 선택",
                            choices=list(PROCESS_VARS.keys())
                        )
                    ),
                    ui.card(
                        ui.card_header("공정별 탐색 결과"),
                        ui.output_ui("proc_plots")
                    )
                )
            ),
            id="eda_nav"
        )
    )


def page_eda_server(input, output, session):
    @output
    @render.ui
    def var_selector():
        if input.var_type() == "numeric":
            choices = [c for c in df.columns if df[c].dtype != "object"]
        else:
            choices = [c for c in df.columns if df[c].dtype == "object"]

        return ui.input_select("var_dist", "변수 선택", choices=choices)

    @output
    @render.plot
    def dist_plot():
        return plot_dist(input.var_dist())

    @output
    @render.plot
    def corr_heatmap():
        return plot_corr_heatmap()

    @output
    @render.ui
    def proc_plots():
        """선택된 공정의 모든 변수를 박스플롯으로 출력"""
        process = input.process_select()
        vars_for_process = PROCESS_VARS.get(process, [])

        plots = []
        for v in vars_for_process:
            plots.append(ui.output_plot(f"plot_{v}", width="100%", height="400px"))
        return ui.div(*plots)

    for process, vars_list in PROCESS_VARS.items():
        for v in vars_list:
            @output(id=f"plot_{v}")
            @render.plot
            def _make_plot(v=v):
                return plot_proc_vs_result(v)
