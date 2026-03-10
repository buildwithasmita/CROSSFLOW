from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def simulate_random_targeting(df: pd.DataFrame) -> dict:
    """
    Simulate random targeting (current approach).
    - Send personal card offers to all GCS customers.
    - Observe overall adoption rate.
    """
    total_customers = len(df)
    actual_adoptions = int(df["adopted_personal_card"].sum())
    adoption_rate = actual_adoptions / total_customers if total_customers > 0 else 0.0

    cost_per_customer = 8
    total_cost = total_customers * cost_per_customer

    avg_annual_value = 1200
    total_revenue = actual_adoptions * avg_annual_value

    roi = ((total_revenue - total_cost) / total_cost) if total_cost > 0 else 0.0
    cpa = (total_cost / actual_adoptions) if actual_adoptions > 0 else 0.0

    return {
        "strategy": "Random Targeting",
        "customers_targeted": total_customers,
        "adoptions": actual_adoptions,
        "adoption_rate": adoption_rate,
        "marketing_cost": total_cost,
        "revenue": total_revenue,
        "profit": total_revenue - total_cost,
        "roi": roi,
        "cost_per_acquisition": cpa,
    }


def simulate_crossflow_targeting(
    df: pd.DataFrame,
    propensity_scores: np.ndarray,
    threshold: float = 0.75,
) -> dict:
    """
    Simulate CROSSFLOW smart targeting.
    - Target only high-propensity customers (score >= threshold).
    """
    high_propensity = propensity_scores >= threshold

    customers_targeted = int(high_propensity.sum())
    actual_adoptions = int(((high_propensity) & (df["adopted_personal_card"])).sum())
    adoption_rate = (
        (actual_adoptions / customers_targeted) if customers_targeted > 0 else 0.0
    )

    cost_per_customer = 8
    total_cost = customers_targeted * cost_per_customer

    avg_annual_value = 1200
    total_revenue = actual_adoptions * avg_annual_value

    roi = ((total_revenue - total_cost) / total_cost) if total_cost > 0 else 0.0
    cpa = (total_cost / actual_adoptions) if actual_adoptions > 0 else 0.0

    return {
        "strategy": "CROSSFLOW Targeting",
        "customers_targeted": customers_targeted,
        "adoptions": actual_adoptions,
        "adoption_rate": adoption_rate,
        "marketing_cost": total_cost,
        "revenue": total_revenue,
        "profit": total_revenue - total_cost,
        "roi": roi,
        "cost_per_acquisition": cpa,
        "customers_saved": len(df) - customers_targeted,
        "cost_saved": (len(df) - customers_targeted) * cost_per_customer,
    }


