# python_ml/01_generate_sim_data.py
import pandas as pd
import numpy as np
import os

def generate_market_data(num_rows=50000000):
    """Generates simulated tick-by-tick market data (trades and quotes)."""
    print("Generating simulated market data...")
    
    # Create data directory if it doesn't exist
    if not os.path.exists('data'):
        os.makedirs('data')

    # Base parameters
    start_price = 100.0
    drift = 0.00005
    volatility = 0.005
    
    # Generate mid-price with a random walk
    price_changes = np.random.normal(loc=drift, scale=volatility, size=num_rows)
    mid_price = start_price + np.cumsum(price_changes)
    
    # Generate Quotes
    spread = np.random.uniform(0.01, 0.05, size=num_rows)
    bid_price = mid_price - spread / 2
    ask_price = mid_price + spread / 2
    bid_qty = np.random.randint(1, 10, size=num_rows)
    ask_qty = np.random.randint(1, 10, size=num_rows)
    
    # Generate Trades
    trade_price = mid_price + np.random.normal(0, volatility, size=num_rows)
    trade_qty = np.random.poisson(1.5, size=num_rows)
    side = np.random.choice(['buy', 'sell'], size=num_rows)
    
    timestamps = pd.to_datetime(np.arange(num_rows), unit='s', origin=pd.Timestamp('2025-10-15'))
    
    # Create DataFrames
    quotes_df = pd.DataFrame({
        'timestamp': timestamps,
        'type': 'QUOTE',
        'bid_price': bid_price,
        'bid_qty': bid_qty,
        'ask_price': ask_price,
        'ask_qty': ask_qty
    })
    
    trades_df = pd.DataFrame({
        'timestamp': timestamps,
        'type': 'TRADE',
        'price': trade_price,
        'qty': trade_qty,
        'side': side
    })
    
    # Save to CSV
    quotes_df.to_csv('data/raw_quotes.csv', index=False)
    trades_df.to_csv('data/raw_trades.csv', index=False)
    
    print(f"Successfully generated {num_rows} rows of data.")
    print("Files created: data/raw_quotes.csv, data/raw_trades.csv")

if __name__ == '__main__':
    generate_market_data()