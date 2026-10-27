"""Tab 2 — Crack Diagnostics & Structural Integrity (Epic 2)."""
from __future__ import annotations

import json
from typing import Any, Dict

import streamlit as st

from core.analysis import run_image_analysis
from core.config import ACCEPTED_IMAGE_TYPES, IS456_CRACK_LIMIT_MM, MAX_UPLOAD_MB, STRUCTURAL_ELEMENTS
from core.contracts import normalize_crack_report
from core.demo import SAMPLE_CRACK_REPORT
from core.imaging import quality_warnings
from core.prompts import CRACK_SYSTEM, crack_prompt
from core.settings import AppSettings
from ui import state
from ui.components import (
    SEVERITY_TONE,
    URGENCY_TONE,
    alert,
    bullets,
    card,
    empty_state,
    esc,
    kpi_row,
    metric_card,
    pill,
    render,
    score_ring,
    section,
    source_banner,
)
from ui.uploads import crack_map_for, load_upload, metrics_for

EXPOSURES = ["Interior (mild)", "Exterior (moderate)", "Wet / below ground (severe)", "Coastal (very severe)"]
GROWTH_OPTIONS = ["Unknown", "Yes — widening over time", "No — stable"]


def _render_summary(report: Dict[str, Any]) -> None:
    source_banner(report["source"], report.get("error"))
    if not report["is_concrete_surface"]:
        alert("This may not be a concrete or masonry surface", report["summary"], "warning", "🔍")

    severity = report["severity"]
    ring_col, text_col = st.columns([1, 1.9], gap="medium")
    with ring_col:
        render(
            card(
                score_ring(report["severity_score"], "Severity score", SEVERITY_TONE[severity])
                + f'<div style="text-align:center">{pill(severity + " severity", SEVERITY_TONE[severity])}</div>'
            )
        )
    with text_col:
        secondary = (
            f'<div class="cip-footnote">Also observed: {esc(", ".join(report["secondary_defects"]))}</div>'
            if report["secondary_defects"]
            else ""
        )
        model = f" · {report['model']}" if report.get("model") else ""
        render(
            card(
                f'<div class="cip-metric-label">Diagnosis</div>'
                f'<div class="cip-metric-value">{esc(report["defect_type"])}</div>'
                f'<div class="cip-hazard-meta">{esc(report["crack_pattern"])}</div>'
                f'<div class="cip-hazard-body">{esc(report["summary"])}</div>{secondary}'
                f'<div class="cip-footnote">Confidence {report["confidence"]:.0%}{esc(model)}</div>'
            )
        )

    low, high = report["width_range_mm"]
    within = report["within_is456_limit"]
    urgency = report["urgency"]
    kpi_row(
        [
            metric_card(
                "Est. crack width",
                f'{report["estimated_crack_width_mm"]:.2f}',
                unit="mm",
                sub=f"range {low:.2f}–{high:.2f} mm",
            ),
            metric_card(
                "IS 456 cl. 35.3.2",
                "Within limit" if within else "Exceeds limit",
                sub=f"surface crack width guidance ≤ {IS456_CRACK_LIMIT_MM} mm",
                tone="good" if within else "critical",
            ),
            metric_card("Urgency", urgency, sub=report["urgency_timeframe"], tone=URGENCY_TONE[urgency]),
        ]
    )
    if report["structural_risk"]:
        render(card(f'<div class="cip-metric-label">Structural risk</div><div class="cip-hazard-body" style="margin-top:.35rem">{esc(report["structural_risk"])}</div>'))


def _render_repairs(report: Dict[str, Any]) -> None:
    section("Recommended engineering repairs", "In priority order — confirm the crack is dormant before cosmetic sealing")
    if not report["recommended_repairs"]:
        render(card('<div class="cip-check-notes">No repair is required for this surface.</div>'))
        return
    steps = []
    for index, repair in enumerate(report["recommended_repairs"], start=1):
        materials = f'<div class="cip-step-mat">🧰 {esc(repair["materials"])}</div>' if repair["materials"] else ""
        steps.append(
            f'<div class="cip-step"><div class="cip-step-num">{index}</div><div>'
            f'<div class="cip-step-title">{esc(repair["method"])}</div>'
            f'<div class="cip-step-body">{esc(repair["description"])}</div>{materials}</div></div>'
        )
    render(card("".join(steps)))


