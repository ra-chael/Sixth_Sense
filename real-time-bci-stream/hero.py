"""The animated hero card.

Streamlit cannot crossfade a gradient, breathe an orb or play a tone, so the
card is a self-contained HTML/JS island that Python drives by handing it a
state on each rerun. It keeps its own previous state in sessionStorage so it
can tell a shift from a repaint and only chime on a real change.
"""

import base64
import functools
import json
import os

# components.html is deprecated in favour of st.iframe, but st.iframe only
# accepts a URL or a Path — it cannot take an HTML string, and this card is
# generated per rerun. Keeping components.html until there is a string-capable
# replacement.
import streamlit.components.v1 as components

ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

# Per-state artwork, inlined as data URIs because the card runs in a sandboxed
# iframe with no filesystem access.
#
# Currently empty: the drawn face is used instead, because it is driven
# continuously by valence and arousal rather than snapping between three fixed
# pictures — the expression can be read back as the values that produced it.
# Putting filenames here (they are in assets/) switches back to artwork.
STATE_IMAGE = {}


@functools.lru_cache(maxsize=8)
def _data_uri(filename):
    """Base64 data URI for an asset, or None when it is missing."""
    path = os.path.join(ASSET_DIR, filename)
    try:
        with open(path, "rb") as handle:
            encoded = base64.b64encode(handle.read()).decode()
    except OSError:
        return None
    return f"data:image/png;base64,{encoded}"


STATE_STYLE = {
    "Stable": {
        "core": "#6E9CBD",
        "coreDark": "#7FAFCF",
        "gradA": "#CFE1EC",
        "gradB": "#E7F1F5",
        "gradADark": "#1E4257",
        "gradBDark": "#141E2B",
        "breath": 4.5,
        "label": "Stable",
        "description": "Signals are steady and settled.",
    },
    "Moderate": {
        "core": "#A57FC0",
        "coreDark": "#BF9BD6",
        "gradA": "#E7D9EF",
        "gradB": "#F5EBBE",
        "gradADark": "#4A2F63",
        "gradBDark": "#2A2418",
        "breath": 3.4,
        "label": "Moderate",
        "description": "The reading has turned negative. Worth a look.",
    },
    "Extreme": {
        "core": "#CC8377",
        "coreDark": "#DE9788",
        "gradA": "#EFD1CB",
        "gradB": "#F8E4DF",
        "gradADark": "#6B2F26",
        "gradBDark": "#2B1714",
        "breath": 2.6,
        "label": "Extreme",
        "description": "Sustained activation with a strongly negative tone.",
    },
}

HEIGHT = 430


def render(
    state,
    valence,
    arousal,
    quality,
    muted,
    night,
    elapsed,
    calibrated=True,
    stale=False,
):
    payload = json.dumps(
        {
            "state": state,
            "valence": valence,
            "arousal": arousal,
            "quality": quality,
            "muted": bool(muted),
            "night": bool(night),
            "elapsed": elapsed,
            "calibrated": bool(calibrated),
            "stale": bool(stale),
            "styles": STATE_STYLE,
            "images": {s: _data_uri(f) for s, f in STATE_IMAGE.items()},
        }
    )
    html = _HTML.replace("__PAYLOAD__", payload)

    # A marker that changes with the state. Streamlit keys a component on its
    # html, so two renders that differ only inside the JSON can be treated as
    # the same document and the script never re-runs — which looks like the
    # mascot refusing to change.
    html = html.replace(
        "<!--STATE-->", f"<!-- {state} {elapsed} {'stale' if stale else ''} -->"
    )

    components.html(html, height=HEIGHT)


