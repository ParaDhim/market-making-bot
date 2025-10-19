"""
Visualize backtest performance with plots and charts.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os


class PerformanceVisualizer:
    def __init__(self, results_path='results/backtest_results.csv'):
        self.results_path = results_path
        sns.set_style('darkgrid')
        
    def load_results(self):
        """Load backtest results."""
        print("Loading results for visualization...")
        df = pd.read_csv(self.results_path)
        
        # Convert timestamp if present
        if 'timestamp' in df.columns:
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ns')
        
        return df
    
    def plot_equity_curve(self, df):
        """Plot cumulative PnL over time."""
        fig, ax = plt.subplots(figsize=(14, 6))
        
        if 'datetime' in df.columns:
            ax.plot(df['datetime'], df['pnl'], linewidth=2, color='#2E86AB')
            ax.set_xlabel('Time', fontsize=12)
        else:
            ax.plot(df.index, df['pnl'], linewidth=2, color='#2E86AB')
            ax.set_xlabel('Trade Number', fontsize=12)
        
        ax.set_ylabel('Cumulative PnL ($)', fontsize=12)
        ax.set_title('Equity Curve', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # Add horizontal line at 0
        ax.axhline(y=0, color='red', linestyle='--', alpha=0.5)
        
        # Annotate final PnL
        final_pnl = df['pnl'].iloc[-1]
        color = 'green' if final_pnl > 0 else 'red'
        ax.text(0.02, 0.98, f'Final PnL: ${final_pnl:,.2f}', 
                transform=ax.transAxes, fontsize=12, 
                verticalalignment='top', bbox=dict(boxstyle='round', 
                facecolor=color, alpha=0.3))
        
        plt.tight_layout()
        output_path = 'results/equity_curve.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✓ Equity curve saved: {output_path}")
        plt.close()
    
    def plot_drawdown(self, df):
        """Plot drawdown over time."""
        fig, ax = plt.subplots(figsize=(14, 6))
        
        # Calculate drawdown
        cumulative = df['pnl']
        running_max = cumulative.expanding().max()
        drawdown = cumulative - running_max
        drawdown_pct = (drawdown / running_max * 100).fillna(0)
        
        if 'datetime' in df.columns:
            ax.fill_between(df['datetime'], drawdown_pct, 0, 
                           color='red', alpha=0.3)
            ax.plot(df['datetime'], drawdown_pct, color='darkred', linewidth=1.5)
            ax.set_xlabel('Time', fontsize=12)
        else:
            ax.fill_between(df.index, drawdown_pct, 0, color='red', alpha=0.3)
            ax.plot(df.index, drawdown_pct, color='darkred', linewidth=1.5)
            ax.set_xlabel('Trade Number', fontsize=12)
        
        ax.set_ylabel('Drawdown (%)', fontsize=12)
        ax.set_title('Drawdown', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # Annotate max drawdown
        max_dd = drawdown_pct.min()
        ax.text(0.02, 0.02, f'Max Drawdown: {max_dd:.2f}%', 
                transform=ax.transAxes, fontsize=12, 
                verticalalignment='bottom', bbox=dict(boxstyle='round', 
                facecolor='red', alpha=0.3))
        
        plt.tight_layout()
        output_path = 'results/drawdown.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✓ Drawdown plot saved: {output_path}")
        plt.close()
    
    def plot_returns_distribution(self, df):
        """Plot distribution of returns."""
        returns = df['pnl'].diff().dropna()
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # Histogram
        ax1.hist(returns, bins=50, color='steelblue', alpha=0.7, edgecolor='black')
        ax1.axvline(x=0, color='red', linestyle='--', linewidth=2)
        ax1.set_xlabel('Return ($)', fontsize=12)
        ax1.set_ylabel('Frequency', fontsize=12)
        ax1.set_title('Returns Distribution', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        
        # Add statistics
        mean_return = returns.mean()
        std_return = returns.std()
        ax1.text(0.02, 0.98, f'Mean: ${mean_return:.2f}\nStd: ${std_return:.2f}', 
                transform=ax1.transAxes, fontsize=10, 
                verticalalignment='top', bbox=dict(boxstyle='round', 
                facecolor='white', alpha=0.8))
        
        # Q-Q plot
        from scipy import stats
        stats.probplot(returns, dist="norm", plot=ax2)
        ax2.set_title('Q-Q Plot (Normality Check)', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        output_path = 'results/returns_distribution.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✓ Returns distribution saved: {output_path}")
        plt.close()
    
    def plot_rolling_sharpe(self, df, window=1000):
        """Plot rolling Sharpe ratio."""
        returns = df['pnl'].diff().dropna()
        
        # Calculate rolling Sharpe
        rolling_mean = returns.rolling(window).mean()
        rolling_std = returns.rolling(window).std()
        rolling_sharpe = (rolling_mean / rolling_std) * np.sqrt(window)
        
        fig, ax = plt.subplots(figsize=(14, 6))
        
        if 'datetime' in df.columns:
            ax.plot(df['datetime'][window:], rolling_sharpe[window:], 
                   linewidth=2, color='purple')
            ax.set_xlabel('Time', fontsize=12)
        else:
            ax.plot(df.index[window:], rolling_sharpe[window:], 
                   linewidth=2, color='purple')
            ax.set_xlabel('Trade Number', fontsize=12)
        
        ax.set_ylabel(f'Rolling Sharpe Ratio (window={window})', fontsize=12)
        ax.set_title('Rolling Sharpe Ratio', fontsize=14, fontweight='bold')
        ax.axhline(y=0, color='red', linestyle='--', alpha=0.5)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        output_path = 'results/rolling_sharpe.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✓ Rolling Sharpe saved: {output_path}")
        plt.close()
    
    def plot_position_analysis(self, df):
        """Plot position and inventory over time."""
        if 'position' not in df.columns:
            print("⚠ Position data not available, skipping position analysis")
            return
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
        
        # Position over time
        if 'datetime' in df.columns:
            ax1.plot(df['datetime'], df['position'], linewidth=1.5, color='green')
            ax2.plot(df['datetime'], df['pnl'], linewidth=2, color='blue')
        else:
            ax1.plot(df.index, df['position'], linewidth=1.5, color='green')
            ax2.plot(df.index, df['pnl'], linewidth=2, color='blue')
        
        ax1.set_ylabel('Position', fontsize=12)
        ax1.set_title('Position and PnL Over Time', fontsize=14, fontweight='bold')
        ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax1.grid(True, alpha=0.3)
        
        ax2.set_ylabel('Cumulative PnL ($)', fontsize=12)
        ax2.set_xlabel('Time' if 'datetime' in df.columns else 'Trade Number', fontsize=12)
        ax2.axhline(y=0, color='red', linestyle='--', alpha=0.5)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        output_path = 'results/position_analysis.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✓ Position analysis saved: {output_path}")
        plt.close()
    
    def create_summary_dashboard(self, df):
        """Create a comprehensive dashboard with multiple metrics."""
        fig = plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # 1. Equity Curve
        ax1 = fig.add_subplot(gs[0, :])
        if 'datetime' in df.columns:
            ax1.plot(df['datetime'], df['pnl'], linewidth=2, color='#2E86AB')
        else:
            ax1.plot(df.index, df['pnl'], linewidth=2, color='#2E86AB')
        ax1.set_title('Equity Curve', fontsize=12, fontweight='bold')
        ax1.axhline(y=0, color='red', linestyle='--', alpha=0.5)
        ax1.grid(True, alpha=0.3)
        
        # 2. Drawdown
        ax2 = fig.add_subplot(gs[1, :])
        cumulative = df['pnl']
        running_max = cumulative.expanding().max()
        drawdown = cumulative - running_max
        drawdown_pct = (drawdown / running_max * 100).fillna(0)
        if 'datetime' in df.columns:
            ax2.fill_between(df['datetime'], drawdown_pct, 0, color='red', alpha=0.3)
        else:
            ax2.fill_between(df.index, drawdown_pct, 0, color='red', alpha=0.3)
        ax2.set_title('Drawdown', fontsize=12, fontweight='bold')
        ax2.set_ylabel('%')
        ax2.grid(True, alpha=0.3)
        
        # 3. Returns histogram
        ax3 = fig.add_subplot(gs[2, 0])
        returns = df['pnl'].diff().dropna()
        ax3.hist(returns, bins=30, color='steelblue', alpha=0.7, edgecolor='black')
        ax3.set_title('Returns Distribution', fontsize=10, fontweight='bold')
        ax3.axvline(x=0, color='red', linestyle='--')
        
        # 4. Performance metrics table
        ax4 = fig.add_subplot(gs[2, 1:])
        ax4.axis('off')
        
        # Calculate metrics
        total_pnl = df['pnl'].iloc[-1]
        max_dd = drawdown_pct.min()
        sharpe = (returns.mean() / returns.std()) * np.sqrt(len(returns)) if returns.std() > 0 else 0
        
        metrics_text = f"""
        PERFORMANCE SUMMARY
        
        Total PnL: ${total_pnl:,.2f}
        Max Drawdown: {max_dd:.2f}%
        Sharpe Ratio: {sharpe:.3f}
        
        Total Trades: {len(df)}
        Avg Return: ${returns.mean():.2f}
        Volatility: ${returns.std():.2f}
        """
        
        ax4.text(0.1, 0.5, metrics_text, fontsize=11, 
                verticalalignment='center', family='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.suptitle('Trading System Performance Dashboard', 
                    fontsize=16, fontweight='bold', y=0.98)
        
        output_path = 'results/performance_dashboard.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✓ Dashboard saved: {output_path}")
        plt.close()


def main():
    """Main visualization function."""
    print("=" * 60)
    print("Performance Visualization")
    print("=" * 60 + "\n")
    
    visualizer = PerformanceVisualizer(results_path='results/backtest_results.csv')
    
    # Load data
    df = visualizer.load_results()
    
    # Create all plots
    print("Generating visualizations...\n")
    visualizer.plot_equity_curve(df)
    visualizer.plot_drawdown(df)
    visualizer.plot_returns_distribution(df)
    visualizer.plot_rolling_sharpe(df)
    visualizer.plot_position_analysis(df)
    visualizer.create_summary_dashboard(df)
    
    print("\n" + "=" * 60)
    print("All visualizations complete!")
    print("Check the 'results/' directory for output files.")
    print("=" * 60)


if __name__ == "__main__":
    main()