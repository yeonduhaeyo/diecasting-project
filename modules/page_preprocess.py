from shiny import ui, render

def page_preprocess_ui():
    return ui.page_fluid(
        ui.h3("데이터 전처리 및 모델링 과정"),

        ui.accordion(
            
            # 0. 데이터 요약
            ui.accordion_panel(
                "0. 데이터 요약",
                ui.h4("설명"),
            ),

            # 1. 가용 변수 선택
            ui.accordion_panel(
                "1. 가용 변수 선택",
                ui.h4("설명"),
                ui.p("➡️ 사용 변수와 제외 변수, 제외 이유를 정리"),

                ui.h4("가용 변수"),
                ui.HTML("""
                <table class="table table-bordered table-hover" style="font-size:0.9rem; text-align:center;">
                    <thead class="table-dark">
                        <tr>
                            <th>한글 변수명</th>
                            <th>원본 변수명</th>
                            <th>선정 이유</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td>용탕 온도</td><td>molten_temp</td><td>고상 분율 제어 핵심 변수</td></tr>
                        <tr><td>전자교반 가동시간</td><td>EMS_operation_time</td><td>입자 크기·분포 직접 영향</td></tr>
                        <tr><td>주조 압력</td><td>cast_pressure</td><td>점성 높은 슬러리 보압 유지 필수</td></tr>
                        <tr><td>저속/고속 구간 속도</td><td>low/high_section_speed</td><td>슬러리 응집 방지 및 완전 충전 확보</td></tr>
                        <tr><td>금형 온도</td><td>upper/lower_mold_temp</td><td>불균일 시 응고 불균일 → 결함</td></tr>
                        <tr><td>냉각수 온도</td><td>Coolant_temperature</td><td>조직 미세화 및 수축 결함 억제</td></tr>
                        <tr><td>슬리브 온도</td><td>sleeve_temperature</td><td>슬러리 응고 시작점, 불량 직결</td></tr>
                        <tr><td>형체력</td><td>physical_strength</td><td>금형 밀착 불량 방지 필요</td></tr>
                        <tr><td>생산 순번/가동여부/시험샷</td><td>count, working, tryshot_signal</td><td>초기화·시험생산·정지 여부 판단</td></tr>
                    </tbody>
                </table>
                """),

                ui.h4("제외 변수"),
                ui.HTML("""
                <table class="table table-bordered table-hover" style="font-size:0.9rem; text-align:center;">
                    <thead class="table-secondary">
                        <tr>
                            <th>한글 변수명</th>
                            <th>원본 변수명</th>
                            <th>제외 이유</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td>행 ID</td><td>id</td><td>단순 식별자, 모델링 불필요</td></tr>
                        <tr><td>작업 라인</td><td>line</td><td>‘전자교반 3라인 2호기’ 동일 값</td></tr>
                        <tr><td>제품명</td><td>name</td><td>‘TM carrier RH’ 동일 값</td></tr>
                        <tr><td>금형명</td><td>mold_name</td><td>‘TM Carrier RH-Semi-Solid DIE-06’ 동일 값</td></tr>
                        <tr><td>비상정지 여부</td><td>emergency_stop</td><td>‘ON’으로 동일</td></tr>
                        <tr><td>수집 시간/일자</td><td>time, date</td><td>생산 주기 기록용, EDA 참고용</td></tr>
                        <tr><td>등록 일시</td><td>registration_time</td><td>date, time과 중복 → 불필요</td></tr>
                        <tr><td>가열로 구분</td><td>heating_furnance</td><td>값 불균일(A/B/nan) → C로 대체 검증 시 불량률 차이 無, 금형코드·EMS 변수로 대체 가능</td></tr>
                        <tr><td>상금형 온도3</td><td>upper_mold_temp3</td><td>1449 동일 값(전체 73612 중 64356), 상수 특성 → 제외</td></tr>
                        <tr><td>하금형 온도3</td><td>lower_mold_temp3</td><td>1449 동일 값(71650), 상수 특성 → 제외</td></tr>
                    </tbody>
                </table>
                """),
            ),

            # 2. 데이터 정제
            ui.accordion_panel(
                "2. 데이터 정제",

                # 행 제거
                ui.h4("행 제거"),
                ui.p("➡️ 센서 오류 의심 값 및 다수 결측 행 제거"),
                ui.HTML("""
                <table class="table table-bordered table-hover" style="font-size:0.9rem; text-align:center;">
                    <thead class="table-secondary">
                        <tr>
                            <th>제거 행 번호</th>
                            <th>제거 사유</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td>[42632, 19327, 35449, 6000, 11811, 17598, 46546, 35451]</td>
                            <td>스파크 의심 / 다수 변수 결측 → 안정적 모델링 위해 제거</td></tr>
                    </tbody>
                </table>
                """),
                ui.output_plot("removed_rows_plot"),
                ui.hr(),

                # 데이터 타입 변경
                ui.h4("데이터 타입 변경"),
                ui.p("➡️ mold_code, EMS_operation_time → 범주형 변환"),
                ui.HTML("""
                <table class="table table-bordered table-hover" style="font-size:0.9rem; text-align:center;">
                    <thead class="table-secondary">
                        <tr>
                            <th>변수명</th>
                            <th>변경 전</th>
                            <th>변경 후</th>
                            <th>변경 이유</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td>mold_code</td><td>수치형(int)</td><td>범주형(category)</td><td>금형 특성 반영</td></tr>
                        <tr><td>EMS_operation_time</td><td>수치형(int)</td><td>범주형(category)</td><td>시간대별 공정 특성 반영</td></tr>
                    </tbody>
                </table>
                """),
                ui.output_table("dtype_changes_example"),
                ui.hr(),

                # 결측치 처리
                ui.h4("결측치 처리"),
                ui.p("➡️ 변수별 결측 처리 방법과 근거"),
                ui.HTML("""
                <table class="table table-bordered table-hover" style="font-size:0.9rem; text-align:center;">
                    <thead class="table-secondary">
                        <tr>
                            <th>변수명</th>
                            <th>결측 처리 방법</th>
                            <th>근거</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td>tryshot_signal</td><td>NaN → 'A'</td><td>정상 생산품으로 라벨링</td></tr>
                        <tr><td>molten_volume</td><td>NaN → -1</td><td>임의 음수 값 처리 (보간 불가)</td></tr>
                        <tr><td>molten_temp</td><td>NaN → 직전/직후 값 보간(709)</td><td>연속 생산 고려</td></tr>
                    </tbody>
                </table>
                """),
                ui.output_plot("missing_plot"),
                ui.output_table("missing_table"),
                ui.hr(),

                # 이상치 처리
                ui.h4("이상치 처리"),
                ui.p("➡️ 0값/비정상값 → 보간 or 대체"),
                ui.HTML("""
                <table class="table table-bordered table-hover" style="font-size:0.85rem; text-align:center;">
                    <thead class="table-secondary">
                        <tr>
                            <th>변수명</th>
                            <th>이상치 값</th>
                            <th>처리 방법</th>
                            <th>근거</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td>production_CycleTime</td><td>0</td><td>facility_CycleTime 값으로 대체</td><td>두 변수 간 패턴 유사</td></tr>
                        <tr><td>molten_temp</td><td>0</td><td>앞뒤 값 보간</td><td>산발적 발생</td></tr>
                        <tr><td>sleeve_temperature</td><td>1449</td><td>앞뒤 값 보간</td><td>금형 8917 특정 구간 발생</td></tr>
                        <tr><td>Coolant_temperature</td><td>1449</td><td>다음 값(35)으로 대체</td><td>연속 9개 값 발생</td></tr>
                        <tr><td>physical_strength</td><td>0</td><td>금형 8412 평균값 대체</td><td>입력 오류 판단</td></tr>
                    </tbody>
                </table>
                """),
                ui.output_plot("outlier_plot"),
            ),

            # 3. 모델링 준비
            ui.accordion_panel(
                "3. 모델링 준비",

                ui.h4("데이터 분리"),
                ui.p("➡️ 8:2 비율, 금형 코드 및 불량 라벨(check 변수)에 맞춘 층화 샘플링"),
                ui.output_plot("split_chart"),

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
                ui.output_plot("scaling_before"),
                ui.output_plot("scaling_after"),
                ui.output_table("encoding_example"),
            ),

            # 4. 최종 모델 도출
            ui.accordion_panel(
                "4. 최종 모델 도출",
                
                ui.h4("최종 모델 성능 지표"),
                ui.p("➡️ 최종 후보 모델 2개에 대해 주요 성능 지표 비교 (예: Accuracy, F1-score)"),
                ui.output_plot("final_model_metric_plot"),
                ui.output_table("final_model_metrics"),

                ui.hr(),

                ui.h4("최종 모델 선정 및 최적 하이퍼파라미터 확인"),
                ui.p("➡️ 최종 모델의 최적 하이퍼파라미터"),
                ui.output_table("best_hyperparams"),
            ),
            id="preprocess_panel",
            open=False,     # 기본값: 다 닫힘
            multiple=False  # 하나 열리면 나머지는 닫힘
        ),
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
