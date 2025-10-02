# modules/service_preprocess.py
from shiny import ui
from shared import df, name_map_kor
import pandas as pd

# 0. 데이터 요약
# 기본 정보 요약 함수
def get_data_summary():
    return {
        "전체 행 수": f"{len(df):,}",
        "전체 열 수": f"{len(df.columns):,}",
        "결측치 포함 열": f"{df.isnull().any().sum()}",
    }

# 데이터 요약 테이블 HTML
data_summary_table = ui.HTML("""
    <table class='table table-striped'>
        <tr><th>항목</th><th>값</th></tr>
    """ + "".join([f"<tr><td>{k}</td><td>{v}</td></tr>" 
                   for k, v in get_data_summary().items()]) + """
    </table>
""")

# 변수 타입별 요약 함수
def get_variable_types():
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    # 매핑 적용 (없는 경우 원래 변수명 유지)
    numeric_cols_kor = [name_map_kor.get(col, col) for col in numeric_cols]
    categorical_cols_kor = [name_map_kor.get(col, col) for col in categorical_cols]
    
    html_table = f"""
    <table class="table table-bordered table-hover" style="font-size:0.9rem; text-align:center;">
        <thead class="table-dark">
            <tr>
                <th>변수<br>타입</th>
                <th>개수</th>
                <th>변수명 예시</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>수치형</td>
                <td>{len(numeric_cols)}</td>
                <td>{", ".join(numeric_cols_kor)}</td>
            </tr>
            <tr>
                <td>범주형</td>
                <td>{len(categorical_cols)}</td>
                <td>{", ".join(categorical_cols_kor)}</td>
            </tr>
        </tbody>
    </table>
    """
    return html_table


# 1. 가용 변수 테이블
available_vars_table = ui.HTML("""
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
""")

# 2. 제외 변수 테이블
removed_vars_table = ui.HTML("""
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
""")


# 3. 행 제거 테이블
removed_rows_table = ui.HTML("""
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
""")

# 4. 데이터 타입 변경 테이블
dtype_change_table = ui.HTML("""
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
""")


# 5. 결측치 처리 테이블
missing_table_html = ui.HTML("""
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
""")

# 6. 이상치 처리 테이블
outlier_table_html = ui.HTML("""
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
""")

# 7. RandomForest 결과 이미지 묶음
rf_results_imgs = ui.div(
    ui.img(src="rf_img/RandomForest_Moldcode8412.PNG",
           style="width:100%; max-width:500px; margin-bottom:15px;"),
    ui.img(src="rf_img/RandomForest_Moldcode8573.PNG",
           style="width:100%; max-width:500px; margin-bottom:15px;"),
    ui.img(src="rf_img/RandomForest_Moldcode8600.PNG",
           style="width:100%; max-width:500px; margin-bottom:15px;"),
    ui.img(src="rf_img/RandomForest_Moldcode8722.PNG",
           style="width:100%; max-width:500px; margin-bottom:15px;"),
    ui.img(src="rf_img/RandomForest_Moldcode8917.PNG",
           style="width:100%; max-width:500px; margin-bottom:15px;"),
)

# 8. XGBoost 결과 이미지 묶음
xgb_results_imgs = ui.div(
    ui.img(src="xgb_img/mold_8412.png",
           style="width:100%; max-width:500px; margin-bottom:15px;"),
    ui.img(src="xgb_img/mold_8573.png",
           style="width:100%; max-width:500px; margin-bottom:15px;"),
    ui.img(src="xgb_img/mold_8600.png",
           style="width:100%; max-width:500px; margin-bottom:15px;"),
    ui.img(src="xgb_img/mold_8722.png",
           style="width:100%; max-width:500px; margin-bottom:15px;"),
    ui.img(src="xgb_img/mold_8917.png",
           style="width:100%; max-width:500px; margin-bottom:15px;"),
)

