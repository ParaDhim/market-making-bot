"""
Diagnostic script to understand your data and identify issues.
Run this BEFORE feature engineering.
"""

import pandas as pd
import numpy as np
from datetime import datetime

def diagnose_raw_data():
    """Diagnose raw trades and quotes data."""
    print("=" * 70)
    print("RAW DATA DIAGNOSTICS")
    print("=" * 70)
    
    # Load raw data
    trades = pd.read_csv('data/raw/trades.csv')
    quotes = pd.read_csv('data/raw/quotes.csv')
    
    print("\n1. TRADES DATA")
    print(f"   Shape: {trades.shape}")
    print(f"   Columns: {list(trades.columns)}")
    print(f"   Time span: {trades['timestamp'].min()} to {trades['timestamp'].max()}")
    print(f"   Sample:\n{trades.head()}")
    
    # Analyze price movement
    if 'price' in trades.columns:
        print(f"\n   Price statistics:")
        print(f"     Min: {trades['price'].min()}")
        print(f"     Max: {trades['price'].max()}")
        print(f"     Mean: {trades['price'].mean():.6f}")
        print(f"     Std: {trades['price'].std():.6f}")
        
        # Calculate returns
        returns = trades['price'].pct_change().dropna()
        print(f"\n   Price returns (1-tick):")
        print(f"     Mean: {returns.mean():.8f}")
        print(f"     Std: {returns.std():.8f}")
        print(f"     Min: {returns.min():.8f}")
        print(f"     Max: {returns.max():.8f}")
        print(f"     % > 0: {(returns > 0).mean():.2%}")
        print(f"     % < 0: {(returns < 0).mean():.2%}")
    
    print("\n2. QUOTES DATA")
    print(f"   Shape: {quotes.shape}")
    print(f"   Columns: {list(quotes.columns)}")
    print(f"   Sample:\n{quotes.head()}")
    
    # Analyze spreads
    if 'bid_price' in quotes.columns and 'ask_price' in quotes.columns:
        spreads = quotes['ask_price'] - quotes['bid_price']
        print(f"\n   Spread statistics:")
        print(f"     Mean: {spreads.mean():.8f}")
        print(f"     Std: {spreads.std():.8f}")
        print(f"     Min: {spreads.min():.8f}")
        print(f"     Max: {spreads.max():.8f}")
    
    print("\n" + "=" * 70)

def diagnose_features():
    """Diagnose processed features."""
    print("\n" + "=" * 70)
    print("FEATURE DIAGNOSTICS")
    print("=" * 70)
    
    try:
        features = pd.read_csv('data/processed/features.csv')
    except FileNotFoundError:
        print("Features file not found. Run feature engineering first.")
        return
    
    print(f"\nShape: {features.shape}")
    print(f"Columns: {len(features.columns)}")
    
    # Target analysis
    if 'target' in features.columns:
        print(f"\nTarget distribution:")
        print(features['target'].value_counts().sort_index())
        print(f"Target unique values: {features['target'].unique()}")
    
    # Future return analysis
    if 'future_return' in features.columns:
        print(f"\nFuture return statistics:")
        print(f"  Mean: {features['future_return'].mean():.8f}")
        print(f"  Std: {features['future_return'].std():.8f}")
        print(f"  Min: {features['future_return'].min():.8f}")
        print(f"  Max: {features['future_return'].max():.8f}")
        print(f"  NaN count: {features['future_return'].isna().sum()}")
    
    # Feature statistics
    exclude = ['timestamp', 'datetime_trade', 'datetime_quote', 'side', 
               'target', 'future_mid', 'future_return']
    feature_cols = [c for c in features.columns if c not in exclude]
    
    print(f"\nUsable features: {len(feature_cols)}")
    print(f"\nFeature NaN percentages:")
    nan_pcts = (features[feature_cols].isna().sum() / len(features) * 100).sort_values(ascending=False)
    print(nan_pcts[nan_pcts > 0].head(10))
    
    print(f"\nFeature variance:")
    variances = features[feature_cols].var().sort_values(ascending=False)
    print(variances.head(10))
    print(f"Zero-variance features: {(variances == 0).sum()}")
    
    # Check for data leakage: correlation between features and target
    if 'target' in features.columns:
        print(f"\nFeature-target correlations (top 10):")
        correlations = features[feature_cols + ['target']].corr()['target'].drop('target').abs().sort_values(ascending=False)
        print(correlations.head(10))
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    diagnose_raw_data()
    diagnose_features()