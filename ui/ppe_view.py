"""Tab 1 — Site Safety & PPE Audit (Epic 2)."""
from __future__ import annotations

import json
from typing import Any, Dict, Optional

import streamlit as st

from core.analysis import run_image_analysis
from core.config import ACCEPTED_IMAGE_TYPES, MAX_UPLOAD_MB
from core.contracts import normalize_ppe_report
from core.demo import SAMPLE_PPE_REPORT
from core.imaging import quality_warnings
from core.prompts import PPE_SYSTEM, ppe_prompt
from core.settings import AppSettings
from ui import state
from ui.components import (
    OVERALL_STATUS_TONE,
    PPE_STATUS_TONE,
    SEVERITY_TONE,
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
    score_tone,
    section,
    severity_pill,
    source_banner,
)
from ui.uploads import load_upload, metrics_for


def _compliance_rate(report: Dict[str, Any]) -> Optional[float]:
    observed = sum(item["workers_observed"] for item in report["ppe_detection"].values())
    compliant = sum(item["workers_compliant"] for item in report["ppe_detection"].values())
    return compliant / observed * 100 if observed else None


def _render_summary(report: Dict[str, Any]) -> None:
    source_banner(report["source"], report.get("error"))
    if not report["is_construction_site"]:
        alert("This may not be a construction-site photo", report["summary"], "warning", "🔍")

    score = report["safety_score"]
    status = report["overall_status"]
    ring_col, text_col = st.columns([1, 1.9], gap="medium")
    with ring_col:
        render(
            card(
                score_ring(score, "Safety score", score_tone(score))
                + f'<div style="text-align:center">{pill(status, OVERALL_STATUS_TONE.get(status, "neutral"))}</div>'
            )
        )
    with text_col:
        model = f" · {report['model']}" if report.get("model") else ""
        render(
            card(
                '<div class="cip-metric-label">Audit summary</div>'
                f'<div class="cip-hazard-body" style="margin-top:.4rem">{esc(report["summary"])}</div>'
                f'<div class="cip-footnote">Confidence {report["confidence"]:.0%}{esc(model)} · '
                f'{esc(report["generated_at"])}</div>'
            )
        )

    hazards = report["hazards"]
    severe = sum(1 for h in hazards if h["severity"] in ("High", "Critical"))
    critical = sum(1 for h in hazards if h["severity"] == "Critical")
    rate = _compliance_rate(report)
    kpi_row(
        [
            metric_card("Workers detected", str(report["workers_detected"])),
            metric_card(
                "PPE compliance",
                f"{rate:.0f}" if rate is not None else "—",
                unit="%" if rate is not None else "",
                sub="worker-items worn correctly",
                tone=score_tone(rate) if rate is not None else None,
            ),
            metric_card("Hazards identified", str(len(hazards)), sub=f"{severe} high or critical"),
            metric_card(
                "Critical hazards",
                str(critical),
                sub="stop-work items" if critical else "none found",
                tone="critical" if critical else "good",
            ),
        ],
        min_width=210,
    )


def _render_checklist(report: Dict[str, Any]) -> None:
    section("PPE detection checklist", "Workers wearing each item correctly / workers on whom it could be assessed")
    rows = []
    for item in report["ppe_detection"].values():
        count = f'{item["workers_compliant"]}/{item["workers_observed"]}' if item["workers_observed"] else "—"
        notes = f'<div class="cip-check-notes">{esc(item["notes"])}</div>' if item["notes"] else ""
        rows.append(
            f'<div class="cip-check"><div class="cip-check-main"><div class="cip-check-title">{esc(item["label"])}</div>'
            f'{notes}</div><div class="cip-check-count">{count}</div>'
            f'{pill(item["status"], PPE_STATUS_TONE.get(item["status"], "neutral"))}</div>'
        )
    render(card("".join(rows)))


