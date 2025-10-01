# modules/page_eda.py
from shiny import ui, render, reactive
from viz.eda_plots import (
    # 변수 분포
    plot_varpair_or_dist_main, plot_varpair_or_dist_fixed,
    # 상관관계 (전처리 only)
    plot_corr_heatmap_fixed_subset, get_fixed_numeric_cols,
    # 공정별 시계열 (Plotly HTML)
    plot_timeseries_fixed3_plotly_html, get_mold_code_levels,
    # 공통 설정
    EXCLUDE_VARS, NONE_LABEL, VAR_LABELS, CAT_VARS,
)
from shared import df as DF_MAIN
from pathlib import Path
import pandas as pd

# ── fixeddata ─────────────────────────────────────────
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

# ── fixeddata3: 날짜 범위용(최소/최대) ─────────────────────────
def _fixed3_path():
    root = Path(__file__).resolve().parents[1]
    data_dir = root / "data"
    for name in ("fixeddata3.parquet","fixeddata3.csv","fixeddata3"):
        p = data_dir / name
        if p.exists():
            return p
    return None

def _detect_date_col(df: pd.DataFrame):
    for c in ("date","Date","DATE","datetime","timestamp","time"):
        if c in df.columns: return c
    for c in df.columns:
        try:
            if pd.api.types.is_datetime64_any_dtype(df[c]): return c
        except: pass
    for c in df.columns:
        try:
            s = pd.to_datetime(df[c], errors="coerce")
            if s.notna().sum() > 0: return c
        except: pass
    return None

def _load_fixed3_date_range():
    """fixeddata3의 최소~최대 날짜(YYYY-MM-DD)"""
    try:
        p = _fixed3_path()
        if p is None: return None, None
        if p.suffix.lower() == ".parquet":
            df = pd.read_parquet(p, columns=["date"])
        else:
            df = pd.read_csv(p, usecols=["date"])
        if "date" not in df.columns: return None, None
        s = pd.to_datetime(df["date"], errors="coerce").dropna()
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
GROUPS_ORDER = ["① 용탕 준비","② 반고체 슬러리 제조","③ 사출 & 금형 충전","④ 응고","기타"]

# ── 공정별 optgroup 드롭다운 (DataFrame 기반) ────────────────
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
    options = meta["options"]; optgroups = meta["optgroups"]
    if add_none:
        first_group = optgroups[0]["value"] if optgroups else "기타"
        options = [{"value": NONE_LABEL, "label": "선택 없음", "group": first_group}] + options
    selected = next((o["value"] for o in options if o["value"] != NONE_LABEL), None)
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

# ── fixeddata3 화이트리스트(세부 변수) ───────────────────────
FIXED3_ALLOWED = {
    "① 용탕 준비": ["molten_temp","molten_volume"],
    "② 반고체 슬러리 제조": ["sleeve_temperature","EMS_operation_time"],
    "③ 사출 & 금형 충전": ["low_section_speed","high_section_speed","cast_pressure","biscuit_thickness","physical_strength"],
    "④ 응고": ["upper_mold_temp1","upper_mold_temp2","lower_mold_temp1","lower_mold_temp2","Coolant_temperature"],
    "기타": ["production_no","machine_cycle_time","product_cycle_time"],
}

def _selectize_grouped_by_process_fixed3_whitelist(id_, label, df_fixed3_like_has_cols, add_none=False):
    """df_fixed3_like_has_cols는 columns 속성만 있으면 됩니다(실제 데이터 필요 X)."""
    if df_fixed3_like_has_cols is None:
        return ui.p("fixeddata3를 찾을 수 없습니다.")
    cols_exist = set(df_fixed3_like_has_cols.columns)
    groups = GROUPS_ORDER
    optgroups = [{"value": g, "label": g} for g in groups]
    options = []
    for g in groups:
        for col in FIXED3_ALLOWED.get(g, []):
            if (col in cols_exist) and (col not in EXCLUDE_VARS):
                options.append({"value": col, "label": VAR_LABELS.get(col, col), "group": g})
    if add_none and optgroups:
        options = [{"value": NONE_LABEL, "label": "선택 없음", "group": optgroups[0]["value"]}] + options
    selected = next((o["value"] for o in options if o["value"] != NONE_LABEL), None)
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

# ── “상관관계-전체선택” 토글에 쓰는 그룹→컬럼 도우미 ─────────────
def _heat_group_map():
    num_cols = set(get_fixed_numeric_cols())
    groups = {}
    used = set()
    for g, cols in PROCESS_VARS.items():
        arr = [c for c in cols if c in num_cols]
        groups[g] = arr
        used.update(arr)
    misc = sorted([c for c in num_cols if c not in used])
    groups["기타"] = misc
    return groups

