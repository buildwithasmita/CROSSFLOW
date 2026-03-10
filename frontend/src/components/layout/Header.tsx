import React from 'react';
import { TrendingUp, Settings } from 'lucide-react';
import { ThemeToggle } from './ThemeToggle';

export const Header: React.FC = () => {
  return (
    <header className="bg-white dark:bg-dark-100 border-b border-gray-200 dark:border-dark-200 sticky top-0 z-50 shadow-sm">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 bg-gradient-amex rounded-xl flex items-center justify-center shadow-glow-amex">
              <TrendingUp className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-amex bg-clip-text text-transparent">
                CROSSFLOW
              </h1>
              <p className="text-xs text-gray-500 dark:text-dark-500">
                Cross-Sell Propensity Engine
              </p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center space-x-4">
            <ThemeToggle />
            <button className="p-3 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-200 transition-colors">
              <Settings className="w-5 h-5 text-gray-600 dark:text-dark-600" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
