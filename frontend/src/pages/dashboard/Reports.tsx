import { useState, useEffect, useRef } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import './Reports.css';

// Types
interface StatsData {
  totalContracts: number;
  ambiguousSentences: number;
  ambiguityRate: number;
  avgQualityScore: number;
}

interface QualityData {
  month: string;
  clarity: number;
  completeness: number;
  accuracy: number;
  consistency: number;
}

interface AmbiguityTrend {
  month: string;
  ambiguityRate: number;
  targetRate: number;
}

interface ContractAnalysis {
  name: string;
  totalSentences: number;
  ambiguousSentences: number;
  percentage: number;
}

interface ReportsData {
  stats: StatsData;
  qualityMetrics: QualityData[];
  ambiguityTrends: AmbiguityTrend[];
  contractAnalysis: ContractAnalysis[];
}

interface ExportSettings {
  scope: 'all' | 'current' | 'custom';
  format: 'pdf' | 'excel' | 'csv';
  includeCharts: boolean;
  includeSentenceData: boolean;
  includeExplanations: boolean;
}

// Export Modal Component
const ExportModal = ({ isOpen, onClose, onExport }: { 
  isOpen: boolean; 
  onClose: () => void; 
  onExport: (settings: ExportSettings) => void; 
}) => {
  const [scope, setScope] = useState<'all' | 'current' | 'custom'>('all');
  const [format, setFormat] = useState<'pdf' | 'excel' | 'csv'>('pdf');
  const [includeCharts, setIncludeCharts] = useState(true);
  const [includeSentenceData, setIncludeSentenceData] = useState(true);
  const [includeExplanations, setIncludeExplanations] = useState(true);
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async () => {
    setIsExporting(true);
    const settings: ExportSettings = {
      scope,
      format,
      includeCharts,
      includeSentenceData,
      includeExplanations
    };
    
    await onExport(settings);
    setIsExporting(false);
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Export Analysis Report</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        
        <div className="modal-body">
          <p className="modal-subtitle">Configure your report export settings</p>
          
          <div className="form-section">
            <label className="form-label">Scope</label>
            <select 
              value={scope}
              onChange={(e) => setScope(e.target.value as any)}
              className="form-select"
            >
              <option value="all">All Contracts</option>
              <option value="current">Current View</option>
              <option value="custom">Custom Range</option>
            </select>
          </div>

          <div className="form-section">
            <label className="form-label">Format</label>
            <select 
              value={format}
              onChange={(e) => setFormat(e.target.value as any)}
              className="form-select"
            >
              <option value="pdf">PDF Report</option>
              <option value="excel">Excel Spreadsheet</option>
              <option value="csv">CSV Data</option>
            </select>
          </div>

          <div className="form-section">
            <label className="form-label">Include</label>
            <div className="checkbox-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={includeCharts}
                  onChange={(e) => setIncludeCharts(e.target.checked)}
                  className="checkbox-input"
                />
                <span className="checkmark"></span>
                Charts and Visualizations
              </label>
              
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={includeSentenceData}
                  onChange={(e) => setIncludeSentenceData(e.target.checked)}
                  className="checkbox-input"
                />
                <span className="checkmark"></span>
                Sentence Analysis Data
              </label>
              
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={includeExplanations}
                  onChange={(e) => setIncludeExplanations(e.target.checked)}
                  className="checkbox-input"
                />
                <span className="checkmark"></span>
                Plain-English Explanations
              </label>
            </div>
          </div>
        </div>

        <div className="modal-footer">
          <button className="cancel-btn" onClick={onClose} disabled={isExporting}>
            Cancel
          </button>
          <button 
            className={`export-confirm-btn ${isExporting ? 'exporting' : ''}`} 
            onClick={handleExport}
            disabled={isExporting}
          >
            {isExporting ? 'Exporting...' : 'Export Report'}
          </button>
        </div>
      </div>
    </div>
  );
};

