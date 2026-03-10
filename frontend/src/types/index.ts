// Customer types
export interface GCSCustomer {
  customer_id: string;
  has_corporate_card: boolean;
  corporate_card_type: string;
  tenure_months: number;
  corporate_monthly_spend: number;
  employee_size: string;
  industry: string;
  
  // Spending patterns
  restaurants_spend_pct: number;
  groceries_spend_pct: number;
  travel_spend_pct: number;
  gas_stations_spend_pct: number;
  online_shopping_spend_pct: number;
  baby_stores_spend_pct: number;
  home_improvement_spend_pct: number;
  luxury_retail_spend_pct: number;
  entertainment_spend_pct: number;
  
  // Life events
  recent_baby_purchase: boolean;
  recent_home_purchase: boolean;
  frequent_traveler: boolean;
  high_grocery_spender: boolean;
  luxury_shopper: boolean;
  
  // Demographics
  age_bracket: string;
  estimated_income: number;
  location_type: string;
  commute_distance: string;
  
  // Product ownership
  has_personal_gold: boolean;
  has_personal_platinum: boolean;
  has_personal_green: boolean;
  has_hilton_card: boolean;
  has_delta_card: boolean;
}

export interface LifeEvent {
  event: string;
  confidence: number;
  detected: boolean;
  signals: string[];
  recommended_product: string;
  recommendation_reason: string;
}

export interface PropensityScore {
  customer_id: string;
  propensity_score: number;
  probability: number;
  tier: 'High' | 'Medium' | 'Low';
  expected_conversion: string;
  confidence: string;
  life_events: LifeEvent[];
  recommended_product: string;
  recommendation_reason: string;
  expected_annual_value: number;
  top_positive_factors: Array<{
    feature: string;
    contribution: number;
    direction: string;
  }>;
  top_negative_factors: Array<{
    feature: string;
    contribution: number;
    direction: string;
  }>;
  explanation: string;
}

export interface CustomerWithScore extends GCSCustomer {
  propensity_score: number;
  tier: 'High' | 'Medium' | 'Low';
  recommended_product: string;
  life_events: LifeEvent[];
  expected_annual_value: number;
}

export type Theme = 'light' | 'dark';