def _render_findings(report: Dict[str, Any]) -> None:
    causes_col, repairs_col = st.columns([1, 1.25], gap="large")
    with causes_col:
        section("Probable root causes", "Most likely first")
        render(card(bullets(report["root_causes"]) if report["root_causes"] else "No causes listed."))
        section("Further investigation (NDT)")
        render(card(bullets(report["further_investigation"]) if report["further_investigation"] else "None required."))
        if report["monitoring_plan"]:
            section("Monitoring plan")
            render(card(f'<div class="cip-hazard-body">{esc(report["monitoring_plan"])}</div>'))
    with repairs_col:
        _render_repairs(report)
        section("Export")
        stamp = report["generated_at"][:19].replace(":", "").replace("-", "")
        st.download_button(
            "Download JSON report",
            data=json.dumps(report, indent=2, ensure_ascii=False),
            file_name=f"crack_diagnostics_{stamp}.json",
            mime="application/json",
            icon=":material/download:",
            width="stretch",
            key="crack_download",
        )
        with st.expander("View raw JSON"):
            st.json(report, expanded=False)


def render_tab(settings: AppSettings) -> None:
    upload_col, result_col = st.columns([5, 7], gap="large")

    with upload_col:
        section("Surface photo", f"Concrete or masonry close-up, JPG/PNG up to {MAX_UPLOAD_MB} MB — include a coin or scale for width")
        upload = st.file_uploader(
            "Concrete or wall surface photo",
            type=ACCEPTED_IMAGE_TYPES,
            key="crack_upload",
            label_visibility="collapsed",
        )
        element_col, exposure_col = st.columns(2)
        element = element_col.selectbox("Structural element", STRUCTURAL_ELEMENTS, key="crack_element")
        exposure = exposure_col.selectbox("Exposure", EXPOSURES, index=1, key="crack_exposure")
        age_col, growth_col = st.columns(2)
        age = age_col.number_input("Building age (years)", min_value=0, max_value=150, value=8, key="crack_age")
        growth = growth_col.selectbox("Crack growing?", GROWTH_OPTIONS, key="crack_growth")

        image = load_upload(upload)
        if image is not None:
            photo_tab, map_tab = st.tabs(["Photo", "Crack-enhancement map"])
            overlay_png, coverage = crack_map_for(image.digest, image)
            with photo_tab:
                st.image(image.image, width="stretch")
            with map_tab:
                st.image(overlay_png, width="stretch")
                st.caption(
                    "Pillow local-contrast filter: pixels darker than their surroundings are highlighted in red. "
                    "It shows where to look, not a diagnosis."
                )
            metrics = metrics_for(image.digest, image)
            for warning in quality_warnings(metrics):
                st.warning(warning, icon="📷")
            st.caption(f"Crack-like pixel coverage {coverage * 100:.2f}% · sharpness {metrics['sharpness']}")

        if settings.live:
            label, disabled = "Run crack diagnostics", image is None
        else:
            label, disabled = "Run diagnostics (demonstration sample)", False
        if st.button(label, type="primary", disabled=disabled, width="stretch", icon=":material/troubleshoot:"):
            with st.spinner("Classifying defect and assessing structural integrity…"):
                report = run_image_analysis(
                    settings,
                    image,
                    crack_prompt(element, exposure, int(age), growth),
                    CRACK_SYSTEM,
                    normalize_crack_report,
                    SAMPLE_CRACK_REPORT,
                )
            st.session_state[state.CRACK_RESULT] = {"digest": image.digest if image else None, "report": report}
        if settings.live and image is None:
            st.caption("Upload a photo to enable diagnostics.")

    result = st.session_state.get(state.CRACK_RESULT)
    with result_col:
        if not result:
            empty_state(
                "🧱",
                "No diagnosis yet",
                "Upload a crack photo to classify the defect, estimate its width and get IS 456-aligned repair guidance.",
            )
            return
        if image is not None and result["digest"] not in (None, image.digest):
            st.info("This report is for a previous photo — run diagnostics again for the new upload.", icon="🔁")
        _render_summary(result["report"])
    _render_findings(result["report"])
