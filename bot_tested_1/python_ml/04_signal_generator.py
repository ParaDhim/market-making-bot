# python_ml/04_signal_generator.py
"""
Simulates live data processing by reading a pre-computed feature file
and sending ML model predictions as signals to the C++ core.
(Verbose IPC Version)
"""
import argparse
import time
from pathlib import Path
import joblib
import pandas as pd

# --- Configuration Constants ---
IPC_PIPE_PATH = Path("ipc/signal_pipe")
TARGET_COLUMN = 'price_direction'
PREDICTION_TO_SIGNAL = {0: -1, 1: 1}  # DOWN: -1, UP: 1
LOG_FREQUENCY = 10 # Print a message every 1000 signals

def generate_signals(feature_path: Path, model_path: Path):
    """Loads features and a trained model to send signals to the C++ core."""
    print("--- Python Signal Generator Starting ---")

    # Load the trained model
    print(f"Attempting to load model from: '{model_path}'")
    if not model_path.exists():
        print(f"FATAL ERROR: Model file not found at '{model_path}'.")
        return
    model = joblib.load(model_path)
    print("-> Model loaded successfully.")

    # Load the pre-computed features
    print(f"Attempting to load features from: '{feature_path}'")
    if not feature_path.exists():
        print(f"FATAL ERROR: Feature file not found at '{feature_path}'.")
        return
    features_df = pd.read_csv(feature_path)
    print(f"-> Features loaded successfully. Shape: {features_df.shape}")

    # Prepare features for prediction
    X_predict = features_df.drop(TARGET_COLUMN, axis=1)

    print(f"Waiting for C++ process to create IPC pipe at '{IPC_PIPE_PATH}'...")
    while not IPC_PIPE_PATH.exists():
        time.sleep(0.1)

    # Open the named pipe for writing
    try:
        with open(IPC_PIPE_PATH, 'w') as pipe_out:
            print("\n--- ✅ IPC PIPE CONNECTED ---")
            print("Starting signal generation loop...\n")

            for i, row in X_predict.iterrows():
                features_for_prediction = pd.DataFrame([row])
                prediction = model.predict(features_for_prediction)[0]
                signal = PREDICTION_TO_SIGNAL[prediction]
                
                # Write the signal to the pipe for C++ to read
                pipe_out.write(f"{signal}\n")
                pipe_out.flush()

                # --- ADDED PRINT STATEMENT ---
                # Print a status update every LOG_FREQUENCY signals
                if (i + 1) % LOG_FREQUENCY == 0:
                    print(f"[Signal {i+1:>5}] Python 🧠 --> Sending signal: {signal:>2} --> C++ ⚙️")
                
                time.sleep(0.001)

    except BrokenPipeError:
        print("\n--- ✅ C++ process finished and closed the pipe. ---")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
    finally:
        print("--- Python signal generator has finished. ---")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate trading signals for the C++ backtester.")
    parser.add_argument('--feature_path', type=Path, default=Path('/Users/parasdhiman/Desktop/market-making-bot/bot/python_ml/data/features.csv'))
    parser.add_argument('--model_path', type=Path, default=Path('/Users/parasdhiman/Desktop/market-making-bot/bot/python_ml/models/price_direction_model.joblib'))
    args = parser.parse_args()
    generate_signals(args.feature_path, args.model_path)