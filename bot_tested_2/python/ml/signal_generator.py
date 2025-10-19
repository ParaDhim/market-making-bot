"""
Simple file-based signal generator for debugging.
Writes signals to a file that C++ reads.
With bidirectional connection handshaking - FIXED VERSION.
"""

import pandas as pd
import numpy as np
import joblib
import os
import time
import sys
from collections import deque


class ConnectionMonitor:
    def __init__(self, cpp_status_file, python_status_file):
        self.cpp_status_file = cpp_status_file
        self.python_status_file = python_status_file
        os.makedirs(os.path.dirname(python_status_file) or '.', exist_ok=True)
    
    def announce_python_ready(self):
        self.write_status_file(self.python_status_file, "PYTHON_RUNNING")
        print("[CONNECTION] Python process: RUNNING (status file written)")
    
    def announce_python_sending(self):
        self.write_status_file(self.python_status_file, "PYTHON_SENDING")
        print("[CONNECTION] Python process: SENDING signals")
    
    def announce_python_shutdown(self):
        self.write_status_file(self.python_status_file, "PYTHON_SHUTDOWN")
        print("\n[CONNECTION] Python process: SHUTDOWN (status updated)")
    
    def is_cpp_ready(self):
        """Check if C++ is ready to receive signals"""
        status = self.read_status_file(self.cpp_status_file)
        return status in ["CPP_READY", "CPP_PROCESSING"]
    
    def is_cpp_connected(self):
        """Check if C++ status file exists AND contains valid status"""
        if not os.path.exists(self.cpp_status_file):
            return False
        status = self.read_status_file(self.cpp_status_file)
        return status in ["CPP_READY", "CPP_PROCESSING"]
    
    def write_status_file(self, filepath, status):
        try:
            with open(filepath, 'w') as f:
                f.write(status + '\n')
                f.flush()
                os.fsync(f.fileno())
        except Exception as e:
            print(f"Warning: Could not write status file {filepath}: {e}", file=sys.stderr)
    
    def read_status_file(self, filepath):
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    return f.read().strip()
        except Exception as e:
            print(f"Warning: Could not read status file {filepath}: {e}", file=sys.stderr)
        return ""


