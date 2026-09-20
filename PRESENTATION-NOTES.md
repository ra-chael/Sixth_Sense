# Technical Q&A Prep

Everything a judge might ask, with the answer and the reasoning behind it.
Read the **30-second version** first — that alone covers most of it.

All numbers here were checked against the source on 2026-09-19.

---

## The 30-second version

> We read EEG from two frontal electrodes. **Valence** — whether the state is
> positive or negative — comes from the difference in alpha power between the
> left and right frontal sites. **Arousal** — how activated they are — comes
> from the ratio of fast brain activity to slow. Both are measured against
> that person's own resting baseline, because absolute values vary enormously
> between people. We smooth the result, reject windows that contain a blink or
> muscle movement, and show a Stable / Moderate / Extreme state on a card a
> caregiver can read in under a second.

If you remember one sentence: **everything is relative to the participant's
own baseline, because absolute EEG power means nothing across people.**

---

## The pipeline, in plain words

Once per second:

1. **Read** 250 samples from 8 electrodes (one second at 250 Hz)
2. **Check for artifacts** — a blink or jaw clench? Hold the previous reading
3. **Split into frequency bands** — theta, alpha, beta, gamma (Welch's method)
4. **Compute valence and arousal** from the frontal pair
5. **Compare to baseline** → how far from this person's own rest
6. **Smooth** → a single bad window cannot yank the display
7. **Threshold** → Stable / Moderate / Extreme
8. **Draw** the card

---

## The two measurements

### Valence — positive or negative?

```
valence = ln(alpha at Fp2) − ln(alpha at Fp1)
```

**What it is:** frontal alpha asymmetry. Alpha power is *inversely* related to
cortical activity — more alpha means that side is less engaged.

**Why it works:** the approach–withdrawal model. Relatively more **left**
frontal activity is associated with approach and positive affect; relatively
more **right** with withdrawal and negative affect. Well-established in
affective EEG (Davidson's work from the 1990s onward).

**Why the logarithm:** power is multiplicative and heavily skewed. A log ratio
makes the difference symmetric — twice as much on the left and twice as much
on the right come out equal and opposite.

### Arousal — how activated?

```
arousal = (beta + 0.5 × gamma) / (alpha + theta)
```

**What it is:** fast activity divided by slow activity, averaged over Fp1/Fp2.

**Why it works:** desynchronisation. An alert, activated brain shows more
fast-band and less slow-band power; a drowsy or relaxed one the reverse.

---

## The constants, and why each is what it is

| Constant | Value | Why |
|---|---|---|
| `EMA_ALPHA` | 0.25 | Each reading is 25% new window, 75% history. One bad window moves the display a little; a real shift lands fully in ~3–5 s |
| `HYSTERESIS` | 0.08 | Leaving a state needs the threshold exceeded by a margin, so a value sitting on a boundary does not flicker |
| `GAMMA_WEIGHT` | 0.5 | Gamma is informative for pain but also where jaw/neck muscle lands — counted, but not equally with beta |
| `MODERATE_AROUSAL` | 0.35 | On the baseline-relative scale, roughly where a change stops looking like normal drift |
| `EXTREME_AROUSAL` | 0.70 | Reserved for a sustained, clear departure |
| `ARTIFACT_UV` | 120 µV | Above plausible cortical amplitude — real scalp EEG is tens of µV |
| `ARTIFACT_FRACTION` | 0.02 | More than 2% of samples on the *worst* channel past that threshold = reject |
| `BASELINE_WINDOWS` | 20 | 20 seconds of rest. Long enough for a stable mean, short enough to actually do |
| `MIN_SAMPLES` | 64 | Below this, Welch's estimate is meaningless |
| `WINDOW_SAMPLES` | 250 | One second at 250 Hz |

**If asked "are these tuned or guessed?"** — answer honestly: *"They're
reasoned starting points, verified in simulation to give the behaviour we
want. They are not fitted to labelled data, because we don't have any. That's
our main limitation."*

That answer scores better than pretending they're optimised.

---

## Frequency bands

| Band | Range | What it means here |
|---|---|---|
| Theta | 4–8 Hz | Drowsiness; part of the "slow" denominator |
| Alpha | 8–13 Hz | Relaxed wakefulness. **Drives valence** via L/R asymmetry |
| Beta | 13–30 Hz | Active thinking, alertness. Main arousal driver |
| Gamma | 30–45 Hz | Associated with pain and high arousal |

**Why gamma stops at 45 Hz:** to stay clear of mains hum — 60 Hz here, 50 Hz
in much of the world. Going higher would measure the building's wiring.

---

## Why negative valence raises the state

```python
distress = arousal + max(0, −valence) × 0.5
```

**The problem:** high arousal alone is ambiguous. Excitement and distress look
very similar in beta power.

**The fix:** positive valence leaves arousal as-is. Negative valence pushes
the same arousal into a higher level.

So someone animated and *positive* reads Stable. Someone equally activated but
*negative* reads Moderate or Extreme. That is the distinction a caregiver
actually needs.

---

## Why the baseline is mandatory

**This is the most important thing to be able to explain.**

Absolute band power differs by an **order of magnitude** between people,
between sessions, and between electrode placements — gel thickness alone moves
it. An arousal of 1.4 means nothing on its own. It only means something
against *this person's* resting 1.1.

So: 20 seconds of rest records their mean and spread, and every later reading
is expressed as *"how many standard deviations from their own rest."*

**Without it** the app still runs, but the thresholds are arbitrary numbers and
the state barely moves.

**One subtlety worth mentioning:** we floor the baseline spread
(`MIN_VALENCE_STD`, `MIN_AROUSAL_STD`). A very consistent 20-second baseline
produced an implausibly small standard deviation, which made ordinary drift
look like a huge deviation and pegged the display at its limits.

---

## The artifact guard

**The problem:** a blink or jaw clench is a large, brief spike that lands in
the same fast bands as real arousal. Without rejection, a facial twitch reads
as distress.

**The solution:** windows with samples past 120 µV are **held, not scored** —
the card dims and shows the reason.

**The subtlety that makes a good answer:** we judge **per channel**, not
across the window. Our first version averaged all 8 channels and missed
blinks entirely — a blink is brief and mostly frontal, so averaging diluted it
to 0.75%, under threshold. Judging each channel and letting the worst decide
catches it at ~6%.

| Window type | Caught? | Worst channel |
|---|---|---|
| Clean | No | 0% |
| Eyeblink | **Yes** | ~6% |
| Jaw clench | **Yes** | ~13% |
| Genuine high arousal | No | 0% |

**Memorable stat:** on recorded real EEG, roughly **a third of windows** carry
an artifact. On synthetic signal, zero. A discomfort detector without
rejection would be reporting muscle activity as distress a third of the time.

---

## Head movement (accelerometer)

**Shown, never used in the estimate.**

**Why it's there:** EEG alone cannot distinguish a distressed patient from one
shifting in bed — both raise fast-band power. Movement gives the caregiver
that context.

**Why it's not in the estimate:** the threshold is uncalibrated, and a false
confidence signal is worse than none.

---

## Likely questions

**"Why only 2 of 8 channels?"**
> All eight record fine — signal quality isn't the reason. It's that the two
> measurements we trust are both *defined* on the frontal pair: valence is
> frontal alpha asymmetry, which is specifically an Fp1-vs-Fp2 quantity, and
> frontal beta is the standard arousal index. Adding the other six would mean
> inventing a weighting we have no data to justify, so we'd be adding
> parameters rather than information. We record and display all eight so the
> narrowness is visible, and multi-channel fusion is the obvious next step —
> we didn't ship it because we couldn't validate it in time.

**"But you have 8 good channels — surely more data is better?"**
> Only if you know how to combine them. With no labelled affective data, any
> weighting across eight channels would be guessed, and a guessed weighting
> across eight inputs is easier to get wrong than a literature-backed formula
> on two. The posterior channels would be genuinely useful as *corroboration*
> — if occipital alpha tracks the frontal reading, that's evidence the signal
> is neural rather than artifact — but that's a validation step, not a bigger
> model.

**"How accurate is it?"**
> We don't have an accuracy number, and I'd be making one up if I gave you one.
> We have no labelled affective data from this hardware. The mappings come from
> the literature, not from fitting. Validating against self-report is the next
> step, and the logging path for it already exists.

**"Is this a pain detector?"**
> No. It reports a state estimate from band power. It can't diagnose and it
> isn't a medical device.

**"What if the patient moves?"**
> Two defences. Windows with a movement transient are rejected rather than
> scored, and the accelerometer shows whether the head was still — so a
> caregiver can see that an arousal rise coincided with movement.

**"Why Streamlit and not a notebook?"**
> It's a real-time tool for a caregiver, not an analysis. A notebook can't be a
> live glanceable display. The detection maths would be identical either way.

**"What's your false positive rate?"**
> Unknown, honestly — that needs labelled sessions we don't have yet. What we
> can say is that artifact rejection removes the most likely source of them.

**"What was hardest?"**
> Simulation hid the bugs that mattered. Three defects only appeared with real
> data: the board returns 24 rows not 8 (accelerometer and timestamps ride
> alongside the EEG), an empty buffer right after start crashed the estimator,
> and a flat channel produced a NaN that the moving average latched onto
> permanently. All three would have first appeared in front of a participant.

---

## Limitations — say these before you're asked

Volunteering them scores on Learning & Reflection. Being caught out doesn't.

1. **Two channels of eight** — deliberate trade, stated above
2. **No affective ground truth** — literature-based, not fitted
3. **EEG only** — no HR, respiration, or skin conductance
4. **Not a pain detector** — no clinical claim

Each has a next step, documented in the README.

---

## What to check before demoing

1. **Channel mapping** — blink test. The channels that jump are frontal. If
   they aren't 1–2, switch to `CHANNEL_NAMES_POSTERIOR_FIRST` in `emotion.py`.
2. **Record a baseline first** — without it the state barely moves and it looks
   broken.
3. **Quit the OpenBCI GUI completely** — it holds the serial port even on its
   start screen.
4. **Click the page once** before expecting sound — browsers block autoplay.
