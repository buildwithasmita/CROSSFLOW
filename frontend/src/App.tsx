import React, { useState } from 'react';
import { ThemeProvider } from './contexts/ThemeContext';
import { Header } from './components/layout/Header';
import { Sidebar } from './components/layout/Sidebar';
import { DashboardPage } from './pages/DashboardPage';
import { InsightsPage } from './pages/InsightsPage';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <DashboardPage />;
      case 'insights':
        return <InsightsPage />;
      case 'customers':
        return (
          <div className="text-center py-12">
            <p className="text-gray-600 dark:text-dark-600">
              Customer details view coming soon...
            </p>
          </div>
        );
      case 'analytics':
        return (
          <div className="text-center py-12">
            <p className="text-gray-600 dark:text-dark-600">
              Advanced analytics coming soon...
            </p>
          </div>
        );
      case 'settings':
        return (
          <div className="text-center py-12">
            <p className="text-gray-600 dark:text-dark-600">
              Settings coming soon...
            </p>
          </div>
        );
      default:
        return <DashboardPage />;
    }
  };

  return (
    <ThemeProvider>
      <div className="min-h-screen bg-gray-50 dark:bg-dark-50">
        <Header />
        <div className="flex">
          <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
          <main className="flex-1 p-8">
            <div className="max-w-7xl mx-auto">
              {renderContent()}
            </div>
          </main>
        </div>
      </div>
    </ThemeProvider>
  );
}

export default App;
