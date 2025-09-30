from shiny import ui, render, reactive
from viz.eda_plots import (
    # 변수 분포
    plot_varpair_or_dist_main, plot_varpair_or_dist_fixed,
    # 상관관계
    plot_corr_heatmap_fixed_subset, get_fixed_numeric_cols,
    # 공정별 시계열 탐색 (fixeddata3 전용)
    plot_timeseries_fixed3_by_codes, get_mold_code_levels,
    # 공통 설정
    EXCLUDE_VARS, NONE_LABEL, VAR_LABELS, CAT_VARS,
)
from shared import df as DF_MAIN
from pathlib import Path
import pandas as pd

# ── 데이터 로드 유틸 ─────────────────────────────────────────
def _load_fixed_df():
    try:
        root = Path(__file__).resolve().parents[1]
        data_dir = root / "data"
        for name in ("fixeddata.parquet","fixeddata.csv","fixeddata"):
            p = data_dir / name
            if p.exists():
                return pd.read_parquet(p) if p.suffix.lower()==".parquet" else pd.read_csv(p)
    except Exception as e:
        print("[page_eda] fixeddata load error:", e)
    return None

DF_FIXED = _load_fixed_df()

def _load_fixed3_df():
    """fixeddata3 전체 DataFrame 로드(세부 변수 후보/날짜 범위용)"""
    try:
        root = Path(__file__).resolve().parents[1]
        data_dir = root / "data"
        for name in ("fixeddata3.parquet","fixeddata3.csv","fixeddata3"):
            p = data_dir / name
            if p.exists():
                return pd.read_parquet(p) if p.suffix.lower()==".parquet" else pd.read_csv(p)
    except Exception as e:
        print("[page_eda] fixeddata3 load error:", e)
    return None

DF_FIXED3 = _load_fixed3_df()

def _detect_date_col(df: pd.DataFrame):
    for c in ("date","Date","DATE","datetime","timestamp","time"):
        if c in df.columns: return c
    for c in df.columns:
        try:
            if pd.api.types.is_datetime64_any_dtype(df[c]): return c
        except: pass
    for c in df.columns:
        try:
            s = pd.to_datetime(df[c], errors="coerce", infer_datetime_format=True)
            if s.notna().sum() > 0: return c
        except: pass
    return None

def _load_fixed3_date_range():
    """fixeddata3의 최소~최대 날짜(YYYY-MM-DD)"""
    try:
        df = DF_FIXED3
        if df is None: return None, None
        dcol = _detect_date_col(df) or "date"
        if dcol not in df.columns: return None, None
        s = pd.to_datetime(df[dcol], errors="coerce", infer_datetime_format=True).dropna()
        if s.empty: return None, None
        return s.min().date().isoformat(), s.max().date().isoformat()
    except Exception as e:
        print("[page_eda] fixeddata3 date range error:", e)
        return None, None

DR3_START, DR3_END = _load_fixed3_date_range()

# ── 공정 변수(라벨/그룹) ─────────────────────────────────────
PROCESS_VARS = {
    "① 용탕 준비": ["molten_temp", "molten_volume"],
    "② 반고체 슬러리 제조": ["sleeve_temperature", "EMS_operation_time"],
    "③ 사출 & 금형 충전": [
        "low_section_speed", "high_section_speed", "cast_pressure",
        "biscuit_thickness", "physical_strength",
    ],
    "④ 응고": [
        "upper_mold_temp1", "upper_mold_temp2", "upper_mold_temp3",
        "lower_mold_temp1", "lower_mold_temp2", "lower_mold_temp3",
        "Coolant_temperature",
    ],
}
ALL_PROCESS_VARS = [v for vs in PROCESS_VARS.values() for v in vs]

