"""Static configuration, domain vocabularies and reference rates.

All monetary figures are indicative Indian market averages (INR, 2025-26) intended
for early-stage decision support, not for tendering or statutory valuation.
"""
from __future__ import annotations

# --------------------------------------------------------------------------- #
# Application identity
# --------------------------------------------------------------------------- #
APP_NAME = "Multimodal Construction Intelligence Platform"
APP_TAGLINE = (
    "AI decision support for site safety, structural health, project economics "
    "and weather-aware daily operations."
)
PROJECT_LABEL = "Skill Wallet Capstone · Project 1"
PLATFORM_ID = "6ac4c98d1dcde6d7857c1642"
APP_VERSION = "1.0.0"

TAB_PPE = "🦺 Site Safety & PPE Audit"
TAB_CRACK = "🧱 Crack Diagnostics"
TAB_PLANNING = "📐 Planning & Valuation"
TAB_ASSISTANT = "🌦️ Site Assistant & Weather"
TAB_LABELS = [TAB_PPE, TAB_CRACK, TAB_PLANNING, TAB_ASSISTANT]

# --------------------------------------------------------------------------- #
# Multimodal LLM
# --------------------------------------------------------------------------- #
GEMINI_MODELS = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.5-flash-lite"]
DEFAULT_MODEL = GEMINI_MODELS[0]
CUSTOM_MODEL_OPTION = "Custom model ID…"
LLM_TIMEOUT_SECONDS = 120

# --------------------------------------------------------------------------- #
# Image handling
# --------------------------------------------------------------------------- #
ACCEPTED_IMAGE_TYPES = ["jpg", "jpeg", "png"]
MAX_UPLOAD_MB = 10
MAX_IMAGE_SIDE = 1600  # px; images are downscaled before upload to the LLM

# --------------------------------------------------------------------------- #
# Shared vocabularies (JSON contract enums)
# --------------------------------------------------------------------------- #
SEVERITY_LEVELS = ["Low", "Medium", "High", "Critical"]
SEVERITY_RANK = {level: rank for rank, level in enumerate(SEVERITY_LEVELS)}
SEVERITY_SYNONYMS = {
    "minor": "Low",
    "negligible": "Low",
    "moderate": "Medium",
    "major": "High",
    "severe": "High",
    "serious": "High",
    "extreme": "Critical",
    "dangerous": "Critical",
}

OVERALL_STATUSES = ["Compliant", "Needs Attention", "Non-Compliant", "Critical Violation"]
PPE_STATUSES = ["Compliant", "Partial", "Non-Compliant", "Not Visible"]
PPE_ITEMS = {
    "helmet": "Safety Helmet",
    "high_vis_vest": "High-Vis Vest",
    "steel_toe_boots": "Steel-Toe Boots",
    "safety_harness": "Safety Harness",
    "gloves": "Hand Gloves",
    "eye_protection": "Eye Protection",
}

CRACK_TYPES = [
    "Hairline",
    "Settlement",
    "Structural Shear",
    "Thermal Expansion",
    "Spalling",
    "No Defect Detected",
]
URGENCY_LEVELS = ["Routine", "Planned", "Urgent", "Immediate"]
URGENCY_SYNONYMS = {
    "low": "Routine",
    "monitor": "Routine",
    "medium": "Planned",
    "moderate": "Planned",
    "high": "Urgent",
    "priority": "Urgent",
    "critical": "Immediate",
    "emergency": "Immediate",
}
URGENCY_TIMEFRAMES = {
    "Routine": "Monitor at the next scheduled inspection (3–6 months)",
    "Planned": "Schedule repair within 30 days",
    "Urgent": "Repair within 7 days; monitor crack width weekly",
    "Immediate": "Restrict access and engage a structural engineer within 24–48 hours",
}
STRUCTURAL_ELEMENTS = [
    "Wall (masonry / plastered)",
    "RCC Beam",
    "RCC Column",
    "RCC Slab / Ceiling",
    "Foundation / Plinth",
    "Retaining Wall",
    "Pavement / Floor",
]
# IS 456:2000 cl. 35.3.2 — general limit on surface crack width.
IS456_CRACK_LIMIT_MM = 0.3

# --------------------------------------------------------------------------- #
# Planning & real-estate valuation reference data
# --------------------------------------------------------------------------- #
LOCATION_TIERS = {
    "Tier 1": "Mumbai, Delhi NCR, Bengaluru, Hyderabad, Chennai, Pune, Kolkata, Ahmedabad",
    "Tier 2": "Jaipur, Lucknow, Indore, Kochi, Chandigarh, Coimbatore, Nagpur, Bhopal",
    "Tier 3": "District towns and emerging urban centres",
}
# Completed residential market rate (₹ / sq ft of built-up area, land inclusive).
MARKET_RATE_PER_SQFT = {"Tier 1": 11000, "Tier 2": 5800, "Tier 3": 3600}
# Share of completed market value attributable to land and location.
LAND_VALUE_SHARE = {"Tier 1": 0.45, "Tier 2": 0.35, "Tier 3": 0.25}
# Risk discount applied to unfinished assets; tapers linearly to 0 at 100 % completion.
UNDER_CONSTRUCTION_DISCOUNT = 0.12

