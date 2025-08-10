import tkinter as tk
from tkinter import simpledialog, messagebox, Toplevel, filedialog
from tkinter import ttk
from constants import (
    LABEL_TO_KEY,
    KEY_TO_LABEL,
    FILTER_OPTIONS,
    get_param_key_from_label as util_get_param_key_from_label,
    get_label_from_param_key as util_get_label_from_param_key,
)
from backend import StockDataService
from datetime import datetime

def format_number(value: float) -> str:
    """Return a human-readable string with comma separators."""
    try:
        return f"{int(round(float(value))):,}"
    except Exception:
        return str(value)


def calculate_dividend_yield(dividend, dividend_yield, price) -> float:
    """Return the dividend yield as a percentage.

    Parameters are expected to be raw values from the API where
    ``dividend_yield`` may be either a ratio (e.g. ``0.02`` for 2%) or a
    percentage (e.g. ``2`` for 2%).  If ``dividend_yield`` is not supplied
    the value is derived from ``dividend`` and ``price``.
    """
    try:
        dividend = float(dividend)
    except Exception:
        dividend = 0.0
    try:
        dividend_yield = float(dividend_yield)
    except Exception:
        dividend_yield = 0.0
    try:
        price = float(price)
    except Exception:
        price = 0.0

    if dividend_yield:
        # Many APIs return dividend yield as a ratio (e.g. 0.02 for 2%)
        # so multiply by 100 when the value is less than 1.  If the value
        # already appears to be a percentage leave it unchanged.
        if dividend_yield < 1:
            dividend_yield *= 100
        return dividend_yield

    if dividend and price:
        return (dividend / price) * 100
    return 0.0


def calculate_intraday_change(price, previous_close) -> tuple[float, float]:
    """Return the absolute and percentage change from the previous close."""
    try:
        price = float(price)
    except Exception:
        price = 0.0
    try:
        previous_close = float(previous_close)
    except Exception:
        previous_close = 0.0

    change = price - previous_close
    if previous_close:
        percent = (change / previous_close) * 100
    else:
        percent = 0.0
    return change, percent

class DraggableBlock(tk.Frame):
    def __init__(self, master, preview_block, app, drop_target):
        super().__init__(master)
        self.preview_block = preview_block
        self.app = app
        self.drop_target = drop_target
        self._drag_window = None
        self.drag_data = {'x': 0, 'y': 0}
        self.bind_all_children(preview_block)

    def bind_all_children(self, widget):
        # Recursively bind all children to forward drag events
        widget.bind("<ButtonPress-1>", self.start_drag, add="+")
        widget.bind("<B1-Motion>", self.do_drag, add="+")
        widget.bind("<ButtonRelease-1>", self.stop_drag, add="+")
        
        for child in widget.winfo_children():
            self.bind_all_children(child)

    def start_drag(self, event):
        self.drag_data['x'] = event.x
        self.drag_data['y'] = event.y

        self._drag_window = tk.Toplevel(self)
        self._drag_window.overrideredirect(True)
        self._drag_window.attributes("-topmost", True)

        # Clone appearance
        clone = self.clone_preview_block()
        clone.pack()

        self._drag_window.update_idletasks()
        self._drag_window.geometry(f"{clone.winfo_reqwidth()}x{clone.winfo_reqheight()}+0+0")
        self._update_drag_window(event)

    def do_drag(self, event):
        self._update_drag_window(event)

    def stop_drag(self, event):
        abs_x = self.preview_block.winfo_rootx() - self.drag_data['x'] + event.x
        abs_y = self.preview_block.winfo_rooty() - self.drag_data['y'] + event.y

        drop_x0 = self.drop_target.winfo_rootx()
        drop_x1 = drop_x0 + self.drop_target.winfo_width()
        drop_y0 = self.drop_target.winfo_rooty()
        drop_y1 = drop_y0 + self.drop_target.winfo_height()

        dropped_in_zone = drop_x0 <= abs_x <= drop_x1 and drop_y0 <= abs_y <= drop_y1

        if dropped_in_zone:
            label = self.preview_block._param_label
            if label in self.app.saved_algorithms:
                self.app.load_algorithm(label)
            else:
                self.app.add_filter_block(label)

        # Destroy immediately after drawing (or skipping drop)
        if self._drag_window:
            self._drag_window.destroy()

    def _update_drag_window(self, event):
        x = self.preview_block.winfo_rootx() - self.drag_data['x'] + event.x
        y = self.preview_block.winfo_rooty() - self.drag_data['y'] + event.y
        self._drag_window.geometry(f"+{x}+{y}")

    def clone_preview_block(self):
        # Reconstruct a visual-only replica of the preview block
        label_text = self.preview_block._param_label
        base_key = self.app.get_param_key_from_label(label_text)

        clone = tk.Frame(
            self._drag_window,
            bg="white",
            relief='solid',
            bd=1,
            width=280,
            height=80,
            highlightthickness=0,
        )
        clone.pack_propagate(False)

        title_row = tk.Frame(clone, bg="white")
        title_row.pack(fill="x", pady=(5, 0), padx=8)
        tk.Label(title_row, text=label_text, font=("Arial", 10, "bold"), bg="white").pack(side="left")

        # Determine visual layout based on filter type
        if any(x in base_key.lower() for x in ["sector", "industry", "exchange", "country", "is", "actively", "classes"]):
            dropdown_row = tk.Frame(clone, bg="white")
            dropdown_row.pack(fill="x", padx=10, pady=(5, 10))
            combo = ttk.Combobox(dropdown_row, font=("Arial", 10), state="disabled")
            combo.set("")
            combo.pack(fill="x")
        elif any(x in base_key.lower() for x in ["price", "marketcap", "volume", "limit", "dividend"]):
            if "marketcap" in base_key.lower():
                input_row = tk.Frame(clone, bg="white")
                input_row.pack(fill="x", padx=10, pady=(5, 10))
                tk.Entry(input_row, font=("Arial", 10), state="disabled").pack(side="left", fill="x", expand=True)
            else:
                slider_row = tk.Frame(clone, bg="white")
                slider_row.pack(fill="x", padx=10, pady=(2, 10))
                tk.Entry(slider_row, width=6, justify="center", relief="groove", font=("Arial", 10), state="disabled").pack(side="left", padx=(0, 10))
                tk.Scale(slider_row, from_=0, to=100, orient="horizontal", resolution=1, length=200, state="disabled").pack(side="left", fill="x", expand=True)

        return clone

class StockScreenerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Block-Based Stock Screener")
        self.root.geometry("1300x750")

        self.api_key = 'ilp96LS93HjMQOCCyXwbt5UmOKf5da16'
        self.base_url = 'https://financialmodelingprep.com/api/v3/stock-screener?'
        self.quote_url = 'https://financialmodelingprep.com/api/v3/quote/'
        self.params = {}

        self.snap_order = []
        self.result_tiles = {}  # Needed for render_stock_tile and cleanup
        self.saved_algorithms = {}
        # Track preview widgets for each saved algorithm so they can be
        # updated or removed later.
        self.algorithm_previews = {}
        # Name of the algorithm currently loaded in the editor, if any
        self.current_algorithm = None
        self.backend = StockDataService(self.api_key, self.base_url, self.quote_url)

        self.setup_layout()

    def setup_layout(self):
        # === LEFT PANEL ===
        self.left_frame = tk.Frame(self.root, width=300, bg="#f0f0f0")
        self.left_frame.pack(side="left", fill='y')
        self.left_frame.pack_propagate(False)  # Prevents shrinking to fit contents

        scroll_container = tk.Frame(self.left_frame, bg="#f0f0f0")
        scroll_container.pack(fill="both", expand=True)

        scroll_canvas = tk.Canvas(scroll_container, bg="#f0f0f0", highlightthickness=0)
        scroll_canvas.pack(side="left", fill="both", expand=True)

        vsb = tk.Scrollbar(scroll_container, orient="vertical", command=scroll_canvas.yview)
        vsb.pack(side="right", fill="y")
        scroll_canvas.configure(yscrollcommand=vsb.set)

        block_scroll = tk.Frame(scroll_canvas, bg="#f0f0f0")
        self.block_scroll = block_scroll  # Required for draggable blocks
        self.block_window_id = scroll_canvas.create_window((0, 0), window=block_scroll, anchor="nw", width=300)

        def on_frame_configure(event):
            scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all"))
            scroll_canvas.itemconfig(self.block_window_id, width=300)

        block_scroll.bind("<Configure>", on_frame_configure)

        def _on_mousewheel(event):
            scroll_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        scroll_canvas.bind("<Enter>", lambda e: scroll_canvas.bind_all("<MouseWheel>", _on_mousewheel))
        scroll_canvas.bind("<Leave>", lambda e: scroll_canvas.unbind_all("<MouseWheel>"))

        # === CENTER DROP ZONE ===
        self.block_area = tk.Frame(self.root, width=325, bg="#f9f9f9", relief='sunken', bd=2)
        self.block_area.pack_propagate(False)  # Prevent internal widgets from resizing the frame

        self.block_area.pack(side="left", fill="y")

        self.snap_zone = tk.Canvas(self.block_area, bg="#f0f8ff", height=700, width=325)
        self.snap_zone.pack(fill="both", expand=True, padx=10, pady=10)
        self.block_area.add_filter_block = self.add_filter_block

        self.snap_zone_placeholder = tk.Label(
            self.snap_zone, text="Drag and Drop Here", font=("Arial", 14, "italic"),
            fg="#a0c4e4", bg="#f0f8ff"
        )
        self.snap_zone_placeholder.place(relx=0.5, rely=0.5, anchor="center")

        # === RIGHT RESULTS PANEL ===
        self.right_frame = tk.Frame(self.root)
        self.right_frame.pack(side="right", fill="both", expand=True)

        self.results_container = tk.Frame(self.right_frame, bg="white")
        self.results_container.pack(fill="both", expand=True, padx=10, pady=10)

        self.results_canvas = tk.Canvas(self.results_container, bg="white", highlightthickness=0)
        self.results_canvas.pack(side="left", fill="both", expand=True)

        self.results_scrollbar = tk.Scrollbar(self.results_container, orient="vertical", command=self.results_canvas.yview)
        self.results_scrollbar.pack(side="right", fill="y")

        self.results_canvas.configure(yscrollcommand=self.results_scrollbar.set)

        self.results_frame = tk.Frame(self.results_canvas, bg="white")
        self.results_window_id = self.results_canvas.create_window((0, 0), window=self.results_frame, anchor="nw")

        def configure_scroll_region(event):
            self.results_canvas.configure(scrollregion=self.results_canvas.bbox("all"))
            self.results_canvas.itemconfig(self.results_window_id, width=self.results_canvas.winfo_width())

        self.results_frame.bind("<Configure>", configure_scroll_region)
        self.results_canvas.bind("<Configure>", configure_scroll_region)

        self.results_canvas.bind("<Enter>", lambda e: self.results_canvas.bind_all("<MouseWheel>", self._on_results_mousewheel))
        self.results_canvas.bind("<Leave>", lambda e: self.results_canvas.unbind_all("<MouseWheel>"))

        # === FILTER PREVIEWS ===
        filters = [
            ("Stock Search", lambda: self.set_parameter("stockSearch", str)),
            ("Sector", lambda: self.open_dropdown("sector", FILTER_OPTIONS["sector"])),
            ("Industry", lambda: self.open_dropdown("industry", FILTER_OPTIONS["industry"])),
            ("Exchange", lambda: self.open_dropdown("exchange", FILTER_OPTIONS["exchange"])),
            ("Is ETF?", lambda: self.open_dropdown("isEtf", FILTER_OPTIONS["isEtf"])),
            ("Is Fund?", lambda: self.open_dropdown("isFund", FILTER_OPTIONS["isFund"])),
            ("Lower Price", lambda: self.set_parameter("priceMoreThan", float)),
            ("Upper Price", lambda: self.set_parameter("priceLowerThan", float)),
            ("Lower Market Cap (10M-4T)", lambda: self.set_parameter("marketCapMoreThan", float)),
            ("Upper Market Cap (10M-4T)", lambda: self.set_parameter("marketCapLowerThan", float)),
            ("Lower Volume", lambda: self.set_parameter("volumeMoreThan", float)),
            ("Upper Volume", lambda: self.set_parameter("volumeLowerThan", float)),
            ("Lower Dividend", lambda: self.set_parameter("dividendMoreThan", float, 0.0)),
            ("Limit Results", lambda: self.set_parameter("limit", int)),
            # MVP Filters
            ("Revenue (TTM) ≥", lambda: self.set_parameter("rev_ttm_min", float)),
            ("YoY Revenue Growth ≥ (%)", lambda: self.set_parameter("yoy_rev_growth_pct_min", float)),
            ("YoY Growth Count (≥ last 4q)", lambda: self.set_parameter("yoy_growth_quarter_count_min", float)),
            ("Max QoQ Revenue Declines (last 4q)", lambda: self.set_parameter("max_qoq_rev_declines_last4", float)),
            ("Gross Margin % ≥", lambda: self.set_parameter("gross_margin_pct_min", float)),
            ("Δ Gross Margin YoY (pp) ≥", lambda: self.set_parameter("delta_gm_pp_yoy_min", float)),
            ("Opex % Slope (last 4q) ≤", lambda: self.set_parameter("opex_pct_slope_last4_max", float)),
            ("Operating CF (TTM) ≥", lambda: self.set_parameter("ocf_ttm_min", float)),
            ("Δ Operating CF TTM YoY ≥", lambda: self.set_parameter("delta_ocf_ttm_yoy_min", float)),
            ("R&D % of Revenue ≤", lambda: self.set_parameter("rd_pct_max", float)),
            ("Δ R&D % YoY (pp) ≤", lambda: self.set_parameter("delta_rd_pct_pp_yoy_max", float)),
            ("R&D Growth ≤ Revenue Growth (YoY)", lambda: self.open_dropdown("rd_growth_lte_rev_growth", FILTER_OPTIONS["rd_growth_lte_rev_growth"])),
            ("Deferred Revenue Rising (YoY)", lambda: self.open_dropdown("deferred_rev_yoy_increase", FILTER_OPTIONS["deferred_rev_yoy_increase"])),
            ("Cash Conversion Cycle Slope (last 4q) ≤", lambda: self.set_parameter("ccc_slope_last4_max", float)),
            ("Rule of 40 (Growth + Op Margin) ≥", lambda: self.set_parameter("rule40_op_ttm_min", float)),
            ("Capex % of Revenue ≤", lambda: self.set_parameter("capex_pct_max", float)),
        ]

        categories = {
            "Tools": [],
            "Drop Down Filters": [],
            "Write in Filters": [],
            "Numeric Filters": [],
            "MVP Filters": [],
        }

        algo_btn = tk.Button(
            self.block_scroll,
            text="＋ Save Algorithm",
            bg="#cce5ff", fg="#004085",
            font=("Arial", 10, "bold"),
            command=self.open_save_algorithm_dialog
        )
        algo_btn.pack(padx=10, pady=(5, 5), fill="x")

        update_btn = tk.Button(
            self.block_scroll,
            text="↻ Update Algorithm",
            bg="#d4edda", fg="#155724",
            font=("Arial", 10, "bold"),
            command=self.update_current_algorithm,
        )
        update_btn.pack(padx=10, pady=(0, 15), fill="x")

        self.algo_header = tk.Label(
            self.block_scroll,
            text="Saved Algorithms",
            bg="#e2e3e5",
            font=("Arial", 10, "bold"),
            anchor="w",
            width=37
        )
        self.algo_header.pack(padx=10, pady=(10, 2))

        self.algo_container = tk.Frame(self.block_scroll, bg="#f0f0f0")
        self.algo_container.pack(fill="x", padx=10)

        mvp_keys = {
            "rev_ttm_min",
            "yoy_rev_growth_pct_min",
            "yoy_growth_quarter_count_min",
            "max_qoq_rev_declines_last4",
            "gross_margin_pct_min",
            "delta_gm_pp_yoy_min",
            "opex_pct_slope_last4_max",
            "ocf_ttm_min",
            "delta_ocf_ttm_yoy_min",
            "rd_pct_max",
            "delta_rd_pct_pp_yoy_max",
            "rd_growth_lte_rev_growth",
            "deferred_rev_yoy_increase",
            "ccc_slope_last4_max",
            "rule40_op_ttm_min",
            "capex_pct_max",
        }

        for label, callback in filters:
            param_key = self.get_param_key_from_label(label)
            if param_key in ["stockSearch", "limit"]:
                categories["Tools"].append((label, callback))
            elif param_key in ["sector", "industry", "exchange", "isEtf", "isFund"]:
                categories["Drop Down Filters"].append((label, callback))
            elif param_key in ["marketCapMoreThan", "marketCapLowerThan"]:
                categories["Write in Filters"].append((label, callback))
            elif param_key in mvp_keys:
                categories["MVP Filters"].append((label, callback))
            else:
                categories["Numeric Filters"].append((label, callback))



        for cat in ["Tools", "Drop Down Filters", "Write in Filters", "Numeric Filters", "MVP Filters"]:
            group = categories[cat]
            header = tk.Label(
                self.block_scroll,
                text=cat,
                bg="#d0d0d0",
                font=("Arial", 10, "bold"),
                anchor="w",
                width=37
            )
            header.pack(padx=10, pady=(10, 2))

            for label, callback in group:
                preview_block = self.create_filter_preview_block(label, self.block_scroll)
                preview_block.pack(pady=3, padx=10)

                DraggableBlock(
                    master=self.left_frame,
                    preview_block=preview_block,
                    app=self,
                    drop_target=self.block_area
                )

    def _on_results_mousewheel(self, event):
        self.results_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


    def get_param_key_from_label(self, label):
        return util_get_param_key_from_label(label)

    def get_label_from_param_key(self, key):
        return util_get_label_from_param_key(key)

    def create_filter_preview_block(self, label, parent):
        base_key = self.get_param_key_from_label(label)

        frame = tk.Frame(
            parent,
            bg="white",
            relief='solid',
            bd=1,
            width=300,
            height=80,
            highlightthickness=0,
        )  # Container for filter preview blocks
        frame.pack_propagate(False)

        title_row = tk.Frame(frame, bg="white")
        title_row.pack(fill="x", pady=(5, 0), padx=8)
        tk.Label(title_row, text=label, font=("Arial", 10, "bold"), bg="white").pack(side="left")

        if base_key in FILTER_OPTIONS:
            options = FILTER_OPTIONS[base_key]
            if isinstance(options, list):
                dropdown_row = tk.Frame(frame, bg="white")
                dropdown_row.pack(fill="x", padx=10, pady=(5, 10))
                combo = ttk.Combobox(dropdown_row, values=options, font=("Arial", 10), state="disabled")
                combo.set('')
                combo.pack(side="left", fill="x", expand=True)
            elif isinstance(options, dict):
                slider_row = tk.Frame(frame, bg="white")
                slider_row.pack(fill="x", padx=10, pady=(2, 10))
                val_entry = tk.Entry(slider_row, width=6, justify="center", relief="groove", font=("Arial", 10), state="disabled")
                val_entry.insert(0, str(options.get('default', '')))
                val_entry.pack(side="left", padx=(0, 10))
                from_, to_, resolution = options.get('from', 0), options.get('to', 100), options.get('resolution', 1)
                slider = tk.Scale(slider_row, from_=from_, to=to_, orient="horizontal", resolution=resolution, length=200, state="disabled")
                slider.set(options.get('default', from_))
                slider.pack(side="left", fill="x", expand=True)

        elif any(term in base_key.lower() for term in ["price", "marketcap", "volume", "limit", "dividend"]):
            if "marketcap" in base_key.lower():
                input_row = tk.Frame(frame, bg="white")
                input_row.pack(fill="x", padx=10, pady=(5, 10))
                val_entry = tk.Entry(input_row, font=("Arial", 10), state="disabled")
                val_entry.insert(0, "")
                val_entry.pack(side="left", fill="x", expand=True)
            else:
                slider_row = tk.Frame(frame, bg="white")
                slider_row.pack(fill="x", padx=10, pady=(2, 10))
                val_entry = tk.Entry(slider_row, width=6, justify="center", relief="groove", font=("Arial", 10), state="disabled")
                val_entry.insert(0, "")
                val_entry.pack(side="left", padx=(0, 10))

                if 'price' in base_key.lower():
                    from_, to_, resolution = 0, 1000, 1
                elif 'volume' in base_key.lower():
                    from_, to_, resolution = 0, 1_000_000, 10_000
                elif 'limit' in base_key.lower():
                    from_, to_, resolution = 0, 100, 1
                elif 'dividend' in base_key.lower():
                    from_, to_, resolution = 0, 25, 0.1
                else:
                    from_, to_, resolution = 0, 200, 1

                slider = tk.Scale(
                    slider_row,
                    from_=from_,
                    to=to_,
                    orient="horizontal",
                    resolution=resolution,
                    length=200,
                    state="disabled",
                )
                slider.set(from_)
                slider.pack(side="left", fill="x", expand=True)

        elif base_key == "stockSearch":
            search_row = tk.Frame(frame, bg="white")
            search_row.pack(fill="x", padx=10, pady=(5, 10))
            entry = tk.Entry(search_row, font=("Arial", 10), state="disabled")
            entry.insert(0, "")
            entry.pack(side="left", fill="x", expand=True)

        frame._title_row = title_row  # store reference
        frame._param_label = label  # used for dragging
        return frame

    def add_filter_block(self, label, value=None):
        base_key = self.get_param_key_from_label(label)

        # Assign a unique key
        count = sum(1 for _, f in self.snap_order if f._param_key.startswith(base_key))
        key = f"{base_key}_{count+1}" if count else base_key


        block_frame = tk.Frame(
            self.snap_zone,
            bg="white",
            relief='solid',
            bd=1,
            width=280,
            height=80,
            highlightthickness=0,
        )
        block_frame.pack_propagate(False)
        block_frame._param_key = key

        title_row = tk.Frame(block_frame, bg="white")
        title_row.pack(fill="x", pady=(5, 0), padx=8)
        tk.Label(title_row, text=label, font=("Arial", 10, "bold"), bg="white").pack(side="left")

        remove_button = tk.Button(
            title_row, text="✖", font=("Arial", 10), fg="red", bg="white", relief="flat",
            command=lambda: self.remove_filter_block(block_frame, key)
        )
        remove_button.pack(side="right")

        if base_key in FILTER_OPTIONS:
            options = FILTER_OPTIONS[base_key]
            if isinstance(options, list):
                dropdown_row = tk.Frame(block_frame, bg="white")
                dropdown_row.pack(fill="x", padx=10, pady=(5, 10))

                default = value if value is not None else (options[0] if options else "")
                combo = ttk.Combobox(dropdown_row, values=[str(o) for o in options], font=("Arial", 10), state="readonly")
                combo.set(str(default))

                combo.pack(side="left", fill="x", expand=True)

                if default != "":
                    self.params[key] = default

                def update_selection(event):
                    selected = combo.get()
                    if selected:
                        try:
                            idx = combo.current()
                            self.params[key] = options[idx]
                        except Exception:
                            self.params[key] = selected
                    else:
                        self.params.pop(key, None)
                    self.delayed_search()  # use this instead of update_display()

                combo.bind("<<ComboboxSelected>>", update_selection)
            elif isinstance(options, dict):
                val_var = tk.StringVar(value="")
                slider_row = tk.Frame(block_frame, bg="white")
                slider_row.pack(fill="x", padx=10, pady=(2, 10))

                val_entry = tk.Entry(
                    slider_row,
                    textvariable=val_var,
                    width=6,
                    justify="center",
                    relief="groove",
                    font=("Arial", 10),
                )
                val_entry.pack(side="left", padx=(0, 10))

                from_, to_, resolution = options.get('from', 0), options.get('to', 100), options.get('resolution', 1)
                default = value if value is not None else options.get('default', from_)

                slider = tk.Scale(
                    slider_row,
                    from_=from_,
                    to=to_,
                    orient="horizontal",
                    resolution=resolution,
                    length=200,
                )
                slider.pack(side="left", fill="x", expand=True)

                value_label = tk.Label(slider_row, text="", font=("Arial", 9), bg="white")
                value_label.place(in_=slider, relx=0, y=-8, anchor="s")

                def update_value_display(val):
                    try:
                        numeric = float(val)
                    except ValueError:
                        numeric = 0
                    formatted = f"{numeric:,.2f}"
                    value_label.config(text=formatted)
                    ratio = (numeric - from_) / (to_ - from_)
                    ratio = max(0, min(1, ratio))
                    value_label.place(in_=slider, relx=ratio, y=-8, anchor="s")

                def on_slider_move(val):
                    val_var.set(f"{float(val):,.2f}")
                    update_value_display(val)

                def on_slider_release(event):
                    try:
                        val = float(slider.get())
                        update_value_display(val)
                        self.params[key] = val
                        self.update_display()
                    except ValueError:
                        self.params.pop(key, None)

                def on_entry_return(event):
                    try:
                        val = float(val_var.get().replace(',', ''))
                        slider.set(val)
                        self.params[key] = val
                        self.update_display()
                    except ValueError:
                        self.params.pop(key, None)

                slider.config(command=on_slider_move)
                slider.bind("<ButtonRelease-1>", on_slider_release)
                val_entry.bind("<Return>", on_entry_return)

                slider.set(default)
                val_var.set(f"{float(default):,.2f}")
                update_value_display(default)
                self.params[key] = default

        elif base_key == "stockSearch":
            search_row = tk.Frame(block_frame, bg="white")
            search_row.pack(fill="x", padx=10, pady=(5, 10))

            entry = tk.Entry(search_row, font=("Arial", 10))
            entry.pack(side="left", fill="x", expand=True)
            if value is not None:
                entry.insert(0, str(value))
                self.params[key] = value

            self._stock_search_delay_id = None

            def delayed_update():
                text = entry.get()
                if text:
                    self.params[key] = text
                else:
                    self.params.pop(key, None)
                self.update_display()

            def on_type(event):
                if self._stock_search_delay_id:
                    self.root.after_cancel(self._stock_search_delay_id)
                self._stock_search_delay_id = self.root.after(300, delayed_update)

            entry.bind("<KeyRelease>", on_type)

        elif any(term in base_key.lower() for term in ["price", "marketcap", "volume", "limit", "dividend"]):
            val_var = tk.StringVar(value="")

            if 'marketcap' in key.lower():
                input_row = tk.Frame(block_frame, bg="white")
                input_row.pack(fill="x", padx=10, pady=(5, 10))

                val_entry = tk.Entry(
                    input_row,
                    textvariable=val_var,
                    font=("Arial", 10),
                )
                val_entry.pack(side="left", fill="x", expand=True)

                from_, to_ = 10_000_000, 4_000_000_000_000

                def on_entry_return(event):
                    try:
                        val = float(val_var.get().replace(',', ''))
                        val = round(val / 1_000_000) * 1_000_000
                        val_var.set(format_number(val))
                        if from_ <= val <= to_:
                            self.params[key] = val
                        else:
                            self.params.pop(key, None)
                        self.update_display()
                    except ValueError:
                        self.params.pop(key, None)

                val_entry.bind("<Return>", on_entry_return)
                if value is not None:
                    val = max(min(value, to_), from_)
                    val_var.set(format_number(val))
                    self.params[key] = val
            else:
                slider_row = tk.Frame(block_frame, bg="white")
                slider_row.pack(fill="x", padx=10, pady=(2, 10))

                val_entry = tk.Entry(
                    slider_row,
                    textvariable=val_var,
                    width=6,
                    justify="center",
                    relief="groove",
                    font=("Arial", 10),
                )
                val_entry.pack(side="left", padx=(0, 10))

                if 'price' in key.lower():
                    from_, to_, resolution = 0, 10_000, 1
                elif 'volume' in key.lower():
                    from_, to_, resolution = 0, 1_000_000, 10_000
                elif 'limit' in key.lower():
                    from_, to_, resolution = 0, 100, 1
                elif 'dividend' in key.lower():
                    from_, to_, resolution = 0, 25, 0.1
                else:
                    from_, to_, resolution = 0, 200, 1

                slider = tk.Scale(
                    slider_row,
                    from_=from_,
                    to=to_,
                    orient="horizontal",
                    resolution=resolution,
                    length=200,
                )
                slider.pack(side="left", fill="x", expand=True)

                value_label = tk.Label(slider_row, text="", font=("Arial", 9), bg="white")
                value_label.place(in_=slider, relx=0, y=-8, anchor="s")

                def update_value_display(val):
                    try:
                        numeric = float(val)
                    except ValueError:
                        numeric = 0
                    formatted = f"{numeric:,.2f}"
                    value_label.config(text=formatted)
                    ratio = (numeric - from_) / (to_ - from_)
                    ratio = max(0, min(1, ratio))
                    value_label.place(in_=slider, relx=ratio, y=-8, anchor="s")

                update_value_display(slider.get())

                def on_slider_move(val):
                    val_var.set(f"{float(val):,.2f}")
                    update_value_display(val)

                def on_slider_release(event):
                    try:
                        val = float(slider.get())
                        update_value_display(val)
                        if key not in self.params or self.params[key] != val:
                            self.params[key] = val
                            self.update_display()
                    except ValueError:
                        self.params.pop(key, None)

                def on_entry_return(event):
                    try:
                        val = float(val_var.get().replace(',', ''))
                        slider.set(val)
                        self.params[key] = val
                        update_value_display(val)
                        self.update_display()
                    except ValueError:
                        self.params.pop(key, None)

                slider.config(command=on_slider_move)
                slider.bind("<ButtonRelease-1>", on_slider_release)
                val_entry.bind("<Return>", on_entry_return)
                if value is not None:
                    slider.set(value)
                    val_var.set(f"{float(value):,.2f}")
                    self.params[key] = value
                    update_value_display(value)


        # Add to snap zone
        item_id = self.snap_zone.create_window(10, 30 + len(self.snap_order) * 90, anchor='nw', window=block_frame)
        self.snap_order.append((item_id, block_frame))
        self.snap_zone_placeholder.place_forget()
        self.reposition_snap_zone()

    def reposition_snap_zone(self):
        for i, (item_id, _) in enumerate(self.snap_order):
            self.snap_zone.coords(item_id, 10, 30 + i * 90)

    def slider_update(self, key, val): 
        try:
            val = float(val)
            if isinstance(self.params.get(key), int):
                val = int(val)
            self.params[key] = val

            self.update_display()
            self.delayed_search()
        except Exception as e:
            print(f"Slider error: {e}")


    def remove_filter_block(self, frame, key):
        frame.destroy()

        if key in self.params:
            del self.params[key]

        self.snap_order = [(item_id, f) for item_id, f in self.snap_order if f != frame]

        if not self.snap_order:
            self.snap_zone_placeholder.place(relx=0.5, rely=0.5, anchor="center")

        self.reposition_snap_zone()

    def open_save_algorithm_dialog(self):
        if not self.params:
            messagebox.showinfo("Save Algorithm", "Add filters to the workspace first.")
            return

        top = Toplevel(self.root)
        top.title("Save Algorithm")
        top.geometry("300x120")

        tk.Label(top, text="Algorithm Name:").pack(pady=(10,0), padx=10, anchor="w")
        name_entry = tk.Entry(top)
        name_entry.pack(padx=10, fill="x")
        name_entry.focus()

        def submit():
            name = name_entry.get().strip()
            if not name:
                return
            self.save_algorithm(name)
            top.destroy()

        tk.Button(top, text="Save", command=submit).pack(pady=10)

    def save_algorithm(self, name: str):
        """Save the current parameters under ``name``.

        If an algorithm with the same name already exists it will be
        replaced, allowing users to update previous saves without creating
        duplicates.
        """
        self.saved_algorithms[name] = dict(self.params)
        self.current_algorithm = name
        if name not in self.algorithm_previews:
            self._add_algorithm_preview(name)

    def delete_algorithm(self, name: str):
        """Delete a previously saved algorithm."""
        self.saved_algorithms.pop(name, None)
        frame = self.algorithm_previews.pop(name, None)
        if frame:
            frame.destroy()
        if self.current_algorithm == name:
            self.current_algorithm = None

    def update_current_algorithm(self):
        """Update the currently loaded algorithm with current parameters."""
        if not self.current_algorithm:
            messagebox.showinfo("Update Algorithm", "No algorithm loaded to update.")
            return
        self.save_algorithm(self.current_algorithm)

    def _add_algorithm_preview(self, name):
        frame = tk.Frame(self.algo_container, bg="white", relief="solid", bd=1, width=300, height=50)
        frame.pack_propagate(False)

        label = tk.Label(frame, text=name, font=("Arial", 10, "bold"), bg="white")
        label.pack(fill="both", expand=True, padx=(20, 0))

        frame._param_label = name
        DraggableBlock(master=self.left_frame, preview_block=frame, app=self, drop_target=self.block_area)

        # Add delete "x" button on the far left
        btn = tk.Button(
            frame,
            text="✖",
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#721c24",
            relief="flat",
            command=lambda n=name: self.delete_algorithm(n),
        )
        btn.place(x=2, rely=0.5, anchor="w")
        btn.bind("<Button-1>", lambda e: "break")
        btn.bind("<B1-Motion>", lambda e: "break")
        btn.bind("<ButtonRelease-1>", lambda e: "break")

        frame.pack(pady=4)
        self.algorithm_previews[name] = frame

    def load_algorithm(self, name):
        params = self.saved_algorithms.get(name)
        if not params:
            return

        # Clear existing workspace
        for _, frame in self.snap_order:
            frame.destroy()
        self.snap_order.clear()
        self.params.clear()

        for key, value in params.items():
            label = self.get_label_from_param_key(key)
            self.add_filter_block(label, value)

        self.reposition_snap_zone()
        self.update_display()
        self.current_algorithm = name

    def open_dropdown(self, key, options):
        def submit_selection():
            selected = combo.get()
            if selected:
                self.params[key] = selected
                self.update_display()
            top.destroy()

        top = Toplevel(self.root)
        top.title(f"Select {key}")
        top.geometry("300x100")
        tk.Label(top, text=f"Select a value for {key}:").pack(pady=5)

        combo = ttk.Combobox(top, values=options)
        combo.pack(pady=5, padx=10, fill="x")
        combo.focus()

        tk.Button(top, text="OK", command=submit_selection).pack(pady=5)

    # Remove usage of simpledialog in set_parameter()
    def set_parameter(self, key: str, value_type: type, default_value=None):
        if default_value is None:
            default_value = 100.0 if value_type == float else 100
        self.params[key] = default_value
        self.add_filter_block(key, default_value)
        self.update_display()
        self.delayed_search()

    def update_display(self):
        self.search_stocks()
        
    def delayed_search(self, delay_ms=10):  # intentionally delay search to speed up snapping mechanism for the search blocks
        if hasattr(self, '_search_delay_id'):
            self.root.after_cancel(self._search_delay_id)
        self._search_delay_id = self.root.after(delay_ms, self.search_stocks)

    def search_stocks(self):
        try:
            data = self.backend.search(self.params)
            self.render_results(data)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch data:\n{e}")

    def render_results(self, data):
        # Clear old tiles
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        self.root.after(50, lambda: self.results_canvas.yview_moveto(0))

        if isinstance(data, list) and data:
            symbols = [item.get("symbol", "") for item in data if "symbol" in item]
            quote_data = self.backend.get_quotes(symbols)
            quote_map = {q["symbol"]: q for q in quote_data if "symbol" in q}

            for item in data:
                symbol = item.get('symbol', 'N/A')
                quote = quote_map.get(symbol, {})
                # prefer name from item when available
                if item.get('name'):
                    quote = {**quote, 'name': item['name']}
                self.render_stock_tile(symbol, quote)
        else:
            tk.Label(
                self.results_frame,
                text="No results found or error in response.",
                bg="white", fg="gray", font=("Arial", 11, "italic")
            ).pack(pady=20)

    def get_historical_prices(self, symbol):
        return self.backend.get_historical_prices(symbol)

    def get_profile(self, symbol):
        return self.backend.get_profile(symbol)

    def render_stock_tile(self, symbol, quote_data, parent=None):
        if parent is None:
            parent = self.results_frame

        name = quote_data.get('name', 'Unknown Company')
        price = quote_data.get('price', 0)
        change = quote_data.get('changesPercentage', 0)
        price_color = "green" if change >= 0 else "red"

        frame = tk.Frame(parent, bd=1, relief="solid", bg="white")
        frame.pack(padx=8, pady=6, fill="x")
        self.result_tiles[symbol] = frame

        # Remove button
        remove_btn = tk.Button(frame, text="✖", font=("Arial", 10), fg="red", bg="white", relief="flat",
            command=lambda: self.remove_stock_tile(symbol))
        remove_btn.place(relx=1.0, x=-16, y=4, anchor="ne")

        dropdown_frame = [None]  # Lazy-loaded dropdown

        def toggle_dropdown(btn):
            if dropdown_frame[0] is None:
                profile = self.get_profile(symbol)
                dropdown = ResultDropdown(
                    frame,
                    symbol=symbol,
                    quote_data=quote_data,
                    profile_data=profile,
                    backend=self.backend,
                )
                dropdown.pack(fill="x", padx=10, pady=(5, 10))
                dropdown_frame[0] = dropdown
                btn.config(text="▲")
            else:
                if dropdown_frame[0].winfo_ismapped():
                    dropdown_frame[0].pack_forget()
                    btn.config(text="▼")
                else:
                    dropdown_frame[0].pack(fill="x", padx=10, pady=(5, 10))
                    btn.config(text="▲")

        # Ticker + price
        top_row = tk.Frame(frame, bg="white")
        top_row.pack(fill="x", padx=10, pady=(5, 0))
        tk.Label(top_row, text=symbol, font=("Arial", 18, "bold"), fg="black", bg="white").pack(side="left")
        tk.Label(top_row, text=f"{price:.2f}", font=("Arial", 18, "bold"), fg=price_color, bg="white").pack(side="right")

        # Name + toggle
        bottom_row = tk.Frame(frame, bg="white")
        bottom_row.pack(fill="x", padx=10, pady=(3, 8))
        tk.Label(bottom_row, text=name, font=("Arial", 9), fg="gray", bg="white",
                justify="left", anchor="w").pack(side="left", fill="x", expand=True)

        toggle_btn = tk.Button(bottom_row, text="▼", font=("Arial", 10), bg="white", relief="flat")
        toggle_btn.pack(side="right")
        toggle_btn.config(command=lambda b=toggle_btn: toggle_dropdown(b))

        # Allow clicking anywhere on the stock tile (including its child widgets)
        # to toggle the dropdown.  Bind recursively so clicks on labels or other
        # widgets also trigger the handler, while skipping the remove and toggle
        # buttons to prevent duplicate toggles.
        def on_tile_click(event, btn=toggle_btn):
            if event.widget not in (btn, remove_btn):
                toggle_dropdown(btn)

        def bind_widget_tree(widget):
            widget.bind("<Button-1>", on_tile_click, add="+")
            for child in widget.winfo_children():
                bind_widget_tree(child)

        bind_widget_tree(frame)
    
    def remove_stock_tile(self, symbol):
        frame = self.result_tiles.pop(symbol, None)
        if frame:
            frame.destroy()
            self.results_canvas.yview_moveto(0)  # Scroll to top

