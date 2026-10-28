# Pyfolio Documentation and Code Review Guide

> **Version**: written against branch `yzeng` at HEAD `4fb77f2` (2026-10-28, pandas 3.x / Python 3.12 compatibility pass). Prior revision: HEAD `5afb198` (2026-10-08).

## Table of Contents
- [Warmup](#warmup)
- [Overview](#overview)
- [Package dependencies for code review](#package-dependencies-for-code-review)
- [Module guide](#module-guide)
  - [`pyfolio.tears`](#pyfoliotears)
  - [`pyfolio.timeseries`](#pyfoliotimeseries)
  - [`pyfolio.plotting`](#pyfolioplotting)
  - [`pyfolio.perf_attrib`](#pyfolioperf_attrib)
  - [`pyfolio.pos` and `pyfolio.txn`](#pyfoliopos-and-pyfoliotxn)
  - [`pyfolio.round_trips` and `pyfolio.capacity`](#pyfolioround_trips-and-pyfoliocapacity)
  - [`pyfolio.utils`](#pyfolioutils)
  - [Support modules](#support-modules)
- [Primary workflow](#primary-workflow)
- [Dependency observations](#dependency-observations)


## Warmup
- [x] Read the project overview and installation instructions in [`README.md`](README.md).
- [x] Review the generated API reference in [`docs/source/api-reference.rst`](docs/source/api-reference.rst).
- [ ] Run an example notebook, such as [`docs/source/notebooks/round_trip_tear_sheet_example.ipynb`](docs/source/notebooks/round_trip_tear_sheet_example.ipynb).
- [ ] Review the package source under [`src/pyfolio/`](src/pyfolio/).

[⬆ 回到目录](#table-of-contents)

## Overview
Pyfolio analyzes the performance and risk of investment portfolios. Its main
workflow accepts non-cumulative strategy returns and, optionally, positions,
transactions, market data, benchmark returns, and factor data. Analysis modules
calculate portfolio statistics and diagnostics; plotting and tear-sheet
modules assemble these into visual reports.

The tear-sheet entry points live in `pyfolio.tears`. The main entry point,
`create_full_tear_sheet`, produces a returns tear sheet and interesting-times
analysis, then includes position, transaction, round-trip, capacity, and
performance-attribution reports when their required inputs are supplied.

[⬆ 回到目录](#table-of-contents)

## Package dependencies for code review
Review the modules in dependency order. Arrows identify direct imports of
other `pyfolio` modules; third-party and standard-library imports are not
shown here. Checkbox order is a suggested review sequence, not a record of
completed review.

### Level 0 — independent modules

1. - [ ] `pyfolio.deprecate`
2. - [ ] `pyfolio.interesting_periods`
3. - [ ] `pyfolio.txn`
4. - [ ] `pyfolio.pos`
5. - [ ] `pyfolio._version`
6. - [ ] `pyfolio.ipycompat` (no imports from other `pyfolio` modules; currently not imported elsewhere in `src/pyfolio`)

### Level 1 — depends on Level 0

7. - [ ] `pyfolio.utils` → `pyfolio.pos`, `pyfolio.txn`
8. - [ ] `pyfolio.capacity` → `pyfolio.pos`

### Level 2 — depends on Level 0–1

9. - [ ] `pyfolio.round_trips` → `pyfolio.utils`
10. - [ ] `pyfolio.timeseries` → `pyfolio.deprecate`, `pyfolio.interesting_periods`, `pyfolio.txn`, `pyfolio.utils`
11. - [ ] `pyfolio.perf_attrib` → `pyfolio.pos`, `pyfolio.txn`, `pyfolio.utils`

### Level 3 — visualization and reporting

12. - [ ] `pyfolio.plotting` → `pyfolio.capacity`, `pyfolio.pos`, `pyfolio.timeseries`, `pyfolio.txn`, `pyfolio.utils`
13. - [ ] `pyfolio.tears` → `pyfolio.capacity`, `pyfolio.perf_attrib`, `pyfolio.plotting`, `pyfolio.pos`, `pyfolio.round_trips`, `pyfolio.timeseries`, `pyfolio.txn`, `pyfolio.utils`

### Level 4 — package public surface

14. - [ ] `pyfolio.__init__` → package modules above; re-exports plotting and tear-sheet functions

[⬆ 回到目录](#table-of-contents)

## Module guide
### `pyfolio.tears`

Composes portfolio inputs and analysis functions into tear sheets. The
comprehensive generator conditionally adds reports depending on which optional
inputs are provided.

Key entry points:

- `create_full_tear_sheet(returns, positions=None, transactions=None, market_data=None, ...)` — returns and interesting-times analysis, with optional position, transaction, round-trip, capacity, and factor-attribution analyses.
- `create_simple_tear_sheet(returns, ...)` — a reduced summary of strategy performance.
- `create_returns_tear_sheet(returns, ...)` — return statistics, drawdowns, rolling metrics, and return plots.
- `create_position_tear_sheet(returns, positions, ...)` — exposures, holdings, and top-position analysis.
- `create_txn_tear_sheet(returns, positions, transactions, ...)` — trading activity and turnover analysis.
- `create_round_trip_tear_sheet(...)` — trade round-trip analysis.
- `create_interesting_times_tear_sheet(returns, ...)` — strategy performance during selected market periods.
- `create_capacity_tear_sheet(...)` — liquidity and strategy-capacity analysis using market data.
- `create_perf_attrib_tear_sheet(...)` — factor-based performance and risk attribution.

### `pyfolio.timeseries`

Provides calculations on return and portfolio time series, including
performance statistics, drawdowns, rolling measures, bootstrap statistics,
and selected-period analysis. Frequently used functions include
`perf_stats`, `perf_stats_bootstrap`, `gross_lev`, `get_max_drawdown`,
`get_top_drawdowns`, and `extract_interesting_date_ranges`. Since `4fb77f2`,
the `sortino_ratio` wrapper forwards `period` to `empyrical.sortino_ratio`
(annualization is no longer dropped), and `rolling_regression` skips
windows where no row has observations for all factors.

### `pyfolio.plotting`

Implements plotting and display helpers consumed by tear sheets and available
for direct use. The module covers return summaries, rolling statistics,
drawdowns, holdings, leverage, exposures, turnover, transactions, capacity,
and round trips. Examples include `plot_monthly_returns_heatmap`,
`plot_rolling_returns`, `plot_drawdown_underwater`, `plot_holdings`,
`plot_turnover`, and `show_perf_stats`.

### `pyfolio.perf_attrib`

Calculates and displays portfolio performance attribution against supplied
factor returns and factor loadings. Main functions include `perf_attrib`,
`create_perf_attrib_stats`, and `show_perf_attrib_stats`; plotting helpers
cover returns, factor contributions, and risk exposures.

### `pyfolio.pos` and `pyfolio.txn`

`pos` provides portfolio allocation, position extraction, exposure,
concentration, and long/short helpers. `txn` provides transaction volume and
turnover calculations. These modules form low-level inputs for several
analytics and reporting modules.

### `pyfolio.round_trips` and `pyfolio.capacity`

`round_trips` extracts round trips from transaction data and calculates
trade-level statistics. `capacity` estimates liquidity and liquidation
capacity from positions, transactions, and market data. Both are used by
optional tear-sheet sections.

### `pyfolio.utils`

Contains shared input validation, formatting, benchmark, intraday, display,
and Zipline backtest-conversion helpers. `extract_rets_pos_txn_from_zipline`
converts a Zipline backtest result into data accepted by pyfolio tear sheets.
Since `4fb77f2` it also provides `_comparable_live_start(dt, index)`, which
normalizes a live-start instant to the target index's timezone.

### Support modules

- `interesting_periods` defines notable historical market periods used by
  time-series analysis and the interesting-times tear sheet.
- `deprecate` provides the deprecated-function decorator used by the API.
- `ipycompat` supports reading notebook files across IPython versions. No
  other source module currently imports it.
- `_version` contains generated package version information.

[⬆ 回到目录](#table-of-contents)

## Primary workflow
1. Prepare daily, non-cumulative strategy returns as a `pandas.Series`.
2. Optionally prepare positions, transactions, benchmark returns, market data,
   and factor data in the formats described in the tear-sheet docstrings.
3. Generate a report with `pyfolio.create_full_tear_sheet(...)`, or select a
   narrower report such as `pyfolio.create_returns_tear_sheet(...)`.
4. For lower-level analysis, call the relevant `timeseries`, `pos`, `txn`,
   `round_trips`, `capacity`, or `perf_attrib` helpers and pass results to
   plotting functions as needed.

[⬆ 回到目录](#table-of-contents)

## Dependency observations
- The internal dependency graph is layered: data and utility modules support
  analytics, which support plotting and tear-sheet composition. No direct
  cyclic imports between `pyfolio` modules were identified from the source
  imports.
- `pyfolio.__init__` imports `plotting` and `tears`, so importing the package
  root loads those modules and their third-party dependencies.
- `pos` and `utils` support optional Zipline integrations. Their Zipline
  imports are guarded, allowing pyfolio's core analysis to be used without
  Zipline.
- `ipycompat` conditionally imports `nbformat` for newer IPython versions but
  is not referenced by another module in the source tree.
- `utils` imports `packaging.version.Version`, and `ipycompat` imports
  `nbformat`; neither is declared as a direct runtime dependency in
  `pyproject.toml`. Whether they are available transitively depends on the
  installed environment.

[⬆ 回到目录](#table-of-contents)

## Revision notes (HEAD `4fb77f2`, 2026-10-28)
The pandas 3.x / Python 3.12 pass (`5afb198..4fb77f2`, intermediate commits
`91b73a0` "pandas 3 portfolio and attribution" and `4871f61` "pandas
3.x / python 3.12") touched every module. Substantive behavior changes:

- **`utils._comparable_live_start(dt, index)`** (new) — converts a live-start
  instant to a timestamp comparable with the target return index (naive or
  aware). Replaces the previous `empyrical.utils.get_utc_timestamp` call in
  `plotting.show_perf_stats`, `plot_returns`, `plot_rolling_returns`,
  `plot_return_quantiles`, so the backtest / out-of-sample cut-off now
  respects the index's own timezone.
- **`timeseries.sortino_ratio`** wrapper now forwards `period=period` to
  `empyrical.sortino_ratio` (previously the annualization was dropped).
- **`timeseries.rolling_regression`** — NaN-skip condition changed from
  `< nan_threshold` to `<= nan_threshold`, and a window with no rows that
  have observations for all factors is now skipped.
- **`plotting.show_perf_stats`** — raises `TypeError` if `returns.index` is
  not a `DatetimeIndex`; casts the assembled stats table to `object` dtype
  up front (avoids deprecated pandas mixed-dtype upcast); uses
  `_comparable_live_start`.
- **`plotting.plot_return_quantiles`** — boxplot now built from a tidy
  DataFrame (`Period` / `Return`) with `x`/`hue="Period"`; accepts a
  `color` kwarg for the out-of-sample swarm; xticks hardcoded to `[0,1,2]`.
- **`plotting.plot_holdings` / `plot_turnover` /
  `plot_monthly_returns_timeseries`** — `.resample("1M"/"M")` →
  `.resample(pd.offsets.MonthEnd())`.
- **`plotting.plot_factor_contribution_to_perf` /
  `plot_risk_exposures`** — `ax.plot(col, label=col)` so legend labels the
  factor columns.
- **`plotting.plot_rolling_returns`** — `starting_value=is_cum_returns.iloc[-1]`
  (positional `[-1]` removed).
- **`plotting.plot_monthly_returns_heatmap`** — `rename(..., inplace=True)`
  → non-inplace.
- **`plotting.plot_prob_profit_trade`** — `ax.locator_params(axis="x", nbins=5)`.
- **`perf_attrib.show_perf_attrib_stats`** — `.astype(object)` on the stats
  names list; `perf_attrib.plot_*` pass `label=col`; `_align_and_warn`
  computes `missing_ratio` only after the zero-coverage `ValueError` guard
  (avoids division by zero).
- **`tears.create_returns_tear_sheet`** — raises `ValueError` if `returns`
  is empty after clipping to the benchmark.
- **`capacity.days_to_liquidate_positions`** — uses `positions_alloc.abs()`
  so short positions do not produce negative days-to-liquidate.
- **`pos.get_sector_alloc`** — `positions.T.groupby(...).sum().T` replaces
  the deprecated `groupby(..., axis=1)`.
- **`txn.get_turnover`** — `txn_vol.txn_volume.astype(float)`.
- **`timeseries.get_top_drawdowns`** — non-inplace `underwater.drop(...)`.
- **`round_trips`** — added a warning when `aggregate_round_trip_stats`
  replaces portfolio-relative returns.

Most remaining diff lines are docstring / RST formatting (`Example` →
`Examples`, `Example::` blocks) and carry no behavior change.

[⬆ 回到目录](#table-of-contents)

## Revision notes — HEAD `4fb77f2` (2026-10-28)
_This revision (`5afb198..4fb77f2`, commits `4871f61` "pandas 3.x / python
3.12", `91b73a0` "pandas 3 portfolio and attribution", `4fb77f2` "updated
pyproject.toml") is primarily a pandas 3.x / Python 3.12 compatibility pass.
Substantive behavior changes captured:

### `pyfolio.utils`
- **New** `utils._comparable_live_start(dt, index)` — converts a `live_start`
  instant to a UTC timestamp and then to the returns index's timezone (or
  strips tz for a naive index). Replaces the previous
  `empyrical.utils.get_utc_timestamp` calls in the plotting entry points so
  `live_start` comparisons line up with the actual index.
- `utils.extract_rets_pos_txn_from_zipline` — pandas 3 compatible
  position/cash extraction (`backtest.ending_cash.to_frame("cash")`,
  `pos.extract_pos`).
- `utils.print_table`-adjacent display helpers (`configure_legend`) — sort
  handles/labels pairs together.

### `pyfolio.plotting`
- `show_perf_stats` — raises `TypeError` when `returns.index` is not a
  `DatetimeIndex` (with a `pd.to_datetime` hint); uses
  `utils._comparable_live_start` for the in-sample / out-of-sample split
  (positions and transactions get their own cutoff); casts the perf-stats
  frame to `object` before formatting mixed numeric/percent strings (avoids
  the deprecated pandas upcast, which becomes an error in a future pandas).
- `plot_returns`, `plot_rolling_returns`, `plot_return_quantiles` — use
  `utils._comparable_live_start`; `plot_return_quantiles` also accepts a
  `color` kwarg (`live_color`, default `"red"`) and renders the boxplot from
  a tidy `quantile_data` DataFrame (`x`/`hue="Period"`) instead of a list.
- `plot_holdings`, `plot_turnover`, `plot_monthly_returns_timeseries` —
  `resample("1M"/"M")` → `resample(pd.offsets.MonthEnd())`.
- `plot_factor_contribution_to_perf`, `plot_risk_exposures` — `ax.plot(..., label=col)`.
- `plot_monthly_returns_heatmap` — `rename(...)` non-inplace (avoid
  SettingWithCopyWarning).
- `plot_prob_profit_trade` — `ax.locator_params(axis="x", nbins=5)`.
- `show_profit_attribution` — drops `inplace=False`.

### `pyfolio.timeseries`
- `sortino_ratio` (deprecated wrapper) now forwards `period` through to
  `empyrical.sortino_ratio`.
- `rolling_regression` — NaN-threshold check uses `<=` (was `<`) and skips a
  window when no rows have observations for all factors
  (`factor_returns_period_dnan.empty`).
- `get_top_drawdowns` — `underwater.drop(...)` non-inplace.

### `pyfolio.perf_attrib`
- `show_perf_attrib_stats` — casts the stat-name list to `object` to avoid
  the pandas upcast path.
- `_align_and_warn` — computes `missing_ratio` only after the zero-coverage
  `ValueError` check (avoids division by zero when no stock is covered).
- `plot_factor_contribution_to_perf` — labels each factor line.

### `pyfolio.pos`, `pyfolio.txn`, `pyfolio.capacity`, `pyfolio.round_trips`
- `pos.get_sector_alloc` — `positions.T.groupby(by=...).sum().T` (the
  `axis=1` groupby is removed in pandas 3).
- `txn.get_turnover` — `txn_vol.txn_volume.astype(float)`.
- `capacity.days_to_liquidate_positions` — `positions_alloc.abs()` (negative
  positions no longer produce a negative days-to-liquidate).
- `round_trips` — adds a warning when `portfolio_value` is None (round-trip
  returns are not portfolio-relative).

### `pyfolio.tears`
- `create_returns_tear_sheet` — raises `ValueError` if `returns` is empty
  after clipping to the benchmark.
- Docstrings throughout `plotting`/`tears`/`perf_attrib` reformatted to
  Sphinx-compatible `Example::` blocks.

[⬆ 回到目录](#table-of-contents)