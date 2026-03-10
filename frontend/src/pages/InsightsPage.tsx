import React from 'react';
import { BarChart3 } from 'lucide-react';

export const InsightsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-gray-900 dark:text-dark-900">
          Model Insights
        </h2>
        <p className="text-gray-600 dark:text-dark-600 mt-1">
          XGBoost feature importance and model performance
        </p>
      </div>

      <div className="text-center py-12">
        <BarChart3 className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600 dark:text-dark-600">
          Model insights coming soon...
        </p>
      </div>
    </div>
  );
};
