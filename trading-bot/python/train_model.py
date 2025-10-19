import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import lightgbm as lgb
import joblib
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

class ModelTrainer:
    def __init__(self):
        self.model = None
        self.feature_names = None
    
    def load_data(self):
        """Load processed features"""
        data_file = "data/processed/features.csv"
        if not Path(data_file).exists():
            raise FileNotFoundError(f"{data_file} not found. Run feature_engineering.py first.")
        
        df = pd.read_csv(data_file)
        
        # Separate features, labels, and metadata
        self.feature_names = [col for col in df.columns 
                             if col not in ['label', 'timestamp', 'mid_price']]
        
        self.X = df[self.feature_names].values
        self.y = df['label'].values
        self.timestamps = pd.to_datetime(df['timestamp'])
        
        print(f"Loaded {len(self.X)} samples with {len(self.feature_names)} features")
        print(f"Class distribution:\n{pd.Series(self.y).value_counts()}")
    
    def train(self):
        """Train LightGBM model"""
        # Time-series split (respect temporal order)
        # Use 80% for training, 20% for testing
        split_idx = int(len(self.X) * 0.8)
        
        X_train, X_test = self.X[:split_idx], self.X[split_idx:]
        y_train, y_test = self.y[:split_idx], self.y[split_idx:]
        
        print(f"\nTraining samples: {len(X_train)}")
        print(f"Testing samples: {len(X_test)}")
        
        # Train LightGBM classifier
        print("\nTraining LightGBM model...")
        self.model = lgb.LGBMClassifier(
            objective='multiclass',
            num_class=3,  # -1, 0, 1
            n_estimators=200,
            learning_rate=0.05,
            max_depth=7,
            num_leaves=31,
            min_child_samples=100,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbose=-1
        )
        
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            callbacks=[lgb.early_stopping(50), lgb.log_evaluation(20)]
        )
        
        # Evaluate
        y_pred_train = self.model.predict(X_train)
        y_pred_test = self.model.predict(X_test)
        
        train_acc = accuracy_score(y_train, y_pred_train)
        test_acc = accuracy_score(y_test, y_pred_test)
        
        print(f"\n=== Model Performance ===")
        print(f"Training Accuracy: {train_acc:.4f}")
        print(f"Testing Accuracy: {test_acc:.4f}")
        
        print("\nClassification Report (Test Set):")
        print(classification_report(y_test, y_pred_test, 
                                   target_names=['Down (-1)', 'Neutral (0)', 'Up (1)']))
        
        # Plot confusion matrix
        self.plot_confusion_matrix(y_test, y_pred_test)
        
        # Plot feature importance
        self.plot_feature_importance()
        
        return test_acc
    
    def plot_confusion_matrix(self, y_true, y_pred):
        """Plot confusion matrix"""
        cm = confusion_matrix(y_true, y_pred)
        
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                   xticklabels=['Down', 'Neutral', 'Up'],
                   yticklabels=['Down', 'Neutral', 'Up'])
        plt.title('Confusion Matrix')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.tight_layout()
        plt.savefig('results/confusion_matrix.png', dpi=150)
        print("\nSaved confusion matrix to results/confusion_matrix.png")
    
    def plot_feature_importance(self):
        """Plot feature importance"""
        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        plt.figure(figsize=(10, 8))
        plt.barh(importance_df['feature'][:15], importance_df['importance'][:15])
        plt.xlabel('Importance')
        plt.title('Top 15 Feature Importances')
        plt.tight_layout()
        plt.savefig('results/feature_importance.png', dpi=150)
        print("Saved feature importance to results/feature_importance.png")
    
    def save_model(self):
        """Save trained model"""
        Path("results").mkdir(exist_ok=True)
        
        model_file = "results/trained_model.joblib"
        joblib.dump({
            'model': self.model,
            'feature_names': self.feature_names
        }, model_file)
        
        print(f"\nSaved model to {model_file}")

def main():
    print("=== ML Model Training Pipeline ===\n")
    
    trainer = ModelTrainer()
    trainer.load_data()
    accuracy = trainer.train()
    trainer.save_model()
    
    print("\n=== Training Complete ===")
    print(f"Final Test Accuracy: {accuracy:.4f}")
    
    if accuracy > 0.40:  # Better than random (0.33 for 3 classes)
        print("✓ Model shows predictive power!")
    else:
        print("⚠ Model may need more data or better features")

if __name__ == "__main__":
    main()