# ── fixeddata3 전용: 보여줄 변수 화이트리스트(공정별) ─────────────
# ※ 오른쪽 문자열은 fixeddata3의 '영문 컬럼명'과 정확히 일치해야 합니다.
FIXED3_ALLOWED = {
    "① 용탕 준비": [
        "molten_temp",         # 용탕 온도 (℃)
        "molten_volume",       # 용탕 부피 (cm³)
    ],
    "② 반고체 슬러리 제조": [
        "sleeve_temperature",  # 슬리브 온도 (℃)
        "EMS_operation_time",  # EMS 작동시간 (s)
    ],
    "③ 사출 & 금형 충전": [
        "low_section_speed",   # 저속 구간 속도 (mm/s)
        "high_section_speed",  # 고속 구간 속도 (mm/s)
        "cast_pressure",       # 주조 압력 (bar)
        "biscuit_thickness",   # 비스킷 두께 (mm)
        "physical_strength",   # 물리 강도 (kgf)
    ],
    "④ 응고": [
        "upper_mold_temp1",    # 상형 온도1 (℃)
        "upper_mold_temp2",    # 상형 온도2 (℃)
        "lower_mold_temp1",    # 하형 온도1 (℃)
        "lower_mold_temp2",    # 하형 온도2 (℃)
        "Coolant_temperature", # 냉각수 온도 (℃)
    ],
    "기타": [
        "production_no",       # 일자별 생산 번호
        "machine_cycle_time",  # 설비 작동 사이클 시간 (s)
        "product_cycle_time",  # 제품 생산 사이클 시간 (s)
    ],
}

# ── 공정별 optgroup 드롭다운 (DataFrame 기반) ─────────────────
def _grouped_choices_for_dataset(df: pd.DataFrame):
    if df is None or df.empty:
        return {"optgroups": [], "options": []}
    cols = [c for c in df.columns if c not in EXCLUDE_VARS]
    process_cols = set(ALL_PROCESS_VARS)
    group_keys = list(PROCESS_VARS.keys()) + ["기타"]
    optgroups = [{"value": g, "label": g} for g in group_keys]
    options = []
    for g, gcols in PROCESS_VARS.items():
        for c in gcols:
            if c in cols:
                options.append({"value": c, "label": VAR_LABELS.get(c, c), "group": g})
    for c in cols:
        if c not in process_cols:
            options.append({"value": c, "label": VAR_LABELS.get(c, c), "group": "기타"})
    return {"optgroups": optgroups, "options": options}

def _selectize_grouped_by_process(id_, label, df, add_none=False):
    meta = _grouped_choices_for_dataset(df)
    options = meta["options"]
    optgroups = meta["optgroups"]
    if add_none:
        first_group = optgroups[0]["value"] if optgroups else "기타"
        options = [{"value": NONE_LABEL, "label": "선택 없음", "group": first_group}] + options
    selected = None
    for opt in options:
        if opt["value"] != NONE_LABEL:
            selected = opt["value"]; break
    return ui.input_selectize(
        id_, label, choices=[], selected=selected,
        options={
            "options": options,
            "optgroups": optgroups,
            "optgroupField": "group",
            "labelField": "label",
            "valueField": "value",
            "searchField": "label",
            "persist": False,
            "create": False,
        },
    )

# ── fixeddata3 용: 화이트리스트 + 실제 존재 컬럼만 optgroup 생성 ──
def _selectize_grouped_by_process_fixed3_whitelist(id_, label, df_fixed3, add_none=False):
    if df_fixed3 is None or df_fixed3.empty:
        return ui.p("fixeddata3를 찾을 수 없습니다.")
    cols_exist = set(df_fixed3.columns)
    groups = ["① 용탕 준비","② 반고체 슬러리 제조","③ 사출 & 금형 충전","④ 응고","기타"]
    optgroups = [{"value": g, "label": g} for g in groups]
    options = []
    for g in groups:
        for col in FIXED3_ALLOWED.get(g, []):
            if (col in cols_exist) and (col not in EXCLUDE_VARS):
                options.append({
                    "value": col,
                    "label": VAR_LABELS.get(col, col),  # var_labels.csv 매핑 있으면 한글/단위 표기
                    "group": g
                })
    if add_none and optgroups:
        options = [{"value": NONE_LABEL, "label": "선택 없음", "group": optgroups[0]["value"]}] + options

    # 첫 항목 기본 선택
    selected = None
    for opt in options:
        if opt["value"] != NONE_LABEL:
            selected = opt["value"]; break

    return ui.input_selectize(
        id_, label, choices=[], selected=selected,
        options={
            "options": options,
            "optgroups": optgroups,
            "optgroupField": "group",
            "labelField": "label",
            "valueField": "value",
            "searchField": "label",
            "persist": False,
            "create": False,
        },
    )

