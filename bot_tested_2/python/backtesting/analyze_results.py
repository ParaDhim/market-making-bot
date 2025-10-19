"""
Analyze backtest results and calculate performance metrics.
"""

import pandas as pd
import numpy as np
import os


class PerformanceAnalyzer:
    def __init__(self, results_path='results/backtest_results.csv'):
        self.results_path = results_path
        
    def load_results(self):
        """Load backtest results."""
        print("Loading backtest results...")
        df = pd.read_csv(self.results_path)
        print(f"Loaded {len(df)} records")
        return df
    
    def calculate_metrics(self, df):
        """Calculate comprehensive performance metrics."""
        print("\n" + "=" * 60)
        print("PERFORMANCE METRICS")
        print("=" * 60)
        
        metrics = {}
        
        # Basic PnL metrics
        metrics['total_pnl'] = df['pnl'].iloc[-1]
        metrics['total_return'] = (df['pnl'].iloc[-1] / df['pnl'].iloc[0] - 1) * 100 if df['pnl'].iloc[0] != 0 else 0
        
        print(f"\n📊 PnL Summary:")
        print(f"   Total PnL: ${metrics['total_pnl']:,.2f}")
        print(f"   Total Return: {metrics['total_return']:.2f}%")
        
        # Trade statistics
        if 'fill_price' in df.columns:
            trades = df[df['fill_price'].notna()]
            metrics['num_trades'] = len(trades)
            metrics['avg_trade_size'] = trades['quantity'].mean() if len(trades) > 0 else 0
            
            print(f"\n📈 Trading Activity:")
            print(f"   Total Trades: {metrics['num_trades']}")
            print(f"   Avg Trade Size: {metrics['avg_trade_size']:.4f}")
        
        # Risk metrics
        returns = df['pnl'].diff().dropna()
        
        # Sharpe Ratio (annualized)
        if len(returns) > 0 and returns.std() > 0:
            # Assuming each row is a trade/update
            mean_return = returns.mean()
            std_return = returns.std()
            
            # Annualization factor (assuming ~252 trading days, ~6.5 hours, ~23400 seconds)
            # Adjust based on your data frequency
            annualization_factor = np.sqrt(252 * 6.5 * 3600)  # Approximate
            
            metrics['sharpe_ratio'] = (mean_return / std_return) * annualization_factor if std_return > 0 else 0
        else:
            metrics['sharpe_ratio'] = 0
        
        # Sortino Ratio (downside deviation)
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0 and downside_returns.std() > 0:
            metrics['sortino_ratio'] = (returns.mean() / downside_returns.std()) * np.sqrt(252 * 6.5 * 3600)
        else:
            metrics['sortino_ratio'] = 0
        
        # Maximum Drawdown
        cumulative = df['pnl']
        running_max = cumulative.expanding().max()
        drawdown = cumulative - running_max
        metrics['max_drawdown'] = drawdown.min()
        metrics['max_drawdown_pct'] = (drawdown.min() / running_max.max() * 100) if running_max.max() > 0 else 0
        
        print(f"\n⚠️  Risk Metrics:")
        print(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.3f}")
        print(f"   Sortino Ratio: {metrics['sortino_ratio']:.3f}")
        print(f"   Max Drawdown: ${metrics['max_drawdown']:,.2f} ({metrics['max_drawdown_pct']:.2f}%)")
        
        # Win rate (if we have trade-level PnL)
        if 'trade_pnl' in df.columns:
            trades_pnl = df[df['trade_pnl'].notna()]['trade_pnl']
            if len(trades_pnl) > 0:
                metrics['win_rate'] = (trades_pnl > 0).sum() / len(trades_pnl) * 100
                metrics['avg_win'] = trades_pnl[trades_pnl > 0].mean() if (trades_pnl > 0).any() else 0
                metrics['avg_loss'] = trades_pnl[trades_pnl < 0].mean() if (trades_pnl < 0).any() else 0
                metrics['profit_factor'] = abs(trades_pnl[trades_pnl > 0].sum() / trades_pnl[trades_pnl < 0].sum()) if (trades_pnl < 0).any() else 0
                
                print(f"\n💰 Trade Performance:")
                print(f"   Win Rate: {metrics['win_rate']:.2f}%")
                print(f"   Avg Win: ${metrics['avg_win']:.2f}")
                print(f"   Avg Loss: ${metrics['avg_loss']:.2f}")
                print(f"   Profit Factor: {metrics['profit_factor']:.3f}")
        
        # Volatility
        metrics['pnl_volatility'] = returns.std()
        
        print(f"\n📉 Volatility:")
        print(f"   PnL Volatility: ${metrics['pnl_volatility']:.2f}")
        
        return metrics
    
    def save_metrics(self, metrics, output_path='results/performance_metrics.txt'):
        """Save metrics to file."""
        with open(output_path, 'w') as f:
            f.write("BACKTEST PERFORMANCE METRICS\n")
            f.write("=" * 60 + "\n\n")
            
            for key, value in metrics.items():
                f.write(f"{key}: {value}\n")
        
        print(f"\n✓ Metrics saved to: {output_path}")
    
    def generate_summary_report(self, df, metrics):
        """Generate a text summary report."""
        report_path = 'results/summary_report.txt'
        
        with open(report_path, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write("TRADING SYSTEM BACKTEST REPORT\n")
            f.write("=" * 70 + "\n\n")
            
            f.write("EXECUTIVE SUMMARY\n")
            f.write("-" * 70 + "\n")
            f.write(f"Total PnL: ${metrics['total_pnl']:,.2f}\n")
            f.write(f"Total Return: {metrics['total_return']:.2f}%\n")
            f.write(f"Sharpe Ratio: {metrics['sharpe_ratio']:.3f}\n")
            f.write(f"Max Drawdown: ${metrics['max_drawdown']:,.2f} ({metrics['max_drawdown_pct']:.2f}%)\n\n")
            
            f.write("DETAILED METRICS\n")
            f.write("-" * 70 + "\n")
            for key, value in metrics.items():
                f.write(f"{key:30s}: {value}\n")
            
            f.write("\n" + "=" * 70 + "\n")
        
        print(f"✓ Summary report saved to: {report_path}")


def main():
    """Main analysis function."""
    print("=" * 60)
    print("Backtest Performance Analyzer")
    print("=" * 60)
    
    analyzer = PerformanceAnalyzer(results_path='results/backtest_results.csv')
    
    # Load results
    df = analyzer.load_results()
    
    # Calculate metrics
    metrics = analyzer.calculate_metrics(df)
    
    # Save metrics
    analyzer.save_metrics(metrics)
    
    # Generate report
    analyzer.generate_summary_report(df, metrics)
    
    print("\n" + "=" * 60)
    print("Analysis complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()