STRUCTURE_TYPES = {
    "Residential – Independent House (G+1 / G+2)": {
        "cost_per_sqft": {"Tier 1": 2400, "Tier 2": 2000, "Tier 3": 1700},
        "market_factor": 1.00,
        "materials": {"steel": 4.0, "cement": 0.40, "sand": 1.80, "aggregate": 1.35, "bricks": 8.0},
        "render_subject": "independent family house",
    },
    "Residential – Apartment (Mid / High-Rise)": {
        "cost_per_sqft": {"Tier 1": 2800, "Tier 2": 2300, "Tier 3": 1950},
        "market_factor": 1.00,
        "materials": {"steel": 4.5, "cement": 0.45, "sand": 1.80, "aggregate": 1.40, "bricks": 7.0},
        "render_subject": "multi-storey residential apartment tower",
    },
    "Premium Villa": {
        "cost_per_sqft": {"Tier 1": 4200, "Tier 2": 3400, "Tier 3": 2800},
        "market_factor": 1.35,
        "materials": {"steel": 4.2, "cement": 0.42, "sand": 1.85, "aggregate": 1.35, "bricks": 8.0},
        "render_subject": "luxury villa with landscaped garden and pool",
    },
    "Commercial – Office / Retail": {
        "cost_per_sqft": {"Tier 1": 3400, "Tier 2": 2800, "Tier 3": 2300},
        "market_factor": 1.25,
        "materials": {"steel": 5.0, "cement": 0.50, "sand": 1.70, "aggregate": 1.50, "bricks": 5.0},
        "render_subject": "commercial office and retail building with glass facade",
    },
    "Industrial – Warehouse / Shed (PEB)": {
        "cost_per_sqft": {"Tier 1": 1900, "Tier 2": 1650, "Tier 3": 1450},
        "market_factor": 0.55,
        "materials": {"steel": 6.0, "cement": 0.25, "sand": 0.90, "aggregate": 0.80, "bricks": 2.0},
        "render_subject": "pre-engineered steel warehouse with loading docks",
    },
    "Institutional – School / Hospital": {
        "cost_per_sqft": {"Tier 1": 3200, "Tier 2": 2700, "Tier 3": 2250},
        "market_factor": 0.90,
        "materials": {"steel": 4.8, "cement": 0.48, "sand": 1.75, "aggregate": 1.45, "bricks": 6.0},
        "render_subject": "institutional campus building",
    },
}

# Thumb-rule material schedule. `done_at` = fraction of overall progress by which the
# material is fully consumed (structural items are front-loaded, finishes back-loaded).
MATERIALS = {
    "steel": {"label": "TMT Steel (Fe 500D)", "unit": "kg", "rate": 62.0, "done_at": 0.55},
    "cement": {"label": "Cement (OPC 53 / PPC)", "unit": "bags", "rate": 400.0, "done_at": 0.85},
    "sand": {"label": "Sand (river / M-sand)", "unit": "cft", "rate": 55.0, "done_at": 0.90},
    "aggregate": {"label": "Coarse Aggregate (20 mm)", "unit": "cft", "rate": 45.0, "done_at": 0.60},
    "bricks": {"label": "Bricks / Blocks", "unit": "nos", "rate": 9.0, "done_at": 0.70},
}

MILESTONES = [
    ("Site Preparation & Excavation", 0, 8),
    ("Foundation & Plinth", 8, 20),
    ("RCC Superstructure (Frame & Slabs)", 20, 50),
    ("Masonry & Walling", 50, 65),
    ("MEP Rough-in", 65, 78),
    ("Plastering & Flooring", 78, 90),
    ("Finishing & Handover", 90, 100),
]

# --------------------------------------------------------------------------- #
# Conceptual rendering (Pollinations AI)
# --------------------------------------------------------------------------- #
POLLINATIONS_ENDPOINT = "https://image.pollinations.ai/prompt/"
ARCH_STYLES = [
    "Contemporary Indian",
    "Modern Minimalist",
    "Tropical Modern",
    "Neo-Classical",
    "Industrial Brutalist",
    "Sustainable Green Building",
]
RENDER_VIEWS = ["Aerial three-quarter view", "Street-level perspective", "Front elevation", "Dusk hero shot"]
TIME_OF_DAY = ["Golden hour", "Bright midday", "Blue hour dusk", "Overcast soft light"]
