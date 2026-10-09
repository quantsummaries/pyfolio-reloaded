# pyfolio.plotting

`src/pyfolio/plotting.py` contains the plotting and table-display helpers used
by the tear sheets in `pyfolio.tears`. Every function can also be used on its
own to draw a single chart or print a single table. All functions are
re-exported at the package root (`from .plotting import *`), so
`pyfolio.plot_rolling_returns(...)` works as well as
`pyfolio.plotting.plot_rolling_returns(...)`.

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
- [Input data model](#input-data-model)
- [Styling and context management](#styling-and-context-management)
  - [`customize`](#customizefunc)
  - [`plotting_context`](#plotting_contextcontextnotebook-font_scale15-rcnone)
  - [`axes_style`](#axes_stylestyledarkgrid-rcnone)
- [Returns](#returns)
- [Rolling statistics](#rolling-statistics)
- [Drawdowns](#drawdowns)
- [Performance statistics tables](#performance-statistics-tables)
- [Positions and exposures](#positions-and-exposures)
- [Transactions, turnover, and slippage](#transactions-turnover-and-slippage)
- [Capacity](#capacity)
- [Round trips](#round-trips)
- [Forecast cones](#forecast-cones)
- [Module-level objects](#module-level-objects)
- [Dependencies](#dependencies)
  - [Function dependency overview](#function-dependency-overview)
  - [Per-function dependencies](#per-function-dependencies)
  - [Indirect dependencies](#indirect-dependencies)
  - [Who depends on `plotting`](#who-depends-on-plotting)
- [Practical usage](#practical-usage)
- [Notes](#notes)

## Overview

| Area | Functions |
| --- | --- |
| Styling | `customize`, `plotting_context`, `axes_style` |
| Returns | `plot_returns`, `plot_rolling_returns`, `plot_monthly_returns_heatmap`, `plot_annual_returns`, `plot_monthly_returns_dist`, `plot_monthly_returns_timeseries`, `plot_return_quantiles` |
| Rolling statistics | `plot_rolling_beta`, `plot_rolling_volatility`, `plot_rolling_sharpe` |
| Drawdowns | `plot_drawdown_periods`, `plot_drawdown_underwater`, `show_worst_drawdown_periods` |
| Performance tables | `show_perf_stats`, `plot_perf_stats` |
| Positions | `plot_holdings`, `plot_long_short_holdings`, `plot_gross_leverage`, `plot_exposures`, `show_and_plot_top_positions`, `plot_max_median_position_concentration`, `plot_sector_allocations` |
| Transactions | `plot_turnover`, `plot_daily_turnover_hist`, `plot_daily_volume`, `plot_txn_time_hist`, `plot_slippage_sweep`, `plot_slippage_sensitivity` |
| Capacity | `plot_capacity_sweep` |
| Round trips | `plot_round_trip_lifetimes`, `show_profit_attribution`, `plot_prob_profit_trade` |
| Forecast cones | `plot_cones` |

## Conventions

- **The `ax` argument.** Almost every `plot_*` function takes `ax`
  (`matplotlib.Axes`, optional). If omitted, the function draws on the current
  axes (`plt.gca()`); `plot_round_trip_lifetimes` and `plot_prob_profit_trade`
  use `plt.subplot()` instead. Tear sheets pass pre-created grid axes.
- **Return value.** `plot_*` functions return the `Axes` that was drawn on.
  `show_*` functions print or display a table and return `None`, except
  `show_perf_stats(..., return_df=True)`, which returns the DataFrame.
  Exceptions are noted per function.
- **`**kwargs`.** Most functions accept extra keyword arguments that are passed
  to the underlying pandas, matplotlib, or seaborn call. A few (listed under
  [Notes](#notes)) accept or document `**kwargs` but ignore them.
- **Returns arguments.** `returns` is a daily, non-cumulative `pd.Series`;
  `factor_returns` is a benchmark series in the same style. Several plots set
  the x-axis range to `returns.index[0]` through `returns.index[-1]`.
- **Percent axes.** Several plots use `utils.percentage` or
  `utils.two_dec_places` tick formatters.

## Input data model

| Argument | Type | Description |
| --- | --- | --- |
| `returns` | `pd.Series` | Daily, non-cumulative decimal returns indexed by date. |
| `factor_returns` | `pd.Series` | Daily, non-cumulative benchmark returns, in the same style as `returns`. |
| `positions` | `pd.DataFrame` | Daily net position values (dollars per asset) plus a `cash` column. |
| `positions_alloc` | `pd.DataFrame` | Portfolio allocation (fractions of portfolio), from `pos.get_percent_alloc`. |
| `sector_alloc` | `pd.DataFrame` | Sector allocation over time, with the `cash` column dropped. |
| `transactions` | `pd.DataFrame` | One row per trade, timestamp index, with `amount`, `price`, and `symbol`. |
| `market_data` | `pd.DataFrame` | Daily price and volume data, multi-level index, equities as columns. |
| `round_trips` | `pd.DataFrame` | One row per round-trip trade, from `round_trips.extract_round_trips`. |

For full descriptions of these structures, see `tears.create_full_tear_sheet`.

## Styling and context management

### `customize(func)`

Decorator that wraps a function so that it runs inside pyfolio's default
seaborn plotting context and axes style. The wrapper pops a keyword argument
`set_context` (default `True`) from the call; when `False`, the function runs
with the caller's current style. All tear-sheet functions except
`create_full_tear_sheet` use this decorator.

### `plotting_context(context="notebook", font_scale=1.5, rc=None)`

Returns `sns.plotting_context(...)` with pyfolio defaults, intended for use in
a `with` block. `rc` defaults to `{"lines.linewidth": 1.5}`; any value passed
in `rc` takes priority.

| Parameter | Description |
| --- | --- |
| `context` | Name of the seaborn context. |
| `font_scale` | Font scaling factor. |
| `rc` | Config flags (dict). |

### `axes_style(style="darkgrid", rc=None)`

Returns `sns.axes_style(...)` with the pyfolio default style (`"darkgrid"`),
intended for use in a `with` block.

## Returns

| Function | Description |
| --- | --- |
| `plot_returns(returns, live_start_date=None, ax=None)` | Raw daily returns over time. Backtest returns are green, out-of-sample (live) returns are red. |
| `plot_rolling_returns(returns, factor_returns=None, live_start_date=None, logy=False, cone_std=None, legend_loc="best", volatility_match=False, cone_function=timeseries.forecast_cone_bootstrap, ax=None, **kwargs)` | Cumulative returns versus an optional benchmark. Backtest in green, live in red, benchmark in gray, with a horizontal reference line at 1.0. |
| `plot_monthly_returns_heatmap(returns, ax=None, **kwargs)` | Heatmap of returns by year (rows) and month (columns), annotated in percent. `**kwargs` go to `sns.heatmap`. |
| `plot_annual_returns(returns, ax=None, **kwargs)` | Horizontal bar chart of yearly returns with a dashed line at the mean. |
| `plot_monthly_returns_dist(returns, ax=None, **kwargs)` | 20-bin histogram of monthly returns with the mean marked. |
| `plot_monthly_returns_timeseries(returns, ax=None, **kwargs)` | Bar chart of monthly cumulative returns, with x-labels only at year boundaries. |
| `plot_return_quantiles(returns, live_start_date=None, ax=None, **kwargs)` | Box plots of the daily, weekly, and monthly return distributions. With `live_start_date`, the box plots use in-sample returns and out-of-sample points are overlaid as red diamonds. |

### `plot_rolling_returns` options

| Parameter | Description |
| --- | --- |
| `factor_returns` | Benchmark series; also used by `volatility_match`. |
| `live_start_date` | Splits the series into backtest and live segments. Should be normalized. |
| `logy` | Log-scales the y-axis. |
| `cone_std` | Float or tuple of standard deviations for the forecast cone drawn over the out-of-sample region. Only drawn when there is out-of-sample data. |
| `legend_loc` | Legend location; `None` hides the legend. |
| `volatility_match` | Rescales `returns` to the benchmark's volatility. Raises `ValueError` if `factor_returns` is `None`. |
| `cone_function` | Function that produces the cone, called as `cone(in_sample_returns, days_to_project_forward, cone_std=..., starting_value=...)`. Defaults to `timeseries.forecast_cone_bootstrap`. |

## Rolling statistics

| Function | Description |
| --- | --- |
| `plot_rolling_beta(returns, factor_returns, legend_loc="best", ax=None, **kwargs)` | Rolling 6-month and 12-month beta to the benchmark, with the 6-month average and a reference line at 1.0. Windows are `APPROX_BDAYS_PER_MONTH * 6` and `* 12`. |
| `plot_rolling_volatility(returns, factor_returns=None, rolling_window=APPROX_BDAYS_PER_MONTH * 6, legend_loc="best", ax=None, **kwargs)` | Rolling volatility, optionally with benchmark volatility, plus the average. |
| `plot_rolling_sharpe(returns, factor_returns=None, rolling_window=APPROX_BDAYS_PER_MONTH * 6, legend_loc="best", ax=None, **kwargs)` | Rolling Sharpe ratio, optionally with the benchmark's, plus the average. |

`rolling_window` is the number of days in the window.

## Drawdowns

| Function | Description |
| --- | --- |
| `plot_drawdown_periods(returns, top=10, ax=None, **kwargs)` | Cumulative returns with the top `top` drawdown periods shaded (uses `timeseries.gen_drawdown_table`). Unrecovered drawdowns are shaded to the end of the series. |
| `plot_drawdown_underwater(returns, ax=None, **kwargs)` | Area chart of the percentage drawdown from the running peak over time. |
| `show_worst_drawdown_periods(returns, top=5)` | Prints a "Worst drawdown periods" table (peak, valley, and recovery dates, net drawdown in %), sorted by net drawdown. Returns `None`. |

## Performance statistics tables

### `show_perf_stats(returns, factor_returns=None, positions=None, transactions=None, turnover_denom="AGB", live_start_date=None, bootstrap=False, header_rows=None, return_df=False)`

Prints a performance statistics table (for example Sharpe ratio, annual
return, max drawdown, alpha, and beta, as computed by `timeseries.perf_stats`).

- With `live_start_date`, statistics are shown in three columns: "In-sample",
  "Out-of-sample", and "All", along with month counts for each period. Without
  it there is one "Backtest" column and a total month count.
- A header section shows start and end dates and the month counts; entries in
  `header_rows` are added to it.
- Statistics named in `STAT_FUNCS_PCT` are formatted as percentages.
- With `bootstrap=True`, `timeseries.perf_stats_bootstrap` is used instead.
- With `return_df=True`, the DataFrame is returned and nothing is printed.

| Parameter | Description |
| --- | --- |
| `factor_returns` | Benchmark used for alpha and beta. |
| `positions`, `transactions` | Enable turnover-related statistics. |
| `turnover_denom` | `"AGB"` or `"portfolio_value"`; see `txn.get_turnover`. |
| `live_start_date` | Split between backtest and live. |
| `header_rows` | Extra rows at the top of the table (dict or `OrderedDict`). |

### `plot_perf_stats(returns, factor_returns, ax=None)`

Horizontal box plots of bootstrapped performance metrics, from
`timeseries.perf_stats_bootstrap(..., return_stats=False)`. The `Kurtosis`
column is dropped. Whisker widths come from the bootstrap.

## Positions and exposures

| Function | Description |
| --- | --- |
| `plot_holdings(returns, positions, legend_loc="best", ax=None, **kwargs)` | Number of assets with an active (long or short) position: daily count, monthly average, and overall average. `positions` must include `cash`, which is dropped. |
| `plot_long_short_holdings(returns, positions, legend_loc="upper left", ax=None, **kwargs)` | Number of long and short holdings as filled regions, with an "Overlap" entry; max and min counts appear in the legend. |
| `plot_gross_leverage(returns, positions, ax=None, **kwargs)` | Gross leverage (from `timeseries.gross_lev`) with its mean as a dashed line. |
| `plot_exposures(returns, positions, ax=None, **kwargs)` | Long, short, and net exposure over time, each as a fraction of total portfolio value. |
| `show_and_plot_top_positions(returns, positions_alloc, show_and_plot=2, hide_positions=False, legend_loc="real_best", ax=None, **kwargs)` | Prints and/or plots the top 10 long, short, and absolute positions of all time. |
| `plot_max_median_position_concentration(positions, ax=None, **kwargs)` | Max and median long and short position concentration over time (from `pos.get_max_median_position_concentration`). |
| `plot_sector_allocations(returns, sector_alloc, ax=None, **kwargs)` | Sector allocation over time with the legend below the plot. |

### `show_and_plot_top_positions` options

| Parameter | Description |
| --- | --- |
| `show_and_plot` | `2` (default) prints and plots; `1` only prints; `0` only plots. |
| `hide_positions` | Removes the legend so no symbol names are displayed. Table output is unaffected; use `show_and_plot=0` to suppress the tables. |
| `legend_loc` | `"real_best"` shrinks the plot by 10% and places the legend beneath it; any other value is passed to `ax.legend`. |

The function returns `ax` only when it plots (`show_and_plot` of `0` or `2`);
with `1` it returns `None`. Column names are converted with
`utils.format_asset`.

## Transactions, turnover, and slippage

| Function | Description |
| --- | --- |
| `plot_turnover(returns, transactions, positions, turnover_denom="AGB", legend_loc="best", ax=None, **kwargs)` | Daily turnover (from `txn.get_turnover`), its monthly average, and its overall average. The y-axis is fixed to 0–2. |
| `plot_daily_turnover_hist(transactions, positions, turnover_denom="AGB", ax=None, **kwargs)` | Histogram of daily turnover rates (`sns.histplot`). |
| `plot_daily_volume(returns, transactions, ax=None, **kwargs)` | Shares traded per day with the all-time daily average (from `txn.get_txn_vol`). |
| `plot_txn_time_hist(transactions, bin_minutes=5, tz="America/New_York", ax=None, **kwargs)` | Share of traded dollar value by time of day, in `bin_minutes` buckets. |
| `plot_slippage_sweep(returns, positions, transactions, slippage_params=(3, 8, 10, 12, 15, 20, 50), ax=None, **kwargs)` | Cumulative returns after applying each slippage level (bps) via `txn.adjust_returns_for_slippage`. |
| `plot_slippage_sensitivity(returns, positions, transactions, ax=None, **kwargs)` | Average annual return as a function of per-dollar slippage, for 1–99 bps. |

Notes on `plot_txn_time_hist`: the transaction index must be timezone-aware
(it is converted to `tz`), the x-axis covers 570–960 minutes after midnight
(09:30–16:00 in the chosen time zone), and `tz` should observe daylight saving
time if the data does, or the distribution may be offset.

## Capacity

### `plot_capacity_sweep(returns, transactions, market_data, bt_starting_capital, min_pv=100000, max_pv=300000000, step_size=1000000, ax=None)`

Plots projected Sharpe ratio against capital base (in $ millions). For each
starting portfolio value from `min_pv` to `max_pv` in `step_size` increments,
returns are adjusted with `capacity.apply_slippage_penalty` using daily
transactions joined with bar data (`capacity.daily_txns_with_bar_data`). The
sweep stops at the first capital base whose Sharpe ratio falls below -1. The
function has no docstring.

| Parameter | Description |
| --- | --- |
| `bt_starting_capital` | Starting capital of the backtest. |
| `min_pv`, `max_pv`, `step_size` | Range and increment of capital bases tested. |
| `market_data` | Price and volume data for the traded assets. |

## Round trips

| Function | Description |
| --- | --- |
| `plot_round_trip_lifetimes(round_trips, disp_amount=16, lsize=18, ax=None)` | Timespans and directions of a sample of round trips: blue bars are long trades, red bars are short. Samples up to `disp_amount` symbols, using `np.random.seed(1)`. `lsize` sets the bar width. |
| `show_profit_attribution(round_trips)` | Prints each traded name's share of total PnL. Returns `None`. |
| `plot_prob_profit_trade(round_trips, ax=None)` | Beta-distribution estimate of the probability that a trade is profitable; vertical lines mark the 2.5th and 97.5th percentiles. |

`round_trips` is the DataFrame produced by `round_trips.extract_round_trips`.

## Forecast cones

### `plot_cones(name, bounds, oos_returns, num_samples=1000, ax=None, cone_std=(1.0, 1.5, 2.0), random_seed=None, num_strikes=3)`

Plots upper and lower bounds of an n-standard-deviation cone of forecasted
cumulative returns against actual out-of-sample returns. A new cone is drawn
(in a new color) whenever cumulative returns fall below the -2 standard
deviation bound of the last cone, up to `num_strikes` redraws.

| Parameter | Description |
| --- | --- |
| `name` | Title of the figure; no title if `None`. |
| `bounds` | DataFrame of cone boundaries; column names are floats of standard deviations above (positive) or below (negative) the projected mean. |
| `oos_returns` | Non-cumulative out-of-sample returns. |
| `ax` | Axes to draw on. |
| `cone_std` | Standard deviations to draw. |
| `num_strikes` | Upper limit on the number of cones drawn (0–3). |

If `ax` is given, it is modified and returned. Otherwise a new
`matplotlib.figure.Figure` (with an Agg canvas) is created and **the figure** is
returned, which can be saved without displaying it. `num_samples` and
`random_seed` are documented but not used by this function's code.

## Module-level objects

### `STAT_FUNCS_PCT`

List of statistic names that `show_perf_stats` formats as percentages:
`Annual return`, `Cumulative returns`, `Annual volatility`, `Max drawdown`,
`Daily value at risk`, `Daily turnover`.

## Dependencies

- **pyfolio modules:** `capacity` (`daily_txns_with_bar_data`,
  `apply_slippage_penalty`), `pos` (`get_top_long_short_abs`,
  `get_max_median_position_concentration`), `timeseries` (`perf_stats`,
  `perf_stats_bootstrap`, `gen_drawdown_table`, `rolling_beta`,
  `rolling_volatility`, `rolling_sharpe`, `gross_lev`,
  `forecast_cone_bootstrap`), `txn` (`get_turnover`, `get_txn_vol`,
  `adjust_returns_for_slippage`), and `utils` (`print_table`, `format_asset`,
  `percentage`, `two_dec_places`, `APPROX_BDAYS_PER_MONTH`, `MM_DISPLAY_UNIT`).
- **Third-party:** `empyrical`, `matplotlib` (including `patches`, `pyplot`,
  `figure`, `FigureCanvasAgg`, `FuncFormatter`), `numpy`, `pandas`, `pytz`,
  `scipy`, `seaborn`.
- **Standard library:** `calendar`, `datetime`, `collections.OrderedDict`,
  `functools.wraps`.

The tear sheets in `pyfolio.tears` are the main consumers of this module.
`plotting` itself does not import `tears`.

### Function dependency overview

Functions in `plotting.py` are independent of each other: no `plot_*` or
`show_*` function calls another one. The only internal link is the
`customize` decorator, which calls `plotting_context` and `axes_style`.

```text
customize
├── plotting_context   → seaborn.plotting_context
└── axes_style         → seaborn.axes_style

plot_* / show_*        → leaf functions (call other pyfolio modules and
                         third-party libraries only)
```

Dependencies on other `pyfolio` modules group as follows:

| `pyfolio` module | Called by |
| --- | --- |
| `timeseries` | `plot_drawdown_periods`, `plot_perf_stats`, `show_perf_stats`, `plot_rolling_returns` (default `cone_function`), `plot_rolling_beta`, `plot_rolling_volatility`, `plot_rolling_sharpe`, `plot_gross_leverage`, `show_worst_drawdown_periods` |
| `pos` | `show_and_plot_top_positions`, `plot_max_median_position_concentration` |
| `txn` | `plot_turnover`, `plot_daily_turnover_hist`, `plot_daily_volume`, `plot_slippage_sweep`, `plot_slippage_sensitivity` |
| `capacity` | `plot_capacity_sweep` |
| `utils` | tick formatters (`percentage`, `two_dec_places`), `print_table`, `format_asset`, and the constants `APPROX_BDAYS_PER_MONTH` and `MM_DISPLAY_UNIT` |

### Per-function dependencies

For each function, the table lists the functions it calls from other
`pyfolio` modules and the third-party or standard-library calls it relies on.
Functions that only use pandas and matplotlib methods on their arguments (for
example `.plot()` or `.resample()`) are shown with a dash for those columns.

| Function | `pyfolio` modules | Third-party / standard library |
| --- | --- | --- |
| `customize` | `plotting_context`, `axes_style` (same module) | `functools.wraps` |
| `plotting_context` | — | `seaborn.plotting_context` |
| `axes_style` | — | `seaborn.axes_style` |
| `plot_monthly_returns_heatmap` | — | `empyrical` (`aggregate_returns`), `seaborn` (`heatmap`), `matplotlib` (`cm`), `calendar` |
| `plot_annual_returns` | `utils.percentage` | `empyrical` (`aggregate_returns`), `pandas`, `matplotlib` (`FuncFormatter`) |
| `plot_monthly_returns_dist` | `utils.percentage` | `empyrical` (`aggregate_returns`), `matplotlib` (`FuncFormatter`) |
| `plot_holdings` | — | `numpy`, `pandas` methods |
| `plot_long_short_holdings` | — | `numpy`, `matplotlib` (`patches`) |
| `plot_drawdown_periods` | `utils.two_dec_places`, `timeseries.gen_drawdown_table` | `empyrical` (`cum_returns`), `seaborn` (`cubehelix_palette`), `pandas`, `matplotlib` (`FuncFormatter`) |
| `plot_drawdown_underwater` | `utils.percentage` | `empyrical` (`cum_returns`), `numpy`, `matplotlib` (`FuncFormatter`) |
| `plot_perf_stats` | `timeseries.perf_stats_bootstrap` | `seaborn` (`boxplot`) |
| `show_perf_stats` | `timeseries.perf_stats` or `timeseries.perf_stats_bootstrap`, `utils.print_table`, `utils.APPROX_BDAYS_PER_MONTH` | `empyrical` (`utils.get_utc_timestamp`), `pandas`, `numpy`, `collections.OrderedDict` |
| `plot_returns` | — | `empyrical` (`utils.get_utc_timestamp`) |
| `plot_rolling_returns` | `utils.two_dec_places`, `timeseries.forecast_cone_bootstrap` (default `cone_function`) | `empyrical` (`cum_returns`, `utils.get_utc_timestamp`), `pandas`, `matplotlib` (`FuncFormatter`) |
| `plot_rolling_beta` | `utils.two_dec_places`, `utils.APPROX_BDAYS_PER_MONTH`, `timeseries.rolling_beta` | `matplotlib` (`FuncFormatter`) |
| `plot_rolling_volatility` | `utils.two_dec_places`, `utils.APPROX_BDAYS_PER_MONTH` (default window), `timeseries.rolling_volatility` | `matplotlib` (`FuncFormatter`) |
| `plot_rolling_sharpe` | `utils.two_dec_places`, `utils.APPROX_BDAYS_PER_MONTH` (default window), `timeseries.rolling_sharpe` | `matplotlib` (`FuncFormatter`) |
| `plot_gross_leverage` | `timeseries.gross_lev` | — |
| `plot_exposures` | — | — |
| `show_and_plot_top_positions` | `utils.format_asset`, `utils.print_table`, `pos.get_top_long_short_abs` | `pandas` |
| `plot_max_median_position_concentration` | `pos.get_max_median_position_concentration` | — |
| `plot_sector_allocations` | — | — |
| `plot_return_quantiles` | — | `empyrical` (`aggregate_returns`), `seaborn` (`boxplot`, `swarmplot`), `matplotlib` (`lines.Line2D`) |
| `plot_turnover` | `utils.two_dec_places`, `txn.get_turnover` | `matplotlib` (`FuncFormatter`) |
| `plot_slippage_sweep` | `txn.adjust_returns_for_slippage` | `empyrical` (`cum_returns`), `pandas` |
| `plot_slippage_sensitivity` | `txn.adjust_returns_for_slippage` | `empyrical` (`annual_return`), `pandas`, `numpy` |
| `plot_capacity_sweep` | `capacity.daily_txns_with_bar_data`, `capacity.apply_slippage_penalty`, `utils.MM_DISPLAY_UNIT` | `empyrical` (`sharpe_ratio`), `pandas` |
| `plot_daily_turnover_hist` | `txn.get_turnover` | `seaborn` (`histplot`) |
| `plot_daily_volume` | `txn.get_txn_vol` | — |
| `plot_txn_time_hist` | — | `pytz`, `datetime` |
| `show_worst_drawdown_periods` | `timeseries.gen_drawdown_table`, `utils.print_table` | — |
| `plot_monthly_returns_timeseries` | — | `empyrical` (`cum_returns`), `seaborn` (`barplot`), `matplotlib` (`pyplot`) |
| `plot_round_trip_lifetimes` | `utils.format_asset` | `numpy`, `pandas`, `matplotlib` (`patches`) |
| `show_profit_attribution` | `utils.format_asset`, `utils.print_table` | — |
| `plot_prob_profit_trade` | — | `scipy` (`stats.beta`), `numpy` |
| `plot_cones` | — | `empyrical` (`cum_returns`), `matplotlib` (`figure`, `FigureCanvasAgg`) |

### Indirect dependencies

The `pyfolio` functions that `plotting` calls depend on further modules at
the function and import level:

- `timeseries` imports `deprecate`, `interesting_periods`, `txn`, and `utils`,
  and uses `empyrical`, `scipy`, and `scikit-learn`. Its statistics, drawdown
  and cone functions are called by `show_perf_stats`, `plot_drawdown_periods`,
  and `plot_rolling_returns`. See [`timeseries.md`](timeseries.md).
- `utils` imports `pos` and `txn`, `IPython.display`, `matplotlib.pyplot`,
  `packaging`, and `empyrical.utils`.
- `capacity` imports `pos`; `txn` and `pos` import only pandas/numpy (and, for
  `pos`, optionally `zipline.assets`).

Because `plotting` imports `timeseries` and `utils` at module load, importing
`plotting` pulls in `scipy`, `scikit-learn`, `IPython`, and `packaging`, even
if you only call a plot that uses none of them.

### Who depends on `plotting`

- `pyfolio.tears` calls `plotting.customize` as a decorator on all but one
  tear sheet, and calls the `plot_*` and `show_*` functions to build the
  figures.
- `pyfolio.__init__` re-exports everything with `from .plotting import *`.
- `plotting` is imported by no other `pyfolio` module.

## Practical usage

```python
import matplotlib.pyplot as plt
import pyfolio as pf

# Single chart on the current axes
pf.plotting.plot_rolling_returns(returns, factor_returns=benchmark_rets)

# Chart on a chosen axes in your own layout
fig, axes = plt.subplots(2, 1, figsize=(12, 8))
pf.plotting.plot_drawdown_underwater(returns, ax=axes[0])
pf.plotting.plot_rolling_sharpe(returns, ax=axes[1])
fig.savefig("charts.png", dpi=150, bbox_inches="tight")

# Print the stats table, or get it as a DataFrame
pf.plotting.show_perf_stats(returns, factor_returns=benchmark_rets)
stats = pf.plotting.show_perf_stats(returns, return_df=True)

# Use pyfolio's style around your own code
with pf.plotting.plotting_context(), pf.plotting.axes_style():
    pf.plotting.plot_monthly_returns_heatmap(returns)
```

## Notes

- `plot_returns` documents `**kwargs`, but its signature is
  `plot_returns(returns, live_start_date=None, ax=None)` and does not accept
  them.
- `plot_exposures` documents a `positions_alloc` argument, but the actual
  argument is `positions` (dollar positions including `cash`). Its docstring
  also describes it as a "cake chart"; the code draws a time series of long,
  short, and net exposure.
- `plot_monthly_returns_timeseries` draws with `sns.barplot` and `plt.xticks`
  on the current axes rather than on `ax`, so passing `ax` may not place the
  bars on the intended axes.
- `plot_perf_stats` takes no `**kwargs`. These functions accept `**kwargs` but
  never use them: `plot_long_short_holdings`, `plot_exposures`,
  `plot_max_median_position_concentration`, `plot_slippage_sweep`,
  `plot_slippage_sensitivity`, and `plot_monthly_returns_timeseries`.
- `show_profit_attribution` documents `ax` and a return value, but takes no
  `ax` and returns `None`.
- `plot_prob_profit_trade` adds a `profitable` column to the `round_trips`
  DataFrame passed in, modifying the caller's data.
- `plot_round_trip_lifetimes` calls `np.random.seed(1)`, which resets NumPy's
  global random state.
- `show_perf_stats` splits transactions at `live_start_date` with `<` for
  in-sample and `>` for out-of-sample, so a transaction exactly at the split
  timestamp falls in neither period, while returns and positions use `>=`.
- `plot_holdings` and `plot_turnover` resample monthly with `"1M"` / `"M"`
  aliases, and `plot_monthly_returns_timeseries` uses `"M"`; newer pandas
  versions deprecate these aliases in favor of `"ME"`.
- `show_and_plot_top_positions` is documented to return `ax` conditionally and
  returns `None` when it only prints.
