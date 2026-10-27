from core.config import PPE_ITEMS
from core.contracts import match_choice, normalize_crack_report, normalize_ppe_report
from core.demo import SAMPLE_CRACK_REPORT, SAMPLE_PPE_REPORT
from core.llm import LLMError, extract_json

import pytest


def test_match_choice_prefers_longest_and_synonyms():
    statuses = ["Compliant", "Partial", "Non-Compliant", "Not Visible"]
    assert match_choice("non compliant", statuses) == "Non-Compliant"
    assert match_choice("NON-COMPLIANT (2 workers)", statuses) == "Non-Compliant"
    assert match_choice("compliant", statuses) == "Compliant"
    assert match_choice("Moderate", ["Low", "Medium", "High"], synonyms={"moderate": "Medium"}) == "Medium"
    assert match_choice(None, statuses, "Not Visible") == "Not Visible"
    assert match_choice("???", statuses, "Partial") == "Partial"


def test_ppe_normaliser_repairs_messy_output():
    raw = {
        "safety_score": "142",
        "overall_status": "mostly fine",
        "workers_detected": -3,
        "ppe_detection": [
            {"item": "Helmet", "status": "compliant", "workers_compliant": 9, "workers_observed": 4},
            {"item": "High-vis vest", "status": "partial"},
        ],
        "hazards": [
            "Loose debris",
            {"hazard": "Open edge", "severity": "extreme"},
            {"hazard": "Trip hazard", "severity": "minor", "remedy": "Tidy up"},
        ],
        "confidence": 7,
    }
    report = normalize_ppe_report(raw)
    assert report["safety_score"] == 100
    assert report["overall_status"] == "Compliant"  # derived from the clamped score
    assert report["workers_detected"] == 0
    assert set(report["ppe_detection"]) == set(PPE_ITEMS)
    helmet = report["ppe_detection"]["helmet"]
    assert helmet["status"] == "Compliant" and helmet["workers_compliant"] == 4  # clamped to observed
    assert report["ppe_detection"]["high_vis_vest"]["status"] == "Partial"
    assert report["ppe_detection"]["safety_harness"]["status"] == "Not Visible"
    assert [h["severity"] for h in report["hazards"]] == ["Critical", "Medium", "Low"]
    assert report["hazards"][2]["corrective_action"] == "Tidy up"
    assert report["confidence"] == 1.0


def test_ppe_normaliser_handles_garbage():
    report = normalize_ppe_report("not a dict")  # type: ignore[arg-type]
    assert report["safety_score"] == 0
    assert report["overall_status"] == "Critical Violation"
    assert report["hazards"] == []


def test_crack_normaliser_enums_and_limits():
    raw = {
        "defect_type": "diagonal structural shear crack",
        "severity_score": 91,
        "estimated_crack_width_mm": "about 2.5 mm",
        "width_range_mm": [3, 1.5],
        "urgency": "critical",
        "recommended_repairs": ["Epoxy injection", {"method": "RC jacketing", "priority": 1}],
    }
    report = normalize_crack_report(raw)
    assert report["defect_type"] == "Structural Shear"
    assert report["severity"] == "Critical"
    assert report["estimated_crack_width_mm"] == 2.5
    assert report["width_range_mm"] == [1.5, 3.0]
    assert report["within_is456_limit"] is False
    assert report["urgency"] == "Immediate"
    assert report["recommended_repairs"][0]["method"] == "RC jacketing"


def test_crack_no_defect():
    report = normalize_crack_report({"defect_detected": "no", "estimated_crack_width_mm": 0})
    assert report["defect_type"] == "No Defect Detected"
    assert report["within_is456_limit"] is True


def test_samples_satisfy_contracts():
    ppe = normalize_ppe_report(SAMPLE_PPE_REPORT, source="demo")
    crack = normalize_crack_report(SAMPLE_CRACK_REPORT, source="demo")
    assert ppe["overall_status"] == "Non-Compliant" and len(ppe["hazards"]) == 5
    assert crack["defect_type"] == "Settlement" and crack["urgency"] == "Urgent"


def test_extract_json_variants():
    assert extract_json('{"a": 1}') == {"a": 1}
    assert extract_json('```json\n{"a": 2}\n```') == {"a": 2}
    assert extract_json('Here you go: {"a": 3} hope it helps') == {"a": 3}
    assert extract_json('[{"a": 4}]') == {"a": 4}
    with pytest.raises(LLMError):
        extract_json("no json here")
    with pytest.raises(LLMError):
        extract_json("")
