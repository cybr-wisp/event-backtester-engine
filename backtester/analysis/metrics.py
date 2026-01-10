# backtester/analysis/metrics.py
from dataclasses import dataclass
import numpy as np
import pandas as pd

@dataclass
class BacktestMetrics:
    total_return: float
    max_drawdown: float
    volatility: float
    sharpe: float

def compute_drawdown(equity: pd.Series) -> pd.Series:
    running_max = equity.cummax()
    drawdown = equity / running_max - 1.0
    return drawdown

def compute_metrics(equity_curve: pd.DataFrame, periods_per_year: int = 252) -> BacktestMetrics:
    """
    equity_curve: DataFrame indexed by timestamp with column 'equity'
    periods_per_year: for daily bars use 252; for minute bars use ~252*390
    """
    equity = equity_curve["equity"].astype(float)

    # returns
    rets = equity.pct_change().dropna()

    # total return
    total_return = float(equity.iloc[-1] / equity.iloc[0] - 1.0)

    # drawdown
    dd = compute_drawdown(equity)
    max_drawdown = float(dd.min())  # negative number, e.g., -0.23

    # volatility (annualized)
    volatility = float(rets.std(ddof=1) * np.sqrt(periods_per_year))

    # Sharpe (simple, rf=0)
    if rets.std(ddof=1) == 0:
        sharpe = 0.0
    else:
        sharpe = float((rets.mean() / rets.std(ddof=1)) * np.sqrt(periods_per_year))

    return BacktestMetrics(
        total_return=total_return,
        max_drawdown=max_drawdown,
        volatility=volatility,
        sharpe=sharpe,
    )