# 9. 최적 하이퍼파라미터 테이블
best_params_table = ui.HTML("""
<table class="table table-bordered table-hover" style="font-size:0.85rem; text-align:center;">
    <thead class="table-secondary">
        <tr>
            <th>금형 코드</th>
            <th>Threshold</th>
            <th>ccp_alpha</th>
            <th>Max Depth</th>
            <th>Max Features</th>
            <th>Min Impurity Decrease</th>
            <th>Min Samples Leaf</th>
            <th>Min Samples Split</th>
            <th>n_estimators</th>
            <th>SMOTE k-neighbors</th>
            <th>SMOTE Sampling Ratio</th>
        </tr>
    </thead>
    <tbody>
        <tr><td>8917</td><td>0.66</td><td>0.000001</td><td>None</td><td>0.5</td><td>0</td><td>6</td><td>10</td><td>100</td><td>9</td><td>0.295</td></tr>
        <tr><td>8412</td><td>0.48</td><td>0.000001</td><td>12</td><td>0.5</td><td>0.00001</td><td>6</td><td>9</td><td>100</td><td>3</td><td>0.366</td></tr>
        <tr><td>8573</td><td>0.66</td><td>0.00002</td><td>16</td><td>0.7</td><td>0.00007</td><td>4</td><td>5</td><td>298</td><td>6</td><td>0.453</td></tr>
        <tr><td>8722</td><td>0.52</td><td>0.000001</td><td>16</td><td>sqrt</td><td>0.00001</td><td>1</td><td>2</td><td>400</td><td>9</td><td>0.5</td></tr>
        <tr><td>8600</td><td>0.22</td><td>0.001</td><td>10</td><td>1</td><td>0.00001</td><td>3</td><td>6</td><td>100</td><td>8</td><td>0.25</td></tr>
    </tbody>
</table>
""")


from shiny import ui

shap_markdown = ui.page_fluid(

                    # 위쪽 2열 (SHAP | Rule)
                    ui.layout_columns(
                        ui.card(
                            ui.card_header("📊 SHAP 신호 계산"),
                            ui.markdown("""
                - **정규화**: `max(0, SHAP값) / 예측확률`  
                - **스코어**: `0.7 × 최댓값 + 0.3 × 평균값`  

                👉 최댓값 = 가장 심각한 / 평균값 = 해당 단계의 평균적인
        
                            """)
                        ),
                        ui.card(
                            ui.card_header("🔎 Rule 신호 계산"),
                            ui.markdown("""
                - **하한선 위반**: `(임계값 - 현재값) / (임계값 - 최솟값)`  
                - **상한선 위반**: `(현재값 - 임계값) / (최댓값 - 임계값)`  
                - **스코어**: `0.7 × 최댓값 + 0.3 × 평균값`  
                            """)
                        ),
                        col_widths=[6, 6]
                    ),

                    # 아래쪽 2열 (왼쪽=경고+설정, 오른쪽=변수별 기여도)
                    ui.layout_columns(
                        # 왼쪽 카드: 경고 등급 기준 + 설정 파라미터
                        ui.card(
                            ui.card_header("🚨 경고 등급 기준 & ⚙️ 설정 파라미터"),
                            ui.markdown("""
                ### 🚨 경고 등급 기준
                | 조건 | 등급 | 의미 |
                |------|------|------|
                | SHAP > 0.15 AND Rule > 0.15 | 강한 원인 후보 | 두 신호 모두 감지 |
                | SHAP > 0.15 OR Rule > 0.15 | 관찰 필요 | 한 신호만 감지 |
                | 둘 다 ≤ 0.15 | 정상 | 이상 없음 |

                ---

                ### ⚙️ 설정 파라미터
                | 파라미터 | 값 | 의미 |
                |----------|----|-----|
                | SHAP 가중치 | 0.5 | AI 신호 비중 |
                | Rule 가중치 | 0.5 | 규칙 신호 비중 |
                | 경고 임계값 | 0.15 | 경고 발생 기준 |
                | 급성/만성 비율 | 7:3 | 최댓값:평균값 비중 |
                            """)
                        ),

                        # 오른쪽 카드: 변수별 기여도 & 적용 예시
                        ui.card(
                            ui.card_header("📊 변수별 기여도 & 적용 예시"),
                            ui.markdown("""
                **중요도 계산**  
                `(SHAP 기여도 + Rule 기여도) / 전체 합계`

                **신호 타입 분류**  
                - 두 신호 모두: SHAP ≥ 0.1 AND Rule ≥ 0.1  
                - SHAP만: SHAP ≥ 0.1 AND Rule < 0.1  
                - Rule만: SHAP < 0.1 AND Rule ≥ 0.1  
                - 약한 신호: 둘 다 < 0.1  
                            """),
                            ui.hr(),
                            ui.markdown("**예시 (Injection 공정)**"),
                            ui.pre("""
                강한 원인 후보 (Score=0.72)

                cast_pressure: SHAP=0.25(30%), Rule=0.67(40%)
                biscuit_thickness: SHAP=0.15(20%), Rule=0.05(5%)
                low_section_speed: SHAP=0.02(2%), Rule=0.12(15%)
                            """),
                            ui.markdown("""
                | SHAP | Rule | Pred |
                |------|------|------|
                | 0.42 | 0.84 | 0.80 |

                👉 cast_pressure: 두 신호 모두 높음 → 즉시 점검 필요  
                👉 biscuit_thickness: SHAP만 감지 → 모니터링 필요
                            """)
                        ),
                        col_widths=[5, 7]  # 왼쪽 좁게, 오른쪽 넓게
                    )
                )



