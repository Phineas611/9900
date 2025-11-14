import { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { API_BASE_URL } from '../../services/api'
import './SentenceAnalysis.css';

interface Sentence {
  id: string;
  sentence: string;
  classification: string;
  confidence: number;
  score: number;
  isAmbiguous: boolean;
  page: number;
  docName: string;
  rationale: string;
}

interface AnalysisStats {
  totalSentences: number;
  ambiguousSentences: number;
  unambiguousSentences: number;
}

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
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sentenceFilter, setSentenceFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [expandedSentenceId, setExpandedSentenceId] = useState<string | null>(null);
  const itemsPerPage = 10;

  /*
  const handleActionClick = (action: string) => {
    if (action === 'Compare Models') {
      navigate('/model_comparison');
    } else if (action === 'Manual Score') {
      navigate('/manual_scoring');
    }
  };
  */

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

  const filteredSentences = sentences.filter(sentence => {
    const matchesSearch = sentence.sentence.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesSentenceFilter = 
      sentenceFilter === 'all' || 
      (sentenceFilter === 'ambiguous' && sentence.isAmbiguous) ||
      (sentenceFilter === 'unambiguous' && !sentence.isAmbiguous);
    
    return matchesSearch && matchesSentenceFilter;
  });

  useEffect(() => {
    if (sentences.length > 0) {
      //setStats(calculateStats(filteredSentences));
    }
  }, [sentences, filteredSentences]);

  const totalPages = Math.ceil(filteredSentences.length / itemsPerPage);
  const paginatedSentences = filteredSentences.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, sentenceFilter]);

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
    ]);

    const csvContent = [
      headers.join(','),
      ...csvData.map(row => row.join(','))
    ].join('\n');

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
          <button onClick={loadSentenceData} className="retry-btn">
            Retry
          </button>
        </div>
      </div>
    );
  }

  const currentStats = calculateStats(filteredSentences);

  return (
    <div className="sentence-analysis">
      <div className="page-header">
        <h1>Sentence Analysis</h1>
        <p>Review ambiguous sentences and their explanations</p>
      </div>

      <div className="tools-card">
        <div className="card-header">
          <h2>Analysis Tools</h2>
          <p>Search, filter, and export sentence analysis results</p>
        </div>
        
        <div className="tools-content">
          <div className="filters-search-row">
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
              
              <button className="export-btn" onClick={handleExportCSV}>
                Export CSV
              </button>
            </div>
          </div>

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
                <th>Page</th>
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
                          {sentence.classification}
                        </span>
                      </td>
                      <td className="confidence">
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
                    {expandedSentenceId === sentence.id && (
                      <tr className="sentence-detail-row">
                        <td colSpan={7} className="sentence-detail-cell">
                          <div className="sentence-detail-content">
                            <div className="detail-section">
                              <h3>Original Sentence</h3>
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

          {totalPages > 1 && (
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