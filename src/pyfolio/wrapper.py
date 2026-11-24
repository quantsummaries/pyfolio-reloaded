from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from . import plotting, tears, timeseries


def return_stats_wrapper(port_rets: pd.Series,
                         freq: int,
                         output_dir: Path | str,
                         benchmark_rets: pd.Series = None) -> pd.DataFrame:
    """Wrapper for pyfolio's return tear sheet and performance statistics.

    Args:
        port_rets (pd.Series): Portfolio returns.
        freq (int): Frequency of trades. If 1, daily returns are used; otherwise, returns are aggregated.
        output_dir (Path | str): Directory to save the output files.
        benchmark_rets (pd.Series, optional): Benchmark returns. Defaults to None.

    Returns:
        pd.DataFrame: Performance statistics of the portfolio returns.
    """
    if freq < 1:
        raise ValueError("Frequency must be a positive integer.")
    if port_rets.name is None:
        raise ValueError("Portfolio returns series must have a name.")
    output_dir = Path(output_dir)

    existing_figures = set(plt.get_fignums())

    try:
        if freq == 1:
            fig = tears.create_returns_tear_sheet(port_rets, benchmark_rets=benchmark_rets, return_fig=True)
            stats = timeseries.perf_stats(port_rets)
            statistics = stats.rename("value").rename_axis("metric").reset_index()
        else:
            fig, ax = plt.subplots(figsize=(12, 6))
            plotting.plot_rolling_returns(port_rets, ax=ax, factor_returns=benchmark_rets, cone_std=None)
            ax.set_title(f"{port_rets.name} returns, one trade every {freq} sessions")
            statistics = pd.DataFrame({}, columns=["metric", "value"])

        output_dir.mkdir(parents=True, exist_ok=True)
        output = output_dir / f"returns_tear_sheet_{port_rets.name}.png"

        partial = output.with_name(f"{output.name}.partial")
        try:
            fig.savefig(partial, format="png", bbox_inches="tight")
            partial.replace(output)
        finally:
            partial.unlink(missing_ok=True)

        port_rets.rename_axis("date").to_frame(name=port_rets.name).reset_index().to_parquet(
            output_dir / f"factor_returns_{port_rets.name}.parquet",
        )

        if freq == 1:
            statistics.to_parquet(output_dir / f"perf_stats_{port_rets.name}.parquet")
        else:
            # Do not retain daily statistics from a previous frequency-1 run.
            (output_dir / f"perf_stats_{port_rets.name}.parquet").unlink(missing_ok=True)

    finally:
        for number in set(plt.get_fignums()) - existing_figures:
            plt.close(number)

    return statistics