def _render_hazards(report: Dict[str, Any]) -> None:
    section("Site hazards", "Sorted by severity, with the governing standard and corrective remedy")
    if not report["hazards"]:
        render(card('<div class="cip-check-notes">No hazards were identified in this photo.</div>'))
        return
    for hazard in report["hazards"]:
        meta = " · ".join(part for part in (hazard["category"], hazard["location"]) if part)
        reference = (
            f'<div class="cip-hazard-ref">📘 {esc(hazard["standard_reference"])}</div>'
            if hazard["standard_reference"]
            else ""
        )
        render(
            card(
                f'<div class="cip-hazard-head"><span class="cip-hazard-title">{esc(hazard["hazard"])}</span>'
                f'{severity_pill(hazard["severity"])}</div><div class="cip-hazard-meta">{esc(meta)}</div>'
                f'<div class="cip-hazard-body"><b>Remedy:</b> {esc(hazard["corrective_action"])}</div>{reference}',
                f"cip-hazard cip-tone-{SEVERITY_TONE[hazard['severity']]}",
            )
        )


def _render_actions(report: Dict[str, Any]) -> None:
    rec_col, export_col = st.columns([1.6, 1], gap="large")
    with rec_col:
        section("Priority recommendations")
        if report["recommendations"]:
            render(card(bullets(report["recommendations"])))
        else:
            st.caption("No additional recommendations.")
    with export_col:
        section("Export", "Versioned JSON contract for downstream systems")
        stamp = report["generated_at"][:19].replace(":", "").replace("-", "")
        st.download_button(
            "Download JSON report",
            data=json.dumps(report, indent=2, ensure_ascii=False),
            file_name=f"ppe_safety_audit_{stamp}.json",
            mime="application/json",
            icon=":material/download:",
            width="stretch",
            key="ppe_download",
        )
        with st.expander("View raw JSON"):
            st.json(report, expanded=False)


def render_tab(settings: AppSettings) -> None:
    upload_col, result_col = st.columns([5, 7], gap="large")

    with upload_col:
        section("Site photo", f"JPG or PNG up to {MAX_UPLOAD_MB} MB — wide shots showing workers head-to-toe work best")
        upload = st.file_uploader(
            "Construction site photo",
            type=ACCEPTED_IMAGE_TYPES,
            key="ppe_upload",
            label_visibility="collapsed",
        )
        site_context = st.text_input(
            "Site context (optional)",
            placeholder="e.g. Slab casting on 4th floor, 12 workers on shift",
            key="ppe_context",
            max_chars=300,
        )
        image = load_upload(upload)
        if image is not None:
            st.image(image.image, caption=f"{image.original_size[0]}×{image.original_size[1]} px", width="stretch")
            metrics = metrics_for(image.digest, image)
            for warning in quality_warnings(metrics):
                st.warning(warning, icon="📷")
            st.caption(
                f"Pillow pre-check · brightness {metrics['brightness']}% · contrast {metrics['contrast']}% · "
                f"sharpness {metrics['sharpness']} · hi-vis colour coverage {metrics['hivis_coverage_pct']}%"
            )

        if settings.live:
            label, disabled = "Run PPE safety audit", image is None
        else:
            label, disabled = "Run audit (demonstration sample)", False
        if st.button(label, type="primary", disabled=disabled, width="stretch", icon=":material/health_and_safety:"):
            with st.spinner("Auditing PPE compliance and site hazards…"):
                report = run_image_analysis(
                    settings, image, ppe_prompt(site_context.strip()), PPE_SYSTEM, normalize_ppe_report, SAMPLE_PPE_REPORT
                )
            st.session_state[state.PPE_RESULT] = {"digest": image.digest if image else None, "report": report}
        if settings.live and image is None:
            st.caption("Upload a photo to enable the audit.")

    result = st.session_state.get(state.PPE_RESULT)
    with result_col:
        if not result:
            empty_state(
                "🦺",
                "No audit yet",
                "Upload a site photo and run the audit to score PPE compliance against OSHA 1926 and Indian BOCW / IS codes.",
            )
            return
        if image is not None and result["digest"] not in (None, image.digest):
            st.info("This report is for a previous photo — run the audit again to analyse the new upload.", icon="🔁")
        _render_summary(result["report"])

    checklist_col, hazard_col = st.columns([1, 1.15], gap="large")
    with checklist_col:
        _render_checklist(result["report"])
    with hazard_col:
        _render_hazards(result["report"])
    _render_actions(result["report"])
