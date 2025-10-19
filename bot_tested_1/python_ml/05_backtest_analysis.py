# python_ml/05_backtest_analysis.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def analyze_results():
    """Reads backtest results and calculates/plots performance metrics."""
    print("Analyzing backtest results...")
    try:
        results_df = pd.read_csv('backtest_results.csv')
    except FileNotFoundError:
        print("Error: backtest_results.csv not found. Please run the C++ backtester first.")
        return

    # 1. Plot Equity Curve
    plt.figure(figsize=(12, 6))
    plt.plot(results_df['timestamp'], results_df['pnl'])
    plt.title('Equity Curve')
    plt.xlabel('Ticks')
    plt.ylabel('Cumulative PnL ($)')
    plt.grid(True)
    plt.savefig('equity_curve.png')
    print("Equity curve plot saved to equity_curve.png")
    plt.show()

    # 2. Calculate Performance Metrics
    returns = results_df['pnl'].diff().dropna()
    
    if returns.std() == 0:
        print("No trades were made or PnL did not change. Cannot calculate Sharpe Ratio.")
        sharpe_ratio = 0
    else:
        # Assuming ticks are daily for this simple calculation
        annualization_factor = np.sqrt(252) 
        sharpe_ratio = (returns.mean() / returns.std()) * annualization_factor

    # Max Drawdown
    cumulative = results_df['pnl']
    peak = cumulative.expanding(min_periods=1).max()
    drawdown = (cumulative - peak) / peak
    max_drawdown = drawdown.min()
    
    # Final PnL
    final_pnl = results_df['pnl'].iloc[-1]
    
    print("\n--- Performance Metrics ---")
    print(f"Final PnL: ${final_pnl:.2f}")
    print(f"Annualized Sharpe Ratio: {sharpe_ratio:.2f}")
    print(f"Maximum Drawdown: {max_drawdown:.2%}")
    print("---------------------------\n")

if __name__ == '__main__':
    analyze_results()