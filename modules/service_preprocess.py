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
    ui.img(src="xgb_img/8412.PNG",
           style="width:100%; max-width:500px; margin-bottom:15px;"),
    ui.img(src="xgb_img/8573.PNG",
           style="width:100%; max-width:500px; margin-bottom:15px;"),
    ui.img(src="xgb_img/8600.PNG",
           style="width:100%; max-width:500px; margin-bottom:15px;"),
    ui.img(src="xgb_img/8722.PNG",
           style="width:100%; max-width:500px; margin-bottom:15px;"),
    ui.img(src="xgb_img/8917.PNG",
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
