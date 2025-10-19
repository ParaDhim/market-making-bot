import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

class BacktestAnalyzer:
    def __init__(self, results_file="results/trades.csv"):
        """Analyze backtest results"""
        self.results = pd.read_csv(results_file)
        print(f"Loaded {len(self.results)} data points from backtest")
    
    def calculate_metrics(self):
        """Calculate performance metrics"""
        pnl = self.results['total_pnl'].values
        returns = np.diff(pnl)
        returns = returns[returns != 0]  # Remove zero returns
        
        # Basic metrics
        final_pnl = pnl[-1]
        max_pnl = np.max(pnl)
        min_pnl = np.min(pnl)
        
        # Drawdown calculation
        cummax = np.maximum.accumulate(pnl)
        drawdown = pnl - cummax
        max_drawdown = np.min(drawdown)
        
        # Sharpe ratio (annualized, assuming ~1 sample per second)
        if len(returns) > 0 and np.std(returns) > 0:
            sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252 * 24 * 60 * 60)
        else:
            sharpe = 0
        
        # Sortino ratio (downside deviation)
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0 and np.std(downside_returns) > 0:
            sortino = np.mean(returns) / np.std(downside_returns) * np.sqrt(252 * 24 * 60 * 60)
        else:
            sortino = 0
        
        # Win rate
        wins = np.sum(returns > 0)
        losses = np.sum(returns < 0)
        win_rate = wins / (wins + losses) if (wins + losses) > 0 else 0
        
        # Average win/loss
        avg_win = np.mean(returns[returns > 0]) if wins > 0 else 0
        avg_loss = np.mean(returns[returns < 0]) if losses > 0 else 0
        
        metrics = {
            'Final PnL': final_pnl,
            'Max PnL': max_pnl,
            'Min PnL': min_pnl,
            'Max Drawdown': max_drawdown,
            'Sharpe Ratio': sharpe,
            'Sortino Ratio': sortino,
            'Win Rate': win_rate,
            'Total Trades': wins + losses,
            'Winning Trades': wins,
            'Losing Trades': losses,
            'Avg Win': avg_win,
            'Avg Loss': avg_loss,
            'Profit Factor': abs(avg_win * wins / (avg_loss * losses)) if losses > 0 and avg_loss != 0 else 0
        }
        
        return metrics
    
    def print_metrics(self):
        """Print performance metrics"""
        metrics = self.calculate_metrics()
        
        print("\n" + "="*60)
        print("BACKTEST PERFORMANCE METRICS")
        print("="*60)
        
        print(f"\n📊 Returns:")
        print(f"  Final PnL:        ${metrics['Final PnL']:>12,.2f}")
        print(f"  Max PnL:          ${metrics['Max PnL']:>12,.2f}")
        print(f"  Min PnL:          ${metrics['Min PnL']:>12,.2f}")
        print(f"  Max Drawdown:     ${metrics['Max Drawdown']:>12,.2f}")
        
        print(f"\n📈 Risk-Adjusted Returns:")
        print(f"  Sharpe Ratio:     {metrics['Sharpe Ratio']:>12.2f}")
        print(f"  Sortino Ratio:    {metrics['Sortino Ratio']:>12.2f}")
        
        print(f"\n🎯 Trade Statistics:")
        print(f"  Total Trades:     {metrics['Total Trades']:>12,}")
        print(f"  Winning Trades:   {metrics['Winning Trades']:>12,}")
        print(f"  Losing Trades:    {metrics['Losing Trades']:>12,}")
        print(f"  Win Rate:         {metrics['Win Rate']:>12.1%}")
        print(f"  Avg Win:          ${metrics['Avg Win']:>12,.2f}")
        print(f"  Avg Loss:         ${metrics['Avg Loss']:>12,.2f}")
        print(f"  Profit Factor:    {metrics['Profit Factor']:>12.2f}")
        
        print("\n" + "="*60 + "\n")
    
    def plot_results(self):
        """Create visualization plots"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Trading Strategy Performance', fontsize=16, fontweight='bold')
        
        # 1. Equity Curve
        ax1 = axes[0, 0]
        ax1.plot(self.results['timestamp'], self.results['total_pnl'], 
                linewidth=2, color='#2E86AB')
        ax1.fill_between(self.results['timestamp'], self.results['total_pnl'], 
                         alpha=0.3, color='#2E86AB')
        ax1.axhline(y=0, color='red', linestyle='--', alpha=0.5)
        ax1.set_title('Equity Curve', fontweight='bold')
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Total PnL ($)')
        ax1.grid(True, alpha=0.3)
        
        # 2. Drawdown
        ax2 = axes[0, 1]
        cummax = np.maximum.accumulate(self.results['total_pnl'])
        drawdown = self.results['total_pnl'] - cummax
        ax2.fill_between(self.results['timestamp'], drawdown, 
                        alpha=0.5, color='#A23B72')
        ax2.set_title('Drawdown', fontweight='bold')
        ax2.set_xlabel('Time')
        ax2.set_ylabel('Drawdown ($)')
        ax2.grid(True, alpha=0.3)
        
        # 3. Inventory Over Time
        ax3 = axes[1, 0]
        ax3.plot(self.results['timestamp'], self.results['inventory'], 
                linewidth=2, color='#F18F01')
        ax3.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        ax3.set_title('Inventory (Position)', fontweight='bold')
        ax3.set_xlabel('Time')
        ax3.set_ylabel('BTC')
        ax3.grid(True, alpha=0.3)
        
        # 4. PnL Components
        ax4 = axes[1, 1]
        ax4.plot(self.results['timestamp'], self.results['realized_pnl'], 
                label='Realized PnL', linewidth=2, color='#06A77D')
        ax4.plot(self.results['timestamp'], self.results['unrealized_pnl'], 
                label='Unrealized PnL', linewidth=2, color='#D62246', alpha=0.7)
        ax4.set_title('PnL Breakdown', fontweight='bold')
        ax4.set_xlabel('Time')
        ax4.set_ylabel('PnL ($)')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('results/backtest_performance.png', dpi=300, bbox_inches='tight')
        print("Saved performance plots to results/backtest_performance.png")
        plt.show()
    
    def plot_returns_distribution(self):
        """Plot returns distribution"""
        returns = np.diff(self.results['total_pnl'].values)
        returns = returns[returns != 0]
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Histogram
        ax1 = axes[0]
        ax1.hist(returns, bins=50, color='#2E86AB', alpha=0.7, edgecolor='black')
        ax1.axvline(x=0, color='red', linestyle='--', linewidth=2)
        ax1.set_title('Returns Distribution', fontweight='bold')
        ax1.set_xlabel('Return ($)')
        ax1.set_ylabel('Frequency')
        ax1.grid(True, alpha=0.3)
        
        # Q-Q plot
        ax2 = axes[1]
        from scipy import stats
        stats.probplot(returns, dist="norm", plot=ax2)
        ax2.set_title('Q-Q Plot (Normal Distribution)', fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('results/returns_distribution.png', dpi=300, bbox_inches='tight')
        print("Saved returns distribution to results/returns_distribution.png")
        plt.show()

def main():
    print("=== Backtest Analysis ===\n")
    
    results_file = "results/trades.csv"
    if not Path(results_file).exists():
        print(f"Error: Results file not found: {results_file}")
        print("Run the C++ trading engine first!")
        return
    
    analyzer = BacktestAnalyzer(results_file)
    analyzer.print_metrics()
    analyzer.plot_results()
    analyzer.plot_returns_distribution()
    
    print("\n✅ Analysis complete!")

if __name__ == "__main__":
    main()