_HTML = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<!--STATE-->
<style>
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  }

  #card {
    position: relative;
    height: 410px;
    border-radius: 20px;
    overflow: hidden;
    border: 1px solid var(--border);
    --border: #E8DFD1;
    --text: #332B24;
    --text-dim: #7A6D5F;
  }
  #card.night {
    --border: #3B3340;
    --text: #F1E9DE;
    --text-dim: #AA9C8C;
  }

  /* Two stacked gradient layers; a shift crossfades between them, because
     background-image itself does not tween. */
  .layer {
    position: absolute;
    inset: 0;
    opacity: 0;
    transition: opacity 1.4s ease;
  }
  .layer.on { opacity: 1; }

  #inner {
    position: relative;
    height: 100%;
    display: flex;
    align-items: center;
    gap: 34px;
    padding: 0 38px;
    color: var(--text);
  }

  #orbwrap { flex: 0 0 auto; position: relative; width: 168px; height: 168px; }
  #orb {
    position: absolute;
    inset: 0;
    border-radius: 50%;
    transition: background 1.2s ease, box-shadow 1.2s ease;
    animation: breathe var(--breath, 4.5s) ease-in-out infinite;
  }
  @keyframes breathe {
    0%, 100% { transform: scale(1); }
    50%      { transform: scale(1.06); }
  }
  /* Each mascot ships already coloured for its state, so a change crossfades
     one tinted image into the next and the artwork carries the same colour
     signal as the gradient and the charts. */
  .mascot {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    object-fit: contain;
    opacity: 0;
    transition: opacity 1.2s ease, filter 1.2s ease;
    animation: breathe var(--breath, 4.5s) ease-in-out infinite;
  }
  .mascot.on { opacity: 1; }

  #face { position: absolute; inset: 0; }
  /* The face is redrawn each tick; easing the geometry keeps it morphing
     rather than jumping between readings. */
  #eyeL, #eyeR { transition: rx 0.9s ease, ry 0.9s ease; }
  #browL, #browR { transition: opacity 0.9s ease, d 0.9s ease; }
  #mouth { transition: d 0.9s ease; }

  #label {
    font-size: 40px;
    font-weight: 600;
    letter-spacing: -0.02em;
    margin: 0 0 4px;
  }
  #desc { color: var(--text-dim); font-size: 15px; margin: 0 0 20px; }

  #stats { display: flex; gap: 30px; }
  .stat .k {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: var(--text-dim);
  }
  .stat .v { font-size: 21px; font-weight: 600; font-variant-numeric: tabular-nums; }

  #bar {
    margin-top: 16px;
    height: 5px;
    width: 250px;
    border-radius: 3px;
    background: rgba(128,128,128,0.22);
    overflow: hidden;
  }
  #fill { height: 100%; width: 0%; border-radius: 3px; transition: width 1s ease, background 1.2s ease; }

  /* Head map. EEG localises to the scalp and nothing else, so the diagram
     shows a head only — the glow tracks intensity, never a body region we
     cannot actually measure. */
  /* The outline needs its own colour rather than inheriting the dim body
     text, which vanished against the card's own background. */
  #headwrap {
    flex: 0 0 auto;
    margin-left: auto;
    text-align: center;
    color: var(--text);
    opacity: 0.85;
  }
  @media (max-width: 720px) { #headwrap { display: none; } }
  #headwrap .cap {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 6px;
  }
  #glow { transition: opacity 1s ease, r 1s ease, fill 1.2s ease; }
  .site { transition: opacity 1s ease, fill 1.2s ease; }

  #uncal {
    position: absolute;
    top: 14px;
    right: 18px;
    font-size: 10px;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 4px 9px;
    border-radius: 20px;
    background: rgba(200,140,60,0.16);
    color: #A9752F;
    border: 1px solid rgba(200,140,60,0.32);
    display: none;
  }
  #card.night #uncal { color: #E8B478; }