class SignalGenerator:
    def __init__(self, model_path='models/price_direction_model.pkl',
                 data_path='data/raw/quotes.csv',
                 signal_file='ipc/ml_signals.txt',
                 cpp_status_file='ipc/cpp_status.txt',
                 python_status_file='ipc/python_status.txt'):
        
        print("Initializing Signal Generator (File-Based with IPC Handshake)...")
        
        # Load trained model
        print(f"Loading model from: {model_path}")
        try:
            model_data = joblib.load(model_path)
            self.model = model_data['model']
            self.feature_names = model_data['feature_names']
            print(f"✓ Model loaded with {len(self.feature_names)} features")
        except Exception as e:
            print(f"⚠ Using dummy model: {e}")
            self.model = None
            self.feature_names = ['mid_price', 'spread', 'spread_bps', 'obi', 'weighted_mid',
                                 'price_return_10', 'price_return_50', 'price_return_100',
                                 'volatility_10', 'volatility_50', 'volatility_100',
                                 'book_depth', 'microprice']
        
        # Data path
        self.data_path = data_path
        self.signal_file = signal_file
        
        # Setup signal file directory
        os.makedirs(os.path.dirname(signal_file) or '.', exist_ok=True)
        
        # Clear old signals file
        if os.path.exists(signal_file):
            os.remove(signal_file)
            print(f"✓ Cleared old signal file")
        
        # Connection monitoring
        self.connection = ConnectionMonitor(cpp_status_file, python_status_file)
        
        # Rolling window
        self.window_size = 100
        self.price_buffer = deque(maxlen=self.window_size)
        self.volume_buffer = deque(maxlen=self.window_size)
        
        # Statistics
        self.signals_sent = 0
        self.signals_buy = 0
        self.signals_sell = 0
        self.signals_neutral = 0
        
    def calculate_features_online(self, quote):
        """Calculate features from streaming data."""
        features = {}
        
        bid_price = float(quote.get('bid_price', 0))
        ask_price = float(quote.get('ask_price', 0))
        bid_volume = float(quote.get('bid_volume', 0))
        ask_volume = float(quote.get('ask_volume', 0))
        
        features['mid_price'] = (bid_price + ask_price) / 2
        features['spread'] = ask_price - bid_price
        features['spread_bps'] = (features['spread'] / features['mid_price']) * 10000 if features['mid_price'] > 0 else 0
        
        total_volume = bid_volume + ask_volume
        features['obi'] = (bid_volume - ask_volume) / total_volume if total_volume > 0 else 0
        features['weighted_mid'] = (bid_price * ask_volume + ask_price * bid_volume) / total_volume if total_volume > 0 else features['mid_price']
        
        self.price_buffer.append(features['mid_price'])
        self.volume_buffer.append(total_volume)
        
        if len(self.price_buffer) >= 10:
            prices = np.array(list(self.price_buffer))
            
            features['price_return_10'] = (prices[-1] - prices[-10]) / prices[-10] if len(prices) >= 10 else 0
            features['price_return_50'] = (prices[-1] - prices[-50]) / prices[-50] if len(prices) >= 50 else 0
            features['price_return_100'] = (prices[-1] - prices[-100]) / prices[-100] if len(prices) >= 100 else 0
            
            features['volatility_10'] = np.std(prices[-10:]) if len(prices) >= 10 else 0
            features['volatility_50'] = np.std(prices[-50:]) if len(prices) >= 50 else 0
            features['volatility_100'] = np.std(prices) if len(prices) >= 100 else 0
        else:
            for window in [10, 50, 100]:
                features[f'price_return_{window}'] = 0
                features[f'volatility_{window}'] = 0
        
        features['book_depth'] = total_volume
        features['microprice'] = features['weighted_mid']
        
        return features
    
    def predict_signal(self, features_dict):
        """Generate prediction from features."""
        if self.model is None:
            rand = np.random.random()
            signal = 1 if rand > 0.55 else (-1 if rand < 0.45 else 0)
            return signal, rand
        
        feature_vector = [features_dict.get(feat_name, 0) for feat_name in self.feature_names]
        X = np.array(feature_vector).reshape(1, -1)
        
        try:
            if hasattr(self.model, 'predict_proba'):
                pred_proba_array = self.model.predict_proba(X)[0]
                pred_proba = pred_proba_array[1] if len(pred_proba_array) == 2 else np.max(pred_proba_array)
            else:
                prediction = self.model.predict(X)[0]
                pred_proba = 0.7 if prediction == 1 else 0.3
        except:
            pred_proba = 0.5
        
        if pred_proba > 0.55:
            signal = 1
        elif pred_proba < 0.45:
            signal = -1
        else:
            signal = 0
        
        return signal, pred_proba
    
    def send_signal(self, signal, confidence):
        """Append signal to file."""
        try:
            with open(self.signal_file, 'a') as f:
                f.write(f"{signal},{confidence:.4f}\n")
                f.flush()
                os.fsync(f.fileno())
            
            self.signals_sent += 1
            if signal > 0:
                self.signals_buy += 1
            elif signal < 0:
                self.signals_sell += 1
            else:
                self.signals_neutral += 1
            
            return True
        except Exception as e:
            print(f"Error writing signal: {e}", file=sys.stderr)
            return False
    
    def run(self, delay_ms=5):
        """Main loop: read data, generate signals, write to file."""
        print("\n" + "=" * 70)
        print("Signal Generator Running (File-Based with IPC Handshake)")
        print("=" * 70)
        print(f"Signals will be written to: {self.signal_file}")
        print(f"Delay between signals: {delay_ms}ms\n")
        
        # Wait for C++ to be ready FIRST (before announcing Python)
        print("\n" + "=" * 70)
        print("WAITING FOR C++ ENGINE CONNECTION...")
        print("=" * 70)
        print("\nMake sure C++ engine is running in another terminal:")
        print("  ./main")
        print("\n" + "=" * 70 + "\n")
        
        wait_count = 0
        start_wait = time.time()
        cpp_ready = False
        
        # Wait for C++ to write CPP_READY status
        while not cpp_ready and (time.time() - start_wait) < 60:
            if self.connection.is_cpp_ready():
                cpp_ready = True
                print("✓ [CONNECTION] C++ Engine is READY!")
                break
            
            wait_count += 1
            if wait_count % 4 == 0:
                print(f"  Waiting for C++... ({wait_count // 2}s)")
            time.sleep(0.5)
        
        if not cpp_ready:
            print("\n✗ TIMEOUT: C++ Engine not ready after 60 seconds.")
            print("  Please start C++ engine first in another terminal:")
            print("    ./main")
            return
        
        # NOW announce Python is ready (after confirming C++ is ready)
        self.connection.announce_python_ready()
        
        # Small delay to ensure C++ picks up the status
        time.sleep(0.5)
        
        print(f"\nLoading market data from: {self.data_path}")
        try:
            quotes = pd.read_csv(self.data_path)
            print(f"✓ Loaded {len(quotes)} quotes\n")
        except Exception as e:
            print(f"✗ Error loading data: {e}")
            self.connection.announce_python_shutdown()
            raise
        
        # Announce Python is sending signals
        self.connection.announce_python_sending()
        
        print("=" * 70)
        print("STARTING SIGNAL GENERATION - CONNECTED TO C++ ENGINE")
        print("=" * 70 + "\n")
        
        start_time = time.time()
        last_status_time = start_time
        
        try:
            for idx, row in quotes.iterrows():
                try:
                    features = self.calculate_features_online(row.to_dict())
                    signal, confidence = self.predict_signal(features)
                    self.send_signal(signal, confidence)
                    
                    current_time = time.time()
                    if idx % 200 == 0 or (current_time - last_status_time) > 5:
                        signal_str = {1: "BUY", 0: "NEUTRAL", -1: "SELL"}[signal]
                        elapsed = current_time - start_time
                        rate = (idx + 1) / elapsed if elapsed > 0 else 0
                        
                        # Check C++ status
                        cpp_status = self.connection.read_status_file(self.connection.cpp_status_file)
                        cpp_indicator = "✓" if cpp_status == "CPP_PROCESSING" else "○"
                        
                        print(f"[{cpp_indicator}] [{idx:6d}] Mid: ${features['mid_price']:8.2f} | "
                              f"Signal: {signal_str:7s} | Conf: {confidence:.4f} | "
                              f"Rate: {rate:.1f} sig/s | Total: {self.signals_sent} | "
                              f"C++: {cpp_status}")
                        
                        last_status_time = current_time
                    
                    if delay_ms > 0:
                        time.sleep(delay_ms / 1000.0)
                
                except Exception as e:
                    print(f"Error at quote {idx}: {e}", file=sys.stderr)
                    continue
        
        except KeyboardInterrupt:
            print("\n\nSignal generator stopped by user.")
        except Exception as e:
            print(f"\nFatal error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            elapsed = time.time() - start_time
            print("\n" + "=" * 70)
            print("Statistics")
            print("=" * 70)
            print(f"Total signals: {self.signals_sent}")
            if self.signals_sent > 0:
                print(f"  BUY: {self.signals_buy} ({100*self.signals_buy/self.signals_sent:.1f}%)")
                print(f"  SELL: {self.signals_sell} ({100*self.signals_sell/self.signals_sent:.1f}%)")
                print(f"  NEUTRAL: {self.signals_neutral} ({100*self.signals_neutral/self.signals_sent:.1f}%)")
            print(f"Runtime: {elapsed:.2f}s")
            if elapsed > 0:
                print(f"Rate: {self.signals_sent/elapsed:.1f} sig/s")
            print("=" * 70)
            
            self.connection.announce_python_shutdown()


def main():
    generator = SignalGenerator(
        model_path='/Users/parasdhiman/Desktop/market-making-bot/bot_tested_2/models/ensemble_model.pkl',
        data_path='data/raw/quotes.csv',
        signal_file='ipc/ml_signals.txt',
        cpp_status_file='ipc/cpp_status.txt',
        python_status_file='ipc/python_status.txt'
    )
    generator.run(delay_ms=0)


if __name__ == "__main__":
    main()