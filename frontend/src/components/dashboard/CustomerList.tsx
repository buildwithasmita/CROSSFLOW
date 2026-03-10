import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Search, Sparkles } from 'lucide-react';
import { CustomerWithScore } from '../../types';
import { Card } from '../common/Card';

interface CustomerListProps {
  customers: CustomerWithScore[];
  onCustomerClick?: (customer: CustomerWithScore) => void;
}

export const CustomerList: React.FC<CustomerListProps> = ({ customers, onCustomerClick }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'score' | 'name'>('score');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [filterTier, setFilterTier] = useState<'all' | 'High' | 'Medium' | 'Low'>('all');

  // Filter and sort
  const filteredCustomers = customers
    .filter(customer => {
      const matchesSearch = customer.customer_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           customer.industry.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesTier = filterTier === 'all' || customer.tier === filterTier;
      return matchesSearch && matchesTier;
    })
    .sort((a, b) => {
      const multiplier = sortOrder === 'asc' ? 1 : -1;
      if (sortBy === 'score') {
        return (a.propensity_score - b.propensity_score) * multiplier;
      }
      return a.customer_id.localeCompare(b.customer_id) * multiplier;
    });

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'High': return 'tier-high';
      case 'Medium': return 'tier-medium';
      case 'Low': return 'tier-low';
      default: return 'bg-gray-300 text-gray-700';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 75) return 'text-success-600 dark:text-success-400';
    if (score >= 50) return 'text-warning-600 dark:text-warning-400';
    return 'text-gray-600 dark:text-gray-400';
  };

  return (
    <Card>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold text-gray-900 dark:text-dark-900">
          GCS Customers ({filteredCustomers.length})
        </h3>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search by ID or industry..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-3 rounded-lg bg-gray-50 dark:bg-dark-100 border-2 border-gray-200 dark:border-dark-200 focus:border-amex-500 focus:ring-2 focus:ring-amex-500/20 transition-all duration-200"
          />
        </div>
        
        <select
          value={filterTier}
          onChange={(e) => setFilterTier(e.target.value as any)}
          className="px-4 py-3 rounded-lg bg-gray-50 dark:bg-dark-100 border-2 border-gray-200 dark:border-dark-200 focus:border-amex-500 transition-all duration-200 w-full sm:w-40"
        >
          <option value="all">All Tiers</option>
          <option value="High">🔥 High</option>
          <option value="Medium">🟡 Medium</option>
          <option value="Low">❄️ Low</option>
        </select>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b-2 border-gray-200 dark:border-dark-200">
              <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-dark-700">
                <button 
                  onClick={() => {
                    setSortBy('name');
                    setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
                  }}
                  className="flex items-center space-x-1 hover:text-amex-500"
                >
                  <span>Customer ID</span>
                  {sortBy === 'name' && (sortOrder === 'asc' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />)}
                </button>
              </th>
              <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-dark-700">Industry</th>
              <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-dark-700">Corporate Card</th>
              <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-dark-700">
                <button 
                  onClick={() => {
                    setSortBy('score');
                    setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
                  }}
                  className="flex items-center space-x-1 hover:text-amex-500"
                >
                  <span>Propensity Score</span>
                  {sortBy === 'score' && (sortOrder === 'asc' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />)}
                </button>
              </th>
              <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-dark-700">Tier</th>
              <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-dark-700">Recommended Product</th>
              <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-dark-700">Life Events</th>
            </tr>
          </thead>
          <tbody>
            {filteredCustomers.map((customer, idx) => (
              <tr 
                key={idx}
                onClick={() => onCustomerClick?.(customer)}
                className="border-b border-gray-100 dark:border-dark-200 hover:bg-gray-50 dark:hover:bg-dark-200 cursor-pointer transition-colors"
              >
                <td className="py-4 px-4 font-medium text-gray-900 dark:text-dark-900">
                  {customer.customer_id}
                </td>
                <td className="py-4 px-4 text-gray-600 dark:text-dark-600">
                  {customer.industry}
                </td>
                <td className="py-4 px-4 text-gray-600 dark:text-dark-600">
                  {customer.corporate_card_type}
                </td>
                <td className="py-4 px-4">
                  <span className={`text-2xl font-bold ${getScoreColor(customer.propensity_score)}`}>
                    {customer.propensity_score}
                  </span>
                  <span className="text-gray-500 dark:text-dark-500">/100</span>
                </td>
                <td className="py-4 px-4">
                  <span className={`${getTierColor(customer.tier)} px-3 py-1 rounded-full text-sm font-semibold`}>
                    {customer.tier}
                  </span>
                </td>
                <td className="py-4 px-4 text-gray-900 dark:text-dark-900 font-medium">
                  {customer.recommended_product}
                </td>
                <td className="py-4 px-4">
                  {customer.life_events && customer.life_events.length > 0 ? (
                    <div className="flex items-center space-x-1">
                      <Sparkles className="w-4 h-4 text-gold-500" />
                      <span className="text-sm text-gold-600 dark:text-gold-400 font-medium">
                        {customer.life_events.length} event{customer.life_events.length > 1 ? 's' : ''}
                      </span>
                    </div>
                  ) : (
                    <span className="text-sm text-gray-400">None</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filteredCustomers.length === 0 && (
        <div className="text-center py-12 text-gray-500 dark:text-dark-500">
          No customers found matching your criteria
        </div>
      )}
    </Card>
  );
};
