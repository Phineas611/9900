import { useState } from 'react';
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import DashboardMain from './dashboard/DashboardMain';
import Contracts from './dashboard/Contracts';
import ModelComparison from './dashboard/ModelComparison';
import ManualScoring from './dashboard/ManualScoring';
import Reports from './dashboard/Reports';
import Settings from './dashboard/Settings';
import './DashboardPage.css';
import UploadPage from './dashboard/UploadPage';

// Definition of menu item types
interface MenuItem {
  key: string;
  label: string;
  icon: string;
  path: string;
  children?: MenuItem[];
}

const DashboardPage = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  // Menu Configuration
  const menuItems: MenuItem[] = [
    {
      key: 'dashboard',
      label: 'Dashboard',
      icon: '📊',
      path: '/dashboard_main'
    },
    {
      key: 'contracts',
      label: 'Contracts',
      icon: '📃',
      path: '/contracts'
    },
    {
      key: 'extract',
      label: 'Extract & Classify',
      icon: '🧩',
      path: '/extract-classify'

    },
    {
      key: 'explain',
      label: 'Explain (One)',
      icon: '💬',
      path: '/explain'
    },
    {
      key: 'model comparison',
      label: 'Model Comparison',
      icon: '🧠',
      path: '/model_comparison'
    },
    {
      key: 'manual scoring',
      label: 'Manual Scoring',
      icon: '⭐',
      path: '/manual_scoring'
    },
    {
      key: 'reports',
      label: 'Reports',
      icon: '📈',
      path: '/reports'
    },
    {
      key: 'settings',
      label: 'Settings',
      icon: '⚙️',
      path: '/settings',
      /*
      children: [
        {
          key: 'general settings',
          label: 'General Settings',
          icon: '🔧',
          path: '/settings/general'
        },
        {
          key: 'other settings',
          label: 'Other Settings',
          icon: '🔒',
          path: '/settings/other'
        }
      ]
      */
    }
  ];

  // Process menu clicks
  const handleMenuClick = (path: string) => {
    navigate(path);
  };

  // Check if the menu is activated
  const isActive = (path: string): boolean => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  // Recursive rendering menu item
  const renderMenuItems = (items: MenuItem[]) => {
    return items.map(item => (
      <div key={item.key} className="menu-item-wrapper">
        <div
          className={`menu-item ${isActive(item.path) ? 'active' : ''}`}
          onClick={() => handleMenuClick(item.path)}
        >
          <span className="menu-icon">{item.icon}</span>
          {!isCollapsed && <span className="menu-label">{item.label}</span>}
        </div>
        {item.children && !isCollapsed && (
          <div className="submenu">
            {renderMenuItems(item.children)}
          </div>
        )}
      </div>
    ));
  };

  return (
    <div className="dashboard-container">
      {/* Sidebar */}
      <div className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}>
        <div className="sidebar-header">
          {!isCollapsed && <h2>MENU</h2>}
          <button 
            className="collapse-btn"
            onClick={() => setIsCollapsed(!isCollapsed)}
          >
            {isCollapsed ? '→' : '←'}
          </button>
        </div>
        
        <div className="menu">
          {renderMenuItems(menuItems)}
        </div>
      </div>

      {/* Main content area */}
      <div className="main-content">
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard_main" replace />} />
          <Route path="/dashboard_main" element={<DashboardMain />} />
          <Route path="/contracts" element={<Contracts />} />
          <Route path="/model_comparison" element={<ModelComparison />} />
          <Route path="/manual_scoring" element={<ManualScoring />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/settings" element={<Settings />} />
          {/*
          <Route path="/settings" element={<Navigate to="/settings/general" replace />} />
          <Route path="/settings/general" element={<GeneralSettings />} />
          <Route path="/settings/other" element={<OtherSettings />} />
          */}

          <Route path="/upload" element={<UploadPage />} />
        </Routes>
      </div>
    </div>
  );
};

export default DashboardPage;