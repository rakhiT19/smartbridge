"""End-to-end smoke tests of the Streamlit UI in demonstration mode (no network, no API key)."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).resolve().parent.parent / "app.py")


@pytest.fixture
def app(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    at = AppTest.from_file(APP_PATH, default_timeout=60)
    at.run()
    assert not at.exception, at.exception
    return at


def _button(at, label_start):
    return next(b for b in at.button if b.label.startswith(label_start))


def test_initial_render(app):
    assert any("Demonstration mode" in str(i.value) for i in app.sidebar.info)
    assert not app.error


def test_demo_ppe_and_crack_flows(app):
    _button(app, "Run audit (demonstration sample)").click().run()
    assert not app.exception
    assert app.session_state["ppe_result"]["report"]["source"] == "demo"

    _button(app, "Run diagnostics (demonstration sample)").click().run()
    assert not app.exception
    assert app.session_state["crack_result"]["report"]["defect_type"] == "Settlement"
    assert not app.error


def test_valuation_reacts_to_inputs(app):
    first = app.session_state["valuation_result"]["cost"]["total_budget"]
    app.slider(key="val_completion").set_value(80).run()
    app.number_input(key="val_sqft").set_value(5000).run()
    result = app.session_state["valuation_result"]
    assert result["inputs"]["completion_pct"] == 80
    assert result["cost"]["total_budget"] > first
    assert not app.exception


def test_weather_and_demo_chat(app):
    _button(app, "🦺 Toolbox talk").click().run()
    assert not app.exception
    history = app.session_state["chat_history"]
    assert [turn["role"] for turn in history] == ["user", "assistant"]
    assert "toolbox" in history[1]["content"].lower()

    app.chat_input(key="assistant_input").set_value("What is the curing period?").run()
    assert "IS 456" in app.session_state["chat_history"][-1]["content"]
    assert not app.exception


def test_sidebar_navigation_switches_tab(app):
    _button(app, "📐 Planning").click().run()
    assert app.session_state["main_tab"] == "📐 Planning & Valuation"
    assert not app.exception
