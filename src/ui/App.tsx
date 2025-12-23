import React from 'react';
import { AnomalyList } from './components/AnomalyList';
import { InsightsList } from './components/InsightsList';
import { PatternList } from './components/PatternList';
import './styles/main.css';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = React.useState<'insights' | 'anomalies' | 'patterns'>('insights');

  return (
    <div className="app-container">
      <header>
        <h1>Solar Plant Analytics</h1>
        <nav>
          <button 
            className={activeTab === 'insights' ? 'active' : ''} 
            onClick={() => setActiveTab('insights')}
          >
            Insights
          </button>
          <button 
            className={activeTab === 'anomalies' ? 'active' : ''} 
            onClick={() => setActiveTab('anomalies')}
          >
            Anomalies
          </button>
          <button 
            className={activeTab === 'patterns' ? 'active' : ''} 
            onClick={() => setActiveTab('patterns')}
          >
            Patterns
          </button>
        </nav>
      </header>

      <main className="content">
        {activeTab === 'insights' && <InsightsList />}
        {activeTab === 'anomalies' && <AnomalyList />}
        {activeTab === 'patterns' && <PatternList />}
      </main>
    </div>
  );
};

export default App;
