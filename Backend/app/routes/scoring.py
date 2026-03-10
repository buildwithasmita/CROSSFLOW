from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Any, Dict, List

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from app.models.customer import GCSCustomer
from app.models.propensity_result import (
    BatchPropensityRequest,
    BatchPropensityResponse,
    PropensityScore,
)
from app.services.life_event_detector import LifeEventDetector
from app.services.propensity_scorer import CrossSellPropensityScorer
from app.utils.feature_engineering import CrossSellFeatureEngineer

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DATA_PATH = BASE_DIR / "data" / "raw" / "gcs_customers.csv"
MODEL_PATH = BASE_DIR / "data" / "models" / "crossflow_model.joblib"

_detector = LifeEventDetector()
_engineer = CrossSellFeatureEngineer()
_scorer = CrossSellPropensityScorer()
_model_loaded = False


def _load_model_if_needed() -> None:
    global _model_loaded
    if _model_loaded:
        return
    if not MODEL_PATH.exists():
        raise HTTPException(status_code=503, detail=f"Model file not found at {MODEL_PATH}")
    try:
        _scorer.load_model(str(MODEL_PATH))
        _model_loaded = True
    except Exception as exc:  # pragma: no cover - defensive runtime guard
        raise HTTPException(status_code=500, detail=f"Failed to load model: {exc}") from exc


