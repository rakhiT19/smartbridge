"""JSON data contracts (Epic 4).

LLM output is never trusted as-is. Every response passes through a normaliser that
coerces types, clamps ranges, maps synonyms onto the contract enums and fills safe
defaults, so the UI and downstream consumers always receive a valid document.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional

from core.config import (
    CRACK_TYPES,
    IS456_CRACK_LIMIT_MM,
    OVERALL_STATUSES,
    PPE_ITEMS,
    PPE_STATUSES,
    SEVERITY_LEVELS,
    SEVERITY_RANK,
    SEVERITY_SYNONYMS,
    URGENCY_LEVELS,
    URGENCY_SYNONYMS,
    URGENCY_TIMEFRAMES,
)

SCHEMA_VERSION = "1.0"

# Schema descriptions embedded in prompts so the model knows the exact contract.
PPE_SCHEMA = """{
  "is_construction_site": true,
  "safety_score": 0-100 integer (100 = fully compliant, no hazards),
  "overall_status": "Compliant" | "Needs Attention" | "Non-Compliant" | "Critical Violation",
  "workers_detected": integer,
  "summary": "2-3 sentence audit summary",
  "ppe_detection": {
    "helmet":          {"status": "Compliant|Partial|Non-Compliant|Not Visible", "workers_compliant": int, "workers_observed": int, "notes": "..."},
    "high_vis_vest":   {...same shape...},
    "steel_toe_boots": {...same shape...},
    "safety_harness":  {...same shape...},
    "gloves":          {...same shape...},
    "eye_protection":  {...same shape...}
  },
  "hazards": [
    {"hazard": "short title", "category": "Fall | Struck-by | Electrical | Housekeeping | Excavation | Fire | Health | Other",
     "severity": "Low|Medium|High|Critical", "location": "where in the image",
     "standard_reference": "e.g. OSHA 1926.501(b)(1) / IS 3521", "corrective_action": "specific remedy"}
  ],
  "recommendations": ["prioritised action", "..."],
  "confidence": 0.0-1.0
}"""

CRACK_SCHEMA = """{
  "is_concrete_surface": true,
  "defect_detected": true,
  "defect_type": "Hairline" | "Settlement" | "Structural Shear" | "Thermal Expansion" | "Spalling" | "No Defect Detected",
  "secondary_defects": ["e.g. efflorescence", "rebar corrosion staining"],
  "crack_pattern": "e.g. diagonal at 45°, vertical, horizontal, map/random, stepped",
  "severity": "Low|Medium|High|Critical",
  "severity_score": 0-100 integer (100 = imminent structural risk),
  "estimated_crack_width_mm": number,
  "width_range_mm": [min, max],
  "structural_risk": "one sentence on load-path / durability implications",
  "root_causes": ["most likely cause first", "..."],
  "recommended_repairs": [
    {"method": "e.g. Low-viscosity epoxy injection", "description": "how and when", "materials": "products / specs", "priority": 1}
  ],
  "urgency": "Routine" | "Planned" | "Urgent" | "Immediate",
  "urgency_timeframe": "e.g. Repair within 7 days",
  "further_investigation": ["e.g. UPV test per IS 13311 (Part 1)"],
  "monitoring_plan": "how to monitor (tell-tales, crack-width gauge, frequency)",
  "summary": "2-3 sentence diagnosis",
  "confidence": 0.0-1.0
}"""


# --------------------------------------------------------------------------- #
# Primitive coercion helpers
# --------------------------------------------------------------------------- #
def _key(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def match_choice(
    value: Any,
    allowed: Iterable[str],
    default: Optional[str] = None,
    synonyms: Optional[Mapping[str, str]] = None,
) -> Optional[str]:
    """Map free text onto an enum: exact match, then synonym, then longest substring."""
    if value is None:
        return default
    raw = _key(str(value))
    if not raw:
        return default
    options = list(allowed)
    for option in options:
        if _key(option) == raw:
            return option
    if synonyms:
        for word, target in synonyms.items():
            if _key(word) == raw:
                return target
    contained = [opt for opt in options if _key(opt) and _key(opt) in raw]
    if contained:
        return max(contained, key=lambda opt: len(_key(opt)))
    if synonyms:
        for word, target in synonyms.items():
            if _key(word) in raw:
                return target
    return default


def as_int(value: Any, default: int = 0, lo: Optional[int] = None, hi: Optional[int] = None) -> int:
    try:
        number = int(round(float(value)))
    except (TypeError, ValueError):
        number = default
    if lo is not None:
        number = max(lo, number)
    if hi is not None:
        number = min(hi, number)
    return number


def as_float(value: Any, default: float = 0.0, lo: Optional[float] = None, hi: Optional[float] = None) -> float:
    try:
        if isinstance(value, str):
            found = re.search(r"-?\d+(?:\.\d+)?", value)
            value = found.group(0) if found else None
        number = float(value)
    except (TypeError, ValueError):
        number = default
    if number != number:  # NaN
        number = default
    if lo is not None:
        number = max(lo, number)
    if hi is not None:
        number = min(hi, number)
    return number


def as_str(value: Any, default: str = "", limit: int = 1200) -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text[:limit] if text else default


def as_str_list(value: Any, limit: int = 12) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, (list, tuple)):
        return []
    items = []
    for item in value:
        if isinstance(item, dict):
            item = next((v for v in item.values() if isinstance(v, str)), "")
        text = as_str(item)
        if text:
            items.append(text)
    return items[:limit]


def as_bool(value: Any, default: bool = True) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "y", "1"}:
            return True
        if lowered in {"false", "no", "n", "0"}:
            return False
    return default


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def status_from_score(score: int) -> str:
    if score >= 85:
        return "Compliant"
    if score >= 70:
        return "Needs Attention"
    if score >= 45:
        return "Non-Compliant"
    return "Critical Violation"


def severity_from_score(score: int) -> str:
    if score >= 80:
        return "Critical"
    if score >= 55:
        return "High"
    if score >= 30:
        return "Medium"
    return "Low"


# --------------------------------------------------------------------------- #
# PPE safety audit contract
# --------------------------------------------------------------------------- #
def _ppe_item_lookup(raw_ppe: Any) -> Dict[str, Any]:
    """Accept either the contract dict or a list of {"item": ..., ...} objects."""
    if isinstance(raw_ppe, dict):
        return raw_ppe
    lookup: Dict[str, Any] = {}
    if isinstance(raw_ppe, list):
        for entry in raw_ppe:
            if not isinstance(entry, dict):
                continue
            name = _key(as_str(entry.get("item") or entry.get("name")))
            for key, label in PPE_ITEMS.items():
                tokens = {_key(key), _key(label)} | set(_key(label).split())
                if name and (name in tokens or _key(key.split("_")[0]) in name):
                    lookup[key] = entry
    return lookup


def normalize_ppe_report(raw: Mapping[str, Any], source: str = "live", model: Optional[str] = None) -> Dict[str, Any]:
    raw = raw if isinstance(raw, Mapping) else {}
    score = as_int(raw.get("safety_score"), default=0, lo=0, hi=100)
    status = match_choice(raw.get("overall_status"), OVERALL_STATUSES) or status_from_score(score)

    lookup = _ppe_item_lookup(raw.get("ppe_detection"))
    ppe: Dict[str, Dict[str, Any]] = {}
    for key, label in PPE_ITEMS.items():
        item = lookup.get(key, {})
        if isinstance(item, str):
            item = {"status": item}
        elif isinstance(item, bool):
            item = {"status": "Compliant" if item else "Non-Compliant"}
        elif not isinstance(item, dict):
            item = {}
        observed = as_int(item.get("workers_observed"), default=0, lo=0)
        compliant = as_int(item.get("workers_compliant"), default=0, lo=0, hi=observed if observed else None)
        ppe[key] = {
            "label": label,
            "status": match_choice(item.get("status"), PPE_STATUSES, default="Not Visible"),
            "workers_compliant": compliant,
            "workers_observed": observed,
            "notes": as_str(item.get("notes")),
        }

    hazards = []
    for entry in raw.get("hazards") or []:
        if isinstance(entry, str):
            entry = {"hazard": entry}
        if not isinstance(entry, dict):
            continue
        title = as_str(entry.get("hazard") or entry.get("title") or entry.get("description"))
        if not title:
            continue
        hazards.append(
            {
                "hazard": title,
                "category": as_str(entry.get("category"), "Other"),
                "severity": match_choice(entry.get("severity"), SEVERITY_LEVELS, "Medium", SEVERITY_SYNONYMS),
                "location": as_str(entry.get("location")),
                "standard_reference": as_str(entry.get("standard_reference") or entry.get("standard")),
                "corrective_action": as_str(
                    entry.get("corrective_action") or entry.get("remedy") or entry.get("recommendation"),
                    "Assign a competent person to assess and control this hazard.",
                ),
            }
        )
    hazards.sort(key=lambda h: SEVERITY_RANK[h["severity"]], reverse=True)

    return {
        "report_type": "ppe_safety_audit",
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now_iso(),
        "source": source,
        "model": model,
        "is_construction_site": as_bool(raw.get("is_construction_site"), True),
        "safety_score": score,
        "overall_status": status,
        "workers_detected": as_int(raw.get("workers_detected"), default=0, lo=0),
        "summary": as_str(raw.get("summary"), "No summary provided."),
        "ppe_detection": ppe,
        "hazards": hazards[:15],
        "recommendations": as_str_list(raw.get("recommendations")),
        "confidence": round(as_float(raw.get("confidence"), 0.5, 0.0, 1.0), 2),
    }


# --------------------------------------------------------------------------- #
# Crack diagnostics contract
# --------------------------------------------------------------------------- #
def normalize_crack_report(raw: Mapping[str, Any], source: str = "live", model: Optional[str] = None) -> Dict[str, Any]:
    raw = raw if isinstance(raw, Mapping) else {}
    defect_type = match_choice(raw.get("defect_type"), CRACK_TYPES, "Hairline")
    detected = as_bool(raw.get("defect_detected"), defect_type != "No Defect Detected")
    if not detected:
        defect_type = "No Defect Detected"

    score = as_int(raw.get("severity_score"), default=0, lo=0, hi=100)
    severity = match_choice(raw.get("severity"), SEVERITY_LEVELS, None, SEVERITY_SYNONYMS) or severity_from_score(score)

    width = round(as_float(raw.get("estimated_crack_width_mm"), 0.0, 0.0, 100.0), 2)
    width_range = raw.get("width_range_mm")
    if isinstance(width_range, (list, tuple)) and len(width_range) >= 2:
        low = round(as_float(width_range[0], width, 0.0, 100.0), 2)
        high = round(as_float(width_range[1], width, 0.0, 100.0), 2)
        width_range = [min(low, high), max(low, high)]
    else:
        width_range = [width, width]

    urgency = match_choice(raw.get("urgency"), URGENCY_LEVELS, "Planned", URGENCY_SYNONYMS)

    ranked = []
    for index, entry in enumerate(raw.get("recommended_repairs") or [], start=1):
        if isinstance(entry, str):
            entry = {"method": entry}
        if not isinstance(entry, dict):
            continue
        method = as_str(entry.get("method") or entry.get("name"))
        if not method:
            continue
        explicit = entry.get("priority") is not None
        repair = {
            "method": method,
            "description": as_str(entry.get("description")),
            "materials": as_str(entry.get("materials")),
            "priority": as_int(entry.get("priority"), default=index, lo=1),
        }
        # Explicit priorities win ties against positional defaults; list order breaks the rest.
        ranked.append(((repair["priority"], 0 if explicit else 1, index), repair))
    repairs = [repair for _, repair in sorted(ranked, key=lambda pair: pair[0])]

    return {
        "report_type": "crack_diagnostics",
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now_iso(),
        "source": source,
        "model": model,
        "is_concrete_surface": as_bool(raw.get("is_concrete_surface"), True),
        "defect_detected": detected,
        "defect_type": defect_type,
        "secondary_defects": as_str_list(raw.get("secondary_defects")),
        "crack_pattern": as_str(raw.get("crack_pattern"), "Not specified"),
        "severity": severity,
        "severity_score": score,
        "estimated_crack_width_mm": width,
        "width_range_mm": width_range,
        "within_is456_limit": width <= IS456_CRACK_LIMIT_MM,
        "structural_risk": as_str(raw.get("structural_risk")),
        "root_causes": as_str_list(raw.get("root_causes")),
        "recommended_repairs": repairs[:8],
        "urgency": urgency,
        "urgency_timeframe": as_str(raw.get("urgency_timeframe"), URGENCY_TIMEFRAMES[urgency]),
        "further_investigation": as_str_list(raw.get("further_investigation")),
        "monitoring_plan": as_str(raw.get("monitoring_plan")),
        "summary": as_str(raw.get("summary"), "No summary provided."),
        "confidence": round(as_float(raw.get("confidence"), 0.5, 0.0, 1.0), 2),
    }