# ── fixeddata3의 “사용 가능 컬럼 목록”만 얻는 얇은 객체 ──────────
def _fixed3_columns_view():
    p = _fixed3_path()
    if p is None:
        return None
    try:
        if p.suffix.lower() == ".parquet":
            import pyarrow.parquet as pq
            schema = pq.ParquetFile(str(p)).schema_arrow
            cols = [n for n in schema.names]
            return type("ColsOnly", (), {"columns": cols})()
        else:
            # CSV 헤더만
            import csv
            with open(p, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader)
            return type("ColsOnly", (), {"columns": header})()
    except Exception:
        # fallback: 가볍게 전체 로드 후 columns만
        if p.suffix.lower() == ".parquet":
            df = pd.read_parquet(p, nrows=1)
        else:
            df = pd.read_csv(p, nrows=1)
        return type("ColsOnly", (), {"columns": list(df.columns)})()

# ── UI ───────────────────────────────────────────────────────
def page_eda_ui():
    return ui.page_fluid(
        ui.tags.style("""
            #proc_date_range input.form-control { font-size: 0.75rem; }
            .heatwrap { margin-bottom: 6px; }
            .heatgrp { margin-bottom: 6px; padding-bottom: 6px; border-bottom: 1px dashed #e5e7eb; }
            .heatgrp h6 { margin: 6px 0 14px; }
            .heatgrp .form-check { margin-bottom: 2px; }

            .mini-guide { position: relative; display: inline-block; margin-top: 6px; margin-right: 8px; }
            .mini-guide .badge { display: inline-block; padding: 3px 7px; border-radius: 8px;
                background: #eef2ff; color: #1f2937; font-weight: 600; font-size: .78rem;
                border: 1px solid #e5e7eb; }
            .mini-guide .panel { display: none; position: absolute; z-index: 20; left: 0; top: 115%;
                width: 360px; max-width: 92vw; background: #fff; border: 1px solid #e5e7eb;
                border-radius: 10px; box-shadow: 0 10px 24px rgba(0,0,0,.08);
                padding: 10px 12px; font-size: .78rem; line-height: 1.35; }
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
                            choices={"compare": "분포 비교하기","main": "원본 데이터","fixed": "전처리 데이터"},
                            selected="compare", inline=True
                        ),
                        ui.output_ui("dist_selectors"),
                        ui.output_ui("simple_guides"),
                    ),
                    ui.layout_columns(
                        ui.card(ui.card_header("원본 데이터 그래프"),
                                ui.output_plot("dist_plot_primary", width="100%", height="520px")),
                        ui.card(ui.card_header("전처리 데이터 그래프"),
                                ui.output_plot("dist_plot_secondary", width="100%", height="520px")),
                        col_widths=(6, 6),
                    ),
                ),
            ),

            # 2) 상관관계 (전처리 only + 초기 자동표시 + HIT으로만 갱신)
            ui.nav_panel(
                "상관관계",
                ui.layout_sidebar(
                    ui.sidebar(
                        ui.h5("변수 선택"),
                        ui.input_checkbox("heat_select_all", "전체 선택", value=True),
                        ui.div(ui.output_ui("heat_var_groups"), class_="heatwrap"),
                        ui.input_action_button("heat_go", "HIT", class_="btn btn-primary"),
                        ui.help_text("원하는 변수 체크 변경 후 HIT을 눌러 갱신하세요."),
                    ),
                    ui.card(
                        ui.card_header("상관관계 Heatmap"),
                        ui.output_plot("corr_heatmap_fixed", width="80%", height="520px"),
                    ),
                ),
            ),

            # 3) 공정별 시계열 탐색 (fixeddata3 + Plotly HTML)
            ui.nav_panel(
                "공정별 시계열 탐색",
                ui.layout_sidebar(
                    ui.sidebar(
                        ui.output_ui("mold_code_selector"),
                        ui.hr(),
                        ui.output_ui("fixed3_var_selector"),  # 단일 선택 (optgroup)
                        ui.input_date_range("proc_date_range", "날짜 범위", start=DR3_START, end=DR3_END),
                        ui.help_text("선택한 금형 코드를 색으로 구분해 시계열을 표시합니다."),
                    ),
                    ui.card(
                        ui.card_header("시계열 공정별 변수 탐색"),
                        ui.output_ui("process_timeseries", width="100%", height="auto"),
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
        else:
            if DF_FIXED is None:
                return ui.p("전처리 데이터(fixeddata)를 찾을 수 없습니다.")
            return ui.TagList(
                _selectize_grouped_by_process("dist_var1", "변수 선택 1", DF_FIXED, add_none=False),
                _selectize_grouped_by_process("dist_var2", "변수 선택 2", DF_FIXED, add_none=True),
            )

    # ---- 간단 가이드(변수 구분 + 사용법)
    @output
    @render.ui
    def simple_guides():
        mode = input.dist_mode()
        df = DF_FIXED if mode in ("fixed", "compare") else DF_MAIN
        if df is None or df.empty:
            cats_kr = "데이터 없음"; nums_kr = "데이터 없음"
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
                (num_cols if is_num else cat_cols).append(c)
            cats_kr = "\n".join(sorted([VAR_LABELS.get(c, c) for c in cat_cols]))
            nums_kr = "\n".join(sorted([VAR_LABELS.get(c, c) for c in num_cols]))
        return ui.HTML(f"""
          <div>
            <div class="mini-guide" aria-label="변수 구분">
              <span class="badge">변수 구분</span>
              <div class="panel">
                <h6>범주형 변수:</h6>
                <p>{cats_kr or '-'}</p>
                <br>
                <h6>수치형 변수:</h6>
                <p>{nums_kr or '-'}</p>
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

    # ---- 변수 분포: 플롯
    @output
    @render.plot
    def dist_plot_primary():
        mode = input.dist_mode(); v1 = input.dist_var1(); v2 = input.dist_var2()
        if mode == "main":
            return plot_varpair_or_dist_main(v1, v2)
        elif mode == "fixed":
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(); ax.axis("off")
            ax.text(0.5,0.5,"전처리 모드에서는 오른쪽 그래프만 사용합니다.",ha="center",va="center")
            return fig
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
            fig, ax = plt.subplots(); ax.axis("off")
            ax.text(0.5,0.5,"원본 모드에서는 왼쪽 그래프만 사용합니다.",ha="center",va="center")
            return fig

    # ---- 상관관계: 체크리스트 UI (초기엔 전부 체크)
    @output
    @render.ui
    def heat_var_groups():
        num_cols = get_fixed_numeric_cols()
        if not num_cols:
            return ui.p("전처리 데이터(fixeddata)가 없거나 숫자형 컬럼이 없습니다.")
        groups = _heat_group_map()

        def _choices_dict(cols):
            return {c: VAR_LABELS.get(c, c) for c in cols}

        out = []
        for g in GROUPS_ORDER:
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

    # ---- “전체 선택” 토글: 체크리스트 전체 on/off (히트맵은 HIT으로만 갱신)
    @reactive.Effect
    @reactive.event(input.heat_select_all)
    def _toggle_all_heat():
        sel_all = input.heat_select_all()
        groups = _heat_group_map()
        for g in GROUPS_ORDER:
            cols = groups.get(g, [])
            gid = f"heat_vars_{hash(g)%100000}"
            try:
                ui.update_checkbox_group(session, gid, selected=(cols if sel_all else []))  # type: ignore
            except Exception:
                session.send_input_message(gid, {"value": (cols if sel_all else [])})

    # ---- 히트맵 렌더 (오직 HIT 클릭 시에만 갱신, 최초는 전체)
    @output
    @render.plot
    @reactive.event(input.heat_go)
    def corr_heatmap_fixed():
        selected = []
        for g in GROUPS_ORDER:
            gid = f"heat_vars_{hash(g)%100000}"
            vals = getattr(input, gid)()
            if vals: selected.extend(vals)
        if not selected:
            selected = get_fixed_numeric_cols()
        return plot_corr_heatmap_fixed_subset(selected)

    # 최초 진입시 전체 히트맵 1회 표시를 위해(사용자가 안 눌러도 보이도록)
    # -> UI 카드에 기본 메시지가 뜨지 않게끔, 첫 로드에 trigger
    @reactive.Effect
    def _auto_hit_once():
        # 페이지 첫 로드 시에만 한 번 실행
        if input.heat_go() == 0:
            session.send_input_message("heat_go", {"value": 1})

    # ---- 공정별 시계열 탐색 (Plotly HTML)
    @output
    @render.ui
    def mold_code_selector():
        levels = get_mold_code_levels()
        return ui.input_checkbox_group(
            "mold_codes", "금형코드", choices=levels, selected=levels, inline=False
        )

    @output
    @render.ui
    def fixed3_var_selector():
        cols_view = _fixed3_columns_view()
        return _selectize_grouped_by_process_fixed3_whitelist(
            "proc_single_var", "변수 선택", cols_view, add_none=False
        )

    @output
    @render.ui
    def process_timeseries():
        # Plotly Figure는 shinywidgets 없이 HTML로 렌더해야 comm 오류가 없습니다.
        yvar   = input.proc_single_var()
        codes  = input.mold_codes() or []
        dr     = input.proc_date_range()
        start  = dr[0] if dr and dr[0] else None
        end    = dr[1] if dr and dr[1] else None
        html = plot_timeseries_fixed3_plotly_html(yvar, codes, start, end)
        return ui.HTML(html)
