"""Tab 3 — Project Planning & Real Estate Valuation (Epic 3)."""
from __future__ import annotations

import json
from typing import Any, Dict

import streamlit as st

from core.config import (
    ARCH_STYLES,
    LOCATION_TIERS,
    MARKET_RATE_PER_SQFT,
    RENDER_VIEWS,
    STRUCTURE_TYPES,
    TIME_OF_DAY,
)
from core.formatting import format_inr, format_quantity, indian_grouping
from core.llm import LLMError
from core.prompts import RENDER_REFINE_SYSTEM
from core.rendering import RenderError, build_render_prompt, fetch_render, pollinations_url
from core.settings import AppSettings
from core.valuation import ValuationInputs, compute_valuation
from ui import state
from ui.components import (
    MILESTONE_TONE,
    card,
    esc,
    kpi_row,
    meter,
    metric_card,
    pill,
    render,
    section,
    stacked_bar,
)

# Categorical slots 1–3 of the validated reference palette (identity, not status).
BUDGET_COLORS = {"Hard construction cost": "#2a78d6", "Soft costs": "#eb6834", "Contingency": "#1baf7a"}
DEFAULT_FLOORS = {
    "Residential – Independent House (G+1 / G+2)": 2,
    "Residential – Apartment (Mid / High-Rise)": 12,
    "Premium Villa": 2,
    "Commercial – Office / Retail": 6,
    "Industrial – Warehouse / Shed (PEB)": 1,
    "Institutional – School / Hospital": 4,
}


def _inputs() -> ValuationInputs:
    with st.container(border=True):
        type_col, area_col, tier_col = st.columns([1.5, 1, 1.2])
        structure = type_col.selectbox("Structure type", list(STRUCTURE_TYPES), key="val_structure")
        sqft = area_col.number_input(
            "Built-up area (sq ft)", min_value=200, max_value=5_000_000, value=2400, step=100, key="val_sqft"
        )
        tier = tier_col.selectbox(
            "Location tier",
            list(LOCATION_TIERS),
            key="val_tier",
            help="\n".join(f"**{tier}** — {cities}" for tier, cities in LOCATION_TIERS.items()),
        )
        completion = st.slider("Construction completion (%)", 0, 100, 45, key="val_completion")
        st.caption(f"{tier}: {LOCATION_TIERS[tier]}")

        with st.expander("Advanced assumptions"):
            a1, a2, a3 = st.columns(3)
            default_rate = MARKET_RATE_PER_SQFT[tier] * STRUCTURE_TYPES[structure]["market_factor"]
            override = a1.number_input(
                "Local market rate (₹/sq ft, 0 = auto)",
                min_value=0,
                max_value=200_000,
                value=0,
                step=250,
                key="val_rate_override",
                help=f"Auto rate for this tier and structure: ₹{indian_grouping(default_rate)}/sq ft",
            )
            land_lakh = a2.number_input(
                "Land acquisition cost (₹ lakh)", min_value=0.0, max_value=1_000_000.0, value=0.0, step=5.0, key="val_land"
            )
            include_land = a3.toggle("Include land value in valuation", value=True, key="val_include_land")
            b1, b2 = st.columns(2)
            soft = b1.slider("Soft costs — design, approvals, supervision (%)", 0.0, 20.0, 7.0, 0.5, key="val_soft")
            contingency = b2.slider("Contingency (%)", 0.0, 20.0, 5.0, 0.5, key="val_contingency")

    return ValuationInputs(
        structure_type=structure,
        built_up_sqft=float(sqft),
        tier=tier,
        completion_pct=float(completion),
        market_rate_override=float(override) or None,
        land_cost_inr=float(land_lakh) * 1e5,
        soft_cost_pct=soft,
        contingency_pct=contingency,
        include_land_value=include_land,
    )


def _render_kpis(result: Dict[str, Any]) -> None:
    cost, value, rates = result["cost"], result["valuation"], result["rates"]
    completion = result["inputs"]["completion_pct"]
    kpi_row(
        [
            metric_card(
                "Total project budget",
                format_inr(cost["total_budget"]),
                sub=f"₹{indian_grouping(cost['all_in_cost_per_sqft'])}/sq ft all-in",
            ),
            metric_card(
                "Capex incurred",
                format_inr(cost["capex_incurred"]),
                sub=f"{completion:.0f}% complete · {format_inr(cost['balance_to_complete'])} to go",
            ),
            metric_card(
                "Current asset valuation",
                format_inr(value["current_valuation"]),
                sub=f"incl. {value['under_construction_discount_pct']:.1f}% under-construction discount",
                tone="accent",
            ),
            metric_card(
                "Value on completion",
                format_inr(value["value_on_completion"]),
                sub=f"@ ₹{indian_grouping(rates['market_rate_per_sqft'])}/sq ft market rate",
            ),
        ]
    )


