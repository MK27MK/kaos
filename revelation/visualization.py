import holoviews as hv
import hvplot.pandas
import lightweight_charts as lw
import pandas as pd

hv.extension("bokeh")


def set_chart(df):

    clr_black = "rgba(0, 0, 0, 100)"
    margin = 0.01
    chart = lw.JupyterChart()
    chart.candle_style(
        "rgba(120, 123, 134, 100)",
        "rgba(42, 46, 57, 100)",
        True,
        True,
        clr_black,
        clr_black,
        wick_up_color=clr_black,
        wick_down_color=clr_black,
    )
    chart.grid(False, False)
    chart.layout("#9598a1", clr_black, 10)
    chart.price_line(False, False)
    chart.crosshair(vert_color=clr_black, horz_color=clr_black)

    chart.price_scale(scale_margin_top=margin, scale_margin_bottom=margin)
    chart.precision(5)

    chart.set(df)

    return chart


hv.renderer("bokeh").theme = "dark_minimal"  # built-in Bokeh theme


def hvplot_ohlc(data: pd.DataFrame, title: str | None = None, precision: int = 5):
    style = dict()
    """Takes a df with a datetime index and ohlc columns"""
    return data.hvplot.ohlc(
        pos_color="rgba(120, 123, 134, 100)",
        neg_color="rgba(42, 46, 57, 100)",
        bgcolor="#b2b5be",
        min_height=200,
        responsive=True,
        aspect=4 / 3,
        autorange="y",
        title=title,
        yaxis="right",
        yformatter=f"%.{precision}f",  # use intrument precision
        fontscale=0.9,
        # colorbar=True,
        legend="top_left",
        # tools=["reset"],
    ).opts(**style)


# def label_down(chart):
#     chart.marker(position="above", shape="arrow_down")
# help(chart.marker)
