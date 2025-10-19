import pandas as pd
import numpy as np
from pathlib import Path
import glob

class FeatureEngineer:
    def __init__(self):
        self.features = None
        self.labels = None
    
    def load_data(self):
        """Load the most recent trades and quotes data"""
        trades_files = sorted(glob.glob("data/raw/trades_*.csv"))
        quotes_files = sorted(glob.glob("data/raw/quotes_*.csv"))
        
        if not trades_files or not quotes_files:
            raise FileNotFoundError("No data files found. Run collect_data.py first.")
        
        # Load most recent files
        self.trades = pd.read_csv(trades_files[-1])
        self.quotes = pd.read_csv(quotes_files[-1])
        
        # Convert timestamps
        self.trades['timestamp'] = pd.to_datetime(self.trades['timestamp'])
        self.quotes['timestamp'] = pd.to_datetime(self.quotes['timestamp'])
        
        print(f"Loaded {len(self.trades)} trades and {len(self.quotes)} quotes")
    
    def create_features(self):
        """Create ML features from market data"""
        df = self.quotes.copy()
        
        # Calculate mid price
        df['mid_price'] = (df['best_bid'] + df['best_ask']) / 2
        
        # Feature 1: Order Book Imbalance (OBI)
        df['obi'] = df['bid_volume'] / (df['bid_volume'] + df['ask_volume'] + 1e-10)
        
        # Feature 2: Spread
        df['spread'] = df['best_ask'] - df['best_bid']
        df['spread_bps'] = (df['spread'] / df['mid_price']) * 10000
        
        # Feature 3: Price changes (momentum)
        for window in [5, 10, 20, 50]:
            df[f'price_change_{window}'] = df['mid_price'].pct_change(window)
            df[f'price_std_{window}'] = df['mid_price'].rolling(window).std()
        
        # Feature 4: Volume-weighted metrics
        df['vwap_5'] = (df['mid_price'] * (df['bid_volume'] + df['ask_volume'])).rolling(5).sum() / \
                       (df['bid_volume'] + df['ask_volume']).rolling(5).sum()
        
        # Feature 5: Bid-Ask pressure
        df['bid_pressure'] = df['bid_volume'].rolling(10).mean()
        df['ask_pressure'] = df['ask_volume'].rolling(10).mean()
        df['pressure_ratio'] = df['bid_pressure'] / (df['ask_pressure'] + 1e-10)
        
        # Feature 6: Price acceleration
        df['price_velocity'] = df['mid_price'].diff()
        df['price_acceleration'] = df['price_velocity'].diff()
        
        # Target: Future price movement (predict 10 ticks ahead)
        look_ahead = 10
        df['future_mid'] = df['mid_price'].shift(-look_ahead)
        df['return'] = (df['future_mid'] - df['mid_price']) / df['mid_price']
        
        # Create binary labels: 1 if price goes up, -1 if down, 0 if neutral
        threshold = df['return'].std() * 0.3  # 30% of std dev
        df['label'] = 0
        df.loc[df['return'] > threshold, 'label'] = 1
        df.loc[df['return'] < -threshold, 'label'] = -1
        
        # Remove NaN values
        df = df.dropna()
        
        # Select feature columns
        feature_cols = [
            'obi', 'spread_bps', 'pressure_ratio',
            'price_change_5', 'price_change_10', 'price_change_20', 'price_change_50',
            'price_std_5', 'price_std_10', 'price_std_20', 'price_std_50',
            'price_velocity', 'price_acceleration',
            'bid_pressure', 'ask_pressure'
        ]
        
        self.features = df[feature_cols].copy()
        self.labels = df['label'].copy()
        self.timestamps = df['timestamp'].copy()
        self.mid_prices = df['mid_price'].copy()
        
        print(f"\nCreated {len(feature_cols)} features")
        print(f"Samples: {len(self.features)}")
        print(f"Label distribution:\n{self.labels.value_counts()}")
    
    def save_processed_data(self):
        """Save processed features for training"""
        Path("data/processed").mkdir(parents=True, exist_ok=True)
        
        # Save features and labels
        feature_df = self.features.copy()
        feature_df['label'] = self.labels
        feature_df['timestamp'] = self.timestamps.values
        feature_df['mid_price'] = self.mid_prices.values
        
        output_file = "data/processed/features.csv"
        feature_df.to_csv(output_file, index=False)
        print(f"\nSaved processed features to {output_file}")

def main():
    print("=== Feature Engineering Pipeline ===\n")
    
    engineer = FeatureEngineer()
    engineer.load_data()
    engineer.create_features()
    engineer.save_processed_data()
    
    print("\nFeature engineering complete!")

if __name__ == "__main__":
    main()