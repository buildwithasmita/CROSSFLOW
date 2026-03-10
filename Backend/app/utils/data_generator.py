from __future__ import annotations

from pathlib import Path
import uuid

import numpy as np
import pandas as pd


def _choose_non_owned_product(
    rng: np.random.Generator,
    owned: dict[str, bool],
    preferred: list[tuple[str, float]],
) -> str:
    available = [(product, weight) for product, weight in preferred if not owned.get(product, False)]
    if not available:
        return "None"

    products = [p for p, _ in available]
    weights = np.array([w for _, w in available], dtype=float)
    weights = weights / weights.sum()
    return str(rng.choice(products, p=weights))


def generate_crossflow_customers(
    n_customers: int = 5000,
    random_seed: int = 42,
) -> pd.DataFrame:
    """Generate synthetic GCS cardholder records for cross-sell propensity modeling."""
    rng = np.random.default_rng(random_seed)

    corporate_card_types = [
        "Corporate Gold",
        "Corporate Platinum",
        "Business Gold",
        "Business Platinum",
    ]
    employee_sizes = ["1-10", "11-50", "51-200", "201-1000", "1000+"]
    industries = [
        "Technology",
        "Healthcare",
        "Finance",
        "Manufacturing",
        "Retail",
        "Professional Services",
    ]
    age_brackets = ["25-30", "31-35", "36-40", "41-50", "51-60", "60+"]
    location_types = ["Urban", "Suburban", "Rural"]

    customer_ids = [str(uuid.uuid4()) for _ in range(n_customers)]
    has_corporate_card = np.ones(n_customers, dtype=bool)

    corporate_card_type = rng.choice(
        corporate_card_types,
        size=n_customers,
        p=[0.38, 0.19, 0.29, 0.14],
    )
    employee_size = rng.choice(employee_sizes, size=n_customers, p=[0.14, 0.25, 0.29, 0.21, 0.11])
    industry = rng.choice(industries, size=n_customers, p=[0.2, 0.14, 0.2, 0.16, 0.12, 0.18])
    age_bracket = rng.choice(age_brackets, size=n_customers, p=[0.13, 0.2, 0.2, 0.24, 0.16, 0.07])
    location_type = rng.choice(location_types, size=n_customers, p=[0.56, 0.34, 0.1])

    tenure_months = rng.integers(6, 121, size=n_customers)

    spend_base = rng.lognormal(mean=8.55, sigma=0.72, size=n_customers)
    card_multiplier = np.select(
        [
            corporate_card_type == "Corporate Platinum",
            corporate_card_type == "Business Platinum",
            corporate_card_type == "Corporate Gold",
        ],
        [1.42, 1.33, 1.12],
        default=1.0,
    )
    size_multiplier = np.select(
        [
            employee_size == "1000+",
            employee_size == "201-1000",
            employee_size == "51-200",
            employee_size == "11-50",
        ],
        [1.35, 1.2, 1.1, 1.0],
        default=0.9,
    )
    industry_multiplier = np.select(
        [industry == "Finance", industry == "Technology", industry == "Professional Services"],
        [1.15, 1.08, 1.05],
        default=1.0,
    )
    corporate_monthly_spend = np.clip(
        spend_base * card_multiplier * size_multiplier * industry_multiplier,
        500,
        50000,
    )

    base_personal_share = rng.beta(2.2, 6.5, size=n_customers)
    urban_boost = np.where(location_type == "Urban", 0.06, 0.0)
    age_boost = np.select(
        [age_bracket == "25-30", age_bracket == "31-35", age_bracket == "36-40"],
        [0.08, 0.07, 0.04],
        default=0.0,
    )
    tenure_penalty = np.where(tenure_months <= 12, -0.03, 0.0)
    personal_share = np.clip(base_personal_share + urban_boost + age_boost + tenure_penalty, 0.03, 0.65)

    category_names = [
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

    all_category_pcts = np.zeros((n_customers, len(category_names)))

    for i in range(n_customers):
        alphas = np.array([2.1, 1.9, 2.0, 1.2, 2.2, 0.45, 0.8, 0.9, 1.3], dtype=float)

        if corporate_card_type[i] in ("Corporate Platinum", "Business Platinum"):
            alphas[2] *= 1.6
            alphas[7] *= 1.5
        if age_bracket[i] in ("25-30", "31-35"):
            alphas[1] *= 1.25
            alphas[4] *= 1.35
            alphas[8] *= 1.2
        if location_type[i] == "Suburban":
            alphas[1] *= 1.22
            alphas[3] *= 1.3
            alphas[6] *= 1.25
        if location_type[i] == "Rural":
            alphas[3] *= 1.75
            alphas[6] *= 1.2
        if industry[i] == "Professional Services":
            alphas[2] *= 1.3
            alphas[0] *= 1.15
        if industry[i] == "Manufacturing":
            alphas[3] *= 1.15
            alphas[6] *= 1.2
        if age_bracket[i] == "31-35":
            alphas[5] *= 1.8

        mix = rng.dirichlet(alphas)
        all_category_pcts[i, :] = mix * personal_share[i]

    (
        restaurants_spend_pct,
        groceries_spend_pct,
        travel_spend_pct,
        gas_stations_spend_pct,
        online_shopping_spend_pct,
        baby_stores_spend_pct,
        home_improvement_spend_pct,
        luxury_retail_spend_pct,
        entertainment_spend_pct,
    ) = all_category_pcts.T

    baby_monthly_spend = corporate_monthly_spend * baby_stores_spend_pct
    home_monthly_spend = corporate_monthly_spend * home_improvement_spend_pct
    travel_monthly_spend = corporate_monthly_spend * travel_spend_pct
    grocery_monthly_spend = corporate_monthly_spend * groceries_spend_pct
    luxury_monthly_spend = corporate_monthly_spend * luxury_retail_spend_pct
    gas_monthly_spend = corporate_monthly_spend * gas_stations_spend_pct

    recent_baby_purchase = baby_monthly_spend * 3 > 500
    recent_home_purchase = home_monthly_spend * 6 > 2000

    flights_3m = rng.poisson(lam=np.clip((travel_monthly_spend * 3) / 430, 0.0, 25.0))
    frequent_traveler = flights_3m > 4

    high_grocery_spender = grocery_monthly_spend > 800
    luxury_shopper = luxury_monthly_spend > 1000

    base_income = corporate_monthly_spend * 12 * rng.uniform(1.6, 3.8, size=n_customers)
    income_card_boost = np.where(
        np.isin(corporate_card_type, ["Corporate Platinum", "Business Platinum"]),
        28000,
        0,
    )
    income_age_boost = np.select(
        [age_bracket == "41-50", age_bracket == "51-60", age_bracket == "60+"],
        [12000, 20000, 23000],
        default=0,
    )
    estimated_income = np.clip(base_income + income_card_boost + income_age_boost, 40000, 500000)

    commute_distance = np.full(n_customers, "0-10mi", dtype=object)
    commute_distance[(gas_monthly_spend >= 180) & (gas_monthly_spend < 360)] = "10-30mi"
    commute_distance[(gas_monthly_spend >= 360) & (gas_monthly_spend < 620)] = "30-50mi"
    commute_distance[gas_monthly_spend >= 620] = "50+ mi"
    commute_distance[(location_type == "Urban") & (gas_monthly_spend < 260)] = "0-10mi"

    has_personal_gold = rng.random(n_customers) < 0.05
    has_personal_platinum = rng.random(n_customers) < 0.03
    has_personal_green = rng.random(n_customers) < 0.02
    has_hilton_card = rng.random(n_customers) < 0.04
    has_delta_card = rng.random(n_customers) < 0.03

    high_income_mask = estimated_income > 180000
    has_personal_platinum = np.where(
        high_income_mask & (rng.random(n_customers) < 0.07),
        True,
        has_personal_platinum,
    )
    has_delta_card = np.where(
        (travel_spend_pct > 0.22) & (rng.random(n_customers) < 0.08),
        True,
        has_delta_card,
    )

    existing_personal_cards_count = (
        has_personal_gold.astype(int)
        + has_personal_platinum.astype(int)
        + has_personal_green.astype(int)
        + has_hilton_card.astype(int)
        + has_delta_card.astype(int)
    )

    pattern = np.full(n_customers, "medium_general", dtype=object)
    base_propensity = np.full(n_customers, 0.40, dtype=float)
    recommended_product = np.full(n_customers, "Green", dtype=object)

    new_parent_mask = (
        recent_baby_purchase
        & high_grocery_spender
        & np.isin(age_bracket, ["25-30", "31-35"])
    )
    frequent_traveler_mask = (
        frequent_traveler
        & (travel_spend_pct > 0.30)
        & (corporate_card_type == "Corporate Gold")
    )
    new_homeowner_mask = (
        recent_home_purchase
        & (home_improvement_spend_pct > 0.15)
        & (estimated_income > 100000)
    )
    luxury_spender_mask = (
        luxury_shopper
        & (estimated_income > 150000)
        & (corporate_card_type == "Corporate Platinum")
    )

    high_mask = new_parent_mask | frequent_traveler_mask | new_homeowner_mask | luxury_spender_mask

    pure_business_mask = personal_share < 0.10
    low_income_mask = estimated_income < 60000
    multi_card_mask = existing_personal_cards_count >= 2
    too_new_mask = tenure_months <= 9
    low_pattern_mask = (~high_mask) & (pure_business_mask | low_income_mask | multi_card_mask | too_new_mask)

    pattern[new_parent_mask] = "high_new_parent"
    base_propensity[new_parent_mask] = 0.85
    recommended_product[new_parent_mask] = "Gold"

    pattern[frequent_traveler_mask] = "high_frequent_traveler"
    base_propensity[frequent_traveler_mask] = 0.75
    recommended_product[frequent_traveler_mask] = "Platinum"

    pattern[new_homeowner_mask] = "high_new_homeowner"
    base_propensity[new_homeowner_mask] = 0.70
    recommended_product[new_homeowner_mask] = "Gold"

    pattern[luxury_spender_mask] = "high_luxury_spender"
    base_propensity[luxury_spender_mask] = 0.80
    recommended_product[luxury_spender_mask] = "Platinum"

    pattern[low_pattern_mask] = "low_propensity"
    base_propensity[low_pattern_mask] = 0.10
    recommended_product[low_pattern_mask] = "None"

    propensity = base_propensity.copy()
    propensity += np.where(personal_share > 0.35, 0.06, 0.0)
    propensity -= np.where(existing_personal_cards_count >= 2, 0.12, 0.0)
    propensity -= np.where(estimated_income < 60000, 0.08, 0.0)
    propensity += np.where(tenure_months > 48, 0.04, 0.0)
    propensity += np.where((travel_spend_pct > 0.2) & (~frequent_traveler), 0.03, 0.0)
    propensity = np.clip(propensity, 0.01, 0.97)

    target_adoption = 0.30
    scale = target_adoption / propensity.mean()
    propensity_score_actual = np.clip(propensity * scale, 0.01, 0.98)

    adopted_personal_card = rng.random(n_customers) < propensity_score_actual

    adopted_product = np.full(n_customers, "None", dtype=object)
    months_to_adoption = np.zeros(n_customers, dtype=int)

    for i in range(n_customers):
        owned = {
            "Gold": bool(has_personal_gold[i]),
            "Platinum": bool(has_personal_platinum[i]),
            "Green": bool(has_personal_green[i]),
            "Hilton": bool(has_hilton_card[i]),
            "Delta": bool(has_delta_card[i]),
        }

        if not adopted_personal_card[i]:
            continue

        if recommended_product[i] == "Gold":
            product = _choose_non_owned_product(
                rng,
                owned,
                [("Gold", 0.74), ("Green", 0.16), ("Hilton", 0.06), ("Delta", 0.04)],
            )
        elif recommended_product[i] == "Platinum":
            product = _choose_non_owned_product(
                rng,
                owned,
                [("Platinum", 0.7), ("Gold", 0.16), ("Delta", 0.08), ("Hilton", 0.06)],
            )
        elif pattern[i] == "medium_general":
            if travel_spend_pct[i] > 0.2:
                product = _choose_non_owned_product(
                    rng,
                    owned,
                    [("Delta", 0.35), ("Platinum", 0.28), ("Hilton", 0.2), ("Gold", 0.1), ("Green", 0.07)],
                )
            elif groceries_spend_pct[i] > 0.14:
                product = _choose_non_owned_product(
                    rng,
                    owned,
                    [("Gold", 0.48), ("Green", 0.24), ("Hilton", 0.16), ("Delta", 0.07), ("Platinum", 0.05)],
                )
            else:
                product = _choose_non_owned_product(
                    rng,
                    owned,
                    [("Green", 0.38), ("Gold", 0.32), ("Hilton", 0.15), ("Delta", 0.1), ("Platinum", 0.05)],
                )
        else:
            product = _choose_non_owned_product(
                rng,
                owned,
                [("Green", 0.45), ("Hilton", 0.22), ("Delta", 0.18), ("Gold", 0.1), ("Platinum", 0.05)],
            )

        adopted_product[i] = product

        if pattern[i].startswith("high"):
            months_to_adoption[i] = int(np.clip(rng.normal(3.8, 1.8), 1, 12))
        elif pattern[i] == "medium_general":
            months_to_adoption[i] = int(np.clip(rng.normal(6.5, 2.3), 1, 12))
        else:
            months_to_adoption[i] = int(np.clip(rng.normal(8.0, 2.4), 1, 12))

        if adopted_product[i] == "None":
            adopted_personal_card[i] = False
            months_to_adoption[i] = 0

    adopted_product = np.where(adopted_personal_card, adopted_product, "None")

    df = pd.DataFrame(
        {
            "customer_id": customer_ids,
            "has_corporate_card": has_corporate_card,
            "corporate_card_type": corporate_card_type,
            "tenure_months": tenure_months,
            "corporate_monthly_spend": np.round(corporate_monthly_spend, 2),
            "employee_size": employee_size,
            "industry": industry,
            "restaurants_spend_pct": np.round(restaurants_spend_pct, 4),
            "groceries_spend_pct": np.round(groceries_spend_pct, 4),
            "travel_spend_pct": np.round(travel_spend_pct, 4),
            "gas_stations_spend_pct": np.round(gas_stations_spend_pct, 4),
            "online_shopping_spend_pct": np.round(online_shopping_spend_pct, 4),
            "baby_stores_spend_pct": np.round(baby_stores_spend_pct, 4),
            "home_improvement_spend_pct": np.round(home_improvement_spend_pct, 4),
            "luxury_retail_spend_pct": np.round(luxury_retail_spend_pct, 4),
            "entertainment_spend_pct": np.round(entertainment_spend_pct, 4),
            "recent_baby_purchase": recent_baby_purchase,
            "recent_home_purchase": recent_home_purchase,
            "frequent_traveler": frequent_traveler,
            "high_grocery_spender": high_grocery_spender,
            "luxury_shopper": luxury_shopper,
            "age_bracket": age_bracket,
            "estimated_income": np.round(estimated_income, 2),
            "location_type": location_type,
            "commute_distance": commute_distance,
            "has_personal_gold": has_personal_gold,
            "has_personal_platinum": has_personal_platinum,
            "has_personal_green": has_personal_green,
            "has_hilton_card": has_hilton_card,
            "has_delta_card": has_delta_card,
            "adopted_personal_card": adopted_personal_card,
            "adopted_product": adopted_product,
            "months_to_adoption": months_to_adoption,
            "propensity_score_actual": np.round(propensity_score_actual, 4),
        }
    )

    output_path = Path(__file__).resolve().parents[2] / "data" / "raw" / "gcs_customers.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    print(f"Generated {len(df):,} synthetic GCS customers")
    print(f"Saved dataset to: {output_path}")
    print("\nAdoption rate by life event:")
    for event_col in [
        "recent_baby_purchase",
        "recent_home_purchase",
        "frequent_traveler",
        "high_grocery_spender",
        "luxury_shopper",
    ]:
        event_rate = df.loc[df[event_col], "adopted_personal_card"].mean()
        print(f"- {event_col}: {event_rate:.2%} ({int(df[event_col].sum()):,} customers)")

    print("\nAdoption rate by age bracket:")
    age_summary = (
        df.groupby("age_bracket", observed=False)["adopted_personal_card"]
        .mean()
        .sort_index()
    )
    for age, rate in age_summary.items():
        print(f"- {age}: {rate:.2%}")

    adopted_non_none = df.loc[df["adopted_personal_card"], "adopted_product"]
    most_common_product = adopted_non_none.value_counts().idxmax() if not adopted_non_none.empty else "None"
    print(f"\nMost common cross-sell product: {most_common_product}")

    print("\nAverage propensity by pattern:")
    pattern_summary = pd.DataFrame(
        {
            "pattern": pattern,
            "propensity_score_actual": propensity_score_actual,
        }
    ).groupby("pattern", observed=False)["propensity_score_actual"].mean()
    for p_name, avg_prop in pattern_summary.sort_values(ascending=False).items():
        print(f"- {p_name}: {avg_prop:.3f}")

    return df


if __name__ == "__main__":
    generate_crossflow_customers()
