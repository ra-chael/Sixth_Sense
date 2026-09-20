<p align="center">
  <img src="./images-emotion/MaranIcon.png" alt="Sixth Sense icon" width="140">
</p>

<h1 align="center">Sixth Sense</h1>

A caregiver assistance tool to sense and address emotional shifts

Estimates a caregiver-facing comfort/discomfort state from live EEG. Runs on
an OpenBCI Cyton, or on synthetic signal when no hardware is attached.

Demonstration prototype — not a medical pain detector.

---

# Overview

## The problem

A patient who cannot speak — late-stage dementia, severe autism, an intubated
ICU patient, a newborn — still experiences discomfort, but has no reliable way
to report it. Caregivers read faces and body language, which is slow,
subjective, and fails exactly when the patient is least able to express
themselves. **Sixth Sense gives that person a channel that does not require
speech or movement: their own cortical activity.**

## What it does

Reads EEG from a dry-electrode headset, estimates two affective dimensions
once per second, and shows a single glanceable state a caregiver can register
in under a second — **Stable**, **Moderate**, or **Extreme**. Every shift is
timestamped in a log the caregiver can annotate.

## The science

Affective state is conventionally described on two axes, and each maps to a
measurable EEG feature:

| Axis | What it means | How we measure it |
|---|---|---|
| **Valence** | Pleasant ↔ unpleasant | **Frontal alpha asymmetry.** Alpha power (8–13 Hz) is *inversely* related to cortical activity, so more right-frontal alpha means relatively more left-frontal engagement. The approach–withdrawal model associates left-frontal dominance with approach and positive affect, right-frontal with withdrawal and negative affect. |
| **Arousal** | Calm ↔ activated | **Fast-over-slow band ratio**, (beta + ½·gamma) / (alpha + theta). An alert cortex desynchronises: fast-band power rises and slow-band power falls. Gamma (30–45 Hz) is weighted at half because it carries pain-related signal but also muscle artefact. |

A state is **not** arousal alone — high arousal is ambiguous, since excitement
and distress look alike in beta. Negative valence is what escalates it:

```python
distress = arousal + max(0, −valence) × 0.5
```

So an animated, *positive* patient reads Stable; one equally activated but
*negative* reads Moderate or Extreme.

## Why it is built this way

Three decisions a reviewer should interrogate, and the reasoning:

**Everything is relative to the individual.** Absolute band power varies by an
order of magnitude between people, sessions, and electrode placements — gel
thickness alone moves it. A 20-second resting baseline is recorded per
participant, and every later reading is expressed as deviation from *their*
rest, using a **median and MAD** rather than mean and standard deviation so a
single bad calibration window cannot skew the reference.

**Artefacts are held, not scored.** A blink or jaw clench is a large transient
landing in the same fast bands as genuine arousal. Windows carrying one are
excluded and the previous reading repeats, with the reason shown. On recorded
EEG roughly a third of windows are affected — without this, a facial twitch
reads as distress a third of the time.

**Two electrodes of eight, deliberately.** All eight channels record cleanly.
But both measurements are *defined* on the frontal pair — alpha asymmetry is
an Fp1-vs-Fp2 quantity by construction. Using the other six would require a
weighting no labelled data justifies, adding parameters rather than
information.

## What it is not

