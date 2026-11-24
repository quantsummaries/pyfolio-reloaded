import numbers
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from . import plotting, tears, timeseries


def return_stats_wrapper(port_rets: pd.Series,
                         freq: int,
                         output_dir: Path | str,
                         benchmark_rets: pd.Series = None) -> pd.DataFrame:
    """Generate a returns tear-sheet image and write returns/statistics artifacts.

    Args:
        port_rets (pd.Series): Portfolio returns.
        freq (int): Trade frequency in sessions. If 1, a full returns tear sheet and
            performance statistics are generated. If greater than 1, a rolling-returns
            plot is generated and no performance statistics are computed.
        output_dir (Path | str): Directory to save the output files.
        benchmark_rets (pd.Series, optional): Benchmark returns for plotting. Defaults to None.

    Returns:
        pd.DataFrame: Portfolio performance statistics with columns ``metric`` and
            ``value`` when ``freq == 1``; otherwise an empty DataFrame with the same
            columns.
    """
    if freq < 1 or not isinstance(freq, numbers.Integral):
        raise ValueError("Frequency must be a positive integer.")
    if port_rets.name is None:
        raise ValueError("Portfolio returns series must have a name.")
    output_dir = Path(output_dir)

    existing_figures = set(plt.get_fignums())

    try:
        if freq == 1:
            fig = tears.create_returns_tear_sheet(port_rets, benchmark_rets=benchmark_rets, return_fig=True)
            stats = timeseries.perf_stats(port_rets, factor_returns=benchmark_rets)
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
            output_dir / f"returns_{port_rets.name}.parquet",
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