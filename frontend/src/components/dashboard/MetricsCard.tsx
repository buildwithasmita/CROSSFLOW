import React from 'react';
import { LucideIcon } from 'lucide-react';
import { Card } from '../common/Card';

interface MetricsCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  color?: 'blue' | 'gold' | 'green' | 'orange' | 'red';
}

export const MetricsCard: React.FC<MetricsCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  color = 'blue',
}) => {
  const colorClasses = {
    blue: 'text-amex-500 bg-amex-50 dark:bg-amex-900/20',
    gold: 'text-gold-500 bg-gold-50 dark:bg-gold-900/20',
    green: 'text-success-500 bg-green-50 dark:bg-green-900/20',
    orange: 'text-warning-500 bg-orange-50 dark:bg-orange-900/20',
    red: 'text-danger-500 bg-red-50 dark:bg-red-900/20',
  };

  return (
    <Card>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600 dark:text-dark-600">
            {title}
          </p>
          <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-dark-900">
            {value}
          </p>
          {subtitle && (
            <p className="mt-1 text-sm text-gray-500 dark:text-dark-500">
              {subtitle}
            </p>
          )}
          {trend && (
            <p className={`mt-2 text-sm font-medium ${trend.isPositive ? 'text-success-500' : 'text-danger-500'}`}>
              {trend.isPositive ? '↑' : '↓'} {Math.abs(trend.value)}%
            </p>
          )}
        </div>
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
    </Card>
  );
};
