import { useState, useEffect } from 'react';
<<<<<<< HEAD
import { API_BASE_URL } from '../../../services/api'
=======
// import { API_BASE_URL } from '../../../services/api'
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
import './AllContracts.css';

// Types
interface ContractStats {
  totalContracts: number;
  totalContractsChange: number;
  analyzedSentences: number;
  analyzedSentencesChange: number;
  averageAmbiguityRate: number;
  averageAmbiguityRateChange: number;
  averageQualityScore: number;
  averageQualityScoreChange: number;
}

interface Contract {
  id: string;
  name: string;
  date: string;
  type: string;
  sentences: number;
  ambiguityRate: number;
  qualityScore: number;
  tags: string[];
}

<<<<<<< HEAD
=======
/*
interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
}
*/

>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
const AllContracts = () => {
  // State management
  const [stats, setStats] = useState<ContractStats | null>(null);
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Search and filter state
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);
  const [totalItems, setTotalItems] = useState(0);

  // Fetch contract statistics
  const fetchContractStats = async (): Promise<ContractStats> => {
<<<<<<< HEAD
=======
    return {
      totalContracts: 156,
      totalContractsChange: 12,
      analyzedSentences: 24567,
      analyzedSentencesChange: 8,
      averageAmbiguityRate: 7.8,
      averageAmbiguityRateChange: -8.3,
      averageQualityScore: 7.2,
      averageQualityScoreChange: 0.5
    };
    /*
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
    const response = await fetch(`${API_BASE_URL}/contracts/stats`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
    });
<<<<<<< HEAD

    if (!response.ok) {
      throw new Error('Failed to fetch contract statistics');
    }

    const result = await response.json();
    return result;
=======
    
    if (!response.ok) {
      throw new Error('Failed to fetch contract statistics');
    }
    
    const result: ApiResponse<ContractStats> = await response.json();
    return result.data;
    */
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
  };

  // Fetch contracts with filters and pagination
  const fetchContracts = async (
    page: number, 
    limit: number, 
    search: string, 
    type: string, 
<<<<<<< HEAD
    status: string
  ): Promise<{ items: Contract[]; total: number }> => {
=======
    _: string
  ): Promise<{ items: Contract[]; total: number }> => {
    const mockContracts: Contract[] = [
      {
        id: '1',
        name: 'Software_License_Agreement.pdf',
        date: '2024-01-15',
        type: 'PDF',
        sentences: 81234,
        ambiguityRate: 12.5,
        qualityScore: 8.2,
        tags: ['Software', 'License', 'Technology']
      },
      {
        id: '2',
        name: 'Employment_Contract_v2.docx',
        date: '2024-01-14',
        type: 'DOCX',
        sentences: 4567,
        ambiguityRate: 8.3,
        qualityScore: 7.8,
        tags: ['Employment', 'HR', 'Legal']
      }
    ];
  
    let filteredContracts = mockContracts;
    
    if (search) {
      filteredContracts = filteredContracts.filter(contract => 
        contract.name.toLowerCase().includes(search.toLowerCase())
      );
    }
    
    if (type) {
      filteredContracts = filteredContracts.filter(contract => 
        contract.type === type
      );
    }
  
    const startIndex = (page - 1) * limit;
    const endIndex = startIndex + limit;
    const paginatedContracts = filteredContracts.slice(startIndex, endIndex);
  
    return {
      items: paginatedContracts,
      total: filteredContracts.length
    };
    /*
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
      ...(search && { search }),
      ...(type && { type }),
      ...(status && { status }),
    });

    const response = await fetch(`${API_BASE_URL}/contracts?${params}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch contracts data');
    }
    
<<<<<<< HEAD
    const result = await response.json();
    return result;
=======
    const result: ApiResponse<{ items: Contract[]; total: number }> = await response.json();
    return result.data;
    */
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
  };

  // Load all data
  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [statsData, contractsData] = await Promise.all([
        fetchContractStats(),
        fetchContracts(currentPage, itemsPerPage, searchTerm, typeFilter, statusFilter),
      ]);

      setStats(statsData);
      setContracts(contractsData.items);
      setTotalItems(contractsData.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load contracts data');
      console.error('Contracts data loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Handle search
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1);
    loadData();
  };

  // Handle filter changes
