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
  type: 'Model Update' | 'New Feature' | 'System Update';
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
  const API_BASE_URL = 'api';

  // Obtain statistical data
  const fetchStats = async (): Promise<StatsData> => {
    const mockStats: StatsData = {
      contractsProcessed: 1245,
      growthPercentage: 12.5,
      certificatesGenerated: 1245,
      certificatesChange: 8.2,
      averageScore: 8.7,
      scoreChange: 0.5,
      averageTime: 4.5,
      timeChange: -3.2
    };
    return mockStats;

    const response = await fetch(`${API_BASE_URL}/dashboard/stats`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch stats data');
    }
    
    const result: ApiResponse<StatsData> = await response.json();
    return result.data;
  };

  // Retrieve upload records
  const fetchUploads = async (page: number, limit: number): Promise<{ items: UploadItem[]; total: number }> => {
    return {items: [], total: 0}
    const response = await fetch(
      `${API_BASE_URL}/uploads?page=${page}&limit=${limit}&sortBy=uploadedAt&sortOrder=desc`,
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to fetch uploads data');
    }
    
    const result: ApiResponse<{ items: UploadItem[]; total: number }> = await response.json();
    return result.data;
  };

  // Get Recent Events
  const fetchActivities = async (): Promise<ActivityItem[]> => {
    const mockActivities: ActivityItem[] = [
      {
        id: 'activity-1',
        type: 'Model Update',
        title: 'Contract Analysis Model v2.1 Released',
        description: 'Improved accuracy and faster processing times',
        timestamp: '2023-10-15 14:30'
      },
      {
        id: 'activity-2',
        type: 'New Feature',
        title: 'Batch Processing Now Available',
        description: 'Upload multiple contracts at once for analysis',
        timestamp: '2023-10-10 09:15'
      },
      {
        id: 'activity-3',
        type: 'System Update',
        title: 'Scheduled Maintenance Completed',
        description: 'System upgrades performed during off-peak hours',
        timestamp: '2023-10-05 18:45'
      }
    ];
    return  mockActivities;

    const response = await fetch(`${API_BASE_URL}/activities/recent`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch activities data');
    }
    
    const result: ApiResponse<ActivityItem[]> = await response.json();
    return result.data;
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
              <div className="stat-icon">📊</div>
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
              <div className="stat-icon">⚠️</div>
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
              <div className="stat-icon">✔️</div>
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
              <div className="stat-icon">🕒</div>
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
                    {upload.analysis || '—'}
                  </td>
                  <td className="actions">
                    <button className="action-btn" title="View analysis">
                      👁️
                    </button>
                    <button className="action-btn" title="Download report">
                      📄
                    </button>
                    <button className="action-btn" title="Share">
                      🔗
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