"""Demonstration-mode content used when no Gemini API key is configured.

The image reports are fixed, representative samples that exercise the full JSON
contract and UI. They are labelled as samples everywhere they appear and never
claim to describe the uploaded photo.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

SAMPLE_PPE_REPORT: Dict[str, Any] = {
    "is_construction_site": True,
    "safety_score": 64,
    "overall_status": "Non-Compliant",
    "workers_detected": 7,
    "summary": (
        "Seven workers are visible on an RCC slab-casting front. Helmets and hi-vis vests are largely worn, "
        "but two workers near the unprotected slab edge have no harness tie-off and one worker is in sandals. "
        "Housekeeping around the rebar cage needs immediate attention."
    ),
    "ppe_detection": {
        "helmet": {"status": "Partial", "workers_compliant": 6, "workers_observed": 7,
                   "notes": "One worker at the mixer is bare-headed."},
        "high_vis_vest": {"status": "Compliant", "workers_compliant": 7, "workers_observed": 7,
                          "notes": "All workers wear fluorescent vests."},
        "steel_toe_boots": {"status": "Partial", "workers_compliant": 5, "workers_observed": 6,
                            "notes": "One worker in sandals near the rebar stack; one pair of feet not visible."},
        "safety_harness": {"status": "Non-Compliant", "workers_compliant": 0, "workers_observed": 2,
                           "notes": "Two workers at the slab edge (≈ 4 m drop) are not tied off."},
        "gloves": {"status": "Partial", "workers_compliant": 3, "workers_observed": 5,
                   "notes": "Bar benders handling rebar without gloves."},
        "eye_protection": {"status": "Not Visible", "workers_compliant": 0, "workers_observed": 0,
                           "notes": "No grinding or chipping visible in this frame."},
    },
    "hazards": [
        {"hazard": "Unprotected slab edge", "category": "Fall", "severity": "Critical",
         "location": "Right edge of the slab, 4th floor",
         "standard_reference": "OSHA 1926.501(b)(1); BOCW Central Rules 1998",
         "corrective_action": "Install 1 m top rail + mid rail + toe board, or anchor workers to a certified lifeline (IS 3521) before work resumes."},
        {"hazard": "Exposed rebar ends without caps", "category": "Struck-by", "severity": "High",
         "location": "Column starters, centre of frame",
         "standard_reference": "OSHA 1926.701(b)",
         "corrective_action": "Fit mushroom caps or bend over protruding bars; barricade the column grid."},
        {"hazard": "Worker without head protection", "category": "Struck-by", "severity": "High",
         "location": "Mixer platform, left foreground",
         "standard_reference": "OSHA 1926.100; IS 2925",
         "corrective_action": "Stop work for the individual, issue an IS 2925 helmet and reinforce in the toolbox talk."},
        {"hazard": "Rebar off-cuts and binding wire on access path", "category": "Housekeeping", "severity": "Medium",
         "location": "Walkway behind the formwork",
         "standard_reference": "OSHA 1926.25; IS 456:2000 cl. 12 (reinforcement storage)",
         "corrective_action": "Clear debris, stack reinforcement on raised supports and keep a 1 m clear walkway."},
        {"hazard": "Temporary cable routed across wet deck", "category": "Electrical", "severity": "Medium",
         "location": "Near the vibrator, bottom right",
         "standard_reference": "OSHA 1926.405; IS 732",
         "corrective_action": "Elevate cable on insulated hooks and confirm 30 mA RCCB protection at the DB."},
    ],
    "recommendations": [
        "Suspend edge work until guardrails or lifelines are installed and inspected.",
        "Enforce a gate-level PPE check: helmet, safety shoes, vest; harness for anyone working above 1.8 m.",
        "Cap all protruding rebar before the next shift.",
        "Assign a housekeeping crew for 15 minutes at the end of every pour.",
    ],
    "confidence": 0.82,
}

SAMPLE_CRACK_REPORT: Dict[str, Any] = {
    "is_concrete_surface": True,
    "defect_detected": True,
    "defect_type": "Settlement",
    "secondary_defects": ["Stepped cracking through mortar joints", "Minor efflorescence at plinth level"],
    "crack_pattern": "Diagonal, stepped at ≈ 45° rising away from the corner, widest at the top",
    "severity": "High",
    "severity_score": 68,
    "estimated_crack_width_mm": 1.8,
    "width_range_mm": [1.2, 2.5],
    "structural_risk": (
        "Indicates differential foundation movement; if active it can propagate into lintels and beams and "
        "compromise wall stability and water-tightness."
    ),
    "root_causes": [
        "Differential settlement of the corner footing (poorly compacted backfill or soft pocket)",
        "Water ingress from a leaking plinth drain softening the founding soil",
        "Absence of a plinth beam tying the wall footings together",
    ],
    "recommended_repairs": [
        {"method": "Confirm crack activity with tell-tale gauges",
         "description": "Fix glass or calibrated tell-tales across the crack and record for 4–6 weeks before any cosmetic repair.",
         "materials": "Calibrated crack monitor, crack-width microscope", "priority": 1},
        {"method": "Foundation stabilisation (if active)",
         "description": "Underpin the affected footing with micro-piles or jacket the footing; fix the drainage leak first.",
         "materials": "Micro-piles, M25 concrete, non-shrink grout", "priority": 2},
        {"method": "Low-viscosity epoxy injection",
         "description": "Once movement has stopped, seal the surface and pressure-inject from the bottom port upwards.",
         "materials": "Two-part low-viscosity epoxy resin, surface sealer, injection ports at 150–300 mm c/c", "priority": 3},
        {"method": "Masonry crack stitching",
         "description": "Install helical stainless-steel bars in cut slots across the stepped crack every 4–5 courses.",
         "materials": "6 mm helical SS bars, cementitious grout", "priority": 4},
    ],
    "urgency": "Urgent",
    "urgency_timeframe": "Investigate within 7 days; weekly width readings until stable",
    "further_investigation": [
        "Ultrasonic pulse velocity across the crack — IS 13311 (Part 1)",
        "Rebound hammer survey of adjacent RCC members — IS 13311 (Part 2)",
        "Trial pit and soil investigation at the corner footing — IS 1892",
    ],
    "monitoring_plan": "Weekly tell-tale and crack-width readings logged with photos; escalate if width grows by more than 0.2 mm.",
    "summary": (
        "Diagonal stepped crack about 1.8 mm wide, consistent with differential settlement at the building corner. "
        "Exceeds the IS 456 0.3 mm guidance; confirm whether it is active before repairing."
    ),
    "confidence": 0.78,
}


def _site_line(context: Dict[str, Any]) -> str:
    weather = context.get("weather", {}).get("condition")
    return f"\n\n_Today's protocol: **{weather}** conditions — see the advisory above._" if weather else ""


KNOWLEDGE_BASE: List[Tuple[Tuple[str, ...], str]] = [
    (("curing", "cure"),
     "**Curing (IS 456:2000 cl. 13.5.1)**\n"
     "- Keep exposed surfaces continuously moist for **≥ 7 days** with OPC.\n"
     "- **≥ 10 days** with PPC or mineral admixtures, and in hot, dry weather (extend to 14 days where possible).\n"
     "- Methods: ponding for slabs, wet hessian for columns and beams, or a membrane-forming curing compound.\n"
     "- Start as soon as the surface can take it without marking."),
    (("cover", "clear cover"),
     "**Nominal cover (IS 456 cl. 26.4)**\n"
     "- Footings: **50 mm** minimum.\n"
     "- Columns: **40 mm** for longitudinal bars.\n"
     "- Beams and slabs: **20 mm** (mild) / **30 mm** (moderate) / **45 mm** (severe) / **50 mm** (very severe) / **75 mm** (extreme exposure).\n"
     "- Use cover blocks of the same grade as the concrete, ~1 m c/c."),
    (("formwork", "shuttering", "strip", "deshuttering", "props"),
     "**Formwork stripping times (IS 456 cl. 11.3.1, OPC, normal temperature)**\n"
     "- Vertical faces of walls, columns and beams: **16–24 h**\n"
     "- Slab soffits (props re-fixed immediately): **3 days**\n"
     "- Beam soffits (props re-fixed immediately): **7 days**\n"
     "- Props to slabs: **7 days** up to 4.5 m span, **14 days** above 4.5 m\n"
     "- Props to beams and arches: **14 days** up to 6 m span, **21 days** above 6 m"),
    (("cube", "compressive", "sampling", "strength test"),
     "**Cube testing (IS 456 cl. 15)**\n"
     "- Sampling frequency: 1–5 m³ → 1 sample; 6–15 → 2; 16–30 → 3; 31–50 → 4; above 50 m³ → 4 + 1 per extra 50 m³.\n"
     "- Each sample is 3 cubes (150 mm), tested at 28 days; 7-day results are typically ~65–70 % of the 28-day strength.\n"
     "- Acceptance follows IS 456 Table 11 (mean of 4 results and individual minimum)."),
    (("slump", "workability"),
     "**Workability (IS 456 cl. 7)**\n"
     "- Lightly reinforced slabs, beams, walls, columns: **25–75 mm** slump.\n"
     "- Heavily reinforced sections: **50–100 mm**.\n"
     "- Pumped concrete: **75–100 mm**, often higher with superplasticisers.\n"
     "- Never add water at site to recover slump — use an approved admixture instead."),
    (("grade", "mix", "m20", "m25", "m30", "ratio"),
     "**Concrete grades**\n"
     "- Minimum grade for RCC is **M20** (mild exposure), M25 moderate, M30 severe — IS 456 Table 5.\n"
     "- M20 nominal mix ≈ 1 : 1.5 : 3 (cement : sand : aggregate); M25 and above should be **design mixes** to IS 10262.\n"
     "- Maximum w/c ratio for RCC: 0.55 (mild) down to 0.40 (extreme exposure)."),
    (("ppe", "helmet", "harness", "vest", "boots", "shoes"),
     "**Minimum PPE on site**\n"
     "- Helmet to **IS 2925** with chin strap.\n"
     "- Safety footwear to **IS 15298** (steel toe, slip and puncture resistant).\n"
     "- Hi-vis vest for everyone in plant-movement zones.\n"
     "- Full-body harness to **IS 3521** with 100 % tie-off for work at height ≥ 1.8 m (OSHA 1926.501).\n"
     "- Task-specific: gloves for rebar, goggles or face shields for grinding and chipping, ear protection near breakers."),
    (("crack", "epoxy", "spalling", "repair"),
     "**Crack repair quick guide**\n"
     "- Width ≤ 0.3 mm (IS 456 cl. 35.3.2 limit): usually cosmetic — seal with a polymer-modified coat.\n"
     "- Dormant cracks 0.3–5 mm: low-viscosity **epoxy injection**.\n"
     "- Live (moving) cracks: rout and seal with a flexible polyurethane sealant.\n"
     "- Spalling: remove loose concrete, clean and passivate rebar, rebuild with polymer-modified mortar or micro-concrete.\n"
     "- Upload a photo in the **Crack Diagnostics** tab for a full assessment."),
    (("steel", "rebar", "cement", "quantity", "estimate", "material"),
     "**Thumb-rule quantities (residential RCC frame, per sq ft built-up)**\n"
     "- Steel: **3.5–4.5 kg**\n"
     "- Cement: **0.4 bags**\n"
     "- Sand: **1.8 cft**\n"
     "- Aggregate: **1.35 cft**\n"
     "- Bricks: **8 nos**\n"
     "Open the **Planning & Valuation** tab for a project-specific take-off and costing."),
    (("wind", "crane", "lifting"),
     "**Wind and crane operations**\n"
     "- Follow the crane manufacturer's in-service wind limit and read wind speed from the anemometer.\n"
     "- Do not hoist personnel platforms above **32 km/h** (OSHA 1926.1431).\n"
     "- Stop handling high-sail-area loads (formwork panels, sheets, glazing) in gusty conditions.\n"
     "- Leave tower cranes free to slew when out of service."),
    (("rain", "monsoon", "waterproof"),
     "**Monsoon checklist**\n"
     "- Weatherproof DBs with 30 mA RCCBs; no outdoor welding in the rain.\n"
     "- Inspect excavation shoring after every downpour; keep dewatering pumps on standby.\n"
     "- Cover fresh concrete for 24 h.\n"
     "- Store cement on raised platforms, ≤ 10 bags high (IS 4082)."),
    (("heat", "hot", "temperature", "summer"),
     "**Hot-weather working**\n"
     "- Workers: water every 15–20 min, ORS, shaded rest, no strenuous work 12:00–15:00.\n"
     "- Concrete: keep placing temperature ≤ 35 °C — chilled water or ice, shaded aggregates, retarders.\n"
     "- Pour early morning or at night; start curing immediately and extend to ≥ 10 days."),
    (("toolbox", "briefing", "today", "risk", "plan"),
     "**Today's toolbox talk outline**\n"
     "1. Weather protocol in force and the operations it restricts.\n"
     "2. Open findings from the latest PPE audit and crack survey.\n"
     "3. High-risk tasks of the day: permits, competent persons, exclusion zones.\n"
     "4. Emergency assembly point, first-aider and ambulance numbers.\n"
     "5. Questions and worker sign-off."),
]

DEMO_FALLBACK = (
    "I'm running in **demonstration mode**, so I can answer from a built-in knowledge base on: "
    "curing, cover, formwork stripping, cube testing, slump, concrete grades, PPE, crack repair, "
    "material quantities, wind/crane limits, monsoon and hot-weather working, and toolbox talks.\n\n"
    "Add a Gemini API key in the sidebar for full conversational answers grounded in your site data."
)


def demo_chat_reply(message: str, context: Dict[str, Any]) -> str:
    text = message.lower()
    best_answer, best_hits = None, 0
    for keywords, answer in KNOWLEDGE_BASE:
        hits = sum(1 for keyword in keywords if keyword in text)
        if hits > best_hits:
            best_answer, best_hits = answer, hits
    if best_answer is None:
        return DEMO_FALLBACK
    return best_answer + _site_line(context)