</style>
</head>
<body>
<div id="card">
  <div class="layer" id="layerA"></div>
  <div class="layer" id="layerB"></div>
  <div id="uncal">No baseline</div>
  <div id="inner">
    <div id="orbwrap">
      <div id="orb"></div>
      <!-- Mascot per state, tinted to the state colour. Two stacked layers so
           a change crossfades rather than snapping. -->
      <img class="mascot" id="mascotA" alt="">
      <img class="mascot" id="mascotB" alt="">
      <!-- Fallback face, used only when the mascot images are missing. Every
           feature is driven by a number: the eyes by arousal, the brows and
           mouth by valence. -->
      <svg id="face" viewBox="0 0 132 132">
        <path id="browL" fill="none" stroke="#fff" stroke-width="3.4"
              stroke-linecap="round" opacity="0"/>
        <path id="browR" fill="none" stroke="#fff" stroke-width="3.4"
              stroke-linecap="round" opacity="0"/>
        <ellipse id="eyeL" cx="48" cy="56" rx="5.5" ry="5.5"
                 fill="#fff" opacity="0.92"/>
        <ellipse id="eyeR" cx="84" cy="56" rx="5.5" ry="5.5"
                 fill="#fff" opacity="0.92"/>
        <path id="mouth" fill="none" stroke="#fff" stroke-width="4.5"
              stroke-linecap="round" opacity="0.92"/>
      </svg>
    </div>
    <div>
      <p id="label">—</p>
      <p id="desc"></p>
      <div id="stats">
        <div class="stat"><div class="k">Valence</div><div class="v" id="sv">—</div></div>
        <div class="stat"><div class="k">Arousal</div><div class="v" id="sa">—</div></div>
        <div class="stat"><div class="k">Signal</div><div class="v" id="sq">—</div></div>
        <div class="stat"><div class="k">Session</div><div class="v" id="se">—</div></div>
      </div>
      <div id="bar"><div id="fill"></div></div>
    </div>

    <div id="headwrap">
      <svg width="132" height="148" viewBox="0 0 132 148">
        <defs>
          <radialGradient id="gl">
            <stop offset="0%"   id="gl0" stop-opacity="0.85"/>
            <stop offset="100%" id="gl1" stop-opacity="0"/>
          </radialGradient>
        </defs>
        <!-- head outline, facing forward -->
        <ellipse cx="66" cy="74" rx="41" ry="52"
                 fill="none" stroke="currentColor" stroke-width="2" opacity="0.75"/>
        <!-- ears -->
        <ellipse cx="24" cy="74" rx="5" ry="10"
                 fill="none" stroke="currentColor" stroke-width="1.8" opacity="0.6"/>
        <ellipse cx="108" cy="74" rx="5" ry="10"
                 fill="none" stroke="currentColor" stroke-width="1.8" opacity="0.6"/>
        <!-- nasion, marks the front so the frontal sites read correctly -->
        <path d="M 60 24 L 66 15 L 72 24" fill="none"
              stroke="currentColor" stroke-width="1.8" opacity="0.6"/>
        <!-- intensity bloom over the frontal region -->
        <circle id="glow" cx="66" cy="48" r="26" fill="url(#gl)" opacity="0"/>
        <!-- the two electrodes the estimate actually depends on -->
        <circle class="site" id="fp1" cx="50" cy="40" r="5"/>
        <circle class="site" id="fp2" cx="82" cy="40" r="5"/>
        <text x="50" y="30" text-anchor="middle" font-size="9"
              fill="currentColor" opacity="0.8">Fp1</text>
        <text x="82" y="30" text-anchor="middle" font-size="9"
              fill="currentColor" opacity="0.8">Fp2</text>
      </svg>
      <div class="cap">Frontal activity</div>
    </div>
  </div>
</div>

<script>
const D = __PAYLOAD__;
const S = D.styles[D.state] || D.styles["Stable"];

// The Night mode toggle forces dark, but the card also has to follow the
// surrounding page: Streamlit renders dark when the OS prefers it, and the
// light pastels washed out to grey against that dark chrome.
const prefersDark =
  window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
const night = D.night || prefersDark;

const card = document.getElementById("card");
if (night) card.classList.add("night");

const gradA = night ? S.gradADark : S.gradA;
const gradB = night ? S.gradBDark : S.gradB;
const core  = night ? S.coreDark  : S.core;

// Alternate which layer is on top so consecutive shifts keep crossfading
// instead of the second one snapping.
const slot = (Number(sessionStorage.getItem("slot")) || 0) ^ 1;
sessionStorage.setItem("slot", String(slot));
const incoming = document.getElementById(slot ? "layerA" : "layerB");
const outgoing = document.getElementById(slot ? "layerB" : "layerA");

