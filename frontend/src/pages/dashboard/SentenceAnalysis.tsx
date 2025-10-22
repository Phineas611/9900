import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './SentenceAnalysis.css';

// Types
interface Sentence {
  id: string;
  sentence: string;
  classification: string;
  confidence: number;
  score: number;
  isAmbiguous: boolean;
}

interface AnalysisStats {
  totalSentences: number;
  ambiguousSentences: number;
  unambiguousSentences: number;
}

interface SentenceDetail {
  originalSentence: string;
  plainEnglishExplanation: string;
  whyAmbiguous: string[];
  actions: string[];
}

const SentenceAnalysis = () => {
  const navigate = useNavigate();
  const [sentences, setSentences] = useState<Sentence[]>([]);
  const [stats, setStats] = useState<AnalysisStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sentenceFilter, setSentenceFilter] = useState('all');
  const [modelFilter, setModelFilter] = useState('ensemble');
  const [currentPage, setCurrentPage] = useState(1);
  const [expandedSentenceId, setExpandedSentenceId] = useState<string | null>(null);
  const itemsPerPage = 10;

  // Mock data for sentences
  const mockData = {
    sentences: [
      {
        id: '1',
        sentence: 'The Company shall provide reasonable efforts to ensure system availability during business hours.',
        classification: 'Ambiguous',
        confidence: 95.0,
        score: 9.1,
        isAmbiguous: true
      },
      {
        id: '2',
        sentence: 'Payment shall be made within thirty (30) days of invoice receipt.',
        classification: 'Unambiguous',
        confidence: 95.0,
        score: 9.1,
        isAmbiguous: false
      },
      {
        id: '3',
        sentence: 'The service will be available most of the time with occasional maintenance windows.',
        classification: 'Ambiguous',
        confidence: 92.0,
        score: 8.1,
        isAmbiguous: true
      },
      {
        id: '4',
        sentence: 'All employees must comply with company policies and procedures.',
        classification: 'Unambiguous',
        confidence: 98.0,
        score: 9.5,
        isAmbiguous: false
      },
      {
        id: '5',
        sentence: 'The parties shall negotiate in good faith to resolve any disputes.',
        classification: 'Ambiguous',
        confidence: 88.0,
        score: 7.8,
        isAmbiguous: true
      },
      {
        id: '6',
        sentence: 'Delivery of goods shall occur within a reasonable timeframe.',
        classification: 'Ambiguous',
        confidence: 90.0,
        score: 8.2,
        isAmbiguous: true
      },
      {
        id: '7',
        sentence: 'The contract term is twelve (12) months from the effective date.',
        classification: 'Unambiguous',
        confidence: 96.0,
        score: 9.3,
        isAmbiguous: false
      },
      {
        id: '8',
        sentence: 'Best efforts shall be used to achieve the desired outcome.',
        classification: 'Ambiguous',
        confidence: 85.0,
        score: 7.5,
        isAmbiguous: true
      },
      {
        id: '9',
        sentence: 'The purchase price is $50,000 payable upon signing.',
        classification: 'Unambiguous',
        confidence: 99.0,
        score: 9.8,
        isAmbiguous: false
      },
      {
        id: '10',
        sentence: 'The vendor shall provide commercially reasonable support services.',
        classification: 'Ambiguous',
        confidence: 87.0,
        score: 7.9,
        isAmbiguous: true
      }
    ]
  };

  // Mock data for sentence details
  const sentenceDetails: Record<string, SentenceDetail> = {
    '1': {
      originalSentence: 'The Company shall provide reasonable efforts to ensure system availability during business hours.',
      plainEnglishExplanation: 'This sentence is unclear because "reasonable efforts" is not specifically defined. Different people might interpret this differently.',
      whyAmbiguous: [
        '"Reasonable efforts" lacks specific definition or measurable criteria',
        '"Business hours" may vary by time zone or company policy',
        'No consequences specified for failure to meet this standard'
      ],
      actions: ['Compare Models', 'Manual Score']
    },
    '2': {
      originalSentence: 'Payment shall be made within thirty (30) days of invoice receipt.',
      plainEnglishExplanation: 'This sentence is clear and specific about the payment timeline.',
      whyAmbiguous: [
        'Specific timeframe clearly defined (30 days)',
        'Clear trigger point (invoice receipt)',
        'No subjective terms used'
      ],
      actions: ['Compare Models', 'Manual Score']
    },
    '3': {
      originalSentence: 'The service will be available most of the time with occasional maintenance windows.',
      plainEnglishExplanation: 'This sentence is ambiguous because "most of the time" and "occasional" are not quantified.',
      whyAmbiguous: [
        '"Most of the time" lacks specific percentage or measurement',
        '"Occasional" maintenance windows are not defined in frequency or duration',
        'No specific uptime guarantee provided'
      ],
      actions: ['Compare Models', 'Manual Score']
    },
    '5': {
      originalSentence: 'The parties shall negotiate in good faith to resolve any disputes.',
      plainEnglishExplanation: 'This sentence is ambiguous because "good faith" is subjective and not clearly defined.',
      whyAmbiguous: [
        '"Good faith" is a subjective term without clear criteria',
        'No specific timeline for negotiations provided',
        'No consequences for failure to negotiate in good faith'
      ],
      actions: ['Compare Models', 'Manual Score']
    },
    '6': {
      originalSentence: 'Delivery of goods shall occur within a reasonable timeframe.',
      plainEnglishExplanation: 'This sentence is ambiguous because "reasonable timeframe" is not specified.',
      whyAmbiguous: [
        '"Reasonable timeframe" lacks specific definition',
        'No objective criteria for what constitutes reasonable',
        'Varies by context and interpretation'
      ],
      actions: ['Compare Models', 'Manual Score']
    },
    '8': {
      originalSentence: 'Best efforts shall be used to achieve the desired outcome.',
      plainEnglishExplanation: 'This sentence is ambiguous because "best efforts" is a high standard but not clearly defined.',
      whyAmbiguous: [
        '"Best efforts" represents a high standard without clear parameters',
        'No specific resources or actions required',
        'Subjective interpretation of what constitutes "best"'
      ],
      actions: ['Compare Models', 'Manual Score']
    },
    '10': {
      originalSentence: 'The vendor shall provide commercially reasonable support services.',
      plainEnglishExplanation: 'This sentence is ambiguous because "commercially reasonable" is context-dependent.',
      whyAmbiguous: [
        '"Commercially reasonable" varies by industry and company size',
        'No specific service levels defined',
        'Subjective interpretation based on commercial context'
      ],
      actions: ['Compare Models', 'Manual Score']
    }
  };

  const handleActionClick = (action: string) => {
    if (action === 'Compare Models') {
      navigate('/model_comparison');
    } else if (action === 'Manual Score') {
      navigate('/manual_scoring');
    }
  };

  // Calculate stats from sentences data
  const calculateStats = (sentencesData: Sentence[]): AnalysisStats => {
    const totalSentences = sentencesData.length;
    const ambiguousSentences = sentencesData.filter(s => s.isAmbiguous).length;
    const unambiguousSentences = sentencesData.filter(s => !s.isAmbiguous).length;
    
    return {
      totalSentences,
      ambiguousSentences,
      unambiguousSentences
    };
  };

  // Simulate API call
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        await new Promise(resolve => setTimeout(resolve, 600));
        setSentences(mockData.sentences);
        setStats(calculateStats(mockData.sentences));
      } catch (err) {
        setError('Failed to load sentence analysis data');
        console.error('Sentence analysis data loading error:', err);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  // Filter sentences based on search and filters
  const filteredSentences = sentences.filter(sentence => {
    const matchesSearch = sentence.sentence.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesSentenceFilter = 
      sentenceFilter === 'all' || 
      (sentenceFilter === 'ambiguous' && sentence.isAmbiguous) ||
      (sentenceFilter === 'unambiguous' && !sentence.isAmbiguous);
    
    return matchesSearch && matchesSentenceFilter;
  });

  // Update stats when filters change
  useEffect(() => {
    if (sentences.length > 0) {
      setStats(calculateStats(sentences));
    }
  }, [sentences]);

  // Pagination
  const totalPages = Math.ceil(filteredSentences.length / itemsPerPage);
  const paginatedSentences = filteredSentences.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  // Reset to first page when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, sentenceFilter]);

  // Handle eye icon click for detailed view
  const handleEyeClick = (sentenceId: string, event: React.MouseEvent) => {
    event.stopPropagation(); // Prevent row click event
    if (expandedSentenceId === sentenceId) {
      // Clicking the same eye icon closes it
      setExpandedSentenceId(null);
    } else {
      // Clicking a different eye icon opens it and closes any previously opened one
      setExpandedSentenceId(sentenceId);
    }
  };

  // Handle export CSV
  const handleExportCSV = () => {
    const headers = ['ID', 'Sentence', 'Classification', 'Confidence', 'Score', 'Is Ambiguous'];
    const csvData = filteredSentences.map(sentence => [
      sentence.id,
      `"${sentence.sentence.replace(/"/g, '""')}"`, // Escape quotes for CSV
      sentence.classification,
      sentence.confidence.toString(),
      sentence.score.toString(),
      sentence.isAmbiguous.toString()
    ]);

    const csvContent = [
      headers.join(','),
      ...csvData.map(row => row.join(','))
    ].join('\n');

    // Create and download CSV file
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', 'sentence_analysis.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (loading) {
    return (
      <div className="sentence-analysis loading">
        <div className="loading-spinner">Loading sentence analysis...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="sentence-analysis error">
        <div className="error-message">
          <h3>Error Loading Sentence Analysis</h3>
          <p>{error}</p>
          <button onClick={() => window.location.reload()} className="retry-btn">
            Retry
          </button>
        </div>
      </div>
    );
  }

  const currentStats = calculateStats(filteredSentences);

  return (
    <div className="sentence-analysis">
      {/* Page Header */}
      <div className="page-header">
        <h1>Sentence Analysis</h1>
        <p>Review ambiguous sentences and their plain-English explanations</p>
      </div>

      {/* Analysis Tools Card */}
      <div className="tools-card">
        <div className="card-header">
          <h2>Analysis Tools</h2>
          <p>Search, filter, and export sentence analysis results</p>
        </div>
        
        <div className="tools-content">
          <div className="filters-search-row">
            {/* Search Input */}
            <div className="search-section">
              <input
                type="text"
                placeholder="Search sentences..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="search-input-sentences"
              />
            </div>

            <div className="filters-row">
              <div className="filter-group">
                <label className="filter-label">Sentence Type</label>
                <select 
                  value={sentenceFilter}
                  onChange={(e) => setSentenceFilter(e.target.value)}
                  className="filter-select"
                >
                  <option value="all">All Sentences</option>
                  <option value="ambiguous">Ambiguous</option>
                  <option value="unambiguous">Unambiguous</option>
                </select>
              </div>
              
              <div className="filter-group">
                <label className="filter-label">Model</label>
                <select 
                  value={modelFilter}
                  onChange={(e) => setModelFilter(e.target.value)}
                  className="filter-select"
                >
                  <option value="ensemble">Ensemble Model</option>
                  <option value="model1">Model 1</option>
                  <option value="model2">Model 2</option>
                  <option value="model3">Model 3</option>
                </select>
              </div>
              
              <button className="export-btn" onClick={handleExportCSV}>
                Export CSV
              </button>
            </div>
          </div>

          {/* Statistics Cards */}
          {currentStats && (
            <div className="stats-cards">
              <div className="stat-card">
                <div className="stat-value">{currentStats.totalSentences}</div>
                <div className="stat-label">Total Sentences</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{currentStats.ambiguousSentences}</div>
                <div className="stat-label">Ambiguous</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{currentStats.unambiguousSentences}</div>
                <div className="stat-label">Unambiguous</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Sentence Analysis Results */}
      <div className="results-card">
        <div className="card-header">
          <h2>Sentence Analysis Results</h2>
          <p>Click on the eye icon to view detailed explanations</p>
        </div>

        <div className="table-container">
          <table className="sentences-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Sentence</th>
                <th>Classification</th>
                <th>Confidence</th>
                <th>Score</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {paginatedSentences.length > 0 ? (
                paginatedSentences.map((sentence, index) => (
                  <>
                    <tr 
                      key={sentence.id} 
                      className={`sentence-row ${expandedSentenceId === sentence.id ? 'expanded' : ''}`}
                    >
                      <td className="sentence-number">
                        {(currentPage - 1) * itemsPerPage + index + 1}
                      </td>
                      <td className="sentence-text">
                        <div className="sentence-content">
                          <span className="sentence">{sentence.sentence}</span>
                        </div>
                      </td>
                      <td className="classification">
                        <span className={`classification-badge ${sentence.isAmbiguous ? 'ambiguous' : 'unambiguous'}`}>
                          {sentence.classification}
                        </span>
                      </td>
                      <td className="confidence">
                        <span className="confidence-value">{sentence.confidence}%</span>
                      </td>
                      <td className="score">
                        <span className="score-value">{sentence.score}/10</span>
                      </td>
                      <td className="actions-sentence">
                        <button 
                          className={`eye-btn ${expandedSentenceId === sentence.id ? 'active' : ''}`}
                          onClick={(e) => handleEyeClick(sentence.id, e)}
                          title="View Details"
                        >
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                            <circle cx="12" cy="12" r="3"></circle>
                          </svg>
                        </button>
                      </td>
                    </tr>
                    {expandedSentenceId === sentence.id && sentenceDetails[sentence.id] && (
                      <tr className="sentence-detail-row">
                        <td colSpan={7} className="sentence-detail-cell">
                          <div className="sentence-detail-content">
                            <div className="detail-section">
                              <h3>Original Sentence</h3>
                              <p className="original-sentence">{sentenceDetails[sentence.id].originalSentence}</p>
                            </div>
                            
                            <div className="detail-section">
                              <h3>Plain-English Explanation</h3>
                              <p className="explanation">{sentenceDetails[sentence.id].plainEnglishExplanation}</p>
                            </div>
                            
                            <div className="detail-section">
                              <h3>Why it's considered ambiguous</h3>
                              <ul className="ambiguity-reasons">
                                {sentenceDetails[sentence.id].whyAmbiguous.map((reason, idx) => (
                                  <li key={idx}>{reason}</li>
                                ))}
                              </ul>
                            </div>
                            
                            <div className="detail-section">
                              <h3>Actions</h3>
                              <div className="action-buttons">
                                {sentenceDetails[sentence.id].actions.map((action, idx) => (
                                  <button key={idx} className="action-btn" onClick={() => handleActionClick(action)}>
                                    {action}
                                  </button>
                                ))}
                              </div>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="no-results">
                    <div className="no-results-message">
                      No sentences found matching your search criteria.
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>

          {/* Pagination */}
          {totalPages >= 1 && (
            <div className="pagination">
              <button
                className="pagination-btn"
                disabled={currentPage === 1}
                onClick={() => setCurrentPage(currentPage - 1)}
              >
                Previous
              </button>
              
              <span className="page-info">
                Page {currentPage} of {totalPages}
              </span>
              
              <button
                className="pagination-btn"
                disabled={currentPage === totalPages}
                onClick={() => setCurrentPage(currentPage + 1)}
              >
                Next
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SentenceAnalysis;