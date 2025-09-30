from shiny import ui

def page_process_ui():
    
    # 1. Cut-off 제목의 내용 (ui.tags.th를 제외한 내용)을 변수로 정의
    #    이 변수는 create_management_table 함수 내의 <th> 태그에서 사용됩니다.
    cutoff_content = ui.tooltip(
        ui.span(["Cut-off", ui.HTML('<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"16\" height=\"16\" fill=\"#1976d2\" class=\"bi bi-info-circle-fill mb-1\" viewBox=\"0 0 16 16\"><path d=\"M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM5.496 6.033h.825c.138 0 .248-.113.266-.25.09-.656.54-1.134 1.342-1.134.686 0 1.314.343 1.314 1.168 0 .635-.374.927-.965 1.371-.673.489-1.206 1.06-1.168 1.987l.003.217a.25.25 0 0 0 .25.246h.811a.25.25 0 0 0 .25-.25v-.105c0-.718.273-.927 1.01-1.486.609-.463 1.244-.977 1.244-2.056 0-1.511-1.276-2.241-2.673-2.241-1.267 0-2.655.59-2.75 2.286a.237.237 0 0 0 .241.247zm2.325 6.443c.61 0 1.029-.394 1.029-.927 0-.552-.42-.94-1.029-.94-.584 0-1.009.388-1.009.94 0 .533.425.927 1.01.927z\"/></svg>')]),
        "cut-off란? 불량률이 급격히 증가하는 임계값을 의미합니다 (0.15 기준)",
        placement="right"
    )

    # 2. 탭별 관리 기준 테이블 생성 함수 (반복 줄이기)
    def create_management_table(data_rows):
        # 테이블 스타일: 폭을 좁히고 셀 간격을 조정
        return ui.tags.table(
            {
                "style": "width: 100%; max-width: 450px; border-spacing: 0; border-collapse: collapse;"},
            ui.tags.thead(
                ui.tags.tr(
                    ui.tags.th({"style": "width: 70%; text-align: left; padding: 4px;"}, "변수"),
                    # **수정된 부분:** white-space: nowrap을 추가하여 줄 바꿈 방지
                    ui.tags.th({
                        "style": "width: 30%; text-align: right; padding: 4px; white-space: nowrap;" 
                    }, cutoff_content), 
                )
            ),
            ui.tags.tbody(*[
                # 변수와 값을 테이블 행으로 받아서 td에 스타일 적용
                ui.tags.tr(
                    ui.tags.td({"style": "padding: 2px 4px;"}, var_name),
                    ui.tags.td({"style": "padding: 2px 4px; text-align: right;"}, var_value)
                ) for var_name, var_value in data_rows
            ])
        )

    # 3. 메인 UI 구성
    return ui.page_fluid(
        ui.h2("다이캐스팅 공정 설명"),

        # 공정 설명 Accordion
        ui.accordion(
            ui.accordion_panel(
                "📘 레오캐스팅(Rheocasting) 공정 소개",
                ui.markdown(
                    """
                    본 프로젝트는 전통적인 다이캐스팅(Die Casting)이 아닌,
                    반고체 금속 슬러리를 활용하는 **레오캐스팅(Rheocasting)** 공정을 기반으로 하고 있습니다.
                    """
                ),
                ui.div(
                    ui.img(src="diecasting2.png", height="400px"),
                    style="text-align:center;"
                ),
                ui.markdown(
                    """
                    레오캐스팅은 액체와 고체가 공존하는 **반고체(Semi-solid)상태**의 금속 슬러리를 활용하는 주조 공정입니다.
                    슬리브에서 빠르게 냉각시키고 **EMS**(Electro-Magnetic Stirring, 전자기 교반)을 가해
                    미세하고 균일한 입자를 형성한 뒤 금형에 충전합니다.

                    이 공정은 기공(Porosity)과 수축 결함을 줄이고,
                    치수 정밀도를 높이며, 기계적 성질(강도·연성)을 향상시키는 장점이 있습니다.

                    따라서 레오캐스팅은 **경량화·고강도 부품**이 필요한 자동차 및 항공우주 산업 등에서 각광받고 있습니다.
                    """
                )
            ),
            id="accordion1",
            open=[]  # 기본적으로 닫힘 상태
        ),

        ui.hr(),

        ui.navset_tab(
            # ① 용탕 준비
            ui.nav_panel(
                "① 용탕 준비 및 가열",
                ui.layout_sidebar(
                    ui.sidebar(
                        ui.h4("관련 변수"),
                        ui.input_select("selected_var_molten", "변수 선택", choices=["molten_temp", "molten_volume"]),
                    ),
                    ui.card(ui.h4("공정 설명"), ui.markdown("용탕을 가열로에서 준비 → 주조 안정성에 직결")),
                    ui.card(
                        ui.h4("관리 기준"),
                        create_management_table([
                            ("용탕 온도 (molten_temp)", "-"),
                            ("용탕 부피 (molten_volume)", "113"),
                        ])
                    ),
                    ui.card(ui.h4("실제 데이터 기반 불량율 변화 그래프"), ui.output_plot("plot_selected_var_quality_molten"))
                )
            ),

            # ② 반고체 슬러리 제조
            ui.nav_panel(
                "② 반고체 슬러리 제조",
                ui.layout_sidebar(
                    ui.sidebar(
                        ui.h4("관련 변수"),
                        ui.input_select("selected_var_slurry", "변수 선택", choices=["sleeve_temperature", "EMS_operation_time"]),
                    ),
                    ui.card(ui.h4("공정 설명"), ui.markdown("슬리브에 용탕 주입 후 냉각 + EMS 교반으로 반고체 슬러리를 제조")),
                    ui.card(
                        ui.h4("관리 기준"),
                        create_management_table([
                            ("슬리브 온도 (sleeve_temperature)", "605"),
                            ("EMS 가동 시간 (EMS_operation_time)", "-"),
                        ])
                    ),
                    ui.card(ui.h4("실제 데이터 기반 불량율 변화 그래프"), ui.output_plot("plot_selected_var_quality_slurry"))
                )
            ),

            # ③ 사출 & 금형 충전
            ui.nav_panel(
                "③ 사출 & 금형 충전",
                ui.layout_sidebar(
                    ui.sidebar(
                        ui.h4("관련 변수"),
                        ui.input_select("selected_var_injection", "변수 선택", choices=["low_section_speed", "high_section_speed", "cast_pressure", "biscuit_thickness", "physical_strength"]),
                    ),
                    ui.card(ui.h4("공정 설명"), ui.markdown("피스톤이 반고체 금속을 밀어내며 금형 충전")),
                    ui.card(
                        ui.h4("관리 기준"),
                        create_management_table([
                            ("저속 구간 속도 (low_section_speed)", "100, 115"),
                            ("고속 구간 속도 (high_section_speed)", "101, 117"),
                            ("주입 압력 (cast_pressure)", "313"),
                            ("비스킷 두께 (biscuit_thickness)", "56"),
                            ("형체력 (physical_strength)", "-"),
                        ])
                    ),
                    ui.card(ui.h4("실제 데이터 기반 불량율 변화 그래프"), ui.output_plot("plot_selected_var_quality_injection"))
                )
            ),

            # ④ 응고
            ui.nav_panel(
                "④ 응고",
                ui.layout_sidebar(
                    ui.sidebar(
                        ui.h4("관련 변수"),
                        ui.input_select("selected_var_solid", "변수 선택", choices=["upper_mold_temp1", "lower_mold_temp1", "upper_mold_temp2", "lower_mold_temp2", "Coolant_temperature"]),
                    ),
                    ui.card(ui.h4("공정 설명"), ui.markdown("냉각/응고되며 최종 형상이 완성")),
                    ui.card(
                        ui.h4("관리 기준"),
                        create_management_table([
                            ("상금형 온도1 (upper_mold_temp1)", "102"),
                            ("하금형 온도1 (lower_mold_temp1)", "-"),
                            ("상금형 온도2 (upper_mold_temp2)", "239"),
                            ("하금형 온도2 (lower_mold_temp2)", "70, 309"),
                            ("냉각수 온도 (Coolant_temperature)", "29"),
                        ])
                    ),
                    ui.card(ui.h4("실제 데이터 기반 불량율 변화 그래프"), ui.output_plot("plot_selected_var_quality_solid"))
                )
            ),

            # ⑤ 품질 판정
            ui.nav_panel(
                "⑤ 품질 판정",
                ui.layout_sidebar(
                    ui.sidebar(
                        ui.h4("관련 변수"),
                        ui.tags.ul(ui.tags.li("최종 품질 결과 (passorfail)"))
                    ),
                    ui.card(ui.h4("공정 설명"), ui.markdown("모든 변수를 종합해 최종 양품/불량품 (0=양품, 1=불량품) 판정"))
                )
            ),
            id="process_nav"
        )
    )

from shiny import render
from viz.plots import plot_failrate_cutoff_dual_fast
from shared import df2

def page_process_server(input, output, session):
    @output()
    @render.plot()
    def plot_selected_var_quality_molten():
        selected_var = input.selected_var_molten()
        fig = plot_failrate_cutoff_dual_fast(df2, selected_var)
        return fig

    @output()
    @render.plot()
    def plot_selected_var_quality_slurry():
        selected_var = input.selected_var_slurry()
        fig = plot_failrate_cutoff_dual_fast(df2, selected_var)
        return fig

    @output()
    @render.plot()
    def plot_selected_var_quality_injection():
        selected_var = input.selected_var_injection()
        fig = plot_failrate_cutoff_dual_fast(df2, selected_var)
        return fig

    @output()
    @render.plot()
    def plot_selected_var_quality_solid():
        selected_var = input.selected_var_solid()
        fig = plot_failrate_cutoff_dual_fast(df2, selected_var)
        return fig
