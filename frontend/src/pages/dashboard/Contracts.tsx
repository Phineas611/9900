import { useState } from 'react';
import AllContracts from './components/AllContracts';
import TrendsPatterns from './components/TrendsPatterns';
import RecurringPhrases from './components/RecurringPhrases';
import './Contracts.css';

const Contracts = () => {
  const [activeTab, setActiveTab] = useState<'all' | 'trends' | 'phrases'>('all');

  const tabs = [
    { id: 'all', label: 'All Contracts' },
    { id: 'trends', label: 'Trends & Patterns' },
    { id: 'phrases', label: 'Recurring Phrases' },
  ];

  const renderContent = () => {
    switch (activeTab) {
      case 'all':
        return <AllContracts />;
      case 'trends':
        return <TrendsPatterns />;
      case 'phrases':
        return <RecurringPhrases />;
      default:
        return <AllContracts />;
    }
  };

  return (
    <div className="contracts-page">
      {/* Page Header */}
      <div className="page-header">
        <h2>Contract Repository</h2>
        <p>Manage and analyze your contract evaluation history</p>
      </div>

      {/* Tab Navigation */}
      <div className="tabs-container">
        <div className="tabs">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id as any)}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {renderContent()}
      </div>
    </div>
  );
};

export default Contracts;