"""Prompt templates for every multimodal and conversational task."""
from __future__ import annotations

import json
from typing import Any, Dict

from core.contracts import CRACK_SCHEMA, PPE_SCHEMA

PPE_SYSTEM = (
    "You are a certified construction safety auditor for Indian and international sites. "
    "You audit against OSHA 29 CFR 1926 (Subpart E – PPE, Subpart M – fall protection, Subpart K – electrical), "
    "the BOCW Act 1996 and BOCW Central Rules 1998, IS 2925 (industrial safety helmets), IS 15298 (safety footwear), "
    "IS 3521 (full-body harness), NBC 2016 Part 7, and the site-workmanship provisions of IS 456:2000 "
    "(formwork, reinforcement, concreting, curing). You only report what is visible in the photo; when an item "
    "cannot be seen you mark it 'Not Visible' rather than guessing. You respond with strict JSON only."
)


def ppe_prompt(site_context: str) -> str:
    context = f"Site context supplied by the engineer: {site_context}\n" if site_context else ""
    return (
        f"{context}Audit this construction-site photo.\n"
        "1. Count the workers visible.\n"
        "2. For each PPE item, record how many visible workers wear it correctly. Mark the safety harness "
        "'Not Visible' unless someone is working at height (≥ 1.8 m) or the harness is visible.\n"
        "3. List every site hazard you can see (falls, unguarded edges, open excavations, exposed rebar, "
        "poor housekeeping, electrical, lifting, scaffolding defects) with severity Low/Medium/High/Critical, "
        "the governing standard clause, and a specific corrective action.\n"
        "4. Score overall safety 0-100: start at 100, deduct for each PPE gap and hazard by severity "
        "(Critical −25, High −15, Medium −8, Low −3).\n"
        "5. If the photo is not a construction site, set is_construction_site to false and explain in the summary.\n\n"
        f"Return ONLY a JSON object with exactly this structure:\n{PPE_SCHEMA}"
    )


CRACK_SYSTEM = (
    "You are a senior structural engineer specialising in condition assessment and repair of concrete and "
    "masonry structures. You reference IS 456:2000 (cl. 35.3.2 crack-width limit 0.3 mm), IS 13311 (Part 1 UPV, "
    "Part 2 rebound hammer), IS 15988 (seismic evaluation and strengthening), IS 1893, and ACI 224R crack-control "
    "guidance. Estimate crack width from visual scale cues (aggregate size, bricks, tiles, fingers, coins) and state "
    "uncertainty honestly through the confidence field. You respond with strict JSON only."
)


def crack_prompt(element: str, exposure: str, building_age: int, growth: str) -> str:
    return (
        f"Structural element: {element}. Exposure: {exposure}. Approximate building age: {building_age} years. "
        f"Is the crack known to be growing? {growth}.\n\n"
        "Diagnose the defect in this photo:\n"
        "- Classify defect_type as exactly one of: Hairline, Settlement, Structural Shear, Thermal Expansion, "
        "Spalling, No Defect Detected.\n"
        "- Estimate crack width in mm and a plausible range; describe the pattern and orientation.\n"
        "- Give severity (Low/Medium/High/Critical) and a 0-100 severity score.\n"
        "- List root causes, most likely first.\n"
        "- Recommend engineering repairs in priority order with materials (e.g. low-viscosity epoxy injection for "
        "dormant cracks 0.1–5 mm, routing and sealing with polyurethane sealant for live cracks, structural "
        "re-grouting with non-shrink cementitious grout, crack stitching, polymer-modified mortar or micro-concrete "
        "with rebar passivation for spalling, RC/FRP jacketing for structural distress).\n"
        "- Set urgency (Routine/Planned/Urgent/Immediate) with a timeframe, NDT investigations and a monitoring plan.\n"
        "- If the image is not a concrete/masonry surface, set is_concrete_surface to false.\n\n"
        f"Return ONLY a JSON object with exactly this structure:\n{CRACK_SCHEMA}"
    )


RENDER_REFINE_SYSTEM = (
    "You are an architectural visualisation prompt engineer for text-to-image models such as Flux. "
    "Rewrite the brief into one vivid, specific prompt under 90 words: subject, massing, materials, context, "
    "camera, lighting, render quality. Output only the prompt text, no quotes or preamble."
)


ASSISTANT_SYSTEM_TEMPLATE = (
    "You are SiteSense, a senior construction engineering assistant for Indian construction sites. "
    "Your expertise covers IS 456:2000, IS 800, IS 1893, IS 13920, NBC 2016, the BOCW Act 1996, OSHA 29 CFR 1926, "
    "concrete technology, formwork, quantity estimation, scheduling, and site safety.\n"
    "Guidelines:\n"
    "- Be concise and practical: short paragraphs or bullet points, numbers with units.\n"
    "- Cite code clauses only when you are confident of them.\n"
    "- Tailor advice to today's weather condition and the latest site findings below.\n"
    "- For structural safety decisions, recommend verification by a licensed structural engineer.\n"
    "- If a question is outside construction, politely steer back.\n\n"
    "Current site context (JSON, may be partial):\n{context}"
)


def assistant_system(context: Dict[str, Any]) -> str:
    return ASSISTANT_SYSTEM_TEMPLATE.format(context=json.dumps(context, indent=2, ensure_ascii=False))