const bg = `radial-gradient(110% 130% at 18% 12%, ${gradA} 0%, ${gradB} 62%, ${gradB} 100%)`;
incoming.style.background = bg;
outgoing.classList.remove("on");
requestAnimationFrame(() => incoming.classList.add("on"));

// --- mascot ---------------------------------------------------------------
// When the artwork is available it replaces the orb entirely. Two stacked
// images crossfade, alternating which is on top so consecutive changes keep
// fading rather than the second one snapping.
const mascotSrc = (D.images || {})[D.state];
const hasMascot = Boolean(mascotSrc);

if (hasMascot) {
  const mSlot = (Number(sessionStorage.getItem("mslot")) || 0) ^ 1;
  sessionStorage.setItem("mslot", String(mSlot));
  const mIn = document.getElementById(mSlot ? "mascotA" : "mascotB");
  const mOut = document.getElementById(mSlot ? "mascotB" : "mascotA");

  mIn.style.setProperty("--breath", S.breath + "s");

  const reveal = () => {
    mOut.classList.remove("on");
    mIn.classList.add("on");
    document.getElementById("orb").style.display = "none";
    document.getElementById("face").style.display = "none";
  };

  mIn.onerror = () => {
    // Fall back to the drawn face rather than showing an empty card.
    document.getElementById("orb").style.display = "";
    document.getElementById("face").style.display = "";
  };

  // decode() resolves whether the image is fresh or already cached, which
  // onload does not: assigning a src the browser has cached can complete
  // before the handler is attached, and the swap then never happened.
  mIn.src = mascotSrc;
  if (mIn.decode) {
    mIn.decode().then(reveal).catch(reveal);
  } else {
    mIn.onload = reveal;
    if (mIn.complete) reveal();
  }
}

const orb = document.getElementById("orb");
// The orb stays visible until the mascot has decoded — the onload handler
// above hides it. Hiding it here would blank the card while the image loads.
orb.style.setProperty("--breath", S.breath + "s");
orb.style.background = `radial-gradient(circle at 34% 30%, ${core} 0%, ${shade(core, -22)} 100%)`;
orb.style.boxShadow = `0 12px 40px ${core}59`;

// --- face ----------------------------------------------------------------
// Each feature is a readout of one value, so the expression can be explained
// rather than just looked at:
//   eyes  <- arousal  (calm narrows them, activation widens them)
//   brows <- valence  (negative angles the inner ends down)
//   mouth <- valence  (smile through flat to a small tense line)
const v = Math.max(-1, Math.min(1, D.valence));
const a = Math.max(-1, Math.min(1, D.arousal));

// Arousal drives eye aperture. Low arousal reads as a relaxed, softened eye;
// high arousal widens it. Kept well short of a "startled" look — this is a
// caregiver's screen, and alarm in the UI helps nobody.
const a01 = Math.max(0, Math.min(1, (a + 1) / 2));
const eyeRy = 3.6 + a01 * 3.6;
const eyeRx = 5.2 + a01 * 1.0;
if (!hasMascot) {
  ["eyeL", "eyeR"].forEach((id) => {
    const e = document.getElementById(id);
    e.setAttribute("rx", eyeRx.toFixed(2));
    e.setAttribute("ry", eyeRy.toFixed(2));
  });
}

// Brows appear only as valence goes negative, and angle in proportion to it.
// A flat brow at neutral would read as a drawn-on feature; fading them in
// keeps the calm face clean.
const tense = Math.max(0, -v);
const browOp = tense * 0.85;
const drop = tense * 5.5;
if (!hasMascot) {
  const browL = document.getElementById("browL");
  const browR = document.getElementById("browR");
  browL.style.opacity = browOp;
  browR.style.opacity = browOp;
  browL.setAttribute("d", `M 40 ${44 - drop} L 56 ${41 + drop}`);
  browR.setAttribute("d", `M 76 ${41 + drop} L 92 ${44 - drop}`);
}

