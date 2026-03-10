from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd

from app.services.life_event_detector import LifeEventDetector


class CrossSellFeatureEngineer:
    """Create ML-ready features for cross-sell propensity modeling."""

    def __init__(self) -> None:
        self.detector = LifeEventDetector()
        self._all_mcc_cols = [
            "restaurants_spend_pct",
            "groceries_spend_pct",
            "travel_spend_pct",
            "gas_stations_spend_pct",
            "online_shopping_spend_pct",
            "baby_stores_spend_pct",
            "home_improvement_spend_pct",
            "luxury_retail_spend_pct",
            "entertainment_spend_pct",
        ]

    def _to_float(self, value: object, default: float = 0.0) -> float:
        try:
            if value is None:
                return default
            if isinstance(value, float) and np.isnan(value):
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    def _to_bool(self, value: object) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, np.integer)):
            return value != 0
        if isinstance(value, str):
            return value.strip().lower() in {"true", "1", "yes", "y"}
        return bool(value)

    def _pct_100(self, value: object) -> float:
        """Normalize spend percentages to 0-100 scale."""
        raw = self._to_float(value, 0.0)
        if raw <= 1.0:
            return raw * 100.0
        return raw

    def calculate_personal_spend_ratio(self, customer_data: Dict) -> float:
        personal_mcc = [
            "restaurants_spend_pct",
            "groceries_spend_pct",
            "online_shopping_spend_pct",
            "entertainment_spend_pct",
            "baby_stores_spend_pct",
            "home_improvement_spend_pct",
        ]
        personal_ratio = sum(self._pct_100(customer_data.get(mcc, 0.0)) for mcc in personal_mcc)
        return float(min(personal_ratio, 100.0))

    def calculate_spending_diversity(self, customer_data: Dict) -> float:
        mcc_pcts = [self._pct_100(customer_data.get(col, 0.0)) for col in self._all_mcc_cols]
        mcc_probs = np.array(mcc_pcts, dtype=float) / 100.0
        mcc_probs = mcc_probs[mcc_probs > 0]
        if len(mcc_probs) == 0:
            return 0.0
        entropy = -np.sum(mcc_probs * np.log2(mcc_probs))
        max_entropy = np.log2(len(self._all_mcc_cols))
        diversity_score = (entropy / max_entropy) * 10.0
        return float(np.clip(diversity_score, 0.0, 10.0))

    def _primary_event_type_code(self, events: list[Dict]) -> int:
        event_codes = {
            "New Parent": 1,
            "New Homeowner": 2,
            "Travel Enthusiast": 3,
            "Lifestyle Upgrade": 4,
        }
        if not events:
            return 0
        return event_codes.get(events[0].get("event", ""), 0)

    def encode_life_events(self, customer_data: Dict, detector: LifeEventDetector) -> Dict:
        events = detector.detect_all_events(customer_data)
        return {
            "has_life_event": int(len(events) > 0),
            "life_event_confidence": events[0]["confidence"] if events else 0,
            "num_life_events": len(events),
            "primary_life_event_type": self._primary_event_type_code(events),
            "new_parent_detected": int(any(e["event"] == "New Parent" for e in events)),
            "new_home_detected": int(any(e["event"] == "New Homeowner" for e in events)),
            "travel_enthusiast_detected": int(any(e["event"] == "Travel Enthusiast" for e in events)),
            "lifestyle_upgrade_detected": int(any(e["event"] == "Lifestyle Upgrade" for e in events)),
        }

    def encode_card_tier(self, card_type: str) -> int:
        tiers = {
            "Corporate Gold": 1,
            "Business Gold": 1,
            "Corporate Platinum": 2,
            "Business Platinum": 2,
        }
        return tiers.get(card_type, 0)

    def encode_age_bracket(self, age: str) -> int:
        brackets = {
            "25-30": 1,
            "31-35": 2,
            "36-40": 3,
            "41-50": 4,
            "51-60": 5,
            "60+": 6,
        }
        return brackets.get(age, 0)

    def encode_location_type(self, location: str) -> int:
        mapping = {"Urban": 1, "Suburban": 2, "Rural": 3}
        return mapping.get(location, 0)

    def encode_commute_distance(self, commute: str) -> int:
        mapping = {"0-10mi": 1, "10-30mi": 2, "30-50mi": 3, "50+ mi": 4}
        return mapping.get(commute, 0)

    def _num_existing_personal_cards(self, customer_data: Dict) -> int:
        return int(
            self._to_bool(customer_data.get("has_personal_gold", False))
            + self._to_bool(customer_data.get("has_personal_platinum", False))
            + self._to_bool(customer_data.get("has_personal_green", False))
            + self._to_bool(customer_data.get("has_hilton_card", False))
            + self._to_bool(customer_data.get("has_delta_card", False))
        )

    def create_ml_features(self, customers_df: pd.DataFrame) -> pd.DataFrame:
        detector = self.detector
        feature_rows = []

        for _, customer in customers_df.iterrows():
            customer_dict = customer.to_dict()
            life_event_features = self.encode_life_events(customer_dict, detector)
            events = detector.detect_all_events(customer_dict)
            recommendation = detector.get_cross_sell_recommendation(events, customer_dict)

            current_tier = self.encode_card_tier(str(customer_dict.get("corporate_card_type", "")))
            recommended_product = recommendation.get("recommended_product", "Green Card")
            recommended_tier = 2 if recommended_product == "Platinum Card" else 1
            tier_gap = max(0, recommended_tier - current_tier)

            monthly_spend = self._to_float(customer_dict.get("corporate_monthly_spend", 0), 0.0)
            annual_spend = max(monthly_spend * 12.0, 1.0)
            estimated_income = self._to_float(customer_dict.get("estimated_income", 0), 0.0)
            num_cards = self._num_existing_personal_cards(customer_dict)

            travel_spend = self._pct_100(customer_dict.get("travel_spend_pct", 0))
            restaurants_spend = self._pct_100(customer_dict.get("restaurants_spend_pct", 0))
            groceries_spend = self._pct_100(customer_dict.get("groceries_spend_pct", 0))
            entertainment_spend = self._pct_100(customer_dict.get("entertainment_spend_pct", 0))
            personal_spend_ratio = self.calculate_personal_spend_ratio(customer_dict)

            # Proxies when timestamp-level spend data is unavailable.
            weekend_spend_ratio = min(100.0, restaurants_spend * 0.55 + entertainment_spend * 0.75 + personal_spend_ratio * 0.15)
            evening_spend_ratio = min(100.0, restaurants_spend * 0.65 + entertainment_spend * 0.85 + travel_spend * 0.10)

            if recommended_product == "Platinum Card":
                product_match = int(travel_spend > 20 or self._pct_100(customer_dict.get("luxury_retail_spend_pct", 0)) > 8)
            elif recommended_product == "Gold Card":
                product_match = int(restaurants_spend + groceries_spend > 22)
            else:
                product_match = int(personal_spend_ratio > 15)

            features = {
                # Spending pattern features
                "personal_spend_ratio": personal_spend_ratio,
                "spending_diversity": self.calculate_spending_diversity(customer_dict),
                "weekend_spend_ratio": weekend_spend_ratio,
                "evening_spend_ratio": evening_spend_ratio,
                # Life event features
                **life_event_features,
                # Product fit features
                "current_card_tier": current_tier,
                "card_tenure_months": int(self._to_float(customer_dict.get("tenure_months", 0))),
                "tier_upgrade_potential": tier_gap,
                "product_recommendation_match": product_match,
                # Demographic features
                "age_bracket_encoded": self.encode_age_bracket(str(customer_dict.get("age_bracket", ""))),
                "estimated_income": estimated_income,
                "income_to_spend_ratio": estimated_income / annual_spend,
                "location_type_encoded": self.encode_location_type(str(customer_dict.get("location_type", ""))),
                "commute_distance_encoded": self.encode_commute_distance(str(customer_dict.get("commute_distance", ""))),
                # Consumer product ownership
                "num_existing_personal_cards": num_cards,
                "has_any_personal_card": int(num_cards > 0),
                "product_saturation_score": num_cards / 5.0,
                # Keep important base MCC features
                "restaurants_spend_pct": restaurants_spend,
                "groceries_spend_pct": groceries_spend,
                "travel_spend_pct": travel_spend,
                "baby_stores_spend_pct": self._pct_100(customer_dict.get("baby_stores_spend_pct", 0)),
                "home_improvement_spend_pct": self._pct_100(customer_dict.get("home_improvement_spend_pct", 0)),
                "luxury_retail_spend_pct": self._pct_100(customer_dict.get("luxury_retail_spend_pct", 0)),
            }
            feature_rows.append(features)

        return pd.DataFrame(feature_rows)