It reports a state estimate derived from band power. It cannot diagnose, it is
not validated against patient self-report, and it is not a medical device. The
[Limitations](#limitations-and-future-work) section states each gap with its
next step.

---

# Quick start

No hardware needed — this runs on simulated EEG.

**macOS / Linux**
```bash
git clone https://github.com/ra-chael/Sixth_Sense.git
cd Sixth_Sense
python3 -m venv .venv && source .venv/bin/activate
pip install streamlit pandas numpy scipy brainflow
python -m streamlit run real-time-bci-stream/app.py
```

**Windows (PowerShell)**
```powershell
git clone https://github.com/ra-chael/Sixth_Sense.git
cd Sixth_Sense
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install streamlit pandas numpy scipy brainflow
python -m streamlit run real-time-bci-stream/app.py
```

Browser opens at `http://localhost:8501`. Then, in the app:

1. Sidebar → leave **Data source** on *Simulation mode*
2. Sidebar → **Record resting baseline** (20 seconds)
3. **Start session**
4. Toggle **Simulate discomfort** and watch the card shift Stable → Moderate → Extreme

That is the whole demo loop. For a real board, electrode placement, or what
the numbers mean, keep reading.

> Activation fails on Windows with *"cannot be loaded"*? Run
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then retry.

Every state change is also summarised in one plain sentence for the caregiver
log — written from the measurements by a deterministic template, so it needs
no network, no API key, and behaves identically every run.

---

# Running the App

Live comfort/discomfort visualizer. Estimates **valence** and **arousal** from
8-channel EEG and shows a Stable / Moderate / Extreme state.

Demonstration prototype — not a medical pain detector.

## 1. Install dependencies

Works on macOS and Windows — same commands, only the venv activation line differs.

From repo root:

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install streamlit pandas numpy scipy brainflow
```

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install streamlit pandas numpy scipy brainflow
```

Already have a venv? Just activate it and run the pip install line above.

## 2. Run the app

From repo root:

```bash
python -m streamlit run real-time-bci-stream/app.py
```

Browser opens at `http://localhost:8501`.

## 3. Session walkthrough

Everything for setup lives in the **sidebar**; the live view is the
**Dashboard** tab and state changes collect in **Saved events**.

1. **Data source** — *Simulation mode* to try it with no hardware, or
   *OpenBCI Cyton* for a real board.
2. **Connect** (Cyton only) — close the OpenBCI GUI first. The serial port can
   only be held by one process at a time. Default port is set for macOS
   (`/dev/cu.usbserial-*`); on Windows, use the **Serial port** field to enter
   the dongle's COM port instead (check Device Manager, e.g. `COM5`).
3. **Record resting baseline** — participant sits still, eyes open, for 20
   seconds. Required: valence and arousal are expressed relative to this
   person's own resting signal, so numbers before calibration mean little.
4. **Start session** — the dashboard now reads a window every second, no
   clicking needed.
5. **Saved events** — each Stable↔Moderate↔Extreme shift is logged with its
   time and readings. Add a caregiver note and **Save note** to write it to
   `history.csv`.

In simulation mode a **Simulate discomfort** toggle appears during a session,
which drives the state up so you can see a full shift without a participant.

### Controls

- **Mute** — silences the state-change chime.
- **Night mode** — dark palette for the hero card.
- **Refresh** — 1s / 2s / 5s per reading.

## What the numbers mean

| Reading | Source | Meaning |
|---|---|---|
| **Valence** | Frontal alpha asymmetry (Fp2 − Fp1) | Negative = withdrawal/negative affect |
| **Arousal** | Frontal (beta + ½·gamma) / (alpha + theta) | Higher = more activated |
| **State** | Arousal, aggravated by negative valence | Stable / Moderate / Extreme |
| **Head movement** | Cyton accelerometer | Context only — never changes the estimate |

Both are smoothed (EMA) and the state uses hysteresis, so a single noisy window
cannot flip the display. Windows carrying a blink or muscle transient are held
rather than scored.

## How it works

One pass of the loop, electrode to screen. Everything below runs once per
second while a session is active.

```
Cyton board
   │  250 samples × 8 channels (1 second)
   ▼
board_connection.capture_window()      ← keeps only the EEG rows
   │
   ▼
data_processing.detect_artifact()      ← blink / muscle transient?
   │  yes → hold the previous reading, skip the rest
   ▼
emotion.band_powers()                  ← Welch PSD, per channel
   │  theta 4-8 · alpha 8-13 · beta 13-30 · gamma 30-45 Hz
   ▼
emotion.raw_valence_arousal()
   │  valence = ln(alpha_Fp2) − ln(alpha_Fp1)
   │  arousal = (beta + ½·gamma) / (alpha + theta), frontal average
   ▼
EmotionTracker.update()
   │  1. subtract this participant's baseline  → z-scores
   │  2. tanh squash                           → −1 … +1
   │  3. EMA smooth                            → drop single-window noise
   │  4. threshold with hysteresis             → Stable/Moderate/Extreme
   ▼
hero.render()                          ← gradient, orb, face, chime
```

### Why the baseline is mandatory

Absolute alpha and beta power differ by an order of magnitude between people,
between sessions, and between electrode placements — even gel thickness moves
them. An arousal of `1.4` means nothing on its own; it only means something
against *this participant's* resting `1.1`.

So the 20-second baseline records resting mean and spread, and every later
reading is expressed as "how far from this person's own rest, in units of
their own variability". The centre and spread are the **median and MAD**
rather than mean and standard deviation, so one bad calibration window cannot
drag the reference. Without a baseline the app still runs, but the numbers are
unreferenced and the state thresholds are arbitrary.

Calibration excludes windows with poor signal, flat channels, blinks, or
muscle artifacts. The live estimator applies the same quality gate before
scoring, so an unreliable window is held as stale instead of changing the
participant's state.

### Why the smoothing

EEG is noisy at one-second resolution. A jaw clench, a blink, or a loose
electrode produces a spike indistinguishable from a real change. Two defenses:

- **EMA** (`EMA_ALPHA = 0.25` in `emotion.py`) — each reading is 25% new
  window, 75% history. A single bad window moves the display a little; a
  sustained shift moves it fully within a few seconds.
- **Hysteresis** (`HYSTERESIS = 0.08`) — once in a state, leaving it needs the
  threshold to be exceeded by a margin. Stops the display flickering when a
  value sits exactly on a boundary.

Trade-off: the state lags real changes by roughly 3-5 seconds. That is
deliberate — a caregiver-facing display that flickers is worse than one that
is slightly late.

### Why negative valence raises the level

High arousal alone is ambiguous — excitement and distress look similar in
beta power. The state calculation is:

```python
distress = arousal + max(0, -valence) * 0.5
```

Positive valence (approach, engagement) leaves arousal as-is. Negative
valence (withdrawal) pushes the same arousal into a higher level. So a
participant who is animated and positive reads Stable, while one equally
activated but negative reads Moderate or Extreme.

### Why gamma is weighted at half

Gamma (30–45 Hz) is the band most consistently associated with pain and high
arousal, so a discomfort estimate that ignored it would have an obvious hole.
It is capped below 50 Hz to stay clear of mains hum, and contributes at
`GAMMA_WEIGHT = 0.5` rather than equally with beta — scalp gamma is also
where jaw and neck muscle activity lands, so it is informative but the least
artifact-free band in use.

### Why some windows are held rather than scored

A blink or jaw clench is a large, brief excursion that lands in the same fast
bands as genuine arousal. Scoring those windows would make a facial twitch
read as distress, so `detect_artifact` flags them and the previous reading is
repeated instead — the card dims and names the reason.

The check is **per channel**, not window-wide: a blink is brief and mostly
frontal, so averaging it across eight channels dilutes it below any sensible
threshold. The worst channel decides.

| Window | Caught | Worst channel |
|---|---|---|
| Clean | no | 0% |
| Eyeblink | yes | ~6% |
| Jaw clench | yes | ~13% |
| Genuine high arousal | no | 0% |

### Why head movement is shown but never used

The Cyton streams accelerometer data alongside EEG. It is displayed beside the
reading and deliberately excluded from the estimate.

The reason it is there: EEG alone cannot distinguish a patient who is
distressed from one who is shifting in bed — both raise fast-band power. Head
movement lets a caregiver see that difference. The reason it is not in the
estimate: the threshold is uncalibrated, and a movement signal feeding the
state could turn a restless patient into a false alarm.

### Why the summary is a template, not a language model

Each state change gets a one-line plain-language summary in the event log,
assembled from the measurements by a deterministic function.

We built this on a local language model first, then replaced it. The reason is
that the sentence has to be *guaranteed*, not merely likely: it must never
read the figures back, never claim to know what the person feels, and must
always carry the movement caveat when the head moved. Those are properties a
prompt requests and a template enforces — and `test_narration_quality.py`
asserts each one, which is only possible because the output is deterministic.

The boundary a language model was there to respect is now structural: **the
summary never sees EEG and never decides a state.** It receives numbers this
pipeline already computed and phrases them. Remove it and every reading and
every state is identical; only the English sentence is lost.

The alternative — handing band powers to a model and asking what the patient
feels — would produce confident text with nothing behind it, replacing a
signal chain we can explain with a guess we cannot.

### Where to change things

| Want to change | File | What to edit |
|---|---|---|
| Electrode layout | `emotion.py` | `CHANNEL_NAMES` |
| State thresholds | `emotion.py` | `MODERATE_AROUSAL`, `EXTREME_AROUSAL` |
| Smoothing amount | `emotion.py` | `EMA_ALPHA` (higher = twitchier) |
| Baseline length | `app.py` | `BASELINE_WINDOWS` |
| Colors, animation, chime | `hero.py` | `STATE_STYLE`, then the HTML block |
| Frequency bands | `emotion.py` | `BANDS`, `GAMMA_WEIGHT` |
| Artifact sensitivity | `data_processing.py` | `ARTIFACT_UV`, `ARTIFACT_FRACTION` |
| Movement threshold | `app.py` | `MOTION_THRESHOLD` |
| Summary wording | `narrate.py` | `summarize()` |

### Testing without hardware

Simulation mode synthesises 8-channel EEG with the spectral properties the
estimator reads, so the whole pipeline runs unchanged — the sliders are not
shortcuts past it.

**Simulate discomfort** is the two-state preset: it raises fast-band power and
suppresses right-frontal alpha, exercising both axes rather than arousal
alone.

**Drive the signal manually** gives finer control during a session:

| Control | Range | What it does |
|---|---|---|
| Arousal | −1 … +1 | Sets fast-band amplitude against alpha/theta |
| Valence | −1 … +1 | Sets right-frontal alpha relative to left |
| Inject artifact | none / blink / clench | Adds the transient the guard should reject |

The reading lags the sliders by a few seconds — that is the moving average,
working as intended. All three states are reachable, which is how the
thresholds were checked:

| Sliders | Measured | State |
|---|---|---|
| a +0.0, v +0.0 | +0.00, +0.13 | Stable |
| a +0.3, v −0.2 | +0.19, −0.37 | Moderate |
| a +0.6, v −0.4 | +0.46, −0.54 | Extreme |

Baseline recording ignores the sliders and always uses a neutral signal, so a
calibration cannot be taken against a cranked-up setting.

## What we tried, and what we learned

The parts of this that were not obvious going in.

**The hardware worked.** All eight channels came up clean in the OpenBCI GUI
on the cap — every channel Not Railed with visible EEG, at 250 Hz over the
BLE dongle on battery power. Getting a full 8-channel montage reading
properly was not a given, and it means every limitation below is about our
method rather than our recording.

**Simulation hides the bugs that matter.** Synthetic EEG never returns an
empty buffer, never goes flat, and never blinks. Three real defects only
surfaced when we ran actual data through the pipeline: the board returns 24
rows, not 8 (accelerometer and timestamps ride alongside the EEG, and we were
treating all of them as brain signal); an empty buffer right after
`start_stream()` crashed the estimator; and a flat channel produced a NaN
that the moving average then latched onto permanently, poisoning the rest of
the session. All three would have appeared for the first time in front of a
participant.

**The artifact guard does more work than expected.** On synthetic signal it
rejects nothing. On real recorded EEG it held roughly a third of windows —
blinks and movement are simply that common. That number is itself a finding:
a discomfort detector without artifact rejection would be reporting facial
muscle activity as distress a third of the time.

**Averaging hid the blinks.** Our first artifact check averaged across all
eight channels and caught almost nothing, because a blink is brief and mostly
frontal. Judging each channel separately and letting the worst one decide
fixed it.

**A calibrated baseline is not optional.** Band power varies by an order of
magnitude between people and placements. Without a per-participant resting
baseline the state thresholds are arbitrary numbers. We also had to floor the
baseline spread: a very consistent 20-second baseline made ordinary drift look
like a large deviation and pegged the display at its limits.

**Sample rate has to come from the board.** The band edges are in Hz, so
assuming a rate that differs from the hardware silently measures the wrong
frequencies — an "alpha" reading that is really beta, with nothing visibly
broken. The app now reads the rate from the board on connect and displays it.

## Limitations and future work

Stated plainly, because these are the first things a reviewer should ask
about — and each one has a next step we know how to take.

### Two channels of eight

Only Fp1 and Fp2 feed the estimate. The other six are recorded and displayed
but unused.

**This is not a signal-quality limitation.** All eight channels were verified
working in the OpenBCI GUI on the cap — the hardware delivers eight usable
channels and we are choosing to use two.

The reason is that both measurements are *defined* on the frontal pair:
valence is frontal alpha asymmetry, an Fp1-vs-Fp2 quantity by construction,
and frontal beta is the standard arousal index. Picking that method — a
literature-backed 2D valence/arousal model — is what fixed the channel count
at two, rather than a separate decision to discard the rest.

Bringing in the other six would mean choosing a weighting across them, and we
have no labelled affective data to justify one. That adds parameters rather
than information. We would rather defend a narrow model than ship a wider one
we cannot explain.

**Next:** use the posterior channels as corroboration — if central and
parietal alpha track the frontal reading, the signal is more likely neural
than artifact. That is a validation step, not a bigger model, and it needs a
labelled session to check against.

### No affective ground truth

The valence and arousal mappings come from the affective-EEG literature, not
from labelled data collected with this hardware. Nothing here has been checked
against a participant reporting how they actually felt.

**Next:** run sessions where a participant self-reports comfort on a scale
while wearing the cap, then check whether the estimate correlates. The app
already logs every reading to `history.csv` with a caregiver note field, so
the data collection path exists — what is missing is participants and time.

### EEG only

No heart rate, respiration, or skin conductance, all of which carry affective
signal. Head movement is read from the accelerometer but shown as context
rather than used.

Note: the accelerometer has read 0.000 g on all three axes in our bench
testing so far, which means it is either disabled in the board's current mode
or not being sampled — worth confirming against a moving board before relying
on the reading. This is also why it stays display-only.

**Next:** the accelerometer is the cheapest addition — it is already in the
Cyton stream. Promoting it from display to a confidence weight would let the
app say "high arousal, but the patient was moving" rather than leaving the
caregiver to notice. We did not ship that because the movement threshold is
uncalibrated and a false confidence signal is worse than none.

### Not a pain detector

It reports a state estimate derived from band power. It cannot diagnose, and
it is not a medical device. Nothing about the current validation would support
a clinical claim, and we are not making one.

## Hardware

What this was built and tested against:

| Part | Detail |
|---|---|
| Board | OpenBCI Cyton V3-32, 8 channels |
| Link | BLE USB dongle (GPIO 6 position) |
| Power | 6 V battery pack — the board runs untethered |
| Cap | Fabric cap with white electrode holders, ribbon cable to the board |
| Electrodes | Touch-proof leads, gel or paste at each site |
| Sample rate | 250 Hz (read from the board, not assumed) |

A Cyton **Daisy** would be 16 channels at 125 Hz and needs `CHANNEL_NAMES`
changed as well — this app assumes the 8-channel board.

### Signal check

**All eight channels were verified working in the OpenBCI GUI** during live
testing on the cap — every channel reading "Not Railed" with visible EEG.

This is worth stating because it rules out an explanation the design might
otherwise suggest. Only two channels feed the estimate, and that is *not* a
signal-quality limitation: the hardware delivers eight usable channels. The
narrowness is in the method, not the recording (see
[Two channels of eight](#two-channels-of-eight)).

## Electrode placement

### Check the channel mapping first

This is the setting most likely to be wrong, and its failure is silent: if
the frontal pair is not on the pins the app thinks it is, every reading still
looks confident but describes a different part of the head.

The app defaults to BrainFlow's Cyton ordering, frontal-first:

```
pin  1    2    3    4    5    6    7    8
    Fp1  Fp2  C3   C4   P7   P8   O1   O2
```

**But the montage card that ships with some OpenBCI caps numbers
posterior-first** — `1 = O2`, `2 = P4`, `3 = C4`. If that is how the cap is
wired, the default above is wrong and `valence` would be computing occipital
alpha asymmetry rather than frontal.

`emotion.py` carries both orderings — `CHANNEL_NAMES` (the default) and
`CHANNEL_NAMES_POSTERIOR_FIRST`. Set the one that matches the cap.

**How to tell which you have**, without guessing:

1. Stream in the OpenBCI GUI with the cap on.
2. Ask the wearer to blink hard several times.
3. Blinks appear as large, slow deflections **on the frontal channels only**.
   Whichever channel numbers jump are your frontal pins.
4. Then ask them to close their eyes for ten seconds. Alpha (a clear ~10 Hz
   rhythm) rises strongest at the **occipital** sites — that identifies the
   other end of the cap.

**Fp1 and Fp2 matter most** — valence is unavailable without that frontal pair.

### Sample rate

Read from the board on connect, not assumed, and shown under the connection
status so it can be checked at a glance. A Cyton reports 250 Hz; a Cyton Daisy
reports 125 Hz and has 16 channels, which would also need `CHANNEL_NAMES`
updated.

This matters more than it looks. Every band edge is in Hz, so if the app
assumed a rate the hardware was not using, the "alpha" band would be measuring
some other frequency entirely — and nothing would appear broken. One value in
`emotion.py` governs the whole pipeline; the other modules read it from there
rather than keeping their own copy.

## Files

All under [`real-time-bci-stream/`](./real-time-bci-stream/). Listed in
dependency order — each depends only on the ones above it, so reading top to
bottom follows the signal.

### The signal path

**`simulated_data.py`** — synthetic 8-channel EEG.
*Why it exists:* the whole pipeline can be exercised and tested without
hardware, which is how the state logic was verified.
*How:* sums alpha, beta, gamma and theta sinusoids per channel, with the
fast/slow balance and the Fp1-vs-Fp2 alpha ratio set from target arousal and
valence — the inverse of what the estimator measures. Defines the `8 × 250`
window shape everything downstream expects. Can inject a blink or jaw clench
to exercise the artefact guard.

**`board_connection.py`** — the OpenBCI Cyton, over BrainFlow.
*Why:* returns the *same* window shape as the simulator, so nothing
downstream can tell real from synthetic.
*How:* slices the EEG rows out of the board's 24-row packet (the rest is
accelerometer, aux and timestamps), adopts the board's own sample rate on
connect, and clears orphaned sessions. Head movement is read by a **separate**
function so a failure there can never break an EEG capture.

**`data_processing.py`** — quality gate.
*Why:* a blink or clench lands in the same fast bands as genuine arousal, so
scoring those windows makes a facial twitch read as distress.
*How:* flags windows with samples past 120 µV, judged **per channel** — a
blink is brief and frontal, so averaging across eight channels dilutes it
below any usable threshold. The worst channel decides.

**`emotion.py`** — the estimate. Most of the science is here.
*Why:* turns band powers into an affective state that means something for
*this* participant.
*How:* Welch PSD → theta/alpha/beta/gamma → frontal alpha asymmetry
(valence) and fast-over-slow ratio (arousal) → referenced to the participant's
resting **median and MAD** → tanh-squashed → exponentially smoothed →
thresholded with hysteresis. Holds the previous reading rather than emitting
NaN when a window is unusable.

### The interface

**`hero.py`** — the state card, as a self-contained HTML/JS island.
*Why:* Streamlit cannot crossfade a gradient, breathe an orb, or play a tone.
*How:* two stacked gradient layers crossfade on a state change; the face is
drawn from the live numbers — eyes track arousal, brows and mouth track
valence — so the expression can be read back as the values that produced it.
A two-tone chime marks any shift, a four-note ascending phrase marks recovery
to Stable. **No detection logic.**

**`trend.py`** — the Altair charts.
*Why:* `st.line_chart` sorts its legend alphabetically, which silently
mislabelled every electrode trace (C3 shown first when row 0 is Fp1).
*How:* montage order made explicit, frontal pair highlighted, and the
Moderate threshold line imported from `emotion.py` rather than hardcoded so
the chart cannot drift out of agreement with the state logic.

**`narrate.py`** — one plain-language sentence per logged state change.
*Why:* a caregiver reads English faster than a number, and the log needs a
record that survives without interpretation.
*How:* a deterministic template over the measurements. It never prints
figures, never names the state, never claims to know what the person feels,
and always surfaces the movement or poor-signal caveat when present — the
properties `test_narration_quality.py` asserts.

**`theme.py`** — page styling: fonts, colours, Streamlit chrome overrides.

**`app.py`** — the Streamlit UI and the once-per-second loop that wires all of
the above together.

### Tests

**`test_pipeline_quality.py`** — blink and flat windows are held before state
estimation, clean windows are scored, a held window does not change the
current state, and the baseline's robust centre survives an outlier.

**`test_narration_quality.py`** — the summary reads no figures back, makes no
claim about the person, and carries the movement caveat whenever the head
moved.

Run them with `python -m pytest` from `real-time-bci-stream/`.

---

If you are changing **what is detected**, you want `emotion.py`. If you are
changing **how it looks**, you want `hero.py`. They do not overlap.

## Before a session with a participant

In order. Each step has cost us a session at least once.

1. **Battery in, board on.** The Cyton runs off its battery pack, not USB. A
   flat pack looks identical to a connection fault.
2. **Dongle switch on GPIO 6.** The other position does not stream.
3. **Quit the OpenBCI GUI completely.** Not "stop stream" — quit. It holds the
   serial port even while sitting on its start screen, and the port takes one
   process at a time.
4. **Check the channel mapping** (above) if this cap has not been verified.
5. **Electrodes wetted and seated.** In the GUI, channels should read "Not
   Railed". A railed channel is a contact problem, not a brain-signal problem.
6. **Connect in the app** and confirm the sample rate shown under the
   connection status is what you expect.
7. **Record the resting baseline** — 20 s, participant still, eyes open. Do
   this while they are actually calm: a baseline taken while they are already
   activated sets their "rest" too high and the state will never leave Stable.
8. **Start session.**

## Troubleshooting

**`ANOTHER_BOARD_IS_CREATED_ERROR`** — a BrainFlow session is still open. The
app clears orphan sessions automatically on connect; if it persists, make sure
the OpenBCI GUI is fully quit, then Connect again.

**`BOARD_NOT_READY_ERROR`** — the dongle opened but the board did not answer.
Check the Cyton power switch is on, the dongle switch is on **GPIO 6**, and the
board is in range.

**Both apps fail to connect** — only one process can hold the serial port.
This is the most common problem: the OpenBCI GUI and this app cannot both be
connected, and the GUI grabs the port even while only *sitting* on its start
screen. Quit it fully, do not just stop the stream.

Check who has the port:

```bash
# macOS/Linux — prints the holding process, or nothing if free
lsof /dev/cu.usbserial-*
```

```powershell
# Windows (PowerShell) — list the COM ports that exist
Get-CimInstance Win32_SerialPort | Select-Object DeviceID, Description

# then confirm the GUI is not running
Get-Process OpenBCI_GUI -ErrorAction SilentlyContinue
```

**Finding your port name**

- **macOS** — `ls /dev/cu.usbserial-*`. Note the name changes if you use a
  different dongle, so re-check it rather than trusting the default.
- **Windows** — Device Manager → Ports (COM & LPT) → look for the FTDI entry,
  e.g. `COM5`. Type that straight into the app's **Serial port** field.

**Windows: `.venv\Scripts\Activate.ps1 cannot be loaded`** — PowerShell blocks
scripts by default. Allow them for your user once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Or sidestep it by using `cmd` instead: `.venv\Scripts\activate.bat`.

**No sound on state change** — browsers block audio until you interact with
the page. Click anywhere in the app once, then trigger a shift. Also check
**Mute** in the sidebar.

**State never leaves Stable with a real participant** — almost always a
baseline problem. If the baseline was recorded while the participant was
already activated, their "rest" is set too high. Re-record it.

Real OpenBCI Cyton setup: see [`cyton_setup_instructions.md`](./real-time-bci-stream/cyton_setup_instructions.md).

## Progress report

- Simulated-EEG MVP working end to end: window generation → band-power
  features → signal-quality check → Streamlit dashboard → CSV history.
- Live dashboard rebuilt around valence/arousal (frontal alpha asymmetry +
  beta/(alpha+theta)) instead of the earlier single discomfort score, with
  EMA smoothing and hysteresis so state doesn't flicker on one noisy window.
- Resting-baseline calibration added — values are meaningless without it, so
  the UI blocks session start-adjacent actions until a baseline is recorded.
- OpenBCI Cyton hardware path wired in (`board_connection.py`): explicit
  Connect button, no auto-connect, orphan BrainFlow sessions cleared via
  `release_all_sessions()` to avoid `ANOTHER_BOARD_IS_CREATED_ERROR` across
  Streamlit reruns.
- Verified running on **macOS** (primary dev machine) and **Windows**
  (teammate) — same `pip install` set on both, only venv activation and
  serial-port naming differ (`/dev/cu.usbserial-*` vs `COMx`).
- Not yet done: real participant data collection with the physical board
  (blocked on hardware availability during dev), trained classifier (still
  rule-based thresholds).

---

# 🧠 Welcome to the Fall 2026 SURGE Neuro Hackathon!

Welcome to the **SURGE Neuro Hack Fall 2026**, where you'll get hands-on experience developing Brain-Computer Interfaces (BCIs) and analyzing neural data. Over the course of this weekend, you'll work in teams to prototype applications using EEG data. 

<details>
<summary>Table of Contents</summary>

## Table of Contents

- [🧠 Welcome to the Fall 2026 SURGE Neuro Hackathon!](#-welcome-to-the-fall-2026-surge-neuro-hackathon)
  - [Table of Contents](#table-of-contents)
- [General Information:](#general-information)
  - [Support \& Collaboration](#support--collaboration)
  - [Hackathon Schedule](#hackathon-schedule)
  - [Rules:](#rules)
- [🏆 Challenge Streams](#-challenge-streams)
  - [**1️⃣ Brain-Controlled Applications (Real-Time BCI)**](#1️⃣-brain-controlled-applications-real-time-bci)
    - [Real-Time BCI Deliverables](#real-time-bci-deliverables)
  - [**2️⃣ AI \& Machine Learning (Offline EEG Data Analysis)**](#2️⃣-ai--machine-learning-offline-eeg-data-analysis)
    - [Offline EEG Data/ML Deliverables](#offline-eeg-dataml-deliverables)
  - [**3️⃣ Hardware Hacking (EEG Hardware \& Embedded Systems)**](#3️⃣-hardware-hacking-eeg-hardware--embedded-systems)
    - [Hardware Hacking Deliverables](#hardware-hacking-deliverables)
- [📩 Submission Information](#-submission-information)
    - [Submission Process](#submission-process)
- [📌 Getting Started](#-getting-started)
    - [**1️⃣ Clone this Repository**](#1️⃣-clone-this-repository)
    - [**2️⃣ Install Dependencies**](#2️⃣-install-dependencies)
    - [**3️⃣ Choose Your Challenge Stream and Get Hacking!**](#3️⃣-choose-your-challenge-stream-and-get-hacking)
- [Don't know where to start? Check this out!](#dont-know-where-to-start-check-this-out)
- [Repository Table of Contents](#repository-table-of-contents)
  - [📂 Neurohack-Fall-2026](#-neurohack-fall-2026)
    - [📂 getting-setup - Instructions on how to setup python](#-getting-setup---instructions-on-how-to-setup-python)
    - [📂 real-time-bci-stream – Resources \& starter code for real-time EEG applications](#-real-time-bci-stream--resources--starter-code-for-real-time-eeg-applications)
    - [📂 offline-analysis-stream – Resources \& starter code for EEG data analysis](#-offline-analysis-stream--resources--starter-code-for-eeg-data-analysis)
    - [📂 resources – Learning materials and references](#-resources--learning-materials-and-references)
</details>

---
# General Information:

## Support & Collaboration
- Join the **#neurohack-fall-2026** channel on the [SURGE Discord server](https://discord.gg/jvkwKfERt) to ask questions, share ideas, and collaborate with other participants.
- Refer back to the [introduction presentation](https://docs.google.com/presentation/d/1Kv9ZSb0_6BqbbZlZWzYRzQ__WZipsEUCZKcd4CUvxyY/edit?usp=sharing)
- Reach out directly to me at [mascini.max@dal.ca](mailto:mascini.max@dal.ca)! (Please keep in mind I may be busy helping other teams, so I may not respond immediately)

## Hackathon Schedule

- **Day 1 (Friday 5:00pm-8:00pm):** Introduction to BCI, EEG, and Team Formation
- **Day 2 (Saturday 9:00am-4:00pm):** Hacking!
- **Day 3 (Sunday 9:00am-4:00pm):** Project wrap-up & submission, team presentations, and judging!
  - Submission Deadline: Sunday @ 1:00 PM
  - Presentations: 2:30 PM - 4:00 PM

## Rules:
1. You are free to use any hardware or software tools you like, but we recommend using the resources provided in this repository.
2. You may work in teams of up to 4 people. Individual submissions are also allowed.
3. All work must be done during the hackathon period (Friday to Sunday).
4. You must submit your project by the deadline to be eligible for judging.
5. All team members must be present and speak during the teams' presentation to be eligible for a prize.
6. You are allowed to - even encouraged to use AI tools (e.g., ChatGPT, GitHub Copilot) to assist with coding, brainstorming, and problem-solving. **However, it is your responsibility to ensure that you understand and can explain all of your work!**
7. Have fun and be creative!

---

# 🏆 Challenge Streams
We have **three challenge tracks** you can choose from:

## **1️⃣ Brain-Controlled Applications (Real-Time BCI)**
**🎯 Challenge & Goal:** Develop an application where EEG signals **control an interaction or interface** in real time. Use real-time EEG to build a brain-controlled game, assistive tool, interactive experience, or whatever you brainstorm!

**Example Ideas:**
   - A **Mind-controlled game**
   - A **An EEG-controlled communication device**
   - A **mind-controlled music device**

### Real-Time BCI Deliverables

- **Project Presentation** (10 minutes max.) - See the [rubric for details.](./resources/Judging_rubrics.pdf) A general template for your presentation should include:
  -  Problem Statement & Motivation  
  - System Design & Implementation 
  - A live Demonstration (or a pre-recorded demo if real-time is not possible)  
  - Results & Interpretation (system performance, user interaction)
  - Challenges & Future Work
- **Code Repository** (GitHub or Zip file) – Should include: 
  - Your code, presentation and instructions for running the project (a readme file)


## **2️⃣ AI & Machine Learning (Offline EEG Data Analysis)**
**🎯 Challenge & Goal:** Analyze pre-recorded EEG data to extract insights, perform statistics, classify brain signals/states, or detect anomalies.

**BCI Dataset:** For this stream we have provided three datasets of EEG recordings from participants subjected to various experimental conditions designed to elicit specific neural responses. For more information on the provided dataset, please refer to the [dataset description](./offline-analysis-stream/dataset_description.md).
- **You may find and use a different, publicly available dataset for your analysis**. However, if you choose to use another dataset, volunteers may not be able to provide as much support.

### Offline EEG Data/ML Deliverables

- **Project Presentation** (10 minutes max.) - see the [rubric for details.](./resources/Judging_rubrics.pdf) A general template for your presentation should include:
  - Problem Statement & Motivation  
  - What you did with the data (preprocessing, analysis, modeling) 
  - Results & Interpretation (accuracy, feature importance, visualization of findings, etc.)  
  - Challenges & Future Work  
- **Code Repository** (GitHub or Zip file) – Should include:  
  - Your code/analyses, presentation and instructions for running the project (a readme file)

## **3️⃣ Hardware Hacking (EEG Hardware & Embedded Systems)**
**🎯 Challenge & Goal:** Design, build, or modify EEG hardware to improve signal acquisition, create a novel sensing device, or interface custom hardware with a BCI pipeline.

**Example Ideas:**
   - A **custom EEG electrode array or headset**
   - A **hardware-accelerated signal processing pipeline**
   - A **low-cost, DIY EEG amplifier or biosignal interface**

### Hardware Hacking Deliverables

- **Project Presentation** (10 minutes max.) - See the [rubric for details.](./resources/Judging_rubrics.pdf) A general template for your presentation should include:
  - Problem Statement & Motivation
  - Hardware Design & Implementation (schematics, components, build process)
  - A live Demonstration (or a pre-recorded demo)
  - Results & Interpretation (signal quality, performance benchmarks)
  - Challenges & Future Work
- **Code Repository** (GitHub or Zip file) – Should include:
  - Your code, schematics/CAD files, and a README with build and usage instructions

---

# 📩 Submission Information

- **Submission Deadline: Sunday, 1:00 PM**
- **Judging Format:** A **short presentation** followed by a **5-minute Q&A** session from the judges.
  - Order of team presentations will be decided at random.
- **Judging Criteria:** Projects will be evaluated based on the [rubrics provided for each challenge stream.](./resources/Judging_rubrics.pdf)
- **Prizes:** The top-scoring team will receive $500 to be split among the group equally; 2nd and 3rd place teams will get bragging rights, a great addition to your CV, and sweet SURGE swag prizes!

### Submission Process
- **How to Submit:**  
  - Upload your presentation, code, reports, and any other relevant files to your Github repository.
    - If files are too large, or you don't have a Github repository, you can submit a zip file.
    - Ensure it includes a *README* explaining about (and how to run/use) your project. 
  - **[Submit through the submission form](https://forms.cloud.microsoft/Pages/ResponsePage.aspx?id=mRm4YH8LLUGSo-F9iunj4H7FrINmspNAj3XHyveOfoJUNEpIMDdMRDVNUDlXVVdQTkpNVDBEMk9QSy4u)**
- **NOTE:** If you submit multiple times, only your most recent submission made before the submission deadline (1:00 pm on Sunday) will be considered. Submissions received after the deadline will not be accepted.  

---

# 📌 Getting Started
### **1️⃣ Clone this Repository**
```bash
git clone https://github.com/SURGE-NeuroTech-Club/Neurohack-Fall-2026.git
cd <Neurohack-Fall-2026>
```

### **2️⃣ Install Dependencies**
Navigate to [getting-setup/python_setup.md](./getting-setup/python_setup.md) for instructions on how to setup the provided miniforge `Brainhack` environment.

Alternatively, If you already have Python 3.12 installed, you will need to ensure you have the following packages installed if you want to run the provided scripts.
```bash
pip install scipy jupyterlab mne brainflow pyserial matplotlib
```

For Unity/Pygame-based projects, additional installations may be required.

### **3️⃣ Choose Your Challenge Stream and Get Hacking!**
Navigate to either:
- `real-time-bci-stream/` for the interactive applications stream.
- `offline-analysis-stream/` for the EEG data processing and machine learning stream.

---
# Don't know where to start? Check this out!
Dr. Aaron Newman produced a free online textbook that is a **fantastic place to start** learning about python, EEG signal processing, and brain-computer interfaces. It uses **MNE-Python** — the same library used in the provided example scripts — and covers preprocessing, artifact removal, ERPs, frequency analysis, and more!
- Full textbook: https://neuraldatascience.io/
  - Jump straight to python introduction: https://neuraldatascience.io/python/introduction/
  - Or to the EEG section: https://neuraldatascience.io/eeg/introduction/
---

# Repository Table of Contents
your_repo_name
## 📂 [Neurohack-Fall-2026](./)
- 📜 [README.md](./README.md) – Main documentation

### 📂 [getting-setup](./getting-setup/) - Instructions on how to setup python
- 📄 [python_setup.md](./getting-setup/python_setup.md) – Instructions on how to setup python
- 🐍 [brainhack_env.yaml](./getting-setup/brainhack_env.yaml) - Anaconda environment file with python 3.13 to get you started
- 🐍 [compatibility_brainhack_env.yaml](./getting-setup/compatibility_brainhack_env.yaml) - Anaconda environment file with python 3.10 to get you started

### 📂 [real-time-bci-stream](./real-time-bci-stream/) – Resources & starter code for real-time EEG applications
  - 📄 [cyton_setup_instructions.md](./real-time-bci-stream/cyton_setup_instructions.md) – Setup guide
  - 📂 [example-scripts/](./real-time-bci-stream/example-scripts/) – Starter code for real-time BCI

### 📂 [offline-analysis-stream](./offline-analysis-stream/) – Resources & starter code for EEG data analysis
  - 📄 [dataset_description.md](./offline-analysis-stream/dataset_description.md) – Information on the dataset
  - 📂 [sample-data/](./offline-analysis-stream/sample-data/) – Example EEG data
  - 📂 [example-scripts/](./offline-analysis-stream/example-scripts/) – Starter scripts for EEG analysis

### 📂 [resources](./resources/) – Learning materials and references
  - 📄 [bci_basics.md](./resources/bci_basics.md) – Introduction to BCI concepts
  - 📄 [useful_links.md](./resources/useful_links.md) – Reference materials and links
  - 📄 [judging_rubrics.pdf](./resources/Judging_rubrics.pdf) – Outline of deliverables for each stream & judging rubrics
