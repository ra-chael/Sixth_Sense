"""Page styling.

Streamlit's default chrome — stock fonts, grey containers, the running-man
toolbar — reads as a script someone is running rather than a product a
caregiver would use. This restyles the shell around the app without changing
any behaviour.
"""

import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
  --brand: #C98A46;
  --ink: #F1E9DE;
  --ink-dim: #AA9C8C;
  --panel: #221D26;
  --panel-2: #2C2530;
  --edge: #3B3340;
}

html, body, [class*="css"], .stApp {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Streamlit's own menu and footer add nothing for a caregiver.
   The toolbar is left alone: the sidebar's expand arrow lives inside it, and
   hiding the toolbar makes a collapsed sidebar impossible to reopen. */
#MainMenu, footer { visibility: hidden; }

/* Keep the collapse control visible and easy to hit. */
div[data-testid="stSidebarCollapsedControl"],
button[data-testid="stSidebarCollapseButton"],
button[kind="header"] {
  visibility: visible !important;
  opacity: 1 !important;
  z-index: 999;
}

.stApp { background: var(--panel); }

/* Title: tighter and larger than the default, so the one thing a caregiver
   reads first actually leads the page. */
h1 {
  font-weight: 700 !important;
  letter-spacing: -0.03em !important;
  font-size: 2.6rem !important;
  background: linear-gradient(92deg, var(--ink) 20%, var(--brand) 120%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

h2, h3 {
  font-weight: 600 !important;
  letter-spacing: -0.015em !important;
  color: var(--ink) !important;
}

section[data-testid="stSidebar"] {
  background: #1B171F;
  border-right: 1px solid var(--edge);
}
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
  font-size: 0.78rem !important;
  text-transform: uppercase;
  letter-spacing: 0.1em !important;
  color: var(--ink-dim) !important;
}

div[data-testid="stTabs"] button {
  font-weight: 500;
  letter-spacing: 0.01em;
}

/* Bordered containers are the event cards; give them real surface. */
div[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--panel-2);
  border: 1px solid var(--edge) !important;
  border-radius: 14px;
}

.stButton button {
  border-radius: 10px;
  font-weight: 550;
  letter-spacing: 0.01em;
  border: 1px solid var(--edge);
  transition: transform 0.12s ease, border-color 0.2s ease;
}
.stButton button:hover {
  transform: translateY(-1px);
  border-color: var(--brand);
}

div[data-testid="stAlert"] { border-radius: 12px; }

.stSlider, .stTextInput input, .stSelectbox { border-radius: 10px; }
.stTextInput input {
  background: var(--panel-2);
  border: 1px solid var(--edge);
}

hr { border-color: var(--edge) !important; }

/* Tighten the gap the hero iframe leaves behind it. */
iframe { display: block; }

/* Tabs read as navigation rather than as a widget. */
div[data-testid="stTabs"] [data-baseweb="tab-list"] {
  gap: 4px;
  border-bottom: 1px solid var(--edge);
}
div[data-testid="stTabs"] [data-baseweb="tab"] {
  padding: 10px 18px;
  border-radius: 10px 10px 0 0;
}
div[data-testid="stTabs"] [aria-selected="true"] {
  background: var(--panel-2);
}

/* Charts and metrics sit on their own surface instead of floating on the
   page background. */
div[data-testid="stVegaLiteChart"],
div[data-testid="stAltairChart"] {
  background: var(--panel-2);
  border: 1px solid var(--edge);
  border-radius: 14px;
  padding: 14px 10px 6px;
}

div[data-testid="stMetric"] {
  background: var(--panel-2);
  border: 1px solid var(--edge);
  border-radius: 12px;
  padding: 12px 14px;
}
div[data-testid="stMetricLabel"] {
  font-size: 0.72rem !important;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--ink-dim) !important;
}
div[data-testid="stMetricValue"] {
  font-variant-numeric: tabular-nums;
  font-weight: 600;
}

/* The event summary is the one place the app speaks in sentences — give it a
   quieter, quote-like treatment so it does not read as an alert. */
div[data-testid="stAlert"] {
  border-radius: 12px;
  border-left: 3px solid var(--brand);
}

section[data-testid="stSidebar"] .stButton button { width: 100%; }

/* Expander headers were indistinguishable from body text. */
details summary { font-weight: 550; }

/* Toggles and radios read as controls, not form fields. */
div[data-testid="stRadio"] label, div[data-testid="stToggle"] label {
  font-size: 0.9rem;
}

h1 + div[data-testid="stCaptionContainer"] { margin-top: -0.4rem; }

/* --- presentation polish ------------------------------------------------ */

/* Give the page room to breathe on a projector, where everything reads
   smaller than it does on a laptop. */
.block-container {
  padding-top: 2.2rem !important;
  max-width: 1500px;
}

/* Section headings get a brand rule, so a viewer can find their place in a
   long scroll without reading. */
h2 {
  font-size: 1.45rem !important;
  padding-bottom: 0.4rem;
  border-bottom: 1px solid var(--edge);
}
h3 { font-size: 1.1rem !important; }

/* The primary action should be the obvious one in a demo. */
.stButton button[kind="primary"] {
  background: var(--brand);
  border-color: var(--brand);
  color: #1B171F;
  font-weight: 650;
}
.stButton button[kind="primary"]:hover {
  filter: brightness(1.08);
  border-color: var(--brand);
}

/* Status pills rather than full-width bars — a running session should read
   at a glance, not shout. */
div[data-testid="stAlert"] {
  padding: 0.7rem 1rem;
  font-size: 0.92rem;
}

/* Sidebar controls sit closer together so the whole setup is visible at once
   without scrolling mid-demo. */
section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] {
  gap: 0.6rem;
}
section[data-testid="stSidebar"] hr { margin: 0.8rem 0; }

/* Charts: remove the doubled border Vega draws inside our own panel. */
div[data-testid="stVegaLiteChart"] canvas,
div[data-testid="stAltairChart"] canvas { border-radius: 8px; }

/* The dataframe reads as part of the page rather than a spreadsheet. */
div[data-testid="stDataFrame"] {
  border: 1px solid var(--edge);
  border-radius: 12px;
  overflow: hidden;
}

/* Captions carry most of the explanation in this app; make them legible
   rather than an afterthought. */
div[data-testid="stCaptionContainer"] p {
  color: var(--ink-dim) !important;
  line-height: 1.5;
}

/* Toggle switches in brand colour when on. */
div[data-testid="stToggle"] [data-baseweb="toggle"][aria-checked="true"] {
  background: var(--brand) !important;
}

/* Tighten the space the hero iframe reserves under itself. */
div[data-testid="stIFrame"] { margin-bottom: -0.6rem; }
</style>
"""


def apply():
    st.markdown(CSS, unsafe_allow_html=True)
