import pytest

from core.formatting import format_inr, format_quantity, indian_grouping
from core.valuation import ValuationInputs, compute_valuation, current_milestone, milestone_progress

HOUSE = "Residential – Independent House (G+1 / G+2)"


def test_indian_formatting():
    assert indian_grouping(1234567) == "12,34,567"
    assert indian_grouping(999) == "999"
    assert indian_grouping(-100000) == "-1,00,000"
    assert format_inr(2.5e7) == "₹2.50 Cr"
    assert format_inr(4.56e5) == "₹4.56 L"
    assert format_inr(85000) == "₹85,000"
    assert format_inr(-3e5) == "-₹3.00 L"
    assert format_quantity(9600, "kg") == "9.60 MT"
    assert format_quantity(960, "bags") == "960 bags"


def test_budget_and_valuation_maths():
    result = compute_valuation(ValuationInputs(HOUSE, 2400, "Tier 2", 50))
    cost = result["cost"]
    assert cost["hard_cost"] == 2400 * 2000
    assert cost["soft_cost"] == round(4_800_000 * 0.07)
    assert cost["total_budget"] == round((4_800_000 * 1.07) * 1.05)
    assert cost["capex_incurred"] == round(cost["total_budget"] * 0.5)

    gross = 2400 * 5800
    land = gross * 0.35
    discount = 0.12 * 0.5
    expected = (land + (gross - land) * 0.5) * (1 - discount)
    assert result["valuation"]["current_valuation"] == round(expected)
    assert result["valuation"]["value_on_completion"] == gross


def test_land_inclusive_value_is_compared_with_land_inclusive_cost():
    assumed = compute_valuation(ValuationInputs(HOUSE, 2400, "Tier 1", 45))
    investment = assumed["investment"]
    assert investment["land_cost_assumed_at_market"] is True
    assert investment["land_cost_basis"] == assumed["valuation"]["land_component"]
    assert 0 < investment["roi_pct"] < 100  # a land-free cost basis would report ~300 %

    entered = compute_valuation(ValuationInputs(HOUSE, 2400, "Tier 1", 45, land_cost_inr=5e6))
    assert entered["investment"]["land_cost_assumed_at_market"] is False
    assert entered["investment"]["total_investment"] == entered["cost"]["total_budget"] + 5_000_000


def test_completed_project_has_no_discount():
    result = compute_valuation(ValuationInputs(HOUSE, 1000, "Tier 1", 100))
    assert result["valuation"]["under_construction_discount_pct"] == 0
    assert result["valuation"]["current_valuation"] == result["valuation"]["value_on_completion"]
    assert result["current_milestone"] == "Handed Over"
    assert all(m["status"] == "Completed" for m in result["milestones"])


def test_structure_only_valuation_and_override():
    result = compute_valuation(
        ValuationInputs(HOUSE, 1000, "Tier 3", 0, market_rate_override=5000, include_land_value=False, land_cost_inr=1e6)
    )
    assert result["rates"]["market_rate_per_sqft"] == 5000
    assert result["valuation"]["current_valuation"] == 0
    assert result["investment"]["total_investment"] == result["cost"]["total_budget"] + 1_000_000


def test_milestones_and_materials():
    rows = milestone_progress(35)
    statuses = [row["status"] for row in rows]
    assert statuses[:2] == ["Completed", "Completed"]
    assert statuses[2] == "In Progress" and rows[2]["progress_pct"] == 50.0
    assert set(statuses[3:]) == {"Pending"}
    assert current_milestone(0) == "Site Preparation & Excavation"

    result = compute_valuation(ValuationInputs(HOUSE, 1000, "Tier 1", 55))
    steel = next(row for row in result["materials"] if row["key"] == "steel")
    assert steel["total_required"] == 4000
    assert steel["consumed_pct"] == 100.0  # structural steel fully consumed once the frame is done
    assert steel["balance"] == 0


@pytest.mark.parametrize(
    "kwargs",
    [
        {"structure_type": "Spaceship"},
        {"tier": "Tier 9"},
        {"built_up_sqft": 0},
        {"completion_pct": 120},
    ],
)
def test_invalid_inputs(kwargs):
    base = {"structure_type": HOUSE, "built_up_sqft": 1000, "tier": "Tier 1", "completion_pct": 10}
    base.update(kwargs)
    with pytest.raises(ValueError):
        compute_valuation(ValuationInputs(**base))
