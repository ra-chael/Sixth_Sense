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

/* Streamlit's own toolbar and footer add nothing for a caregiver. */
#MainMenu, footer, header [data-testid="stToolbar"] { visibility: hidden; }

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
</style>
"""


def apply():
    st.markdown(CSS, unsafe_allow_html=True)