def _render_progress(result: Dict[str, Any]) -> None:
    completion = result["inputs"]["completion_pct"]
    rows = [meter(completion, "accent", f"Overall progress — {result['current_milestone']}", f"{completion:.0f}%")]
    for milestone in result["milestones"]:
        status = milestone["status"]
        icon = {"Completed": "✓", "In Progress": "◐", "Pending": "○"}[status]
        rows.append(
            meter(
                milestone["progress_pct"],
                MILESTONE_TONE[status],
                f"{icon} {milestone['milestone']}",
                f"{status} · {milestone['start_pct']}–{milestone['end_pct']}%",
            )
        )
    render(card("".join(rows)))


def _render_budget(result: Dict[str, Any]) -> None:
    cost, investment = result["cost"], result["investment"]
    segments = [
        ("Hard construction cost", cost["hard_cost"], BUDGET_COLORS["Hard construction cost"]),
        ("Soft costs", cost["soft_cost"], BUDGET_COLORS["Soft costs"]),
        ("Contingency", cost["contingency"], BUDGET_COLORS["Contingency"]),
    ]
    render(card(f'<div class="cip-metric-label">Budget composition</div>{stacked_bar(segments, format_inr)}'))

    margin = investment["projected_margin"]
    if result["inputs"]["land_cost_inr"]:
        land_note = f"Investment includes the entered land cost of {format_inr(investment['land_cost_basis'])}."
    elif investment["land_cost_assumed_at_market"]:
        land_note = f"No land cost entered — land assumed at market value ({format_inr(investment['land_cost_basis'])})."
    else:
        land_note = "Structure-only basis — land excluded from value and cost."
    stats = [
        ("Projected margin", format_inr(margin)),
        ("Return on investment", f"{investment['roi_pct']:.1f}%"),
        ("Cost-to-value", f"{investment['cost_to_value_pct']:.0f}%"),
    ]
    verdict = pill("Positive margin", "good") if margin >= 0 else pill("Negative margin", "critical")
    render(
        card(
            '<div class="cip-metric-label">Investment snapshot · on completion</div><div class="cip-stats">'
            + "".join(f"<div><span>{esc(label)}</span><b>{esc(value)}</b></div>" for label, value in stats)
            + f'</div><div class="cip-snapshot-foot">{verdict}<span class="cip-footnote">{esc(land_note)}</span></div>'
        )
    )


def _render_materials(result: Dict[str, Any]) -> None:
    section("Steel, cement & material requirements", "Thumb-rule take-off with a front-loaded consumption profile")
    body = []
    for row in result["materials"]:
        body.append(
            "<tr>"
            f"<td>{esc(row['material'])}</td>"
            f"<td class='num'>{row['rate_per_sqft']:g} {esc(row['unit'])}/sq ft</td>"
            f"<td class='num'>{esc(format_quantity(row['total_required'], row['unit']))}</td>"
            f"<td class='num'>{esc(format_quantity(row['consumed_to_date'], row['unit']))}</td>"
            f"<td>{meter(row['consumed_pct'], 'accent')}</td>"
            f"<td class='num'>{esc(format_quantity(row['balance'], row['unit']))}</td>"
            f"<td class='num'>{esc(format_inr(row['estimated_cost_inr']))}</td>"
            "</tr>"
        )
    total = sum(row["estimated_cost_inr"] for row in result["materials"])
    render(
        card(
            '<div class="cip-table-wrap"><table class="cip-table"><thead><tr>'
            "<th>Material</th><th class='num'>Thumb rule</th><th class='num'>Total required</th>"
            "<th class='num'>Used to date</th><th>Consumed</th><th class='num'>Balance to procure</th>"
            "<th class='num'>Est. cost</th></tr></thead>"
            f"<tbody>{''.join(body)}</tbody></table></div>"
            f'<div class="cip-footnote">Core materials ≈ {esc(format_inr(total))} '
            f"({total / result['cost']['hard_cost'] * 100:.0f}% of hard cost) at indicative rates: steel ₹62/kg, "
            "cement ₹400/bag, sand ₹55/cft, aggregate ₹45/cft, bricks ₹9 each.</div>"
        )
    )


