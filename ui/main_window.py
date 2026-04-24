import tkinter as tk
import re
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from tkinter import filedialog, messagebox, ttk

from calc_logic.analysis_service import AnalysisService
from calc_logic.economic_assumption_registry import (
    ECONOMIC_ASSUMPTION_ORDER,
)
from calc_logic.expense_planning_engine import (
    calculate_expense_plan_summary,
    resolve_category_total,
    sum_detail_values,
)
from calc_logic.home_purchase_engine import calculate_home_purchase_plan
from calc_logic.sample_value_builder import build_reference_sample_values
from calc_logic.special_goal_engine import build_special_goal_saving_plan
from config import (
    CATEGORY_LABELS,
    DEFAULT_HOME_PURCHASE_GOAL,
    EXPENSE_ALLOCATION_ORDER,
    EXPENSE_DETAIL_LABELS,
    EXPENSE_DETAIL_MULTIPLIERS,
    INSURANCE_PRODUCT_LABELS,
    PRODUCT_INPUT_GROUPS,
    PRODUCT_LABELS,
)
from economic_context.service import CurrentEconomicContextService
from housing_context.service import CurrentHomeLoanContextService
from input_logic.input_mapper import map_to_profile
from input_logic.validators import ECONOMIC_ASSUMPTION_LABELS, validate_raw_input
from output_logic.file_name_builder import (
    build_input_filename,
    build_report_filename,
    build_word_report_filename,
)
from output_logic.report_builder import dumps_report
from output_logic.source_report_builder import build_source_report_text
from output_logic.sentence_builder import build_summary_text
from output_logic.table_builder import build_analysis_tables
from output_logic.word_report_builder import write_word_report
from storage.profile_store import load_profile, save_profile
from ui.window_icon import apply_window_icon


RESULT_NEGATIVE_PATTERNS = (
    r"기준 ?보다 낮아",
    r"낮습니다",
    r"낮음",
    r"부족(?:액)?",
    r"적자",
    r"불량",
    r"위험",
    r"초과",
    r"과다",
    r"경고",
)

RESULT_POSITIVE_PATTERNS = (
    r"양호",
    r"강점",
    r"안정적?",
    r"우수",
    r"적정",
    r"여유",
)


class FinancialPlannerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("가구 기준 비교형 재무설계")
        self.applied_icon_path = apply_window_icon(self)
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        default_width = max(1280, min(1900, screen_width - 80))
        default_height = max(860, min(980, screen_height - 120))
        self.geometry(f"{default_width}x{default_height}")
        self.service = AnalysisService()
        self.economic_context_service = CurrentEconomicContextService()
        self.home_loan_context_service = CurrentHomeLoanContextService()
        self.main_panedwindow = None
        self.inputs = {}
        self.economic_inputs = {}
        self.category_inputs = {}
        self.expense_detail_inputs = {}
        self.expense_output_vars = {}
        self.expense_allocation_rows_frame = None
        self.product_inputs = {}
        self.insurance_inputs = {}
        self.home_purchase_inputs = {}
        self.home_purchase_output_vars = {}
        self.pension_inputs = {}
        self.pension_output_vars = {}
        self.special_goal_rows_frame = None
        self.goal_rows = []
        self.fixed_home_goal_row = None
        self.numeric_entries = set()
        self._syncing_home_goal = False
        self.table_canvas = None
        self.table_container = None
        self.table_window_id = None
        self.source_report_text = None
        self.input_tab_marker_image = None
        self.last_profile = None
        self.last_analysis = None
        self._build_ui()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        main = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        main.grid(row=0, column=0, sticky="nsew")
        self.main_panedwindow = main

        left = ttk.Frame(main, padding=10, width=320)
        right = ttk.Frame(main, padding=10, width=1280)
        main.add(left, weight=1)
        main.add(right, weight=8)

        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)
        right.rowconfigure(2, weight=1)

        notebook_frame = ttk.Frame(left)
        notebook_frame.grid(row=0, column=0, sticky="nsew")
        notebook_frame.columnconfigure(0, weight=1)
        notebook_frame.rowconfigure(1, weight=1)

        ttk.Label(
            notebook_frame,
            text="※ [입력] 탭은 분석 전에 입력이 필요합니다.",
            foreground="#0f5cc0",
            justify="left",
        ).grid(row=0, column=0, sticky="w", pady=(0, 6))

        notebook = ttk.Notebook(notebook_frame)
        notebook.grid(row=1, column=0, sticky="nsew")

        basic_tab = ttk.Frame(notebook, padding=10)
        expense_tab = ttk.Frame(notebook, padding=10)
        product_tab = ttk.Frame(notebook, padding=10)
        pension_tab = ttk.Frame(notebook, padding=10)
        special_goal_tab = ttk.Frame(notebook, padding=10)
        source_tab = ttk.Frame(notebook, padding=10)

        notebook.add(basic_tab, text="[입력] 기본정보")
        notebook.add(expense_tab, text="[입력] 소비 항목")
        notebook.add(product_tab, text="[입력] 상품 구분")
        notebook.add(pension_tab, text="[입력] 연금")
        self._mark_input_notebook_tabs(notebook, (basic_tab, expense_tab, product_tab, pension_tab))

        notebook.add(special_goal_tab, text="특별 목표자금")

        self._build_basic_tab(basic_tab)
        self._build_expense_tab(expense_tab)
        self._build_product_tab(product_tab)
        self._build_pension_tab(pension_tab)
        self._build_special_goal_tab(special_goal_tab)

        notebook.add(source_tab, text="자료 근거")
        self._build_source_report_tab(source_tab)

        button_bar = ttk.Frame(left, padding=(0, 10, 0, 0))
        button_bar.grid(row=1, column=0, sticky="ew")
        for index in range(6):
            button_bar.columnconfigure(index, weight=1)

        ttk.Button(button_bar, text="예시값 채우기", command=self.fill_sample).grid(row=0, column=0, sticky="ew", padx=3)
        analysis_style = ttk.Style(self)
        analysis_style.configure("Analysis.TButton", font=("맑은 고딕", 9, "bold"))
        analysis_button_frame = tk.Frame(button_bar, bg="#0f6cbd", highlightthickness=0, bd=0)
        analysis_button_frame.grid(row=0, column=1, sticky="ew", padx=3)
        analysis_button_frame.columnconfigure(0, weight=1)
        ttk.Button(
            analysis_button_frame,
            text="분석 실행",
            command=self.run_analysis,
            style="Analysis.TButton",
        ).grid(row=0, column=0, sticky="ew", padx=1, pady=1)
        ttk.Button(button_bar, text="입력 저장", command=self.save_input).grid(row=0, column=2, sticky="ew", padx=3)
        ttk.Button(button_bar, text="입력 불러오기", command=self.load_input).grid(row=0, column=3, sticky="ew", padx=3)
        ttk.Button(button_bar, text="결과 JSON 저장", command=self.save_report).grid(row=0, column=4, sticky="ew", padx=3)
        ttk.Button(button_bar, text="워드 저장", command=self.save_word_report).grid(row=0, column=5, sticky="ew", padx=3)

        ttk.Label(right, text="분석 결과", font=("맑은 고딕", 12, "bold")).grid(row=0, column=0, sticky="w")
        self.result_text = tk.Text(right, wrap="word", font=("맑은 고딕", 10))
        self.result_text.grid(row=1, column=0, sticky="nsew")
        self._configure_result_text_tags()
        scrollbar = ttk.Scrollbar(right, orient="vertical", command=self.result_text.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.result_text.configure(yscrollcommand=scrollbar.set)
        comparison_frame = ttk.LabelFrame(right, text="비교표", padding=8)
        comparison_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(10, 0))
        comparison_frame.columnconfigure(0, weight=1)
        comparison_frame.rowconfigure(1, weight=1)

        ttk.Label(
            comparison_frame,
            text="연한 초록은 양호, 연한 빨강은 불량, 흰색은 참고 또는 점검 항목입니다.",
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        self.table_canvas = tk.Canvas(comparison_frame, highlightthickness=0)
        table_scrollbar = ttk.Scrollbar(comparison_frame, orient="vertical", command=self.table_canvas.yview)
        self.table_canvas.grid(row=1, column=0, sticky="nsew")
        table_scrollbar.grid(row=1, column=1, sticky="ns")
        self.table_canvas.configure(yscrollcommand=table_scrollbar.set)

        self.table_container = ttk.Frame(self.table_canvas, padding=(0, 0, 6, 0))
        self.table_window_id = self.table_canvas.create_window((0, 0), window=self.table_container, anchor="nw")
        self.table_container.columnconfigure(0, weight=1)
        self.table_container.bind("<Configure>", self._on_table_frame_configure)
        self.table_canvas.bind("<Configure>", self._on_table_canvas_configure)

        ttk.Label(self.table_container, text="분석 실행 후 비교표가 여기에 표시됩니다.").grid(row=0, column=0, sticky="w")

        self.status_var = tk.StringVar(value="준비됨")
        ttk.Label(right, textvariable=self.status_var).grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))
        self.after_idle(self._set_initial_pane_layout)

    def _on_table_frame_configure(self, _event=None):
        if self.table_canvas is not None:
            self.table_canvas.configure(scrollregion=self.table_canvas.bbox("all"))

    def _set_initial_pane_layout(self):
        if self.main_panedwindow is None:
            return

        total_width = self.main_panedwindow.winfo_width() or self.winfo_width()
        if total_width <= 0:
            return

        left_width = max(240, int(total_width * 0.14))
        max_left_width = max(240, total_width - 980)
        left_width = min(left_width, max_left_width)

        try:
            self.main_panedwindow.sashpos(0, left_width)
        except tk.TclError:
            return

    def _on_table_canvas_configure(self, event):
        if self.table_canvas is not None and self.table_window_id is not None:
            self.table_canvas.itemconfigure(self.table_window_id, width=event.width)

    def _get_input_tab_marker_image(self):
        if self.input_tab_marker_image is None:
            marker = tk.PhotoImage(width=10, height=10)
            marker.put("#0f5cc0", to=(0, 0, 10, 10))
            self.input_tab_marker_image = marker
        return self.input_tab_marker_image

    def _mark_input_notebook_tabs(self, notebook, tabs):
        marker = self._get_input_tab_marker_image()
        for tab in tabs:
            try:
                notebook.tab(tab, image=marker, compound="left")
            except tk.TclError:
                continue
            try:
                notebook.tab(tab, foreground="#0f5cc0")
            except tk.TclError:
                pass

    def _table_tone_background(self, tone: str) -> str:
        tone_map = {
            "good": "#e6f4ea",
            "bad": "#fbe4e6",
            "neutral": "#ffffff",
        }
        return tone_map.get(tone, "#ffffff")

    def _render_comparison_tables(self, profile, analysis):
        if self.table_container is None:
            return

        for child in self.table_container.winfo_children():
            child.destroy()

        tables = build_analysis_tables(profile, analysis)
        if not tables:
            ttk.Label(self.table_container, text="표시할 비교표가 없습니다.").grid(row=0, column=0, sticky="w")
            self._on_table_frame_configure()
            return

        for index, table in enumerate(tables):
            section = ttk.LabelFrame(self.table_container, text=table["title"], padding=10)
            section.grid(row=index, column=0, sticky="ew", pady=(0, 10))
            section.columnconfigure(0, weight=1)

            if table.get("description"):
                ttk.Label(section, text=table["description"], wraplength=880).grid(
                    row=0,
                    column=0,
                    sticky="w",
                    pady=(0, 8),
                )

            grid_frame = tk.Frame(section, bg="#d0d7de", highlightthickness=0)
            grid_frame.grid(row=1, column=0, sticky="ew")

            for column_index, column in enumerate(table["columns"]):
                grid_frame.grid_columnconfigure(column_index, weight=column.get("weight", 1))
                tk.Label(
                    grid_frame,
                    text=column["title"],
                    bg="#f3f4f6",
                    font=("맑은 고딕", 9, "bold"),
                    anchor=column.get("anchor", "w"),
                    padx=6,
                    pady=5,
                    borderwidth=1,
                    relief="solid",
                ).grid(row=0, column=column_index, sticky="nsew")

            for row_index, row in enumerate(table["rows"], start=1):
                background = self._table_tone_background(row.get("tone", "neutral"))
                for column_index, column in enumerate(table["columns"]):
                    value = row["values"].get(column["id"], "")
                    tk.Label(
                        grid_frame,
                        text=value,
                        bg=background,
                        anchor=column.get("anchor", "w"),
                        justify="right" if column.get("anchor") == "e" else "left",
                        padx=6,
                        pady=5,
                        borderwidth=1,
                        relief="solid",
                    ).grid(row=row_index, column=column_index, sticky="nsew")

        self.table_canvas.yview_moveto(0.0)
        self._on_table_frame_configure()

    def _build_basic_tab(self, frame):
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        self._build_identity_section(frame)
        self._build_financial_section(frame)
        self._build_economic_section(frame)
        self._build_special_goal_section(frame)
        self._on_marital_status_change()

    def _create_section(self, parent, title, row, column):
        section = ttk.LabelFrame(parent, text=title, padding=10)
        section.grid(row=row, column=column, sticky="nsew", padx=6, pady=6)
        section.columnconfigure(1, weight=1)
        return section

    def _add_entry(
        self,
        parent,
        row,
        label,
        key,
        default="",
        numeric=False,
        on_blur=None,
        container=None,
        label_width=None,
        entry_padx=(4, 0),
        entry_width=14,
        stretch=False,
    ):
        label_kwargs = {"text": label}
        if label_width is not None:
            label_kwargs["width"] = label_width
        ttk.Label(parent, **label_kwargs).grid(row=row, column=0, sticky="w", pady=4)
        entry = ttk.Entry(parent, width=entry_width)
        entry.grid(row=row, column=1, sticky="ew" if stretch else "w", pady=4, padx=entry_padx)
        self._set_entry_value(entry, default, numeric=numeric)
        target = container if container is not None else self.inputs
        target[key] = entry
        if numeric:
            self._bind_numeric_entry(entry, on_blur=on_blur)
        else:
            self._bind_apply_on_enter(entry, callback=on_blur)
        return entry

    def _add_numeric_entry(
        self,
        parent,
        row,
        label,
        target_dict,
        key,
        default="0",
        on_blur=None,
        label_width=None,
        entry_padx=(4, 0),
        entry_width=14,
        stretch=False,
    ):
        return self._add_entry(
            parent,
            row,
            label,
            key,
            default,
            numeric=True,
            on_blur=on_blur,
            container=target_dict,
            label_width=label_width,
            entry_padx=entry_padx,
            entry_width=entry_width,
            stretch=stretch,
        )

    def _add_display_row(self, parent, row, label, key, initial="0만원", target_dict=None):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=4)
        variable = tk.StringVar(value=initial)
        ttk.Label(parent, textvariable=variable).grid(row=row, column=1, sticky="w", pady=4, padx=(8, 0))
        target = target_dict if target_dict is not None else self.home_purchase_output_vars
        target[key] = variable

    def _bind_apply_on_enter(self, widget, callback=None):
        widget.bind("<Return>", lambda event, current_callback=callback: self._on_input_enter(event, current_callback), add="+")

    def _on_input_enter(self, event, callback=None):
        widget = event.widget
        if str(widget.cget("state")) == "disabled":
            return "break"
        if callback:
            callback()
        return "break"

    def _build_identity_section(self, frame):
        section = self._create_section(frame, "1행 1열: 기본/가구 정보", 0, 0)

        self._add_entry(section, 0, "이름", "name", "")

        ttk.Label(section, text="성별").grid(row=1, column=0, sticky="w", pady=4)
        gender = ttk.Combobox(section, values=["", "male", "female"], state="readonly", width=12)
        gender.grid(row=1, column=1, sticky="w", pady=4, padx=(4, 0))
        gender.set("")
        self._bind_apply_on_enter(gender)
        self.inputs["gender"] = gender

        self._add_entry(section, 2, "출생년도", "birth_year", "", numeric=True, on_blur=self._sync_age_from_birth)
        self._add_entry(section, 3, "출생월", "birth_month", "", numeric=True, on_blur=self._sync_age_from_birth)
        self._add_entry(section, 4, "출생일", "birth_day", "", numeric=True, on_blur=self._sync_age_from_birth)
        self._add_entry(section, 5, "나이", "age", "40", numeric=True, on_blur=self._sync_birth_year_from_age)

        ttk.Label(section, text="혼인상태").grid(row=6, column=0, sticky="w", pady=4)
        marital = ttk.Combobox(section, values=["single", "married"], state="readonly", width=12)
        marital.grid(row=6, column=1, sticky="w", pady=4, padx=(4, 0))
        marital.set("married")
        marital.bind("<<ComboboxSelected>>", self._on_marital_status_change, add="+")
        self._bind_apply_on_enter(marital, callback=self._on_marital_status_change)
        self.inputs["marital_status"] = marital

        self._add_entry(section, 7, "자녀 수", "children_count", "1", numeric=True)

        ttk.Label(section, text="막내 자녀 단계").grid(row=8, column=0, sticky="w", pady=4)
        child_stage = ttk.Combobox(
            section,
            values=["none", "preschool", "elementary", "middle_high", "college", "adult"],
            state="readonly",
            width=14,
        )
        child_stage.grid(row=8, column=1, sticky="w", pady=4, padx=(4, 0))
        child_stage.set("middle_high")
        self._bind_apply_on_enter(child_stage)
        self.inputs["youngest_child_stage"] = child_stage

    def _build_financial_section(self, frame):
        section = self._create_section(frame, "1행 2열: 재무 입력", 0, 1)
        fields = [
            ("household_income", "월 가구소득(만원)", "628"),
            ("monthly_expense", "월 소비/지출(만원)", "379"),
            ("monthly_debt_payment", "월 부채상환(만원)", "53"),
            ("monthly_saving_investment", "월 저축/투자(만원)", "108"),
            ("monthly_emergency_fund", "월 예비자금(만원)", "88"),
            ("average_consumption", "평균 소비액(만원)", "379"),
            ("liquid_assets", "현금성 자산(만원)", "8,055"),
            ("non_liquid_assets", "비현금성 보유자산(만원)", "68,962"),
        ]
        for row, (key, label, default) in enumerate(fields):
            on_blur = self._sync_home_purchase_plan if key == "household_income" else None
            self._add_entry(section, row, label, key, default, numeric=True, on_blur=on_blur)

    def _build_economic_section(self, frame):
        section = self._create_section(frame, "2행 1열: 경제값", 1, 0)
        ttk.Label(
            section,
            text="기본값은 내부 보수 가정입니다. 현재 계산에는 물가, 연금 적립, 연금 수령 수익률이 직접 반영됩니다.",
            foreground="#555555",
            wraplength=360,
            justify="left",
        ).grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        section.columnconfigure(1, weight=1, minsize=120)
        defaults = self.economic_context_service.build_default_percent_map()
        for row, key in enumerate(ECONOMIC_ASSUMPTION_ORDER, start=1):
            label = f"{ECONOMIC_ASSUMPTION_LABELS[key]}(%)"
            self._add_entry(
                section,
                row,
                label,
                key,
                defaults[key],
                numeric=True,
                on_blur=self._refresh_special_goal_savings_tab,
                container=self.economic_inputs,
                label_width=16,
                entry_padx=(4, 0),
            )
        ttk.Label(
            section,
            text=self.economic_context_service.build_ui_hint(),
            foreground="#1f4e79",
            wraplength=360,
            justify="left",
        ).grid(row=len(ECONOMIC_ASSUMPTION_ORDER) + 1, column=0, columnspan=2, sticky="ew", pady=(6, 4))
        ttk.Button(
            section,
            text="\ud604\uc7ac \uc0c1\ud669 \ubc18\uc601",
            command=self.apply_current_economic_context,
        ).grid(row=len(ECONOMIC_ASSUMPTION_ORDER) + 2, column=0, columnspan=2, sticky="ew")

    def apply_current_economic_context(self):
        defaults = self.economic_context_service.build_default_percent_map()
        for key, value in defaults.items():
            self._set_widget_value(self.economic_inputs[key], value, numeric=True)
        self._refresh_special_goal_savings_tab()

    def _build_special_goal_section(self, frame):
        section = self._create_section(frame, "2행 2열: 특별 목표 자금", 1, 1)
        section.columnconfigure(0, weight=1)
        section.columnconfigure(1, weight=1)
        section.columnconfigure(2, weight=1)

        header = ttk.Frame(section)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        header.columnconfigure(1, weight=1)
        header.columnconfigure(2, weight=1)
        ttk.Label(header, text="목표기간(년)").grid(row=0, column=2, sticky="w")
        ttk.Label(header, text="자금명").grid(row=0, column=0, sticky="w")
        ttk.Label(header, text="목표금액(만원)").grid(row=0, column=1, sticky="w")

        self.goal_rows_frame = ttk.Frame(section)
        self.goal_rows_frame.grid(row=1, column=0, sticky="nsew", pady=(6, 0))
        self.goal_rows_frame.columnconfigure(0, weight=1)
        self.goal_rows_frame.columnconfigure(1, weight=1)
        self.goal_rows_frame.columnconfigure(2, weight=1)
        section.rowconfigure(1, weight=1)

        action_bar = ttk.Frame(section)
        action_bar.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(action_bar, text="행 추가", command=self._add_goal_row).pack(side="left")
        ttk.Button(action_bar, text="빈 행 정리", command=self._trim_empty_goal_rows).pack(side="left", padx=(6, 0))

        self._set_goal_rows([])

    def _add_goal_row(self, name="", amount="", target_years="", fixed=False):
        row_frame = ttk.Frame(self.goal_rows_frame)
        row_frame.grid(row=len(self.goal_rows), column=0, sticky="ew", pady=2)
        row_frame.columnconfigure(0, weight=1)
        row_frame.columnconfigure(1, weight=1)
        row_frame.columnconfigure(2, weight=1)

        name_entry = ttk.Entry(row_frame)
        name_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        name_entry.insert(0, "주택자금" if fixed else str(name))
        if fixed:
            name_entry.configure(state="readonly")
        self._bind_apply_on_enter(name_entry, callback=self._refresh_special_goal_savings_tab)

        amount_entry = ttk.Entry(row_frame)
        amount_entry.grid(row=0, column=1, sticky="ew", padx=(0, 6))
        self._set_entry_value(amount_entry, amount, numeric=True)
        amount_callback = self._refresh_special_goal_savings_tab
        if fixed:
            amount_callback = lambda current=amount_entry: self._sync_home_purchase_from_target_widget(current)
        self._bind_numeric_entry(amount_entry, on_blur=amount_callback)

        target_years_entry = ttk.Entry(row_frame)
        target_years_entry.grid(row=0, column=2, sticky="ew", padx=(0, 6))
        self._set_entry_value(target_years_entry, target_years, numeric=True)
        target_years_callback = self._refresh_special_goal_savings_tab
        if fixed:
            target_years_callback = lambda current=target_years_entry: self._sync_home_target_years_from_goal_widget(current)
        self._bind_numeric_entry(target_years_entry, on_blur=target_years_callback)

        remove_button = ttk.Button(row_frame, text="삭제")
        row_data = {
            "frame": row_frame,
            "name": name_entry,
            "target_amount": amount_entry,
            "target_years": target_years_entry,
            "remove": remove_button,
            "fixed": fixed,
        }
        if fixed:
            remove_button.configure(state="disabled")
        else:
            remove_button.configure(command=lambda current=row_data: self._remove_goal_row(current))
        remove_button.grid(row=0, column=3, sticky="e")

        self.goal_rows.append(row_data)
        if fixed:
            self.fixed_home_goal_row = row_data
        self._refresh_goal_row_positions()
        self._refresh_special_goal_savings_tab()

    def _remove_goal_row(self, row_data):
        if row_data not in self.goal_rows or row_data.get("fixed"):
            return
        row_data["frame"].destroy()
        self.goal_rows.remove(row_data)
        if len(self.goal_rows) == 1 and self.fixed_home_goal_row is not None:
            self._add_goal_row()
        else:
            self._refresh_goal_row_positions()
        self._refresh_special_goal_savings_tab()

    def _refresh_goal_row_positions(self):
        for index, row_data in enumerate(self.goal_rows):
            row_data["frame"].grid_configure(row=index)

    def _trim_empty_goal_rows(self):
        keep_rows = []
        for row_data in self.goal_rows:
            if row_data.get("fixed"):
                keep_rows.append(row_data)
                continue
            name = row_data["name"].get().strip()
            amount = row_data["target_amount"].get().replace(",", "").strip()
            target_years = row_data["target_years"].get().replace(",", "").strip()
            if not name and not amount and not target_years:
                row_data["frame"].destroy()
            else:
                keep_rows.append(row_data)
        self.goal_rows = keep_rows
        if len(self.goal_rows) == 1 and self.fixed_home_goal_row is not None:
            self._add_goal_row()
        else:
            self._refresh_goal_row_positions()
        self._refresh_special_goal_savings_tab()

    def _build_expense_tab(self, frame):
        frame.columnconfigure(1, weight=1)
        for index, (key, label) in enumerate(CATEGORY_LABELS.items()):
            self._add_numeric_entry(frame, index, f"{label}(만원)", self.category_inputs, key)

    def _build_expense_tab(self, frame):
        frame.columnconfigure(1, weight=1)
        for index, (key, label) in enumerate(CATEGORY_LABELS.items()):
            self._add_numeric_entry(
                frame,
                index,
                f"{label}(만원)",
                self.category_inputs,
                key,
                on_blur=self._refresh_expense_summary,
            )
        summary_row = len(CATEGORY_LABELS)
        self._add_display_row(frame, summary_row, "소비 합계", "expense_total", target_dict=self.expense_output_vars)
        self._add_display_row(frame, summary_row + 1, "월간 가용자금", "available_cash", target_dict=self.expense_output_vars)
        self._refresh_expense_summary()

    def _refresh_expense_summary(self):
        if not self.expense_output_vars:
            return

        expense_total = 0.0
        for widget in self.category_inputs.values():
            expense_total += self._entry_float(widget, 0.0)

        household_income = self._entry_float(self.inputs.get("household_income"), 0.0) if self.inputs.get("household_income") else 0.0
        available_cash = household_income - expense_total

        self.expense_output_vars["expense_total"].set(self._format_money_label(expense_total))
        self.expense_output_vars["available_cash"].set(self._format_money_label(available_cash))

    def _build_expense_tab(self, frame):
        frame.columnconfigure(0, weight=3, minsize=520)
        frame.columnconfigure(1, weight=2, minsize=320)
        frame.rowconfigure(0, weight=1)

        input_section = ttk.LabelFrame(frame, text="\uc18c\ube44 \uc785\ub825", padding=10)
        input_section.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        input_section.columnconfigure(0, weight=1)
        input_section.rowconfigure(0, weight=1)

        result_section = ttk.LabelFrame(frame, text="\uacb0\uacfc \uc694\uc57d", padding=10)
        result_section.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        result_section.columnconfigure(0, weight=1)
        result_section.rowconfigure(4, weight=0)

        canvas = tk.Canvas(input_section, highlightthickness=0)
        scrollbar = ttk.Scrollbar(input_section, orient="vertical", command=canvas.yview)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=scrollbar.set)

        container = ttk.Frame(canvas, padding=(0, 0, 8, 0))
        container.columnconfigure(2, weight=1)
        window_id = canvas.create_window((0, 0), window=container, anchor="nw")

        container.bind(
            "<Configure>",
            lambda _event, current_canvas=canvas: current_canvas.configure(scrollregion=current_canvas.bbox("all")),
        )
        canvas.bind(
            "<Configure>",
            lambda event, current_canvas=canvas, current_window=window_id: current_canvas.itemconfigure(
                current_window,
                width=event.width,
            ),
        )

        ttk.Label(container, text="\ucd1d\uc561").grid(row=0, column=1, sticky="w", padx=(4, 0), pady=(0, 6))
        ttk.Label(container, text="\uc138\ubd80 \ub0b4\uc5ed").grid(row=0, column=2, sticky="w", padx=(8, 0), pady=(0, 6))

        self.expense_detail_inputs = {}
        for index, (key, label) in enumerate(CATEGORY_LABELS.items(), start=1):
            grid_row = ((index - 1) * 2) + 1
            self._add_numeric_entry(
                container,
                grid_row,
                f"{label}(\ub9cc\uc6d0)",
                self.category_inputs,
                key,
                on_blur=lambda current=key: self._on_expense_category_total_change(current),
                label_width=10,
                entry_width=10,
                stretch=False,
            )

            detail_frame = ttk.Frame(container)
            detail_frame.grid(row=grid_row, column=2, sticky="ew", padx=(8, 0), pady=2)

            detail_inputs = {}
            for detail_index, (detail_key, detail_label) in enumerate(EXPENSE_DETAIL_LABELS.get(key, {}).items()):
                detail_row = detail_index % 2
                detail_group = detail_index // 2
                label_column = detail_group * 2
                value_column = label_column + 1
                detail_frame.columnconfigure(label_column, minsize=110)
                ttk.Label(detail_frame, text=f"- {detail_label}").grid(
                    row=detail_row,
                    column=label_column,
                    sticky="w",
                    padx=(0, 4),
                    pady=1,
                )
                entry = ttk.Entry(detail_frame, width=8)
                entry.grid(row=detail_row, column=value_column, sticky="w", padx=(0, 12), pady=1)
                self._bind_numeric_entry(entry, on_blur=lambda current=key: self._on_expense_detail_change(current))
                detail_inputs[detail_key] = entry
            self.expense_detail_inputs[key] = detail_inputs

            if index < len(CATEGORY_LABELS):
                ttk.Separator(container, orient="horizontal").grid(
                    row=grid_row + 1,
                    column=0,
                    columnspan=3,
                    sticky="ew",
                    pady=(6, 6),
                )

        self._add_display_row(
            result_section,
            0,
            "\uc18c\ube44 \ud569\uacc4",
            "expense_total",
            target_dict=self.expense_output_vars,
        )
        self._add_display_row(
            result_section,
            1,
            "\uc6d4\uac04 \uac00\uc6a9\uc790\uae08",
            "available_cash",
            target_dict=self.expense_output_vars,
        )
        ttk.Separator(result_section, orient="horizontal").grid(row=2, column=0, sticky="ew", pady=(8, 8))

        ttk.Label(result_section, text="\uac00\uc6a9\uc790\uae08 \ubd84\ubc30").grid(
            row=3,
            column=0,
            sticky="w",
            pady=(0, 4),
        )
        self.expense_allocation_rows_frame = ttk.Frame(result_section)
        self.expense_allocation_rows_frame.grid(
            row=4,
            column=0,
            sticky="ew",
            pady=(0, 10),
        )
        self.expense_allocation_rows_frame.columnconfigure(0, weight=1)

        self._add_display_row(
            result_section,
            5,
            "\ubd84\ubc30 \ud569\uacc4",
            "allocation_total",
            target_dict=self.expense_output_vars,
        )
        ttk.Separator(result_section, orient="horizontal").grid(row=6, column=0, sticky="ew", pady=(8, 8))
        self._add_display_row(
            result_section,
            7,
            "\uac00\uc6a9\uc790\uae08 \ucc28\uc774",
            "allocation_gap",
            target_dict=self.expense_output_vars,
        )
        self._refresh_expense_summary()

    def _on_expense_category_total_change(self, category_key):
        self._refresh_expense_category_total(category_key)
        self._refresh_expense_summary()

    def _on_expense_detail_change(self, category_key):
        self._refresh_expense_category_total(category_key)
        self._refresh_expense_summary()

    def _refresh_expense_category_total(self, category_key):
        if category_key not in self.category_inputs:
            return

        detail_values = {
            detail_key: self._entry_float(widget, 0.0)
            for detail_key, widget in self.expense_detail_inputs.get(category_key, {}).items()
        }
        detail_multipliers = EXPENSE_DETAIL_MULTIPLIERS.get(category_key, {})
        resolved_total = resolve_category_total(
            self._entry_float(self.category_inputs[category_key], 0.0),
            detail_values,
            detail_multipliers,
        )
        if abs(sum_detail_values(detail_values, detail_multipliers)) > 1e-9:
            self._set_entry_value(self.category_inputs[category_key], resolved_total, numeric=True)

    def _refresh_all_expense_category_totals(self):
        for category_key in self.expense_detail_inputs:
            self._refresh_expense_category_total(category_key)

    def _collect_expense_detail_inputs(self):
        return {
            category_key: {
                detail_key: self._get_widget_value(widget)
                for detail_key, widget in detail_inputs.items()
            }
            for category_key, detail_inputs in self.expense_detail_inputs.items()
        }

    def _handle_product_input_change(self):
        self._refresh_expense_summary()

    def _handle_pension_product_change(self):
        self._sync_pension_product_context()
        self._refresh_expense_summary()

    def _render_expense_allocation_rows(self, allocation_rows):
        if self.expense_allocation_rows_frame is None:
            return

        for child in self.expense_allocation_rows_frame.winfo_children():
            child.destroy()

        visible_rows = [row for row in allocation_rows if abs(float(row.get("amount", 0.0))) > 1e-9]
        if not visible_rows:
            ttk.Label(
                self.expense_allocation_rows_frame,
                text="\uc785\ub825\ub41c \uc800\ucd95/\ubcf4\ud5d8 \ubd84\ubc30 \ub0b4\uc5ed\uc774 \uc5c6\uc2b5\ub2c8\ub2e4.",
            ).grid(row=0, column=0, columnspan=2, sticky="w")
            return

        for row_index, row in enumerate(visible_rows):
            ttk.Label(self.expense_allocation_rows_frame, text=row["label"]).grid(
                row=row_index,
                column=0,
                sticky="w",
                padx=(0, 12),
                pady=2,
            )
            ttk.Label(
                self.expense_allocation_rows_frame,
                text=self._format_money_label(row["amount"]),
            ).grid(row=row_index, column=1, sticky="w", pady=2)

    def _refresh_expense_summary(self):
        if not self.expense_output_vars:
            return

        self._refresh_all_expense_category_totals()
        category_totals = {
            category_key: self._entry_float(widget, 0.0)
            for category_key, widget in self.category_inputs.items()
        }
        household_income = (
            self._entry_float(self.inputs.get("household_income"), 0.0)
            if self.inputs.get("household_income")
            else 0.0
        )
        saving_products = {
            product_key: self._entry_float(widget, 0.0)
            for product_key, widget in self.product_inputs.items()
        }
        insurance_products = {
            product_key: self._entry_float(widget, 0.0)
            for product_key, widget in self.insurance_inputs.items()
        }

        summary = calculate_expense_plan_summary(
            category_totals=category_totals,
            household_income=household_income,
            saving_products=saving_products,
            insurance_products=insurance_products,
            labels={**PRODUCT_LABELS, **INSURANCE_PRODUCT_LABELS},
            ordered_keys=EXPENSE_ALLOCATION_ORDER,
        )
        self._render_expense_allocation_rows(summary["allocation_rows"])

        self.expense_output_vars["expense_total"].set(self._format_money_label(summary["expense_total"]))
        self.expense_output_vars["available_cash"].set(self._format_money_label(summary["available_cash"]))
        self.expense_output_vars["allocation_total"].set(self._format_money_label(summary["allocation_total"]))
        self.expense_output_vars["allocation_gap"].set(self._format_money_label(summary["allocation_gap"]))

    def _build_product_tab(self, frame):
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        self._build_general_product_section(frame)
        self._build_tax_benefit_section(frame)
        self._build_home_purchase_section(frame)
        self._build_insurance_section(frame)
        self._sync_home_purchase_plan()
        return

        frame.columnconfigure(0, weight=1)

        general_section = ttk.LabelFrame(frame, text="일반 상품", padding=10)
        general_section.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        general_section.columnconfigure(1, weight=1)
        for index, key in enumerate(PRODUCT_INPUT_GROUPS["general"]):
            self._add_numeric_entry(
                general_section,
                index,
                f"{PRODUCT_LABELS[key]}(월 납입, 만원)",
                self.product_inputs,
                key,
                on_blur=self._sync_pension_product_context if key in ("pension_savings", "irp") else None,
            )

        tax_section = ttk.LabelFrame(frame, text="세제혜택 상품", padding=10)
        tax_section.grid(row=1, column=0, sticky="ew")
        tax_section.columnconfigure(1, weight=1)
        ttk.Label(
            tax_section,
            text="세제혜택 상품은 일반 상품과 중복 입력하지 않고 해당 항목에만 입력합니다.",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))
        for index, key in enumerate(PRODUCT_INPUT_GROUPS["tax_benefit"]):
            self._add_numeric_entry(
                tax_section,
                index + 1,
                f"{PRODUCT_LABELS[key]}(월 납입, 만원)",
                self.product_inputs,
                key,
            )

    def _build_general_product_section(self, frame):
        section = self._create_section(frame, "1행 1열 일반 상품", 0, 0)
        for index, key in enumerate(PRODUCT_INPUT_GROUPS["general"]):
            self._add_numeric_entry(
                section,
                index,
                f"{PRODUCT_LABELS[key]}(월 납입, 만원)",
                self.product_inputs,
                key,
            )

    def _build_tax_benefit_section(self, frame):
        section = self._create_section(frame, "1행 2열 세제혜택 상품", 0, 1)
        ttk.Label(section, text="예시값은 세제혜택 최대 한도를 기준으로 채웁니다.").grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 6),
        )
        for index, key in enumerate(PRODUCT_INPUT_GROUPS["tax_benefit"], start=1):
            self._add_numeric_entry(
                section,
                index,
                f"{PRODUCT_LABELS[key]}(월 납입, 만원)",
                self.product_inputs,
                key,
            )

    def _build_home_purchase_section(self, frame):
        defaults = self.home_loan_context_service.build_default_input_map()
        section = self._create_section(frame, "2행 1열 내 집 마련 계산", 1, 0)
        self._add_numeric_entry(
            section,
            0,
            "집 값(만원)",
            self.home_purchase_inputs,
            "house_price",
            defaults["house_price"],
            on_blur=self._sync_home_purchase_plan,
        )
        self._add_numeric_entry(
            section,
            1,
            "LTV(%)",
            self.home_purchase_inputs,
            "ltv",
            defaults["ltv"],
            on_blur=self._sync_home_purchase_plan,
        )
        self._add_numeric_entry(
            section,
            2,
            "DTI(%)",
            self.home_purchase_inputs,
            "dti",
            defaults["dti"],
            on_blur=self._sync_home_purchase_plan,
        )
        self._add_display_row(section, 3, "대출제외 목표금액", "down_payment_target")
        self._add_numeric_entry(
            section,
            4,
            "목표 기간(년)",
            self.home_purchase_inputs,
            "target_years",
            defaults["target_years"],
            on_blur=self._sync_home_purchase_plan,
        )
        self._add_display_row(section, 4, "월 저축금액", "required_monthly_saving")
        self._add_numeric_entry(
            section,
            5,
            "대출 기간(년)",
            self.home_purchase_inputs,
            "loan_term_years",
            defaults["loan_term_years"],
            on_blur=self._sync_home_purchase_plan,
        )
        self._add_numeric_entry(
            section,
            6,
            "대출 이자율(%)",
            self.home_purchase_inputs,
            "loan_interest_rate",
            defaults["loan_interest_rate"],
            on_blur=self._sync_home_purchase_plan,
        )
        self._add_display_row(section, 7, "매달 상환금액", "monthly_repayment")

        ttk.Label(
            section,
            text=self.home_loan_context_service.build_ui_hint(),
            foreground="#1f4e79",
            wraplength=300,
            justify="left",
        ).grid(row=8, column=0, columnspan=2, sticky="ew", pady=(6, 4))
        ttk.Button(section, text="대출 예시 반영", command=self.apply_current_home_loan_context).grid(
            row=9, column=0, sticky="w"
        )

    def apply_current_home_loan_context(self):
        defaults = self.home_loan_context_service.build_default_input_map()
        for key, value in defaults.items():
            if key == "house_price":
                continue
            if key in self.home_purchase_inputs:
                self._set_widget_value(self.home_purchase_inputs[key], value, numeric=True)
        self._sync_home_purchase_plan()

    def _build_home_purchase_section(self, frame):
        defaults = self.home_loan_context_service.build_default_input_map()
        section = self._create_section(frame, "2행 1열 내 집 마련 계산", 1, 0)
        self._add_numeric_entry(
            section,
            0,
            "집 값(만원)",
            self.home_purchase_inputs,
            "house_price",
            defaults["house_price"],
            on_blur=self._sync_home_purchase_plan,
        )
        self._add_numeric_entry(
            section,
            1,
            "LTV(%)",
            self.home_purchase_inputs,
            "ltv",
            defaults["ltv"],
            on_blur=self._sync_home_purchase_plan,
        )
        self._add_numeric_entry(
            section,
            2,
            "DTI(%)",
            self.home_purchase_inputs,
            "dti",
            defaults["dti"],
            on_blur=self._sync_home_purchase_plan,
        )
        self._add_display_row(section, 3, "대출제외 목표금액", "down_payment_target")
        self._add_numeric_entry(
            section,
            4,
            "목표 기간(년)",
            self.home_purchase_inputs,
            "target_years",
            defaults["target_years"],
            on_blur=self._sync_home_purchase_plan,
        )
        self._add_display_row(section, 5, "월 저축금액", "required_monthly_saving")
        self._add_numeric_entry(
            section,
            6,
            "대출 기간(년)",
            self.home_purchase_inputs,
            "loan_term_years",
            defaults["loan_term_years"],
            on_blur=self._sync_home_purchase_plan,
        )
        self._add_numeric_entry(
            section,
            7,
            "대출 이자율(%)",
            self.home_purchase_inputs,
            "loan_interest_rate",
            defaults["loan_interest_rate"],
            on_blur=self._sync_home_purchase_plan,
        )
        self._add_display_row(section, 8, "매달 상환금액", "monthly_repayment")

        ttk.Label(
            section,
            text=self.home_loan_context_service.build_ui_hint(),
            foreground="#1f4e79",
            wraplength=300,
            justify="left",
        ).grid(row=9, column=0, columnspan=2, sticky="ew", pady=(6, 4))
        ttk.Button(section, text="대출 예시 반영", command=self.apply_current_home_loan_context).grid(
            row=10, column=0, sticky="w"
        )

    def _build_insurance_section(self, frame):
        section = self._create_section(frame, "2행 2열 보험 구성", 1, 1)
        for index, key in enumerate(PRODUCT_INPUT_GROUPS["insurance"]):
            self._add_numeric_entry(
                section,
                index,
                f"{PRODUCT_LABELS[key]}(월 납입, 만원)",
                self.insurance_inputs,
                key,
            )

    def _build_general_product_section(self, frame):
        section = self._create_section(frame, "1\ud589 1\uc5f4 \uc77c\ubc18 \uc0c1\ud488", 0, 0)
        for index, key in enumerate(PRODUCT_INPUT_GROUPS["general"]):
            self._add_numeric_entry(
                section,
                index,
                f"{PRODUCT_LABELS[key]}(\uc6d4 \ub0a9\uc785, \ub9cc\uc6d0)",
                self.product_inputs,
                key,
                on_blur=self._handle_product_input_change,
            )

    def _build_tax_benefit_section(self, frame):
        section = self._create_section(frame, "1\ud589 2\uc5f4 \uc138\uc81c\ud61c\ud0dd \uc0c1\ud488", 0, 1)
        ttk.Label(
            section,
            text="\uc608\uc2dc\uac12\uc740 \uc138\uc81c\ud61c\ud0dd \ucd5c\ub300 \ud55c\ub3c4\ub97c \uae30\uc900\uc73c\ub85c \ucc44\uc6c1\ub2c8\ub2e4.",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))
        for index, key in enumerate(PRODUCT_INPUT_GROUPS["tax_benefit"], start=1):
            callback = self._handle_pension_product_change if key in ("pension_savings", "irp") else self._handle_product_input_change
            self._add_numeric_entry(
                section,
                index,
                f"{PRODUCT_LABELS[key]}(\uc6d4 \ub0a9\uc785, \ub9cc\uc6d0)",
                self.product_inputs,
                key,
                on_blur=callback,
            )

    def _build_insurance_section(self, frame):
        section = self._create_section(frame, "2\ud589 2\uc5f4 \ubcf4\ud5d8 \uad6c\uc131", 1, 1)
        for index, key in enumerate(PRODUCT_INPUT_GROUPS["insurance"]):
            self._add_numeric_entry(
                section,
                index,
                f"{PRODUCT_LABELS[key]}(\uc6d4 \ub0a9\uc785, \ub9cc\uc6d0)",
                self.insurance_inputs,
                key,
                on_blur=self._handle_product_input_change,
            )

    def _build_pension_tab(self, frame):
        frame.columnconfigure(1, weight=1)
        pension_fields = [
            ("current_age", "현재 나이", "40"),
            ("retirement_age", "수령 나이", "60"),
            ("expected_monthly_pension", "기대 월수령액(만원)", "200"),
            ("current_balance", "현재 적립액(만원)", "3,000"),
        ]
        for index, (key, label, default) in enumerate(pension_fields):
            self._add_numeric_entry(frame, index, label, self.pension_inputs, key, default)

    def _build_pension_tab(self, frame):
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

        current_section = self._create_section(frame, "1행 1열 현재 상황", 0, 0)
        result_section = self._create_section(frame, "1행 2열 계산 결과", 0, 1)

        current_fields = [
            ("current_age", "현재 나이", "40"),
            ("retirement_age", "수령 나이", "60"),
            ("expected_monthly_pension", "월연금 목표(만원)", "200"),
            ("current_balance", "현재 적립액(만원)", "3,000"),
        ]
        for index, (key, label, default) in enumerate(current_fields):
            self._add_numeric_entry(current_section, index, label, self.pension_inputs, key, default)

        self._add_display_row(
            current_section,
            len(current_fields),
            "연금저축",
            "pension_savings",
            target_dict=self.pension_output_vars,
        )
        self._add_display_row(
            current_section,
            len(current_fields) + 1,
            "IRP",
            "irp",
            target_dict=self.pension_output_vars,
        )

        result_fields = [
            ("inflation_adjusted_pension", "상향 연금", "0만원"),
            ("saving_period", "저축 기간", "-"),
            ("required_monthly", "월 필요액", "0만원"),
            ("additional_gap", "추가 부족액", "0만원"),
        ]
        for index, (key, label, initial) in enumerate(result_fields):
            self._add_display_row(result_section, index, label, key, initial=initial, target_dict=self.pension_output_vars)

        self._sync_pension_product_context()

    def _build_special_goal_tab(self, frame):
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        description = (
            "기본정보의 특별 목표 자금 중 주택자금을 제외한 목표를 기준으로, "
            "현재 적금 수익률과 투자 수익률을 적용한 월 저축액 예시를 보여줍니다. "
            "각 목표는 기본정보 탭에 입력한 목표기간을 그대로 사용합니다."
        )
        ttk.Label(frame, text=description, wraplength=420, justify="left").grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )

        container = ttk.Frame(frame)
        container.grid(row=1, column=0, sticky="nsew")
        container.columnconfigure(0, weight=2)
        container.columnconfigure(1, weight=1)
        container.columnconfigure(2, weight=1)

        ttk.Label(container, text="자금명").grid(row=0, column=0, sticky="w", padx=(0, 12), pady=(0, 6))
        ttk.Label(container, text="월저축액(적금)").grid(row=0, column=1, sticky="w", padx=(0, 12), pady=(0, 6))
        ttk.Label(container, text="월저축액(투자)").grid(row=0, column=2, sticky="w", pady=(0, 6))

        self.special_goal_rows_frame = ttk.Frame(container)
        self.special_goal_rows_frame.grid(row=1, column=0, columnspan=3, sticky="nsew")
        self.special_goal_rows_frame.columnconfigure(0, weight=2)
        self.special_goal_rows_frame.columnconfigure(1, weight=1)
        self.special_goal_rows_frame.columnconfigure(2, weight=1)
        self._refresh_special_goal_savings_tab()

    def _refresh_special_goal_savings_tab(self):
        if self.special_goal_rows_frame is None:
            return

        for child in self.special_goal_rows_frame.winfo_children():
            child.destroy()

        goals = []
        for row_data in self.goal_rows:
            name = row_data["name"].get().strip()
            amount_text = row_data["target_amount"].get().replace(",", "").strip()
            target_years_text = row_data["target_years"].get().replace(",", "").strip()
            if row_data.get("fixed"):
                continue
            if not name or not amount_text or not target_years_text:
                continue
            try:
                target_amount = float(amount_text)
                target_years = int(float(target_years_text))
            except ValueError:
                continue
            if target_years <= 0:
                continue
            goals.append({"name": name, "target_amount": target_amount, "target_years": target_years})

        installment_rate = 0.0
        investment_rate = 0.0
        if self.economic_inputs.get("installment_return_rate") is not None:
            installment_rate = self._entry_float(self.economic_inputs["installment_return_rate"], 0.0) / 100.0
        if self.economic_inputs.get("investment_return_rate") is not None:
            investment_rate = self._entry_float(self.economic_inputs["investment_return_rate"], 0.0) / 100.0

        rows = build_special_goal_saving_plan(
            goals=goals,
            installment_return_rate=installment_rate,
            investment_return_rate=investment_rate,
            excluded_names={"주택자금"},
        )

        if not rows:
            ttk.Label(
                self.special_goal_rows_frame,
                text="주택자금을 제외한 특별 목표 자금이 없으면 여기에는 표시되지 않습니다.",
            ).grid(row=0, column=0, columnspan=3, sticky="w")
            return

        for row_index, row in enumerate(rows):
            ttk.Label(self.special_goal_rows_frame, text=row["name"]).grid(
                row=row_index, column=0, sticky="w", padx=(0, 12), pady=3
            )
            ttk.Label(
                self.special_goal_rows_frame,
                text=self._format_money_label(row["installment_monthly_saving"]),
            ).grid(row=row_index, column=1, sticky="w", padx=(0, 12), pady=3)
            ttk.Label(
                self.special_goal_rows_frame,
                text=self._format_money_label(row["investment_monthly_saving"]),
            ).grid(row=row_index, column=2, sticky="w", pady=3)

    def _build_source_report_tab(self, frame):
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        self.source_report_text = tk.Text(frame, wrap="word", font=("맑은 고딕", 10))
        self.source_report_text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.source_report_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.source_report_text.configure(yscrollcommand=scrollbar.set)
        self.source_report_text.insert(
            tk.END,
            "분석을 실행하면 이번 결과에 적용된 보고서, 규칙, 계산형 기준의 근거가 여기에 표시됩니다.",
        )
        self.source_report_text.configure(state="disabled")

    def _render_source_report(self, profile, analysis):
        if self.source_report_text is None:
            return
        report_text = build_source_report_text(profile, analysis)
        self.source_report_text.configure(state="normal")
        self.source_report_text.delete("1.0", tk.END)
        self.source_report_text.insert(tk.END, report_text)
        self.source_report_text.configure(state="disabled")

    def _configure_result_text_tags(self):
        if self.result_text is None:
            return
        self.result_text.tag_configure(
            "header",
            font=("맑은 고딕", 10, "bold"),
        )
        self.result_text.tag_configure(
            "negative",
            foreground="#8b2d2d",
            background="#fdeaea",
        )
        self.result_text.tag_configure(
            "positive",
            foreground="#1f6b2b",
            background="#eaf7ea",
        )

    def _render_result_text(self, text: str):
        if self.result_text is None:
            return
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, text)
        self._apply_result_text_highlights(text)

    def _apply_result_text_highlights(self, text: str):
        if self.result_text is None:
            return

        self.result_text.tag_remove("header", "1.0", tk.END)
        self.result_text.tag_remove("negative", "1.0", tk.END)
        self.result_text.tag_remove("positive", "1.0", tk.END)

        self._apply_text_regex_tag(r"(?m)^\[[^\n]+\]$", text, "header")
        self._apply_regex_patterns(text, RESULT_NEGATIVE_PATTERNS, "negative")
        self._apply_regex_patterns(text, RESULT_POSITIVE_PATTERNS, "positive")

    def _apply_regex_patterns(self, text: str, patterns, tag_name: str):
        if not patterns:
            return
        for pattern in patterns:
            self._apply_text_regex_tag(pattern, text, tag_name)

    def _apply_text_regex_tag(self, pattern: str, text: str, tag_name: str):
        if self.result_text is None:
            return
        for match in re.finditer(pattern, text):
            start = f"1.0 + {match.start()}c"
            end = f"1.0 + {match.end()}c"
            self.result_text.tag_add(tag_name, start, end)

    def _bind_numeric_entry(self, entry, on_blur=None):
        self.numeric_entries.add(entry)
        entry.bind("<FocusIn>", self._on_numeric_focus_in, add="+")
        entry.bind("<FocusOut>", lambda event, callback=on_blur: self._on_numeric_focus_out(event, callback), add="+")
        entry.bind("<Return>", lambda event, callback=on_blur: self._on_numeric_enter(event, callback), add="+")

    def _on_numeric_focus_in(self, event):
        widget = event.widget
        if str(widget.cget("state")) == "disabled":
            return
        value = widget.get().replace(",", "")
        if value != widget.get():
            self._replace_entry_text(widget, value)

    def _on_numeric_focus_out(self, event, callback=None):
        widget = event.widget
        if str(widget.cget("state")) == "disabled":
            return
        self._set_entry_value(widget, widget.get(), numeric=True)
        if callback:
            callback()

    def _on_numeric_enter(self, event, callback=None):
        self._on_numeric_focus_out(event, callback)
        return "break"

    def _format_numeric_value(self, value) -> str:
        text = str(value).replace(",", "").strip()
        if text == "":
            return ""
        try:
            number = float(text)
        except ValueError:
            return str(value)
        if number.is_integer():
            return f"{int(number):,}"
        return f"{number:,.2f}".rstrip("0").rstrip(".")

    def _format_money_label(self, value) -> str:
        text = f"{float(value):,.1f}".rstrip("0").rstrip(".")
        return f"{text}만원"

    def _format_period_label(self, months: int) -> str:
        safe_months = max(int(months or 0), 0)
        years, remain_months = divmod(safe_months, 12)
        if years and remain_months:
            return f"{years}년 {remain_months}개월"
        if years:
            return f"{years}년"
        return f"{remain_months}개월"

    def _sync_pension_product_context(self):
        if not self.pension_output_vars:
            return

        pension_savings = self._entry_float(self.product_inputs.get("pension_savings"), 0.0) if self.product_inputs.get("pension_savings") else 0.0
        irp = self._entry_float(self.product_inputs.get("irp"), 0.0) if self.product_inputs.get("irp") else 0.0
        self.pension_output_vars["pension_savings"].set(self._format_money_label(pension_savings))
        self.pension_output_vars["irp"].set(self._format_money_label(irp))
        last_analysis = getattr(self, "last_analysis", None)
        if last_analysis is not None:
            self._render_pension_result_panel(last_analysis)

    def _render_pension_result_panel(self, analysis):
        if not self.pension_output_vars:
            return

        pension = analysis.pension_result
        current_monthly_pension_saving = self._entry_float(self.product_inputs.get("pension_savings"), 0.0) + self._entry_float(
            self.product_inputs.get("irp"), 0.0
        )
        additional_gap = max(float(pension.get("required_monthly_contribution", 0.0)) - current_monthly_pension_saving, 0.0)

        self.pension_output_vars["inflation_adjusted_pension"].set(
            self._format_money_label(pension.get("inflation_adjusted_monthly_pension_at_retirement", 0.0))
        )
        self.pension_output_vars["saving_period"].set(
            self._format_period_label(pension.get("months_to_retirement", 0))
        )
        self.pension_output_vars["required_monthly"].set(
            self._format_money_label(pension.get("required_monthly_contribution", 0.0))
        )
        self.pension_output_vars["additional_gap"].set(
            self._format_money_label(additional_gap)
        )

    def _replace_entry_text(self, entry, value: str):
        entry.delete(0, tk.END)
        entry.insert(0, value)

    def _set_entry_value(self, entry, value, numeric=False):
        text = self._format_numeric_value(value) if numeric else str(value)
        self._replace_entry_text(entry, text)

    def _set_widget_value(self, widget, value, numeric=False):
        if isinstance(widget, ttk.Combobox):
            widget.set("" if value is None else str(value))
            return
        self._set_entry_value(widget, value, numeric=numeric)

    def _get_widget_value(self, widget):
        return widget.get()

    def _widget_is_empty(self, widget) -> bool:
        return self._get_widget_value(widget).strip() == ""

    def _widget_is_effectively_empty(self, widget, numeric=False, zero_is_empty=False) -> bool:
        text = self._get_widget_value(widget).replace(",", "").strip()
        if text == "":
            return True
        if numeric and zero_is_empty:
            try:
                return float(text) == 0.0
            except ValueError:
                return False
        return False

    def _fill_widget_if_empty(self, widget, value, numeric=False):
        if self._widget_is_empty(widget):
            self._set_widget_value(widget, value, numeric=numeric)

    def _fill_widget_if_unset(self, widget, value, numeric=False, zero_is_empty=False):
        if self._widget_is_effectively_empty(widget, numeric=numeric, zero_is_empty=zero_is_empty):
            self._set_widget_value(widget, value, numeric=numeric)

    def _get_numeric_value(self, key):
        text = self._get_widget_value(self.inputs[key]).replace(",", "").strip()
        if text == "":
            return None
        try:
            return int(float(text))
        except ValueError:
            return None

    def _entry_float(self, widget, default=0.0):
        text = self._get_widget_value(widget).replace(",", "").strip()
        if text == "":
            return float(default)
        try:
            return float(text)
        except ValueError:
            return float(default)

    def _set_home_goal_target_value(self, amount):
        if self.fixed_home_goal_row is not None:
            self._set_entry_value(self.fixed_home_goal_row["target_amount"], amount, numeric=True)

    def _set_home_goal_target_years_value(self, years):
        if self.fixed_home_goal_row is not None and "target_years" in self.fixed_home_goal_row:
            self._set_entry_value(self.fixed_home_goal_row["target_years"], years, numeric=True)

    def _sync_home_purchase_from_target_widget(self, widget):
        if self._syncing_home_goal or not self.home_purchase_inputs:
            return

        self._syncing_home_goal = True
        try:
            target_amount = self._entry_float(widget, 0.0)
            self._set_home_goal_target_value(target_amount)
            self._set_widget_value(self.home_purchase_inputs["house_price"], target_amount, numeric=True)
        finally:
            self._syncing_home_goal = False

        self._sync_home_purchase_plan()

    def _sync_home_target_years_from_goal_widget(self, widget):
        if self._syncing_home_goal or not self.home_purchase_inputs:
            return

        target_years_text = self._get_widget_value(widget).replace(",", "").strip()
        if target_years_text == "":
            self._refresh_special_goal_savings_tab()
            return

        self._syncing_home_goal = True
        try:
            try:
                target_years = max(int(float(target_years_text)), 0)
            except ValueError:
                return
            self._set_home_goal_target_years_value(target_years)
            self._set_widget_value(self.home_purchase_inputs["target_years"], target_years, numeric=True)
        finally:
            self._syncing_home_goal = False

        self._sync_home_purchase_plan()

    def _sync_home_purchase_plan(self):
        if not self.home_purchase_inputs:
            return
        defaults = self.home_loan_context_service.get_recommended_defaults()

        result = calculate_home_purchase_plan(
            house_price=self._entry_float(
                self.home_purchase_inputs["house_price"],
                defaults["house_price"],
            ),
            ltv=self._entry_float(
                self.home_purchase_inputs["ltv"],
                defaults["ltv"] * 100.0,
            )
            / 100.0,
            dti=self._entry_float(
                self.home_purchase_inputs["dti"],
                defaults["dti"] * 100.0,
            )
            / 100.0,
            target_years=int(
                self._entry_float(
                    self.home_purchase_inputs["target_years"],
                    defaults["target_years"],
                )
            ),
            loan_term_years=int(
                self._entry_float(
                    self.home_purchase_inputs["loan_term_years"],
                    defaults["loan_term_years"],
                )
            ),
            loan_interest_rate=self._entry_float(
                self.home_purchase_inputs["loan_interest_rate"],
                defaults["loan_interest_rate"] * 100.0,
            )
            / 100.0,
            household_income=self._entry_float(self.inputs["household_income"], 0.0)
            if "household_income" in self.inputs
            else 0.0,
        )
        self.home_purchase_output_vars["down_payment_target"].set(
            self._format_money_label(result["down_payment_target"])
        )
        self.home_purchase_output_vars["required_monthly_saving"].set(
            self._format_money_label(result["required_monthly_saving"])
        )
        self.home_purchase_output_vars["monthly_repayment"].set(
            self._format_money_label(result["monthly_repayment"])
        )
        self._set_home_goal_target_value(result["house_price"])
        self._set_home_goal_target_years_value(
            int(
                self._entry_float(
                    self.home_purchase_inputs["target_years"],
                    defaults["target_years"],
                )
            )
        )
        self._refresh_expense_summary()
        self._refresh_special_goal_savings_tab()

    def _sync_age_from_birth(self):
        birth_year = self._get_numeric_value("birth_year")
        birth_month = self._get_numeric_value("birth_month") or 0
        birth_day = self._get_numeric_value("birth_day") or 0
        if not birth_year:
            return

        today = date.today()
        age = today.year - birth_year
        if birth_month > 0 and birth_day > 0 and (today.month, today.day) < (birth_month, birth_day):
            age -= 1
        if age > 0:
            self._set_widget_value(self.inputs["age"], age, numeric=True)

    def _sync_birth_year_from_age(self):
        age = self._get_numeric_value("age")
        if age is None:
            return

        birth_month = self._get_numeric_value("birth_month") or 0
        birth_day = self._get_numeric_value("birth_day") or 0
        today = date.today()
        birth_year = today.year - age
        if birth_month > 0 and birth_day > 0 and (birth_month, birth_day) > (today.month, today.day):
            birth_year -= 1
        if birth_year > 0:
            self._set_widget_value(self.inputs["birth_year"], birth_year, numeric=True)

    def _on_marital_status_change(self, _event=None):
        marital_status = self._get_widget_value(self.inputs["marital_status"])
        children_entry = self.inputs["children_count"]
        child_stage = self.inputs["youngest_child_stage"]

        if marital_status == "single":
            self._set_widget_value(children_entry, "0", numeric=True)
            self._set_widget_value(child_stage, "none")
            children_entry.configure(state="disabled")
            child_stage.configure(state="disabled")
        else:
            children_entry.configure(state="normal")
            child_stage.configure(state="readonly")
            if self._get_widget_value(child_stage) == "":
                self._set_widget_value(child_stage, "none")

    def _collect_special_goals(self):
        goals = []
        for row_data in self.goal_rows:
            name_value = row_data["name"].get()
            if row_data.get("fixed"):
                name_value = "주택자금"
            goals.append(
                {
                    "name": name_value,
                    "target_amount": row_data["target_amount"].get(),
                    "target_years": row_data["target_years"].get(),
                }
            )
        return goals

    def collect_raw_input(self):
        raw = {key: self._get_widget_value(widget) for key, widget in self.inputs.items()}
        raw["economic_assumptions"] = {
            key: self._get_widget_value(widget) for key, widget in self.economic_inputs.items()
        }
        raw["special_goals"] = self._collect_special_goals()
        raw["expense_categories"] = {key: self._get_widget_value(widget) for key, widget in self.category_inputs.items()}
        raw["expense_detail_categories"] = self._collect_expense_detail_inputs()
        raw["saving_products"] = {key: self._get_widget_value(widget) for key, widget in self.product_inputs.items()}
        raw["insurance_products"] = {key: self._get_widget_value(widget) for key, widget in self.insurance_inputs.items()}
        raw["home_purchase_goal"] = {
            key: self._get_widget_value(widget) for key, widget in self.home_purchase_inputs.items()
        }
        raw["pension"] = {key: self._get_widget_value(widget) for key, widget in self.pension_inputs.items()}
        return raw

    def fill_sample(self):
        self._fill_widget_if_empty(self.inputs["name"], "홍길동")
        if self._get_widget_value(self.inputs["gender"]).strip() == "":
            self._set_widget_value(self.inputs["gender"], "male")
        self._fill_widget_if_empty(self.inputs["birth_year"], "1981", numeric=True)
        self._fill_widget_if_empty(self.inputs["birth_month"], "4", numeric=True)
        self._fill_widget_if_empty(self.inputs["birth_day"], "22", numeric=True)
        if self._get_widget_value(self.inputs["birth_year"]).strip():
            self._sync_age_from_birth()
        elif self._get_widget_value(self.inputs["age"]).strip():
            self._sync_birth_year_from_age()
        else:
            self._fill_widget_if_empty(self.inputs["age"], "45", numeric=True)
            self._sync_birth_year_from_age()
        if self._get_widget_value(self.inputs["marital_status"]).strip() == "":
            self._set_widget_value(self.inputs["marital_status"], "married")
        self._on_marital_status_change()
        if str(self.inputs["children_count"].cget("state")) != "disabled":
            self._fill_widget_if_empty(self.inputs["children_count"], "1", numeric=True)
        if self._get_widget_value(self.inputs["youngest_child_stage"]).strip() == "":
            self._set_widget_value(self.inputs["youngest_child_stage"], "middle_high")

        self._fill_widget_if_empty(self.inputs["household_income"], "628", numeric=True)
        self._fill_widget_if_empty(self.inputs["monthly_expense"], "379", numeric=True)
        self._fill_widget_if_empty(self.inputs["monthly_debt_payment"], "53", numeric=True)
        self._fill_widget_if_empty(self.inputs["monthly_saving_investment"], "108", numeric=True)
        self._fill_widget_if_empty(self.inputs["monthly_emergency_fund"], "88", numeric=True)
        self._fill_widget_if_empty(self.inputs["average_consumption"], "379", numeric=True)
        self._fill_widget_if_empty(self.inputs["liquid_assets"], "8055", numeric=True)
        self._fill_widget_if_empty(self.inputs["non_liquid_assets"], "68962", numeric=True)

        economic_defaults = self.economic_context_service.build_default_percent_map()
        for key, value in economic_defaults.items():
            self._fill_widget_if_empty(self.economic_inputs[key], value, numeric=True)

        sample_categories = {
            "food": 89,
            "transport": 30,
            "utilities": 30,
            "communication": 20,
            "housing": 69,
            "leisure": 21,
            "fashion": 21,
            "social": 22,
            "allowance": 39,
            "education": 97,
            "medical": 26,
        }
        sample_products = {
            "cash_flow": 5,
            "installment": 0,
            "investment": 0,
            "pension_savings": 50,
            "irp": 25,
            "housing_subscription": 25,
        }
        sample_insurance = {
            "indemnity_insurance": 1,
            "life_insurance": 1,
            "variable_insurance": 1,
        }
        sample_home_purchase = self.home_loan_context_service.build_default_input_map()
        for key, value in sample_categories.items():
            self._fill_widget_if_empty(self.category_inputs[key], value, numeric=True)
        for key, value in sample_products.items():
            self._fill_widget_if_empty(self.product_inputs[key], value, numeric=True)
        for key, value in sample_insurance.items():
            self._fill_widget_if_empty(self.insurance_inputs[key], value, numeric=True)
        fixed_home_value = ""
        if self.fixed_home_goal_row is not None:
            fixed_home_value = self.fixed_home_goal_row["target_amount"].get().strip()
        if self._widget_is_empty(self.home_purchase_inputs["house_price"]) and fixed_home_value:
            self._set_widget_value(self.home_purchase_inputs["house_price"], fixed_home_value, numeric=True)
        else:
            self._fill_widget_if_empty(self.home_purchase_inputs["house_price"], sample_home_purchase["house_price"], numeric=True)
        for key in ("ltv", "dti", "target_years", "loan_term_years", "loan_interest_rate"):
            self._fill_widget_if_empty(self.home_purchase_inputs[key], sample_home_purchase[key], numeric=True)

        pension_current_age = self._get_widget_value(self.inputs["age"]).strip() or "45"
        sample_pension = {
            "current_age": pension_current_age,
            "retirement_age": "60",
            "expected_monthly_pension": "200",
            "current_balance": "3000",
        }
        for key, value in sample_pension.items():
            self._fill_widget_if_empty(self.pension_inputs[key], value, numeric=True)

        if self.fixed_home_goal_row is not None and self._widget_is_empty(self.fixed_home_goal_row["target_amount"]):
            self._set_home_goal_target_value(self._get_widget_value(self.home_purchase_inputs["house_price"]))

        non_fixed_rows = [row for row in self.goal_rows if not row.get("fixed")]
        filled_non_fixed_rows = [row for row in non_fixed_rows if row["name"].get().strip() or row["target_amount"].get().strip()]
        if not filled_non_fixed_rows and non_fixed_rows:
            self._set_entry_value(non_fixed_rows[0]["name"], "교육자금")
            self._set_entry_value(non_fixed_rows[0]["target_amount"], "5000", numeric=True)

        self._sync_home_purchase_plan()
        self.status_var.set("예시값을 채웠습니다.")

    def run_analysis(self):
        raw = self.collect_raw_input()
        normalized, errors, warnings = validate_raw_input(raw)
        if errors:
            messagebox.showerror("입력 오류", "\n".join(errors))
            return

        self._apply_normalized_identity_fields(normalized)
        profile = map_to_profile(normalized)
        analysis = self.service.analyze(profile, warnings=warnings)

        self.last_profile = profile
        self.last_analysis = analysis

        text = build_summary_text(profile, analysis)
        self._render_result_text(text)
        self._sync_pension_product_context()
        self._render_pension_result_panel(analysis)
        self._render_comparison_tables(profile, analysis)
        self._render_source_report(profile, analysis)
        self.status_var.set("분석 완료")

    def _apply_normalized_identity_fields(self, normalized):
        for key in ("birth_year", "birth_month", "birth_day", "age", "children_count"):
            self._set_widget_value(self.inputs[key], normalized.get(key, ""), numeric=True)
        self._set_widget_value(self.inputs["youngest_child_stage"], normalized.get("youngest_child_stage", "none"))

        for key, value in normalized["economic_assumptions"].items():
            self._set_widget_value(self.economic_inputs[key], value * 100.0, numeric=True)

        for key in self.product_inputs:
            self._set_widget_value(self.product_inputs[key], normalized["saving_products"].get(key, 0), numeric=True)

        for key in self.insurance_inputs:
            self._set_widget_value(self.insurance_inputs[key], normalized["insurance_products"].get(key, 0), numeric=True)

        home_goal = normalized["home_purchase_goal"]
        self._set_widget_value(self.home_purchase_inputs["house_price"], home_goal["house_price"], numeric=True)
        self._set_widget_value(self.home_purchase_inputs["ltv"], home_goal["ltv"] * 100.0, numeric=True)
        self._set_widget_value(self.home_purchase_inputs["dti"], home_goal["dti"] * 100.0, numeric=True)
        self._set_widget_value(self.home_purchase_inputs["target_years"], home_goal["target_years"], numeric=True)
        self._set_widget_value(self.home_purchase_inputs["loan_term_years"], home_goal["loan_term_years"], numeric=True)
        self._set_widget_value(
            self.home_purchase_inputs["loan_interest_rate"],
            home_goal["loan_interest_rate"] * 100.0,
            numeric=True,
        )
        self._set_goal_rows(normalized["special_goals"])
        self._sync_home_purchase_plan()

    def _set_goal_rows(self, goals):
        for row_data in self.goal_rows:
            row_data["frame"].destroy()
        self.goal_rows = []
        self.fixed_home_goal_row = None

        housing_goal_amount = ""
        housing_goal_years = ""
        other_goals = []
        for goal in goals or []:
            if str(goal.get("name", "")).strip() == "주택자금" and housing_goal_amount == "":
                housing_goal_amount = goal.get("target_amount", "")
                housing_goal_years = goal.get("target_years", "")
            else:
                other_goals.append(goal)

        if housing_goal_amount in ("", None) and self.home_purchase_inputs.get("house_price") is not None:
            housing_goal_amount = self._get_widget_value(self.home_purchase_inputs["house_price"])
        if housing_goal_years in ("", None) and self.home_purchase_inputs.get("target_years") is not None:
            housing_goal_years = self._get_widget_value(self.home_purchase_inputs["target_years"])

        self._add_goal_row("주택자금", housing_goal_amount, housing_goal_years, fixed=True)

        if other_goals:
            for goal in other_goals:
                self._add_goal_row(
                    goal.get("name", ""),
                    goal.get("target_amount", ""),
                    goal.get("target_years", ""),
                )
        else:
            self._add_goal_row()
        self._refresh_special_goal_savings_tab()

    def save_input(self):
        raw = self.collect_raw_input()
        path = filedialog.asksaveasfilename(
            title="입력 저장",
            defaultextension=".json",
            initialfile=build_input_filename(raw),
            filetypes=[("JSON 파일", "*.json")],
        )
        if not path:
            return
        save_profile(Path(path), raw)
        self.status_var.set(f"입력 저장 완료: {path}")

    def load_input(self):
        path = filedialog.askopenfilename(
            title="입력 불러오기",
            filetypes=[("JSON 파일", "*.json")],
        )
        if not path:
            return
        payload = load_profile(Path(path))
        self._set_payload(payload)
        self.status_var.set(f"입력 불러오기 완료: {path}")

    def _set_payload(self, payload):
        numeric_input_keys = {
            "birth_year",
            "birth_month",
            "birth_day",
            "age",
            "children_count",
            "household_income",
            "monthly_expense",
            "monthly_debt_payment",
            "monthly_saving_investment",
            "monthly_emergency_fund",
            "average_consumption",
            "liquid_assets",
            "non_liquid_assets",
        }
        for key, widget in self.inputs.items():
            value = payload.get(key, "")
            self._set_widget_value(widget, value, numeric=key in numeric_input_keys)

        economic_payload = payload.get("economic_assumptions", {})
        for key, widget in self.economic_inputs.items():
            self._set_widget_value(widget, economic_payload.get(key, DEFAULT_ECONOMIC_ASSUMPTIONS[key] * 100), numeric=True)

        self._set_goal_rows(payload.get("special_goals", []))

        for key, widget in self.category_inputs.items():
            self._set_widget_value(widget, payload.get("expense_categories", {}).get(key, 0), numeric=True)
        detail_payload = payload.get("expense_detail_categories", {})
        for category_key, detail_inputs in self.expense_detail_inputs.items():
            category_payload = detail_payload.get(category_key, {})
            for detail_key, widget in detail_inputs.items():
                self._set_widget_value(widget, category_payload.get(detail_key, ""), numeric=True)
        self._refresh_all_expense_category_totals()

        for key, widget in self.product_inputs.items():
            self._set_widget_value(widget, payload.get("saving_products", {}).get(key, 0), numeric=True)

        insurance_payload = payload.get("insurance_products", {})
        if not insurance_payload and payload.get("saving_products", {}).get("insurance"):
            insurance_payload = {
                "indemnity_insurance": 0,
                "life_insurance": payload.get("saving_products", {}).get("insurance", 0),
                "variable_insurance": 0,
            }
        for key, widget in self.insurance_inputs.items():
            self._set_widget_value(widget, insurance_payload.get(key, 0), numeric=True)

        home_payload = payload.get("home_purchase_goal", {})
        home_defaults = self.home_loan_context_service.get_recommended_defaults()
        home_defaults.update(home_payload)
        self._set_widget_value(self.home_purchase_inputs["house_price"], home_defaults["house_price"], numeric=True)
        self._set_widget_value(
            self.home_purchase_inputs["ltv"],
            home_defaults["ltv"] * 100.0 if home_defaults["ltv"] <= 1 else home_defaults["ltv"],
            numeric=True,
        )
        self._set_widget_value(
            self.home_purchase_inputs["dti"],
            home_defaults["dti"] * 100.0 if home_defaults["dti"] <= 1 else home_defaults["dti"],
            numeric=True,
        )
        self._set_widget_value(self.home_purchase_inputs["target_years"], home_defaults["target_years"], numeric=True)
        self._set_widget_value(self.home_purchase_inputs["loan_term_years"], home_defaults["loan_term_years"], numeric=True)
        self._set_widget_value(
            self.home_purchase_inputs["loan_interest_rate"],
            home_defaults["loan_interest_rate"] * 100.0
            if home_defaults["loan_interest_rate"] <= 1
            else home_defaults["loan_interest_rate"],
            numeric=True,
        )

        for key, widget in self.pension_inputs.items():
            self._set_widget_value(widget, payload.get("pension", {}).get(key, ""), numeric=True)

        self._on_marital_status_change()
        if self._get_widget_value(self.inputs["birth_year"]).strip():
            self._sync_age_from_birth()
        elif self._get_widget_value(self.inputs["age"]).strip():
            self._sync_birth_year_from_age()
        self._sync_home_purchase_plan()
        self._sync_pension_product_context()
        self._refresh_expense_summary()

    def fill_sample(self):
        self._fill_widget_if_empty(self.inputs["name"], "\ud64d\uae38\ub3d9")
        if self._get_widget_value(self.inputs["gender"]).strip() == "":
            self._set_widget_value(self.inputs["gender"], "male")
        self._fill_widget_if_empty(self.inputs["birth_year"], "1981", numeric=True)
        self._fill_widget_if_empty(self.inputs["birth_month"], "4", numeric=True)
        self._fill_widget_if_empty(self.inputs["birth_day"], "22", numeric=True)
        if self._get_widget_value(self.inputs["birth_year"]).strip():
            self._sync_age_from_birth()
        elif self._get_widget_value(self.inputs["age"]).strip():
            self._sync_birth_year_from_age()
        else:
            self._fill_widget_if_empty(self.inputs["age"], "45", numeric=True)
            self._sync_birth_year_from_age()
        if self._get_widget_value(self.inputs["marital_status"]).strip() == "":
            self._set_widget_value(self.inputs["marital_status"], "married")
        self._on_marital_status_change()
        if str(self.inputs["children_count"].cget("state")) != "disabled":
            self._fill_widget_if_empty(self.inputs["children_count"], "1", numeric=True)
        if self._get_widget_value(self.inputs["youngest_child_stage"]).strip() == "":
            self._set_widget_value(self.inputs["youngest_child_stage"], "middle_high")

        self._fill_widget_if_empty(self.inputs["household_income"], "628", numeric=True)
        self._fill_widget_if_empty(self.inputs["monthly_expense"], "379", numeric=True)
        self._fill_widget_if_empty(self.inputs["monthly_debt_payment"], "53", numeric=True)
        self._fill_widget_if_empty(self.inputs["monthly_saving_investment"], "108", numeric=True)
        self._fill_widget_if_empty(self.inputs["monthly_emergency_fund"], "88", numeric=True)
        self._fill_widget_if_empty(self.inputs["average_consumption"], "379", numeric=True)
        self._fill_widget_if_empty(self.inputs["liquid_assets"], "8055", numeric=True)
        self._fill_widget_if_empty(self.inputs["non_liquid_assets"], "68962", numeric=True)

        economic_defaults = self.economic_context_service.build_default_percent_map()
        for key, value in economic_defaults.items():
            self._fill_widget_if_empty(self.economic_inputs[key], value, numeric=True)

        reference_context = SimpleNamespace(
            age=self._get_numeric_value("age") or 45,
            marital_status=self._get_widget_value(self.inputs["marital_status"]).strip() or "married",
            children_count=self._get_numeric_value("children_count") or 0,
            youngest_child_stage=self._get_widget_value(self.inputs["youngest_child_stage"]).strip() or "none",
            household_income=self._entry_float(self.inputs["household_income"], 628.0),
            monthly_saving_investment=self._entry_float(self.inputs["monthly_saving_investment"], 108.0),
        )
        reference_samples = build_reference_sample_values(self.service.report_provider, reference_context)

        for key, value in reference_samples["financial_fields"].items():
            self._fill_widget_if_unset(self.inputs[key], value, numeric=True, zero_is_empty=True)

        for key, value in reference_samples["expense_categories"].items():
            self._fill_widget_if_unset(self.category_inputs[key], value, numeric=True, zero_is_empty=True)
        for key, value in reference_samples["saving_products"].items():
            self._fill_widget_if_unset(self.product_inputs[key], value, numeric=True, zero_is_empty=True)
        for key, value in reference_samples["insurance_products"].items():
            self._fill_widget_if_unset(self.insurance_inputs[key], value, numeric=True, zero_is_empty=True)

        sample_home_purchase = self.home_loan_context_service.build_default_input_map()
        fixed_home_value = ""
        if self.fixed_home_goal_row is not None:
            fixed_home_value = self.fixed_home_goal_row["target_amount"].get().strip()
        if self._widget_is_empty(self.home_purchase_inputs["house_price"]) and fixed_home_value:
            self._set_widget_value(self.home_purchase_inputs["house_price"], fixed_home_value, numeric=True)
        else:
            self._fill_widget_if_empty(
                self.home_purchase_inputs["house_price"],
                sample_home_purchase["house_price"],
                numeric=True,
            )
        for key in ("ltv", "dti", "target_years", "loan_term_years", "loan_interest_rate"):
            self._fill_widget_if_empty(self.home_purchase_inputs[key], sample_home_purchase[key], numeric=True)

        pension_current_age = self._get_widget_value(self.inputs["age"]).strip() or "45"
        sample_pension = {
            "current_age": pension_current_age,
            "retirement_age": "60",
            "expected_monthly_pension": "200",
            "current_balance": "3000",
        }
        for key, value in sample_pension.items():
            self._fill_widget_if_unset(self.pension_inputs[key], value, numeric=True, zero_is_empty=True)

        if self.fixed_home_goal_row is not None and self._widget_is_empty(self.fixed_home_goal_row["target_amount"]):
            self._set_home_goal_target_value(self._get_widget_value(self.home_purchase_inputs["house_price"]))
        if self.fixed_home_goal_row is not None and self._widget_is_empty(self.fixed_home_goal_row["target_years"]):
            self._set_home_goal_target_years_value(self._get_widget_value(self.home_purchase_inputs["target_years"]))

        non_fixed_rows = [row for row in self.goal_rows if not row.get("fixed")]
        filled_non_fixed_rows = [
            row
            for row in non_fixed_rows
            if row["name"].get().strip() or row["target_amount"].get().strip() or row["target_years"].get().strip()
        ]
        sample_goal_years = max(int(self._entry_float(self.home_purchase_inputs["target_years"], 10)), 1)
        if not filled_non_fixed_rows and non_fixed_rows:
            self._set_entry_value(non_fixed_rows[0]["name"], "\uad50\uc721\uc790\uae08")
            self._set_entry_value(non_fixed_rows[0]["target_amount"], "5000", numeric=True)
            self._set_entry_value(non_fixed_rows[0]["target_years"], min(sample_goal_years, 8), numeric=True)
        for row in non_fixed_rows:
            if (row["name"].get().strip() or row["target_amount"].get().strip()) and self._widget_is_empty(row["target_years"]):
                self._set_entry_value(row["target_years"], min(sample_goal_years, 8), numeric=True)

        self._sync_home_purchase_plan()
        self._sync_pension_product_context()
        self.status_var.set("\uc608\uc2dc\uac12\uc744 \ucc44\uc6e0\uc2b5\ub2c8\ub2e4.")

    def save_report(self):
        if not self.last_profile or not self.last_analysis:
            messagebox.showinfo("안내", "먼저 분석을 실행해 주세요.")
            return

        path = filedialog.asksaveasfilename(
            title="결과 JSON 저장",
            defaultextension=".json",
            initialfile=build_report_filename(self.last_profile),
            filetypes=[("JSON 파일", "*.json")],
        )
        if not path:
            return

        with open(path, "w", encoding="utf-8") as file:
            file.write(dumps_report(self.last_profile, self.last_analysis))
        self.status_var.set(f"결과 저장 완료: {path}")

    def save_word_report(self):
        if not self.last_profile or not self.last_analysis:
            messagebox.showinfo("안내", "먼저 분석을 실행해 주세요.")
            return

        path = filedialog.asksaveasfilename(
            title="워드 파일 저장",
            defaultextension=".docx",
            initialfile=build_word_report_filename(self.last_profile),
            filetypes=[("Word 파일", "*.docx")],
        )
        if not path:
            return

        write_word_report(Path(path), self.last_profile, self.last_analysis)
        self.status_var.set(f"워드 저장 완료: {path}")
