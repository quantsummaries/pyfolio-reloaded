import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from pyfolio.extra import plot_rolling_returns_df


@pytest.fixture
def ax():
    fig, axes = plt.subplots()
    yield axes
    plt.close(fig)


@pytest.fixture
def returns():
    return pd.DataFrame(
        {"first": [0.1, -0.05, np.nan], "second": [-0.1, 0.2, 0.0]},
        index=pd.date_range("2024-01-01", periods=3),
    )


def test_compounds_plots_and_exports(returns, ax, tmp_path):
    original = returns.copy()
    result = plot_rolling_returns_df(returns, tmp_path / "plots", ax=ax)
    expected = pd.DataFrame(
        {"first": [1.1, 1.045, 1.045], "second": [0.9, 1.08, 1.08]},
        index=returns.index,
    )
    pd.testing.assert_frame_equal(result, expected)
    pd.testing.assert_frame_equal(returns, original)
    for line, column in zip(ax.lines, expected):
        np.testing.assert_allclose(line.get_ydata(), expected[column])
        assert line.get_label() == column
    assert ax.lines[0].get_color() != ax.lines[1].get_color()
    assert (tmp_path / "plots" / "cumulative_returns.png").stat().st_size > 0
    saved = pd.read_csv(tmp_path / "plots" / "cumulative_returns.csv", index_col=0)
    np.testing.assert_allclose(saved, expected)


def test_volatility_matching_and_benchmark(returns, ax):
    benchmark = pd.Series([0.02, -0.01, 0.03], index=returns.index, name="Market")
    result = plot_rolling_returns_df(
        returns,
        factor_returns=benchmark,
        volatility_match=True,
        logy=True,
        legend_loc=None,
        ax=ax,
        lw=3,
    )
    expected = (
        1 + returns.div(returns.std()).mul(benchmark.std()).fillna(0)
    ).cumprod()
    pd.testing.assert_frame_equal(result, expected)
    np.testing.assert_allclose(ax.lines[0].get_ydata(), (1 + benchmark).cumprod())
    assert ax.get_yscale() == "log"
    assert ax.get_legend() is None


def test_live_split_and_cones(returns, ax):
    calls = []

    def cone(history, days, cone_std, starting_value):
        calls.append((history, days, starting_value))
        assert cone_std == [1]
        return pd.DataFrame(
            {
                1.0: [starting_value * 1.1] * days,
                -1.0: [starting_value * 0.9] * days,
            }
        )

    plot_rolling_returns_df(
        returns,
        live_start_date="2024-01-03T00:00:00Z",
        cone_std=1,
        cone_function=cone,
        ax=ax,
    )
    assert len(calls) == 2
    assert len(ax.collections) == 2
    assert ax.lines[0].get_label() == "first (Backtest)"
    assert ax.lines[1].get_label() == "first (Live)"
    assert ax.lines[1].get_linestyle() == "--"
    assert ax.lines[0].get_color() == ax.lines[1].get_color()
    assert calls[0][1] == 1
    assert calls[0][2] == pytest.approx(1.045)


def test_invalid_inputs(returns, ax):
    with pytest.raises(ValueError, match="factor_returns"):
        plot_rolling_returns_df(returns, volatility_match=True, ax=ax)
    with pytest.raises(TypeError, match="DatetimeIndex"):
        plot_rolling_returns_df(returns.reset_index(drop=True), ax=ax)
    with pytest.raises(ValueError, match="at least one"):
        plot_rolling_returns_df(returns.iloc[:0], ax=ax)
