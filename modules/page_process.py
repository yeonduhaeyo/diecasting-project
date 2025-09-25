from shiny import ui, render
from viz.plots import plot_molten_temp

def page_process_ui():
    return ui.page_fluid(
        ui.h2("다이캐스팅 공정 설명"),
        ui.markdown(
            """
            다이캐스팅(Die Casting)은 금속을 고압으로 금형에 주입해  
            **정밀하고 복잡한 부품**을 대량 생산하는 공정입니다.
            """
        ),
        ui.img(src="diecasting.png", height="400px"),  # www 폴더 기준 경로
        ui.hr(),

        ui.navset_tab(
            # ① 용탕 준비
            ui.nav_panel(
                "① 용탕 준비 및 가열",
                ui.layout_sidebar(
                    ui.sidebar(
                        ui.h4("관련 변수"),
                        ui.tags.ul(
                            ui.tags.li("molten_temp: 용탕 온도"),
                            ui.tags.li("molten_volume: 용탕 부피"),
                            ui.tags.li("heating_furnace: 가열로 정보"),
                        )
                    ),
                    ui.card(
                        ui.h4("공정 설명"),
                        ui.markdown("용탕을 가열로에서 준비"),
                        ui.output_plot("molten_plot")  # <- 추후 그래프 자리
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
                            ui.tags.li("sleeve_temperature: 슬리브 온도"),
                            ui.tags.li("EMS_operation_time: EMS 가동 시간"),
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
                            ui.tags.li("low_section_speed: 저속 구간 속도"),
                            ui.tags.li("high_section_speed: 고속 구간 속도"),
                            ui.tags.li("cast_pressure: 주입 압력"),
                            ui.tags.li("biscuit_thickness: 비스킷 두께"),
                            ui.tags.li("physical_strength: 형체력"),
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
                            ui.tags.li("upper_mold_temp1~3: 상금형 온도"),
                            ui.tags.li("lower_mold_temp1~3: 하금형 온도"),
                            ui.tags.li("Coolant_temperature: 냉각수 온도"),
                            
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
                            ui.tags.li("passorfail: 최종 품질 결과 (0=불합격, 1=합격)"),
                        )
                    ),
                    ui.card(
                        ui.h4("공정 설명"),
                        ui.markdown("모든 변수를 종합해 최종 합격/불합격 판정"),
                        ui.output_text_verbatim("text_quality")  # <- 예측/판정 출력 자리
                    )
                )
            ),
        )
    )


def page_process_server(input, output, session):
    @output
    @render.plot
    def molten_plot():
        return plot_molten_temp()