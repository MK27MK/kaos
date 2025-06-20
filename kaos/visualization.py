import pandas as pd

"""
Currently fkn around with different visualization methods,
but unsatisfied with all of them.
I'm consider using apache Echarts, 
but that would need some sort of wrapper.
"""

# colors ---------------------------------------------------------------
BG_COL = "#b2b5be"
UP_COL = "rgba(120, 123, 134, 100)"
CLR_BLACK = "rgba(0, 0, 0, 100)"
DOWN_COL = "rgba(42, 46, 57, 100)"

# Tradingview lightweight charts (unofficial python wrapper) -----------


def set_chart(df):
    import lightweight_charts as lw

    margin = 0.01
    chart = lw.JupyterChart()
    chart.candle_style(
        UP_COL,
        DOWN_COL,
        True,
        True,
        CLR_BLACK,
        CLR_BLACK,
        wick_up_color=CLR_BLACK,
        wick_down_color=CLR_BLACK,
    )
    chart.grid(False, False)
    chart.layout(BG_COL, CLR_BLACK, 10)
    chart.price_line(False, False)
    chart.crosshair(vert_color=CLR_BLACK, horz_color=CLR_BLACK)

    chart.price_scale(scale_margin_top=margin, scale_margin_bottom=margin)
    chart.precision(5)

    chart.set(df)

    return chart


# hvplot ---------------------------------------------------------------


def hvplot_ohlc(
    data: pd.DataFrame,
    title: str | None = None,
    precision: int = 5,
    fit_n_bars: int = 100,
):
    import holoviews as hv
    import hvplot.pandas
    from bokeh.models.formatters import DatetimeTickFormatter

    hv.extension("bokeh")
    hv.renderer("bokeh").theme = "dark_minimal"  # built-in Bokeh theme
    style = dict()
    # https://docs.bokeh.org/en/latest/docs/reference/models/formatters.html#bokeh.models.DatetimeTickFormatter
    # formatter = DatetimeTickFormatter(
    #     milliseconds=["%a %d %b '%y %H:%M"],
    #     seconds=["%a %d %b '%y %H:%M"],
    #     minutes=["%a %d %b '%y %H:%M"],
    #     hours=["%a %d %b '%y"],
    #     days=["%a %d %b '%y"],
    #     months=["%b '%y"],
    #     years=["%Y"],
    # )
    n = min(fit_n_bars, len(data))
    """Takes a df with a datetime index and ohlc columns"""
    return data.hvplot.ohlc(
        pos_color=UP_COL,
        neg_color=DOWN_COL,
        bgcolor=BG_COL,
        min_height=100,
        responsive=True,
        aspect=4 / 3,
        autorange="y",
        title=title,
        yaxis="right",
        yformatter=f"%.{precision}f",  # use  Instrument.precision
        fontscale=0.9,
        # xformatter=formatter,
        xlim=(data.index[-n], data.index[-1]),
    ).opts(**style)


# plotly ---------------------------------------------------------------


def plot(df, precision: int = 5):
    import plotly.graph_objects as go

    # NOTE: FigureWidget is used to enable autoscale y, but it breaks if you
    # display it as HTML to zoom with the mouse wheel
    fig = go.FigureWidget(
        data=[
            go.Candlestick(
                x=df.index,
                open=df["open"],
                high=df["high"],
                low=df["low"],
                close=df["close"],
                name="OHLC",
                increasing=dict(line=dict(color=UP_COL), fillcolor=UP_COL),
                decreasing=dict(line=dict(color=DOWN_COL), fillcolor=DOWN_COL),
            )
        ]
    )
    padding = 25
    fig.update_layout(
        autosize=True,
        height=500,
        xaxis_rangeslider_visible=True,  # slider sotto
        dragmode="pan",
        margin=dict(l=padding, r=padding, t=padding, b=padding),
        xaxis_rangeslider_yaxis_rangemode="auto",
        paper_bgcolor="#1c2026",
        # plot_bgcolor=BG_COL,
        font_color="white",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False, tickformat=f".{precision}f")

    # ---- callback that triggers when xaxis.range changes ----------------------
    def autoscale_y(layout, _):
        # current range of the X axis
        x0, x1 = fig.layout.xaxis.range
        # filter the visible data
        in_view = df.loc[x0:x1]

        if in_view.empty:
            return  # protection if the interval is empty

        ymin = in_view["low"].min()
        ymax = in_view["high"].max()
        pad = (ymax - ymin) * 0.03  # 3% of "air" (padding)

        # apply the new Y range
        fig.layout.yaxis.range = [ymin - pad, ymax + pad]

    # 'xaxis.range' is the property that changes with both the slider and zoom/pan
    fig.layout.on_change(autoscale_y, "xaxis.range")
    # fig.show(config={"scrollZoom": True})
    return fig
    # html_str = pio.to_html(fig, config={"scrollZoom": True}, include_plotlyjs="cdn")

    # # Show it directly
    # HTML(html_str)


if __name__ == "__main__":
    import panel as pn

    from kaos.data.loading import (
        Catalog,
        CSVPreset,
        firstrate_dirname,
        firstrate_filename,
    )

    catalog = Catalog()
    df = catalog.get_csv(
        catalog.raw_directory
        / "csv/firstrate"
        / firstrate_dirname()
        / firstrate_filename(),
        CSVPreset.FIRSTRATE,
    )

    chart = hvplot_ohlc(df)
    pn.panel(chart).servable()
    pn.serve(chart)
