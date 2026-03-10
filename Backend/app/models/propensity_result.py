from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from app.models.customer import GCSCustomer


class LifeEvent(BaseModel):
    event: str
    confidence: int = Field(..., ge=0, le=100)
    detected: bool
    signals: List[str] = Field(default_factory=list)
    recommended_product: str
    recommendation_reason: str


class PropensityScore(BaseModel):
    customer_id: str
    propensity_score: int = Field(..., ge=0, le=100)
    probability: float = Field(..., ge=0.0, le=1.0)
    tier: Literal["High", "Medium", "Low"]
    expected_conversion: str
    confidence: Literal["High", "Medium", "Low"]
    life_events: List[LifeEvent] = Field(default_factory=list)
    recommended_product: str
    recommendation_reason: str
    expected_annual_value: float = Field(..., ge=0)
    top_positive_factors: List[Dict[str, Any]] = Field(default_factory=list)
    top_negative_factors: List[Dict[str, Any]] = Field(default_factory=list)
    explanation: str


class BatchPropensityRequest(BaseModel):
    customers: List[GCSCustomer]
    include_explanations: bool = True


class BatchPropensityResponse(BaseModel):
    results: List[PropensityScore]
    summary: Dict[str, Any] = Field(default_factory=dict)
    processing_time_seconds: float = Field(..., ge=0)
    generated_at: Optional[datetime] = None
