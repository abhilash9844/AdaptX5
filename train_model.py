"""
Model Training Script
=====================
Trains a RandomForest model to predict infrastructure efficiency.
Implements proper ML practices with train/test split and regularization.

Usage:
    python train_model.py
"""

import os
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error


def load_dataset(path: str = 'dataset/dataset.csv') -> pd.DataFrame:
    """
    Load the infrastructure dataset.
    
    Args:
        path: Path to dataset CSV
        
    Returns:
        Loaded DataFrame
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Dataset not found at {path}. "
            "Run 'python generate_dataset.py' first."
        )
    
    return pd.read_csv(path)


def prepare_features(df: pd.DataFrame) -> tuple:
    """
    Prepare features and target for training.
    
    Args:
        df: Dataset DataFrame
        
    Returns:
        Tuple of (features, target)
    """
    # Feature columns
    feature_cols = ['servers', 'workload', 'cpu', 'energy', 'temperature']
    
    # Target column
    target_col = 'efficiency'
    
    X = df[feature_cols].values
    y = df[target_col].values
    
    return X, y, feature_cols


def train_model(
    X_train: np.ndarray,
    y_train: np.ndarray,
    n_estimators: int = 100,
    max_depth: int = 10
) -> RandomForestRegressor:
    """
    Train RandomForest regressor with regularization.
    
    Args:
        X_train: Training features
        y_train: Training targets
        n_estimators: Number of trees
        max_depth: Maximum tree depth (limits overfitting)
        
    Returns:
        Trained model
    """
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    return model


def evaluate_model(
    model: RandomForestRegressor,
    X_test: np.ndarray,
    y_test: np.ndarray
) -> dict:
    """
    Evaluate model performance.
    
    Args:
        model: Trained model
        X_test: Test features
        y_test: Test targets
        
    Returns:
        Dictionary of metrics
    """
    y_pred = model.predict(X_test)
    
    # Clip predictions to valid range
    y_pred = np.clip(y_pred, 20, 92)
    
    return {
        'r2_score': r2_score(y_test, y_pred),
        'mae': mean_absolute_error(y_test, y_pred),
        'rmse': np.sqrt(mean_squared_error(y_test, y_pred))
    }


def save_artifacts(
    model: RandomForestRegressor,
    scaler: StandardScaler,
    model_path: str = 'models/efficiency_model.pkl',
    scaler_path: str = 'models/scaler.pkl'
) -> None:
    """
    Save trained model and scaler.
    
    Args:
        model: Trained model
        scaler: Fitted scaler
        model_path: Path for model file
        scaler_path: Path for scaler file
    """
    # Create models directory
    os.makedirs('models', exist_ok=True)
    
    # Save artifacts
    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)
    
    print(f"✅ Model saved to: {model_path}")
    print(f"✅ Scaler saved to: {scaler_path}")


def main():
    """Main training pipeline."""
    print("=" * 60)
    print("AI Infrastructure Efficiency Model Training")
    print("=" * 60)
    
    # Load dataset
    print("\n📂 Loading dataset...")
    df = load_dataset()
    print(f"   Loaded {len(df)} samples")
    
    # Prepare features
    print("\n🔧 Preparing features...")
    X, y, feature_names = prepare_features(df)
    print(f"   Features: {feature_names}")
    
    # Train/test split (80/20)
    print("\n📊 Splitting data (80/20)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"   Training samples: {len(X_train)}")
    print(f"   Test samples: {len(X_test)}")
    
    # Scale features
    print("\n⚖️ Scaling features with StandardScaler...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train model with regularization to prevent overfitting
    print("\n🤖 Training RandomForestRegressor...")
    print("   n_estimators: 100")
    print("   max_depth: 10 (prevents overfitting)")
    
    model = train_model(
        X_train_scaled, 
        y_train,
        n_estimators=100,
        max_depth=10
    )
    
    # Evaluate on training set
    print("\n📈 Training Set Performance:")
    train_metrics = evaluate_model(model, X_train_scaled, y_train)
    print(f"   R² Score: {train_metrics['r2_score']:.4f}")
    print(f"   MAE: {train_metrics['mae']:.2f}")
    print(f"   RMSE: {train_metrics['rmse']:.2f}")
    
    # Evaluate on test set
    print("\n📈 Test Set Performance:")
    test_metrics = evaluate_model(model, X_test_scaled, y_test)
    print(f"   R² Score: {test_metrics['r2_score']:.4f}")
    print(f"   MAE: {test_metrics['mae']:.2f}")
    print(f"   RMSE: {test_metrics['rmse']:.2f}")
    
    # Check for overfitting
    overfit_gap = train_metrics['r2_score'] - test_metrics['r2_score']
    print(f"\n🔍 Overfitting Check:")
    print(f"   Train-Test R² Gap: {overfit_gap:.4f}")
    if overfit_gap < 0.05:
        print("   ✅ No significant overfitting detected")
    else:
        print("   ⚠️ Some overfitting present")
    
    # Feature importance
    print("\n📊 Feature Importance:")
    importance = dict(zip(feature_names, model.feature_importances_))
    for feat, imp in sorted(importance.items(), key=lambda x: -x[1]):
        bar = "█" * int(imp * 50)
        print(f"   {feat:12s}: {imp:.3f} {bar}")
    
    # Save artifacts
    print("\n💾 Saving model and scaler...")
    save_artifacts(model, scaler)
    
    # Validation: test prediction
    print("\n🧪 Validation Test:")
    test_input = np.array([[3, 60, 55, 85, 35]])  # Example input
    test_input_scaled = scaler.transform(test_input)
    prediction = model.predict(test_input_scaled)[0]
    prediction = np.clip(prediction, 20, 92)
    print(f"   Input: servers=3, workload=60%, cpu=55%, energy=85W, temp=35°C")
    print(f"   Predicted Efficiency: {prediction:.1f}%")
    
    print("\n" + "=" * 60)
    print("✅ Model training complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()