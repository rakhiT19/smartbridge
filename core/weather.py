"""Weather-aware site protocols (Epic 5) and optional live conditions via Open-Meteo."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Tuple

import requests

WEATHER_CONDITIONS = ["Normal", "High Wind", "Heavy Rain", "Extreme Heat"]
WEATHER_ICONS = {"Normal": "☀️", "High Wind": "🌬️", "Heavy Rain": "🌧️", "Extreme Heat": "🔥"}
OPERATION_STATES = ["Go", "Restricted", "Suspended"]

PROTOCOLS: Dict[str, Dict[str, Any]] = {
    "Normal": {
        "risk": "Low",
        "headline": "Standard operating conditions — proceed with the approved work plan.",
        "operations": {
            "Crane & Hoisting": ("Go", "Pre-lift checklist, SWL and load chart verified"),
            "Work at Height": ("Go", "Harness tie-off at ≥ 1.8 m; guardrails in place"),
            "Concreting": ("Go", "Normal pour sequence; slump and cube sampling"),
            "Excavation": ("Go", "Daily inspection of shoring and edge protection"),
            "Electrical & Welding": ("Go", "Hot-work permit; 30 mA RCCB on temporary DBs"),
            "Material Handling": ("Go", "Mechanical aids for loads above 25 kg"),
        },
        "alerts": ["No weather-related restrictions in force today."],
        "protocols": {
            "Safety": [
                "Conduct a 10–15 minute toolbox talk on today's high-risk activities.",
                "Gate check: helmet (IS 2925), safety footwear (IS 15298), hi-vis vest for every worker.",
                "Full-body harness (IS 3521) with 100 % tie-off for work at height ≥ 1.8 m (OSHA 1926.501).",
                "Issue permits-to-work for hot work, confined spaces and excavations deeper than 1.5 m.",
            ],
            "Concrete & Materials": [
                "Moist-cure exposed concrete for ≥ 7 days (OPC) / ≥ 10 days (PPC, blended) — IS 456 cl. 13.5.1.",
                "Cast cube samples at the IS 456 cl. 15.2.2 frequency; record slump for every batch.",
                "Strip formwork only after the periods in IS 456 cl. 11.3.1 (e.g. slab props: 7 days up to 4.5 m span).",
            ],
            "Plant & Electrical": [
                "Complete the daily pre-start inspection for cranes, hoists and the concrete pump.",
                "Inspect temporary cables, earthing pits and distribution boards.",
            ],
        },
    },
    "High Wind": {
        "risk": "High",
        "headline": "High wind advisory — lifting operations and exposed work at height are curtailed.",
        "operations": {
            "Crane & Hoisting": ("Suspended", "Stop lifts once wind exceeds the crane's in-service limit"),
            "Work at Height": ("Suspended", "No work on exposed roof edges, facades or open scaffolds"),
            "Concreting": ("Restricted", "No extended pump booms; protect against rapid evaporation"),
            "Excavation": ("Go", "Watch for dust and falling debris at edges"),
            "Electrical & Welding": ("Restricted", "Secure cables; keep clear of overhead lines"),
            "Material Handling": ("Restricted", "No handling of sheets, panels or glazing (high sail area)"),
        },
        "alerts": [
            "Suspend crane lifting when sustained wind or gusts exceed the manufacturer's in-service limit — read it from the anemometer, not by feel.",
            "Do not hoist personnel platforms when wind exceeds 32 km/h (20 mph) — OSHA 1926.1431.",
            "Secure or lower loose sheets, formwork panels, tarpaulins and scaffold sheeting before the gusts peak.",
        ],
        "protocols": {
            "Safety": [
                "Clear workers from exposed edges and the swing radius of cranes.",
                "Inspect scaffold ties and remove sheeting that increases wind load.",
                "Issue eye protection against wind-blown dust and grit.",
            ],
            "Concrete & Materials": [
                "Erect windbreaks and fog-spray fresh slabs to prevent plastic-shrinkage cracking.",
                "Apply curing compound immediately after finishing; avoid large flatwork pours.",
                "Weigh down or band stacked materials and empty cement bags.",
            ],
            "Plant & Electrical": [
                "Leave tower cranes free to slew (weathervane) when out of service; park mobile crane booms.",
                "Log wind readings hourly; a competent person signs off before lifting resumes.",
            ],
        },
    },
    "Heavy Rain": {
        "risk": "High",
        "headline": "Heavy rain advisory — electrical, excavation-collapse and slip hazards are elevated.",
        "operations": {
            "Crane & Hoisting": ("Restricted", "Suspend in thunderstorms or poor visibility"),
            "Work at Height": ("Suspended", "Wet roofs, slabs and scaffold boards are slip hazards"),
            "Concreting": ("Suspended", "No open pours unless fully covered; protect fresh concrete"),
            "Excavation": ("Restricted", "Competent-person inspection and dewatering before entry"),
            "Electrical & Welding": ("Suspended", "No outdoor welding or work on live temporary supply"),
            "Material Handling": ("Restricted", "Keep cement and steel off the ground and covered"),
        },
        "alerts": [
            "Electrical hazard: isolate outdoor distribution boards and temporary wiring that are not weatherproof; confirm 30 mA RCCB/ELCB protection.",
            "Excavations: inspect shoring, benching and edges for softening before anyone enters — side collapse risk.",
            "Lightning: stop crane and work at height when thunder is heard; resume 30 minutes after the last thunder.",
        ],
        "protocols": {
            "Safety": [
                "Barricade waterlogged areas and open drains; keep site drainage clear.",
                "Check ladder footing and access routes for slippery surfaces; issue gumboots where needed.",
                "Keep first-aid and rescue equipment ready near excavations.",
            ],
            "Concrete & Materials": [
                "Cover freshly placed concrete with polythene/tarpaulin for at least 24 hours.",
                "Adjust batch water for wet aggregates and sand bulking — never add water to a wet mix.",
                "Store cement on raised platforms in a dry shed, stacked no more than 10 bags high (IS 4082).",
            ],
            "Plant & Electrical": [
                "Run dewatering pumps on dedicated, protected circuits.",
                "Shelter generators with open ventilation and keep fuel dry.",
            ],
        },
    },
    "Extreme Heat": {
        "risk": "High",
        "headline": "Heat-wave advisory — heat stress controls and hot-weather concreting are mandatory.",
        "operations": {
            "Crane & Hoisting": ("Go", "Ventilated cabins; monitor hydraulic and engine temperatures"),
            "Work at Height": ("Restricted", "Buddy system; heat exhaustion raises fall risk"),
            "Concreting": ("Restricted", "Pour early morning or at night; control concrete temperature"),
            "Excavation": ("Go", "Shade and water for workers in trenches"),
            "Electrical & Welding": ("Restricted", "Limit welding in direct sun; watch for overheated cables"),
            "Material Handling": ("Restricted", "Rotate manual tasks; frequent rest breaks"),
        },
        "alerts": [
            "Reschedule strenuous work away from 12:00–15:00; enforce water–rest–shade cycles (NDMA heat action guidelines).",
            "Hot-weather concreting: keep fresh concrete at or below 35 °C at placement (ACI 305R; IS 7861 Part 1).",
            "Start curing immediately; extend moist curing to at least 10 days in hot, dry weather (IS 456 cl. 13.5.1).",
        ],
        "protocols": {
            "Safety": [
                "Provide cool drinking water (≈ 250 ml every 15–20 minutes) and ORS at every work front.",
                "Set up shaded rest shelters; acclimatise new workers over the first week.",
                "Train supervisors to spot heat exhaustion and heat stroke; keep the ambulance contact posted.",
            ],
            "Concrete & Materials": [
                "Shade and sprinkle aggregate stockpiles; use chilled water or ice flakes in the mix.",
                "Use retarding admixtures for long hauls; minimise transit and placing time.",
                "Fog-spray and cover with wet hessian immediately after finishing.",
            ],
            "Plant & Electrical": [
                "Check engine coolant levels; refuel only when engines are cool.",
                "Store flammables, gas cylinders and adhesives in shade.",
            ],
        },
    },
}

CITY_COORDINATES: Dict[str, Tuple[float, float]] = {
    "Mumbai": (19.0760, 72.8777),
    "Delhi": (28.6139, 77.2090),
    "Bengaluru": (12.9716, 77.5946),
    "Hyderabad": (17.3850, 78.4867),
    "Chennai": (13.0827, 80.2707),
    "Kolkata": (22.5726, 88.3639),
    "Pune": (18.5204, 73.8567),
    "Ahmedabad": (23.0225, 72.5714),
    "Jaipur": (26.9124, 75.7873),
    "Lucknow": (26.8467, 80.9462),
    "Indore": (22.7196, 75.8577),
    "Kochi": (9.9312, 76.2673),
    "Chandigarh": (30.7333, 76.7794),
    "Nagpur": (21.1458, 79.0882),
    "Bhopal": (23.2599, 77.4126),
    "Coimbatore": (11.0168, 76.9558),
    "Patna": (25.5941, 85.1376),
    "Guwahati": (26.1445, 91.7362),
}

WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast", 45: "Fog", 48: "Rime fog",
    51: "Light drizzle", 53: "Drizzle", 55: "Dense drizzle", 61: "Light rain", 63: "Moderate rain",
    65: "Heavy rain", 80: "Rain showers", 81: "Heavy showers", 82: "Violent showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Severe thunderstorm with hail",
}
HEAVY_RAIN_CODES = {63, 65, 81, 82, 95, 96, 99}

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


class WeatherError(Exception):
    """Raised when live weather cannot be fetched."""


def classify_conditions(temperature_c: float, apparent_c: float, precipitation_mm: float,
                        wind_kmh: float, gust_kmh: float, weather_code: int) -> Tuple[str, str]:
    """Map observed weather onto a site protocol; the most hazardous condition wins."""
    if weather_code in HEAVY_RAIN_CODES or precipitation_mm >= 4:
        return "Heavy Rain", f"{WMO_CODES.get(weather_code, 'Rain')}, {precipitation_mm:.1f} mm/h"
    if wind_kmh >= 40 or gust_kmh >= 55:
        return "High Wind", f"Wind {wind_kmh:.0f} km/h, gusts {gust_kmh:.0f} km/h"
    if temperature_c >= 40 or apparent_c >= 42:
        return "Extreme Heat", f"{temperature_c:.0f} °C (feels like {apparent_c:.0f} °C)"
    return "Normal", "Within normal working thresholds"


def fetch_live_weather(city: str, timeout: int = 10) -> Dict[str, Any]:
    if city not in CITY_COORDINATES:
        raise WeatherError(f"No coordinates configured for {city}.")
    lat, lon = CITY_COORDINATES[city]
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,"
                   "weather_code,wind_speed_10m,wind_gusts_10m",
        "wind_speed_unit": "kmh",
        "timezone": "auto",
    }
    try:
        response = requests.get(OPEN_METEO_URL, params=params, timeout=timeout)
        response.raise_for_status()
        current = response.json()["current"]
    except (requests.RequestException, KeyError, ValueError) as exc:
        raise WeatherError(f"Live weather unavailable ({exc.__class__.__name__}). Use the manual selector.") from exc

    reading = {
        "city": city,
        "temperature_c": float(current.get("temperature_2m") or 0),
        "apparent_c": float(current.get("apparent_temperature") or 0),
        "humidity_pct": float(current.get("relative_humidity_2m") or 0),
        "precipitation_mm": float(current.get("precipitation") or 0),
        "wind_kmh": float(current.get("wind_speed_10m") or 0),
        "gust_kmh": float(current.get("wind_gusts_10m") or 0),
        "weather_code": int(current.get("weather_code") or 0),
        "observed_at": current.get("time") or datetime.now().isoformat(timespec="minutes"),
    }
    reading["description"] = WMO_CODES.get(reading["weather_code"], "Variable conditions")
    reading["condition"], reading["reason"] = classify_conditions(
        reading["temperature_c"], reading["apparent_c"], reading["precipitation_mm"],
        reading["wind_kmh"], reading["gust_kmh"], reading["weather_code"],
    )
    return reading


def daily_protocol_markdown(condition: str, site_notes: Dict[str, str]) -> str:
    """Printable daily site protocol combining weather rules with the latest findings."""
    protocol = PROTOCOLS[condition]
    lines = [
        f"# Daily Site Protocol — {datetime.now():%d %b %Y}",
        f"**Weather condition:** {condition} · **Risk level:** {protocol['risk']}",
        "",
        f"> {protocol['headline']}",
        "",
        "## Operations status",
    ]
    for operation, (state, note) in protocol["operations"].items():
        lines.append(f"- **{operation}:** {state} — {note}")
    lines += ["", "## Critical alerts"] + [f"- {alert}" for alert in protocol["alerts"]]
    for section, items in protocol["protocols"].items():
        lines += ["", f"## {section}"] + [f"- [ ] {item}" for item in items]
    if site_notes:
        lines += ["", "## Open findings from today's AI audits"] + [f"- **{k}:** {v}" for k, v in site_notes.items()]
    lines += ["", "---", "Supervisor sign-off: ____________________  Time: ________"]
    return "\n".join(lines)
