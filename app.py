"""Multimodal Construction Intelligence Platform — Streamlit entry point.

Run locally:  streamlit run app.py
"""
from __future__ import annotations

import logging
from typing import Callable

import streamlit as st

st.set_page_config(
    page_title="Construction Intelligence Platform",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "Multimodal Construction Intelligence Platform — Skill Wallet Capstone Project 1"},
)

from core.config import PLATFORM_ID, TAB_LABELS  # noqa: E402  (set_page_config must run first)
from core.settings import AppSettings  # noqa: E402
from ui import assistant_view, crack_view, planning_view, ppe_view, state  # noqa: E402
from ui.components import hero  # noqa: E402
from ui.sidebar import render_navigation, render_sidebar  # noqa: E402
from ui.styles import inject_css  # noqa: E402

logger = logging.getLogger("construction_intelligence")


def _guarded(render_fn: Callable[[AppSettings], None], settings: AppSettings, name: str) -> None:
    """Isolate each module so an unexpected error never takes down the whole app."""
    try:
        render_fn(settings)
    except Exception as exc:  # Streamlit's rerun/stop signals are BaseException and pass through
        logger.exception("Unhandled error in %s", name)
        st.error(f"The {name} module hit an unexpected error: {exc}", icon="🚧")
        with st.expander("Technical details"):
            st.exception(exc)


def main() -> None:
    inject_css()
    state.init_state()
    settings, nav_slot = render_sidebar()
    hero(settings)

    ppe_tab, crack_tab, planning_tab, assistant_tab = st.tabs(TAB_LABELS, key=state.MAIN_TAB, on_change="rerun")
    with ppe_tab:
        _guarded(ppe_view.render_tab, settings, "PPE audit")
    with crack_tab:
        _guarded(crack_view.render_tab, settings, "crack diagnostics")
    with planning_tab:
        _guarded(planning_view.render_tab, settings, "planning & valuation")
    with assistant_tab:
        _guarded(assistant_view.render_tab, settings, "site assistant")

    render_navigation(nav_slot)
    st.caption(
        f"Platform ID {PLATFORM_ID} · AI outputs support, and never replace, the judgement of a qualified "
        "safety officer or structural engineer."
    )


main()
