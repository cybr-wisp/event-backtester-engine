# backtester/analysis/plots.py
import matplotlib.pyplot as plt
from .metrics import compute_drawdown

def plot_equity_and_drawdown(equity_curve, out_dir: str = "outputs"):
    equity = equity_curve["equity"]
    dd = compute_drawdown(equity)

    # Equity curve
    plt.figure()
    equity.plot()
    plt.title("Equity Curve")
    plt.xlabel("Time")
    plt.ylabel("Equity")
    plt.tight_layout()
    plt.savefig(f"{out_dir}/equity_curve.png", dpi=150)
    plt.close()

    # Drawdown curve
    plt.figure()
    dd.plot()
    plt.title("Drawdown")
    plt.xlabel("Time")
    plt.ylabel("Drawdown")
    plt.tight_layout()
    plt.savefig(f"{out_dir}/drawdown_curve.png", dpi=150)
    plt.close()
