import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { API_BASE_URL } from '../../services/api'
import './DashboardMain.css';

// Type definition
interface StatsData {
  contractsProcessed: number;
  growthPercentage: number;
  certificatesGenerated: number;
  certificatesChange: number;
  averageScore: number;
  scoreChange: number;
  averageTime: number;
  timeChange: number;
}

interface UploadItem {
  id: string;
  fileName: string;
  fileType: string;
  uploadedAt: string;
  status: 'Completed' | 'Processing' | 'Failed';
  analysis?: string;
}

interface ActivityItem {
  id: string;
  type: string; // accept any backend event_type
  title: string;
  description: string;
  timestamp: string;
}

/*
interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
}
*/

const DashboardMain = () => {
  const navigate = useNavigate();
  // State management
  const [stats, setStats] = useState<StatsData | null>(null);
  const [uploads, setUploads] = useState<UploadItem[]>([]);
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Paging status
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(5);
  const [totalItems, setTotalItems] = useState(0);

  // Obtain statistical data
  const fetchStats = async (): Promise<StatsData> => {
    const response = await fetch(`${API_BASE_URL}/analytics/kpi`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
    });
    if (!response.ok) {
      throw new Error('Failed to fetch stats data');
    }
    const result = await response.json();
    const mapped: StatsData = {
      contractsProcessed: result.total_contracts ?? 0,
      growthPercentage: result.growth_percentage ?? 0,
      certificatesGenerated: result.total_sentences ?? 0,
      certificatesChange: result.certificates_change_pct ?? 0,
      averageScore: result.avg_explanation_clarity ?? 0,
      scoreChange: result.score_change ?? 0,
      averageTime: Math.round(((result.avg_analysis_time_sec ?? 0) / 60) * 10) / 10,
      timeChange: result.time_change_pct ?? 0,
    };
    return mapped;
  };

  // Normalize backend status values to UI-friendly labels
  const mapStatus = (raw: any): UploadItem['status'] => {
    const v = String(raw ?? '').toLowerCase();
    if (v === 'completed' || v === 'success' || v === 'done') return 'Completed';
    if (v === 'processing' || v === 'running' || v === 'in_progress') return 'Processing';
    if (v === 'failed' || v === 'error') return 'Failed';
    // default
    return 'Completed';
  };

  // Retrieve upload records
  const fetchUploads = async (page: number, limit: number): Promise<{ items: UploadItem[]; total: number }> => {
    const response = await fetch(`${API_BASE_URL}/uploads/recent?limit=100`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
    });
    if (!response.ok) {
      throw new Error('Failed to fetch uploads data');
    }
    const rows = await response.json();
    const mapped: UploadItem[] = (rows || []).map((row: any) => ({
      id: String(row.contract_id ?? row.job_id ?? row.id ?? Math.random()),
      fileName: row.file_name ?? 'Unknown',
      fileType: row.file_type ?? 'Unknown',
      uploadedAt: row.uploaded_at ?? '',
      status: mapStatus(row.status),
      analysis: row.total_sentences != null ? `${row.total_sentences} sentences` : undefined,
    }));
    const total = mapped.length;
    const start = (page - 1) * limit;
    const end = start + limit;
    return { items: mapped.slice(start, end), total };
  };

  // Get Recent Events
  const fetchActivities = async (): Promise<ActivityItem[]> => {
  const response = await fetch(`${API_BASE_URL}/activity/recent?limit=5`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
    });
    if (!response.ok) {
      throw new Error('Failed to fetch activities data');
    }
    const rows = await response.json();
    const mapped: ActivityItem[] = (rows || []).map((row: any) => ({
      id: String(row.id ?? Math.random()),
      type: String(row.event_type ?? 'System Update'),
      title: row.title ?? '',
      description: row.message ?? '',
      timestamp: row.created_at ?? '',
    }));
    return mapped;
  };

  // Load all data
  const loadDashboardData = async () => {
    try {
      // setLoading(true);
      setError(null);

      const [statsData, uploadsData, activitiesData] = await Promise.all([
        fetchStats(),
        fetchUploads(currentPage, itemsPerPage),
        fetchActivities(),
      ]);

      setStats(statsData);
      setActivities(activitiesData);
      console.log(uploadsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
      console.error('Dashboard data loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Handle upload button click - navigate to upload page
  const handleUploadClick = () => {
    navigate('/upload');
  };

  // Handle pagination changes
  const handlePageChange = async (page: number) => {
    try {
      const uploadsData = await fetchUploads(page, itemsPerPage);
      setUploads(uploadsData.items);
      setTotalItems(uploadsData.total);
      setCurrentPage(page);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load page data');
    } finally {
      setLoading(false);
    }
  };

  // Reload data during initial loading and paging changes
  useEffect(() => {
    loadDashboardData();
    handlePageChange(1);
  }, []);

  // Rendering loading status
  if (loading) {
    return (
      <div className="dashboard-main loading">
        <div className="loading-spinner">Loading...</div>
      </div>
    );
  }

  // Rendering error status
  if (error) {
    return (
      <div className="dashboard-main error">
        <div className="error-message">
          <h3>Error Loading Dashboard</h3>
          <p>{error}</p>
          <button onClick={loadDashboardData} className="retry-btn">
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Calculate pagination
  const totalPages = Math.ceil(totalItems / itemsPerPage);

  const handleSentenceAnalysisClick = (id: string) => {
    navigate(`/sentence_analysis?id=${id}`);
  };

  return (
    <div className="dashboard-main">
      {/* Page Title */}
      <div className="page-header">
        <h2>Dashboard</h2>
        <p>Overview of your contract analysis activity and insights</p>
      </div>

      {/* Statistical data card */}
      {stats && (
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-header">
              <div className="stat-title">Analyzed Contracts</div>
              <div className="stat-icon"></div>
            </div>
            <div className="stat-value">{stats.contractsProcessed}</div>
            <div className="stat-label">Total Contracts processed</div>
            <div className={`stat-change ${stats.growthPercentage >= 0 ? 'positive' : 'negative'}`}>
              {stats.growthPercentage >= 0 ? '+' : ''}{stats.growthPercentage}% from last month
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-header">
              <div className="stat-title">Total Sentences</div>
              <div className="stat-icon"></div>
            </div>
            <div className="stat-value">{stats.certificatesGenerated}</div>
            <div className="stat-label">Sentences resulting segmentation</div>
            <div className={`stat-change ${stats.certificatesChange >= 0 ? 'positive' : 'negative'}`}>
              {stats.certificatesChange >= 0 ? '+' : ''}{stats.certificatesChange}% from last month
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-header">
              <div className="stat-title">Clarity Score</div>
              <div className="stat-icon"></div>
            </div>
            <div className="stat-value">{stats.averageScore}/1</div>
            <div className="stat-label">Average explanation diarty</div>
            <div className={`stat-change ${stats.scoreChange >= 0 ? 'positive' : 'negative'}`}>
              {stats.scoreChange >= 0 ? '+' : ''}{stats.scoreChange} from last month
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-header">
              <div className="stat-title">Processing Time</div>
              <div className="stat-icon"></div>
            </div>
            <div className="stat-value">{stats.averageTime} min</div>
            <div className="stat-label">Average analysis time</div>
            <div className={`stat-change ${stats.timeChange >= 0 ? 'positive' : 'negative'}`}>
              {stats.timeChange >= 0 ? '+' : ''}{stats.timeChange}% from last month
            </div>
          </div>
        </div>
      )}

      {/* Recently uploaded form */}
      <div className="recent-uploads-section">
        <h3>Recent Uploads</h3>
        <p>Your latest contract analysis results</p>

        <div className="uploads-table-container">
          <table className="uploads-table">
            <thead>
              <tr>
                <th>Filename</th>
                <th>Type</th>
                <th>Uploaded</th>
                <th>Status</th>
                <th>Analysis</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {uploads.map((upload) => (
                <tr key={upload.id}>
                  <td className="filename">{upload.fileName}</td>
                  <td className="file-type">{upload.fileType}</td>
                  <td className="upload-date">{upload.uploadedAt}</td>
                  <td>
                    <span className={`status-badge status-${upload.status.toLowerCase()}`}>
                      {upload.status}
                    </span>
                  </td>
                  <td className="analysis">
                    {upload.analysis || ''}
                  </td>
                  <td className="actions">
                    <button className="action-btn-dashboard-main" title="View analysis" onClick={() => handleSentenceAnalysisClick(upload.id)}>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                        <circle cx="12" cy="12" r="3"></circle>
                      </svg>
                    </button>
                    <button className="action-btn-dashboard-main" title="Download report" onClick={() => window.location.href = `/api/uploads/${upload.id}/download/csv`}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                        <polyline points="7 10 12 15 17 10"></polyline>
                        <line x1="12" y1="15" x2="12" y2="3"></line>
                      </svg>
                    </button>
                    <button className="action-btn-dashboard-main" title="Go Prompt Lab" onClick={() => window.location.href = `/prompt_lab?id=${upload.id}`}>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="5" y1="12" x2="19" y2="12" />
                        <polyline points="13 6 19 12 13 18" />
                      </svg>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Paging Control */}
          {totalPages > 1 && (
            <div className="pagination">
              <button
                className="pagination-btn"
                disabled={currentPage === 1}
                onClick={() => handlePageChange(currentPage - 1)}
              >
                Previous
              </button>
              
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                <button
                  key={page}
                  className={`pagination-btn ${currentPage === page ? 'active' : ''}`}
                  onClick={() => handlePageChange(page)}
                >
                  {page}
                </button>
              ))}
              
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

      {/* Bottom quick operation area */}
      <div className="quick-actions-grid">
        <div className="upload-card">
          <h3>Quick Start</h3>
          <p>Upload a new contract to begin analysis</p>
          
          <div className="upload-section">
            <div className="file-upload-area">
              <button onClick={handleUploadClick} className="upload-btn">
                Upload New Contract
              </button>
            </div>
          </div>
        </div>

        <div className="activities-card">
          <h3>Recent Activity</h3>
          <p>Latest system updates and insights</p>
          
          <div className="activities-list">
            {activities.map((activity) => (
              <div key={activity.id} className="activity-item">
                <div className="activity-header">
                  <span className={`activity-type type-${activity.type.toLowerCase().replace(' ', '-')}`}>
                    {activity.type}
                  </span>
                  <span className="activity-time">{activity.timestamp}</span>
                </div>
                <div className="activity-title">{activity.title}</div>
                <div className="activity-description">{activity.description}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardMain;
