from pathlib import Path

import empyrical as ep
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

from . import timeseries, utils


def plot_rolling_returns_df(
    returns: pd.DataFrame,
    output_dir: Path | str | None = None,
    *,
    factor_returns=None,
    live_start_date=None,
    logy=False,
    cone_std=None,
    legend_loc="best",
    volatility_match=False,
    cone_function=timeseries.forecast_cone_bootstrap,
    ax=None,
    **kwargs,
) -> pd.DataFrame:
    """
    Compound and plot each column of noncumulative returns, starting at 1.

    Parameters
    ----------
    returns : pd.DataFrame
        Numeric decimal returns with a DatetimeIndex, one strategy per column.
        Missing returns are treated as zero, as in Empyrical's cum_returns.
    output_dir : Path or str, optional
        Save cumulative_returns.png and cumulative_returns.csv here.
        The directory is created if necessary.
    factor_returns : pd.Series, optional
        Noncumulative benchmark returns covering the strategy dates.
    live_start_date : datetime, optional
        Start of live trading. Live segments use dashed lines in each
        strategy's color; backtest segments use solid lines.
    logy : bool, optional
        Use a logarithmic y-axis.
    cone_std : number or iterable of numbers, optional
        Forecast cone standard deviations, computed separately per strategy
        when both backtest and live observations exist.
    legend_loc : str or None, optional
        Legend location. None suppresses the legend.
    volatility_match : bool, optional
        Scale each strategy to the benchmark's volatility before compounding.
        Requires factor_returns and nonzero strategy volatility.
    cone_function : callable, optional
        Forecast function with the signature used by plot_rolling_returns.
    ax : matplotlib.axes.Axes, optional
        Axes to draw on; defaults to the current axes.
    **kwargs
        Passed to pandas Series.plot, overriding default line styles.

    Returns
    -------
    pd.DataFrame
        Cumulative growth of 1 for each strategy, after any volatility scaling.

    Notes
    -----
    A value of 1.05 represents a cumulative gain of 5%. Returns are compounded
    at the supplied frequency without resampling. Pass ax to access the plot.
    """
    if not isinstance(returns, pd.DataFrame):
        raise TypeError("returns must be a pd.DataFrame")
    if not isinstance(returns.index, pd.DatetimeIndex):
        raise TypeError("returns.index must be a pd.DatetimeIndex")
    if returns.empty:
        raise ValueError("returns must contain at least one row and column")
    if not all(pd.api.types.is_numeric_dtype(dtype) for dtype in returns.dtypes):
        raise TypeError("returns columns must be numeric")

    benchmark = None
    if volatility_match and factor_returns is None:
        raise ValueError("volatility_match requires passing of factor_returns.")
    if factor_returns is not None:
        benchmark = factor_returns.loc[returns.index]
    if volatility_match:
        volatility = returns.std()
        if volatility.isna().any() or (volatility == 0).any():
            raise ValueError("volatility_match requires nonzero strategy volatility")
        returns = returns.div(volatility).mul(benchmark.std())

    cum_returns = ep.cum_returns(returns, starting_value=1.0)
    live = pd.Series(False, index=returns.index)
    if live_start_date is not None:
        start = utils._comparable_live_start(live_start_date, returns.index)
        live = returns.index >= start
    deviations = [] if cone_std is None else cone_std
    if isinstance(deviations, (float, int)):
        deviations = [deviations]
    deviations = list(deviations)

    if ax is None:
        ax = plt.gca()
    ax.set_xlabel("")
    ax.set_ylabel("Cumulative returns")
    ax.set_yscale("log" if logy else "linear")
    ax.yaxis.set_major_formatter(FuncFormatter(utils.two_dec_places))

    if benchmark is not None:
        benchmark_style = dict(
            lw=2, color="gray", alpha=0.6, label=str(benchmark.name)
        )
        benchmark_style.update(kwargs)
        benchmark_style["legend"] = False
        ep.cum_returns(benchmark, starting_value=1.0).plot(
            ax=ax, **benchmark_style
        )

    for position, column in enumerate(returns.columns):
        cumulative = cum_returns.iloc[:, position]
        style = dict(lw=2, alpha=0.6)
        style.update(kwargs)
        style["legend"] = False
        if "color" not in style:
            style["color"] = ax._get_lines.get_next_color()
        color = style["color"]
        backtest, live_returns = cumulative.loc[~live], cumulative.loc[live]
        if not backtest.empty:
            label = f"{column} (Backtest)" if live_start_date is not None else str(column)
            backtest.plot(ax=ax, **dict(style, label=label))
        if not live_returns.empty:
            live_returns.plot(
                ax=ax,
                **dict(style, linestyle="--", label=f"{column} (Live)"),
            )
        if deviations and not backtest.empty and not live_returns.empty:
            bounds = cone_function(
                returns.iloc[:, position].loc[~live],
                len(live_returns),
                cone_std=deviations,
                starting_value=backtest.iloc[-1],
            ).set_index(live_returns.index)
            for deviation in deviations:
                ax.fill_between(
                    bounds.index,
                    bounds[float(deviation)],
                    bounds[-float(deviation)],
                    color=color,
                    alpha=0.15,
                )

    ax.axhline(1.0, linestyle="--", color="black", lw=1)
    if legend_loc is not None:
        ax.legend(loc=legend_loc, frameon=True, framealpha=0.5)
    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        ax.figure.savefig(output_dir / "cumulative_returns.png", bbox_inches="tight")
        cum_returns.to_csv(output_dir / "cumulative_returns.csv")
    return cum_returns
