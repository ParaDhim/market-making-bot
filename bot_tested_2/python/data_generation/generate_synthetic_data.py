"""
Realistic market microstructure data generator - FIXED VERSION
"""

import numpy as np
import pandas as pd
import os


class MarketParams:
    """Market microstructure parameters."""
    def __init__(self):
        self.initial_price = 100.0
        self.drift = 0.0
        self.volatility = 0.5
        self.mean_reversion_speed = 0.1
        self.mean_reversion_level = 100.0
        self.base_spread_bps = 5.0
        self.volume_sensitivity = -0.8
        self.volatility_sensitivity = 1.2
        self.buy_probability = 0.5
        self.flow_persistence = 0.6
        self.trade_intensity = 50
        self.depth_base = 5000
        self.depth_volatility = 0.3


class RealisticMarketDataGenerator:
    def __init__(self, params=None, random_seed=42):
        self.params = params or MarketParams()
        np.random.seed(random_seed)
        
    def generate_price_process(self, n_steps):
        """Generate mean-reverting price process."""
        prices = np.zeros(n_steps)
        prices[0] = self.params.initial_price
        
        dt = 1.0
        
        for i in range(1, n_steps):
            mean_reversion = (
                self.params.mean_reversion_speed * 
                (self.params.mean_reversion_level - prices[i-1]) * dt
            )
            diffusion = self.params.volatility * np.sqrt(dt) * np.random.randn()
            jump = np.random.poisson(0.001) * np.random.randn() * 0.01
            
            prices[i] = prices[i-1] + mean_reversion + diffusion + jump
            prices[i] = max(prices[i], 10)
        
        return prices
    
    def generate_volatility_surface(self, prices, window=50):
        """Generate realized volatility."""
        returns = np.diff(np.log(prices))
        
        # Manual rolling std to avoid pandas issues
        vol = np.zeros(len(prices))
        for i in range(len(prices)):
            start = max(0, i - window)
            vol[i] = np.std(returns[start:i]) if i > 0 else self.params.volatility
        
        vol = np.maximum(vol, self.params.volatility * 0.5)
        return vol
    
    def generate_flow(self, n_steps):
        """Generate trade flow with persistence."""
        flow = np.zeros(n_steps, dtype=int)
        last_flow = np.random.choice([-1, 1])
        
        for i in range(n_steps):
            if np.random.random() < self.params.flow_persistence:
                flow[i] = last_flow
            else:
                flow[i] = np.random.choice([-1, 1])
            
            if np.random.random() < 0.05:
                flow[i] *= -1
            
            last_flow = flow[i]
        
        return flow
    
    def generate_order_book_depth(self, n_steps, volatility):
        """Generate bid/ask volumes responding to volatility."""
        vol_min = volatility.min()
        vol_max = volatility.max()
        vol_normalized = (volatility - vol_min) / (vol_max - vol_min + 1e-8)
        
        base_depth = self.params.depth_base
        
        bid_volumes = base_depth * (1 - vol_normalized * self.params.depth_volatility)
        ask_volumes = base_depth * (1 - vol_normalized * self.params.depth_volatility)
        
        bid_volumes = bid_volumes * (0.8 + 0.4 * np.random.random(n_steps))
        ask_volumes = ask_volumes * (0.8 + 0.4 * np.random.random(n_steps))
        
        bid_volumes = np.maximum(bid_volumes, 100)
        ask_volumes = np.maximum(ask_volumes, 100)
        
        return bid_volumes, ask_volumes
    
    def generate_spread(self, prices, volatility, bid_volumes, ask_volumes):
        """Generate spreads responding to vol and volume."""
        mid_prices = prices
        
        vol_min = volatility.min()
        vol_max = volatility.max()
        vol_norm = (volatility - vol_min) / (vol_max - vol_min + 1e-8)
        
        volume_total = bid_volumes + ask_volumes
        vol_min_size = volume_total.min()
        vol_max_size = volume_total.max()
        vol_size_norm = (volume_total - vol_min_size) / (vol_max_size - vol_min_size + 1e-8)
        
        spreads_bps = (
            self.params.base_spread_bps +
            self.params.volatility_sensitivity * vol_norm * 10 +
            self.params.volume_sensitivity * vol_size_norm * 5
        )
        
        spreads_bps = np.maximum(spreads_bps, 1.0)
        spreads = mid_prices * spreads_bps / 10000
        
        return spreads
    
    def generate_trade_volumes(self, n_steps):
        """Generate log-normal trade sizes."""
        mean_size = 100
        log_mean = np.log(mean_size)
        log_std = 1.0
        
        volumes = np.random.lognormal(log_mean, log_std, n_steps)
        volumes = np.clip(volumes, 10, 5000)
        
        return volumes.astype(int)
    
    def generate_trades(self, n_trades=15000, quotes_per_trade=0.7):
        """Generate realistic trade and quote data."""
        print(f"Generating {n_trades} trades with microstructure...")
        
        # Generate price and dynamics
        prices = self.generate_price_process(n_trades)
        volatility = self.generate_volatility_surface(prices)
        flow = self.generate_flow(n_trades)
        bid_volumes, ask_volumes = self.generate_order_book_depth(n_trades, volatility)
        spreads = self.generate_spread(prices, volatility, bid_volumes, ask_volumes)
        trade_volumes = self.generate_trade_volumes(n_trades)
        
        # Build timestamps
        base_time = pd.Timestamp('2024-01-01').value
        timestamps = base_time + np.arange(n_trades) * int(1e7)
        
        # Calculate bid/ask prices
        mid_prices = prices
        bid_prices = mid_prices - spreads / 2
        ask_prices = mid_prices + spreads / 2
        
        # Trade prices execute at bid/ask based on flow
        trade_prices = np.where(flow == 1, ask_prices, bid_prices)
        
        # ==================== TRADES ====================
        trades_data = pd.DataFrame({
            'timestamp': timestamps,
            'price': trade_prices.astype(np.float64),
            'quantity': trade_volumes,
            'side': np.where(flow == 1, 'buy', 'sell')
        })
        
        print(f"  Trades created: {len(trades_data)}")
        print(f"    Price: {trades_data['price'].min():.4f} - {trades_data['price'].max():.4f}")
        print(f"    Side: {(trades_data['side'] == 'buy').sum()} buys, {(trades_data['side'] == 'sell').sum()} sells")
        
        # ==================== QUOTES ====================
        n_quotes = int(n_trades * quotes_per_trade)
        quote_indices = sorted(np.random.choice(n_trades, n_quotes, replace=False))
        
        quotes_data = pd.DataFrame({
            'timestamp': timestamps[quote_indices],
            'bid_price': bid_prices[quote_indices].astype(np.float64),
            'ask_price': ask_prices[quote_indices].astype(np.float64),
            'bid_volume': bid_volumes[quote_indices].astype(np.float64),
            'ask_volume': ask_volumes[quote_indices].astype(np.float64)
        })
        
        print(f"  Quotes created: {len(quotes_data)}")
        print(f"    Bid prices: {quotes_data['bid_price'].min():.4f} - {quotes_data['bid_price'].max():.4f}")
        print(f"    Ask prices: {quotes_data['ask_price'].min():.4f} - {quotes_data['ask_price'].max():.4f}")
        print(f"    Spreads: {(quotes_data['ask_price'] - quotes_data['bid_price']).mean():.6f} avg")
        
        # ==================== STATISTICS ====================
        print(f"\nData Statistics:")
        print(f"  Price range: ${prices.min():.2f} - ${prices.max():.2f}")
        print(f"  Avg spread (bps): {spreads.mean() * 10000 / prices.mean():.2f}")
        print(f"  Avg bid-ask volume ratio: {(bid_volumes / ask_volumes).mean():.2f}")
        print(f"  Buy ratio: {(flow == 1).sum() / len(flow):.2%}")
        
        return trades_data, quotes_data
    
    def save_data(self, trades_df, quotes_df, output_dir='data/raw'):
        """Save generated data to CSV files."""
        os.makedirs(output_dir, exist_ok=True)
        
        trades_path = os.path.join(output_dir, 'trades.csv')
        quotes_path = os.path.join(output_dir, 'quotes.csv')
        
        # Ensure data types are clean before saving
        trades_df = trades_df.astype({
            'timestamp': 'int64',
            'price': 'float64',
            'quantity': 'int64',
            'side': 'object'
        })
        
        quotes_df = quotes_df.astype({
            'timestamp': 'int64',
            'bid_price': 'float64',
            'ask_price': 'float64',
            'bid_volume': 'float64',
            'ask_volume': 'float64'
        })
        
        trades_df.to_csv(trades_path, index=False)
        quotes_df.to_csv(quotes_path, index=False)
        
        print(f"\n✓ Trades saved to: {trades_path}")
        print(f"  Shape: {trades_df.shape}")
        print(f"✓ Quotes saved to: {quotes_path}")
        print(f"  Shape: {quotes_df.shape}")
        
        # Verify by reading back
        trades_check = pd.read_csv(trades_path)
        quotes_check = pd.read_csv(quotes_path)
        
        print(f"\nVerification:")
        print(f"  Trades read back: {len(trades_check)} rows, {list(trades_check.columns)}")
        print(f"  Quotes read back: {len(quotes_check)} rows, {list(quotes_check.columns)}")
        print(f"  Sample quote bid_price: {quotes_check['bid_price'].iloc[0]:.4f}")
        
        return trades_path, quotes_path


def main():
    print("=" * 70)
    print("REALISTIC MARKET DATA GENERATOR (FIXED)")
    print("=" * 70)
    print()
    
    params = MarketParams()
    generator = RealisticMarketDataGenerator(params, random_seed=42)
    
    trades, quotes = generator.generate_trades(n_trades=15000, quotes_per_trade=0.7)
    generator.save_data(trades, quotes)
    
    print("\n" + "=" * 70)
    print("Data generation complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()