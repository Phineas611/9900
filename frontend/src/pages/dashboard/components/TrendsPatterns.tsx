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
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer
} from 'recharts';
import './TrendsPatterns.css';

// Types
interface ChartData {
  monthlyData: Array<{
    month: string;
    contracts: number;
    ambiguityRate: number;
  }>;
  qualityScores: Array<{
    month: string;
    score: number;
  }>;
  contractTypes: Array<{
    type: string;
    value: number;
    ambiguity: number;
  }>;
  ambiguityByType: Array<{
    type: string;
    ambiguity: number;
  }>;
}

const TrendsPatterns = () => {
  const [data, setData] = useState<ChartData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState('3months');

  // Fetch chart data from API
  const fetchChartData = async (range: string): Promise<ChartData> => {
    const response = await fetch(`${API_BASE_URL}/charts/trends?range=${range}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch chart data');
    }
    
    const result = await response.json();
    return result.data;
  };

  // Load data when component mounts or time range changes
  useEffect(() => {
    const loadData = async () => {
      try {
        // setLoading(true);
        setError(null);
        // const chartData = await fetchChartData(timeRange);
        // setData(chartData);
        const mockChartData: ChartData = {
          monthlyData: [
            { month: 'Jan', contracts: 45, ambiguityRate: 12.5 },
            { month: 'Feb', contracts: 52, ambiguityRate: 11.8 },
            { month: 'Mar', contracts: 48, ambiguityRate: 13.2 },
            { month: 'Apr', contracts: 61, ambiguityRate: 10.5 },
            { month: 'May', contracts: 55, ambiguityRate: 9.8 },
            { month: 'Jun', contracts: 67, ambiguityRate: 8.9 }
          ],
          qualityScores: [
            { month: 'Jan', score: 7.2 },
            { month: 'Feb', score: 7.5 },
            { month: 'Mar', score: 7.8 },
            { month: 'Apr', score: 8.1 },
            { month: 'May', score: 8.3 },
            { month: 'Jun', score: 8.6 }
          ],
          contractTypes: [
            { type: 'PDF', value: 45, ambiguity: 12.3 },
            { type: 'DOCX', value: 35, ambiguity: 9.8 },
            { type: 'TXT', value: 15, ambiguity: 18.2 },
            { type: 'DOC', value: 5, ambiguity: 22.1 }
          ],
          ambiguityByType: [
            { type: 'PDF', ambiguity: 8.5 },
            { type: 'DOCX', ambiguity: 12.7 },
            { type: 'TXT', ambiguity: 11.2 },
            { type: 'DOC', ambiguity: 15.8 }
          ]
        };
        setData(mockChartData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load chart data');
        console.error('Chart data loading error:', err);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [timeRange]);

  // Colors for charts
  const COLORS = ['#0088CC', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];
  const QUALITY_COLORS = {
    excellent: '#00C49F',
    good: '#0088FE',
    fair: '#FFBB28',
    poor: '#FF8042'
  };

  // Custom tooltip for combined chart
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="custom-tooltip">
          <p className="tooltip-label">{label}</p>
          <p className="tooltip-value" style={{ color: '#0088FE' }}>
            Contracts: {payload[0].value}
          </p>
          <p className="tooltip-value" style={{ color: '#FF8042' }}>
            Ambiguity: {payload[1].value}%
          </p>
        </div>
      );
    }
    return null;
  };

  if (loading) {
    return (
      <div className="trends-patterns loading">
        <div className="loading-spinner">Loading charts...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="trends-patterns error">
        <div className="error-message">
          <h3>Error Loading Charts</h3>
          <p>{error}</p>
          <button onClick={() => window.location.reload()} className="retry-btn">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="trends-patterns">
      {/* Time Range Selection Card */}
      <div className="time-range-card">
        <div className="card-header">
          <h2>Analysis Period</h2>
          <p>Select time range for trend analysis</p>
        </div>
        <div className="time-range-selector">
          <select 
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="range-select"
          >
            <option value="1month">Last Month</option>
            <option value="3months">Last 3 Months</option>
            <option value="6months">Last 6 Months</option>
            <option value="1year">Last Year</option>
          </select>
        </div>
      </div>

      {/* Charts Grid */}
      {data && (
        <div className="charts-grid">
          {/* Chart 1: Contract Volume & Ambiguity Trends */}
          <div className="chart-card">
            <div className="chart-header">
              <h3>Contract Volume & Ambiguity Trends</h3>
              <p>Monthly contract analysis volume and ambiguity rates</p>
            </div>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={data.monthlyData}
                  margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" domain={[0, 100]} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  <Bar 
                    yAxisId="left" 
                    dataKey="contracts" 
                    fill="#0088CC" 
                    name="Contracts"
                    radius={[4, 4, 0, 0]}
                  />
                  <Line 
                    yAxisId="right" 
                    type="monotone" 
                    dataKey="ambiguityRate" 
                    stroke="#FF8042" 
                    strokeWidth={2}
                    name="Ambiguity Rate %"
                    dot={{ fill: '#FF8042', strokeWidth: 2, r: 4 }}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Chart 2: Quality Score Trends */}
          <div className="chart-card">
            <div className="chart-header">
              <h3>Quality Score Trends</h3>
              <p>Average explanation quality over time</p>
            </div>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height={300}>
                <LineChart
                  data={data.qualityScores}
                  margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis domain={[0, 10]} />
                  <Tooltip />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="score" 
                    stroke={QUALITY_COLORS.excellent}
                    strokeWidth={3}
                    name="Quality Score"
                    dot={{ fill: QUALITY_COLORS.excellent, strokeWidth: 2, r: 4 }}
                    activeDot={{ r: 6 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Chart 3: Contract Type Analysis */}
          <div className="chart-card">
            <div className="chart-header">
              <h3>Contract Type Analysis</h3>
              <p>Distribution and ambiguity rates by file type</p>
            </div>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={data.contractTypes}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ type, value }) => `${type}: ${value}%`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                    nameKey="type"
                  >
                    {data.contractTypes.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => [`${value}%`, 'Percentage']} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Chart 4: Avg Ambiguity by Type */}
          <div className="chart-card">
            <div className="chart-header">
              <h3>Avg Ambiguity by Type</h3>
              <p>Average ambiguity rates across different contract types</p>
            </div>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={data.ambiguityByType}
                  layout="vertical"
                  margin={{ top: 20, right: 30, left: 80, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" domain={[0, 100]} />
                  <YAxis type="category" dataKey="type" width={70} />
                  <Tooltip formatter={(value) => [`${value}%`, 'Ambiguity Rate']} />
                  <Legend />
                  <Bar 
                    dataKey="ambiguity" 
                    fill="#FF8042"
                    name="Ambiguity Rate %"
                    radius={[0, 4, 4, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TrendsPatterns;