"""
Fixed feature engineering - creates target BEFORE cleaning NaN values.
"""

import pandas as pd
import numpy as np
import ta
from scipy.stats import skew, kurtosis
import os


class ComprehensiveFeatureEngineer:
    def __init__(self, trades_path, quotes_path):
        self.trades_path = trades_path
        self.quotes_path = quotes_path

    def load_data(self):
        """Load and prepare raw data."""
        print("Loading raw data...")
        trades = pd.read_csv(self.trades_path)
        quotes = pd.read_csv(self.quotes_path)
        
        trades['datetime'] = pd.to_datetime(trades['timestamp'], unit='ns')
        quotes['datetime'] = pd.to_datetime(quotes['timestamp'], unit='ns')
        trades = trades.sort_values('timestamp').reset_index(drop=True)
        quotes = quotes.sort_values('timestamp').reset_index(drop=True)
        
        print(f"Loaded {len(trades)} trades and {len(quotes)} quotes")
        return trades, quotes

    def merge_data(self, trades, quotes):
        """Merge trades and quotes."""
        print("Merging trades and quotes...")
        merged = pd.merge_asof(
            trades.sort_values('timestamp'),
            quotes.sort_values('timestamp'),
            on='timestamp',
            direction='backward',
            suffixes=('_trade', '_quote')
        )
        print(f"Merged dataset: {len(merged)} rows")
        return merged

    def calculate_comprehensive_features(self, df):
        """Calculate extensive feature set."""
        print("Calculating comprehensive features...")
        
        f = df.copy()
        feature_dict = {}
        
        # ==================== BASE FEATURES ====================
        print("  > Base features...")
        feature_dict['mid_price'] = (f['bid_price'] + f['ask_price']) / 2
        feature_dict['spread'] = f['ask_price'] - f['bid_price']
        feature_dict['spread_pct'] = (feature_dict['spread'] / feature_dict['mid_price']) * 10000
        feature_dict['obi'] = (f['bid_volume'] - f['ask_volume']) / (f['bid_volume'] + f['ask_volume'])
        feature_dict['book_depth'] = f['bid_volume'] + f['ask_volume']
        
        # ==================== FLOW & ORDER BOOK ====================
        print("  > Flow and order book features...")
        
        feature_dict['buy_signal'] = (f['side'] == 'buy').astype(int)
        feature_dict['sell_signal'] = (f['side'] == 'sell').astype(int)
        
        for window in [5, 10, 20, 50]:
            buy_vol = (feature_dict['buy_signal'] * f['quantity']).rolling(window).sum()
            sell_vol = (feature_dict['sell_signal'] * f['quantity']).rolling(window).sum()
            feature_dict[f'buy_volume_{window}'] = buy_vol
            feature_dict[f'sell_volume_{window}'] = sell_vol
            feature_dict[f'flow_imbalance_{window}'] = (buy_vol - sell_vol) / (buy_vol + sell_vol + 1e-10)
            feature_dict[f'net_flow_{window}'] = buy_vol - sell_vol
        
        feature_dict['volume'] = f['quantity']
        feature_dict['volume_ma_10'] = f['quantity'].rolling(10).mean()
        feature_dict['volume_ma_50'] = f['quantity'].rolling(50).mean()
        feature_dict['volume_acceleration'] = feature_dict['volume_ma_10'] - feature_dict['volume_ma_50']
        
        # ==================== VOLATILITY & PRICE ACTION ====================
        print("  > Volatility and price action features...")
        
        for window in [10, 20, 50, 100]:
            feature_dict[f'volatility_{window}'] = f['price'].rolling(window).std()
            feature_dict[f'log_return_{window}'] = np.log(f['price'] / f['price'].shift(window))
            high = f['price'].rolling(window).max()
            low = f['price'].rolling(window).min()
            feature_dict[f'high_{window}'] = high
            feature_dict[f'low_{window}'] = low
            feature_dict[f'price_range_{window}'] = high - low
            feature_dict[f'price_position_{window}'] = (f['price'] - low) / (high - low + 1e-10)
        
        for window in [5, 10, 20]:
            mean = f['price'].rolling(window).mean()
            std = f['price'].rolling(window).std()
            feature_dict[f'price_zscore_{window}'] = (f['price'] - mean) / (std + 1e-10)
            feature_dict[f'extreme_move_{window}'] = (np.abs(feature_dict[f'price_zscore_{window}']) > 1.5).astype(int)
        
        # ==================== MARKET MICROSTRUCTURE ====================
        print("  > Market microstructure features...")
        
        feature_dict['spread_change'] = feature_dict['spread'].diff()
        feature_dict['spread_ma_10'] = feature_dict['spread'].rolling(10).mean()
        feature_dict['spread_ma_50'] = feature_dict['spread'].rolling(50).mean()
        feature_dict['spread_expansion'] = (feature_dict['spread'] > feature_dict['spread_ma_50']).astype(int)
        
        feature_dict['obi_change'] = feature_dict['obi'].diff()
        feature_dict['obi_ma_10'] = feature_dict['obi'].rolling(10).mean()
        feature_dict['obi_extreme'] = (np.abs(feature_dict['obi']) > 0.5).astype(int)
        
        feature_dict['bid_ask_ratio'] = f['bid_volume'] / (f['ask_volume'] + 1e-10)
        feature_dict['bid_ask_ratio_ma'] = feature_dict['bid_ask_ratio'].rolling(10).mean()
        feature_dict['thin_book'] = (feature_dict['book_depth'] < feature_dict['book_depth'].quantile(0.25)).astype(int)
        
        feature_dict['price_to_bid'] = (f['price'] - f['bid_price']) / (feature_dict['spread'] + 1e-10)
        feature_dict['price_to_mid'] = (f['price'] - feature_dict['mid_price']) / feature_dict['mid_price']
        
        # ==================== MOMENTUM & TREND ====================
        print("  > Momentum and trend features...")
        
        for window in [5, 10, 20, 50]:
            feature_dict[f'momentum_{window}'] = f['price'].diff(window)
            feature_dict[f'price_change_pct_{window}'] = f['price'].pct_change(window, fill_method=None)
        
        # ==================== TECHNICAL INDICATORS ====================
        print("  > Technical indicators...")
        
        try:
            feature_dict['rsi_14'] = ta.momentum.RSIIndicator(close=f['price'], window=14).rsi()
        except:
            feature_dict['rsi_14'] = np.nan
        
        try:
            macd = ta.trend.MACD(close=f['price'])
            feature_dict['macd'] = macd.macd()
            feature_dict['macd_signal'] = macd.macd_signal()
            feature_dict['macd_diff'] = macd.macd_diff()
        except:
            feature_dict['macd'] = np.nan
            feature_dict['macd_signal'] = np.nan
            feature_dict['macd_diff'] = np.nan
        
        # ==================== TIME-BASED FEATURES ====================
        print("  > Time-based features...")
        
        feature_dict['hour'] = f['datetime_trade'].dt.hour
        feature_dict['minute'] = f['datetime_trade'].dt.minute
        
        # ==================== CONVERT ALL AT ONCE ====================
        print("  > Converting to DataFrame...")
        features_df = pd.DataFrame(feature_dict)
        result = pd.concat([f, features_df], axis=1)
        
        print(f"Total features created: {len(result.columns)}")
        return result

    def create_target(self, df, forward_window=20, percentile_threshold=0.5):
        """
        Create target BEFORE cleaning NaN.
        Use rows that have valid future data.
        """
        print(f"Creating target (forward_window={forward_window})...")
        
        # Only work with rows that have valid future data
        n = len(df)
        valid_idx = np.arange(0, n - forward_window)
        
        df_target = df.iloc[valid_idx].copy()
        
        # Shift to get future prices
        future_mid = df['mid_price'].iloc[valid_idx + forward_window].values
        current_mid = df_target['mid_price'].values
        
        df_target['future_mid'] = future_mid
        df_target['future_return'] = (future_mid - current_mid) / current_mid
        
        # Create binary target using percentile
        threshold = df_target['future_return'].quantile(percentile_threshold)
        df_target['target'] = (df_target['future_return'] > threshold).astype(int)
        
        print(f"Valid rows with future data: {len(df_target)}")
        print(f"Return threshold (p{percentile_threshold*100}): {threshold:.6f}")
        print(f"Return range: {df_target['future_return'].min():.6f} to {df_target['future_return'].max():.6f}")
        print(f"Target distribution: {df_target['target'].value_counts().to_dict()}")
        print(f"Up ratio: {df_target['target'].mean():.2%}")
        
        return df_target

    def clean_data(self, df):
        """Remove NaN and infinite values."""
        print("\nCleaning data...")
        initial = len(df)
        
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.dropna()
        
        final = len(df)
        removed = initial - final
        print(f"Removed {removed} rows with NaN/inf. Final: {final} rows")
        
        if final < 100:
            print("  WARNING: Very few rows remaining after cleaning!")
        
        return df

    def save_features(self, df, output_path='data/processed/features_comprehensive.csv'):
        """Save features."""
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        
        df.to_csv(output_path, index=False)
        print(f"Saved to: {output_path}")
        print(f"Shape: {df.shape}")
        print(f"Columns: {list(df.columns)[:10]}... ({len(df.columns)} total)")
        
        return output_path


def main():
    print("=" * 80)
    print("COMPREHENSIVE FEATURE ENGINEERING PIPELINE (FIXED)")
    print("=" * 80)
    print()
    
    engineer = ComprehensiveFeatureEngineer(
        trades_path='data/raw/trades.csv',
        quotes_path='data/raw/quotes.csv'
    )
    
    trades, quotes = engineer.load_data()
    merged = engineer.merge_data(trades, quotes)
    features = engineer.calculate_comprehensive_features(merged)
    
    # FIXED: Create target with valid rows BEFORE cleaning
    features = engineer.create_target(features, forward_window=20, percentile_threshold=0.5)
    
    # THEN clean NaN values
    features = engineer.clean_data(features)
    
    # Save
    engineer.save_features(features)
    
    print("\n" + "=" * 80)
    print("Feature engineering complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()