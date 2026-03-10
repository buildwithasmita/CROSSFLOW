from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class GCSCustomer(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "customer_id": "9f6f1a26-3d79-4e66-a733-b88999f12761",
                "has_corporate_card": True,
                "corporate_card_type": "Corporate Gold",
                "tenure_months": 36,
                "corporate_monthly_spend": 12500.0,
                "employee_size": "51-200",
                "industry": "Technology",
                "restaurants_spend_pct": 14.5,
                "groceries_spend_pct": 16.0,
                "travel_spend_pct": 23.0,
                "gas_stations_spend_pct": 8.0,
                "online_shopping_spend_pct": 11.0,
                "baby_stores_spend_pct": 4.0,
                "home_improvement_spend_pct": 9.0,
                "luxury_retail_spend_pct": 6.0,
                "entertainment_spend_pct": 8.5,
                "recent_baby_purchase": True,
                "recent_home_purchase": False,
                "frequent_traveler": True,
                "high_grocery_spender": True,
                "luxury_shopper": False,
                "age_bracket": "31-35",
                "estimated_income": 165000.0,
                "location_type": "Urban",
                "commute_distance": "10-30mi",
                "has_personal_gold": False,
                "has_personal_platinum": False,
                "has_personal_green": False,
                "has_hilton_card": False,
                "has_delta_card": False,
            }
        }
    )

    customer_id: str
    has_corporate_card: bool
    corporate_card_type: Literal[
        "Corporate Gold",
        "Corporate Platinum",
        "Business Gold",
        "Business Platinum",
    ]
    tenure_months: int = Field(..., ge=0)
    corporate_monthly_spend: float = Field(..., ge=0)
    employee_size: Literal["1-10", "11-50", "51-200", "201-1000", "1000+"]
    industry: Literal[
        "Technology",
        "Healthcare",
        "Finance",
        "Manufacturing",
        "Retail",
        "Professional Services",
    ]

    restaurants_spend_pct: float = Field(..., ge=0, le=100)
    groceries_spend_pct: float = Field(..., ge=0, le=100)
    travel_spend_pct: float = Field(..., ge=0, le=100)
    gas_stations_spend_pct: float = Field(..., ge=0, le=100)
    online_shopping_spend_pct: float = Field(..., ge=0, le=100)
    baby_stores_spend_pct: float = Field(..., ge=0, le=100)
    home_improvement_spend_pct: float = Field(..., ge=0, le=100)
    luxury_retail_spend_pct: float = Field(..., ge=0, le=100)
    entertainment_spend_pct: float = Field(..., ge=0, le=100)

    recent_baby_purchase: bool
    recent_home_purchase: bool
    frequent_traveler: bool
    high_grocery_spender: bool
    luxury_shopper: bool

    age_bracket: Literal["25-30", "31-35", "36-40", "41-50", "51-60", "60+"]
    estimated_income: float = Field(..., gt=0)
    location_type: Literal["Urban", "Suburban", "Rural"]
    commute_distance: Literal["0-10mi", "10-30mi", "30-50mi", "50+ mi"]

    has_personal_gold: bool
    has_personal_platinum: bool
    has_personal_green: bool
    has_hilton_card: bool
    has_delta_card: bool

    @model_validator(mode="after")
    def validate_spend_percentage_distribution(self) -> "GCSCustomer":
        mcc_values = [
            self.restaurants_spend_pct,
            self.groceries_spend_pct,
            self.travel_spend_pct,
            self.gas_stations_spend_pct,
            self.online_shopping_spend_pct,
            self.baby_stores_spend_pct,
            self.home_improvement_spend_pct,
            self.luxury_retail_spend_pct,
            self.entertainment_spend_pct,
        ]
        total_pct = float(sum(mcc_values))

        # In this project these MCC features represent the share of total spend
        # captured by selected personal-like categories, not a full 100% spend mix.
        in_percent_scale = 0.0 <= total_pct <= 100.0
        in_ratio_scale = 0.0 <= total_pct <= 1.0
        if not (in_percent_scale or in_ratio_scale):
            raise ValueError(
                f"Spending percentages must be a valid bounded share of spend. Got {total_pct:.3f}."
            )
        return self
