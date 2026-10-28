# Pyfolio Reloaded — Learning Roadmap

> **Version**: written against branch `yzeng` at HEAD `5afb198` (2026-10-08).

Entry-points and recommended reading order for learning this codebase.
All paths below are relative to the repo root `pyfolio-reloaded/`.

Companion docs: `CODE_OVERVIEW.md` (overview), `DEPENDENCIES.md` (layered
function call graph), `docs/tears.md`, `docs/plotting.md`, `docs/timeseries.md`
(module-by-module notes).

## Table of Contents

- [0. Layout at a glance](#0-layout-at-a-glance)
  - [Source modules (`src/pyfolio/`, by size)](#source-modules-srcpyfolio-by-size)
  - [Examples (`src/pyfolio/examples/`)](#examples-srcpyfolioexamples)
  - [Tests (`tests/`)](#tests-tests)
- [1. Setup and orientation](#1-setup-and-orientation)
- [2. Master the data contract](#2-master-the-data-contract)
- [3. Run the end-to-end example FIRST](#3-run-the-end-to-end-example-first)
- [4. `tears.py` — the orchestration layer](#4-tearspy--the-orchestration-layer)
- [5. `timeseries.py` — split into two halves](#5-timeseriespy--split-into-two-halves)
- [6. Analysis modules (numeric work)](#6-analysis-modules-numeric-work)
- [7. `plotting.py` — visualization](#7-plottingpy--visualization)
- [8. Cross-repo integration](#8-cross-repo-integration)
- [9. Known quirks / hot paths (from `DEPENDENCIES.md`)](#9-known-quirks--hot-paths-from-dependenciesmd)
- [Suggested order](#suggested-order)

## 0. Layout at a glance

### Source modules (`src/pyfolio/`, by size)

| File | Size | Role |
|---|---:|---|
| `plotting.py` | 64 KB | All matplotlib/seaborn diagnostics |
| `tears.py` | 46 KB | Tear-sheet orchestration |
| `timeseries.py` | 38 KB | Live analytics + deprecated metric wrappers |
| `perf_attrib.py` | 22 KB | Factor attribution regression |
| `utils.py` | 17 KB | Input plumbing, display helpers, zipline bridge |
| `round_trips.py` | 15 KB | Closed-trade decomposition |
| `capacity.py` | 9.5 KB | Liquidation / capacity analysis |
| `pos.py` | 7.2 KB | Position analysis |
| `txn.py` | 6.6 KB | Transaction analysis |
| `interesting_periods.py` | 4.2 KB | Named market windows (2008 crash, etc.) |
| `deprecate.py` | 1.5 KB | Deprecation decorator |
| `ipycompat.py` | 0.6 KB | IPython/Jupyter shim |

Public API: `from pyfolio import tears, plotting, timeseries, pos, txn, ...`.
`tears` and `plotting` are re-exported at package level via `from .plotting
import *` / `from .tears import *`.

### Examples (`src/pyfolio/examples/`)

- [ ] `results.pickle` (2.4 MB) — pre-computed zipline backtest result, the
      input every example notebook loads.
- [ ] `zipline_algo_example.ipynb` (3.8 MB) — end-to-end: run a zipline
      algorithm, then feed the result into pyfolio. **Start here.**
- [ ] `single_stock_example.ipynb` (604 KB) — analyze one stock's returns.
- [ ] `slippage_example.ipynb` (2.1 MB) — slippage sensitivity sweep.
- [ ] `round_trip_tear_sheet_example.ipynb` (7 KB) — round-trip tear sheet.
- [ ] `sector_mappings_example.ipynb` (1 MB) — sector attribution.

### Tests (`tests/`)

- [ ] `test_timeseries.py` (13 KB), `test_perf_attrib.py` (19 KB),
      `test_round_trips.py` (10 KB), `test_pos.py` (8.8 KB),
      `test_capacity.py` (5 KB), `test_tears.py` (6 KB), `test_txn.py`
      (3 KB). Read alongside the corresponding source module.

[⬆ 回到目录](#table-of-contents)

## 1. Setup and orientation

- [ ] Verify editable install: `python -c "import pyfolio; print(pyfolio.__file__)"`.
- [ ] Run tests green: `pytest tests/ -q`.
- [ ] Open `README.md` and skim.
- [ ] Open `DEPENDENCIES.md` to see the call-graph layering before reading any
      source — it tells you which functions are hot paths.

[⬆ 回到目录](#table-of-contents)

## 2. Master the data contract

Pyfolio's whole API accepts three positional inputs: **returns**,
**positions**, **transactions**. Lock this in before reading any code.

- [ ] `returns`: `pd.Series` indexed by date, portfolio simple returns.
- [ ] `positions`: `pd.DataFrame` indexed by date, columns = asset IDs (plus
      `'cash'`), values = dollar holdings.
- [ ] `transactions`: `pd.DataFrame` with columns like `amount`, `price`,
      `dt`, `symbol`.
- [ ] Read `utils.extract_rets_pos_txn_from_zipline(...)` — this is the
      function that turns a zipline backtest result into the triple above.
- [ ] Read `utils.check_intraday(...)` — it decides whether downstream
      tear sheets render daily or intraday plots; it is called by six of
      the ten tear-sheet generators.

[⬆ 回到目录](#table-of-contents)

## 3. Run the end-to-end example FIRST

- [ ] Open `src/pyfolio/examples/zipline_algo_example.ipynb` and run it
      against `results.pickle` (you don't need to re-run the zipline algo).
- [ ] Identify where `create_full_tear_sheet(...)` is called and what it
      returns / displays.
- [ ] Match each figure in the notebook to the underlying `plotting.*`
      function using `docs/pdoc/` or `DEPENDENCIES.md`.

[⬆ 回到目录](#table-of-contents)

## 4. `tears.py` — the orchestration layer

Read entry points in this order (each adds one report section):

- [ ] `create_simple_tear_sheet` — minimal report.
- [ ] `create_returns_tear_sheet` — returns-focused.
- [ ] `create_position_tear_sheet` — holdings / exposure.
- [ ] `create_txn_tear_sheet` — transaction costs / volume.
- [ ] `create_round_trip_tear_sheet` — closed-trade analysis.
- [ ] `create_capacity_tear_sheet` — liquidity / capacity.
- [ ] `create_perf_attrib_tear_sheet` — factor attribution.
- [ ] `create_interesting_times_tear_sheet` — named market periods.
- [ ] `create_full_tear_sheet` — chains all of the above.

Note: `tears.py` performs no numeric work — every function is a composition
of `plotting.*`, `timeseries.*`, and the `pos/txn/round_trips/capacity`
analysis modules.

[⬆ 回到目录](#table-of-contents)

## 5. `timeseries.py` — split into two halves

This module is misleadingly large; half of it is deprecated.

- [ ] **Deprecated half**: `sharpe_ratio`, `sortino_ratio`, `alpha`, `beta`,
      `calmar_ratio`, `max_drawdown`, `omega_ratio`, `tail_ratio`,
      `stability_of_timeseries`, `cum_returns`, `annual_return`,
      `annual_volatility`, `downside_risk`, `aggregate_returns`,
      `alpha_beta`. These all delegate to **empyrical-reloaded** at runtime.
      Read them to understand the API surface, not the math.
- [ ] **Live half** (the functions that actually do work in pyfolio):
  - [ ] Drawdown: `gen_drawdown_table`, `get_top_drawdowns`,
        `get_max_drawdown_underwater`.
  - [ ] Rolling stats: `rolling_beta`, `rolling_sharpe`,
        `rolling_volatility`, `rolling_regression`.
  - [ ] Bootstrap / cones: `calc_bootstrap`, `simulate_paths`,
        `summarize_paths`, `forecast_cone_bootstrap`.
  - [ ] Other: `gross_lev`, `perf_stats`, `perf_stats_bootstrap`,
        `extract_interesting_date_ranges`, `value_at_risk`,
        `var_cov_var_normal`, `common_sense_ratio`.

[⬆ 回到目录](#table-of-contents)

## 6. Analysis modules (numeric work)

Read in this order:

- [ ] `txn.py` — `get_turnover`, `get_txn_vol`,
      `adjust_returns_for_slippage`, `make_transaction_frame`,
      `map_transaction`.
- [ ] `pos.py` — `get_percent_alloc`, `get_long_short_pos`,
      `get_sector_exposures`, `get_top_long_short_abs`,
      `get_max_median_position_concentration`.
- [ ] `round_trips.py` — `extract_round_trips`, `gen_round_trip_stats`,
      `apply_sector_mappings_to_round_trips`.
- [ ] `capacity.py` — `apply_slippage_penalty`,
      `daily_txns_with_bar_data`, `days_to_liquidate_positions`,
      `get_low_liquidity_transactions`,
      `get_max_days_to_liquidate_by_ticker`.
- [ ] `perf_attrib.py` — `compute_exposures`, `perf_attrib`,
      `create_perf_attrib_stats`.

[⬆ 回到目录](#table-of-contents)

## 7. `plotting.py` — visualization

- [ ] Styling plumbing: `customize`, `plotting_context`, `axes_style`.
- [ ] Table renderers: `show_perf_stats`, `show_profit_attribution`,
      `show_worst_drawdown_periods`, `show_and_plot_top_positions`,
      `show_perf_attrib_stats` — all funnel through `utils.print_table`.
- [ ] Returns plots: `plot_returns`, `plot_annual_returns`,
      `plot_monthly_returns_dist`, `plot_monthly_returns_heatmap`,
      `plot_return_quantiles`.
- [ ] Rolling: `plot_rolling_returns`, `plot_rolling_beta`,
      `plot_rolling_sharpe`, `plot_rolling_volatility`.
- [ ] Drawdown: `plot_drawdown_periods`, `plot_drawdown_underwater`.
- [ ] Positions: `plot_holdings`, `plot_long_short_holdings`,
      `plot_exposures`, `plot_sector_allocations`,
      `plot_gross_leverage`, `plot_max_median_position_concentration`.
- [ ] Transactions: `plot_turnover`, `plot_daily_turnover_hist`,
      `plot_daily_volume`, `plot_txn_time_hist`,
      `plot_slippage_sweep`, `plot_slippage_sensitivity`.
- [ ] Round trips: `plot_round_trip_lifetimes`, `plot_prob_profit_trade`.
- [ ] Capacity: `plot_capacity_sweep`.

[⬆ 回到目录](#table-of-contents)

## 8. Cross-repo integration

- [ ] **Upstream**: pyfolio calls `empyrical.*` for the deprecated metrics
      in `timeseries.py`. Grep `import empyrical` / `from empyrical` to see
      the exact surface.
- [ ] **Downstream**: `utils.extract_rets_pos_txn_from_zipline` is the
      bridge from `zipline-reloaded` backtest results into pyfolio's
      `(returns, positions, transactions)` triple.
- [ ] **Adjacent**: `alphalens.performance.create_pyfolio_input` produces
      the same triple so that factor-research results can flow into
      pyfolio tear sheets.

[⬆ 回到目录](#table-of-contents)

## 9. Known quirks / hot paths (from `DEPENDENCIES.md`)

- [ ] `utils.print_table` is called by 8+ `show_*` functions — changing it
      affects every text output.
- [ ] `utils.check_intraday` gates 6 tear sheets — its heuristics decide
      daily vs. intraday rendering.
- [ ] `pos.get_percent_alloc` is the hot numeric primitive — used by
      capacity, position analysis, and perf_attrib.
- [ ] `txn.get_turnover` is shared between `timeseries.perf_stats`,
      `perf_attrib._align_and_warn`, and two plotting functions.

[⬆ 回到目录](#table-of-contents)

## Suggested order

1. Setup + green tests (§1).
2. Lock in the `(returns, positions, transactions)` data contract (§2).
3. Run `zipline_algo_example.ipynb` end-to-end (§3).
4. Walk `tears.py` entry points (§4) — this is the user-facing surface.
5. Read the **live half** of `timeseries.py` (§5), skipping deprecated
   wrappers on first pass.
6. Read `txn/pos/round_trips/capacity/perf_attrib` (§6).
7. Skim `plotting.py` (§7).
8. Trace upstream/downstream edges (§8).

[⬆ 回到目录](#table-of-contents)
