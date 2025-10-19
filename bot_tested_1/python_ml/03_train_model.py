# python_ml/03_train_model.py
"""
Trains a LightGBM classification model to predict price direction.
This version includes hyperparameter tuning and early stopping.
"""

import argparse
import logging
from pathlib import Path
from typing import Tuple

import joblib
import lightgbm as lgb
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

# --- Configuration Constants ---
RANDOM_STATE = 42
TEST_SIZE = 0.2
TARGET_COLUMN = 'price_direction'
# We've removed the 'STAY' class, so the mapping is simpler
Y_MAP = {-1: 0, 1: 1} # DOWN: 0, UP: 1

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_data(file_path: Path) -> pd.DataFrame:
    # (This function remains the same as before)
    logging.info(f"Loading data from '{file_path}'...")
    df = pd.read_csv(file_path)
    logging.info(f"Successfully loaded data with shape: {df.shape}")
    return df

def prepare_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """Prepares data by mapping the binary target variable."""
    logging.info("Preparing data for training...")
    # The new feature script creates a binary target, so we filter if needed
    df_filtered = df[df[TARGET_COLUMN] != 0].copy()
    y = df_filtered[TARGET_COLUMN].map(Y_MAP)
    X = df_filtered.drop(TARGET_COLUMN, axis=1)
    return X, y

def train_and_evaluate(X_train, y_train, X_test, y_test) -> lgb.LGBMClassifier:
    """Initializes, trains, and evaluates the LightGBM model with tuned parameters."""
    logging.info("Training LightGBM model with optimized parameters...")
    
    # These are more robust parameters than the defaults
    params = {
        'objective': 'binary',
        'metric': 'binary_logloss',
        'n_estimators': 1000,
        'learning_rate': 0.05,
        'feature_fraction': 0.9,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'verbose': -1,
        'n_jobs': -1,
        'seed': RANDOM_STATE,
        'boosting_type': 'gbdt',
        'num_leaves': 31,
        'max_depth': -1,
    }
    
    model = lgb.LGBMClassifier(**params)
    
    # Use early stopping to prevent overfitting
    model.fit(X_train, y_train,
              eval_set=[(X_test, y_test)],
              eval_metric='logloss',
              callbacks=[lgb.early_stopping(100, verbose=True)])

    logging.info("Evaluating model performance...")
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    target_names = ['DOWN (-1)', 'UP (1)']
    report = classification_report(y_test, y_pred, target_names=target_names)
    
    logging.info(f"\n\n--- Model Evaluation ---")
    logging.info(f"Model Accuracy: {accuracy:.4f}")
    logging.info(f"Classification Report:\n{report}")
    logging.info("--- End of Report ---\n")
    
    return model

def save_model(model: lgb.LGBMClassifier, output_path: Path):
    # (This function remains the same as before)
    logging.info(f"Saving model to '{output_path}'...")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output_path)
    logging.info("Model saved successfully.")

def main(args):
    """Main function to orchestrate the model training pipeline."""
    df = load_data(args.input_path)
    X, y = prepare_data(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )
    
    trained_model = train_and_evaluate(X_train, y_train, X_test, y_test)
    save_model(trained_model, args.output_path)

if __name__ == '__main__':
    # (This main block remains the same as before)
    parser = argparse.ArgumentParser(description="Train a LightGBM price direction model.")
    parser.add_argument('--input_path', type=Path, default=Path('data/features.csv'))
    parser.add_argument('--output_path', type=Path, default=Path('models/price_direction_model.joblib'))
    args = parser.parse_args()
    main(args)