from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd


class LifeEventDetector:
    """Detect life events from corporate card spending signals and recommend cross-sell products."""

    def _to_bool(self, value: object) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, np.integer)):
            return value != 0
        if isinstance(value, str):
            return value.strip().lower() in {"true", "1", "yes", "y"}
        return bool(value)

    def _to_float(self, value: object, default: float = 0.0) -> float:
        try:
            if value is None or (isinstance(value, float) and np.isnan(value)):
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    def _pct(self, value: object) -> float:
        """Normalize spend pct field to 0-100 scale."""
        raw = self._to_float(value, 0.0)
        if raw <= 1.0:
            return raw * 100.0
        return raw

    def detect_new_parent(self, customer_data: Dict) -> Dict:
        baby_store_spend = self._pct(customer_data.get("baby_stores_spend_pct", 0))
        grocery_spend = self._pct(customer_data.get("groceries_spend_pct", 0))
        recent_baby_purchase = self._to_bool(customer_data.get("recent_baby_purchase", False))
        high_grocery_spender = self._to_bool(customer_data.get("high_grocery_spender", False))
        age_bracket = str(customer_data.get("age_bracket", ""))

        new_parent_score = 0
        signals_detected: List[str] = []

        if recent_baby_purchase:
            new_parent_score += 40
            signals_detected.append("Recent baby store purchases ($500+ in 3 months)")

        if baby_store_spend > 5:
            new_parent_score += 30
            signals_detected.append(f"High baby store spend ({baby_store_spend:.1f}% of total)")

        if grocery_spend > 0 and high_grocery_spender:
            new_parent_score += 20
            signals_detected.append("High grocery spending (>$800/month)")

        if age_bracket in ["25-30", "31-35"]:
            new_parent_score += 10
            signals_detected.append("Prime parenting age (25-35)")

        return {
            "event": "New Parent",
            "confidence": min(new_parent_score, 100),
            "detected": new_parent_score >= 50,
            "signals": signals_detected,
            "recommended_product": "Gold Card",
            "recommendation_reason": (
                "4x points on groceries (avg $800/month) + 4x dining = "
                "$38/month in points ($456/year value!)"
            ),
        }

    def detect_new_homeowner(self, customer_data: Dict) -> Dict:
        home_improvement_spend = self._pct(customer_data.get("home_improvement_spend_pct", 0))
        online_shopping_spend = self._pct(customer_data.get("online_shopping_spend_pct", 0))
        gas_spend = self._pct(customer_data.get("gas_stations_spend_pct", 0))
        recent_home_purchase = self._to_bool(customer_data.get("recent_home_purchase", False))
        estimated_income = self._to_float(customer_data.get("estimated_income", 0))
        monthly_spend = self._to_float(customer_data.get("corporate_monthly_spend", 0))

        score = 0
        signals_detected: List[str] = []

        if recent_home_purchase:
            score += 40
            signals_detected.append("Recent home improvement purchases (>$2,000 in 6 months)")

        if home_improvement_spend > 15:
            score += 30
            signals_detected.append(
                f"Home improvement category spike ({home_improvement_spend:.1f}% of total)"
            )

        # Proxy furniture/appliance signal via high online + home improvement overlap.
        if online_shopping_spend > 12 and home_improvement_spend > 8:
            score += 15
            signals_detected.append("Furniture/appliance purchase pattern (online + home improvement)")

        # Proxy one-time large transactions via high monthly spend concentrated in home category.
        home_monthly_amount = monthly_spend * (home_improvement_spend / 100.0)
        if home_monthly_amount > 1500:
            score += 10
            signals_detected.append("Large home-category ticket size detected")

        if estimated_income > 100000:
            score += 10
            signals_detected.append("Income supports recent home setup spending")

        if gas_spend > 10:
            score += 5
            signals_detected.append("Commute/gas increase consistent with new home move")

        return {
            "event": "New Homeowner",
            "confidence": min(score, 100),
            "detected": score >= 50,
            "signals": signals_detected,
            "recommended_product": "Gold Card",
            "recommendation_reason": (
                "New-home spending mix favors everyday categories; Gold maximizes "
                "ongoing groceries, dining, and home-related run-rate."
            ),
        }

    def detect_travel_enthusiast(self, customer_data: Dict) -> Dict:
        travel_spend = self._pct(customer_data.get("travel_spend_pct", 0))
        restaurants_spend = self._pct(customer_data.get("restaurants_spend_pct", 0))
        frequent_traveler = self._to_bool(customer_data.get("frequent_traveler", False))
        card_type = str(customer_data.get("corporate_card_type", ""))
        location_type = str(customer_data.get("location_type", ""))
        monthly_spend = self._to_float(customer_data.get("corporate_monthly_spend", 0))

        score = 0
        signals_detected: List[str] = []

        if frequent_traveler:
            score += 35
            signals_detected.append("Frequent traveler flag (>4 flights in 3 months)")

        if travel_spend > 20:
            score += 30
            signals_detected.append(f"High airline/hotel spend ({travel_spend:.1f}% of total)")

        # Proxy hotel + dining away-from-home pattern.
        if travel_spend > 15 and restaurants_spend > 10:
            score += 10
            signals_detected.append("Travel + dining mix suggests recurring trip behavior")

        # Proxy international profile from premium corporate travel behavior.
        if card_type in {"Corporate Platinum", "Business Platinum"} and travel_spend > 18:
            score += 15
            signals_detected.append("Premium corporate card + high travel indicates international propensity")

        if location_type == "Urban" and monthly_spend > 12000:
            score += 5
            signals_detected.append("Urban high-spend profile aligned to frequent travel")

        return {
            "event": "Travel Enthusiast",
            "confidence": min(score, 100),
            "detected": score >= 50,
            "signals": signals_detected,
            "recommended_product": "Platinum Card",
            "recommendation_reason": (
                "Travel-heavy behavior aligns with lounge access, hotel status, "
                "and annual travel credits from Platinum."
            ),
        }

    def detect_lifestyle_upgrade(self, customer_data: Dict) -> Dict:
        luxury_spend = self._pct(customer_data.get("luxury_retail_spend_pct", 0))
        restaurants_spend = self._pct(customer_data.get("restaurants_spend_pct", 0))
        entertainment_spend = self._pct(customer_data.get("entertainment_spend_pct", 0))
        luxury_shopper = self._to_bool(customer_data.get("luxury_shopper", False))
        estimated_income = self._to_float(customer_data.get("estimated_income", 0))
        monthly_spend = self._to_float(customer_data.get("corporate_monthly_spend", 0))
        card_type = str(customer_data.get("corporate_card_type", ""))

        score = 0
        signals_detected: List[str] = []

        if luxury_shopper:
            score += 35
            signals_detected.append("Luxury shopper flag (>$1,000/month luxury retail)")

        if luxury_spend > 8:
            score += 25
            signals_detected.append(f"Elevated luxury retail share ({luxury_spend:.1f}% of total)")

        if restaurants_spend > 14 and entertainment_spend > 8:
            score += 15
            signals_detected.append("Fine-dining + entertainment profile increasing")

        # Income vs spend mismatch can signal unmet premium product fit.
        annual_corporate_spend = monthly_spend * 12
        if estimated_income > 150000 and annual_corporate_spend > (estimated_income * 0.18):
            score += 15
            signals_detected.append("High income with premium spend intensity mismatch")

        if card_type in {"Corporate Platinum", "Business Platinum"}:
            score += 10
            signals_detected.append("Corporate premium cardholder likely to convert to premium personal")

        return {
            "event": "Lifestyle Upgrade",
            "confidence": min(score, 100),
            "detected": score >= 50,
            "signals": signals_detected,
            "recommended_product": "Platinum Card",
            "recommendation_reason": (
                "Premium lifestyle signals indicate strong fit for Platinum benefits "
                "and prestige positioning."
            ),
        }

    def detect_all_events(self, customer_data: Dict) -> List[Dict]:
        events: List[Dict] = []

        new_parent = self.detect_new_parent(customer_data)
        if new_parent["detected"]:
            events.append(new_parent)

        new_home = self.detect_new_homeowner(customer_data)
        if new_home["detected"]:
            events.append(new_home)

        travel = self.detect_travel_enthusiast(customer_data)
        if travel["detected"]:
            events.append(travel)

        lifestyle = self.detect_lifestyle_upgrade(customer_data)
        if lifestyle["detected"]:
            events.append(lifestyle)

        events.sort(key=lambda x: x["confidence"], reverse=True)
        return events

    def calculate_annual_value(self, product: str, customer_data: Dict) -> float:
        """Calculate expected annual value (fee + incremental spend)."""
        fees = {
            "Gold Card": 250,
            "Platinum Card": 695,
            "Green Card": 150,
            "Delta Card": 99,
            "Hilton Card": 95,
        }

        avg_personal_spend = {
            "Gold Card": 18000,
            "Platinum Card": 36000,
            "Green Card": 12000,
            "Delta Card": 15000,
            "Hilton Card": 12000,
        }

        revenue_per_dollar = 0.025
        fee = fees.get(product, 150)
        spend = avg_personal_spend.get(product, 12000)
        annual_value = fee + (spend * revenue_per_dollar)
        return float(annual_value)

    def get_cross_sell_recommendation(self, events: List[Dict], customer_data: Dict) -> Dict:
        travel_spend = self._pct(customer_data.get("travel_spend_pct", 0))
        estimated_income = self._to_float(customer_data.get("estimated_income", 0))

        if events:
            primary_event = events[0]
            product = primary_event["recommended_product"]
            annual_value = self.calculate_annual_value(product, customer_data)
            return {
                "recommended_product": product,
                "confidence": primary_event["confidence"],
                "reason": (
                    f"Life event: {primary_event['event']}. "
                    f"{primary_event['recommendation_reason']}"
                ),
                "expected_adoption_rate": "75%",
                "expected_annual_value": f"${annual_value:,.0f}",
            }

        if travel_spend > 25:
            annual_value = self.calculate_annual_value("Platinum Card", customer_data)
            return {
                "recommended_product": "Platinum Card",
                "confidence": 65,
                "reason": (
                    "High travel spending (25%+ of total). "
                    "Platinum offers lounge access + $200 airline credit."
                ),
                "expected_adoption_rate": "45%",
                "expected_annual_value": f"${annual_value:,.0f}",
            }

        if estimated_income > 100000:
            annual_value = self.calculate_annual_value("Gold Card", customer_data)
            return {
                "recommended_product": "Gold Card",
                "confidence": 40,
                "reason": (
                    "High income, general personal spending on corporate card. "
                    "Gold offers 4x dining + groceries."
                ),
                "expected_adoption_rate": "30%",
                "expected_annual_value": f"${annual_value:,.0f}",
            }

        annual_value = self.calculate_annual_value("Green Card", customer_data)
        return {
            "recommended_product": "Green Card",
            "confidence": 20,
            "reason": "Entry-level option for general rewards.",
            "expected_adoption_rate": "15%",
            "expected_annual_value": f"${annual_value:,.0f}",
        }
