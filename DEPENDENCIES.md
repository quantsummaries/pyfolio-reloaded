# Pyfolio Function Dependencies

> **Version**: written against branch `yzeng` at HEAD `5afb198` (2026-10-08).

This document maps the in-package function calls in `src/pyfolio`. It is
intended as a navigation aid for reviewing implementation changes: a change to
a lower-level function may affect every caller listed beneath it.

Dependencies below are direct calls between Pyfolio functions. Calls into
NumPy, pandas, SciPy, matplotlib, seaborn, and **empyrical** are not listed.
Most legacy return/risk metrics in `timeseries.py` are deprecated wrappers that
delegate to `empyrical-reloaded` at runtime; those edges are called out
separately because they are not visible as direct calls. The graph follows the
checked-in source on branch `yzeng` and may need updating when functions are
added or refactored.

## Table of Contents
- [Function dependency layers](#function-dependency-layers)
  - [Level 0 — foundational functions and values](#level-0--foundational-functions-and-values)
  - [Level 1 — shared operations, deprecated wrappers, and composed primitives](#level-1--shared-operations-deprecated-wrappers-and-composed-primitives)
  - [Level 1 (continued) — deprecated metrics wrappers](#level-1-continued--deprecated-metrics-wrappers)
  - [Level 2 — tear-sheet generators (mid-size)](#level-2--tear-sheet-generators-mid-size)
  - [Level 3 — most composed entry point](#level-3--most-composed-entry-point)
- [Decorator / dynamic edges](#decorator--dynamic-edges)
- [Module dependency overview](#module-dependency-overview)
- [Key observations](#key-observations)

## Function dependency layers
Levels indicate the direction of dependency: higher-level functions rely on
lower-level functions. Functions within a level are grouped by purpose rather
than guaranteed to be entirely independent.

### Level 0 — foundational functions and values

These functions do not call another Pyfolio function directly.

1. `pyfolio.utils`: `check_intraday`, `clip_returns_to_benchmark`,
   `configure_legend`, `detect_intraday`, `estimate_intraday`,
   `format_asset`, `get_symbol_rets`, `one_dec_places`, `percentage`,
   `print_table`, `register_return_func`, `sample_colormap`,
   `standardize_data`, `to_series`, `to_utc`, `two_dec_places`, `vectorize`.
2. `pyfolio.txn`: `adjust_returns_for_slippage`, `get_turnover`,
   `get_txn_vol`, `make_transaction_frame`, `map_transaction`.
3. `pyfolio.pos`: `extract_pos`, `get_long_short_pos`, `get_percent_alloc`,
   `get_sector_exposures`, `get_top_long_short_abs`.
4. `pyfolio.round_trips`: `_groupby_consecutive`, `add_closing_transactions`,
   `agg_all_long_short`, `apply_sector_mappings_to_round_trips`,
   `extract_round_trips`, `gen_round_trip_stats`.
5. `pyfolio.capacity`: `apply_slippage_penalty`, `daily_txns_with_bar_data`,
   `get_low_liquidity_transactions`.
6. `pyfolio.perf_attrib`: `_cumulative_returns_less_costs`,
   `compute_exposures`, `create_perf_attrib_stats`, `perf_attrib`,
   `plot_returns`.
7. `pyfolio.timeseries` (still live, non-deprecated): `calc_bootstrap`,
   `calc_distribution_stats`, `common_sense_ratio`,
   `extract_interesting_date_ranges`, `forecast_cone_bootstrap`,
   `gen_drawdown_table`, `get_max_drawdown`, `get_max_drawdown_underwater`,
   `get_top_drawdowns`, `gross_lev`, `normalize`, `perf_stats_bootstrap`,
   `rolling_beta`, `rolling_regression`, `rolling_sharpe`,
   `rolling_volatility`, `simulate_paths`, `summarize_paths`,
   `value_at_risk`, `var_cov_var_normal`.
8. `pyfolio.plotting` (primitives): `axes_style`, `customize`,
   `plot_annual_returns`, `plot_cones`, `plot_drawdown_underwater`,
   `plot_exposures`, `plot_holdings`, `plot_long_short_holdings`,
   `plot_monthly_returns_dist`, `plot_monthly_returns_heatmap`,
   `plot_monthly_returns_timeseries`, `plot_prob_profit_trade`,
   `plot_return_quantiles`, `plot_returns`, `plot_rolling_returns`,
   `plot_sector_allocations`, `plot_txn_time_hist`, `plotting_context`.
9. `pyfolio.tears`: `timer` (decorator).
10. `pyfolio.deprecate`: `deprecated` (its returned wrapper calls the
    decorated function dynamically).
11. `pyfolio.interesting_periods` and `pyfolio.ipycompat` define no
    top-level functions.

### Level 1 — shared operations, deprecated wrappers, and composed primitives

1. `utils.extract_rets_pos_txn_from_zipline` → `pos.extract_pos`,
   `txn.make_transaction_frame`. This is the bridge from a zipline backtest
   result into pyfolio's `(returns, positions, transactions)` tuple.
2. `pos.get_max_median_position_concentration` → `pos.get_percent_alloc`.
3. `capacity.days_to_liquidate_positions` → `pos.get_percent_alloc`.
4. `capacity.get_max_days_to_liquidate_by_ticker` → `pos.get_percent_alloc`.
5. `perf_attrib._align_and_warn` → `txn.get_turnover`.
6. `perf_attrib._stack_positions` → `pos.get_percent_alloc`.
7. `perf_attrib.plot_alpha_returns` → `utils.configure_legend`.
8. `perf_attrib.plot_factor_contribution_to_perf` → `utils.configure_legend`.
9. `perf_attrib.plot_risk_exposures` → `utils.configure_legend`.
10. `perf_attrib.show_perf_attrib_stats` → `utils.print_table`.
11. `round_trips.print_round_trip_stats` → `utils.print_table`.
12. `timeseries.perf_stats` → `txn.get_turnover`.
13. `plotting.plot_capacity_sweep` → `capacity.apply_slippage_penalty`,
    `capacity.daily_txns_with_bar_data`.
14. `plotting.plot_daily_turnover_hist` → `txn.get_turnover`.
15. `plotting.plot_daily_volume` → `txn.get_txn_vol`.
16. `plotting.plot_drawdown_periods` → `timeseries.gen_drawdown_table`.
17. `plotting.plot_gross_leverage` → `timeseries.gross_lev`.
18. `plotting.plot_perf_stats` → `timeseries.perf_stats_bootstrap`.
19. `plotting.plot_rolling_beta` → `timeseries.rolling_beta`.
20. `plotting.plot_rolling_sharpe` → `timeseries.rolling_sharpe`.
21. `plotting.plot_rolling_volatility` → `timeseries.rolling_volatility`.
22. `plotting.plot_round_trip_lifetimes` → `utils.format_asset`.
23. `plotting.plot_slippage_sensitivity` → `txn.adjust_returns_for_slippage`.
24. `plotting.plot_slippage_sweep` → `txn.adjust_returns_for_slippage`.
25. `plotting.plot_turnover` → `txn.get_turnover`.
26. `plotting.show_and_plot_top_positions` → `pos.get_top_long_short_abs`,
    `utils.print_table`.
27. `plotting.show_perf_stats` → `utils.print_table`.
28. `plotting.show_profit_attribution` → `utils.print_table`.
29. `plotting.show_worst_drawdown_periods` →
    `timeseries.gen_drawdown_table`, `utils.print_table`.

### Level 1 (continued) — deprecated metrics wrappers

The following `timeseries.py` functions are thin wrappers that apply the
`deprecated` decorator and then forward to `empyrical` at call time. They
appear here because `deprecated` is a direct call, but their real numeric
work is done outside this package:

- `aggregate_returns`, `alpha`, `alpha_beta`, `annual_return`,
  `annual_volatility`, `beta`, `calmar_ratio`, `cum_returns`,
  `downside_risk`, `max_drawdown`, `omega_ratio`, `sharpe_ratio`,
  `sortino_ratio`, `stability_of_timeseries`, `tail_ratio`.

### Level 2 — tear-sheet generators (mid-size)

1. `tears.create_capacity_tear_sheet` → `utils.check_intraday`,
   `capacity.get_low_liquidity_transactions`,
   `capacity.get_max_days_to_liquidate_by_ticker`,
   `plotting.plot_capacity_sweep`, `utils.print_table`.
2. `tears.create_full_tear_sheet` → `txn.adjust_returns_for_slippage`,
   `utils.check_intraday`. (It chains the other tear sheets; see Level 3.)
3. `tears.create_interesting_times_tear_sheet` →
   `utils.clip_returns_to_benchmark`,
   `timeseries.extract_interesting_date_ranges`, `utils.print_table`.
4. `tears.create_perf_attrib_tear_sheet` → `perf_attrib.perf_attrib`,
   `perf_attrib.plot_factor_contribution_to_perf`, `plotting.plot_returns`,
   `perf_attrib.plot_risk_exposures`,
   `perf_attrib.show_perf_attrib_stats`.
5. `tears.create_returns_tear_sheet` → many `plotting.*` and `show_*`
   helpers (see edge list).
6. `tears.create_round_trip_tear_sheet` → `round_trips.add_closing_transactions`,
   `round_trips.apply_sector_mappings_to_round_trips`, `utils.check_intraday`,
   `round_trips.extract_round_trips`, `plotting.plot_prob_profit_trade`,
   `plotting.plot_round_trip_lifetimes`, `round_trips.print_round_trip_stats`,
   `plotting.show_profit_attribution`.
7. `tears.create_simple_tear_sheet` → `txn.adjust_returns_for_slippage`,
   `utils.check_intraday`, `pos.get_percent_alloc`, plus multiple
   `plotting.*` and `show_*` helpers.
8. `tears.create_txn_tear_sheet` → `utils.check_intraday`,
   `plotting.plot_daily_turnover_hist`, `plotting.plot_daily_volume`,
   `plotting.plot_slippage_sensitivity`, `plotting.plot_slippage_sweep`,
   `plotting.plot_turnover`, `plotting.plot_txn_time_hist`.
9. `plotting.plot_max_median_position_concentration` →
   `pos.get_max_median_position_concentration`.

### Level 3 — most composed entry point

1. `tears.create_position_tear_sheet` → `utils.check_intraday`,
   `pos.get_percent_alloc`, `pos.get_sector_exposures`,
   `plotting.plot_exposures`, `plotting.plot_gross_leverage`,
   `plotting.plot_holdings`, `plotting.plot_long_short_holdings`,
   `plotting.plot_max_median_position_concentration`,
   `plotting.plot_sector_allocations`,
   `plotting.show_and_plot_top_positions`.

`create_full_tear_sheet` itself does not appear at the top of the layering
because its body mostly chains the other tear-sheet functions
(`create_simple_tear_sheet`, `create_position_tear_sheet`,
`create_round_trip_tear_sheet`, `create_perf_attrib_tear_sheet`,
`create_interesting_times_tear_sheet`) — those calls are resolved through
dynamic dispatch / loop constructs rather than static `Call` nodes.

[⬆ 回到目录](#table-of-contents)

## Decorator / dynamic edges
- `plotting.customize` wraps every public plotting function; it applies
  seaborn context and then invokes the wrapped function.
- `tears.timer` times how long a tear-sheet function takes.
- `deprecate.deprecated` wraps the legacy `timeseries.*` metrics listed above
  and forwards calls to the empyrical equivalent.
- `utils.register_return_func` registers a callback used by
  `utils.get_symbol_rets` for non-Yahoo data sources.

[⬆ 回到目录](#table-of-contents)

## Module dependency overview
```text
pyfolio.deprecate
    └── generic deprecation decorator (wraps timeseries legacy metrics)

pyfolio.utils
    ├── input/data plumbing: to_series, standardize_data, to_utc, check_intraday
    ├── display helpers: print_table, configure_legend, format_asset, percentage
    └── zipline bridge: extract_rets_pos_txn_from_zipline

pyfolio.txn
    └── raw transaction analysis: turnover, slippage, volume, txn frame

pyfolio.pos
    └── position analysis: percent allocation, long/short, sector exposure

pyfolio.round_trips
    └── closed-trade decomposition

pyfolio.capacity
    └── liquidity / liquidation analysis (uses pos.get_percent_alloc)

pyfolio.perf_attrib
    ├── factor exposure regression
    ├── plotting helpers (configure_legend)
    └── show_perf_attrib_stats

pyfolio.timeseries
    ├── live analytics: drawdown tables, rolling stats, bootstrap, cones
    └── deprecated wrappers → empyrical (sharpe, sortino, alpha, beta, ...)

pyfolio.plotting
    ├── styling: customize, plotting_context, axes_style
    ├── table renderers (→ utils.print_table)
    └── diagnostic plots (→ timeseries rolling stats, txn, pos, capacity)

pyfolio.tears
    └── orchestrates plotting + timeseries + pos/txn/round_trips/capacity
        into assembled reports
```

[⬆ 回到目录](#table-of-contents)

## Key observations
- **`utils.print_table` is the most depended-upon display helper** — used by
  `show_perf_stats`, `show_profit_attribution`, `show_worst_drawdown_periods`,
  `show_and_plot_top_positions`, `show_perf_attrib_stats`,
  `print_round_trip_stats`, and `create_capacity_tear_sheet` /
  `create_interesting_times_tear_sheet`.
- **`utils.check_intraday` is called by six of the ten tear-sheet
  generators** — it gates whether a tear sheet renders daily vs. intraday
  plots. Changing its heuristics affects nearly every high-level entry point.
- **`pos.get_percent_alloc` is the hot numeric primitive** — used by
  `create_position_tear_sheet`, `create_simple_tear_sheet`,
  `capacity.days_to_liquidate_positions`,
  `capacity.get_max_days_to_liquidate_by_ticker`,
  `pos.get_max_median_position_concentration`, and
  `perf_attrib._stack_positions`.
- **`txn.get_turnover`** is the shared transaction statistic, used by
  `timeseries.perf_stats`, `perf_attrib._align_and_warn`,
  `plotting.plot_daily_turnover_hist`, and `plotting.plot_turnover`.
- **`timeseries.py` is mostly a legacy shim.** The 15 deprecated metrics
  (`sharpe_ratio`, `sortino_ratio`, `alpha`, `beta`, `max_drawdown`, …)
  delegate to `empyrical-reloaded` at runtime. The live analytics in
  `timeseries.py` are drawdown tables, rolling statistics, bootstrap
  simulation, and cones — these are the functions that actually do work
  inside pyfolio.
- **`tears.py` is purely an orchestration layer.** It performs no numeric
  computation itself; every tear sheet is a composition of `plotting.*`,
  `timeseries.*`, and the `pos/txn/round_trips/capacity` analysis modules.

[⬆ 回到目录](#table-of-contents)