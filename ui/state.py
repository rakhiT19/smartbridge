"""Session-state keys and cross-module summaries (no database: everything lives in st.session_state)."""
from __future__ import annotations

from datetime import date
from typing import Any, Dict

import streamlit as st

from core.formatting import format_inr

PPE_RESULT = "ppe_result"
CRACK_RESULT = "crack_result"
VALUATION_RESULT = "valuation_result"
WEATHER_STATE = "weather_state"
CHAT_HISTORY = "chat_history"
RENDER_RESULT = "render_result"
MAIN_TAB = "main_tab"


def init_state() -> None:
    st.session_state.setdefault(CHAT_HISTORY, [])
    st.session_state.setdefault(WEATHER_STATE, {"condition": "Normal", "source": "manual", "reading": None})


def _sample_note(report: Dict[str, Any]) -> str:
    return "" if report.get("source") == "live" else " (sample)"


def ppe_status() -> str:
    result = st.session_state.get(PPE_RESULT)
    if not result:
        return "Not run yet"
    report = result["report"]
    return f"Score {report['safety_score']}/100 · {report['overall_status']}{_sample_note(report)}"


def crack_status() -> str:
    result = st.session_state.get(CRACK_RESULT)
    if not result:
        return "Not run yet"
    report = result["report"]
    return f"{report['defect_type']} · {report['severity']} severity{_sample_note(report)}"


def valuation_status() -> str:
    result = st.session_state.get(VALUATION_RESULT)
    if not result:
        return "Awaiting inputs"
    return f"Budget {format_inr(result['cost']['total_budget'])} · Value {format_inr(result['valuation']['current_valuation'])}"


def weather_status() -> str:
    weather = st.session_state.get(WEATHER_STATE) or {}
    turns = sum(1 for turn in st.session_state.get(CHAT_HISTORY, []) if turn["role"] == "user")
    return f"{weather.get('condition', 'Normal')} protocol · {turns} chat question{'s' if turns != 1 else ''}"


def site_context() -> Dict[str, Any]:
    """Compact snapshot of every module's latest output, used to ground the assistant."""
    context: Dict[str, Any] = {"date": date.today().isoformat()}

    weather = st.session_state.get(WEATHER_STATE) or {}
    context["weather"] = {"condition": weather.get("condition", "Normal"), "source": weather.get("source", "manual")}
    if weather.get("reading"):
        reading = weather["reading"]
        context["weather"]["live_reading"] = {
            key: reading[key]
            for key in ("city", "temperature_c", "apparent_c", "wind_kmh", "gust_kmh", "precipitation_mm", "description")
        }

    ppe = st.session_state.get(PPE_RESULT)
    if ppe:
        report = ppe["report"]
        context["latest_ppe_audit"] = {
            "is_sample_data": report["source"] != "live",
            "safety_score": report["safety_score"],
            "overall_status": report["overall_status"],
            "workers_detected": report["workers_detected"],
            "ppe_gaps": [
                f"{item['label']}: {item['status']}"
                for item in report["ppe_detection"].values()
                if item["status"] in ("Partial", "Non-Compliant")
            ],
            "top_hazards": [f"{h['severity']}: {h['hazard']}" for h in report["hazards"][:5]],
        }

    crack = st.session_state.get(CRACK_RESULT)
    if crack:
        report = crack["report"]
        context["latest_crack_diagnosis"] = {
            "is_sample_data": report["source"] != "live",
            "defect_type": report["defect_type"],
            "severity": report["severity"],
            "estimated_width_mm": report["estimated_crack_width_mm"],
            "urgency": report["urgency"],
            "root_causes": report["root_causes"][:3],
        }

    valuation = st.session_state.get(VALUATION_RESULT)
    if valuation:
        inputs = valuation["inputs"]
        context["project"] = {
            "structure_type": inputs["structure_type"],
            "built_up_sqft": inputs["built_up_sqft"],
            "location_tier": inputs["tier"],
            "completion_pct": inputs["completion_pct"],
            "current_milestone": valuation["current_milestone"],
            "total_budget": format_inr(valuation["cost"]["total_budget"]),
            "capex_incurred": format_inr(valuation["cost"]["capex_incurred"]),
            "current_valuation": format_inr(valuation["valuation"]["current_valuation"]),
        }
    return context


def open_findings() -> Dict[str, str]:
    """One-line findings for the printable daily protocol."""
    findings: Dict[str, str] = {}
    ppe = st.session_state.get(PPE_RESULT)
    if ppe:
        report = ppe["report"]
        top = report["hazards"][0]["hazard"] if report["hazards"] else "no hazards listed"
        findings["PPE audit"] = f"{report['safety_score']}/100, {report['overall_status']} — top hazard: {top}{_sample_note(report)}"
    crack = st.session_state.get(CRACK_RESULT)
    if crack:
        report = crack["report"]
        findings["Structural"] = (
            f"{report['defect_type']} crack ≈ {report['estimated_crack_width_mm']} mm, "
            f"{report['severity']} severity, {report['urgency']}{_sample_note(report)}"
        )
    return findings
