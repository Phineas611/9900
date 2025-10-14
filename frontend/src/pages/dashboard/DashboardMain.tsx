import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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

interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
}

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

  // API Base URL
  const API_BASE_URL = '/api';

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
      id: String(row.job_id ?? row.id ?? Math.random()),
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
      setLoading(true);
      setError(null);

      const [statsData, uploadsData, activitiesData] = await Promise.all([
        fetchStats(),
        fetchUploads(currentPage, itemsPerPage),
        fetchActivities(),
      ]);

      setStats(statsData);
      setUploads(uploadsData.items);
      setTotalItems(uploadsData.total);
      setActivities(activitiesData);
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
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  // Reload data during initial loading and paging changes
  useEffect(() => {
    loadDashboardData();
  }, [currentPage]);

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
              <div className="stat-title">Analyzed Contracts</div>
              <div className="stat-icon"></div>
            </div>
            <div className="stat-value">{stats.certificatesGenerated}</div>
            <div className="stat-label">Sentences resulting classification</div>
            <div className={`stat-change ${stats.certificatesChange >= 0 ? 'positive' : 'negative'}`}>
              {stats.certificatesChange >= 0 ? '+' : ''}{stats.certificatesChange}% from last month
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-header">
              <div className="stat-title">Analyzed Contracts</div>
              <div className="stat-icon"></div>
            </div>
            <div className="stat-value">{stats.averageScore}/10</div>
            <div className="stat-label">Average explanation diarty</div>
            <div className={`stat-change ${stats.scoreChange >= 0 ? 'positive' : 'negative'}`}>
              {stats.scoreChange >= 0 ? '+' : ''}{stats.scoreChange} from last month
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-header">
              <div className="stat-title">Analyzed Contracts</div>
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
                    <button className="action-btn" title="View analysis">
                      
                    </button>
                    <button className="action-btn" title="Download report">
                      
                    </button>
                    <button className="action-btn" title="Share">
                      
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
