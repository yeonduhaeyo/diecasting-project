from shiny import ui, render
from viz.plots import plot_molten_temp_vs_fail   # ← 새로운 함수 (viz/plots.py에 구현)
# 기존 plot_molten_temp 대신 vs_fail 버전 사용

def page_process_ui():
    return ui.page_fluid(
        ui.h2("다이캐스팅 공정 설명"),
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
        ),
        ui.hr(),

        ui.navset_tab(
            # ① 용탕 준비
            ui.nav_panel(
                "① 용탕 준비 및 가열",
                ui.layout_sidebar(
                    ui.sidebar(
                        ui.h4("관련 변수"),
                        ui.tags.ul(
                            ui.tags.li("용탕 온도 (molten_temp)"),
                            ui.tags.li("용탕 부피 (molten_volume)"),
                        )
                    ),
                    ui.card(
                        ui.h4("공정 설명"),
                        ui.markdown("용탕을 가열로에서 준비 → 주조 안정성에 직결")
                    ),
                    ui.card(
                        ui.h4("관리 기준"),
                        ui.tags.table(
                            ui.tags.tr(ui.tags.th("변수"), ui.tags.th("하한"), ui.tags.th("상한"), ui.tags.th("관리 포인트")),
                            ui.tags.tr(ui.tags.td("용탕 온도 (molten_temp)"), ui.tags.td("600℃"), ui.tags.td("750℃"), ui.tags.td("온도가 낮으면 미충전 위험")),
                            ui.tags.tr(ui.tags.td("용탕 부피 (molten_volume)"), ui.tags.td("50ml"), ui.tags.td("500ml"), ui.tags.td("과소 주입 방지")),
                        )
                    ),
                    ui.card(
                        ui.h4("실제 데이터 기반 예시 그래프"),
                        ui.output_plot("plot_molten_quality")
                    )
                )
            ),

            # ② 반고체 슬러리 제조
            ui.nav_panel(
                "② 반고체 슬러리 제조",
                ui.layout_sidebar(
                    ui.sidebar(
                        ui.h4("관련 변수"),
                        ui.tags.ul(
                            ui.tags.li("슬리브 온도 (sleeve_temperature)"),
                            ui.tags.li("EMS 가동 시간 (EMS_operation_time)"),
                        )
                    ),
                    ui.card(
                        ui.h4("공정 설명"),
                        ui.markdown("슬리브에 용탕 주입 후 냉각 + EMS 교반으로 반고체 슬러리를 제조"),
                        ui.output_plot("plot_slurry")
                    )
                )
            ),

            # ③ 사출 & 금형 충전
            ui.nav_panel(
                "③ 사출 & 금형 충전",
                ui.layout_sidebar(
                    ui.sidebar(
                        ui.h4("관련 변수"),
                        ui.tags.ul(
                            ui.tags.li("저속 구간 속도 (low_section_speed)"),
                            ui.tags.li("고속 구간 속도 (high_section_speed)"),
                            ui.tags.li("주입 압력 (cast_pressure)"),
                            ui.tags.li("비스킷 두께 (biscuit_thickness)"),
                            ui.tags.li("형체력 (physical_strength)"),
                        )
                    ),
                    ui.card(
                        ui.h4("공정 설명"),
                        ui.markdown("피스톤이 반고체 금속을 밀어내며 금형 충전"),
                        ui.output_plot("plot_injection")
                    )
                )
            ),

            # ④ 응고
            ui.nav_panel(
                "④ 응고",
                ui.layout_sidebar(
                    ui.sidebar(
                        ui.h4("관련 변수"),
                        ui.tags.ul(
                            ui.tags.li("상금형 온도 (upper_mold_temp1~3)"),
                            ui.tags.li("하금형 온도 (lower_mold_temp1~3)"),
                            ui.tags.li("냉각수 온도 (Coolant_temperature)"),
                        )
                    ),
                    ui.card(
                        ui.h4("공정 설명"),
                        ui.markdown("냉각/응고되며 최종 형상이 완성"),
                        ui.output_plot("plot_mold")
                    )
                )
            ),

            # ⑤ 품질 판정
            ui.nav_panel(
                "⑤ 품질 판정",
                ui.layout_sidebar(
                    ui.sidebar(
                        ui.h4("관련 변수"),
                        ui.tags.ul(
                            ui.tags.li("최종 품질 결과 (passorfail)"),
                        )
                    ),
                    ui.card(
                        ui.h4("공정 설명"),
                        ui.markdown("모든 변수를 종합해 최종 양품/불량품 (0=양품, 1=불량품) 판정"),
                        ui.output_text_verbatim("text_quality")
                    )
                )
            ),
            id="process_nav"
        )
    )


def page_process_server(input, output, session):
    @output
    @render.plot
    def plot_molten_quality():
        return plot_molten_temp_vs_fail()