// Mouth: a wider swing than before, so the states are actually distinct.
// Arousal also shortens it slightly, which reads as tension without needing
// an open, anguished mouth.
const curve = 80 - v * 20;
const half = 22 - a01 * 4;
if (!hasMascot) {
  document.getElementById("mouth").setAttribute(
    "d",
    `M ${66 - half} 82 Q 66 ${curve} ${66 + half} 82`
  );
}

document.getElementById("label").textContent = S.label;
document.getElementById("desc").textContent = S.description;
document.getElementById("sv").textContent = fmt(D.valence);
document.getElementById("sa").textContent = fmt(D.arousal);
document.getElementById("sq").textContent = D.quality;
document.getElementById("se").textContent = D.elapsed;

const fill = document.getElementById("fill");
fill.style.background = core;
fill.style.width = Math.round(((D.arousal + 1) / 2) * 100) + "%";

if (!D.calibrated) document.getElementById("uncal").style.display = "block";

// A held reading is the previous one repeated. Fade the card so it cannot be
// mistaken for a live value, and stop the breathing that implies liveness.
if (D.stale) {
  document.getElementById("inner").style.opacity = "0.45";
  orb.style.animationPlayState = "paused";
}

// --- head map ------------------------------------------------------------
// The bloom tracks arousal only. EEG localises to the scalp, so nothing here
// claims a body region the signal cannot speak to.
// Reuses a01 from the face block above — same 0..1 arousal, same meaning.
document.getElementById("gl0").setAttribute("stop-color", core);
document.getElementById("gl1").setAttribute("stop-color", core);

const glow = document.getElementById("glow");
glow.setAttribute("r", 20 + a01 * 16);
glow.style.opacity = 0.15 + a01 * 0.75;

// Valence is a left/right alpha difference, so the two frontal sites are lit
// asymmetrically — the side driving the reading is the brighter one.
const tilt = Math.max(-1, Math.min(1, D.valence));
const fp1 = document.getElementById("fp1");
const fp2 = document.getElementById("fp2");
fp1.setAttribute("fill", core);
fp2.setAttribute("fill", core);
fp1.style.opacity = 0.35 + Math.max(0, -tilt) * 0.6;
fp2.style.opacity = 0.35 + Math.max(0, tilt) * 0.6;

// --- audio ---------------------------------------------------------------
// Only a genuine change of state chimes. A rerun that repaints the same
// state must stay silent, so the previous state is kept across reloads.
const prev = sessionStorage.getItem("prevState");
sessionStorage.setItem("prevState", D.state);

if (prev && prev !== D.state && !D.muted) {
  if (D.state === "Stable") {
    // Recovery: a fuller ascending phrase, deliberately more rewarding.
    play([523.25, 659.25, 783.99, 1046.5], 0.16);
  } else {
    play([392.0, 523.25], 0.18);
  }
}

function play(notes, dur) {
  let ctx;
  try {
    ctx = new (window.AudioContext || window.webkitAudioContext)();
  } catch (e) {
    return;
  }
  notes.forEach((freq, i) => {
    const t = ctx.currentTime + i * dur;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "sine";
    osc.frequency.value = freq;
    gain.gain.setValueAtTime(0.0001, t);
    gain.gain.exponentialRampToValueAtTime(0.12, t + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    osc.connect(gain).connect(ctx.destination);
    osc.start(t);
    osc.stop(t + dur + 0.02);
  });
}

function fmt(x) {
  const s = x >= 0 ? "+" : "";
  return s + Number(x).toFixed(2);
}

function shade(hex, pct) {
  const n = parseInt(hex.slice(1), 16);
  const cl = (c) => Math.max(0, Math.min(255, c + Math.round(255 * pct / 100)));
  const r = cl((n >> 16) & 255), g = cl((n >> 8) & 255), b = cl(n & 255);
  return "#" + ((r << 16) | (g << 8) | b).toString(16).padStart(6, "0");
}
</script>
</body>
</html>
"""
