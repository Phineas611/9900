import { useState, useEffect } from 'react';
import { API_BASE_URL } from '../../../services/api'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import './RecurringPhrases.css';

// Types
interface AmbiguousPhrase {
  id: string;
  rank: number;
  phrase: string;
  description: string;
  frequency: number;
  maxFrequency: number;
  status: string;
  time: string;
}

interface PhrasesData {
  ambiguousPhrases: AmbiguousPhrase[];
}

const RecurringPhrases = () => {
  const [data, setData] = useState<PhrasesData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch phrases data from API
  const fetchPhrasesData = async (): Promise<PhrasesData> => {
    const response = await fetch(`${API_BASE_URL}/phrases/recurring`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch phrases data');
    }
    
    const result = await response.json();
    return result.data;
  };

  // Load data
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);
        const phrasesData = await fetchPhrasesData();
        setData(phrasesData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load phrases data');
        console.error('Phrases data loading error:', err);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  // Custom tooltip for usage chart
  const UsageTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="usage-tooltip">
          <p className="tooltip-label">"{label}"</p>
          <p className="tooltip-value">
            Used: {payload[0].value} times
          </p>
          <p className="tooltip-value">
            Frequency: {payload[0].payload.percentage}%
          </p>
        </div>
      );
    }
    return null;
  };

  if (loading) {
    return (
      <div className="recurring-phrases loading">
        <div className="loading-spinner">Loading phrases analysis...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="recurring-phrases error">
        <div className="error-message">
          <h3>Error Loading Phrases Analysis</h3>
          <p>{error}</p>
          <button onClick={() => window.location.reload()} className="retry-btn">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="recurring-phrases">
      {/* Ambiguous Phrases Card */}
      <div className="phrases-card">
        <div className="card-header">
          <h2>Recurring Ambiguous Phrases</h2>
          <p>Most common ambiguous terms across all analyzed contracts</p>
        </div>

        <div className="phrases-list">
          {data?.ambiguousPhrases.map((item) => (
            <div key={item.id} className="phrase-item">
              <div className="phrase-rank">
                <span className="rank-number">{item.rank}</span>
              </div>
              
              <div className="phrase-content">
                <div className="phrase-text">
                  <span className="main-phrase">{item.phrase}</span>
                  <span className="phrase-description">{item.description}</span>
                </div>
                
                <div className="phrase-meta">
                  <span className="phrase-time">{item.time}</span>
                  <span className="phrase-status">{item.status}</span>
                </div>
              </div>

              <div className="phrase-progress">
                <div className="progress-bar">
                  <div 
                    className="progress-fill"
                    style={{ width: `${(item.frequency / item.maxFrequency) * 100}%` }}
                  ></div>
                </div>
                <span className="progress-text">{item.frequency} times</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Phrase Usage Analysis Card */}
      <div className="usage-card">
        <div className="card-header">
          <h2>Phrase Usage Analysis</h2>
          <p>Frequency distribution of ambiguous phrases</p>
        </div>

        <div className="usage-chart">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={data?.ambiguousPhrases}
              layout="vertical"
              margin={{ top: 20, right: 30, left: 30, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" />
              <YAxis 
                type="category" 
                dataKey="phrase" 
                width={280}
                tick={{ fontSize: 12 }}
              />
              <Tooltip content={<UsageTooltip />} />
              <Legend />
              <Bar 
                dataKey="frequency" 
                name="Frequency"
                fill="#FF6B35"
                radius={[0, 4, 4, 0]}
                barSize={20}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default RecurringPhrases;