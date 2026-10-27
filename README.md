# 🏗️ Multimodal Construction Intelligence Platform

**Skill Wallet Capstone · Project 1** · Platform ID `6ac4c98d1dcde6d7857c1642`

This Streamlit app supports decisions on construction sites. It audits PPE compliance from site photos, diagnoses concrete cracks, estimates project budgets and asset valuations in INR, and gives weather-aware daily protocols plus an engineering chatbot.

It runs without an API key. In **demonstration mode**, every feature works with clearly labelled sample outputs. Add a Google Gemini key for live multimodal analysis.

| Tab | Epic | What it does |
|---|---|---|
| 🦺 Site Safety & PPE Audit | 2, 4 | Scores PPE compliance (helmet, hi-vis vest, steel-toe boots, harness, gloves, eye protection) against OSHA 1926 / BOCW / IS 2925 / IS 15298 / IS 3521 and lists hazards by severity with remedies. Shows a score ring, metric cards and status pills, and exports JSON. |
| 🧱 Crack Diagnostics | 2, 4 | Classifies the defect (Hairline, Settlement, Structural Shear, Thermal Expansion, Spalling) and estimates crack width in mm. Checks it against the IS 456 cl. 35.3.2 0.3 mm limit, then gives root causes, prioritised repairs (epoxy injection, re-grouting, stitching…), urgency, NDT and monitoring. Includes a Pillow crack-enhancement map. |
| 📐 Planning & Valuation | 3 | Takes structure type, area, Tier 1/2/3 location and a completion slider. Calculates budget, capex incurred, current and on-completion valuation (₹ L / Cr), ROI, a steel/cement/sand/aggregate/brick take-off and a milestone tracker. Generates a Pollinations (Flux) 3D concept render. |
| 🌦️ Site Assistant & Weather | 5 | A High Wind / Heavy Rain / Extreme Heat / Normal selector (or live Open-Meteo weather) drives a Go/Restricted/Suspended status for each site operation, safety alerts and a downloadable daily checklist. It also hosts a multi-turn chatbot grounded in the latest audits. |

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
streamlit run app.py
```

Paste a Gemini API key in the sidebar (get one free at [Google AI Studio](https://aistudio.google.com/apikey)), or leave it blank for demo mode. To preload the key, copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`, or set the `GEMINI_API_KEY` environment variable.

## Deploy to Streamlit Community Cloud (1-click)

1. Push this folder to a GitHub repository. `secrets.toml` is git-ignored.
2. At [share.streamlit.io](https://share.streamlit.io), create an app with main file `app.py` and Python 3.11 or 3.12.
3. Optional: under **App settings → Secrets**, add `GEMINI_API_KEY = "…"`.

No database or extra services are needed. State lives in `st.session_state`.

## Architecture

```
app.py                     entry point: page config, sidebar, tabs, per-tab error guard
core/                      framework-free logic (unit-tested)
  config.py                vocabularies, INR rate tables, milestones, material thumb rules
  llm.py                   Gemini client (google-genai): JSON extraction, friendly errors, chat
  prompts.py               system prompts + task prompts for each module
  contracts.py             JSON data contracts: schemas + normalisers (Epic 4)
  analysis.py              live call → contract, demo sample, or labelled fallback
  imaging.py               Pillow: validation, EXIF fix, downscale, quality checks, crack map
  valuation.py             budget, capex, valuation, ROI, milestones, material take-off
  weather.py               weather protocols, Open-Meteo client, daily checklist export
  rendering.py             Pollinations prompt builder + fetch
  demo.py                  sample reports and offline chatbot knowledge base
ui/                        Streamlit views and HTML components
tests/                     pytest: contracts, valuation, imaging, weather, full-app smoke tests
```

**Request flow:** upload → Pillow pre-processing → Gemini multimodal prompt (domain system instruction + schema) → JSON → normaliser (enum mapping, range clamping, defaults) → UI and downloadable report.

### JSON data contracts

Every model response is normalised before use, so the UI never breaks on malformed output. Both reports carry `report_type`, `schema_version`, `generated_at`, `source` (`live` / `demo` / `fallback`) and `model`.

- **PPE audit:** `safety_score` (0–100), `overall_status`, `workers_detected`, `ppe_detection{helmet, high_vis_vest, steel_toe_boots, safety_harness, gloves, eye_protection}`, `hazards[{hazard, category, severity, location, standard_reference, corrective_action}]`, `recommendations`, `confidence`
- **Crack diagnostics:** `defect_type`, `severity`, `severity_score`, `estimated_crack_width_mm`, `width_range_mm`, `within_is456_limit`, `root_causes`, `recommended_repairs[{method, description, materials, priority}]`, `urgency`, `urgency_timeframe`, `further_investigation`, `monitoring_plan`

## Testing

```bash
pip install -r requirements-dev.txt
pytest
```

There are 35 tests. They cover contract normalisation of messy LLM output, valuation maths, Indian number formatting, Pillow processing and weather classification. They also run end-to-end UI flows through Streamlit's `AppTest`: demo audits, valuation inputs, chat and sidebar navigation.

## Notes and assumptions

- **Model:** the brief names Gemini 1.5, which Google has retired. The app defaults to `gemini-2.5-flash` and also offers `gemini-2.5-pro`, `gemini-2.5-flash-lite`, or any custom model ID.
- **Standards:** IS 456:2000 is the concrete code. It governs the crack module (cl. 35.3.2) and site workmanship (formwork, curing). PPE itself is audited against OSHA 1926, the BOCW Act, IS 2925 (helmets), IS 15298 (footwear) and IS 3521 (harness).
- **Valuation:** rates are indicative 2025-26 averages for each tier and structure type, all editable under *Advanced assumptions*. When land value is included but no land cost is entered, land is assumed held at market value, so ROI is not overstated. These figures support decisions; they do not replace a QS estimate or a registered valuation.
- **Pollinations:** the free tier allows about one image every 45 seconds per IP and adds a watermark. The app reports the rate limit and offers a direct link.
- **Safety:** AI outputs support, and never replace, the judgement of a qualified safety officer or structural engineer.
