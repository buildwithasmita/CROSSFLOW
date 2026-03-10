import React, { useState } from 'react';
import { Users, TrendingUp, Target, DollarSign } from 'lucide-react';
import { MetricsCard } from '../components/dashboard/MetricsCard';
import { CustomerList } from '../components/dashboard/CustomerList';
import { PropensityDistribution } from '../components/dashboard/PropensityDistribution';
import { LifeEventCard } from '../components/dashboard/LifeEventCard';
import { Button } from '../components/common/Button';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { getSampleCustomers, scoreBatchCustomers } from '../services/api';
import { CustomerWithScore } from '../types';

export const DashboardPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [customers, setCustomers] = useState<CustomerWithScore[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState<CustomerWithScore | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState({
    total: 0,
    avgScore: 0,
    highCount: 0,
    mediumCount: 0,
    lowCount: 0,
    totalValue: 0
  });

  const loadCustomers = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Step 1: Fetch sample customers from backend
      const sampleCustomers = await getSampleCustomers(50);
      
      // Step 2: Score them via backend API
      const scoreResponse = await scoreBatchCustomers(sampleCustomers, true);
      
      // Step 3: Combine customer data with scores
      const enrichedCustomers: CustomerWithScore[] = scoreResponse.results.map((score, idx) => ({
        ...sampleCustomers[idx],
        propensity_score: score.propensity_score,
        tier: score.tier,
        recommended_product: score.recommended_product,
        life_events: score.life_events,
        expected_annual_value: score.expected_annual_value
      }));
      
      setCustomers(enrichedCustomers);
      
      // Step 4: Calculate summary statistics
      const scores = enrichedCustomers.map(c => c.propensity_score);
      const totalValue = enrichedCustomers.reduce((sum, c) => sum + c.expected_annual_value, 0);
      
      setSummary({
        total: enrichedCustomers.length,
        avgScore: scores.reduce((a, b) => a + b, 0) / scores.length,
        highCount: enrichedCustomers.filter(c => c.tier === 'High').length,
        mediumCount: enrichedCustomers.filter(c => c.tier === 'Medium').length,
        lowCount: enrichedCustomers.filter(c => c.tier === 'Low').length,
        totalValue: totalValue
      });
      
    } catch (err: any) {
      console.error('Failed to load customers:', err);
      setError(
        err.message?.includes('Network Error') 
          ? 'Backend API not running! Start backend with: cd backend && uvicorn app.main:app --reload' 
          : 'Failed to load data. Check console for details.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-gray-900 dark:text-dark-900">
            Cross-Sell Dashboard
          </h2>
          <p className="text-gray-600 dark:text-dark-600 mt-1">
            AI-powered propensity scoring for GCS corporate cardholders
          </p>
        </div>
        <Button onClick={loadCustomers} loading={loading}>
          {customers.length > 0 ? '🔄 Refresh Data' : '🚀 Analyze Customers'}
        </Button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-danger-50 dark:bg-danger-900/20 border border-danger-500 rounded-lg p-4">
          <p className="text-danger-700 dark:text-danger-400 font-semibold">{error}</p>
          <p className="text-sm text-gray-600 dark:text-dark-600 mt-2">
            Make sure backend is running: <code className="bg-gray-800 text-white px-2 py-1 rounded">cd backend && uvicorn app.main:app --reload</code>
          </p>
        </div>
      )}

      {loading ? (
        <LoadingSpinner size="lg" text="Analyzing customers with XGBoost..." />
      ) : customers.length > 0 ? (
        <>
          {/* Metrics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <MetricsCard
              title="Total Customers"
              value={summary.total}
              icon={Users}
              color="blue"
            />
            <MetricsCard
              title="Average Propensity"
              value={`${summary.avgScore.toFixed(1)}/100`}
              icon={Target}
              color="gold"
            />
            <MetricsCard
              title="High Propensity"
              value={summary.highCount}
              subtitle={`${((summary.highCount / summary.total) * 100).toFixed(0)}% of total`}
              icon={TrendingUp}
              color="green"
              trend={{ value: 12, isPositive: true }}
            />
            <MetricsCard
              title="Expected Value"
              value={`$${(summary.totalValue / 1000).toFixed(0)}K`}
              subtitle="Annual revenue potential"
              icon={DollarSign}
              color="gold"
            />
          </div>

          {/* Main Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Customer List (2/3 width) */}
            <div className="lg:col-span-2">
              <CustomerList 
                customers={customers}
                onCustomerClick={setSelectedCustomer}
              />
            </div>

            {/* Side Panel (1/3 width) */}
            <div className="space-y-6">
              {/* Selected Customer Life Events */}
              {selectedCustomer ? (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-dark-900 mb-3">
                    Life Events: {selectedCustomer.customer_id}
                  </h3>
                  <LifeEventCard lifeEvents={selectedCustomer.life_events || []} />
                </div>
              ) : (
                <div className="card text-center py-8">
                  <p className="text-gray-500 dark:text-dark-500">
                    Click a customer to view life events
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Score Distribution */}
          <PropensityDistribution scores={customers.map(c => c.propensity_score)} />
        </>
      ) : (
        <div className="text-center py-12">
          <Users className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 dark:text-dark-600 mb-4">
            No customers analyzed yet. Click "Analyze Customers" to get started.
          </p>
        </div>
      )}
    </div>
  );
};