avg_result_table = ui.HTML("""
        <div style="overflow-x:auto;">
        <table class="table table-bordered table-sm table-hover">
            <thead>
                <tr>
                    <th>Model</th><th>Accuracy</th><th>F1 Score</th>
                    <th>F2 Score</th><th>AUC</th><th>Recall (불량=1)</th>
                </tr>
            </thead>
            <tbody>
                <tr><td><b>LightGBM</b></td><td>0.9924</td><td>0.9143</td><td>0.9200</td><td>0.9970</td><td>0.9169</td></tr>
                <tr><td><b>XGBoost</b></td><td>0.9890</td><td>0.8776</td><td>0.8850</td><td>0.9763</td><td>0.8828</td></tr>
                <tr><td><b>Random Forest</b></td><td>0.9930</td><td>0.9286</td><td>0.9504</td><td>0.9935</td><td>0.9663</td></tr>
                <tr><td><b>Logistic Regression</b></td><td>0.9731</td><td>0.7325</td><td>0.7920</td><td>0.9660</td><td>0.8277</td></tr>
                <tr><td><b>Decision Tree</b></td><td>0.9907</td><td>0.9401</td><td>0.9360</td><td>0.9100</td><td>0.9309</td></tr>
            </tbody>
        </table>
        </div>
        """)