const Reports = () => {
  const [data, setData] = useState<ReportsData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);

  // Mock data
  const mockReportsData: ReportsData = {
    stats: {
      totalContracts: 156,
      ambiguousSentences: 24567,
      ambiguityRate: 12.8,
      avgQualityScore: 7.8
    },
    qualityMetrics: [
      { month: 'Jan', clarity: 7.2, completeness: 6.8, accuracy: 7.5, consistency: 6.9 },
      { month: 'Feb', clarity: 7.4, completeness: 7.1, accuracy: 7.6, consistency: 7.2 },
      { month: 'Mar', clarity: 7.6, completeness: 7.3, accuracy: 7.8, consistency: 7.4 },
      { month: 'Apr', clarity: 7.8, completeness: 7.5, accuracy: 8.0, consistency: 7.6 },
      { month: 'May', clarity: 8.0, completeness: 7.7, accuracy: 8.2, consistency: 7.8 },
      { month: 'Jun', clarity: 8.2, completeness: 7.9, accuracy: 8.4, consistency: 8.0 }
    ],
    ambiguityTrends: [
      { month: 'Jan', ambiguityRate: 15.2, targetRate: 10 },
      { month: 'Feb', ambiguityRate: 14.6, targetRate: 10 },
      { month: 'Mar', ambiguityRate: 13.8, targetRate: 10 },
      { month: 'Apr', ambiguityRate: 12.9, targetRate: 10 },
      { month: 'May', ambiguityRate: 11.5, targetRate: 10 },
      { month: 'Jun', ambiguityRate: 10.8, targetRate: 10 }
    ],
    contractAnalysis: [
      { name: 'Partnership Agreement', totalSentences: 153156, ambiguousSentences: 24505, percentage: 16.0 },
      { name: 'Service Agreement', totalSentences: 23456, ambiguousSentences: 2815, percentage: 12.0 },
      { name: 'NDA Template', totalSentences: 12086, ambiguousSentences: 1692, percentage: 14.0 },
      { name: 'Employment Contract', totalSentences: 4567, ambiguousSentences: 502, percentage: 11.0 },
      { name: 'Software License Agreement', totalSentences: 81234, ambiguousSentences: 8926, percentage: 11.0 }
    ]
  };

  // Simulate API call
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        await new Promise(resolve => setTimeout(resolve, 800));
        setData(mockReportsData);
      } catch (err) {
        setError('Failed to load reports data');
        console.error('Reports data loading error:', err);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  // Handle export report
  const handleExportReport = () => {
    setIsExportModalOpen(true);
  };

  const handleExportConfirm = async (settings: ExportSettings) => {
    try {
      let content = '';
      
      // Generate report content based on settings
      if (settings.format === 'csv') {
        content = generateCSVContent(settings);
        downloadFile(content, 'contract-analysis-report.csv', 'text/csv');
      } else if (settings.format === 'excel') {
        content = generateExcelContent(settings);
        downloadFile(content, 'contract-analysis-report.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
      } else {
        // For PDF, we'll generate HTML content that can be printed
        content = generatePDFContent(settings);
        openPDFPrint(content);
      }
      
      alert(`Report exported successfully as ${settings.format.toUpperCase()}!`);
    } catch (error) {
      console.error('Export failed:', error);
      alert('Export failed. Please try again.');
    } finally {
      setIsExportModalOpen(false);
    }
  };

  // Generate CSV content
  const generateCSVContent = (settings: ExportSettings): string => {
    let csvContent = 'Contract Analysis Report\n\n';
    
    // Add stats
    if (data) {
      csvContent += 'Key Statistics\n';
      csvContent += 'Total Contracts,' + data.stats.totalContracts + '\n';
      csvContent += 'Ambiguous Sentences,' + data.stats.ambiguousSentences + '\n';
      csvContent += 'Ambiguity Rate,' + data.stats.ambiguityRate + '%\n';
      csvContent += 'Average Quality Score,' + data.stats.avgQualityScore + '/10\n\n';
    }

    // Add quality metrics
    if (settings.includeCharts && data) {
      csvContent += 'Quality Metrics Over Time\n';
      csvContent += 'Month,Clarity,Completeness,Accuracy,Consistency\n';
      data.qualityMetrics.forEach(item => {
        csvContent += `${item.month},${item.clarity},${item.completeness},${item.accuracy},${item.consistency}\n`;
      });
      csvContent += '\n';
    }

    // Add ambiguity trends
    if (settings.includeCharts && data) {
      csvContent += 'Ambiguity Rate Trends\n';
      csvContent += 'Month,Ambiguity Rate,Target Rate\n';
      data.ambiguityTrends.forEach(item => {
        csvContent += `${item.month},${item.ambiguityRate}%,${item.targetRate}%\n`;
      });
      csvContent += '\n';
    }

    // Add contract analysis
    if (settings.includeSentenceData && data) {
      csvContent += 'Per-Contract Analysis\n';
      csvContent += 'Contract Name,Total Sentences,Ambiguous Sentences,Ambiguity Rate\n';
      data.contractAnalysis.forEach(item => {
        csvContent += `${item.name},${item.totalSentences},${item.ambiguousSentences},${item.percentage}%\n`;
      });
      csvContent += '\n';
    }

    // Add ambiguous phrases
    if (settings.includeExplanations) {
      csvContent += 'Most Common Ambiguous Phrases\n';
      csvContent += 'Rank,Phrase,Occurrences\n';
      const phrases = [
        { rank: 1, phrase: 'reasonable efforts', count: 24 },
        { rank: 2, phrase: 'best efforts', count: 18 },
        { rank: 3, phrase: 'promptly', count: 15 },
        { rank: 4, phrase: 'substantial', count: 12 },
        { rank: 5, phrase: 'completion', count: 10 }
      ];
      phrases.forEach(item => {
        csvContent += `${item.rank},${item.phrase},${item.count}\n`;
      });
    }

    return csvContent;
  };

  // Generate Excel content (simplified - in real app you'd use a library like xlsx)
  const generateExcelContent = (settings: ExportSettings): string => {
    // For demo purposes, we'll create a simple HTML table that can be opened in Excel
    let htmlContent = `
      <html>
      <head>
        <meta charset="UTF-8">
        <title>Contract Analysis Report</title>
        <style>
          table { border-collapse: collapse; width: 100%; }
          th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
          th { background-color: #f2f2f2; }
        </style>
      </head>
      <body>
        <h1>Contract Analysis Report</h1>
    `;

    if (data) {
      htmlContent += `
        <h2>Key Statistics</h2>
        <table>
          <tr><th>Metric</th><th>Value</th></tr>
          <tr><td>Total Contracts</td><td>${data.stats.totalContracts}</td></tr>
          <tr><td>Ambiguous Sentences</td><td>${data.stats.ambiguousSentences.toLocaleString()}</td></tr>
          <tr><td>Ambiguity Rate</td><td>${data.stats.ambiguityRate}%</td></tr>
          <tr><td>Average Quality Score</td><td>${data.stats.avgQualityScore}/10</td></tr>
        </table>
      `;
    }

    if (settings.includeCharts && data) {
      htmlContent += `
        <h2>Quality Metrics</h2>
        <table>
          <tr><th>Month</th><th>Clarity</th><th>Completeness</th><th>Accuracy</th><th>Consistency</th></tr>
          ${data.qualityMetrics.map(item => `
            <tr>
              <td>${item.month}</td>
              <td>${item.clarity}</td>
              <td>${item.completeness}</td>
              <td>${item.accuracy}</td>
              <td>${item.consistency}</td>
            </tr>
          `).join('')}
        </table>
      `;
    }

    if (settings.includeSentenceData && data) {
      htmlContent += `
        <h2>Contract Analysis</h2>
        <table>
          <tr><th>Contract Name</th><th>Total Sentences</th><th>Ambiguous Sentences</th><th>Ambiguity Rate</th></tr>
          ${data.contractAnalysis.map(item => `
            <tr>
              <td>${item.name}</td>
              <td>${item.totalSentences.toLocaleString()}</td>
              <td>${item.ambiguousSentences.toLocaleString()}</td>
              <td>${item.percentage}%</td>
            </tr>
          `).join('')}
        </table>
      `;
    }

    if (settings.includeExplanations) {
      htmlContent += `
        <h2>Ambiguous Phrases</h2>
        <table>
          <tr><th>Rank</th><th>Phrase</th><th>Occurrences</th></tr>
          <tr><td>1</td><td>reasonable efforts</td><td>24</td></tr>
          <tr><td>2</td><td>best efforts</td><td>18</td></tr>
          <tr><td>3</td><td>promptly</td><td>15</td></tr>
          <tr><td>4</td><td>substantial</td><td>12</td></tr>
          <tr><td>5</td><td>completion</td><td>10</td></tr>
        </table>
      `;
    }

    htmlContent += `</body></html>`;
    return htmlContent;
  };

  // Generate PDF content
  const generatePDFContent = (settings: ExportSettings): string => {
    let pdfContent = `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <title>Contract Analysis Report</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 40px; color: #333; }
          h1 { color: #2d3748; border-bottom: 2px solid #3182ce; padding-bottom: 10px; }
          h2 { color: #4a5568; margin-top: 30px; }
          .section { margin-bottom: 30px; }
          .stats-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin: 20px 0; }
          .stat-card { border: 1px solid #e2e8f0; padding: 20px; border-radius: 8px; }
          .stat-value { font-size: 24px; font-weight: bold; color: #3182ce; }
          table { width: 100%; border-collapse: collapse; margin: 20px 0; }
          th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
          th { background-color: #f7fafc; font-weight: 600; }
          .summary-item { background: #f0fff4; padding: 15px; margin: 10px 0; border-left: 4px solid #38a169; }
          @media print { body { margin: 20px; } }
        </style>
      </head>
      <body>
        <h1>Contract Analysis Report</h1>
        <div class="section">
          <p><strong>Generated:</strong> ${new Date().toLocaleDateString()}</p>
          <p><strong>Scope:</strong> ${settings.scope}</p>
        </div>
    `;

    if (data) {
      pdfContent += `
        <div class="section">
          <h2>Key Statistics</h2>
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-value">${data.stats.totalContracts}</div>
              <div>Total Contracts Analyzed</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">${data.stats.ambiguousSentences.toLocaleString()}</div>
              <div>Ambiguous Sentences</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">${data.stats.ambiguityRate}%</div>
              <div>Average Ambiguity Rate</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">${data.stats.avgQualityScore}/10</div>
              <div>Average Quality Score</div>
            </div>
          </div>
        </div>
      `;
    }

    if (settings.includeCharts && data) {
      pdfContent += `
        <div class="section">
          <h2>Quality Metrics Trends</h2>
          <table>
            <tr>
              <th>Month</th>
              <th>Clarity</th>
              <th>Completeness</th>
              <th>Accuracy</th>
              <th>Consistency</th>
            </tr>
            ${data.qualityMetrics.map(item => `
              <tr>
                <td>${item.month}</td>
                <td>${item.clarity}/10</td>
                <td>${item.completeness}/10</td>
                <td>${item.accuracy}/10</td>
                <td>${item.consistency}/10</td>
              </tr>
            `).join('')}
          </table>
        </div>

        <div class="section">
          <h2>Ambiguity Rate Trends</h2>
          <table>
            <tr>
              <th>Month</th>
              <th>Ambiguity Rate</th>
              <th>Target Rate</th>
            </tr>
            ${data.ambiguityTrends.map(item => `
              <tr>
                <td>${item.month}</td>
                <td>${item.ambiguityRate}%</td>
                <td>${item.targetRate}%</td>
              </tr>
            `).join('')}
          </table>
        </div>
      `;
    }

    if (settings.includeSentenceData && data) {
      pdfContent += `
        <div class="section">
          <h2>Per-Contract Analysis</h2>
          <table>
            <tr>
              <th>Contract Name</th>
              <th>Total Sentences</th>
              <th>Ambiguous Sentences</th>
              <th>Ambiguity Rate</th>
            </tr>
            ${data.contractAnalysis.map(item => `
              <tr>
                <td>${item.name}</td>
                <td>${item.totalSentences.toLocaleString()}</td>
                <td>${item.ambiguousSentences.toLocaleString()}</td>
                <td>${item.percentage}%</td>
              </tr>
            `).join('')}
          </table>
        </div>
      `;
    }

    if (settings.includeExplanations) {
      pdfContent += `
        <div class="section">
          <h2>Most Common Ambiguous Phrases</h2>
          <table>
            <tr>
              <th>Rank</th>
              <th>Phrase</th>
              <th>Occurrences</th>
            </tr>
            <tr><td>1</td><td>reasonable efforts</td><td>24</td></tr>
            <tr><td>2</td><td>best efforts</td><td>18</td></tr>
            <tr><td>3</td><td>promptly</td><td>15</td></tr>
            <tr><td>4</td><td>substantial</td><td>12</td></tr>
            <tr><td>5</td><td>completion</td><td>10</td></tr>
          </table>
        </div>

        <div class="section">
          <h2>Analysis Summary</h2>
          <div class="summary-item">
            <strong>Improving Clarity</strong>
            <p>Average explanation quality has improved by 12% over the last 6 months.</p>
          </div>
          <div class="summary-item">
            <strong>Top Issue</strong>
            <p>"Reasonable efforts" appears in 24 contracts and consistently causes ambiguity.</p>
          </div>
          <div class="summary-item">
            <strong>Processing Efficiency</strong>
            <p>Average analysis time has decreased by 15% with improved models.</p>
          </div>
        </div>
      `;
    }

    pdfContent += `</body></html>`;
    return pdfContent;
  };

  // Download file utility
  const downloadFile = (content: string, filename: string, mimeType: string) => {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // Open PDF for printing
  const openPDFPrint = (content: string) => {
    const printWindow = window.open('', '_blank');
    if (printWindow) {
      printWindow.document.write(content);
      printWindow.document.close();
      printWindow.focus();
      setTimeout(() => {
        printWindow.print();
        // printWindow.close(); // Uncomment to auto-close after print
      }, 500);
    }
  };

  const handleCloseModal = () => {
    setIsExportModalOpen(false);
  };

  // Custom tooltip for quality metrics
  const QualityTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="custom-tooltip">
          <p className="tooltip-label">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="tooltip-value" style={{ color: entry.color }}>
              {entry.name}: {entry.value}/10
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  // Custom tooltip for ambiguity trend
  const AmbiguityTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="custom-tooltip">
          <p className="tooltip-label">{label}</p>
          <p className="tooltip-value" style={{ color: '#FF6B35' }}>
            Actual: {payload[0].value}%
          </p>
          <p className="tooltip-value" style={{ color: '#718096' }}>
            Target: {payload[1].value}%
          </p>
        </div>
      );
    }
    return null;
  };

  if (loading) {
    return (
      <div className="reports-page loading">
        <div className="loading-spinner">Loading reports...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="reports-page error">
        <div className="error-message">
          <h3>Error Loading Reports</h3>
          <p>{error}</p>
          <button onClick={() => window.location.reload()} className="retry-btn">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="reports-page" ref={contentRef}>
      {/* Export Modal */}
      <ExportModal 
        isOpen={isExportModalOpen}
        onClose={handleCloseModal}
        onExport={handleExportConfirm}
      />

      {/* Page Header */}
      <div className="page-header">
        <div className="header-content">
          <div className="header-text">
            <h1>Reports & Analytics</h1>
            <p>Visualize contract analysis trends and export detailed reports</p>
          </div>
          <button className="export-btn" onClick={handleExportReport}>
            Export Report
          </button>
        </div>
      </div>

      {/* Statistics Cards */}
      {data && (
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-header">
              <div className="stat-title">Total Contracts</div>
              <div className="stat-icon">📋</div>
            </div>
            <div className="stat-value">{data.stats.totalContracts}</div>
            <div className="stat-label">Contracts analyzed</div>
          </div>

          <div className="stat-card">
            <div className="stat-header">
              <div className="stat-title">Ambiguous Sentences</div>
              <div className="stat-icon">❓</div>
            </div>
            <div className="stat-value">{data.stats.ambiguousSentences.toLocaleString()}</div>
            <div className="stat-label">Sentences flagged</div>
          </div>

          <div className="stat-card">
            <div className="stat-header">
              <div className="stat-title">Ambiguity Rate</div>
              <div className="stat-icon">📊</div>
            </div>
            <div className="stat-value">{data.stats.ambiguityRate}%</div>
            <div className="stat-label">Average rate</div>
          </div>

          <div className="stat-card">
            <div className="stat-header">
              <div className="stat-title">Avg Quality Score</div>
              <div className="stat-icon">⭐</div>
            </div>
            <div className="stat-value">{data.stats.avgQualityScore}/10</div>
            <div className="stat-label">Explanation quality</div>
          </div>
        </div>
      )}

      {/* Charts Row 1 */}
      <div className="charts-row">
        {/* Model Explanation Quality */}
        <div className="chart-card large">
          <div className="chart-header">
            <h3>Model Explanation Quality</h3>
            <p>Monthly trends for explanation quality metrics</p>
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart
                data={data?.qualityMetrics}
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis domain={[0, 10]} />
                <Tooltip content={<QualityTooltip />} />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="clarity" 
                  stroke="#0088FE" 
                  strokeWidth={2}
                  name="Clarity"
                  dot={{ fill: '#0088FE', strokeWidth: 2, r: 4 }}
                />
                <Line 
                  type="monotone" 
                  dataKey="completeness" 
                  stroke="#00C49F" 
                  strokeWidth={2}
                  name="Completeness"
                  dot={{ fill: '#00C49F', strokeWidth: 2, r: 4 }}
                />
                <Line 
                  type="monotone" 
                  dataKey="accuracy" 
                  stroke="#FFBB28" 
                  strokeWidth={2}
                  name="Accuracy"
                  dot={{ fill: '#FFBB28', strokeWidth: 2, r: 4 }}
                />
                <Line 
                  type="monotone" 
                  dataKey="consistency" 
                  stroke="#FF8042" 
                  strokeWidth={2}
                  name="Consistency"
                  dot={{ fill: '#FF8042', strokeWidth: 2, r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Ambiguity Rate Trend */}
        <div className="chart-card large">
          <div className="chart-header">
            <h3>Ambiguity Rate Trend</h3>
            <p>Percentage of ambiguous sentences over time</p>
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart
                data={data?.ambiguityTrends}
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis domain={[0, 20]} />
                <Tooltip content={<AmbiguityTooltip />} />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="ambiguityRate" 
                  stroke="#FF6B35" 
                  strokeWidth={3}
                  name="Ambiguity Rate"
                  dot={{ fill: '#FF6B35', strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6 }}
                />
                <Line 
                  type="monotone" 
                  dataKey="targetRate" 
                  stroke="#718096" 
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  name="Target Rate"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Per-Contract Analysis */}
      <div className="chart-card full-width">
        <div className="chart-header">
          <h3>Per-Contract Analysis</h3>
          <p>Proportion of ambiguous sentences across analyzed contracts</p>
        </div>
        <div className="chart-container contract-analysis-chart">
          <ResponsiveContainer width="100%" height={350}>
            <BarChart
              data={data?.contractAnalysis}
              layout="vertical"
              margin={{ top: 20, right: 30, left: 180, bottom: 40 }}
            >
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" domain={[0, 20]} />
              <YAxis 
                type="category" 
                dataKey="name" 
                width={160}
                tick={{ fontSize: 12 }}
              />
              <Tooltip 
                formatter={(value, name) => {
                  if (name === 'percentage') return [`${value}%`, 'Ambiguity Rate'];
                  return [value, 'Sentences'];
                }}
              />
              <Legend />
              <Bar 
                dataKey="percentage" 
                name="Ambiguity Rate"
                fill="#8884D8"
                radius={[0, 4, 4, 0]}
                barSize={20}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Bottom Cards Row */}
      <div className="bottom-cards-row">
        {/* Most Common Ambiguous Phrases */}
        <div className="info-card">
          <div className="card-header">
            <h3>Most Common Ambiguous Phrases</h3>
            <p>Frequently occurring ambiguous terms across all contracts</p>
          </div>
          <div className="phrases-list">
            {[
              { rank: 1, phrase: 'reasonable efforts', count: 24, maxCount: 30 },
              { rank: 2, phrase: 'best efforts', count: 18, maxCount: 30 },
              { rank: 3, phrase: 'promptly', count: 15, maxCount: 30 },
              { rank: 4, phrase: 'substantial', count: 12, maxCount: 30 },
              { rank: 5, phrase: 'completion', count: 10, maxCount: 30 },
              { rank: 6, phrase: 'material breach', count: 10, maxCount: 30 },
              { rank: 7, phrase: 'good faith', count: 8, maxCount: 30 },
              { rank: 8, phrase: 'commercially', count: 7, maxCount: 30 },
              { rank: 9, phrase: 'reasonable', count: 6, maxCount: 30 },
              { rank: 10, phrase: 'industry standard', count: 6, maxCount: 30 }
            ].map((item) => (
              <div key={item.rank} className="phrase-item">
                <span className="phrase-rank">{item.rank}</span>
                <span className="phrase-text">{item.phrase}</span>
                <div className="phrase-progress">
                  <div className="progress-bar">
                    <div 
                      className="progress-fill"
                      style={{ width: `${(item.count / item.maxCount) * 100}%` }}
                    ></div>
                  </div>
                  <span className="phrase-count">{item.count} occurrences</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Analysis Summary */}
        <div className="info-card">
          <div className="card-header">
            <h3>Analysis Summary</h3>
            <p>Key insights from contract analysis</p>
          </div>
          <div className="summary-content">
            <div className="summary-item positive">
              <div className="summary-icon">✔</div>
              <div className="summary-text">
                <strong>Improving Clarity</strong>
                <p>Average explanation quality has improved by 12% over the last 6 months.</p>
              </div>
            </div>
            
            <div className="summary-item warning">
              <div className="summary-icon">⚠</div>
              <div className="summary-text">
                <strong>Top Issue</strong>
                <p>"Reasonable efforts" appears in 24 contracts and consistently causes ambiguity.</p>
              </div>
            </div>
            
            <div className="summary-item positive">
              <div className="summary-icon">⚡</div>
              <div className="summary-text">
                <strong>Processing Efficiency</strong>
                <p>Average analysis time has decreased by 15% with improved models.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Reports;