class ResultDropdown(tk.Frame):
    def __init__(self, parent, symbol, quote_data, profile_data=None, backend=None):
        super().__init__(parent, bg="#f5f5f5", height=100)
        self.symbol = symbol
        self.quote_data = quote_data or {}
        self.profile_data = profile_data or {}
        self.backend = backend

        self.build_dropdown_content()

    def build_dropdown_content(self):
        price = self.quote_data.get("price") or self.profile_data.get("price")

        prev_close = (
            self.quote_data.get("previousClose")
            or self.profile_data.get("previousClose")
            or 0
        )
        change, change_pct = calculate_intraday_change(price, prev_close)
        change_color = "green" if change >= 0 else "red"

        dividend = (
            self.quote_data.get("lastDiv")
            or self.profile_data.get("lastDiv")
            or 0
        )
        dividend_yield = calculate_dividend_yield(
            dividend,
            self.quote_data.get("dividendYield")
            or self.profile_data.get("dividendYield")
            or 0,
            price,
        )
        try:
            dividend = float(dividend)
        except Exception:
            dividend = 0.0

        change_row = tk.Frame(self, bg="#f5f5f5")
        change_row.pack(fill="x", padx=10, pady=2)
        tk.Label(
            change_row,
            text="Intra-day Change:",
            width=15,
            anchor="w",
            bg="#f5f5f5",
        ).pack(side="left")
        tk.Label(
            change_row,
            text=f"{change:+.2f} ({change_pct:+.2f}%)",
            anchor="w",
            bg="#f5f5f5",
            fg=change_color,
        ).pack(side="left")

        metrics = [
            (
                "Market Cap",
                format_number(
                    self.quote_data.get("marketCap")
                    or self.profile_data.get("mktCap")
                    or 0
                ),
            ),
            ("P/E Ratio", self.quote_data.get("pe", "N/A")),
            ("Volume", format_number(self.quote_data.get("volume") or 0)),
            ("Dividend", f"{dividend:.2f}"),
            ("Dividend Yield", f"{dividend_yield:.2f}%"),
            ("Listed Sector", self.profile_data.get("sector", "N/A")),
            ("Listed Industry", self.profile_data.get("industry", "N/A")),
            (
                "Listed Exchange",
                self.profile_data.get("exchangeShortName")
                or self.profile_data.get("exchange", "N/A"),
            ),
        ]

        for label_text, value in metrics:
            row = tk.Frame(self, bg="#f5f5f5")
            row.pack(fill="x", padx=10, pady=2)
            tk.Label(row, text=f"{label_text}:", width=15, anchor="w", bg="#f5f5f5").pack(side="left")
            tk.Label(row, text=str(value), anchor="w", bg="#f5f5f5").pack(side="left")

if __name__ == "__main__":
    root = tk.Tk()
    app = StockScreenerApp(root)
    root.mainloop()
