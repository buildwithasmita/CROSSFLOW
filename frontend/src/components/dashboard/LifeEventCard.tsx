import React from 'react';
import { Baby, Home, Plane, TrendingUp, Sparkles } from 'lucide-react';
import { LifeEvent } from '../../types';
import { Card } from '../common/Card';

interface LifeEventCardProps {
  lifeEvents: LifeEvent[];
}

export const LifeEventCard: React.FC<LifeEventCardProps> = ({ lifeEvents }) => {
  const getEventIcon = (eventName: string) => {
    if (eventName.includes('Parent')) return Baby;
    if (eventName.includes('Home')) return Home;
    if (eventName.includes('Travel')) return Plane;
    if (eventName.includes('Lifestyle')) return TrendingUp;
    return Sparkles;
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 75) return 'text-success-500 bg-success-50 dark:bg-success-900/20';
    if (confidence >= 50) return 'text-warning-500 bg-warning-50 dark:bg-warning-900/20';
    return 'text-gray-500 bg-gray-50 dark:bg-gray-900/20';
  };

  if (!lifeEvents || lifeEvents.length === 0) {
    return (
      <Card>
        <div className="text-center py-8">
          <Sparkles className="w-12 h-12 text-gray-300 dark:text-dark-400 mx-auto mb-3" />
          <p className="text-gray-500 dark:text-dark-500">No life events detected</p>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {lifeEvents.map((event, idx) => {
        const Icon = getEventIcon(event.event);
        
        return (
          <Card key={idx} className="hover:shadow-glow-amex">
            <div className="flex items-start space-x-4">
              {/* Icon */}
              <div className="p-3 bg-gradient-amex rounded-lg">
                <Icon className="w-6 h-6 text-white" />
              </div>
              
              {/* Content */}
              <div className="flex-1">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-lg font-bold text-gray-900 dark:text-dark-900">
                    {event.event}
                  </h4>
                  <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getConfidenceColor(event.confidence)}`}>
                    {event.confidence}% confidence
                  </span>
                </div>
                
                {/* Signals */}
                <div className="mb-3">
                  <p className="text-sm font-medium text-gray-600 dark:text-dark-600 mb-2">
                    Detected Signals:
                  </p>
                  <ul className="space-y-1">
                    {event.signals.map((signal, i) => (
                      <li key={i} className="text-sm text-gray-700 dark:text-dark-700 flex items-start">
                        <span className="text-amex-500 mr-2">✓</span>
                        {signal}
                      </li>
                    ))}
                  </ul>
                </div>
                
                {/* Recommendation */}
                <div className="bg-gold-50 dark:bg-gold-900/20 border-l-4 border-gold-500 p-3 rounded">
                  <p className="text-sm font-semibold text-gold-700 dark:text-gold-400 mb-1">
                    Recommended: {event.recommended_product}
                  </p>
                  <p className="text-sm text-gold-600 dark:text-gold-500">
                    {event.recommendation_reason}
                  </p>
                </div>
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
};
