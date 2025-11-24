<<<<<<< HEAD
import { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { API_BASE_URL } from '../../services/api'
import './SentenceAnalysis.css';

=======
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './SentenceAnalysis.css';

// Types
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
interface Sentence {
  id: string;
  sentence: string;
  classification: string;
  confidence: number;
  score: number;
  isAmbiguous: boolean;
<<<<<<< HEAD
  page: number;
  docName: string;
  rationale: string;
=======
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
}

interface AnalysisStats {
  totalSentences: number;
  ambiguousSentences: number;
  unambiguousSentences: number;
}

<<<<<<< HEAD
interface ApiSentence {
  docId: string;
  docName: string;
  page: number;
  sentenceId: string;
  text: string;
  label: string | null;
  score: number | null;
  rationale: string;
}

interface ImportResponse {
  contract_id: number;
  job_id: string;
  imported_count: number;
  csv_path: string;
}

interface ExtractResponse {
  sentences: ApiSentence[];
}

const SentenceAnalysis = () => {
  const [searchParams] = useSearchParams();
  const contract_id = searchParams.get('id'); 
  const [sentences, setSentences] = useState<Sentence[]>([]);
  //const [stats, setStats] = useState<AnalysisStats | null>(null);
=======
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
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sentenceFilter, setSentenceFilter] = useState('all');
<<<<<<< HEAD
=======
  const [modelFilter, setModelFilter] = useState('ensemble');
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
  const [currentPage, setCurrentPage] = useState(1);
  const [expandedSentenceId, setExpandedSentenceId] = useState<string | null>(null);
  const itemsPerPage = 10;

<<<<<<< HEAD
  /*
=======
  console.log(stats);

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

>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
  const handleActionClick = (action: string) => {
    if (action === 'Compare Models') {
      navigate('/model_comparison');
    } else if (action === 'Manual Score') {
      navigate('/manual_scoring');
    }
  };
<<<<<<< HEAD
  */

=======

  // Calculate stats from sentences data
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
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

<<<<<<< HEAD
  const fetchSentenceAnalysisData = async (contract_id: string): Promise<ImportResponse> => {
    const response = await fetch(`${API_BASE_URL}/contracts/${contract_id}/sentences/import`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Failed to import sentences');
    }

    return await response.json();
  };

  const fetchExtractedSentences = async (job_id: string): Promise<ExtractResponse> => {
    const response = await fetch(`${API_BASE_URL}/extract/${job_id}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch extracted sentences');
    }

    return await response.json();
  };

  const convertApiSentences = (apiSentences: ApiSentence[]): Sentence[] => {
    return apiSentences.map((apiSentence: ApiSentence): Sentence => {
      const hasLabel = apiSentence.label !== null;
      const classification = hasLabel ? apiSentence.label : 'Pending';
      const isAmbiguous = classification?.toUpperCase() === 'AMBIGUOUS';
      const confidence = apiSentence.score ? Math.round(apiSentence.score * 100) : 0;
      const score = apiSentence.score ? Math.round(apiSentence.score * 10) : 0;

      return {
        id: apiSentence.sentenceId,
        sentence: apiSentence.text,
        classification: classification || 'Pending',
        confidence,
        score,
        isAmbiguous,
        page: apiSentence.page,
        docName: apiSentence.docName,
        rationale: apiSentence.rationale
      };
    });
  };

  const loadSentenceData = async () => {
    if (!contract_id) {
      setError('Contract ID is missing');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const importResult = await fetchSentenceAnalysisData(contract_id);
      
      if (!importResult.job_id) {
        throw new Error('No job ID returned from import');
      }

      const extractResult = await fetchExtractedSentences(importResult.job_id);
      
      if (!extractResult.sentences || extractResult.sentences.length === 0) {
        setError('No sentences found in the document');
        return;
      }

      const convertedSentences = convertApiSentences(extractResult.sentences);
      setSentences(convertedSentences);
      //setStats(calculateStats(convertedSentences));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load sentence analysis data');
      console.error('Sentence analysis data loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  const isLoadedRef = useRef(false)
  useEffect(() => {
    if (isLoadedRef.current || !contract_id) return;
    isLoadedRef.current = true;
    loadSentenceData();
  }, [contract_id]);

=======
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
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
  const filteredSentences = sentences.filter(sentence => {
    const matchesSearch = sentence.sentence.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesSentenceFilter = 
      sentenceFilter === 'all' || 
      (sentenceFilter === 'ambiguous' && sentence.isAmbiguous) ||
      (sentenceFilter === 'unambiguous' && !sentence.isAmbiguous);
    
    return matchesSearch && matchesSentenceFilter;
  });

<<<<<<< HEAD
  useEffect(() => {
    if (sentences.length > 0) {
      //setStats(calculateStats(filteredSentences));
    }
  }, [sentences, filteredSentences]);

=======
  // Update stats when filters change
  useEffect(() => {
    if (sentences.length > 0) {
      setStats(calculateStats(sentences));
    }
  }, [sentences]);

  // Pagination
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
  const totalPages = Math.ceil(filteredSentences.length / itemsPerPage);
  const paginatedSentences = filteredSentences.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

<<<<<<< HEAD
=======
  // Reset to first page when filters change
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, sentenceFilter]);

<<<<<<< HEAD
  const handleEyeClick = (sentenceId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    setExpandedSentenceId(expandedSentenceId === sentenceId ? null : sentenceId);
  };

  const handleExportCSV = () => {
    const headers = ['ID', 'Sentence', 'Classification', 'Confidence', 'Score', 'Is Ambiguous', 'Page', 'Document', 'Rationale'];
    const csvData = filteredSentences.map(sentence => [
      sentence.id,
      `"${sentence.sentence.replace(/"/g, '""')}"`,
      sentence.classification,
      sentence.confidence.toString(),
      sentence.score.toString(),
      sentence.isAmbiguous.toString(),
      sentence.page.toString(),
      `"${sentence.docName.replace(/"/g, '""')}"`,
      `"${sentence.rationale.replace(/"/g, '""')}"`
=======
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
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
    ]);

    const csvContent = [
      headers.join(','),
      ...csvData.map(row => row.join(','))
    ].join('\n');