each_result_table = ui.HTML("""
        <div style="overflow-x:auto;">
        <table class="table table-bordered table-sm table-hover">
            <thead>
                <tr>
                    <th>Mold Code</th><th>Model</th><th>Accuracy</th>
                    <th>Precision</th><th>Recall</th><th>F1 Score</th>
                    <th>F2 Score</th><th>AUC</th>
                </tr>
            </thead>
            <tbody>
                <tr><td rowspan="3"><b>8412</b></td><td>LightGBM</td><td>0.9970</td><td>0.9457</td><td>0.9683</td><td>0.9569</td><td>0.9631</td><td>0.9997</td></tr>
                <tr><td>XGBoost</td><td>0.9962</td><td>0.9667</td><td>0.9206</td><td>0.9431</td><td>0.9307</td><td>0.9964</td></tr>
                <tr><td><b>RandomForest</b></td><td><b>0.9965</b></td><td><b>0.9313</b></td><td><b>0.9683</b></td><td><b>0.9494</b></td><td><b>0.9606</b></td><td><b>0.9996</b></td></tr>

                <tr><td rowspan="3"><b>8722</b></td><td>LightGBM</td><td>0.9947</td><td>0.9434</td><td>0.9569</td><td>0.9501</td><td>0.9544</td><td>0.9992</td></tr>
                <tr><td>XGBoost</td><td>0.9929</td><td>0.9415</td><td>0.9234</td><td>0.9324</td><td>0.9275</td><td>0.9990</td></tr>
                <tr><td><b>RandomForest</b></td><td><b>0.9948</b></td><td><b>0.9405</b></td><td><b>0.9405</b></td><td><b>0.9405</b></td><td><b>0.9405</b></td><td><b>0.9792</b></td></tr>

                <tr><td rowspan="3"><b>8917</b></td><td>LightGBM</td><td>0.9952</td><td>0.9463</td><td>0.9463</td><td>0.9463</td><td>0.9463</td><td>0.9959</td></tr>
                <tr><td>XGBoost</td><td>0.9954</td><td>0.9510</td><td>0.9463</td><td>0.9487</td><td>0.9475</td><td>0.9929</td></tr>
                <tr><td><b>RandomForest</b></td><td><b>0.9865</b></td><td><b>0.7895</b></td><td><b>1.0000</b></td><td><b>0.8824</b></td><td><b>0.9494</b></td><td><b>0.9963</b></td></tr>

                <tr><td rowspan="3"><b>8573</b></td><td>LightGBM</td><td>0.9948</td><td>0.9405</td><td>0.9405</td><td>0.9405</td><td>0.9405</td><td>0.9975</td></tr>
                <tr><td>XGBoost</td><td>0.9958</td><td>0.9634</td><td>0.9405</td><td>0.9518</td><td>0.9461</td><td>0.9854</td></tr>
                <tr><td><b>RandomForest</b></td><td><b>0.9929</b></td><td><b>0.9022</b></td><td><b>0.9713</b></td><td><b>0.9355</b></td><td><b>0.9566</b></td><td><b>0.9991</b></td></tr>

                <tr><td rowspan="3"><b>8600</b></td><td>LightGBM</td><td>0.9916</td><td>0.9310</td><td>0.9000</td><td>0.9153</td><td>0.9065</td><td>0.9987</td></tr>
                <tr><td>XGBoost</td><td>0.9932</td><td>0.9063</td><td>0.9667</td><td>0.9355</td><td>0.9494</td><td>0.9979</td></tr>
                <tr><td><b>RandomForest</b></td><td><b>0.9941</b></td><td><b>0.9198</b></td><td><b>0.9512</b></td><td><b>0.9353</b></td><td><b>0.9448</b></td><td><b>0.9935</b></td></tr>
            </tbody>
        </table>
        </div>
        """)

feature_markdown = ui.markdown(
            """
            
            # 조정값 계산 알고리즘

            ---

            ## 🎯 목적
            **해당 샘플의 불량 확률 30% 미만으로 낮추기**

            ---

            ## 🔄 프로세스

            ### **1단계: Rule 기반 강제 보정**
            - 상/하한선 위반 변수를 임계값으로 즉시 보정
            - 물리적 제약 조건 충족

            ### **2단계: SHAP 기반 최적화**
            - SHAP 기여도 높은 변수부터 순차 조정
            - 불량률 감소 효과가 큰 변수 우선

            ---

            ## 📐 핵심 파라미터

            | 항목 | 값 | 설명 |
            |:---:|:---:|:---|
            | **조정 스텝** | `0.15σ` | 표준편차의 15% 단위로 조정 |
            | **목표 확률** | `< 30%` | 불량 예측 확률 목표치 |
            | **제약 조건** | `양품 평균` | 평균값 초과 조정 방지 |

            ---
            """
    
)
