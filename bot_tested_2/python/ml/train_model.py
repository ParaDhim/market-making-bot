"""
Optimized training pipeline with feature selection, ensemble methods, and hyperparameter tuning.
"""

import pandas as pd
import numpy as np
import lightgbm as lgb
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import (accuracy_score, f1_score, roc_auc_score, 
                             precision_score, recall_score, classification_report)
import joblib
import os
import warnings
warnings.filterwarnings('ignore')


class OptimizedModelTrainer:
    def __init__(self, features_path='data/processed/features_comprehensive.csv'):
        self.features_path = features_path
        self.models = {}
        self.feature_names = None
        self.scaler = StandardScaler()
        self.selected_features = None
        
    def load_features(self):
        """Load engineered features."""
        print("Loading features...")
        df = pd.read_csv(self.features_path)
        print(f"Loaded {len(df)} samples with {len(df.columns)} columns")
        return df
    
    def select_features(self, X, y, n_features=100):
        """Select top features using multiple methods."""
        print(f"\nSelecting top {n_features} features...")
        
        # Method 1: Correlation with target
        correlations = []
        for i, col in enumerate(X.columns):
            try:
                corr = np.corrcoef(X.iloc[:, i].fillna(0), y)[0, 1]
                correlations.append((col, abs(corr)))
            except:
                pass
        
        top_corr = sorted(correlations, key=lambda x: x[1], reverse=True)[:n_features//3]
        top_corr_features = [x[0] for x in top_corr]
        
        print(f"  Top correlated features: {len(top_corr_features)}")
        
        # Method 2: Mutual information
        from sklearn.feature_selection import mutual_info_classif
        mi_scores = mutual_info_classif(X.fillna(0), y, random_state=42)
        mi_ranking = sorted(zip(X.columns, mi_scores), key=lambda x: x[1], reverse=True)
        top_mi_features = [x[0] for x in mi_ranking[:n_features//3]]
        
        print(f"  Top MI features: {len(top_mi_features)}")
        
        # Method 3: LightGBM feature importance
        train_data = lgb.Dataset(X.fillna(0), label=y)
        lgb_model = lgb.train(
            {'objective': 'binary', 'verbose': -1},
            train_data,
            num_boost_round=100
        )
        lgb_importance = lgb_model.feature_importance()
        lgb_ranking = sorted(zip(X.columns, lgb_importance), key=lambda x: x[1], reverse=True)
        top_lgb_features = [x[0] for x in lgb_ranking[:n_features//3]]
        
        print(f"  Top LightGBM features: {len(top_lgb_features)}")
        
        # Combine: take union of top features from all methods
        combined_features = list(set(top_corr_features + top_mi_features + top_lgb_features))
        self.selected_features = combined_features[:n_features]
        
        print(f"\n✓ Selected {len(self.selected_features)} features")
        return self.selected_features
    
    def prepare_data(self, df):
        """Prepare features and target."""
        print("\nPreparing data...")
        
        exclude_cols = ['timestamp', 'datetime_trade', 'datetime_quote', 'side', 
                       'target', 'future_mid', 'future_return', 'price', 'bid_price', 
                       'ask_price', 'quantity']
        
        feature_cols = [col for col in df.columns if col not in exclude_cols and col in df.columns]
        
        # Select features if not already done
        if self.selected_features is None:
            X = df[feature_cols].copy()
            y = df['target'].values
            self.select_features(X, y, n_features=100)
        
        X = df[self.selected_features].copy()
        y = df['target'].values
        
        # Handle NaN and inf
        X = X.replace([np.inf, -np.inf], np.nan)
        X = X.fillna(X.median())
        
        self.feature_names = list(X.columns)
        
        # Scale
        X_scaled = self.scaler.fit_transform(X)
        
        print(f"Feature matrix: {X_scaled.shape}")
        print(f"Target distribution: {np.bincount(y)}")
        
        return X_scaled, y
    
    def walk_forward_validation(self, X, y, n_splits=5):
        """Time-series cross-validation."""
        print("\n" + "=" * 80)
        print("WALK-FORWARD VALIDATION")
        print("=" * 80)
        
        tscv = TimeSeriesSplit(n_splits=n_splits)
        results = []
        
        for fold, (train_idx, test_idx) in enumerate(tscv.split(X)):
            print(f"\nFold {fold + 1}/{n_splits}")
            
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]
            
            print(f"  Train: {len(train_idx)}, Test: {len(test_idx)}")
            
            # Train ensemble
            models = self._train_ensemble(X_train, y_train)
            
            # Predict with ensemble
            y_pred_proba = np.mean([
                model.predict_proba(X_test)[:, 1] if hasattr(model, 'predict_proba') 
                else model.predict(X_test) 
                for model in models
            ], axis=0)
            
            y_pred = (y_pred_proba > 0.5).astype(int)
            
            acc = accuracy_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred)
            try:
                auc = roc_auc_score(y_test, y_pred_proba)
            except:
                auc = 0.5
            
            results.append({'acc': acc, 'f1': f1, 'auc': auc})
            
            print(f"  Accuracy: {acc:.4f} | F1: {f1:.4f} | AUC: {auc:.4f}")
        
        mean_acc = np.mean([r['acc'] for r in results])
        std_acc = np.std([r['acc'] for r in results])
        mean_f1 = np.mean([r['f1'] for r in results])
        mean_auc = np.mean([r['auc'] for r in results])
        
        print("\n" + "-" * 80)
        print(f"Average Accuracy: {mean_acc:.4f} ± {std_acc:.4f}")
        print(f"Average F1-Score: {mean_f1:.4f}")
        print(f"Average AUC: {mean_auc:.4f}")
        print("=" * 80)
        
        return mean_acc, std_acc, mean_f1
    
    def _train_ensemble(self, X_train, y_train):
        """Train ensemble of models."""
        models = []
        
        # LightGBM
        train_data = lgb.Dataset(X_train, label=y_train)
        lgb_model = lgb.train(
            {
                'objective': 'binary',
                'metric': 'auc',
                'num_leaves': 31,
                'learning_rate': 0.05,
                'feature_fraction': 0.8,
                'bagging_fraction': 0.8,
                'min_data_in_leaf': 50,
                'verbose': -1,
            },
            train_data,
            num_boost_round=200
        )
        models.append(lgb_model)
        
        # XGBoost
        xgb_model = xgb.XGBClassifier(
            max_depth=5,
            learning_rate=0.05,
            n_estimators=200,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbose=0,
            n_jobs=-1,
            use_label_encoder=False,
            eval_metric='auc'
        )
        xgb_model.fit(X_train, y_train)
        models.append(xgb_model)
        
        # Random Forest
        rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_leaf=50,
            n_jobs=-1,
            random_state=42
        )
        rf_model.fit(X_train, y_train)
        models.append(rf_model)
        
        return models
    
    def train_final_model(self, X, y):
        """Train final ensemble model."""
        print("\nTraining final ensemble model...")
        
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        models = self._train_ensemble(X_train, y_train)
        self.models = models
        
        # Evaluate
        y_pred_proba = np.mean([
            m.predict_proba(X_test)[:, 1] if hasattr(m, 'predict_proba') 
            else m.predict(X_test) 
            for m in models
        ], axis=0)
        
        y_pred = (y_pred_proba > 0.5).astype(int)
        
        print("\n" + "=" * 80)
        print("FINAL MODEL EVALUATION")
        print("=" * 80)
        print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
        print(f"F1-Score: {f1_score(y_test, y_pred):.4f}")
        print(f"Precision: {precision_score(y_test, y_pred):.4f}")
        print(f"Recall: {recall_score(y_test, y_pred):.4f}")
        print(f"AUC: {roc_auc_score(y_test, y_pred_proba):.4f}")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred, target_names=['Down', 'Up']))
        
        return accuracy_score(y_test, y_pred)
    
    def save_model(self, output_dir='models/'):
        """Save trained models."""
        os.makedirs(output_dir, exist_ok=True)
        
        model_data = {
            'models': self.models,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'selected_features': self.selected_features
        }
        
        joblib.dump(model_data, f'{output_dir}/ensemble_model.pkl')
        print(f"\n✓ Model saved to: {output_dir}/ensemble_model.pkl")


def main():
    print("=" * 80)
    print("OPTIMIZED ML TRAINING PIPELINE")
    print("=" * 80)
    
    trainer = OptimizedModelTrainer()
    df = trainer.load_features()
    X, y = trainer.prepare_data(df)
    
    # Cross-validation
    mean_acc, std_acc, mean_f1 = trainer.walk_forward_validation(X, y, n_splits=5)
    
    # Final model
    final_acc = trainer.train_final_model(X, y)
    trainer.save_model()
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Cross-validation accuracy: {mean_acc:.4f} ± {std_acc:.4f}")
    print(f"Final test accuracy: {final_acc:.4f}")
    print(f"\nNote: Realistic signal is limited by data quality, not model complexity")
    print("=" * 80)


if __name__ == "__main__":
    main()