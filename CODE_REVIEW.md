# Pyfolio Documentation and Code Review Guide

## Warmup

- [x] Read the project overview and installation instructions in [`README.md`](README.md).
- [x] Review the generated API reference in [`docs/source/api-reference.rst`](docs/source/api-reference.rst).
- [ ] Run an example notebook, such as [`docs/source/notebooks/round_trip_tear_sheet_example.ipynb`](docs/source/notebooks/round_trip_tear_sheet_example.ipynb).
- [ ] Review the package source under [`src/pyfolio/`](src/pyfolio/).

## Table of Contents

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
`get_top_drawdowns`, and `extract_interesting_date_ranges`.

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

### Support modules

- `interesting_periods` defines notable historical market periods used by
  time-series analysis and the interesting-times tear sheet.
- `deprecate` provides the deprecated-function decorator used by the API.
- `ipycompat` supports reading notebook files across IPython versions. No
  other source module currently imports it.
- `_version` contains generated package version information.

## Primary workflow

1. Prepare daily, non-cumulative strategy returns as a `pandas.Series`.
2. Optionally prepare positions, transactions, benchmark returns, market data,
   and factor data in the formats described in the tear-sheet docstrings.
3. Generate a report with `pyfolio.create_full_tear_sheet(...)`, or select a
   narrower report such as `pyfolio.create_returns_tear_sheet(...)`.
4. For lower-level analysis, call the relevant `timeseries`, `pos`, `txn`,
   `round_trips`, `capacity`, or `perf_attrib` helpers and pass results to
   plotting functions as needed.

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
