from __future__ import annotations

from datetime import datetime
from time import perf_counter
from typing import Dict, List

import joblib
import numpy as np
import pandas as pd
import shap
import xgboost as xgb
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


class CrossSellPropensityScorer:
    """Train and score cross-sell propensity using XGBoost."""

    def __init__(self, random_seed: int = 42) -> None:
        self.random_seed = random_seed
        np.random.seed(self.random_seed)
        self.model = xgb.XGBClassifier(
            n_estimators=150,
            max_depth=5,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=3,
            gamma=0.1,
            objective="binary:logistic",
            eval_metric="logloss",
            random_state=self.random_seed,
            scale_pos_weight=2.3,
            n_jobs=-1,
        )
        self.feature_names: List[str] = []

    def _ensure_dataframe(self, data: pd.DataFrame | Dict) -> pd.DataFrame:
        if isinstance(data, pd.DataFrame):
            return data.copy()
        if not self.feature_names:
            raise ValueError("Feature names are not set. Train or load the model first.")
        row = {name: data.get(name, 0.0) for name in self.feature_names}
        return pd.DataFrame([row], columns=self.feature_names)

    def _assert_model_ready(self) -> None:
        if self.model is None or not self.feature_names:
            raise ValueError("Model is not ready. Train or load the model first.")

    def train_model(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series | np.ndarray,
        X_val: pd.DataFrame,
        y_val: pd.Series | np.ndarray,
    ) -> Dict:
        X_train_df = pd.DataFrame(X_train).copy()
        X_val_df = pd.DataFrame(X_val).copy()
        y_train_arr = np.asarray(y_train).astype(int)
        y_val_arr = np.asarray(y_val).astype(int)

        self.feature_names = list(X_train_df.columns)

        start = perf_counter()
        self.model.fit(
            X_train_df,
            y_train_arr,
            eval_set=[(X_val_df, y_val_arr)],
            verbose=False,
        )
        train_time_seconds = perf_counter() - start

        val_prob = self.model.predict_proba(X_val_df)[:, 1]
        val_pred = (val_prob >= 0.5).astype(int)

        metrics = {
            "accuracy": float(accuracy_score(y_val_arr, val_pred)),
            "precision": float(precision_score(y_val_arr, val_pred, zero_division=0)),
            "recall": float(recall_score(y_val_arr, val_pred, zero_division=0)),
            "f1_score": float(f1_score(y_val_arr, val_pred, zero_division=0)),
            "roc_auc": float(roc_auc_score(y_val_arr, val_prob)),
            "train_time_seconds": round(float(train_time_seconds), 3),
        }
        return metrics

    def predict_propensity(self, customer_features: Dict) -> Dict:
        self._assert_model_ready()
        feature_df = self._ensure_dataframe(customer_features)
        probability = float(self.model.predict_proba(feature_df)[0][1])
        propensity_score = int(probability * 100)

        if propensity_score >= 75:
            tier = "High"
            expected_conversion = "70-85%"
        elif propensity_score >= 50:
            tier = "Medium"
            expected_conversion = "40-60%"
        else:
            tier = "Low"
            expected_conversion = "10-25%"

        return {
            "propensity_score": propensity_score,
            "probability": probability,
            "tier": tier,
            "expected_conversion": expected_conversion,
            "confidence": "High" if probability > 0.8 or probability < 0.2 else "Medium",
        }

    def get_feature_importance(self) -> pd.DataFrame:
        self._assert_model_ready()
        importance = self.model.feature_importances_
        return pd.DataFrame(
            {"feature_name": self.feature_names, "importance_score": importance}
        ).sort_values("importance_score", ascending=False, ignore_index=True)

    def explain_prediction(self, customer_features: Dict, prediction: Dict) -> Dict:
        self._assert_model_ready()
        feature_df = self._ensure_dataframe(customer_features)

        explainer = shap.TreeExplainer(self.model)
        shap_values = explainer.shap_values(feature_df)
        if isinstance(shap_values, list):
            values = np.asarray(shap_values[1][0], dtype=float)
        else:
            values = np.asarray(shap_values[0], dtype=float)

        feature_contributions = list(zip(self.feature_names, values))
        feature_contributions.sort(key=lambda x: abs(float(x[1])), reverse=True)

        top_positive = [
            {"feature": f, "contribution": round(float(c) * 100, 1), "direction": "positive"}
            for f, c in feature_contributions
            if c > 0
        ][:5]

        top_negative = [
            {"feature": f, "contribution": round(abs(float(c)) * 100, 1), "direction": "negative"}
            for f, c in feature_contributions
            if c < 0
        ][:3]

        explanation = self.generate_explanation(top_positive, top_negative, prediction)
        return {
            "top_positive_factors": top_positive,
            "top_negative_factors": top_negative,
            "explanation": explanation,
        }

    def generate_explanation(
        self,
        positive_factors: List[Dict],
        negative_factors: List[Dict],
        prediction: Dict,
    ) -> str:
        score = prediction["propensity_score"]
        tier = prediction["tier"]

        explanation = f"Propensity score is {tier} ({score}/100) because: "

        if positive_factors:
            top_reason = positive_factors[0]
            feature_name = str(top_reason["feature"]).lower()
            if "life_event" in feature_name:
                explanation += "Life event detected (new parent/homeowner) - highest cross-sell indicator. "
            elif "personal_spend" in feature_name:
                explanation += "High personal spending on corporate card indicates personal card need. "
            elif "travel" in feature_name:
                explanation += "Frequent travel spending signals premium card opportunity. "
            else:
                explanation += f"Strong positive signal from {top_reason['feature']}. "

        if tier == "Low" and negative_factors:
            explanation += "However, "
            top_negative = negative_factors[0]
            feature_name = str(top_negative["feature"]).lower()
            if "existing" in feature_name:
                explanation += "customer already has multiple personal cards. "
            elif "tenure" in feature_name:
                explanation += "short tenure with Amex (too new for cross-sell). "
            else:
                explanation += f"{top_negative['feature']} reduces near-term conversion likelihood. "

        return explanation.strip()

    def batch_predict(self, customers_features: pd.DataFrame) -> List[Dict]:
        self._assert_model_ready()
        feature_df = pd.DataFrame(customers_features).copy()

        # Align columns to training schema.
        for col in self.feature_names:
            if col not in feature_df.columns:
                feature_df[col] = 0.0
        feature_df = feature_df[self.feature_names]

        probabilities = self.model.predict_proba(feature_df)[:, 1]
        scores = (probabilities * 100).astype(int)

        results = []
        for i, score in enumerate(scores):
            results.append(
                {
                    "customer_id": feature_df.index[i],
                    "propensity_score": int(score),
                    "probability": float(probabilities[i]),
                    "tier": "High" if score >= 75 else "Medium" if score >= 50 else "Low",
                }
            )
        return results

    def save_model(self, filepath: str) -> None:
        """Save model and metadata."""
        self._assert_model_ready()
        joblib.dump(
            {
                "model": self.model,
                "feature_names": self.feature_names,
                "training_date": datetime.now().isoformat(),
            },
            filepath,
        )

    def load_model(self, filepath: str) -> None:
        """Load pre-trained model."""
        data = joblib.load(filepath)
        self.model = data["model"]
        self.feature_names = data["feature_names"]
