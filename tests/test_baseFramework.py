import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from baseFramework import (
    StockScreenerApp,
    calculate_dividend_yield,
    calculate_intraday_change,
    DraggableBlock,
)
import pytest
from unittest.mock import MagicMock


def test_get_param_key_from_label():
    app = StockScreenerApp.__new__(StockScreenerApp)
    assert app.get_param_key_from_label("Lower Market Cap (10M-4T)") == "marketCapMoreThan"
    assert app.get_param_key_from_label("Sector") == "sector"
    assert app.get_param_key_from_label("Stock Search") == "stockSearch"
    assert app.get_param_key_from_label("Unknown") == "Unknown"
    assert app.get_param_key_from_label("Lower Dividend") == "dividendMoreThan"


def test_calculate_dividend_yield():
    # Yield supplied as a ratio should be converted to percentage
    assert calculate_dividend_yield(1.0, 0.02, 50) == pytest.approx(2.0)

    # When no yield supplied, derive from dividend and price
    assert calculate_dividend_yield(2.0, 0, 50) == pytest.approx(4.0)

    # Yield already given as percentage should remain unchanged
    assert calculate_dividend_yield(1.0, 5, 50) == pytest.approx(5.0)


def test_calculate_intraday_change():
    change, pct = calculate_intraday_change(105, 100)
    assert change == pytest.approx(5.0)
    assert pct == pytest.approx(5.0)

    change, pct = calculate_intraday_change(95, 100)
    assert change == pytest.approx(-5.0)
    assert pct == pytest.approx(-5.0)


def test_save_and_delete_algorithm_clears_workspace():
    app = StockScreenerApp.__new__(StockScreenerApp)
    app.saved_algorithms = {}
    app.algorithm_previews = {}
    app.params = {"a": 1}
    app.snap_order = []
    app.current_algorithm = "Test"


    added = []
    destroyed = []

    class DummyFrame:
        def __init__(self, n):
            self.n = n

        def pack_forget(self):
            pass

        def destroy(self):
            destroyed.append(self.n)

    class DummyPlaceholder:
        def __init__(self):
            self.placed = False

        def place(self, **kwargs):
            self.placed = True

    def stub_add(name):
        added.append(name)
        app.algorithm_previews[name] = DummyFrame(name)

    app._add_algorithm_preview = stub_add

    app.save_algorithm("Test")
    assert app.saved_algorithms["Test"] == {"a": 1}
    assert added == ["Test"]
    assert app.current_algorithm == "Test"

    app.params = {"a": 2}
    app.update_current_algorithm("Test")
    assert app.saved_algorithms["Test"] == {"a": 2}
    assert added == ["Test"]  # no duplicate preview added

    app.snap_order = [(1, DummyFrame("block"))]
    app.snap_zone_placeholder = DummyPlaceholder()
    app.reposition_snap_zone = lambda: None
    app.update_display = lambda: None

    app.delete_algorithm("Test")
    assert "Test" not in app.saved_algorithms
    assert "Test" not in app.algorithm_previews
    assert destroyed == ["Test", "block"]
    assert app.snap_order == []
    assert app.params == {}
    assert app.snap_zone_placeholder.placed
    assert app.current_algorithm is None


def test_open_save_algorithm_dialog_enter(monkeypatch):
    app = StockScreenerApp.__new__(StockScreenerApp)
    app.root = MagicMock()
    app.params = {"a": 1}

    saved = {}
    app.save_algorithm = lambda name: saved.setdefault("name", name)

    destroyed = []

    class DummyTop:
        def __init__(self, root):
            self.root = root

        def title(self, *args, **kwargs):
            pass

        def geometry(self, *args, **kwargs):
            pass

        def destroy(self):
            destroyed.append(True)

    top = DummyTop(app.root)
    monkeypatch.setattr("baseFramework.Toplevel", lambda root: top)

    class DummyLabel:
        def __init__(self, parent, text):
            pass

        def pack(self, **kwargs):
            pass

    monkeypatch.setattr("baseFramework.tk.Label", DummyLabel)

    class DummyEntry:
        def __init__(self, parent):
            self.bindings = {}

        def pack(self, **kwargs):
            pass

        def focus(self):
            pass

        def get(self):
            return "Algo"

        def bind(self, sequence, func):
            self.bindings[sequence] = func

    entry = DummyEntry(top)
    monkeypatch.setattr("baseFramework.tk.Entry", lambda parent: entry)

    class DummyButton:
        def __init__(self, parent, text, command):
            self.command = command

        def pack(self, **kwargs):
            pass

    monkeypatch.setattr("baseFramework.tk.Button", DummyButton)

    app.open_save_algorithm_dialog()

    assert "<Return>" in entry.bindings
    # simulate pressing Enter
    entry.bindings["<Return>"](None)
    assert saved["name"] == "Algo"
    assert destroyed == [True]