def _parse_expected_annual_value(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        sanitized = value.replace("$", "").replace(",", "").strip()
        try:
            return float(sanitized)
        except ValueError:
            return 0.0
    return 0.0


@router.post("/api/v1/crosssell/score/single", response_model=PropensityScore)
async def score_single_customer(customer: GCSCustomer) -> PropensityScore:
    """Score a single GCS customer for personal card cross-sell propensity."""
    _load_model_if_needed()

    customer_dict = customer.model_dump()
    life_events = _detector.detect_all_events(customer_dict)
    recommendation = _detector.get_cross_sell_recommendation(life_events, customer_dict)

    customer_df = pd.DataFrame([customer_dict])
    features = _engineer.create_ml_features(customer_df)
    feature_row = features.iloc[0].to_dict()

    propensity = _scorer.predict_propensity(feature_row)
    explanation = _scorer.explain_prediction(feature_row, propensity)

    return PropensityScore(
        customer_id=customer.customer_id,
        propensity_score=propensity["propensity_score"],
        probability=propensity["probability"],
        tier=propensity["tier"],
        expected_conversion=propensity["expected_conversion"],
        confidence=propensity["confidence"],
        life_events=life_events,
        recommended_product=recommendation["recommended_product"],
        recommendation_reason=recommendation["reason"],
        expected_annual_value=_parse_expected_annual_value(
            recommendation.get("expected_annual_value", 0.0)
        ),
        top_positive_factors=explanation["top_positive_factors"],
        top_negative_factors=explanation["top_negative_factors"],
        explanation=explanation["explanation"],
    )


@router.post("/api/v1/crosssell/score/batch", response_model=BatchPropensityResponse)
async def score_batch_customers(request: BatchPropensityRequest) -> BatchPropensityResponse:
    """Score up to 1000 GCS customers in one batch request."""
    if len(request.customers) == 0:
        raise HTTPException(status_code=400, detail="At least one customer is required")
    if len(request.customers) > 1000:
        raise HTTPException(status_code=400, detail="Batch limit exceeded (max 1000 customers)")

    _load_model_if_needed()
    start = perf_counter()

    customer_records = [cust.model_dump() for cust in request.customers]
    customers_df = pd.DataFrame(customer_records)
    features_df = _engineer.create_ml_features(customers_df)
    batch_predictions = _scorer.batch_predict(features_df)

    results: List[PropensityScore] = []
    for i, pred in enumerate(batch_predictions):
        customer = request.customers[i]
        customer_dict = customer.model_dump()
        life_events = _detector.detect_all_events(customer_dict)
        recommendation = _detector.get_cross_sell_recommendation(life_events, customer_dict)

        top_positive_factors: List[Dict[str, Any]] = []
        top_negative_factors: List[Dict[str, Any]] = []
        explanation_text = "Explanation omitted by request."
        confidence = "High" if pred["probability"] > 0.8 or pred["probability"] < 0.2 else "Medium"
        expected_conversion = (
            "70-85%"
            if pred["propensity_score"] >= 75
            else "40-60%"
            if pred["propensity_score"] >= 50
            else "10-25%"
        )
        if request.include_explanations:
            explanation = _scorer.explain_prediction(features_df.iloc[i].to_dict(), pred)
            top_positive_factors = explanation["top_positive_factors"]
            top_negative_factors = explanation["top_negative_factors"]
            explanation_text = explanation["explanation"]

        results.append(
            PropensityScore(
                customer_id=customer.customer_id,
                propensity_score=pred["propensity_score"],
                probability=pred["probability"],
                tier=pred["tier"],
                expected_conversion=expected_conversion,
                confidence=confidence,
                life_events=life_events,
                recommended_product=recommendation["recommended_product"],
                recommendation_reason=recommendation["reason"],
                expected_annual_value=_parse_expected_annual_value(
                    recommendation.get("expected_annual_value", 0.0)
                ),
                top_positive_factors=top_positive_factors,
                top_negative_factors=top_negative_factors,
                explanation=explanation_text,
            )
        )

    processing_time = perf_counter() - start
    scores = [r.propensity_score for r in results]
    summary = {
        "total_customers": len(results),
        "high_tier": sum(1 for r in results if r.tier == "High"),
        "medium_tier": sum(1 for r in results if r.tier == "Medium"),
        "low_tier": sum(1 for r in results if r.tier == "Low"),
        "average_propensity_score": float(round(sum(scores) / len(scores), 2)),
    }

    return BatchPropensityResponse(
        results=results,
        summary=summary,
        processing_time_seconds=round(processing_time, 3),
    )


@router.get("/api/v1/crosssell/customers/sample")
async def get_sample_customers(limit: int = Query(default=50, ge=1, le=500)) -> List[Dict[str, Any]]:
    """Get sample GCS customers for demo."""
    if not RAW_DATA_PATH.exists():
        raise HTTPException(status_code=404, detail=f"Sample data not found at {RAW_DATA_PATH}")
    df = pd.read_csv(RAW_DATA_PATH)
    sample = df.head(limit)
    return sample.to_dict("records")


@router.get("/api/v1/crosssell/analytics/feature-importance")
async def get_feature_importance() -> List[Dict[str, Any]]:
    """Return trained model feature importance scores."""
    _load_model_if_needed()
    importance_df = _scorer.get_feature_importance()
    return importance_df.to_dict("records")


@router.get("/api/v1/crosssell/analytics/adoption-by-segment")
async def get_adoption_by_segment() -> Dict[str, Any]:
    """Return adoption analytics by key business segments."""
    if not RAW_DATA_PATH.exists():
        raise HTTPException(status_code=404, detail=f"Data file not found at {RAW_DATA_PATH}")

    df = pd.read_csv(RAW_DATA_PATH)
    if "adopted_personal_card" not in df.columns:
        raise HTTPException(status_code=400, detail="Dataset missing 'adopted_personal_card' column")

    adoption_col = "adopted_personal_card"
    summary = {
        "overall_adoption_rate": float(df[adoption_col].mean()),
        "by_life_event": {
            "recent_baby_purchase": float(df[df["recent_baby_purchase"]][adoption_col].mean())
            if df["recent_baby_purchase"].any()
            else 0.0,
            "recent_home_purchase": float(df[df["recent_home_purchase"]][adoption_col].mean())
            if df["recent_home_purchase"].any()
            else 0.0,
            "frequent_traveler": float(df[df["frequent_traveler"]][adoption_col].mean())
            if df["frequent_traveler"].any()
            else 0.0,
        },
        "by_age_bracket": (
            df.groupby("age_bracket", observed=False)[adoption_col]
            .mean()
            .sort_index()
            .to_dict()
        ),
        "by_industry": (
            df.groupby("industry", observed=False)[adoption_col]
            .mean()
            .sort_values(ascending=False)
            .to_dict()
        ),
        "by_card_tier": (
            df.assign(
                card_tier=df["corporate_card_type"].map(
                    {
                        "Corporate Gold": "Gold",
                        "Business Gold": "Gold",
                        "Corporate Platinum": "Platinum",
                        "Business Platinum": "Platinum",
                    }
                )
            )
            .groupby("card_tier", observed=False)[adoption_col]
            .mean()
            .to_dict()
        ),
    }
    return summary


def _health_payload() -> Dict[str, Any]:
    model_exists = MODEL_PATH.exists()
    data_exists = RAW_DATA_PATH.exists()
    loaded = _model_loaded
    if model_exists and not loaded:
        try:
            _load_model_if_needed()
            loaded = True
        except HTTPException:
            loaded = False

    return {
        "status": "ok",
        "model_path": str(MODEL_PATH),
        "model_exists": model_exists,
        "model_loaded": loaded,
        "data_path": str(RAW_DATA_PATH),
        "data_exists": data_exists,
    }


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint with model/data status."""
    return _health_payload()


@router.get("/api/v1/health")
async def api_health_check() -> Dict[str, Any]:
    """Versioned health check endpoint for frontend API clients."""
    return _health_payload()
