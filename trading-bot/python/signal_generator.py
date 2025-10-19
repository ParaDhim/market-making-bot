import pandas as pd
import numpy as np
import joblib
from pathlib import Path
import time

class SignalGenerator:
    def __init__(self, model_path="results/trained_model.joblib"):
        """Load trained model and generate trading signals"""
        model_data = joblib.load(model_path)
        self.model = model_data['model']
        self.feature_names = model_data['feature_names']
        print(f"Loaded model with {len(self.feature_names)} features")
    
    def calculate_features(self, quotes_window):
        """Calculate features from recent quotes"""
        if len(quotes_window) < 50:
            return None
        
        df = quotes_window.copy()
        
        # Calculate mid price
        df['mid_price'] = (df['best_bid'] + df['best_ask']) / 2
        
        # Feature 1: Order Book Imbalance
        obi = df['bid_volume'].iloc[-1] / (df['bid_volume'].iloc[-1] + df['ask_volume'].iloc[-1] + 1e-10)
        
        # Feature 2: Spread in basis points
        spread = df['best_ask'].iloc[-1] - df['best_bid'].iloc[-1]
        spread_bps = (spread / df['mid_price'].iloc[-1]) * 10000
        
        # Feature 3: Price momentum
        price_change_5 = df['mid_price'].pct_change(5).iloc[-1]
        price_change_10 = df['mid_price'].pct_change(10).iloc[-1]
        price_change_20 = df['mid_price'].pct_change(20).iloc[-1]
        price_change_50 = df['mid_price'].pct_change(50).iloc[-1]
        
        # Feature 4: Volatility
        price_std_5 = df['mid_price'].rolling(5).std().iloc[-1]
        price_std_10 = df['mid_price'].rolling(10).std().iloc[-1]
        price_std_20 = df['mid_price'].rolling(20).std().iloc[-1]
        price_std_50 = df['mid_price'].rolling(50).std().iloc[-1]
        
        # Feature 5: Price velocity and acceleration
        price_velocity = df['mid_price'].diff().iloc[-1]
        price_acceleration = df['mid_price'].diff().diff().iloc[-1]
        
        # Feature 6: Bid-Ask pressure
        bid_pressure = df['bid_volume'].rolling(10).mean().iloc[-1]
        ask_pressure = df['ask_volume'].rolling(10).mean().iloc[-1]
        pressure_ratio = bid_pressure / (ask_pressure + 1e-10)
        
        features = {
            'obi': obi,
            'spread_bps': spread_bps,
            'pressure_ratio': pressure_ratio,
            'price_change_5': price_change_5,
            'price_change_10': price_change_10,
            'price_change_20': price_change_20,
            'price_change_50': price_change_50,
            'price_std_5': price_std_5,
            'price_std_10': price_std_10,
            'price_std_20': price_std_20,
            'price_std_50': price_std_50,
            'price_velocity': price_velocity,
            'price_acceleration': price_acceleration,
            'bid_pressure': bid_pressure,
            'ask_pressure': ask_pressure
        }
        
        # Convert to array in correct order
        feature_array = np.array([features[name] for name in self.feature_names]).reshape(1, -1)
        
        # Handle NaN values
        if np.any(np.isnan(feature_array)):
            return None
        
        return feature_array
    
    def generate_signals(self, quotes_file, output_file="results/signals.txt"):
        """Generate signals from quotes data"""
        print(f"Reading quotes from {quotes_file}")
        quotes = pd.read_csv(quotes_file)
        quotes['timestamp'] = pd.to_datetime(quotes['timestamp'])
        
        print(f"Generating signals for {len(quotes)} quotes...")
        
        signals = []
        window_size = 100
        
        with open(output_file, 'w') as f:
            for i in range(window_size, len(quotes)):
                # Get window of recent quotes
                window = quotes.iloc[i-window_size:i]
                
                # Calculate features
                features = self.calculate_features(window)
                
                if features is None:
                    signal = 0  # Neutral if can't calculate features
                else:
                    # Predict using model
                    prediction = self.model.predict(features)[0]
                    signal = int(prediction)  # -1, 0, or 1
                
                signals.append(signal)
                f.write(f"{signal}\n")
                
                if i % 1000 == 0:
                    print(f"Generated {i-window_size} signals...")
        
        print(f"\nGenerated {len(signals)} signals")
        print(f"Signal distribution:")
        signal_counts = pd.Series(signals).value_counts().sort_index()
        for sig, count in signal_counts.items():
            print(f"  {sig:2d}: {count:6d} ({count/len(signals)*100:.1f}%)")
        
        print(f"\nSignals saved to {output_file}")

def main():
    import glob
    
    # Find most recent quotes file
    quotes_files = sorted(glob.glob("data/raw/quotes_*.csv"))
    if not quotes_files:
        print("Error: No quotes files found. Run collect_data.py first.")
        return
    
    quotes_file = quotes_files[-1]
    print(f"Using quotes file: {quotes_file}")
    
    # Create symlink for C++ engine
    Path("data/raw/quotes_latest.csv").unlink(missing_ok=True)
    Path("data/raw/quotes_latest.csv").symlink_to(Path(quotes_file).name)
    
    trades_file = quotes_file.replace("quotes_", "trades_")
    if Path(trades_file).exists():
        Path("data/raw/trades_latest.csv").unlink(missing_ok=True)
        Path("data/raw/trades_latest.csv").symlink_to(Path(trades_file).name)
    
    # Generate signals
    generator = SignalGenerator()
    generator.generate_signals(quotes_file)

if __name__ == "__main__":
    main()