def compare_strategies(random_results: dict, crossflow_results: dict) -> pd.DataFrame:
    """Generate comparison dataframe."""
    random_customers = max(int(random_results["customers_targeted"]), 1)
    random_adoptions = max(int(random_results["adoptions"]), 1)
    random_adoption_rate = max(float(random_results["adoption_rate"]), 1e-9)
    random_marketing_cost = max(float(random_results["marketing_cost"]), 1e-9)
    random_revenue = max(float(random_results["revenue"]), 1e-9)
    random_profit = float(random_results["profit"])
    random_cpa = max(float(random_results["cost_per_acquisition"]), 1e-9)

    cross_customers = int(crossflow_results["customers_targeted"])
    cross_adoptions = int(crossflow_results["adoptions"])
    cross_adoption_rate = float(crossflow_results["adoption_rate"])
    cross_marketing_cost = float(crossflow_results["marketing_cost"])
    cross_revenue = float(crossflow_results["revenue"])
    cross_profit = float(crossflow_results["profit"])
    cross_cpa = float(crossflow_results["cost_per_acquisition"])

    comparison = pd.DataFrame(
        {
            "Metric": [
                "Customers Targeted",
                "Adoptions",
                "Adoption Rate",
                "Marketing Cost",
                "Revenue Generated",
                "Profit",
                "ROI",
                "Cost per Acquisition",
            ],
            "Random Targeting": [
                f"{random_customers:,}",
                f"{int(random_results['adoptions']):,}",
                f"{random_results['adoption_rate']:.1%}",
                f"${float(random_results['marketing_cost']):,.0f}",
                f"${float(random_results['revenue']):,.0f}",
                f"${float(random_results['profit']):,.0f}",
                f"{float(random_results['roi']):.1%}",
                f"${float(random_results['cost_per_acquisition']):.2f}",
            ],
            "CROSSFLOW Targeting": [
                f"{cross_customers:,}",
                f"{cross_adoptions:,}",
                f"{cross_adoption_rate:.1%}",
                f"${cross_marketing_cost:,.0f}",
                f"${cross_revenue:,.0f}",
                f"${cross_profit:,.0f}",
                f"{float(crossflow_results['roi']):.1%}",
                f"${cross_cpa:.2f}",
            ],
            "Improvement": [
                f"-{(1 - cross_customers / random_customers):.0%}",
                f"+{(cross_adoptions / random_adoptions - 1):.0%}",
                f"{(cross_adoption_rate / random_adoption_rate):.1f}x",
                f"-{(1 - cross_marketing_cost / random_marketing_cost):.0%}",
                f"+{(cross_revenue / random_revenue - 1):.0%}",
                f"+{(cross_profit / random_profit - 1):.0%}" if random_profit != 0 else "N/A",
                f"+{(float(crossflow_results['roi']) - float(random_results['roi'])):.0%}pp",
                f"-{(1 - cross_cpa / random_cpa):.0%}",
            ],
        }
    )

    return comparison


def visualize_comparison(random_results: dict, crossflow_results: dict) -> None:
    """Create visual comparison charts."""
    sns.set_style("whitegrid")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    adoption_data = [random_results["adoption_rate"], crossflow_results["adoption_rate"]]
    axes[0, 0].bar(["Random", "CROSSFLOW"], adoption_data, color=["#94a3b8", "#006FCF"])
    axes[0, 0].set_title("Adoption Rate", fontsize=14, fontweight="bold")
    axes[0, 0].set_ylabel("Rate")
    axes[0, 0].set_ylim(0, max(adoption_data) * 1.2 if max(adoption_data) > 0 else 1)
    for i, v in enumerate(adoption_data):
        axes[0, 0].text(i, v + 0.01, f"{v:.1%}", ha="center", fontweight="bold", fontsize=12)

    roi_data = [random_results["roi"], crossflow_results["roi"]]
    axes[0, 1].bar(["Random", "CROSSFLOW"], roi_data, color=["#94a3b8", "#f59e0b"])
    axes[0, 1].set_title("Return on Investment (ROI)", fontsize=14, fontweight="bold")
    axes[0, 1].set_ylabel("ROI")
    for i, v in enumerate(roi_data):
        axes[0, 1].text(i, v + 0.1, f"{v:.0%}", ha="center", fontweight="bold", fontsize=12)

    cpa_data = [random_results["cost_per_acquisition"], crossflow_results["cost_per_acquisition"]]
    axes[1, 0].bar(["Random", "CROSSFLOW"], cpa_data, color=["#ef4444", "#10b981"])
    axes[1, 0].set_title("Cost per Acquisition", fontsize=14, fontweight="bold")
    axes[1, 0].set_ylabel("Cost ($)")
    for i, v in enumerate(cpa_data):
        axes[1, 0].text(i, v + 0.5, f"${v:.2f}", ha="center", fontweight="bold", fontsize=12)

    profit_data = [random_results["profit"], crossflow_results["profit"]]
    axes[1, 1].bar(["Random", "CROSSFLOW"], profit_data, color=["#94a3b8", "#10b981"])
    axes[1, 1].set_title("Total Profit", fontsize=14, fontweight="bold")
    axes[1, 1].set_ylabel("Profit ($)")
    for i, v in enumerate(profit_data):
        axes[1, 1].text(i, v + 5000, f"${v:,.0f}", ha="center", fontweight="bold", fontsize=11)

    plt.tight_layout()
    plt.savefig("data/processed/baseline_comparison.png", dpi=150, bbox_inches="tight")
    plt.show()
