"""Tab 4 — Daily Site Assistant & Weather-Aware Advisory (Epic 5)."""
from __future__ import annotations

from datetime import date
from typing import Any, Dict, List

import streamlit as st

from core.demo import demo_chat_reply
from core.llm import LLMError
from core.prompts import assistant_system
from core.settings import AppSettings
from core.weather import (
    CITY_COORDINATES,
    PROTOCOLS,
    WEATHER_CONDITIONS,
    WEATHER_ICONS,
    WeatherError,
    daily_protocol_markdown,
    fetch_live_weather,
)
from ui import state
from ui.components import OPERATION_TONE, SEVERITY_TONE, alert, bullets, card, esc, kpi_row, metric_card, pill, render, section

QUICK_PROMPTS = [
    ("🦺 Toolbox talk", "Prepare today's toolbox talk for my site."),
    ("🧪 Curing today", "What curing period should I follow for an M25 slab in today's weather?"),
    ("🪵 Formwork stripping", "When can I strip slab and beam formwork?"),
    ("🧱 Repair today's crack", "How should I repair the crack found in today's diagnosis?"),
]
MAX_HISTORY_TURNS = 20  # replayed to the model; older turns are dropped to bound cost


def _weather_controls() -> str:
    weather = st.session_state[state.WEATHER_STATE]
    source = st.radio(
        "Condition source",
        ["Manual selection", "Live weather (Open-Meteo)"],
        horizontal=True,
        key="weather_source",
    )
    if source == "Manual selection":
        condition = st.segmented_control(
            "Today's site weather",
            WEATHER_CONDITIONS,
            default="Normal",
            required=True,
            format_func=lambda c: f"{WEATHER_ICONS[c]} {c}",
            key="weather_manual",
        )
        weather.update(condition=condition, source="manual", reading=None)
        return condition

    city_col, button_col = st.columns([2, 1], vertical_alignment="bottom")
    city = city_col.selectbox("Site city", list(CITY_COORDINATES), key="weather_city")
    if button_col.button("Fetch live weather", icon=":material/cloud_sync:", width="stretch"):
        try:
            with st.spinner(f"Fetching current conditions for {city}…"):
                weather["live_cache"] = fetch_live_weather(city)
        except WeatherError as exc:
            st.error(str(exc), icon="📡")
    reading = weather.get("live_cache")
    if not reading or reading["city"] != city:
        st.caption("Fetch live conditions to set the protocol automatically. Using **Normal** until then.")
        weather.update(condition="Normal", source="live", reading=None)
        return "Normal"

    kpi_row(
        [
            metric_card("Temperature", f"{reading['temperature_c']:.1f}", unit="°C", sub=f"feels like {reading['apparent_c']:.0f} °C"),
            metric_card("Wind", f"{reading['wind_kmh']:.0f}", unit="km/h", sub=f"gusts {reading['gust_kmh']:.0f} km/h"),
            metric_card("Precipitation", f"{reading['precipitation_mm']:.1f}", unit="mm", sub=reading["description"]),
            metric_card("Humidity", f"{reading['humidity_pct']:.0f}", unit="%", sub=f"observed {reading['observed_at'][-5:]} local"),
        ]
    )
    st.caption(f"Classified as **{reading['condition']}** — {reading['reason']}. Source: Open-Meteo.")
    weather.update(condition=reading["condition"], source="live", reading=reading)
    return reading["condition"]


def _render_protocol(condition: str) -> None:
    protocol = PROTOCOLS[condition]
    risk = protocol["risk"]
    alert(
        f"{condition} — {risk} risk day",
        protocol["headline"],
        SEVERITY_TONE.get(risk, "neutral"),
        WEATHER_ICONS[condition],
    )

    cells = []
    for operation, (status, note) in protocol["operations"].items():
        cells.append(
            card(
                f'<div class="cip-op-head"><span class="cip-op-name">{esc(operation)}</span>'
                f'{pill(status, OPERATION_TONE[status])}</div><div class="cip-op-note">{esc(note)}</div>'
            )
        )
    render(f'<div class="cip-ops">{"".join(cells)}</div>')

    section("Dynamic safety alerts")
    render(card(bullets(protocol["alerts"]), f"cip-hazard cip-tone-{SEVERITY_TONE.get(risk, 'neutral')}"))

    section("Daily site protocol")
    columns = st.columns(len(protocol["protocols"]), gap="medium")
    for column, (heading, items) in zip(columns, protocol["protocols"].items()):
        with column:
            render(card(f'<div class="cip-metric-label">{esc(heading)}</div>{bullets(items)}'))

    st.download_button(
        "Download today's protocol (Markdown checklist)",
        data=daily_protocol_markdown(condition, state.open_findings()),
        file_name=f"daily_site_protocol_{date.today():%Y%m%d}.md",
        mime="text/markdown",
        icon=":material/checklist:",
        key="protocol_download",
    )


def _assistant_reply(settings: AppSettings, history: List[Dict[str, str]], context: Dict[str, Any]) -> str:
    if not settings.live:
        return demo_chat_reply(history[-1]["content"], context)
    try:
        return settings.client().chat(history[-MAX_HISTORY_TURNS:], assistant_system(context))
    except LLMError as exc:
        return f"⚠️ {exc}\n\n---\n_Offline answer from the built-in knowledge base:_\n\n" + demo_chat_reply(
            history[-1]["content"], context
        )


def _render_chat(settings: AppSettings) -> None:
    history: List[Dict[str, str]] = st.session_state[state.CHAT_HISTORY]
    mode = "Gemini, grounded in your latest audits, valuation and weather" if settings.live else "Demo knowledge base"
    section("Construction engineering assistant", f"Multi-turn chat · {mode}")

    pending = None
    quick_cols = st.columns(len(QUICK_PROMPTS))
    for index, (column, (label, text)) in enumerate(zip(quick_cols, QUICK_PROMPTS)):
        if column.button(label, key=f"quick_prompt_{index}", width="stretch", help=text):
            pending = text

    messages = st.container(height=440, border=True)
    with messages:
        if not history:
            with st.chat_message("assistant", avatar="👷"):
                st.markdown(
                    "Namaste! I'm **SiteSense**, your site engineering assistant. Ask me about IS codes, concreting, "
                    "formwork, safety, quantities, or today's weather protocol."
                )
        for turn in history:
            with st.chat_message(turn["role"], avatar="👷" if turn["role"] == "assistant" else "🧑‍🔧"):
                st.markdown(turn["content"])

    typed = st.chat_input("Ask the site assistant…", key="assistant_input", max_chars=2000)
    prompt = typed if isinstance(typed, str) else pending
    if prompt and prompt.strip():
        history.append({"role": "user", "content": prompt.strip()})
        with messages:
            with st.chat_message("user", avatar="🧑‍🔧"):
                st.markdown(prompt.strip())
            with st.chat_message("assistant", avatar="👷"):
                with st.spinner("Thinking…"):
                    reply = _assistant_reply(settings, history, state.site_context())
                st.markdown(reply)
        history.append({"role": "assistant", "content": reply})

    if history and st.button("Clear conversation", icon=":material/delete_sweep:", key="clear_chat", type="tertiary"):
        st.session_state[state.CHAT_HISTORY] = []
        st.rerun()


def render_tab(settings: AppSettings) -> None:
    section("Weather-aware advisory", "Select today's condition or pull live weather to set the site protocol")
    condition = _weather_controls()
    _render_protocol(condition)
    st.divider()
    _render_chat(settings)
