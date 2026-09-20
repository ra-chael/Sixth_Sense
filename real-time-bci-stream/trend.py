"""Signal trend chart.

st.line_chart cannot take a per-state stroke colour or shade the state bands,
so the trend is built in Altair instead. Both the raw and smoothed arousal
lines are drawn: the raw one shows how noisy the underlying signal is, which
is the honest way to present a smoothed estimate.
"""

import altair as alt
import numpy as np
import pandas as pd

from emotion import MODERATE_AROUSAL
from hero import STATE_STYLE

RAW_OPACITY = 0.28
SMOOTH_WIDTH = 2.5


def render_raw(window, labels, night=False):
    """Raw EEG traces, stacked one channel per row.

    st.line_chart sorts its legend alphabetically, which silently remapped
    every trace to the wrong 10-20 site (C3 appeared first when the data's
    first row is Fp1). Building it here keeps the montage order, and one row
    per channel is readable where eight overlaid traces were not.
    """
    window = np.asarray(window)
    n_ch, n_samples = window.shape

    axis_color = "#AA9C8C" if night else "#7A6D5F"
    frontal = {"Fp1", "Fp2"}

    frames = []
    for i, name in enumerate(labels):
        frames.append(
            pd.DataFrame(
                {
                    "sample": np.arange(n_samples),
                    "uV": window[i],
                    "channel": name,
                    "order": i,
                    "role": "frontal (drives estimate)"
                    if name in frontal
                    else "other",
                }
            )
        )
    df = pd.concat(frames, ignore_index=True)

    return (
        alt.Chart(df)
        .mark_line(strokeWidth=1)
        .encode(
            x=alt.X("sample:Q", title="sample (250 = 1 second)",
                    axis=alt.Axis(labelColor=axis_color, titleColor=axis_color)),
            y=alt.Y("uV:Q", title=None,
                    axis=alt.Axis(labelColor=axis_color, tickCount=3)),
            # Sorting on the row's index keeps electrode order, not A-Z.
            row=alt.Row(
                "channel:N",
                sort=alt.EncodingSortField(field="order", order="ascending"),
                title=None,
                header=alt.Header(labelAngle=0, labelAlign="left",
                                  labelColor=axis_color, labelFontSize=11),
            ),
            color=alt.Color(
                "role:N",
                title=None,
                scale=alt.Scale(
                    domain=["frontal (drives estimate)", "other"],
                    range=["#DE9788" if night else "#CC8377",
                           "#6E7B8A" if night else "#9AA7B4"],
                ),
                legend=alt.Legend(orient="top", labelColor=axis_color),
            ),
        )
        .properties(height=38)
        .configure_view(strokeWidth=0)
        .configure(background="transparent")
    )


def render(trend_rows, state, night=False):
    """Build the trend chart. trend_rows is the app's rolling window."""
    df = pd.DataFrame(list(trend_rows))
    if len(df) < 2:
        return None

    style = STATE_STYLE.get(state, STATE_STYLE["Stable"])
    core = style["coreDark"] if night else style["core"]

    axis_color = "#AA9C8C" if night else "#7A6D5F"
    grid_color = "#3B3340" if night else "#E8DFD1"

    long = df.melt(
        id_vars="t",
        value_vars=["arousal", "valence"],
        var_name="measure",
        value_name="value",
    )

    base = alt.Chart(long).encode(
        x=alt.X(
            "t:T",
            title=None,
            axis=alt.Axis(format="%H:%M:%S", labelColor=axis_color, grid=False),
        ),
        y=alt.Y(
            "value:Q",
            title=None,
            scale=alt.Scale(domain=[-1, 1]),
            axis=alt.Axis(labelColor=axis_color, gridColor=grid_color),
        ),
    )

    # Arousal carries the state colour; valence stays neutral so the two are
    # distinguishable without a legend lookup.
    lines = base.transform_filter(alt.datum.measure == "arousal").mark_line(
        strokeWidth=SMOOTH_WIDTH, color=core, interpolate="monotone"
    )

    valence_line = base.transform_filter(alt.datum.measure == "valence").mark_line(
        strokeWidth=1.4,
        color=axis_color,
        opacity=0.65,
        strokeDash=[4, 3],
        interpolate="monotone",
    )

    # The threshold the state logic actually uses, so the chart and the state
    # badge cannot appear to disagree.
    rule = (
        alt.Chart(pd.DataFrame({"y": [MODERATE_AROUSAL]}))
        .mark_rule(strokeDash=[2, 4], color=axis_color, opacity=0.5)
        .encode(y="y:Q")
    )

    chart = (
        (rule + valence_line + lines)
        .properties(height=240)
        .configure_view(strokeWidth=0)
        .configure(background="transparent")
    )

    return chart
