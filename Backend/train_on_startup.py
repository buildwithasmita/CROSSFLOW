#!/usr/bin/env python3
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def train_model_if_missing():
    model_path = Path('data/models/crossflow_model.joblib')

    if model_path.exists():
        print("✅ Model exists, skipping training")
        return

    print("🚀 Training model on Render...")

    from app.utils.data_generator import generate_crossflow_customers
    from app.utils.feature_engineering import CrossSellFeatureEngineer
    from app.services.propensity_scorer import CrossSellPropensityScorer
    from sklearn.model_selection import train_test_split
    import pandas as pd

    # Generate data
    data_path = Path('data/raw/gcs_customers.csv')
    if not data_path.exists():
        generate_crossflow_customers(5000)

    # Load and train
    df = pd.read_csv('data/raw/gcs_customers.csv')
    engineer = CrossSellFeatureEngineer()
    X = engineer.create_ml_features(df)
    y = df['adopted_personal_card']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scorer = CrossSellPropensityScorer()
    scorer.train_model(X_train, y_train, X_test, y_test)

    model_path.parent.mkdir(parents=True, exist_ok=True)
    scorer.save_model(str(model_path))

    print("✅ Model training complete!")


if __name__ == "__main__":
    train_model_if_missing()
