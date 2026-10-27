"""Sidebar: API configuration, feature navigation and architecture overview."""
from __future__ import annotations

import os
from typing import Optional, Tuple

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from core.config import (
    APP_VERSION,
    CUSTOM_MODEL_OPTION,
    DEFAULT_MODEL,
    GEMINI_MODELS,
    PLATFORM_ID,
    TAB_ASSISTANT,
    TAB_CRACK,
    TAB_PLANNING,
    TAB_PPE,
)
from core.llm import LLMError
from core.settings import AppSettings
from ui import state
from ui.components import esc, render

ARCHITECTURE_MD = """
**Request pipeline**

1. **Ingest** – Streamlit uploader → Pillow (EXIF orientation, RGB, ≤ 1600 px, exposure & blur checks)
2. **Reason** – Gemini multimodal call with a domain system prompt (OSHA 1926, IS 456, BOCW, IS 13311)
3. **Contract** – JSON output → schema normaliser (enums, ranges, defaults) → versioned report
4. **Decide** – score ring, metric cards, severity pills, downloadable JSON
5. **Advise** – weather protocols + site-aware chatbot grounded in the latest reports

**Deterministic engines** – INR budgeting & valuation, material take-off, milestone tracker

**External services** – Gemini API · Open-Meteo (live weather, no key) · Pollinations Flux (renders)

**State** – `st.session_state` only, no database → 1-click Streamlit Cloud deploy
"""

NAV_ITEMS = [
    (TAB_PPE, "Epic 2", state.ppe_status),
    (TAB_CRACK, "Epic 2", state.crack_status),
    (TAB_PLANNING, "Epic 3", state.valuation_status),
    (TAB_ASSISTANT, "Epic 5", state.weather_status),
]


def _configured_api_key() -> Optional[str]:
    """Key from Streamlit secrets or the environment (for deployed instances)."""
    key = None
    try:
        key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
    except Exception:  # no secrets.toml present
        key = None
    key = key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    return key.strip() if isinstance(key, str) and key.strip() else None


def _fingerprint(settings: AppSettings) -> str:
    return f"{(settings.api_key or '')[-6:]}::{settings.model}"


def _test_connection(settings: AppSettings) -> None:
    try:
        reply = settings.client().generate_text("Reply with exactly: OK", temperature=0)
        outcome = ("ok", f"Connected to {settings.model} — model replied “{reply[:40]}”.")
    except LLMError as exc:
        outcome = ("error", str(exc))
    st.session_state["connection_test"] = (_fingerprint(settings),) + outcome


def render_sidebar() -> Tuple[AppSettings, DeltaGenerator]:
    with st.sidebar:
        render(
            '<div class="cip-brand"><div class="cip-brand-mark">🏗️</div><div>'
            '<div class="cip-brand-name">Construction Intelligence</div>'
            '<div class="cip-brand-sub">Multimodal AI decision support</div></div></div>'
        )

        st.markdown("**🔐 AI configuration**")
        configured = _configured_api_key()
        use_configured = False
        if configured:
            use_configured = st.toggle("Use key from app secrets", value=True, help="Set GEMINI_API_KEY in Streamlit secrets.")
        typed = st.text_input(
            "Google Gemini API key",
            type="password",
            key="api_key_input",
            placeholder="Paste your key (AIza…)",
            help="Held only in this browser session and never written to disk. Leave blank for demonstration mode.",
            disabled=use_configured,
        )
        api_key = configured if use_configured else (typed.strip() or None)

        choice = st.selectbox("Multimodal model", GEMINI_MODELS + [CUSTOM_MODEL_OPTION], key="model_choice")
        if choice == CUSTOM_MODEL_OPTION:
            model = st.text_input("Model ID", value=DEFAULT_MODEL, key="custom_model_id").strip() or DEFAULT_MODEL
        else:
            model = choice
        settings = AppSettings(api_key=api_key, model=model)

        if settings.live:
            st.success("Live AI mode is active.", icon="✅")
            if st.button("Test connection", icon=":material/network_check:", width="stretch"):
                with st.spinner("Contacting Gemini…"):
                    _test_connection(settings)
            outcome = st.session_state.get("connection_test")
            if outcome and outcome[0] == _fingerprint(settings):
                if outcome[1] == "ok":
                    st.caption(outcome[2])
                else:
                    st.error(outcome[2])
        else:
            st.info(
                "**Demonstration mode** — every feature works with labelled sample outputs. "
                "Get a free key at [Google AI Studio](https://aistudio.google.com/apikey).",
                icon="🧪",
            )

        st.divider()
        st.markdown("**🧭 Feature navigation**")
        nav_slot = st.container()

        st.divider()
        with st.expander("🏛️ Architecture overview"):
            st.markdown(ARCHITECTURE_MD)
        with st.expander("📋 Epic coverage"):
            st.markdown(
                "- **Epic 1** – Requirements & environment (`requirements.txt`, secrets)\n"
                "- **Epic 2** – PPE safety vision & crack diagnostics\n"
                "- **Epic 3** – Project planning & real-estate valuation\n"
                "- **Epic 4** – Multimodal AI & JSON data contracts\n"
                "- **Epic 5** – Site chatbot & weather advisory\n"
                "- **Epic 6** – Interface, tests (`pytest`), cloud deployment"
            )
        st.caption(f"v{APP_VERSION} · Platform ID {PLATFORM_ID}")
    return settings, nav_slot


def _go_to(tab_label: str) -> None:
    st.session_state[state.MAIN_TAB] = tab_label


def render_navigation(slot: DeltaGenerator) -> None:
    """Filled after the tabs run so status lines reflect this run's results."""
    active = st.session_state.get(state.MAIN_TAB, TAB_PPE)
    with slot:
        for label, epic, status_fn in NAV_ITEMS:
            st.button(
                label,
                key=f"nav::{label}",
                type="primary" if label == active else "secondary",
                width="stretch",
                on_click=_go_to,
                args=(label,),
            )
            render(f'<div class="cip-nav-status">{esc(epic)} · {esc(status_fn())}</div>')
