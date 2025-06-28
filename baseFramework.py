import tkinter as tk
from tkinter import simpledialog, messagebox, Toplevel, filedialog
from tkinter import ttk
try:
    import requests
except Exception:  # pragma: no cover - optional dependency for tests
    class _RequestsStub:
        def get(self, *a, **k):
            raise ModuleNotFoundError("requests is required to fetch remote data")

    requests = _RequestsStub()
import json
try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import matplotlib.dates as mdates
except Exception:  # pragma: no cover - optional dependency for tests
    FigureCanvasTkAgg = Figure = mdates = None
from datetime import datetime

# Mapping between UI labels and parameter keys
LABEL_TO_KEY = {
    # Numeric filters
    "Lower Price": "priceMoreThan",
    "Upper Price": "priceLowerThan",
    "Lower Market Cap": "marketCapMoreThan",
    "Upper Market Cap": "marketCapLowerThan",
    "Lower Volume": "volumeMoreThan",
    "Upper Volume": "volumeLowerThan",
    "Lower Beta": "betaMoreThan",
    "Upper Beta": "betaLowerThan",
    "Lower Dividend": "dividendMoreThan",
    "Upper Dividend": "dividendLowerThan",
    # Dropdowns + Boolean filters
    "Sector": "sector",
    "Industry": "industry",
    "Exchange": "exchange",
    "Is ETF?": "isEtf",
    "Is Fund?": "isFund",
    "Market Stage": "marketStage",
    "YoY Growth (%)": "yoyGrowth",
    "Profit Margin (%)": "profitMargin",
    "R&D Ratio (%)": "rdRatio",
    "Company Age (yrs)": "companyAge",
    "Rule of 40": "ruleOf40",
    "MVP Stage": "mvpStage",
    # Misc Filters
    "Stock Search": "stockSearch",
    "Limit Results": "limit",
}

KEY_TO_LABEL = {v: k for k, v in LABEL_TO_KEY.items()}

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

        label = self.preview_block._param_label

        target_container = None
        for c in self.app.containers:
            cx0 = c.winfo_rootx()
            cx1 = cx0 + c.winfo_width()
            cy0 = c.winfo_rooty()
            cy1 = cy0 + c.winfo_height()
            if cx0 <= abs_x <= cx1 and cy0 <= abs_y <= cy1:
                target_container = c
                break

        if dropped_in_zone or target_container:
            if label == "Container" and not target_container:
                self.app.add_container_block()
            elif label in self.app.saved_algorithms:
                self.app.load_algorithm(label)
            else:
                self.app.add_filter_block(label, container=target_container)


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

        if label_text == "Container":
            clone = tk.Frame(self._drag_window, bg="#dfefff", relief="groove", bd=2, width=300, height=80)
            clone.pack_propagate(False)
            tk.Label(clone, text="Container", font=("Arial", 10, "bold"), bg="#dfefff").pack(expand=True)
            return clone

        clone = tk.Frame(self._drag_window, bg="white", relief='solid', bd=1, width=300, height=80)
        clone.pack_propagate(False)

        title_row = tk.Frame(clone, bg="white")
        title_row.pack(fill="x", pady=(5, 0), padx=8)
        tk.Label(title_row, text=label_text, font=("Arial", 10, "bold"), bg="white").pack(side="left")

        # Determine visual layout based on filter type
        if any(x in base_key.lower() for x in ["sector", "industry", "exchange", "country", "is", "actively", "classes", "marketStage"]):
            dropdown_row = tk.Frame(clone, bg="white")
            dropdown_row.pack(fill="x", padx=10, pady=(5, 10))
            combo = ttk.Combobox(dropdown_row, font=("Arial", 10), state="disabled")
            if base_key == "marketStage":
                combo.set("Rule of 40: Growth + Margin >= 40%")
            else:
                combo.set("")  # Leave blank for all other dropdowns

            combo.pack(fill="x")
        elif any(x in base_key.lower() for x in ["price", "marketcap", "volume", "beta", "dividend", "limit"]):
            slider_row = tk.Frame(clone, bg="white")
            slider_row.pack(fill="x", padx=10, pady=(2, 10))
            tk.Entry(slider_row, width=6, justify="center", relief="groove", font=("Arial", 10), state="disabled").pack(side="left", padx=(0, 10))
            tk.Scale(slider_row, from_=0, to=100, orient="horizontal", resolution=1, length=200, state="disabled").pack(side="left", fill="x", expand=True)

        return clone