# ── UI ───────────────────────────────────────────────────────
def page_eda_ui():
    return ui.page_fluid(
        ui.tags.style("""
            #proc_date_range input.form-control { font-size: 0.75rem; }
            .heatwrap { margin-bottom: 6px; }
            .heatgrp { margin-bottom: 6px; padding-bottom: 6px; border-bottom: 1px dashed #e5e7eb; }
            .heatgrp h6 { margin: 6px 0 14px; }
            .heatgrp .form-check { margin-bottom: 2px; }

            /* 간단 가이드 배지(작게) */
            .mini-guide { position: relative; display: inline-block; margin-top: 6px; margin-right: 8px; }
            .mini-guide .badge {
                display: inline-block; padding: 3px 7px; border-radius: 8px;
                background: #eef2ff; color: #1f2937; font-weight: 600; font-size: .78rem;
                border: 1px solid #e5e7eb;
            }
            .mini-guide .panel {
                display: none; position: absolute; z-index: 20; left: 0; top: 115%;
                width: 360px; max-width: 92vw;
                background: #fff; border: 1px solid #e5e7eb; border-radius: 10px;
                box-shadow: 0 10px 24px rgba(0,0,0,.08);
                padding: 10px 12px; font-size: .78rem; line-height: 1.35;
            }
            .mini-guide:hover .panel { display: block; }
            .mini-guide .panel h6 { margin: 0 0 8px; font-size: .82rem; }
            .mini-guide .panel p { margin: 4px 0; white-space: pre-line; }
        """),
        ui.h3("데이터 탐색"),
        ui.navset_tab(
            # 1) 변수 분포
            ui.nav_panel(
                "변수 분포",
                ui.layout_sidebar(
                    ui.sidebar(
                        ui.input_radio_buttons(
                            "dist_mode", "보기 모드",
                            choices={
                                "compare": "분포 비교하기",
                                "main":    "원본 데이터",
                                "fixed":   "전처리 데이터",
                            },
                            selected="compare", inline=True
                        ),
                        ui.output_ui("dist_selectors"),
                        ui.output_ui("simple_guides"),   # 간단 가이드(변수 구분 + 사용법)
                    ),
                    ui.layout_columns(
                        ui.card(
                            ui.card_header("원본 데이터 그래프"),
                            ui.output_plot("dist_plot_primary", width="100%", height="520px")
                        ),
                        ui.card(
                            ui.card_header("전처리 데이터 그래프"),
                            ui.output_plot("dist_plot_secondary", width="100%", height="520px")
                        ),
                        col_widths=(6, 6),
                    ),
                ),
            ),

            # 2) 상관관계 (전처리 only + 초기 자동표시 + HIT으로 갱신)
            ui.nav_panel(
                "상관관계",
                ui.layout_sidebar(
                    ui.sidebar(
                        ui.h5("변수 선택 (전처리 데이터)"),
                        ui.input_checkbox("heat_select_all", "전체 선택", value=True),
                        ui.div(ui.output_ui("heat_var_groups"), class_="heatwrap"),
                        ui.input_action_button("heat_go", "HIT", class_="btn btn-primary"),
                        ui.help_text("처음에는 전체 변수가 표시되고, 이후에는 체크 후 HIT을 눌러 갱신됩니다."),
                    ),
                    ui.card(
                        ui.card_header("상관관계 Heatmap (전처리 데이터, 선택 변수)"),
                        ui.output_plot("corr_heatmap_fixed", width="80%", height="520px"),
                    ),
                ),
            ),

            # 3) 공정별 시계열 탐색 (fixeddata3 전용)
            ui.nav_panel(
                "공정별 시계열 탐색",
                ui.layout_sidebar(
                    ui.sidebar(
                        ui.output_ui("mold_code_selector"),
                        ui.hr(),
                        # ★ 세부 변수: fixeddata3에 '실제로 존재' + 화이트리스트 포함 항목만, 공정별 optgroup으로 단일 선택
                        ui.output_ui("fixed3_var_selector"),
                        ui.input_date_range("proc_date_range", "날짜 범위", start=DR3_START, end=DR3_END),
                        ui.help_text("선택한 mold_code 조합을 색상으로 구분해 1분 단위 시계열을 표시합니다. (x=날짜/시간, y=선택 변수)"),
                    ),
                    ui.card(
                        ui.card_header("시계열 (1분 단위 / 색=mold_code)"),
                        ui.output_plot("process_timeseries", width="100%", height="640px"),
                    ),
                ),
            ),
            id="eda_nav",
        ),
    )