def _render_rendering(settings: AppSettings, inputs: ValuationInputs) -> None:
    section("Conceptual 3D architectural rendering", "Prompt generator for the Pollinations AI (Flux) image model")
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([1.2, 1.2, 1, 0.7])
        style = c1.selectbox("Architectural style", ARCH_STYLES, key="render_style")
        view = c2.selectbox("Camera view", RENDER_VIEWS, key="render_view")
        light = c3.selectbox("Lighting", TIME_OF_DAY, key="render_light")
        floors = c4.number_input(
            "Floors", min_value=1, max_value=80, value=DEFAULT_FLOORS.get(inputs.structure_type, 2), key=f"render_floors::{inputs.structure_type}"
        )
        prompt = build_render_prompt(inputs.structure_type, inputs.built_up_sqft, inputs.tier, style, view, light, int(floors))

        opt1, opt2 = st.columns([1, 1])
        refine = opt1.toggle(
            "Refine prompt with Gemini",
            value=False,
            disabled=not settings.live,
            key="render_refine",
            help="Requires an API key. Gemini rewrites the brief into a richer text-to-image prompt.",
        )
        seed = opt2.number_input("Seed (change for a new variation)", min_value=0, max_value=999_999, value=42, key="render_seed")

        st.code(prompt, language=None, wrap_lines=True)
        if st.button("Generate concept render", type="primary", icon=":material/view_in_ar:", key="render_go"):
            final_prompt = prompt
            if refine and settings.live:
                try:
                    with st.spinner("Refining the prompt with Gemini…"):
                        final_prompt = settings.client().generate_text(prompt, system=RENDER_REFINE_SYSTEM, temperature=0.8)
                except LLMError as exc:
                    st.warning(f"{exc} Using the original prompt.", icon="⚠️")
            url = pollinations_url(final_prompt, seed=int(seed))
            try:
                with st.spinner("Rendering with Flux — this usually takes 10–40 seconds…"):
                    image_bytes = fetch_render(url)
                st.session_state[state.RENDER_RESULT] = {"prompt": final_prompt, "url": url, "image": image_bytes}
            except RenderError as exc:
                st.session_state[state.RENDER_RESULT] = {"prompt": final_prompt, "url": url, "image": None, "error": str(exc)}

        result = st.session_state.get(state.RENDER_RESULT)
        if result:
            if result.get("image"):
                st.image(result["image"], caption="AI concept render — illustrative only, not a design drawing", width="stretch")
                d1, d2 = st.columns(2)
                d1.download_button(
                    "Download render (JPG)", data=result["image"], file_name="concept_render.jpg", mime="image/jpeg",
                    icon=":material/download:", width="stretch", key="render_download",
                )
                d2.link_button("Open in Pollinations", result["url"], icon=":material/open_in_new:", width="stretch")
            else:
                st.error(f"{result.get('error', 'Rendering failed.')} You can open the render directly instead.", icon="🖼️")
                st.link_button("Open render in a new tab", result["url"], icon=":material/open_in_new:")
            if result["prompt"] != prompt:
                with st.expander("Prompt used for this render"):
                    st.write(result["prompt"])


def render_tab(settings: AppSettings) -> None:
    section("Project parameters", "Indicative 2025-26 Indian market rates — adjust in Advanced assumptions")
    inputs = _inputs()
    try:
        result = compute_valuation(inputs)
    except ValueError as exc:
        st.error(str(exc))
        return
    st.session_state[state.VALUATION_RESULT] = result

    _render_kpis(result)
    progress_col, budget_col = st.columns([1.15, 1], gap="large")
    with progress_col:
        section("Milestone progress", f"Current stage: {result['current_milestone']}")
        _render_progress(result)
    with budget_col:
        section("Budget & investment", f"{inputs.tier} · {inputs.structure_type}")
        _render_budget(result)
        st.download_button(
            "Download valuation JSON",
            data=json.dumps(result, indent=2, ensure_ascii=False),
            file_name="project_valuation.json",
            mime="application/json",
            icon=":material/download:",
            width="stretch",
            key="valuation_download",
        )
    _render_materials(result)
    _render_rendering(settings, inputs)
    render(
        pill("Decision-support estimate", "accent")
        + '<span class="cip-footnote" style="margin-left:.5rem">Figures use thumb rules and tier averages; '
        "obtain a quantity surveyor's estimate and a registered valuer's report for financing or statutory use.</span>"
    )