<<<<<<< HEAD
  /*
=======
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
  const handleFilterChange = () => {
    setCurrentPage(1);
    loadData();
  };
<<<<<<< HEAD
  */
=======
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98

  // Handle pagination
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  // Initial load and when dependencies change
  useEffect(() => {
    loadData();
  }, [currentPage]);

  // Calculate total pages
  const totalPages = Math.ceil(totalItems / itemsPerPage);

  if (loading) {
    return (
      <div className="all-contracts loading">
        <div className="loading-spinner">Loading contracts...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="all-contracts error">
        <div className="error-message">
          <h3>Error Loading Contracts</h3>
          <p>{error}</p>
          <button onClick={loadData} className="retry-btn">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="all-contracts">
      {/* Search and Filter Card */}
      <div className="search-filter-card">
        <div className="card-header">
          <h3>Search & Filter</h3>
          <p>Find contracts by name, type, or tags</p>
        </div>
        
        <form onSubmit={handleSearch} className="search-filter-form">
          <div className="search-input-group">
            <input
              type="text"
              placeholder="Search contracts..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
            
            <select 
              value={typeFilter}
              onChange={(e) => {
                setTypeFilter(e.target.value);
<<<<<<< HEAD
                // handleFilterChange();
=======
                handleFilterChange();
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
              }}
              className="filter-select"
            >
              <option value="">All Types</option>
<<<<<<< HEAD
              <option value=".pdf">.pdf</option>
              <option value=".docx">.docx</option>
              <option value=".txt">.txt</option>
=======
              <option value="PDF">PDF</option>
              <option value="DOCX">DOCX</option>
              <option value="TXT">TXT</option>
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
            </select>
            
            <select 
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
<<<<<<< HEAD
                // handleFilterChange();
=======
                handleFilterChange();
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
              }}
              className="filter-select"
            >
              <option value="">All Status</option>
              <option value="completed">Completed</option>
              <option value="processing">Processing</option>
              <option value="failed">Failed</option>
            </select>
            
            <button type="submit" className="analyze-btn">
              Analyze Trends
            </button>
          </div>
        </form>
      </div>

      {/* Statistics Cards */}
      {stats && (
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-header">
              <div className="stat-title">Total Contracts</div>
              <div className="stat-icon">📋</div>
            </div>
            <div className="stat-value">{stats.totalContracts}</div>
            <div className="stat-label">Contracts analyzed</div>
            <div className={`stat-change ${stats.totalContractsChange >= 0 ? 'positive' : 'negative'}`}>
              {stats.totalContractsChange >= 0 ? '+' : ''}{stats.totalContractsChange}% from last month
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-header">
              <div className="stat-title">Analyzed Sentences</div>
              <div className="stat-icon">📝</div>
            </div>
            <div className="stat-value">{stats.analyzedSentences.toLocaleString()}</div>
            <div className="stat-label">Total sentences processed</div>
            <div className={`stat-change ${stats.analyzedSentencesChange >= 0 ? 'positive' : 'negative'}`}>
              {stats.analyzedSentencesChange >= 0 ? '+' : ''}{stats.analyzedSentencesChange}% from last month
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-header">
              <div className="stat-title">Ambiguity Rate</div>
              <div className="stat-icon">❓</div>
            </div>
            <div className="stat-value">{stats.averageAmbiguityRate}%</div>
            <div className="stat-label">Average ambiguity rate</div>
            <div className={`stat-change ${stats.averageAmbiguityRateChange <= 0 ? 'positive' : 'negative'}`}>
              {stats.averageAmbiguityRateChange >= 0 ? '+' : ''}{stats.averageAmbiguityRateChange}% from last month
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-header">
              <div className="stat-title">Quality Score</div>
              <div className="stat-icon">⭐</div>
            </div>
<<<<<<< HEAD
            <div className="stat-value">{stats.averageQualityScore.toFixed(2)}/1</div>
=======
            <div className="stat-value">{stats.averageQualityScore}/10</div>
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
            <div className="stat-label">Average quality score</div>
            <div className={`stat-change ${stats.averageQualityScoreChange >= 0 ? 'positive' : 'negative'}`}>
              {stats.averageQualityScoreChange >= 0 ? '+' : ''}{stats.averageQualityScoreChange} from last month
            </div>
          </div>
        </div>
      )}

      {/* Contracts Table */}
      <div className="contracts-table-section">
        <div className="table-header">
          <h3>Contract Analysis Results</h3>
          <div className="table-actions">
            <span className="results-count">
              Showing {contracts.length} of {totalItems} results
            </span>
          </div>
        </div>

        <div className="table-container">
          <table className="contracts-table">
            <thead>
              <tr>
                <th>Contract</th>
                <th>Date</th>
                <th>Type</th>
                <th>Sentences</th>
                <th>Ambiguity Rate</th>
                <th>Quality Score</th>
                <th>Tags</th>
              </tr>
            </thead>
            <tbody>
              {contracts.map((contract) => (
                <tr key={contract.id}>
                  <td className="contract-name">
                    <div className="name-wrapper">
                      <span className="file-icon">
<<<<<<< HEAD
                        {contract.type === '.pdf' ? '📄' : 
                         contract.type === '.docx' ? '📝' : '📃'}
=======
                        {contract.type === 'PDF' ? '📄' : 
                         contract.type === 'DOCX' ? '📝' : '📃'}
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
                      </span>
                      {contract.name}
                    </div>
                  </td>
                  <td className="contract-date">{contract.date}</td>
                  <td className="contract-type">
                    <span className="type-badge">{contract.type}</span>
                  </td>
                  <td className="contract-sentences">{contract.sentences.toLocaleString()}</td>
                  <td className="ambiguity-rate">
                    <div className="rate-display">
                      <span className="rate-value">{contract.ambiguityRate}%</span>
                      <div className="rate-bar">
                        <div 
                          className="rate-fill" 
                          style={{ width: `${contract.ambiguityRate}%` }}
                        ></div>
                      </div>
                    </div>
                  </td>
                  <td className="quality-score">
                    <span className={`score-badge ${
                      contract.qualityScore >= 8 ? 'excellent' :
                      contract.qualityScore >= 6 ? 'good' :
                      contract.qualityScore >= 4 ? 'fair' : 'poor'
                    }`}>
                      {contract.qualityScore}/10
                    </span>
                  </td>
                  <td className="contract-tags">
                    <div className="tags-container">
                      {contract.tags.slice(0, 2).map((tag, index) => (
                        <span key={index} className="tag">
                          {tag}
                        </span>
                      ))}
                      {contract.tags.length > 2 && (
                        <span className="tag-more">+{contract.tags.length - 2}</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Pagination */}
          {totalPages >= 1 && (
            <div className="pagination">
              <button
                className="pagination-btn"
                disabled={currentPage === 1}
                onClick={() => handlePageChange(currentPage - 1)}
              >
                Previous
              </button>
              
              {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                let pageNum;
                if (totalPages <= 5) {
                  pageNum = i + 1;
                } else if (currentPage <= 3) {
                  pageNum = i + 1;
                } else if (currentPage >= totalPages - 2) {
                  pageNum = totalPages - 4 + i;
                } else {
                  pageNum = currentPage - 2 + i;
                }
                
                return (
                  <button
                    key={pageNum}
                    className={`pagination-btn ${currentPage === pageNum ? 'active' : ''}`}
                    onClick={() => handlePageChange(pageNum)}
                  >
                    {pageNum}
                  </button>
                );
              })}
              
              <button
                className="pagination-btn"
                disabled={currentPage === totalPages}
                onClick={() => handlePageChange(currentPage + 1)}
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

export default AllContracts;