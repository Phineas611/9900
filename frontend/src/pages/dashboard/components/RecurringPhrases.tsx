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
        // setLoading(true);
        setError(null);
        //const phrasesData = await fetchPhrasesData();
        //setData(phrasesData);

        // Mock data
        const mockPhrasesData: PhrasesData = {
          ambiguousPhrases: [
            {
              id: '1',
              rank: 1,
              phrase: 'reasonable efforts',
              description: 'Found in 156 contracts',
              frequency: 156,
              maxFrequency: 200,
              status: 'High Risk',
              time: '24 times'
            },
            {
              id: '2',
              rank: 2,
              phrase: 'best efforts',
              description: 'Found in 142 contracts',
              frequency: 142,
              maxFrequency: 200,
              status: 'High Risk',
              time: '18 times'
            },
            {
              id: '3',
              rank: 3,
              phrase: 'material breach',
              description: 'Found in 128 contracts',
              frequency: 128,
              maxFrequency: 200,
              status: 'Medium Risk',
              time: '15 times'
            },
            {
              id: '4',
              rank: 4,
              phrase: 'good faith',
              description: 'Found in 115 contracts',
              frequency: 115,
              maxFrequency: 200,
              status: 'Medium Risk',
              time: '12 times'
            },
            {
              id: '5',
              rank: 5,
              phrase: 'commercially reasonable',
              description: 'Found in 98 contracts',
              frequency: 98,
              maxFrequency: 200,
              status: 'Medium Risk',
              time: '8 times'
            },
            {
              id: '6',
              rank: 6,
              phrase: 'sole discretion',
              description: 'Found in 87 contracts',
              frequency: 87,
              maxFrequency: 200,
              status: 'Low Risk',
              time: '6 times'
            }
          ]
        };
        setData(mockPhrasesData);
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
              margin={{ top: 20, right: 30, left: 100, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" />
              <YAxis 
                type="category" 
                dataKey="phrase" 
                width={90}
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