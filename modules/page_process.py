from shiny import ui

def page_process_ui():
    
    # 1. 툴팁 아이콘 콘텐츠 정의 (테이블 밖에서 재사용)
    # 아이콘 SVG와 툴팁 메시지를 정의합니다.
    tooltip_icon_content = ui.span([
        ui.HTML('<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"16\" height=\"16\" fill=\"#1976d2\" class=\"bi bi-info-circle-fill mb-1\" viewBox=\"0 0 16 16\"><path d=\"M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM5.496 6.033h.825c.138 0 .248-.113.266-.25.09-.656.54-1.134 1.342-1.134.686 0 1.314.343 1.314 1.168 0 .635-.374.927-.965 1.371-.673.489-1.206 1.06-1.168 1.987l.003.217a.25.25 0 0 0 .25.246h.811a.25.25 0 0 0 .25-.25v-.105c0-.718.273-.927 1.01-1.486.609-.463 1.244-.977 1.244-2.056 0-1.511-1.276-2.241-2.673-2.241-1.267 0-2.655.59-2.75 2.286a.237.237 0 0 0 .241.247zm2.325 6.443c.61 0 1.029-.394 1.029-.927 0-.552-.42-.94-1.029-.94-.584 0-1.009.388-1.009.94 0 .533.425.927 1.01.927z\"/></svg>')
    ])
    
    # 최종 툴팁 컴포넌트 (설명 내용 업데이트)
    tooltip_component = ui.tooltip(
        tooltip_icon_content,
        "Cut-off란? 불량률이 급격히 증가하는 임계값을 의미", # 설명 업데이트
        placement="right"
    )
    
    # 2. 탭별 관리 기준 테이블 생성 함수 (하한/상한 분리)
    def create_management_table_revised(data_rows):
        
        return ui.tags.table(
            {
                "style": "width: 100%; max-width: 450px; border-spacing: 0; border-collapse: collapse;"},
            ui.tags.thead(
                ui.tags.tr(
                    # 변수
                    ui.tags.th({"style": "width: 60%; text-align: left; padding: 4px;"}, "변수"),
                    # Cut-off 하한 (툴팁 및 아이콘 제거)
                    ui.tags.th({"style": "width: 20%; text-align: center; padding: 4px; white-space: nowrap;"}, 
                               "Cut-off (하한)"),
                    # Cut-off 상한
                    ui.tags.th({"style": "width: 20%; text-align: center; padding: 4px; white-space: nowrap;"}, 
                               "Cut-off (상한)"),
                )
            ),
            ui.tags.tbody(*[
                # (변수명, 하한값, 상한값)
                ui.tags.tr(
                    ui.tags.td({"style": "padding: 2px 4px;"}, var_name),
                    ui.tags.td({"style": "padding: 2px 4px; text-align: center;"}, lower_value),
                    ui.tags.td({"style": "padding: 2px 4px; text-align: center;"}, upper_value)
                ) for var_name, lower_value, upper_value in data_rows
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
                    # **수정된 관리 기준 카드:** 툴팁을 우측 상단으로 이동
                    ui.card(
                        ui.div(
                            {"style": "display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;"},
                            ui.h4("관리 기준", style="margin: 0;"), # h4의 기본 마진 제거
                            tooltip_component # 우측 상단에 툴팁 배치
                        ),
                        create_management_table_revised([
                            ("용탕 온도 (molten_temp)", "-", "-"),
                            ("용탕 부피 (molten_volume)", "5", "113"),
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
                    # **수정된 관리 기준 카드:**
                    ui.card(
                        ui.div(
                            {"style": "display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;"},
                            ui.h4("관리 기준", style="margin: 0;"),
                            tooltip_component
                        ),
                        create_management_table_revised([
                            ("슬리브 온도 (sleeve_temperature)", "147", "605"),
                            ("EMS 가동 시간 (EMS_operation_time)", "-", "-"),
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
                    # **수정된 관리 기준 카드:**
                    ui.card(
                        ui.div(
                            {"style": "display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;"},
                            ui.h4("관리 기준", style="margin: 0;"),
                            tooltip_component
                        ),
                        create_management_table_revised([
                            ("저속 구간 속도 (low_section_speed)", "100", "115"),
                            ("고속 구간 속도 (high_section_speed)", "101", "117"),
                            ("주입 압력 (cast_pressure)", "313", "-"),
                            ("비스킷 두께 (biscuit_thickness)", "42", "56"),
                            ("형체력 (physical_strength)", "-", "-"),
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
                    # **수정된 관리 기준 카드:**
                    ui.card(
                        ui.div(
                            {"style": "display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;"},
                            ui.h4("관리 기준", style="margin: 0;"),
                            tooltip_component
                        ),
                        create_management_table_revised([
                            ("상금형 온도1 (upper_mold_temp1)", "102", "-"),
                            ("하금형 온도1 (lower_mold_temp1)", "95", "-"),
                            ("상금형 온도2 (upper_mold_temp2)", "121", "235"),
                            ("하금형 온도2 (lower_mold_temp2)", "70", "309"),
                            ("냉각수 온도 (Coolant_temperature)", "29", "-"),
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

# ----------------------------------------------------
# 서버 코드는 그대로 유지하며, ui 함수만 변경했습니다.
# ----------------------------------------------------

# (이 부분은 page_process_ui와 분리된 파일에 있어야 함)
from shiny import render
# from viz.plots import plot_failrate_cutoff_dual_fast # 이 임포트는 순환참조 가능성이 높음
from shared import df2

def page_process_server(input, output, session):
    
    # 순환 참조 해결을 위해 함수 내부에서 임포트하거나, 별도 설정 필요
    try:
        from viz.plots import plot_failrate_cutoff_dual_fast
    except ImportError:
        # 실제 환경에 맞게 처리 필요
        print("Warning: plot_failrate_cutoff_dual_fast not imported correctly in server.")
        return 

    @output()
    @render.plot()
    def plot_selected_var_quality_molten():
        selected_var = input.selected_var_molten()
        # Vars to hide (예시)
        VARS_TO_HIDE = ["physical_strength"]
        fig = plot_failrate_cutoff_dual_fast(df2, selected_var, vars_to_hide=VARS_TO_HIDE)
        return fig

    @output()
    @render.plot()
    def plot_selected_var_quality_slurry():
        selected_var = input.selected_var_slurry()
        VARS_TO_HIDE = ["physical_strength"]
        fig = plot_failrate_cutoff_dual_fast(df2, selected_var, vars_to_hide=VARS_TO_HIDE)
        return fig

    @output()
    @render.plot()
    def plot_selected_var_quality_injection():
        selected_var = input.selected_var_injection()
        VARS_TO_HIDE = ["physical_strength"]
        fig = plot_failrate_cutoff_dual_fast(df2, selected_var, vars_to_hide=VARS_TO_HIDE)
        return fig

    @output()
    @render.plot()
    def plot_selected_var_quality_solid():
        selected_var = input.selected_var_solid()
        VARS_TO_HIDE = ["physical_strength"]
        fig = plot_failrate_cutoff_dual_fast(df2, selected_var, vars_to_hide=VARS_TO_HIDE)
        return fig