# python_ml/02_feature_engineering.py
"""
Reads raw market data and engineers a rich set of features for predicting
short-term price movements.
"""
import pandas as pd
import numpy as np
import logging

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

def create_features(raw_quotes_path='data/raw_quotes.csv', output_path='data/features.csv'):
    """Reads raw data and engineers features for the ML model."""
    logging.info("Starting feature engineering...")
    
    try:
        df = pd.read_csv(raw_quotes_path, parse_dates=['timestamp'])
    except FileNotFoundError:
        logging.error(f"Error: Raw data file not found at '{raw_quotes_path}'")
        raise

    # --- Basic Feature Creation ---
    df['mid_price'] = (df['bid_price'] + df['ask_price']) / 2
    df['spread'] = df['ask_price'] - df['bid_price']
    df['obi'] = (df['bid_qty'] - df['ask_qty']) / (df['bid_qty'] + df['ask_qty'])
    
    # --- Time-Based Features (Moving Averages) ---
    # These features help the model understand recent trends.
    windows = [10, 50, 200]
    for window in windows:
        # Simple Moving Average
        df[f'sma_{window}'] = df['mid_price'].rolling(window=window).mean()
        # Exponential Moving Average (gives more weight to recent prices)
        df[f'ema_{window}'] = df['mid_price'].ewm(span=window, adjust=False).mean()
        # Momentum (price change over the window)
        df[f'momentum_{window}'] = df['mid_price'].diff(window)

    # --- Volatility Features ---
    # These features help the model understand how turbulent the market is.
    for window in windows:
        # Rolling Standard Deviation (a measure of volatility)
        rolling_std = df['mid_price'].rolling(window=window).std()
        # Bollinger Bands
        df[f'bollinger_upper_{window}'] = df[f'sma_{window}'] + (rolling_std * 2)
        df[f'bollinger_lower_{window}'] = df[f'sma_{window}'] - (rolling_std * 2)

    # --- Target Variable Creation (Refined Approach) ---
    logging.info("Creating a more robust target variable...")
    future_steps = 10
    # Calculate future returns as a percentage change
    df['future_return'] = (df['mid_price'].shift(-future_steps) - df['mid_price']) / df['mid_price']
    
    # Define a threshold to ignore insignificant noise.
    # We only want to predict meaningful moves up or down.
    threshold = 0.0001 # 0.01% price change
    
    df['price_direction'] = 0 # Default to STAY
    df.loc[df['future_return'] > threshold, 'price_direction'] = 1  # UP
    df.loc[df['future_return'] < -threshold, 'price_direction'] = -1 # DOWN
    
    # Now, drop all the rows where the movement was just noise (within the threshold)
    # This focuses the model on predicting significant changes.
    df = df[df['price_direction'] != 0].copy()
    
    # --- Finalize Feature Set ---
    # Drop rows with NaN values created by rolling windows
    df.dropna(inplace=True)
    
    # Select the columns to be used as features
    feature_columns = [
        'spread', 'obi', 'mid_price',
        'sma_10', 'ema_10', 'momentum_10', 'bollinger_upper_10', 'bollinger_lower_10',
        'sma_50', 'ema_50', 'momentum_50', 'bollinger_upper_50', 'bollinger_lower_50',
        'sma_200', 'ema_200', 'momentum_200', 'bollinger_upper_200', 'bollinger_lower_200',
    ]
    
    final_df = df[feature_columns + ['price_direction']]
    
    final_df.to_csv(output_path, index=False)
    logging.info(f"Feature engineering complete. {len(final_df)} samples saved to '{output_path}'")
    logging.info(f"Features created: {feature_columns}")

if __name__ == '__main__':
    create_features()