# pyfolio.tears

`src/pyfolio/tears.py` assembles pyfolio's analysis and plotting functions
into **tear sheets**: printed tables plus multi-panel matplotlib figures that
summarize a strategy's performance and risk. All public functions are also
available from the package root (for example `pyfolio.create_full_tear_sheet`).

## Table of Contents

- [Overview](#overview)
- [Input data model](#input-data-model)
- [Common behavior](#common-behavior)
- [Module-level objects](#module-level-objects)
- [Tear sheet functions](#tear-sheet-functions)
  - [`create_full_tear_sheet`](#create_full_tear_sheet)
  - [`create_simple_tear_sheet`](#create_simple_tear_sheet)
  - [`create_returns_tear_sheet`](#create_returns_tear_sheet)
  - [`create_position_tear_sheet`](#create_position_tear_sheet)
  - [`create_txn_tear_sheet`](#create_txn_tear_sheet)
  - [`create_round_trip_tear_sheet`](#create_round_trip_tear_sheet)
  - [`create_interesting_times_tear_sheet`](#create_interesting_times_tear_sheet)
  - [`create_capacity_tear_sheet`](#create_capacity_tear_sheet)
  - [`create_perf_attrib_tear_sheet`](#create_perf_attrib_tear_sheet)
- [Dependencies](#dependencies)
  - [Function dependency overview](#function-dependency-overview)
  - [Per-function dependencies](#per-function-dependencies)
  - [Indirect dependencies](#indirect-dependencies)
- [Practical usage](#practical-usage)
- [Notes](#notes)

## Overview

| Function | Purpose | Required inputs |
| --- | --- | --- |
| `create_full_tear_sheet` | Orchestrates all other tear sheets based on available inputs | `returns` |
| `create_simple_tear_sheet` | Compact single-figure summary | `returns` |
| `create_returns_tear_sheet` | Return statistics, rolling metrics, drawdowns | `returns` |
| `create_position_tear_sheet` | Exposures, holdings, concentration, leverage, sectors | `returns`, `positions` |
| `create_txn_tear_sheet` | Turnover, volume, trade timing, slippage | `returns`, `positions`, `transactions` |
| `create_round_trip_tear_sheet` | Round-trip trade duration and profitability | `returns`, `positions`, `transactions` |
| `create_interesting_times_tear_sheet` | Performance during historical stress events | `returns` |
| `create_capacity_tear_sheet` | Liquidity and capacity analysis | `returns`, `positions`, `transactions`, `market_data` |
| `create_perf_attrib_tear_sheet` | Factor-based performance attribution | `returns`, `positions`, `factor_returns`, `factor_loadings` |

## Input data model

| Argument | Type | Description |
| --- | --- | --- |
| `returns` | `pd.Series` | Daily, non-cumulative decimal returns indexed by date. |
| `positions` | `pd.DataFrame` | Daily net position values (dollar amount per asset), one column per asset plus a `cash` column. Unheld days may be `0` or `NaN`. |
| `transactions` | `pd.DataFrame` | One row per trade, indexed by timestamp, with `amount`, `price`, and `symbol` columns. |
| `market_data` | `pd.DataFrame` | Daily market data with a multi-level index (dates and a second level) containing volume and price, with equities as columns. |
| `benchmark_rets` | `pd.Series` | Daily non-cumulative benchmark returns, in the same style as `returns`. |
| `factor_returns` | `pd.DataFrame` | Returns by factor; dates as index, factors as columns. |
| `factor_loadings` | `pd.DataFrame` | Factor loadings; dates and tickers as the index, factors as columns. |
| `sector_mappings` | `dict` or `pd.Series` | Security identifier to sector mapping. |

## Common behavior

- **Decorator.** Every tear sheet except `create_full_tear_sheet` is wrapped
  with `plotting.customize`. The wrapper accepts an extra keyword argument
  `set_context` (default `True`). When true, the function runs inside pyfolio's
  default seaborn plotting context and axes style; pass `set_context=False` to
  use your own style context.
- **Return value.** The `return_fig` parameter (default `False`) is available
  on the individual tear sheets other than `create_simple_tear_sheet`. When
  `True`, the matplotlib `Figure` is returned. `create_full_tear_sheet` and
  `create_simple_tear_sheet` do not return a figure.
- **Intraday handling.** Functions that accept `estimate_intraday` call
  `utils.check_intraday`. With the default `"infer"`, positions and
  transactions are inspected for an intraday strategy and, if detected,
  positions are adjusted (a warning is emitted). Pass a boolean to override.
- **Output.** Functions print/display tables (via `utils.print_table` or IPython
  `display`) and draw figures; they do not return the underlying tables.

## Module-level objects

### `FACTOR_PARTITIONS`

Default mapping used by the performance-attribution tear sheet to split
factors into groups for plots:

- `"style"`: `momentum`, `size`, `value`, `reversal_short_term`, `volatility`
- `"sector"`: `basic_materials`, `consumer_cyclical`, `financial_services`,
  `real_estate`, `consumer_defensive`, `health_care`, `utilities`,
  `communication_services`, `energy`, `industrials`, `technology`

### `timer(msg_body, previous_time)`

Prints `Finished <msg_body> (required N.NN seconds).` using the elapsed time
since `previous_time` and returns the current time. It is a helper for timing
steps and is not called by the tear-sheet functions in this module.

## Tear sheet functions

### `create_full_tear_sheet`

```python
create_full_tear_sheet(
    returns, positions=None, transactions=None, market_data=None,
    benchmark_rets=None, slippage=None, live_start_date=None,
    sector_mappings=None, round_trips=False, estimate_intraday="infer",
    hide_positions=False, cone_std=(1.0, 1.5, 2.0), bootstrap=False,
    unadjusted_returns=None, turnover_denom="AGB", set_context=True,
    factor_returns=None, factor_loadings=None, pos_in_dollars=True,
    header_rows=None, factor_partitions=FACTOR_PARTITIONS,
)
```

Generates a comprehensive set of tear sheets for a strategy. It is not
decorated with `customize`; instead, `set_context` is an explicit parameter
forwarded to some of the sub-sheets.

**Behavior**

1. If `slippage` (basis points) and `transactions` are given and
   `unadjusted_returns` is not, keeps a copy of `returns` as
   `unadjusted_returns` and adjusts `returns` with
   `txn.adjust_returns_for_slippage`.
2. Resolves intraday positions with `utils.check_intraday`.
3. Always creates the **returns** and **interesting-times** tear sheets.
4. If `positions` is provided, creates the **position** tear sheet.
5. If `positions` and `transactions` are provided, creates the **transaction**
   tear sheet (with slippage sweep plots when `unadjusted_returns` is set).
   - If `round_trips=True`, also creates the **round-trip** tear sheet.
   - If `market_data` is provided, also creates the **capacity** tear sheet
     (`liquidation_daily_vol_limit=0.2`, `last_n_days=125`).
6. If `positions`, `factor_returns`, and `factor_loadings` are provided,
   creates the **performance-attribution** tear sheet.

**Parameters**

Annotations follow the function's docstring (`tears.py`, lines 90–183), listed
in signature order. `benchmark_rets` and `unadjusted_returns` are in the
signature but absent from that docstring; their entries are inferred from the
code and the other tear-sheet docstrings.

| Parameter | Type | Default | Annotation |
| --- | --- | --- | --- |
| `returns` | `pd.Series` | required | Daily, non-cumulative returns of the strategy, as a time series of decimal returns (e.g. `2015-07-16  -0.012143`). |
| `positions` | `pd.DataFrame`, optional | `None` | Daily net position values: a time series of the dollar amount invested in each position and cash. Days where stocks are not held may be `0` or `NaN`. Non-working capital is labelled `cash`. Example columns: `'AAPL'`, `'MSFT'`, `cash`. |
| `transactions` | `pd.DataFrame`, optional | `None` | Executed trade volumes and fill prices, one row per trade. Trades on different names at the same time share an identical index. Example columns: `amount`, `price`, `symbol`. |
| `market_data` | `pd.DataFrame`, optional | `None` | Daily market data. Multi-level index (one level is dates, another is the market-data field such as volume and price), with equities as columns. Enables the capacity tear sheet. |
| `benchmark_rets` | `pd.Series`, optional | `None` | *(Not in this docstring.)* Daily non-cumulative benchmark returns, in the same style as `returns`. |
| `slippage` | `int` or `float`, optional | `None` | Basis points of slippage applied to returns before generating stats and plots. If set, slippage parameter-sweep plots are generated from the unadjusted returns. `transactions` and `positions` must also be passed. See `txn.adjust_returns_for_slippage`. |
| `live_start_date` | `datetime`, optional | `None` | Point in time when the strategy began live trading, after its backtest period. Should be normalized. |
| `sector_mappings` | `dict` or `pd.Series`, optional | `None` | Security identifier to sector mapping: security IDs as keys, sectors as values. |
| `round_trips` | `bool`, optional | `False` | If `True`, generates a round-trip tear sheet. |
| `estimate_intraday` | `bool` or `str`, optional | `"infer"` | Use the point in the day with the most dollars invested instead of end-of-day positions, to better represent an intraday strategy. By default (`"infer"`) an attempt is made to detect an intraday strategy; specifying a value prevents detection. |
| `hide_positions` | `bool`, optional | `False` | If `True`, no symbol names are output. |
| `cone_std` | `float` or `tuple`, optional | `(1.0, 1.5, 2.0)` | Standard deviation(s) for the cone plots. A float uses one value; a tuple uses several. The cone is a normal distribution with this standard deviation centered around a linear regression. |
| `bootstrap` | `bool`, optional | `False` | Whether to run bootstrap analysis of the performance metrics. Takes a few minutes longer. (Requires `benchmark_rets` in the returns tear sheet.) |
| `unadjusted_returns` | `pd.Series`, optional | `None` | *(Not in this docstring.)* Returns before slippage adjustment. If omitted while `slippage` and `transactions` are given, a copy of `returns` is used. Drives the slippage sweep plots in the transaction tear sheet. |
| `turnover_denom` | `str` | `"AGB"` | Either `"AGB"` or `"portfolio_value"`. See `txn.get_turnover`. |
| `set_context` | `bool`, optional | `True` | If `True`, sets the default plotting style context. See `plotting.plotting_context()`. |
| `factor_returns` | `pd.DataFrame`, optional | `None` | Returns by factor, with date as index and factors as columns. |
| `factor_loadings` | `pd.DataFrame`, optional | `None` | Factor loadings for all days in the date range, with date and ticker as index and factors as columns. |
| `pos_in_dollars` | `bool`, optional | `True` | Whether `positions` is in dollars. |
| `header_rows` | `dict` or `OrderedDict`, optional | `None` | Extra rows to display at the top of the performance stats table. |
| `factor_partitions` | `dict`, optional | `FACTOR_PARTITIONS` | How factors are separated in the performance-attribution factor-returns and risk-exposure plots. See `create_perf_attrib_tear_sheet()`. |

The docstring also summarizes what the function does: it fetches benchmarks if
needed (see [Notes](#notes)), creates tear sheets for returns and significant
events, and, if possible, tear sheets for position analysis and transaction
analysis.

### `create_simple_tear_sheet`

```python
create_simple_tear_sheet(
    returns, positions=None, transactions=None, benchmark_rets=None,
    slippage=None, estimate_intraday="infer", live_start_date=None,
    turnover_denom="AGB", header_rows=None,
)
```

A shorter version of the full tear sheet that shows performance statistics and
a single figure. Optional sections are added depending on inputs.

- Always: cumulative returns, rolling Sharpe, underwater plot (and performance
  statistics table).
- With `benchmark_rets`: rolling beta.
- With `positions`: exposures, top positions, holdings, long/short holdings.
- With `positions` and `transactions`: daily turnover and transaction time
  histogram.

It never uses `market_data`, `sector_mappings`, or bootstrap analysis, never
hides position names, and always uses the default cone standard deviations
`(1.0, 1.5, 2.0)`. If `slippage` and `transactions` are supplied, returns are
slippage-adjusted before plotting.

### `create_returns_tear_sheet`

```python
create_returns_tear_sheet(
    returns, positions=None, transactions=None, live_start_date=None,
    cone_std=(1.0, 1.5, 2.0), benchmark_rets=None, bootstrap=False,
    turnover_denom="AGB", header_rows=None, return_fig=False,
)
```

Prints the performance statistics table and worst drawdown periods, then
draws a single multi-panel figure:

- Cumulative returns (with cone), volatility-matched cumulative returns, and
  cumulative returns on a log scale
- Daily returns
- Rolling beta (with a benchmark), rolling volatility, rolling Sharpe
- Top drawdown periods and underwater plot
- Monthly returns heatmap, annual returns, monthly returns distribution
- Return quantiles

If `benchmark_rets` is provided, `returns` are clipped to the benchmark's date
range (`utils.clip_returns_to_benchmark`). With `bootstrap=True`, a bootstrap
performance plot is added; this raises `ValueError` if `benchmark_rets` is
missing.

### `create_position_tear_sheet`

```python
create_position_tear_sheet(
    returns, positions, show_and_plot_top_pos=2, hide_positions=False,
    sector_mappings=None, transactions=None, estimate_intraday="infer",
    return_fig=False,
)
```

Analyzes holdings. Panels: exposures, top positions, max/median position
concentration, holdings count, long/short holdings, and gross leverage. If
`sector_mappings` is provided and more than one sector results, a sector
allocation plot is added.

`show_and_plot_top_pos`: `2` (default) prints and plots top positions, `1`
only prints, `0` only plots. `hide_positions=True` forces `0`.

### `create_txn_tear_sheet`

```python
create_txn_tear_sheet(
    returns, positions, transactions, turnover_denom="AGB",
    unadjusted_returns=None, estimate_intraday="infer", return_fig=False,
)
```

Analyzes trading activity: turnover, daily volume, a histogram of daily
turnover, and a histogram of transaction times. If `unadjusted_returns` is
given, adds a slippage sweep and slippage sensitivity plot. If the turnover
histogram cannot be generated (`ValueError`), a `UserWarning` is emitted and
the remaining plots are still drawn.

### `create_round_trip_tear_sheet`

```python
create_round_trip_tear_sheet(
    returns, positions, transactions, sector_mappings=None,
    estimate_intraday="infer", return_fig=False,
)
```

Describes the duration, frequency, and profitability of round trips. A round
trip begins when a long or short position is opened and ends when the share
count returns to or crosses zero.

Steps: add closing transactions, extract round trips (using beginning-of-day
portfolio value), print round-trip statistics and profit attribution (also by
sector if `sector_mappings` is provided), then plot trade lifetimes, win
probability, holding time, and PnL per round trip in dollars and percent.

If fewer than 5 round trips are found, a `UserWarning` is issued and the
function returns `None` without producing the figure (even when
`return_fig=True`).

### `create_interesting_times_tear_sheet`

```python
create_interesting_times_tear_sheet(
    returns, benchmark_rets=None, periods=None, legend_loc="best",
    return_fig=False,
)
```

Plots cumulative returns during notable historical events (defined in
`pyfolio.interesting_periods`, or a custom `periods` dict), and prints a
"Stress Events" table of mean, min, and max returns per event. When
`benchmark_rets` is supplied, the benchmark is overlaid for comparison and
`returns` are clipped to its range. If `returns` overlap no event, a
`UserWarning` is issued and the function returns `None`.

### `create_capacity_tear_sheet`

```python
create_capacity_tear_sheet(
    returns, positions, transactions, market_data,
    liquidation_daily_vol_limit=0.2, trade_daily_vol_limit=0.05,
    last_n_days=utils.APPROX_BDAYS_PER_MONTH * 6, days_to_liquidate_limit=1,
    estimate_intraday="infer", return_fig=False,
)
```

Reports portfolio size constraints set by the least liquid tickers.

- Prints tickers whose days to liquidate exceed a limit (assuming a $1M
  capital base and trailing 5-day mean volume), for the whole backtest and for
  the last `last_n_days`.
- Prints tickers whose daily transactions consume more than
  `trade_daily_vol_limit` of the daily bar, for the whole backtest and the last
  `last_n_days`.
- Plots a capacity sweep: projected Sharpe ratio under slippage penalties at
  capital bases from $100,000 to $300,000,000 in $1,000,000 steps.

### `create_perf_attrib_tear_sheet`

```python
create_perf_attrib_tear_sheet(
    returns, positions, factor_returns, factor_loadings,
    transactions=None, pos_in_dollars=True,
    factor_partitions=FACTOR_PARTITIONS, return_fig=False,
)
```

Shows performance relative to common risk factors. It runs
`perf_attrib.perf_attrib`, displays a "Performance Relative to Common Risk
Factors" heading and summary statistics, then plots total/common/specific
returns plus, for each group in `factor_partitions`, cumulative factor
contributions and daily risk exposures. With `factor_partitions=None`, all
factors are plotted together.

## Dependencies

- **pyfolio modules:** `capacity`, `perf_attrib`, `plotting`, `pos`,
  `round_trips`, `timeseries`, `txn`, `utils`.
- **Third-party:** `empyrical`, `matplotlib` (`pyplot`, `gridspec`), `pandas`,
  `seaborn`, `IPython.display`.
- **Standard library:** `warnings`, `time`.

### Function dependency overview

```text
create_full_tear_sheet
├── create_returns_tear_sheet
├── create_interesting_times_tear_sheet
├── create_position_tear_sheet        (if positions)
├── create_txn_tear_sheet             (if positions and transactions)
├── create_round_trip_tear_sheet      (if round_trips=True)
├── create_capacity_tear_sheet        (if market_data)
└── create_perf_attrib_tear_sheet     (if factor_returns and factor_loadings)

create_simple_tear_sheet              (standalone; calls no other tear sheet)
```

Only `create_full_tear_sheet` calls other functions defined in `tears.py`; the
other tear sheets are independent of each other. `timer` is not called by any
function in the module.

### Per-function dependencies

Each function below lists the external functions it calls directly.
`plotting.customize` wraps every function except `create_full_tear_sheet`
(and `timer`), so they all depend on `plotting.plotting_context` and
`plotting.axes_style` through that decorator.

| Function | `tears.py` functions | `plotting` | Other `pyfolio` modules | Third-party |
| --- | --- | --- | --- | --- |
| `create_full_tear_sheet` | `create_returns_tear_sheet`, `create_interesting_times_tear_sheet`, `create_position_tear_sheet`, `create_txn_tear_sheet`, `create_round_trip_tear_sheet`, `create_capacity_tear_sheet`, `create_perf_attrib_tear_sheet` | — | `txn.adjust_returns_for_slippage`, `utils.check_intraday` | — |
| `create_simple_tear_sheet` | — | `customize`, `show_perf_stats`, `plot_rolling_returns`, `plot_rolling_beta`, `plot_rolling_sharpe`, `plot_drawdown_underwater`, `plot_exposures`, `show_and_plot_top_positions`, `plot_holdings`, `plot_long_short_holdings`, `plot_turnover`, `plot_txn_time_hist` | `utils.check_intraday`, `txn.adjust_returns_for_slippage`, `pos.get_percent_alloc` | `empyrical` (`ep.utils.get_utc_timestamp`), `matplotlib` (`plt`, `gridspec`) |
| `create_returns_tear_sheet` | — | `customize`, `show_perf_stats`, `show_worst_drawdown_periods`, `plot_rolling_returns`, `plot_returns`, `plot_rolling_beta`, `plot_rolling_volatility`, `plot_rolling_sharpe`, `plot_drawdown_periods`, `plot_drawdown_underwater`, `plot_monthly_returns_heatmap`, `plot_annual_returns`, `plot_monthly_returns_dist`, `plot_return_quantiles`, `plot_perf_stats` | `utils.clip_returns_to_benchmark` | `empyrical` (`ep.utils.get_utc_timestamp`), `matplotlib` (`plt`, `gridspec`) |
| `create_position_tear_sheet` | — | `customize`, `plot_exposures`, `show_and_plot_top_positions`, `plot_max_median_position_concentration`, `plot_holdings`, `plot_long_short_holdings`, `plot_gross_leverage`, `plot_sector_allocations` | `utils.check_intraday`, `pos.get_percent_alloc`, `pos.get_sector_exposures` | `matplotlib` (`plt`, `gridspec`) |
| `create_txn_tear_sheet` | — | `customize`, `plot_turnover`, `plot_daily_volume`, `plot_daily_turnover_hist`, `plot_txn_time_hist`, `plot_slippage_sweep`, `plot_slippage_sensitivity` | `utils.check_intraday` | `matplotlib` (`plt`, `gridspec`), `warnings` |
| `create_round_trip_tear_sheet` | — | `customize`, `show_profit_attribution`, `plot_round_trip_lifetimes`, `plot_prob_profit_trade` | `utils.check_intraday`, `round_trips.add_closing_transactions`, `round_trips.extract_round_trips`, `round_trips.print_round_trip_stats`, `round_trips.apply_sector_mappings_to_round_trips` | `seaborn` (`sns.histplot`), `matplotlib` (`plt`, `gridspec`), `warnings` |
| `create_interesting_times_tear_sheet` | — | `customize` | `timeseries.extract_interesting_date_ranges`, `utils.print_table`, `utils.clip_returns_to_benchmark` | `empyrical` (`ep.cum_returns`), `pandas`, `matplotlib` (`plt`, `gridspec`), `warnings` |
| `create_capacity_tear_sheet` | — | `customize`, `plot_capacity_sweep` | `utils.check_intraday`, `utils.format_asset`, `utils.print_table`, `utils.APPROX_BDAYS_PER_MONTH` (default argument), `capacity.get_max_days_to_liquidate_by_ticker`, `capacity.get_low_liquidity_transactions` | `matplotlib` (`plt`) |
| `create_perf_attrib_tear_sheet` | — | `customize` | `perf_attrib.perf_attrib`, `perf_attrib.show_perf_attrib_stats`, `perf_attrib.plot_returns`, `perf_attrib.plot_factor_contribution_to_perf`, `perf_attrib.plot_risk_exposures` | `IPython.display` (`display`, `Markdown`), `matplotlib` (`plt`, `gridspec`) |

### Indirect dependencies

The `plotting` and analysis helpers listed above call further into the
package. The module-level imports of these modules (not the individual
functions) show the chain:

- `plotting` imports `capacity`, `pos`, `timeseries`, `txn`, and `utils`.
- `perf_attrib` imports `pos`, `txn`, and `utils`.
- `timeseries` imports `deprecate`, `interesting_periods`, `txn`, and `utils`.
- `round_trips` imports `utils`; `capacity` imports `pos`;
  `utils` imports `pos` and `txn`.

Because of this, a tear sheet that only calls `plotting` functions still
depends transitively on `timeseries` (and through it on `scipy` and
`scikit-learn`) at import time.

### Module dependency on `FACTOR_PARTITIONS`

`FACTOR_PARTITIONS` is a module-level constant used as the default argument of
both `create_full_tear_sheet` and `create_perf_attrib_tear_sheet`; the full
tear sheet passes it through to the performance-attribution sheet.

## Practical usage

```python
import pyfolio as pf

# Full report from returns only
pf.create_full_tear_sheet(returns)

# With positions, transactions, and a benchmark
pf.create_full_tear_sheet(
    returns,
    positions=positions,
    transactions=transactions,
    benchmark_rets=benchmark_rets,
    round_trips=True,
)

# Individual sheet, returning the figure
fig = pf.create_returns_tear_sheet(returns, benchmark_rets=benchmark_rets, return_fig=True)

# Custom plotting style
with pf.plotting.plotting_context(font_scale=2):
    pf.create_returns_tear_sheet(returns, set_context=False)
```

For Zipline backtests, convert results first:

```python
returns, positions, transactions = pf.utils.extract_rets_pos_txn_from_zipline(backtest)
```

## Notes

- `create_full_tear_sheet` documents that it "fetches benchmarks if needed",
  but the function does not fetch benchmark data; pass `benchmark_rets`
  yourself.
- The docstring of `create_interesting_times_tear_sheet` states that
  `benchmark_rets` must be passed, but the code treats it as optional.
- `create_full_tear_sheet` forwards `set_context` only to the sheets it calls
  with that argument (returns, interesting times, position, and transaction).
  The round-trip, capacity, and performance-attribution sheets use their
  default `set_context=True`.
- `create_simple_tear_sheet`'s docstring lists `set_context`, which is handled
  by the `customize` decorator rather than the function signature.
- `bootstrap=True` in `create_full_tear_sheet` and
  `create_returns_tear_sheet` requires `benchmark_rets`.