# ── Server ───────────────────────────────────────────────────
def page_eda_server(input, output, session):
    # ---- 변수 분포: 모드별 변수 선택 UI
    @output
    @render.ui
    def dist_selectors():
        mode = input.dist_mode()
        if mode == "main":
            return ui.TagList(
                _selectize_grouped_by_process("dist_var1", "변수 선택 1", DF_MAIN, add_none=False),
                _selectize_grouped_by_process("dist_var2", "변수 선택 2", DF_MAIN, add_none=True),
            )
        elif mode == "fixed":
            if DF_FIXED is None:
                return ui.p("전처리 데이터(fixeddata)를 찾을 수 없습니다.")
            return ui.TagList(
                _selectize_grouped_by_process("dist_var1", "변수 선택 1", DF_FIXED, add_none=False),
                _selectize_grouped_by_process("dist_var2", "변수 선택 2", DF_FIXED, add_none=True),
            )
        else:  # compare (전처리 변수만으로 선택)
            if DF_FIXED is None:
                return ui.p("전처리 데이터(fixeddata)를 찾을 수 없습니다.")
            return ui.TagList(
                _selectize_grouped_by_process("dist_var1", "변수 선택 1 (전처리 변수)", DF_FIXED, add_none=False),
                _selectize_grouped_by_process("dist_var2", "변수 선택 2 (전처리 변수)", DF_FIXED, add_none=True),
            )

    # ---- 간단 가이드(변수 구분 + 사용법) : hover 배지 2개
    @output
    @render.ui
    def simple_guides():
        mode = input.dist_mode()
        df = DF_FIXED if mode in ("fixed", "compare") else DF_MAIN

        if df is None or df.empty:
            cats_kr = "데이터 없음"
            nums_kr = "데이터 없음"
        else:
            cols = [c for c in df.columns if c not in EXCLUDE_VARS]
            cat_cols, num_cols = [], []
            for c in cols:
                is_num = False
                if c in CAT_VARS:
                    is_num = False
                else:
                    try:
                        is_num = pd.api.types.is_numeric_dtype(df[c])
                    except Exception:
                        is_num = False
                if is_num: num_cols.append(c)
                else:      cat_cols.append(c)

            cats_kr = "\n".join(sorted([VAR_LABELS.get(c, c) for c in cat_cols]))
            nums_kr = "\n".join(sorted([VAR_LABELS.get(c, c) for c in num_cols]))

        return ui.HTML(f"""
          <div>
            <div class="mini-guide" aria-label="변수 구분">
              <span class="badge">변수 구분</span>
              <div class="panel">
                <h6>범주형 변수:</h6>
                <p>{cats_kr if cats_kr else '-'}</p>
                <br>
                <h6>수치형 변수:</h6>
                <p>{nums_kr if nums_kr else '-'}</p>
              </div>
            </div>
            <div class="mini-guide" aria-label="사용법">
              <span class="badge">사용법</span>
              <div class="panel">
                <p style="margin:0;">변수 &amp; 선택 없음 
                : 분포 그래프</p>
                <p style="margin:6px 0 0;">수치형 &amp; 범주형 
                : 박스 플롯</p>
                <p style="margin:6px 0 0;">수치형 &amp; 수치형 
                : 산점도 분포 그래프</p>
              </div>
            </div>
          </div>
        """)

    # ---- 변수 분포: 플롯 렌더링
    @output
    @render.plot
    def dist_plot_primary():
        mode = input.dist_mode(); v1 = input.dist_var1(); v2 = input.dist_var2()
        if mode == "main":
            return plot_varpair_or_dist_main(v1, v2)
        elif mode == "fixed":
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(); ax.axis("off"); ax.text(0.5,0.5,"전처리 모드에서는 오른쪽 그래프만 사용합니다.",ha="center",va="center"); return fig
        else:
            return plot_varpair_or_dist_main(v1, v2)

    @output
    @render.plot
    def dist_plot_secondary():
        mode = input.dist_mode(); v1 = input.dist_var1(); v2 = input.dist_var2()
        if mode in ("compare","fixed"):
            return plot_varpair_or_dist_fixed(v1, v2)
        else:
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(); ax.axis("off"); ax.text(0.5,0.5,"원본 모드에서는 왼쪽 그래프만 사용합니다.",ha="center",va="center"); return fig

    # ---- 상관관계: 초기 자동표시 + 이후 HIT으로만 갱신
    @output
    @render.ui
    def heat_var_groups():
        num_cols = get_fixed_numeric_cols()
        if not num_cols:
            return ui.p("전처리 데이터(fixeddata)가 없거나 숫자형 컬럼이 없습니다.")
        num_set = set(num_cols)
        groups, used = {}, set()
        for g, cols in PROCESS_VARS.items():
            arr = [c for c in cols if c in num_set]
            groups[g] = arr; used.update(arr)
        misc = sorted([c for c in num_cols if c not in used])
        groups["기타"] = misc

        def _choices_dict(cols):
            return {c: VAR_LABELS.get(c, c) for c in cols}

        out = []
        for g in ["① 용탕 준비","② 반고체 슬러리 제조","③ 사출 & 금형 충전","④ 응고","기타"]:
            cols = groups.get(g, [])
            if not cols: continue
            out.append(
                ui.div(
                    ui.h6(g),
                    ui.input_checkbox_group(
                        f"heat_vars_{hash(g)%100000}", "",
                        choices=_choices_dict(cols),
                        selected=cols, inline=False
                    ),
                    class_="heatgrp"
                )
            )
        return ui.TagList(*out)

    def _collect_heat_vars():
        selected = []
        for g in ["① 용탕 준비","② 반고체 슬러리 제조","③ 사출 & 금형 충전","④ 응고","기타"]:
            gid = f"heat_vars_{hash(g)%100000}"
            vals = getattr(input, gid)()
            if vals: selected.extend(vals)
        seen = set(); dedup = []
        for v in selected:
            if v not in seen:
                seen.add(v); dedup.append(v)
        return dedup

    @output
    @render.plot
    def corr_heatmap_fixed():
        clicks = input.heat_go()
        if clicks is None or clicks == 0:
            selected = get_fixed_numeric_cols()
        else:
            selected = _collect_heat_vars() or get_fixed_numeric_cols()
        return plot_corr_heatmap_fixed_subset(selected)

    # ---- 공정별 시계열 탐색 (fixeddata3 전용)
    @output
    @render.ui
    def mold_code_selector():
        levels = get_mold_code_levels()
        return ui.input_checkbox_group(
            "mold_codes", "mold_code (복수)", choices=levels, selected=levels, inline=False
        )

    @output
    @render.ui
    def fixed3_var_selector():
        """세부 변수 (fixeddata3 / 단일 선택) — 화이트리스트 + 실제 존재 컬럼만 공정별로 표시"""
        return _selectize_grouped_by_process_fixed3_whitelist(
            "proc_single_var", "세부 변수", DF_FIXED3, add_none=False
        )

    @output
    @render.plot
    def process_timeseries():
        # x: 날짜(분 단위, 내부에서 resample) / y: 선택 변수
        yvar   = input.proc_single_var()
        codes  = input.mold_codes() or []
        dr     = input.proc_date_range()
        start  = dr[0] if dr and dr[0] else None
        end    = dr[1] if dr and dr[1] else None
        return plot_timeseries_fixed3_by_codes(yvar, codes, start, end)