class ContainerBlock(tk.Frame):
    def __init__(self, master, app, name="Container"):
        super().__init__(master, bg="#dfefff", relief="groove", bd=2)
        self.app = app
        self.name = name
        header = tk.Frame(self, bg="#dfefff")
        header.pack(fill="x")
        tk.Label(header, text=name, font=("Arial", 10, "bold"), bg="#dfefff")\
            .pack(side="left")
        remove_btn = tk.Button(
            header, text="✖", font=("Arial", 10), fg="red", bg="#dfefff",
            relief="flat", command=self.remove_self
        )
        remove_btn.pack(side="right")

        self.canvas = tk.Canvas(self, bg="#f0f8ff", height=150, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=5, pady=5)
        self.snap_order = []

    def add_filter_block(self, label, value=None):
        frame = self.app._create_filter_block(self.canvas, self.snap_order, label, value)
        self.reposition()
        return frame

    def reposition(self):
        for i, (item_id, _) in enumerate(self.snap_order):
            self.canvas.coords(item_id, 10, 30 + i * 90)

    def remove_self(self):
        for _, f in list(self.snap_order):
            self.app.remove_filter_block(f, f._param_key, container=self)
        self.app.containers = [c for c in self.app.containers if c != self]
        self.app.snap_order = [t for t in self.app.snap_order if t[1] != self]
        self.destroy()
        self.app.reposition_snap_zone()

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
        self._income_cache = {}  # Cache for income statement data
        self.saved_algorithms = {}
        self.containers = []

        self.setup_layout()

    def add_container_block(self):
        container = ContainerBlock(self.snap_zone, self)
        item_id = self.snap_zone.create_window(10, 30 + len(self.snap_order) * 90, anchor='nw', window=container)
        self.snap_order.append((item_id, container))
        self.containers.append(container)
        self.snap_zone_placeholder.place_forget()
        self.reposition_snap_zone()

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
        self.block_area = tk.Frame(self.root, width=345, bg="#f9f9f9", relief='sunken', bd=2)
        self.block_area.pack_propagate(False)  # Prevent internal widgets from resizing the frame

        self.block_area.pack(side="left", fill="y")

        self.snap_zone = tk.Canvas(self.block_area, bg="#f0f8ff", height=700, width=345)
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
            ("Container", None),
            ("Stock Search", lambda: self.set_parameter("stockSearch", str)),
            ("Sector", lambda: self.open_dropdown("sector", ["Technology", "Energy", "Healthcare", "Financial Services", "Consumer Cyclical",
                                                            "Communication Services", "Industrials", "Basic Materials", "Real Estate", "Utilities"])),
            ("Industry", lambda: self.open_dropdown("industry", ["Software", "Oil & Gas", "Biotechnology", "Banks", "Retail", "Semiconductors"])),
            ("Exchange", lambda: self.open_dropdown("exchange", ["NASDAQ", "NYSE", "AMEX"])),
            ("Is ETF?", lambda: self.open_dropdown("isEtf", ["true", "false"])),
            ("Is Fund?", lambda: self.open_dropdown("isFund", ["true", "false"])),
            ("Lower Price", lambda: self.set_parameter("priceMoreThan", float)),
            ("Upper Price", lambda: self.set_parameter("priceLowerThan", float)),
            ("Lower Market Cap", lambda: self.set_parameter("marketCapMoreThan", float)),
            ("Upper Market Cap", lambda: self.set_parameter("marketCapLowerThan", float)),
            ("Lower Beta", lambda: self.set_parameter("betaMoreThan", float)),
            ("Upper Beta", lambda: self.set_parameter("betaLowerThan", float)),
            ("Lower Dividend", lambda: self.set_parameter("dividendMoreThan", float)),
            ("Upper Dividend", lambda: self.set_parameter("dividendLowerThan", float)),
            ("Lower Volume", lambda: self.set_parameter("volumeMoreThan", float)),
            ("Upper Volume", lambda: self.set_parameter("volumeLowerThan", float)),
            ("Limit Results", lambda: self.set_parameter("limit", int)),
            ("Market Stage", lambda: self.open_dropdown("marketStage", ["Rule of 40: Growth + Margin >= 40%"]))
            ,("YoY Growth (%)",    lambda: self.open_dropdown("yoyGrowth", ["Annual", "Quarterly"]))
            ,("Profit Margin (%)", lambda: self.open_dropdown("profitMargin", ["Annual", "Quarterly"]))
            ,("R&D Ratio (%)",     lambda: self.open_dropdown("rdRatio", ["Annual", "Quarterly"]))
            ,("Company Age (yrs)", lambda: self.open_parameter("companyAge", int))
            ,("Rule of 40",        lambda: self.open_dropdown("ruleOf40", ["≥ 40"]))
            ,("MVP Stage",         lambda: self.open_dropdown("mvpStage", ["Pre-product","Early Product","Scaling"]))
        ]

        categories = {
            "Tools": [],
            "Drop Down Filters": [],
            "Numeric Filters": []
        }

        algo_btn = tk.Button(
            self.block_scroll,
            text="＋ Save Algorithm",
            bg="#cce5ff", fg="#004085",
            font=("Arial", 10, "bold"),
            command=self.open_save_algorithm_dialog
        )
        algo_btn.pack(padx=10, pady=(5, 15), fill="x")

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

        for label, callback in filters:
            param_key = self.get_param_key_from_label(label)
            if label == "Container" or param_key in ["stockSearch", "limit"]:
                categories["Tools"].append((label, callback))
            elif param_key in ["sector", "industry", "exchange", "isEtf", "isFund"]:
                categories["Drop Down Filters"].append((label, callback))
            else:
                categories["Numeric Filters"].append((label, callback))



        for cat in ["Tools", "Drop Down Filters", "Numeric Filters"]:
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
        return LABEL_TO_KEY.get(label, label)

    def get_label_from_param_key(self, key):
        base = key.split('_')[0]
        return KEY_TO_LABEL.get(base, base)

    def create_filter_preview_block(self, label, parent):
        base_key = self.get_param_key_from_label(label)
        if label == "Container":
            frame = tk.Frame(parent, bg="#dfefff", relief="groove", bd=2, width=300, height=80)
            frame.pack_propagate(False)
            tk.Label(frame, text="Container", font=("Arial", 10, "bold"), bg="#dfefff").pack(expand=True)
            frame._param_label = label
            return frame
        options_map = {
            "sector": ["Technology", "Energy", "Healthcare", "Financial Services", "Consumer Cyclical",
                    "Communication Services", "Industrials", "Basic Materials", "Real Estate", "Utilities"],
            "industry": ["Software", "Oil & Gas", "Biotechnology", "Banks", "Retail", "Semiconductors"],
            "country": ["US", "Canada", "Germany", "UK", "France", "India", "Japan", "China"],
            "exchange": ["NASDAQ", "NYSE", "AMEX"],
            "isEtf": ["true", "false"],
            "isFund": ["true", "false"],
            "isActivelyTrading": ["true", "false"],
            "includeAllShareClasses": ["true", "false"],
            "marketStage": ["Rule of 40: Growth + Margin >= 40%"],
            "yoyGrowth": ["Annual", "Quarterly"],
            "profitMargin": ["Annual", "Quarterly"],
            "rdRatio": ["Annual", "Quarterly"],
            "companyAge": None,
            "ruleOf40": ["≥ 40"],
            "mvpStage": ["Pre-product", "Early Product", "Scaling"]

        }

        frame = tk.Frame(parent, bg="white", relief='solid', bd=1, width=300, height=80)  # Container for filter preview blocks
        frame.pack_propagate(False)

        title_row = tk.Frame(frame, bg="white")
        title_row.pack(fill="x", pady=(5, 0), padx=8)
        tk.Label(title_row, text=label, font=("Arial", 10, "bold"), bg="white").pack(side="left")

        if base_key in options_map:
            dropdown_row = tk.Frame(frame, bg="white")
            dropdown_row.pack(fill="x", padx=10, pady=(5, 10))
            options = options_map[base_key]
            if options is None:
                entry = tk.Entry(dropdown_row, font=("Arial", 10), state="disabled")
                entry.insert(0, "")
                entry.pack(side="left", fill="x", expand=True)
            else:
                combo = ttk.Combobox(dropdown_row, values=options, font=("Arial", 10), state="disabled")
                combo.set('')
                combo.pack(side="left", fill="x", expand=True)

        elif any(term in base_key.lower() for term in ["price", "marketcap", "volume", "beta", "dividend", "limit"]):
            slider_row = tk.Frame(frame, bg="white")
            slider_row.pack(fill="x", padx=10, pady=(2, 10))
            val_entry = tk.Entry(slider_row, width=6, justify="center", relief="groove", font=("Arial", 10), state="disabled")
            val_entry.insert(0, "")
            val_entry.pack(side="left", padx=(0, 10))

            slider = tk.Scale(slider_row, from_=0, to=1000, orient="horizontal", resolution=1, length=200, state="disabled")
            slider.set(0)
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

    def _create_filter_block(self, canvas, order_list, label, value=None):

        base_key = self.get_param_key_from_label(label)

        # Assign a unique key within this container/workspace
        count = sum(1 for _, f in order_list if f._param_key.startswith(base_key))
        key = f"{base_key}_{count+1}" if count else base_key

        options_map = {
            "sector": ["Technology", "Energy", "Healthcare", "Financial Services", "Consumer Cyclical",
                    "Communication Services", "Industrials", "Basic Materials", "Real Estate", "Utilities"],
            "industry": ["Software", "Oil & Gas", "Biotechnology", "Banks", "Retail", "Semiconductors"],
            "country": ["US", "Canada", "Germany", "UK", "France", "India", "Japan", "China"],
            "exchange": ["NASDAQ", "NYSE", "AMEX"],
            "isEtf": ["true", "false"],
            "isFund": ["true", "false"],
            "isActivelyTrading": ["true", "false"],
            "includeAllShareClasses": ["true", "false"],
            "marketStage": ["Rule of 40: Growth + Margin >= 40%"],
            "yoyGrowth": ["Annual", "Quarterly"],
            "profitMargin": ["Annual", "Quarterly"],
            "rdRatio": ["Annual", "Quarterly"],
            "companyAge": None,
            "ruleOf40": ["≥ 40"],
            "mvpStage": ["Pre-product", "Early Product", "Scaling"]
        }

        block_frame = tk.Frame(canvas, bg="white", relief='solid', bd=1, width=300, height=80)
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

        if base_key in options_map:
            dropdown_row = tk.Frame(block_frame, bg="white")
            dropdown_row.pack(fill="x", padx=10, pady=(5, 10))

            opts = options_map[base_key]
            if opts is None:
                entry = tk.Entry(dropdown_row, font=("Arial", 10))
                entry.pack(side="left", fill="x", expand=True)
                if value is not None:
                    entry.insert(0, str(value))
                    self.params[key] = value

                def on_return(event):
                    try:
                        self.params[key] = int(entry.get())
                    except ValueError:
                        self.params.pop(key, None)
                    self.delayed_search()

                entry.bind("<Return>", on_return)
            else:
                combo = ttk.Combobox(dropdown_row, values=opts, font=("Arial", 10), state="readonly")
                combo.set(value if value is not None else "")
                combo.pack(side="left", fill="x", expand=True)

                def update_selection(event):
                    selected = combo.get()
                    if selected:
                        self.params[key] = selected
                    else:
                        self.params.pop(key, None)
                    self.delayed_search()  # use this instead of update_display()

                combo.bind("<<ComboboxSelected>>", update_selection)
                if value is not None:
                    self.params[key] = value

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

        elif any(term in base_key.lower() for term in ["price", "marketcap", "volume", "beta", "dividend", "limit"]):
            slider_row = tk.Frame(block_frame, bg="white")
            slider_row.pack(fill="x", padx=10, pady=(2, 10))

            val_var = tk.StringVar(value="")

            val_entry = tk.Entry(slider_row, textvariable=val_var, width=6, justify="center", relief="groove", font=("Arial", 10))
            val_entry.pack(side="left", padx=(0, 10))

            if 'price' in key.lower():
                from_, to_, resolution = 0, 1000, 1
            elif 'marketcap' in key.lower():
                from_, to_, resolution = 0, 1_000_000_000_000, 1_000_000
            elif 'beta' in key.lower():
                from_, to_, resolution = -2, 5, 0.1
            elif 'volume' in key.lower():
                from_, to_, resolution = 0, 1_000_000, 10_000
            elif 'dividend' in key.lower():
                from_, to_, resolution = 0, 20, 0.1
            elif 'limit' in key.lower():
                from_, to_, resolution = 0, 100, 1
            else:
                from_, to_, resolution = 0, 200, 1

            slider = tk.Scale(slider_row, from_=from_, to=to_, orient="horizontal",
                            resolution=resolution, length=200)
            slider.pack(side="left", fill="x", expand=True)

            def on_slider_move(val):
                val_var.set(f"{float(val):.2f}")

            def on_slider_release(event):
                try:
                    val = float(slider.get())
                    if key not in self.params or self.params[key] != val:
                        self.params[key] = val
                        self.update_display()
                except ValueError:
                    self.params.pop(key, None)

            def on_entry_return(event):
                try:
                    val = float(val_var.get())
                    slider.set(val)
                    self.params[key] = val
                    self.update_display()
                except ValueError:
                    self.params.pop(key, None)

            slider.config(command=on_slider_move)
            slider.bind("<ButtonRelease-1>", on_slider_release)
            val_entry.bind("<Return>", on_entry_return)
            if value is not None:
                slider.set(value)
                val_var.set(f"{float(value):.2f}")
                self.params[key] = value

        # Add to snap zone
        item_id = canvas.create_window(10, 30 + len(order_list) * 90, anchor='nw', window=block_frame)
        order_list.append((item_id, block_frame))
        return block_frame

    def add_filter_block(self, label, value=None, container=None):
        if container is None:
            frame = self._create_filter_block(self.snap_zone, self.snap_order, label, value)
            self.snap_zone_placeholder.place_forget()
            self.reposition_snap_zone()
        else:
            frame = container.add_filter_block(label, value)
        return frame

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


    def remove_filter_block(self, frame, key, container=None):
        frame.destroy()

        if key in self.params:
            del self.params[key]

        if container is None:
            self.snap_order = [(item_id, f) for item_id, f in self.snap_order if f != frame]
            if not self.snap_order:
                self.snap_zone_placeholder.place(relx=0.5, rely=0.5, anchor="center")
            self.reposition_snap_zone()
        else:
            container.snap_order = [(item_id, f) for item_id, f in container.snap_order if f != frame]
            container.reposition()

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
            self.saved_algorithms[name] = dict(self.params)
            self._add_algorithm_preview(name)
            top.destroy()

        tk.Button(top, text="Save", command=submit).pack(pady=10)

    def _add_algorithm_preview(self, name):
        frame = tk.Frame(self.algo_container, bg="white", relief="solid", bd=1, width=300, height=50)
        frame.pack_propagate(False)
        tk.Label(frame, text=name, font=("Arial", 10, "bold"), bg="white").pack(fill="both", expand=True)

        frame._param_label = name
        DraggableBlock(master=self.left_frame, preview_block=frame, app=self, drop_target=self.block_area)
        frame.pack(pady=4)

    def load_algorithm(self, name):
        params = self.saved_algorithms.get(name)
        if not params:
            return

        # Clear existing workspace
        for _, frame in self.snap_order:
            frame.destroy()
        self.snap_order.clear()
        for c in list(self.containers):
            c.destroy()
        self.containers.clear()
        self.params.clear()

        for key, value in params.items():
            label = self.get_label_from_param_key(key)
            self.add_filter_block(label, value)

        self.reposition_snap_zone()
        self.update_display()

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
            self.saved_algorithms[name] = dict(self.params)
            self._add_algorithm_preview(name)
            top.destroy()

        tk.Button(top, text="Save", command=submit).pack(pady=10)

    def _add_algorithm_preview(self, name):
        frame = tk.Frame(self.algo_container, bg="white", relief="solid", bd=1, width=300, height=50)
        frame.pack_propagate(False)
        tk.Label(frame, text=name, font=("Arial", 10, "bold"), bg="white").pack(fill="both", expand=True)

        frame._param_label = name
        DraggableBlock(master=self.left_frame, preview_block=frame, app=self, drop_target=self.block_area)
        frame.pack(pady=4)

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

    def open_parameter(self, key, value_type):
        def submit_value():
            try:
                val = value_type(entry.get())
                self.params[key] = val
                self.add_filter_block(self.get_label_from_param_key(key), val)
                self.update_display()
            except Exception:
                pass
            top.destroy()

        top = Toplevel(self.root)
        top.title(f"Enter {key}")
        top.geometry("300x100")
        tk.Label(top, text=f"Enter a value for {key}:").pack(pady=5)

        entry = tk.Entry(top)
        entry.pack(pady=5, padx=10, fill="x")
        entry.focus()

        tk.Button(top, text="OK", command=submit_value).pack(pady=5)

    # Remove usage of simpledialog in set_parameter()
    def set_parameter(self, key: str, value_type: type):
        default_value = 100.0 if value_type == float else 100
        self.params[key] = default_value
        self.add_filter_block(key)
        self.update_display()
        self.delayed_search()

    def update_display(self):
        self.search_stocks()
        
    def delayed_search(self, delay_ms=10):  # intentionally delay search to speed up snapping mechanism for the search blocks
        if hasattr(self, '_search_delay_id'):
            self.root.after_cancel(self._search_delay_id)
        self._search_delay_id = self.root.after(delay_ms, self.search_stocks)

    def search_stocks(self):
        if "stockSearch" in self.params:
            symbol_fragment = self.params["stockSearch"]
            if len(symbol_fragment) < 1:
                return
            url = f"https://financialmodelingprep.com/api/v3/search?query={symbol_fragment}&limit=10&exchange=NASDAQ&apikey={self.api_key}"
        else:
            url = self.base_url + '&'.join(
                f"{key}={str(val).lower() if isinstance(val, bool) else val}"
                for key, val in self.params.items() if val not in ["", None]
            )

            url += f"&apikey={self.api_key}"
            if "limit" not in self.params:
                url += "&limit=20"

        #if "limit" not in self.params:
            #url += "&limit=20"

        try:
            response = requests.get(url)
            data = response.json()

            if any("marketStage" in k for k in self.params):
                base_screen_url = self.base_url + '&'.join(
                    f"{key}={str(val).lower() if isinstance(val, bool) else val}"
                    for key, val in self.params.items()
                    if key != "marketStage" and val not in ["", None]
                )
                base_screen_url += f"&apikey={self.api_key}&limit=100"

                try:
                    response = requests.get(base_screen_url)
                    screener_data = response.json()

                    matching_stocks = []
                    import concurrent.futures

                    def fetch_income(symbol):
                        if symbol in self._income_cache:
                            return symbol, self._income_cache[symbol]

                        try:
                            url = (
                                f"https://financialmodelingprep.com/api/v3/income-statement/"
                                f"{symbol}?period=quarter&limit=6&apikey={self.api_key}"
                            )
                            data = requests.get(url, timeout=3).json()
                            self._income_cache[symbol] = data
                            return symbol, data
                        except Exception:
                            return symbol, []

                    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                        futures = [executor.submit(fetch_income, stock["symbol"]) for stock in screener_data]
                        income_results = {}
                        for future in concurrent.futures.as_completed(futures):
                            symbol, inc_data = future.result()
                            if inc_data:
                                income_results[symbol] = inc_data

                        for stock in screener_data:
                            symbol = stock["symbol"]
                            income_data = income_results.get(symbol, [])

                            if len(income_data) < 5:
                                continue

                            try:
                                q0, q1, q2, q3, q4 = income_data[:5]

                                rev0 = float(q0.get("revenue") or 0)
                                rev1 = float(q1.get("revenue") or 0)
                                rev2 = float(q2.get("revenue") or 0)
                                rev3 = float(q3.get("revenue") or 0)
                                rev4 = float(q4.get("revenue") or 0)

                                net0 = float(q0.get("netIncome") or 0)
                                net1 = float(q1.get("netIncome") or 0)

                                if any(v == 0 for v in [rev0, rev1, rev2, rev3, rev4]):
                                    continue

                                growth0 = (rev0 - rev1) / rev1 * 100
                                growth1 = (rev1 - rev2) / rev2 * 100
                                margin0 = (net0 / rev0) * 100
                                margin1 = (net1 / rev1) * 100

                                rule40_avg = ((growth0 + margin0) + (growth1 + margin1)) / 2

                                flat_prev1 = (rev2 - rev3) / rev3 * 100
                                flat_prev2 = (rev3 - rev4) / rev4 * 100

                                if (
                                    rule40_avg >= 40
                                    and abs(flat_prev1) <= 5
                                    and abs(flat_prev2) <= 5
                                ):
                                    matching_stocks.append(stock)
                                    if len(matching_stocks) >= 20:
                                        break

                            except Exception:
                                continue

                    screener_data = matching_stocks

                except Exception as e:
                    messagebox.showerror("Error", f"Failed Market Stage filter:\n{e}")
                    return

            else:
                screener_data = data

            if any(k in self.params for k in ["yoyGrowth", "profitMargin", "rdRatio", "companyAge", "ruleOf40", "mvpStage"]):

                def fetch_metrics(symbol):
                    inc = requests.get(
                        f"https://financialmodelingprep.com/api/v3/income-statement/{symbol}"
                        f"?period={'annual' if self.params.get('yoyGrowth')=='Annual' else 'quarter'}"
                        f"&limit=2&apikey={self.api_key}"
                    ).json()
                    profile = requests.get(
                        f"https://financialmodelingprep.com/api/v3/profile/{symbol}"
                        f"?apikey={self.api_key}"
                    ).json()[0]
                    return inc, profile

                matching = []
                for stock in screener_data:
                    sym = stock["symbol"]
                    inc_data, prof = fetch_metrics(sym)

                    rev0 = float(inc_data[0]["revenue"] or 0)
                    rev1 = float(inc_data[1]["revenue"] or 1)
                    yoy = (rev0 - rev1) / rev1 * 100

                    ni0 = float(inc_data[0]["netIncome"] or 0)
                    pm = ni0 / rev0 * 100 if rev0 else 0

                    rd0 = float(inc_data[0].get("rdExpenses") or 0)
                    rd_ratio = rd0 / rev0 * 100 if rev0 else 0

                    ipo = datetime.strptime(prof["ipoDate"], "%Y-%m-%d")
                    age = (datetime.today() - ipo).days / 365

                    rule40 = (yoy + pm) / 2 if "ruleOf40" in self.params else None

                    if "mvpStage" in self.params:
                        stage = self.params["mvpStage"]
                        if stage == "Pre-product" and age > 2:
                            continue
                        if stage == "Early Product" and not (age <= 2 and rev0 >= 1_000_000):
                            continue
                        if stage == "Scaling" and rev0 < 10_000_000:
                            continue

                    if "yoyGrowth" in self.params and isinstance(self.params["yoyGrowth"], (int, float)) and yoy < float(self.params["yoyGrowth"]):
                        continue
                    if "profitMargin" in self.params and isinstance(self.params["profitMargin"], (int, float)) and pm < float(self.params["profitMargin"]):
                        continue
                    if "rdRatio" in self.params and isinstance(self.params["rdRatio"], (int, float)) and rd_ratio < float(self.params["rdRatio"]):
                        continue
                    if "companyAge" in self.params and age > int(self.params["companyAge"]):
                        continue
                    if "ruleOf40" in self.params and rule40 is not None and rule40 < 40:
                        continue

                    matching.append(stock)
                    if len(matching) >= self.params.get("limit", 20):
                        break

                data = matching
            else:
                data = screener_data

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
            quote_url = f"{self.quote_url}{','.join(symbols)}?apikey={self.api_key}"
            quote_data = requests.get(quote_url).json()
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
        try:
            url = f"https://financialmodelingprep.com/api/v3/historical-chart/5min/{symbol}?apikey={self.api_key}"
            response = requests.get(url)
            data = response.json()

            print(f"[DEBUG] {symbol} returned {len(data)} entries")
            print("[DEBUG] Sample date:", data[0]["date"] if data else "No data")

            return [(datetime.strptime(item["date"], "%Y-%m-%d %H:%M:%S"), item["close"])
                    for item in reversed(data)]
        except Exception as e:
            print(f"[ERROR] Failed to fetch history for {symbol}: {e}")
            return []

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
                history = self.get_historical_prices(symbol)
                dropdown = ResultDropdown(frame, symbol=symbol, quote_data=quote_data, price_history=history)
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
    
    def remove_stock_tile(self, symbol):
        frame = self.result_tiles.pop(symbol, None)
        if frame:
            frame.destroy()
            self.results_canvas.yview_moveto(0)  # Scroll to top