def test_update_algorithm_rename_replaces_old():
    app = StockScreenerApp.__new__(StockScreenerApp)
    app.saved_algorithms = {"Old": {"a": 1}}
    destroyed = []

    class DummyFrame:
        def pack_forget(self):
            destroyed.append("forget")

        def destroy(self):
            destroyed.append("destroy")

    app.algorithm_previews = {"Old": DummyFrame()}

    added = []

    def stub_add(name):
        added.append(name)
        app.algorithm_previews[name] = DummyFrame()

    app._add_algorithm_preview = stub_add

    app.params = {"a": 2}
    app.current_algorithm = "Old"

    app.update_current_algorithm("New")

    assert "Old" not in app.saved_algorithms
    assert "Old" not in app.algorithm_previews
    assert app.saved_algorithms["New"] == {"a": 2}
    assert added == ["New"]
    assert destroyed == ["forget", "destroy"]


def test_format_algorithm_summary_shows_only_labels():
    app = StockScreenerApp.__new__(StockScreenerApp)
    params = {
        "sector": "Basic Materials",
        "marketCapMoreThan": 1234,
        "industry": "Chemicals",
    }
    summary = app._format_algorithm_summary(params)
    assert summary == "Sector || Lower Market Cap (10M-4T) || Industry"
    assert "Basic Materials" not in summary
    assert "1234" not in summary


def test_drag_clone_preserves_algorithm_preview(monkeypatch):
    """Dragging a saved algorithm should clone its preview unchanged."""
    from types import SimpleNamespace

    # Minimal dummy tk module to avoid initializing a real Tk instance
    class DummyFrame:
        def __init__(self, master=None, **kwargs):
            self.master = master
            self.children = []
            if master and hasattr(master, "children"):
                master.children.append(self)
            self.kwargs = kwargs

        def pack(self, **kwargs):
            pass

        def pack_propagate(self, flag):
            pass

        def winfo_children(self):
            return self.children

        def cget(self, option):
            return self.kwargs.get(option)

    class DummyLabel(DummyFrame):
        pass

    dummy_tk = SimpleNamespace(Frame=DummyFrame, Label=DummyLabel)
    monkeypatch.setattr("baseFramework.tk", dummy_tk)

    # Prepare a preview block that mimics a saved algorithm preview
    summary = DummyLabel(text="Block1 || Block2 || Block3")
    preview = SimpleNamespace(_param_label="Algo", _summary_label=summary)

    app = SimpleNamespace(get_param_key_from_label=lambda x: x)

    block = DraggableBlock.__new__(DraggableBlock)
    block.preview_block = preview
    block.app = app
    block._drag_window = DummyFrame()

    clone = block.clone_preview_block()

    # First child is the title row containing the name label
    title_row = clone.children[0]
    assert title_row.children[0].cget("text") == "Algo"

    # Second child is the summary label with first three block names
    assert clone.children[1].cget("text") == "Block1 || Block2 || Block3"


def test_remove_filter_block_delays_results_not_removal():
    """Removing a filter block should delete immediately but delay results."""
    app = StockScreenerApp.__new__(StockScreenerApp)

    destroyed = []

    class DummyFrame:
        def destroy(self):
            destroyed.append(True)

    frame = DummyFrame()
    app.params = {"k": 1}
    app.snap_order = [(1, frame)]
    app.snap_zone_placeholder = MagicMock()
    app.reposition_snap_zone = MagicMock()
    app.delayed_search = MagicMock()

    app.remove_filter_block(frame, "k")

    # Removal happens immediately
    assert destroyed == [True]
    assert app.snap_order == []
    assert "k" not in app.params

    # Search results are scheduled with a 0.5 second delay
    app.delayed_search.assert_called_once_with(delay_ms=500)


def test_dropdown_filter_block_adds_without_error(monkeypatch):
    app = StockScreenerApp.__new__(StockScreenerApp)
    app.params = {}
    app.snap_order = []
    app.delayed_search = lambda *a, **k: None
    app.reposition_snap_zone = lambda: None

    app.snap_zone = MagicMock()
    app.snap_zone.create_window.return_value = 1

    app.snap_zone_placeholder = MagicMock()

    class DummyStringVar:
        def __init__(self, value=""):
            self.value = value

        def get(self):
            return self.value

        def set(self, v):
            self.value = v

    monkeypatch.setattr("baseFramework.tk.StringVar", DummyStringVar)
    monkeypatch.setattr("baseFramework.tk.Frame", lambda *a, **k: MagicMock())
    monkeypatch.setattr("baseFramework.tk.Label", lambda *a, **k: MagicMock())
    monkeypatch.setattr("baseFramework.tk.Button", lambda *a, **k: MagicMock())

    class DummyCombobox:
        def __init__(self, *a, **k):
            self.bindings = {}

        def pack(self, *a, **k):
            pass

        def bind(self, seq, func):
            self.bindings[seq] = func

    monkeypatch.setattr("baseFramework.ttk.Combobox", DummyCombobox)
    monkeypatch.setattr("baseFramework.tk.Entry", lambda *a, **k: MagicMock())
    monkeypatch.setattr("baseFramework.tk.Scale", lambda *a, **k: MagicMock())

    app.add_filter_block("Sector")

    # Block should be added to the snap order without raising errors
    assert len(app.snap_order) == 1
