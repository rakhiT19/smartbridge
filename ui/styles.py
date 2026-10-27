"""Global CSS. Neutral surfaces use translucent greys and inherit text colour, so every
component reads correctly in both Streamlit's light and dark themes."""
from __future__ import annotations

import streamlit as st

CSS = """
<style>
:root {
  --cip-accent: #2a78d6;
  --cip-accent-strong: #1c5cab;
  --cip-surface: rgba(127, 127, 127, 0.06);
  --cip-border: rgba(127, 127, 127, 0.22);
  --cip-track: rgba(127, 127, 127, 0.18);
  --cip-radius: 12px;
}
.cip-tone-good     { --tone: #0ca30c; --tone-bg: rgba(12, 163, 12, 0.11);  --tone-border: rgba(12, 163, 12, 0.35);  --tone-ink: #ffffff; }
.cip-tone-warning  { --tone: #fab219; --tone-bg: rgba(250, 178, 25, 0.14); --tone-border: rgba(250, 178, 25, 0.50); --tone-ink: #1a1a19; }
.cip-tone-serious  { --tone: #ec835a; --tone-bg: rgba(236, 131, 90, 0.14); --tone-border: rgba(236, 131, 90, 0.50); --tone-ink: #1a1a19; }
.cip-tone-critical { --tone: #d03b3b; --tone-bg: rgba(208, 59, 59, 0.11);  --tone-border: rgba(208, 59, 59, 0.40);  --tone-ink: #ffffff; }
.cip-tone-neutral  { --tone: #898781; --tone-bg: rgba(137, 135, 129, 0.10); --tone-border: rgba(137, 135, 129, 0.35); --tone-ink: #ffffff; }
.cip-tone-accent   { --tone: #2a78d6; --tone-bg: rgba(42, 120, 214, 0.10); --tone-border: rgba(42, 120, 214, 0.35); --tone-ink: #ffffff; }

[data-testid="stMainBlockContainer"], .block-container { padding-top: 2.2rem; max-width: 1320px; }
button[data-baseweb="tab"] p { font-size: 0.98rem; font-weight: 600; }
[data-testid="stFileUploaderDropzone"] { border: 1.5px dashed var(--cip-border); border-radius: var(--cip-radius); }

/* Hero ---------------------------------------------------------------- */
.cip-hero {
  position: relative; overflow: hidden; border-radius: 16px; padding: 26px 30px 32px; margin-bottom: 1rem; color: #f6f8fc;
  background:
    linear-gradient(rgba(255,255,255,.055) 1px, transparent 1px) 0 0 / 28px 28px,
    linear-gradient(90deg, rgba(255,255,255,.055) 1px, transparent 1px) 0 0 / 28px 28px,
    linear-gradient(135deg, #0d366b 0%, #184f95 58%, #1c5cab 100%);
}
.cip-hero::after {
  content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 6px;
  background: repeating-linear-gradient(-45deg, #fab219 0 14px, #1a1a19 14px 28px);
}
.cip-eyebrow { font-size: .74rem; letter-spacing: .12em; text-transform: uppercase; font-weight: 600; opacity: .82; }
.cip-hero-title { font-size: clamp(1.45rem, 2.6vw, 2.2rem); font-weight: 800; line-height: 1.15; margin: .35rem 0 .45rem; color: #fff; }
.cip-hero-sub { opacity: .88; max-width: 780px; font-size: .97rem; line-height: 1.5; }
.cip-hero-chips { display: flex; flex-wrap: wrap; gap: .5rem; margin-top: 1rem; }
.cip-chip {
  display: inline-flex; align-items: center; gap: .45rem; font-size: .78rem; font-weight: 600; color: #fff;
  padding: .3rem .75rem; border-radius: 999px; background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.24);
}
.cip-chip i { width: 8px; height: 8px; border-radius: 50%; background: var(--tone); display: inline-block; }

/* Brand (sidebar) ---------------------------------------------------- */
.cip-brand { display: flex; align-items: center; gap: .7rem; margin: .2rem 0 .9rem; }
.cip-brand-mark {
  width: 42px; height: 42px; border-radius: 10px; display: grid; place-items: center; font-size: 1.35rem;
  background: linear-gradient(135deg, #0d366b, #1c5cab); box-shadow: inset 0 -4px 0 #fab219;
}
.cip-brand-name { font-weight: 800; font-size: 1rem; line-height: 1.15; }
.cip-brand-sub { font-size: .76rem; opacity: .7; }
.cip-nav-status { font-size: .76rem; opacity: .78; margin: -0.35rem 0 .55rem .2rem; }

/* Cards & metrics ----------------------------------------------------- */
.cip-card { background: var(--cip-surface); border: 1px solid var(--cip-border); border-radius: var(--cip-radius); padding: 14px 16px; }
.cip-kpi-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; margin: .25rem 0 1rem; }
.cip-metric { position: relative; overflow: hidden; }
.cip-metric[class*="cip-tone-"]::before { content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 4px; background: var(--tone); }
.cip-metric-label { font-size: .72rem; text-transform: uppercase; letter-spacing: .06em; font-weight: 600; opacity: .7; }
.cip-metric-value { font-size: 1.55rem; font-weight: 750; line-height: 1.2; margin-top: .25rem; }
.cip-metric-value small { font-size: .85rem; font-weight: 600; opacity: .65; margin-left: .15rem; }
.cip-metric-sub { font-size: .8rem; opacity: .72; margin-top: .25rem; }

.cip-section { margin: 1.3rem 0 .6rem; }
.cip-section-title { font-size: 1.08rem; font-weight: 700; }
.cip-section-sub { font-size: .85rem; opacity: .7; margin-top: .1rem; }

/* Pills ----------------------------------------------------------------- */
.cip-pill {
  display: inline-flex; align-items: center; gap: .38rem; padding: .18rem .62rem .18rem .3rem; border-radius: 999px;
  font-size: .76rem; font-weight: 650; white-space: nowrap; background: var(--tone-bg); border: 1px solid var(--tone-border);
}
.cip-pill b {
  display: inline-grid; place-items: center; width: 16px; height: 16px; border-radius: 50%;
  font-size: .62rem; font-weight: 800; color: var(--tone-ink); background: var(--tone);
}

/* Score ring ------------------------------------------------------------ */
.cip-ring { --size: 148px; width: var(--size); height: var(--size); position: relative; display: grid; place-items: center; margin: 4px auto 8px; }
.cip-ring::before {
  content: ""; position: absolute; inset: 0; border-radius: 50%;
  background: conic-gradient(var(--tone) calc(var(--pct) * 1%), var(--cip-track) 0);
  -webkit-mask: radial-gradient(farthest-side, transparent calc(100% - 13px), #000 calc(100% - 12px));
          mask: radial-gradient(farthest-side, transparent calc(100% - 13px), #000 calc(100% - 12px));
}
.cip-ring-inner { text-align: center; }
.cip-ring-value { font-size: 2.3rem; font-weight: 800; line-height: 1; }
.cip-ring-cap { font-size: .7rem; opacity: .7; text-transform: uppercase; letter-spacing: .07em; margin-top: .3rem; }

/* Meter ----------------------------------------------------------------- */
.cip-meter { height: 8px; border-radius: 4px; background: var(--cip-track); overflow: hidden; }
.cip-meter > span { display: block; height: 100%; border-radius: 4px; background: var(--tone, var(--cip-accent)); }
.cip-meter-row { display: flex; justify-content: space-between; gap: .5rem; font-size: .84rem; margin-bottom: .3rem; }
.cip-meter-row span:last-child { font-variant-numeric: tabular-nums; opacity: .8; white-space: nowrap; }
.cip-meter-block { margin-bottom: .75rem; }

/* Lists: checklist, hazards, repairs -------------------------------------- */
.cip-check { display: flex; align-items: center; gap: .8rem; padding: .65rem .2rem; border-bottom: 1px solid rgba(127,127,127,.13); }
.cip-check:last-child { border-bottom: none; }
.cip-check-main { flex: 1; min-width: 0; }
.cip-check-title { font-weight: 650; font-size: .92rem; }
.cip-check-notes { font-size: .8rem; opacity: .72; }
.cip-check-count { font-variant-numeric: tabular-nums; font-size: .85rem; opacity: .8; white-space: nowrap; }

.cip-hazard { position: relative; padding-left: 20px; margin-bottom: 10px; }
.cip-hazard::before { content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 4px; border-radius: 12px 0 0 12px; background: var(--tone); }
.cip-hazard-head { display: flex; justify-content: space-between; align-items: flex-start; gap: .6rem; }
.cip-hazard-title { font-weight: 700; font-size: .95rem; }
.cip-hazard-meta { font-size: .78rem; opacity: .7; margin: .15rem 0 .45rem; }
.cip-hazard-body { font-size: .86rem; line-height: 1.45; }
.cip-hazard-ref { font-size: .76rem; opacity: .7; margin-top: .4rem; }

.cip-step { display: flex; gap: .8rem; margin-bottom: 10px; }
.cip-step-num {
  flex: none; width: 28px; height: 28px; border-radius: 50%; display: grid; place-items: center;
  font-weight: 800; font-size: .82rem; color: #fff; background: var(--cip-accent-strong);
}
.cip-step-title { font-weight: 700; font-size: .93rem; }
.cip-step-body { font-size: .85rem; line-height: 1.45; opacity: .9; }
.cip-step-mat { font-size: .78rem; opacity: .7; margin-top: .25rem; }

.cip-bullets { margin: .2rem 0 0; padding-left: 1.1rem; font-size: .88rem; line-height: 1.55; }

/* Alert banner ----------------------------------------------------------- */
.cip-alert {
  display: flex; gap: .85rem; align-items: flex-start; border-radius: var(--cip-radius); padding: 14px 16px; margin: .2rem 0 .9rem;
  background: var(--tone-bg); border: 1px solid var(--tone-border);
}
.cip-alert-icon { font-size: 1.5rem; line-height: 1; }
.cip-alert-title { font-weight: 750; font-size: .98rem; }
.cip-alert-body { font-size: .86rem; opacity: .9; margin-top: .15rem; }

/* Operations grid --------------------------------------------------------- */
.cip-ops { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 270px), 1fr)); gap: 10px; margin-bottom: 1rem; }
.cip-op-head { display: flex; justify-content: space-between; align-items: center; gap: .5rem; margin-bottom: .35rem; }
.cip-op-name { font-weight: 700; font-size: .9rem; }
.cip-op-note { font-size: .8rem; opacity: .75; line-height: 1.4; }

/* Stacked bar ----------------------------------------------------------- */
.cip-stack { display: flex; gap: 2px; height: 14px; margin-top: .3rem; }
.cip-stack > span { display: block; height: 100%; min-width: 3px; }
.cip-stack > span:first-child { border-radius: 4px 0 0 4px; }
.cip-stack > span:last-child { border-radius: 0 4px 4px 0; }
.cip-legend { display: flex; flex-wrap: wrap; gap: .45rem 1.2rem; margin-top: .65rem; font-size: .83rem; }
.cip-legend span { display: inline-flex; align-items: center; gap: .4rem; }
.cip-legend i { width: 10px; height: 10px; border-radius: 2px; display: inline-block; }
.cip-legend em { font-style: normal; opacity: .7; font-variant-numeric: tabular-nums; }

/* Table ------------------------------------------------------------------- */
.cip-table-wrap { overflow-x: auto; }
.cip-table { width: 100%; border-collapse: collapse; font-size: .86rem; }
.cip-table th {
  text-align: left; font-size: .7rem; text-transform: uppercase; letter-spacing: .05em; font-weight: 600; opacity: .7;
  padding: .5rem .6rem; border-bottom: 1px solid var(--cip-border); white-space: nowrap;
}
.cip-table td { padding: .55rem .6rem; border-bottom: 1px solid rgba(127,127,127,.12); font-variant-numeric: tabular-nums; vertical-align: middle; }
.cip-table .num { text-align: right; white-space: nowrap; }
.cip-table tr:last-child td { border-bottom: none; }
.cip-table .cip-meter { min-width: 80px; height: 6px; }

.cip-footnote { font-size: .76rem; opacity: .65; margin-top: .4rem; }
.cip-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 12px; margin-top: .6rem; }
.cip-stats span { display: block; font-size: .74rem; opacity: .7; }
.cip-stats b { display: block; font-size: 1.3rem; font-weight: 750; margin-top: .1rem; }
.cip-snapshot-foot { display: flex; align-items: center; flex-wrap: wrap; gap: .3rem .6rem; margin-top: .75rem; }
.cip-snapshot-foot .cip-footnote { margin-top: 0; }
.cip-empty { text-align: center; padding: 34px 20px; opacity: .8; }
.cip-empty-icon { font-size: 2.2rem; }
.cip-empty-title { font-weight: 700; margin-top: .4rem; }
.cip-empty-body { font-size: .86rem; opacity: .8; margin-top: .2rem; }
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