class ResultDropdown(tk.Frame):
    def __init__(self, parent, symbol, quote_data, price_history=None, profile_data=None):
        super().__init__(parent, bg="#f5f5f5", height=100)
        self.symbol = symbol
        self.quote_data = quote_data
        self.price_history = price_history or []
        self.profile_data = profile_data or {}

        self.build_dropdown_content()

    def build_dropdown_content(self):
        if not self.price_history:
            tk.Label(self, text="No price history available.", bg="#f5f5f5", fg="gray").pack(pady=10)
            return

        try:
            import matplotlib.pyplot as plt

            times, prices = zip(*self.price_history)

            fig = Figure(figsize=(5.0, 3.0), dpi=100)
            ax = fig.add_subplot(111)
            ax.plot(times, prices, color='blue', linewidth=1.5, marker='o', markersize=2)

            # Remove surrounding box lines
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_linewidth(1)
            ax.spines['bottom'].set_linewidth(1)

            # Set hourly x-axis ticks starting at 9:30
            ax.xaxis.set_major_locator(mdates.MinuteLocator(byminute=[30], interval=1))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%I:%M %p'))  # 12-hour format
            ax.tick_params(axis='x', labelrotation=45, labelsize=6)
            ax.tick_params(axis='y', labelsize=6)
            ax.set_title(f"{self.symbol} Trend (Intraday)", fontsize=8)

            fig.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=self)
            canvas.draw()
            canvas.get_tk_widget().pack(side="left", padx=5, pady=5)

        except Exception as e:
            import traceback
            print("[ERROR] Failed to draw chart:")
            traceback.print_exc()  # This will print the real reason why it failed
            tk.Label(self, text=f"Error rendering graph:\n{e}", fg="red").pack()

if __name__ == "__main__":
    root = tk.Tk()
    app = StockScreenerApp(root)
    root.mainloop()
