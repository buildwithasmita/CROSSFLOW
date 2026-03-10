import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Card } from '../common/Card';
import { useTheme } from '../../contexts/ThemeContext';

interface PropensityDistributionProps {
  scores: number[];
}

export const PropensityDistribution: React.FC<PropensityDistributionProps> = ({ scores }) => {
  const { theme } = useTheme();
  
  // Create histogram buckets
  const buckets = [
    { range: '0-20', count: 0, color: '#ef4444', label: 'Very Low' },
    { range: '21-40', count: 0, color: '#f59e0b', label: 'Low' },
    { range: '41-60', count: 0, color: '#eab308', label: 'Medium' },
    { range: '61-80', count: 0, color: '#10b981', label: 'High' },
    { range: '81-100', count: 0, color: '#059669', label: 'Very High' },
  ];

  scores.forEach(score => {
    if (score <= 20) buckets[0].count++;
    else if (score <= 40) buckets[1].count++;
    else if (score <= 60) buckets[2].count++;
    else if (score <= 80) buckets[3].count++;
    else buckets[4].count++;
  });

  return (
    <Card>
      <h3 className="text-lg font-semibold text-gray-900 dark:text-dark-900 mb-4">
        Propensity Score Distribution
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={buckets}>
          <CartesianGrid strokeDasharray="3 3" stroke={theme === 'dark' ? '#3f3f46' : '#e5e7eb'} />
          <XAxis 
            dataKey="range" 
            stroke={theme === 'dark' ? '#a1a1aa' : '#6b7280'}
            tick={{ fill: theme === 'dark' ? '#a1a1aa' : '#6b7280' }}
          />
          <YAxis 
            stroke={theme === 'dark' ? '#a1a1aa' : '#6b7280'}
            tick={{ fill: theme === 'dark' ? '#a1a1aa' : '#6b7280' }}
          />
          <Tooltip 
            contentStyle={{
              backgroundColor: theme === 'dark' ? '#27272a' : '#ffffff',
              border: '1px solid ' + (theme === 'dark' ? '#3f3f46' : '#e5e7eb'),
              borderRadius: '8px',
              color: theme === 'dark' ? '#f8fafc' : '#1e293b'
            }}
            labelStyle={{ color: theme === 'dark' ? '#f8fafc' : '#1e293b' }}
          />
          <Bar dataKey="count" radius={[8, 8, 0, 0]}>
            {buckets.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      
      {/* Legend */}
      <div className="mt-4 flex flex-wrap gap-4 justify-center">
        {buckets.map((bucket, idx) => (
          <div key={idx} className="flex items-center space-x-2">
            <div 
              className="w-4 h-4 rounded" 
              style={{ backgroundColor: bucket.color }}
            />
            <span className="text-sm text-gray-600 dark:text-dark-600">
              {bucket.range}: {bucket.label}
            </span>
          </div>
        ))}
      </div>
    </Card>
  );
};