<<<<<<< HEAD
=======
    // Create and download CSV file
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
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
<<<<<<< HEAD
          <button onClick={loadSentenceData} className="retry-btn">
=======
          <button onClick={() => window.location.reload()} className="retry-btn">
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
            Retry
          </button>
        </div>
      </div>
    );
  }

  const currentStats = calculateStats(filteredSentences);

  return (
    <div className="sentence-analysis">
<<<<<<< HEAD
      <div className="page-header">
        <h1>Sentence Analysis</h1>
        <p>Review ambiguous sentences and their explanations</p>
      </div>

=======
      {/* Page Header */}
      <div className="page-header">
        <h1>Sentence Analysis</h1>
        <p>Review ambiguous sentences and their plain-English explanations</p>
      </div>

      {/* Analysis Tools Card */}
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
      <div className="tools-card">
        <div className="card-header">
          <h2>Analysis Tools</h2>
          <p>Search, filter, and export sentence analysis results</p>
        </div>
        
        <div className="tools-content">
          <div className="filters-search-row">
<<<<<<< HEAD
=======
            {/* Search Input */}
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
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
              
<<<<<<< HEAD
=======
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
              
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
              <button className="export-btn" onClick={handleExportCSV}>
                Export CSV
              </button>
            </div>
          </div>

<<<<<<< HEAD
=======
          {/* Statistics Cards */}
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
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

<<<<<<< HEAD
=======
      {/* Sentence Analysis Results */}
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
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
<<<<<<< HEAD
                <th>Page</th>
=======
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
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
<<<<<<< HEAD
                          <span className="doc-name">
                            {sentence.docName}
                          </span>
                        </div>
                      </td>
                      <td className="classification">
                        <span className={`classification-badge ${
                          sentence.classification === 'Ambiguous' ? 'ambiguous' : 
                          sentence.classification === 'Unambiguous' ? 'unambiguous' : 'pending'
                        }`}>
=======
                        </div>
                      </td>
                      <td className="classification">
                        <span className={`classification-badge ${sentence.isAmbiguous ? 'ambiguous' : 'unambiguous'}`}>
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
                          {sentence.classification}
                        </span>
                      </td>
                      <td className="confidence">
<<<<<<< HEAD
                        <span className="confidence-value">
                          {sentence.confidence > 0 ? `${sentence.confidence}%` : 'N/A'}
                        </span>
                      </td>
                      <td className="score">
                        <span className="score-value">
                          {sentence.score > 0 ? `${sentence.score}/10` : 'N/A'}
                        </span>
                      </td>
                      <td className="page-number">
                        {sentence.page}
=======
                        <span className="confidence-value">{sentence.confidence}%</span>
                      </td>
                      <td className="score">
                        <span className="score-value">{sentence.score}/10</span>
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
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
<<<<<<< HEAD
                    {expandedSentenceId === sentence.id && (
=======
                    {expandedSentenceId === sentence.id && sentenceDetails[sentence.id] && (
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
                      <tr className="sentence-detail-row">
                        <td colSpan={7} className="sentence-detail-cell">
                          <div className="sentence-detail-content">
                            <div className="detail-section">
                              <h3>Original Sentence</h3>
<<<<<<< HEAD
                              <p className="original-sentence">{sentence.sentence}</p>
                            </div>
                            
                            <div className="detail-section">
                              <h3>Explanation</h3>
                              <p className="explanation">
                                {sentence.rationale || 'No explanation available.'}
                              </p>
                            </div>
                            
                            <div className="detail-section">
                              <h3>Classification Details</h3>
                              <div className="classification-details">
                                <p><strong>Type:</strong> {sentence.classification}</p>
                                <p><strong>Confidence:</strong> {sentence.confidence}%</p>
                                <p><strong>Score:</strong> {sentence.score}/10</p>
                                <p><strong>Document:</strong> {sentence.docName}</p>
                                <p><strong>Page:</strong> {sentence.page}</p>
                              </div>
                            </div>

                            {/*
                            <div className="detail-section">
                              <h3>Actions</h3>
                              <div className="action-buttons">
                                <button className="action-btn" onClick={() => handleActionClick('Compare Models')}>
                                  Compare Models
                                </button>
                                <button className="action-btn" onClick={() => handleActionClick('Manual Score')}>
                                  Manual Score
                                </button>
                              </div>
                            </div>
                            */}
=======
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
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
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

<<<<<<< HEAD
          {totalPages > 1 && (
=======
          {/* Pagination */}
          {totalPages >= 1 && (
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
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