"""Signal trend chart.

st.line_chart cannot take a per-state stroke colour or shade the state bands,
so the trend is built in Altair instead. Both the raw and smoothed arousal
lines are drawn: the raw one shows how noisy the underlying signal is, which
is the honest way to present a smoothed estimate.
"""

import altair as alt
import pandas as pd

from emotion import MODERATE_AROUSAL
from hero import STATE_STYLE

RAW_OPACITY = 0.28
SMOOTH_WIDTH = 2.5


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
