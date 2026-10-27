"""Project budgeting, capital expenditure, asset valuation and material take-off (Epic 3)."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from core.config import (
    LAND_VALUE_SHARE,
    MARKET_RATE_PER_SQFT,
    MATERIALS,
    MILESTONES,
    STRUCTURE_TYPES,
    UNDER_CONSTRUCTION_DISCOUNT,
)


@dataclass(frozen=True)
class ValuationInputs:
    structure_type: str
    built_up_sqft: float
    tier: str
    completion_pct: float
    market_rate_override: Optional[float] = None  # ₹ / sq ft, completed value
    land_cost_inr: float = 0.0
    soft_cost_pct: float = 7.0  # design, approvals, supervision
    contingency_pct: float = 5.0
    include_land_value: bool = True

    def validate(self) -> None:
        if self.structure_type not in STRUCTURE_TYPES:
            raise ValueError(f"Unknown structure type: {self.structure_type}")
        if self.tier not in MARKET_RATE_PER_SQFT:
            raise ValueError(f"Unknown location tier: {self.tier}")
        if self.built_up_sqft <= 0:
            raise ValueError("Built-up area must be greater than zero.")
        if not 0 <= self.completion_pct <= 100:
            raise ValueError("Completion must be between 0 and 100 %.")


def milestone_progress(completion_pct: float) -> List[Dict[str, Any]]:
    """Status of each construction milestone for an overall completion percentage."""
    rows = []
    for name, start, end in MILESTONES:
        if completion_pct >= end:
            status, progress = "Completed", 100.0
        elif completion_pct > start:
            status, progress = "In Progress", (completion_pct - start) / (end - start) * 100
        else:
            status, progress = "Pending", 0.0
        rows.append({"milestone": name, "start_pct": start, "end_pct": end, "status": status, "progress_pct": round(progress, 1)})
    return rows


def current_milestone(completion_pct: float) -> str:
    if completion_pct >= 100:
        return "Handed Over"
    for name, start, end in MILESTONES:
        if start <= completion_pct < end:
            return name
    return MILESTONES[-1][0]


def material_takeoff(structure_type: str, built_up_sqft: float, completion_pct: float) -> List[Dict[str, Any]]:
    """Thumb-rule quantities per sq ft with a front-loaded consumption profile."""
    factors = STRUCTURE_TYPES[structure_type]["materials"]
    progress = completion_pct / 100
    rows = []
    for key, spec in MATERIALS.items():
        total = factors[key] * built_up_sqft
        used_fraction = min(1.0, progress / spec["done_at"]) if spec["done_at"] else 1.0
        used = total * used_fraction
        rows.append(
            {
                "material": spec["label"],
                "key": key,
                "unit": spec["unit"],
                "rate_per_sqft": factors[key],
                "total_required": round(total, 1),
                "consumed_to_date": round(used, 1),
                "balance": round(total - used, 1),
                "unit_rate_inr": spec["rate"],
                "estimated_cost_inr": round(total * spec["rate"]),
                "consumed_pct": round(used_fraction * 100, 1),
            }
        )
    return rows


def compute_valuation(inputs: ValuationInputs) -> Dict[str, Any]:
    inputs.validate()
    spec = STRUCTURE_TYPES[inputs.structure_type]
    progress = inputs.completion_pct / 100
    sqft = inputs.built_up_sqft

    cost_rate = spec["cost_per_sqft"][inputs.tier]
    hard_cost = sqft * cost_rate
    soft_cost = hard_cost * inputs.soft_cost_pct / 100
    contingency = (hard_cost + soft_cost) * inputs.contingency_pct / 100
    total_budget = hard_cost + soft_cost + contingency
    capex_incurred = total_budget * progress  # earned-value basis

    market_rate = inputs.market_rate_override or MARKET_RATE_PER_SQFT[inputs.tier] * spec["market_factor"]
    land_share = LAND_VALUE_SHARE[inputs.tier]
    gross_value = sqft * market_rate
    land_component = gross_value * land_share
    risk_discount = UNDER_CONSTRUCTION_DISCOUNT * (1 - progress)

    if inputs.include_land_value:
        value_on_completion = gross_value
        current_value = (land_component + (gross_value - land_component) * progress) * (1 - risk_discount)
    else:
        value_on_completion = gross_value - land_component
        current_value = value_on_completion * progress * (1 - risk_discount)

    # A land-inclusive value must be compared with a land-inclusive cost. When no
    # acquisition cost is entered, assume the land is held at its market value.
    land_cost_assumed = inputs.include_land_value and not inputs.land_cost_inr
    if inputs.land_cost_inr:
        land_cost_basis = inputs.land_cost_inr
    elif inputs.include_land_value:
        land_cost_basis = land_component
    else:
        land_cost_basis = 0.0
    total_investment = total_budget + land_cost_basis
    projected_margin = value_on_completion - total_investment

    return {
        "report_type": "project_valuation",
        "inputs": asdict(inputs),
        "rates": {
            "construction_cost_per_sqft": cost_rate,
            "market_rate_per_sqft": round(market_rate),
            "land_value_share_pct": round(land_share * 100, 1),
        },
        "cost": {
            "hard_cost": round(hard_cost),
            "soft_cost": round(soft_cost),
            "contingency": round(contingency),
            "total_budget": round(total_budget),
            "capex_incurred": round(capex_incurred),
            "balance_to_complete": round(total_budget - capex_incurred),
            "all_in_cost_per_sqft": round(total_budget / sqft),
        },
        "valuation": {
            "value_on_completion": round(value_on_completion),
            "current_valuation": round(current_value),
            "land_component": round(land_component) if inputs.include_land_value else 0,
            "under_construction_discount_pct": round(risk_discount * 100, 1),
            "value_created_to_date": round(current_value - capex_incurred - land_cost_basis),
        },
        "investment": {
            "land_cost_basis": round(land_cost_basis),
            "land_cost_assumed_at_market": land_cost_assumed,
            "total_investment": round(total_investment),
            "projected_margin": round(projected_margin),
            "roi_pct": round(projected_margin / total_investment * 100, 1) if total_investment else 0.0,
            "cost_to_value_pct": round(total_investment / value_on_completion * 100, 1) if value_on_completion else 0.0,
        },
        "current_milestone": current_milestone(inputs.completion_pct),
        "milestones": milestone_progress(inputs.completion_pct),
        "materials": material_takeoff(inputs.structure_type, sqft, inputs.completion_pct),
    }
