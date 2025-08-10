import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from baseFramework import (
    StockScreenerApp,
    calculate_dividend_yield,
    calculate_intraday_change,
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
