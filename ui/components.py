"""Reusable HTML components. Every dynamic string is escaped before rendering."""
from __future__ import annotations

import html as _html
from typing import Iterable, List, Optional, Sequence, Tuple

import streamlit as st

from core.settings import AppSettings
from core.config import APP_NAME, APP_TAGLINE, PLATFORM_ID, PROJECT_LABEL

SEVERITY_TONE = {"Low": "good", "Medium": "warning", "High": "serious", "Critical": "critical"}
TONE_ICON = {"good": "✓", "warning": "!", "serious": "▲", "critical": "✕", "neutral": "–", "accent": "i"}
PPE_STATUS_TONE = {"Compliant": "good", "Partial": "warning", "Non-Compliant": "critical", "Not Visible": "neutral"}
OVERALL_STATUS_TONE = {
    "Compliant": "good",
    "Needs Attention": "warning",
    "Non-Compliant": "serious",
    "Critical Violation": "critical",
}
URGENCY_TONE = {"Routine": "good", "Planned": "warning", "Urgent": "serious", "Immediate": "critical"}
OPERATION_TONE = {"Go": "good", "Restricted": "warning", "Suspended": "critical"}
MILESTONE_TONE = {"Completed": "good", "In Progress": "accent", "Pending": "neutral"}


def esc(value: object) -> str:
    return _html.escape(str(value), quote=True)


def render(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


def score_tone(score: float) -> str:
    if score >= 85:
        return "good"
    if score >= 70:
        return "warning"
    if score >= 45:
        return "serious"
    return "critical"


def pill(label: str, tone: str) -> str:
    return f'<span class="cip-pill cip-tone-{tone}"><b>{TONE_ICON.get(tone, "•")}</b>{esc(label)}</span>'


def severity_pill(level: str) -> str:
    return pill(level, SEVERITY_TONE.get(level, "neutral"))


def metric_card(label: str, value: str, sub: str = "", tone: Optional[str] = None, unit: str = "") -> str:
    tone_class = f" cip-tone-{tone}" if tone else ""
    unit_html = f"<small>{esc(unit)}</small>" if unit else ""
    sub_html = f'<div class="cip-metric-sub">{esc(sub)}</div>' if sub else ""
    return (
        f'<div class="cip-card cip-metric{tone_class}"><div class="cip-metric-label">{esc(label)}</div>'
        f'<div class="cip-metric-value">{esc(value)}{unit_html}</div>{sub_html}</div>'
    )


def kpi_row(cards: Iterable[str], min_width: int = 170) -> None:
    """Responsive tile grid; raise `min_width` to force an even 2×2 in narrow columns."""
    render(
        f'<div class="cip-kpi-row" style="grid-template-columns:repeat(auto-fit,minmax(min(100%,{min_width}px),1fr))">'
        f'{"".join(cards)}</div>'
    )


def score_ring(score: int, caption: str, tone: str) -> str:
    return (
        f'<div class="cip-ring cip-tone-{tone}" style="--pct:{max(0, min(100, int(score)))}" '
        f'role="img" aria-label="{esc(caption)}: {int(score)} out of 100">'
        f'<div class="cip-ring-inner"><div class="cip-ring-value">{int(score)}</div>'
        f'<div class="cip-ring-cap">{esc(caption)}</div></div></div>'
    )


def meter(pct: float, tone: str = "accent", label: str = "", value_text: str = "") -> str:
    width = max(0.0, min(100.0, pct))
    head = (
        f'<div class="cip-meter-row"><span>{esc(label)}</span><span>{esc(value_text)}</span></div>'
        if label or value_text
        else ""
    )
    return (
        f'<div class="cip-meter-block">{head}<div class="cip-meter cip-tone-{tone}" role="progressbar" '
        f'aria-valuenow="{width:.0f}" aria-valuemin="0" aria-valuemax="100"><span style="width:{width:.1f}%"></span></div></div>'
    )


def section(title: str, subtitle: str = "") -> None:
    sub = f'<div class="cip-section-sub">{esc(subtitle)}</div>' if subtitle else ""
    render(f'<div class="cip-section"><div class="cip-section-title">{esc(title)}</div>{sub}</div>')


def alert(title: str, body: str, tone: str, icon: str = "⚠️") -> None:
    render(
        f'<div class="cip-alert cip-tone-{tone}"><div class="cip-alert-icon">{esc(icon)}</div>'
        f'<div><div class="cip-alert-title">{esc(title)}</div><div class="cip-alert-body">{esc(body)}</div></div></div>'
    )


def bullets(items: Sequence[str]) -> str:
    return '<ul class="cip-bullets">' + "".join(f"<li>{esc(item)}</li>" for item in items) + "</ul>"


def card(inner_html: str, extra_class: str = "") -> str:
    return f'<div class="cip-card {extra_class}">{inner_html}</div>'


def empty_state(icon: str, title: str, body: str) -> None:
    render(
        card(
            f'<div class="cip-empty"><div class="cip-empty-icon">{esc(icon)}</div>'
            f'<div class="cip-empty-title">{esc(title)}</div><div class="cip-empty-body">{esc(body)}</div></div>'
        )
    )


def stacked_bar(segments: List[Tuple[str, float, str]], formatter) -> str:
    """Single part-to-whole bar with a legend that carries every value (no colour-only identity)."""
    total = sum(value for _, value, _ in segments) or 1.0
    bars = "".join(
        f'<span style="width:{value / total * 100:.2f}%;background:{color}" '
        f'title="{esc(label)}: {esc(formatter(value))} ({value / total * 100:.1f}%)"></span>'
        for label, value, color in segments
    )
    legend = "".join(
        f'<span><i style="background:{color}"></i>{esc(label)} <em>{esc(formatter(value))} · {value / total * 100:.1f}%</em></span>'
        for label, value, color in segments
    )
    return f'<div class="cip-stack" role="img" aria-label="Budget composition">{bars}</div><div class="cip-legend">{legend}</div>'


def hero(settings: AppSettings) -> None:
    tone = "good" if settings.live else "warning"
    render(
        f'<div class="cip-hero"><div class="cip-eyebrow">{esc(PROJECT_LABEL)}</div>'
        f'<div class="cip-hero-title">{esc(APP_NAME)}</div><div class="cip-hero-sub">{esc(APP_TAGLINE)}</div>'
        f'<div class="cip-hero-chips"><span class="cip-chip cip-tone-{tone}"><i></i>{esc(settings.mode_label)}</span>'
        f'<span class="cip-chip">Platform ID · {esc(PLATFORM_ID)}</span>'
        f'<span class="cip-chip">OSHA 1926 · IS 456 · BOCW</span></div></div>'
    )


def source_banner(source: str, error: Optional[str] = None) -> None:
    """Explain where a report came from: live AI, demo sample, or fallback after an error."""
    if source == "demo":
        alert(
            "Demonstration sample report",
            "No Gemini API key is configured, so this is a representative sample — it does not describe your photo. "
            "Add a key in the sidebar for live multimodal analysis.",
            "warning",
            "🧪",
        )
    elif source == "fallback":
        alert(
            "Live analysis failed — showing the demonstration sample",
            error or "The AI service could not complete the request.",
            "serious",
            "⚠️",
        )
