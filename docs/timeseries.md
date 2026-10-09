# pyfolio.timeseries

`src/pyfolio/timeseries.py` provides calculations on return and position time
series: performance statistics, drawdown analysis, rolling measures, bootstrap
statistics, forecast cones, and extraction of returns around historical events.
Much of the module is a set of thin, deprecated wrappers around the
[`empyrical`](https://github.com/stefan-jansen/empyrical-reloaded) library;
the plotting and tear-sheet modules call both the wrappers' underlying
`empyrical` functions and the native functions defined here.

## Table of Contents

- [Overview](#overview)
- [Conventions](#conventions)
- [Module-level objects](#module-level-objects)
- [Performance statistics](#performance-statistics)
  - [`perf_stats`](#perf_stats)
  - [`perf_stats_bootstrap`](#perf_stats_bootstrap)
  - [`calc_bootstrap`](#calc_bootstrapfunc-returns-args-kwargs)
  - [`calc_distribution_stats`](#calc_distribution_statsx)
  - [`value_at_risk`](#value_at_riskreturns-periodnone-sigma20)
  - [`var_cov_var_normal`](#var_cov_var_normalp-c-mu0-sigma1)
  - [`common_sense_ratio`](#common_sense_ratioreturns)
  - [`gross_lev`](#gross_levpositions)
- [Drawdowns](#drawdowns)
- [Rolling measures](#rolling-measures)
- [Forecast cones](#forecast-cones)
- [Interesting date ranges](#interesting-date-ranges)
- [Return transformations](#return-transformations)
- [Deprecated empyrical wrappers](#deprecated-empyrical-wrappers)
- [Dependencies](#dependencies)
  - [Function dependency overview](#function-dependency-overview)
  - [Per-function dependencies](#per-function-dependencies)
  - [Indirect dependencies](#indirect-dependencies)
  - [Who depends on `timeseries`](#who-depends-on-timeseries)
- [Practical usage](#practical-usage)
- [Notes](#notes)

## Overview

| Area | Functions |
| --- | --- |
| Summary statistics | `perf_stats`, `perf_stats_bootstrap`, `calc_bootstrap`, `calc_distribution_stats` |
| Risk measures | `value_at_risk`, `var_cov_var_normal`, `common_sense_ratio`, `gross_lev` |
| Drawdowns | `get_max_drawdown`, `get_max_drawdown_underwater`, `get_top_drawdowns`, `gen_drawdown_table` |
| Rolling | `rolling_beta`, `rolling_regression`, `rolling_volatility`, `rolling_sharpe` |
| Forecast cones | `simulate_paths`, `summarize_paths`, `forecast_cone_bootstrap` |
| Events | `extract_interesting_date_ranges` |
| Transformations | `normalize` |
| Deprecated wrappers | `max_drawdown`, `annual_return`, `annual_volatility`, `calmar_ratio`, `omega_ratio`, `sortino_ratio`, `downside_risk`, `sharpe_ratio`, `alpha_beta`, `alpha`, `beta`, `stability_of_timeseries`, `tail_ratio`, `cum_returns`, `aggregate_returns` |

## Conventions

- `returns` is a daily, non-cumulative `pd.Series` of decimal returns indexed
  by date. `factor_returns` is a benchmark series in the same style.
- `positions` is a `pd.DataFrame` of daily net position values (dollars per
  asset) with a `cash` column. `transactions` is a one-row-per-trade DataFrame.
  See `tears.create_full_tear_sheet` for full descriptions.
- Rolling window lengths are expressed in days. Defaults use
  `APPROX_BDAYS_PER_MONTH * 6` (six months of business days).
- Annualization uses `APPROX_BDAYS_PER_YEAR` (252) for the native rolling
  functions in this module.

## Module-level objects

### `DEPRECATION_WARNING`

Message used by the `@deprecated` decorator on the empyrical wrappers: risk
functions in `pyfolio.timeseries` are deprecated and will be removed in a
future release; install `empyrical` instead.

### `SIMPLE_STAT_FUNCS`

Statistic functions applied to `returns` alone, in order:
`ep.annual_return`, `ep.cum_returns_final`, `ep.annual_volatility`,
`ep.sharpe_ratio`, `ep.calmar_ratio`, `ep.stability_of_timeseries`,
`ep.max_drawdown`, `ep.omega_ratio`, `ep.sortino_ratio`, `stats.skew`,
`stats.kurtosis`, `ep.tail_ratio`, and this module's `value_at_risk`.

### `FACTOR_STAT_FUNCS`

Statistics that need a benchmark: `ep.alpha` and `ep.beta`.

### `STAT_FUNC_NAMES`

Mapping from function `__name__` to the display label used in
`perf_stats` output.

| Function name | Label |
| --- | --- |
| `annual_return` | Annual return |
| `cum_returns_final` | Cumulative returns |
| `annual_volatility` | Annual volatility |
| `sharpe_ratio` | Sharpe ratio |
| `calmar_ratio` | Calmar ratio |
| `stability_of_timeseries` | Stability |
| `max_drawdown` | Max drawdown |
| `omega_ratio` | Omega ratio |
| `sortino_ratio` | Sortino ratio |
| `skew` | Skew |
| `kurtosis` | Kurtosis |
| `tail_ratio` | Tail ratio |
| `common_sense_ratio` | Common sense ratio |
| `value_at_risk` | Daily value at risk |
| `alpha` | Alpha |
| `beta` | Beta |

## Performance statistics

### `perf_stats`

```python
perf_stats(returns, factor_returns=None, positions=None, transactions=None,
           turnover_denom="AGB")
```

Calculates a set of performance metrics and returns them as a `pd.Series`.
It is the function `plotting.show_perf_stats` uses to build its table.

- **From `returns` alone**, one entry for each function in `SIMPLE_STAT_FUNCS`:
  Annual return, Cumulative returns, Annual volatility, Sharpe ratio, Calmar
  ratio, Stability, Max drawdown, Omega ratio, Sortino ratio, Skew, Kurtosis,
  Tail ratio, and Daily value at risk.
- **With non-empty `positions`:** adds `Gross leverage` (mean of `gross_lev`).
- **With non-empty `positions` and `transactions`:** adds `Daily turnover`
  (mean of `txn.get_turnover(positions, transactions, turnover_denom)`).
- **With `factor_returns`:** adds `Alpha` and `Beta`.

| Parameter | Description |
| --- | --- |
| `returns` | Daily non-cumulative strategy returns. |
| `factor_returns` | Benchmark returns. If `None`, alpha and beta are not computed. |
| `positions` | Daily net position values; enables gross leverage. |
| `transactions` | Executed trades; with `positions`, enables turnover. |
| `turnover_denom` | `"AGB"` or `"portfolio_value"`; see `txn.get_turnover`. |

### `perf_stats_bootstrap`

```python
perf_stats_bootstrap(returns, factor_returns=None, return_stats=True, **kwargs)
```

Bootstraps each statistic in `SIMPLE_STAT_FUNCS` (and, with `factor_returns`,
`FACTOR_STAT_FUNCS`) using `calc_bootstrap`.

- `return_stats=True` (default): returns a DataFrame indexed by statistic with
  columns `mean`, `median`, `5%`, and `95%`.
- `return_stats=False`: returns a DataFrame of the raw bootstrap samples, one
  column per statistic. `plotting.plot_perf_stats` uses this form.

`**kwargs` is accepted but not used. `show_perf_stats(bootstrap=True)` passes
`positions`, `transactions`, and `turnover_denom` to this function; they are
absorbed by `**kwargs` and ignored, so bootstrapped results do not include
gross leverage or turnover.

### `calc_bootstrap(func, returns, *args, **kwargs)`

Runs a bootstrap of a summary statistic: draws `n_samples` resamples of
`returns` (with replacement, same length as the input), evaluates `func` on
each, and returns a `numpy.ndarray` of the results.

| Parameter | Description |
| --- | --- |
| `func` | Function taking returns (or returns and factor returns) and returning a scalar. Extra `args` and `kwargs` are forwarded to it. |
| `returns` | Daily non-cumulative returns. |
| `factor_returns` (kwarg) | Optional benchmark; resampled with the same indices as `returns`. |
| `n_samples` (kwarg) | Number of bootstrap samples. Default `1000`. |

Resampled series have their index reset to a `RangeIndex`, so `func` must not
depend on dates. The module uses NumPy's global random state; seed it with
`np.random.seed(...)` for repeatable results.

### `calc_distribution_stats(x)`

Returns a `pd.Series` of `mean`, `median`, `std`, `5%`, `25%`, `75%`, `95%`,
and `IQR` for an array or Series.

### `value_at_risk(returns, period=None, sigma=2.0)`

Daily (or aggregated-period) value at risk estimated as
`mean(returns) - sigma * std(returns)`.

| Parameter | Description |
| --- | --- |
| `period` | `'weekly'`, `'monthly'`, or `'yearly'` to aggregate returns first with `ep.aggregate_returns`; otherwise uses the series as given. |
| `sigma` | Number of standard deviations. Default `2.0`. |

### `var_cov_var_normal(P, c, mu=0, sigma=1)`

Variance-covariance Value-at-Risk for a portfolio of value `P` at confidence
level `c`, assuming normally distributed returns with mean `mu` and standard
deviation `sigma`. Computed as `P - P * (alpha + 1)`, where `alpha` is the
normal quantile at `1 - c`.

### `common_sense_ratio(returns)`

Tail ratio multiplied by `(1 + annual return)`, computed with
`ep.tail_ratio` and `ep.annual_return`. Its docstring describes it as the tail
ratio multiplied by the gain-to-pain ratio, which is not what the code
computes. It has a label in `STAT_FUNC_NAMES` but is not part of
`SIMPLE_STAT_FUNCS`, so `perf_stats` does not report it.

### `gross_lev(positions)`

Gross leverage as a `pd.Series`: the sum of absolute position values excluding
`cash`, divided by total portfolio value (sum of all columns including `cash`),
per day.

## Drawdowns

All drawdown functions work from cumulative returns starting at 1.0 and an
"underwater" series, `cumulative / running_max - 1`.

| Function | Description |
| --- | --- |
| `get_max_drawdown_underwater(underwater)` | Given an underwater series, returns `(peak, valley, recovery)` dates of the deepest drawdown. `recovery` is `np.nan` if the drawdown has not recovered. |
| `get_max_drawdown(returns)` | Computes the underwater series and returns the `(peak, valley, recovery)` **dates** of the maximum drawdown. It does not return the drawdown magnitude. |
| `get_top_drawdowns(returns, top=10)` | Returns a list of up to `top` `(peak, valley, recovery)` tuples, deepest first. After each drawdown is found, its period is removed so that the next one is separate (an unrecovered drawdown truncates the series at its peak). Stops early if no further drawdown exists. |
| `gen_drawdown_table(returns, top=10)` | Builds a `pd.DataFrame` with one row per drawdown. |

### `gen_drawdown_table` output

| Column | Description |
| --- | --- |
| `Net drawdown in %` | `(cumulative at peak - cumulative at valley) / cumulative at peak * 100`. |
| `Peak date` | Date of the peak before the drawdown. |
| `Valley date` | Date of the lowest point. |
| `Recovery date` | Date the peak was regained; `NaT` if not recovered. |
| `Duration` | Number of business days from peak to recovery (`pd.date_range(..., freq="B")`); `NaN` if not recovered. |

The table has `top` rows; rows for drawdowns that were not found stay empty.

To get the maximum-drawdown **value**, use `ep.max_drawdown(returns)` (or the
deprecated `timeseries.max_drawdown`), or the first row of
`gen_drawdown_table`.

## Rolling measures

| Function | Description |
| --- | --- |
| `rolling_beta(returns, factor_returns, rolling_window=APPROX_BDAYS_PER_MONTH * 6)` | Rolling beta of `returns` to `factor_returns`, computed with `ep.beta` over each window. If `factor_returns` is a DataFrame, returns a DataFrame with a column per factor. Results start `rolling_window` observations in. |
| `rolling_regression(returns, factor_returns, rolling_window=APPROX_BDAYS_PER_MONTH * 6, nan_threshold=0.1)` | Rolling multivariate linear regression (`sklearn.linear_model.LinearRegression`) of `returns` on a DataFrame of factors. Returns a DataFrame with an `alpha` column plus one column per factor, indexed by date. |
| `rolling_volatility(returns, rolling_vol_window)` | Rolling standard deviation annualized by `sqrt(APPROX_BDAYS_PER_YEAR)`. |
| `rolling_sharpe(returns, rolling_sharpe_window)` | Rolling mean divided by rolling standard deviation, annualized by `sqrt(APPROX_BDAYS_PER_YEAR)`. Assumes a zero risk-free rate. |

`rolling_regression` skips a date when the NaN fraction check fails
(`nan_threshold`); the regression drops rows with missing factor values.

## Forecast cones

Non-parametric probability cones for forecasting cumulative returns, used by
`plotting.plot_rolling_returns` and `plotting.plot_cones`.

| Function | Description |
| --- | --- |
| `simulate_paths(is_returns, num_days, starting_value=1, num_samples=1000, random_seed=None)` | Draws `num_samples` paths of `num_days` returns by sampling with replacement from the in-sample returns. Returns an array of shape `(num_samples, num_days)`. `starting_value` is accepted but unused here. |
| `summarize_paths(samples, cone_std=(1.0, 1.5, 2.0), starting_value=1.0)` | Converts sampled paths to cumulative returns and returns a DataFrame of cone bounds: columns are `+std` and `-std` floats (for example `1.0` and `-1.0`), computed as the cross-sectional mean plus or minus `std` times the standard deviation. |
| `forecast_cone_bootstrap(is_returns, num_days, cone_std=(1.0, 1.5, 2.0), starting_value=1, num_samples=1000, random_seed=None)` | Runs `simulate_paths` then `summarize_paths` and returns the cone-bounds DataFrame. Does not assume normally distributed returns. |

Use `random_seed` for reproducible cones.

## Interesting date ranges

### `extract_interesting_date_ranges(returns, periods=None)`

Slices `returns` around historical events. `periods` is a dict mapping an
event name to a `(start, end)` pair; by default it uses `PERIODS` from
`pyfolio.interesting_periods`. Returns an `OrderedDict` of
`name -> returns slice`, skipping events with no overlapping returns (or whose
slicing raises an error). `tears.create_interesting_times_tear_sheet` uses it.

## Return transformations

### `normalize(returns, starting_value=1)`

Returns `starting_value * (returns / returns.iloc[0])`: the series divided by
its first value. Note that this scales raw values, it does not compound
returns; use `ep.cum_returns` for cumulative returns.

## Deprecated empyrical wrappers

These functions only forward to `empyrical` and are decorated with
`@deprecated`, which emits a `DeprecationWarning` on each call. Use the
`empyrical` function directly.

| pyfolio function | Forwards to | Notes |
| --- | --- | --- |
| `max_drawdown(returns)` | `ep.max_drawdown` | Returns the drawdown magnitude. |
| `annual_return(returns, period=DAILY)` | `ep.annual_return` | CAGR. |
| `annual_volatility(returns, period=DAILY)` | `ep.annual_volatility` | |
| `calmar_ratio(returns, period=DAILY)` | `ep.calmar_ratio` | |
| `omega_ratio(returns, annual_return_threshhold=0.0)` | `ep.omega_ratio(required_return=...)` | Parameter name is spelled `annual_return_threshhold`. |
| `sortino_ratio(returns, required_return=0, period=DAILY)` | `ep.sortino_ratio` | `period` is not forwarded. |
| `downside_risk(returns, required_return=0, period=DAILY)` | `ep.downside_risk` | |
| `sharpe_ratio(returns, risk_free=0, period=DAILY)` | `ep.sharpe_ratio` | |
| `alpha_beta(returns, factor_returns)` | `ep.alpha_beta` | Returns `(alpha, beta)`. |
| `alpha(returns, factor_returns)` | `ep.alpha` | Annualized alpha. |
| `beta(returns, factor_returns)` | `ep.beta` | |
| `stability_of_timeseries(returns)` | `ep.stability_of_timeseries` | R-squared of a linear fit to cumulative log returns. |
| `tail_ratio(returns)` | `ep.tail_ratio` | Ratio of the 95th to the 5th percentile tails. |
| `cum_returns(returns, starting_value=0)` | `ep.cum_returns` | |
| `aggregate_returns(returns, convert_to)` | `ep.aggregate_returns` | `'weekly'`, `'monthly'`, or `'yearly'`. |

## Dependencies

- **pyfolio modules:** `deprecate` (`deprecated`), `interesting_periods`
  (`PERIODS`), `txn` (`get_turnover`), and `utils`
  (`APPROX_BDAYS_PER_MONTH`, `APPROX_BDAYS_PER_YEAR`, `DAILY`).
- **Third-party:** `empyrical`, `numpy`, `pandas`, `scipy` (`scipy.stats`),
  `scikit-learn` (`linear_model`).
- **Standard library:** `collections.OrderedDict`, `functools.partial`.

Modules that import `timeseries`: `plotting` (statistics, drawdowns, rolling
measures, cones) and `tears` (interesting date ranges).

### Function dependency overview

Within the module, a handful of functions call one another; everything else is
a leaf that only calls `empyrical`, NumPy, pandas, or scikit-learn.

```text
perf_stats
├── SIMPLE_STAT_FUNCS   (ep.* functions, stats.skew, stats.kurtosis, value_at_risk)
├── gross_lev           (if positions)
├── txn.get_turnover    (if positions and transactions)
└── FACTOR_STAT_FUNCS   (ep.alpha, ep.beta; if factor_returns)

perf_stats_bootstrap
├── calc_bootstrap           → SIMPLE_STAT_FUNCS / FACTOR_STAT_FUNCS
└── calc_distribution_stats  (if return_stats)

gen_drawdown_table
└── get_top_drawdowns
    └── get_max_drawdown_underwater

get_max_drawdown
└── get_max_drawdown_underwater

forecast_cone_bootstrap
├── simulate_paths
└── summarize_paths

rolling_beta
└── rolling_beta        (recursive, per column when factor_returns is a DataFrame)
```

`STAT_FUNC_NAMES` is read by both `perf_stats` and `perf_stats_bootstrap` to
label each statistic.

### Per-function dependencies

| Function | `timeseries.py` functions / constants | Other `pyfolio` modules | Third-party / standard library |
| --- | --- | --- | --- |
| `var_cov_var_normal` | — | — | `scipy` (`stats.norm.ppf`) |
| `value_at_risk` | — | — | `empyrical` (`aggregate_returns`) |
| `common_sense_ratio` | — | — | `empyrical` (`tail_ratio`, `annual_return`) |
| `normalize` | — | — | — |
| `gross_lev` | — | — | `pandas` |
| `perf_stats` | `SIMPLE_STAT_FUNCS`, `FACTOR_STAT_FUNCS`, `STAT_FUNC_NAMES`, `value_at_risk`, `gross_lev` | `txn.get_turnover` | `empyrical` (via the stat function lists), `scipy.stats` (`skew`, `kurtosis`), `pandas` |
| `perf_stats_bootstrap` | `SIMPLE_STAT_FUNCS`, `FACTOR_STAT_FUNCS`, `STAT_FUNC_NAMES`, `calc_bootstrap`, `calc_distribution_stats` | — | `pandas`, `collections.OrderedDict` |
| `calc_bootstrap` | — | — | `numpy` (`random.randint`, `empty`) |
| `calc_distribution_stats` | — | — | `numpy`, `pandas` |
| `get_max_drawdown_underwater` | — | — | `numpy` |
| `get_max_drawdown` | `get_max_drawdown_underwater` | — | `empyrical` (`cum_returns`), `numpy` |
| `get_top_drawdowns` | `get_max_drawdown_underwater` | — | `empyrical` (`cum_returns`), `numpy`, `pandas` |
| `gen_drawdown_table` | `get_top_drawdowns` | — | `empyrical` (`cum_returns`), `numpy`, `pandas` (`date_range`) |
| `rolling_beta` | `rolling_beta` (recursive, for DataFrame input) | `utils.APPROX_BDAYS_PER_MONTH` (default window) | `empyrical` (`beta`), `pandas`, `functools.partial` |
| `rolling_regression` | — | `utils.APPROX_BDAYS_PER_MONTH` (default window) | `scikit-learn` (`linear_model.LinearRegression`), `numpy`, `pandas` |
| `rolling_volatility` | — | `utils.APPROX_BDAYS_PER_YEAR` | `numpy` |
| `rolling_sharpe` | — | `utils.APPROX_BDAYS_PER_YEAR` | `numpy` |
| `simulate_paths` | — | — | `numpy` (`random.RandomState`) |
| `summarize_paths` | — | — | `empyrical` (`cum_returns`), `pandas` |
| `forecast_cone_bootstrap` | `simulate_paths`, `summarize_paths` | — | — |
| `extract_interesting_date_ranges` | — | `interesting_periods.PERIODS` (default `periods`) | `pandas`, `collections.OrderedDict` |

The deprecated wrappers each call one `empyrical` function and are wrapped by
`deprecate.deprecated`:

| Function | `pyfolio` modules | Third-party |
| --- | --- | --- |
| `max_drawdown`, `annual_return`, `annual_volatility`, `calmar_ratio`, `omega_ratio`, `sortino_ratio`, `downside_risk`, `sharpe_ratio`, `alpha_beta`, `alpha`, `beta`, `stability_of_timeseries`, `tail_ratio`, `cum_returns`, `aggregate_returns` | `deprecate.deprecated`; `utils.DAILY` (default `period` for several) | `empyrical` (same-named function) |

### Indirect dependencies

- `deprecate` has no further `pyfolio` dependencies.
- `interesting_periods` only uses `pandas` and the standard library.
- `txn` only uses `pandas` (and the standard library).
- `utils` imports `pos` and `txn` and, at module level, `IPython.display`,
  `matplotlib.pyplot`, `packaging`, and `empyrical.utils`. Because
  `timeseries` imports `utils`, importing `timeseries` loads those libraries as
  well, even though it only needs three constants from `utils`.

### Who depends on `timeseries`

| Caller | Functions used |
| --- | --- |
| `plotting` | `gen_drawdown_table` (`plot_drawdown_periods`, `show_worst_drawdown_periods`), `perf_stats` and `perf_stats_bootstrap` (`show_perf_stats`, `plot_perf_stats`), `rolling_beta`, `rolling_volatility`, `rolling_sharpe`, `gross_lev`, `forecast_cone_bootstrap` (default `cone_function` of `plot_rolling_returns`) |
| `tears` | `extract_interesting_date_ranges` (`create_interesting_times_tear_sheet`) |
| `pyfolio.__init__` | Imports the module as `pyfolio.timeseries` |
| `tests/test_timeseries.py` | `gen_drawdown_table`, `get_max_drawdown`, `get_top_drawdowns`, `var_cov_var_normal`, `normalize`, `rolling_sharpe`, `rolling_beta`, `forecast_cone_bootstrap`, `calc_bootstrap`, `gross_lev` |

Public functions that no other module in `src/pyfolio` calls: `rolling_regression`,
`common_sense_ratio`, `get_max_drawdown`, `normalize`, `var_cov_var_normal`,
`simulate_paths`, `summarize_paths` (used internally only by
`forecast_cone_bootstrap`), and the deprecated wrappers.

## Practical usage

```python
import pyfolio as pf

# Summary statistics as a Series
stats = pf.timeseries.perf_stats(returns, factor_returns=benchmark_rets)

# Bootstrapped distribution of the statistics
boot = pf.timeseries.perf_stats_bootstrap(returns, factor_returns=benchmark_rets)

# Worst drawdowns as a table
table = pf.timeseries.gen_drawdown_table(returns, top=5)

# Dates of the single worst drawdown
peak, valley, recovery = pf.timeseries.get_max_drawdown(returns)

# Rolling measures (126 business days is roughly six months)
roll_sharpe = pf.timeseries.rolling_sharpe(returns, 126)
roll_vol = pf.timeseries.rolling_volatility(returns, 126)
roll_beta = pf.timeseries.rolling_beta(returns, benchmark_rets)

# Returns around historical events
events = pf.timeseries.extract_interesting_date_ranges(returns)
```

## Notes

- `get_max_drawdown` returns dates `(peak, valley, recovery)`, not the
  drawdown value, even though its docstring says it returns a float. Use
  `ep.max_drawdown` for the value.
- `sortino_ratio` accepts a `period` argument but does not pass it to
  `ep.sortino_ratio`. `omega_ratio`'s docstring refers to
  `annual_return_threshold`, while the parameter is spelled
  `annual_return_threshhold`.
- `common_sense_ratio` is not what its docstring says (see
  [above](#common_sense_ratioreturns)) and is not reported by `perf_stats`.
- The docstring of `perf_stats` and `perf_stats_bootstrap` mentions computing an
  information ratio when `factor_returns` is given; no information ratio is
  computed.
- `Kurtosis` is scipy's default, which is excess kurtosis (a normal
  distribution gives 0), and `Skew` is the sample skewness from
  `scipy.stats.skew`.
- `normalize` and `cum_returns` have different meanings: `normalize` divides
  by the first value, `cum_returns` compounds returns.
- `rolling_beta` and `rolling_regression` loop over each window in Python and
  can be slow on long series.
- `rolling_regression` uses `np.all(factor_returns_period.isnull().mean()) <
  nan_threshold`. `np.all` returns a boolean, so the check compares a boolean
  with the threshold and does not apply the NaN fraction as documented.
- `perf_stats_bootstrap` ignores `positions`, `transactions`, and
  `turnover_denom`, so bootstrapped tables lack gross leverage and turnover.
- `simulate_paths` accepts `starting_value` but does not use it;
  `forecast_cone_bootstrap` applies it in `summarize_paths`.
- `calc_bootstrap` and `calc_distribution_stats` use NumPy randomness and
  statistics only; results vary between runs unless `np.random.seed` is set.
- The `get_top_drawdowns` loop drops intermediate dates from the underwater
  series, so repeated drawdowns are non-overlapping but the series passed in
  is not modified (it works on a copy).
