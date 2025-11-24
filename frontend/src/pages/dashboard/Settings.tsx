<<<<<<< HEAD
import { useState, useEffect } from 'react';
import './Settings.css';

interface SettingsState {
=======
import { useState } from 'react';
import './Settings.css';

interface SettingsState {
  // Model Settings
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
  defaultModel: string;
  explanationLanguage: string;
  confidenceThreshold: number;
  enableModelComparison: boolean;
<<<<<<< HEAD
=======

  // Report Templates
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
  defaultFormat: string;
  templateStyle: string;
  reportHeader: string;
  signatureBlock: string;
  includeCharts: boolean;
<<<<<<< HEAD
  retentionPeriod: string;
  autoDeleteFiles: boolean;
  exportBeforeDeletion: boolean;
=======

  // Data Retention Policy
  retentionPeriod: string;
  autoDeleteFiles: boolean;
  exportBeforeDeletion: boolean;

  // Notifications
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
  emailNotifications: boolean;
  processingComplete: boolean;
  weeklyDigest: boolean;
  securityAlerts: boolean;
<<<<<<< HEAD
=======

  // Interface Preferences
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
  theme: string;
  contextView: boolean;
  showConfidenceScores: boolean;
  highlightAmbiguousText: boolean;
}

<<<<<<< HEAD
const useTheme = () => {
  const [theme, setTheme] = useState<string>(() => {
    return localStorage.getItem('app-theme') || 'system';
  });

  useEffect(() => {
    const root = document.documentElement;
    root.classList.remove('light', 'dark', 'system', 'gray');
    if (theme !== 'system') {
      root.classList.add(theme);
    }
    localStorage.setItem('app-theme', theme);
  }, [theme]);

  return { theme, setTheme };
};

const Settings = () => {
  const { theme, setTheme } = useTheme();

  const [_, setSettings] = useState<SettingsState>({
=======
const Settings = () => {
  const [settings, setSettings] = useState<SettingsState>({
    // Model Settings
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
    defaultModel: 'Ensemble Model',
    explanationLanguage: 'Standard',
    confidenceThreshold: 70,
    enableModelComparison: true,
<<<<<<< HEAD
=======

    // Report Templates
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
    defaultFormat: 'PDF Report',
    templateStyle: 'Professional',
    reportHeader: 'Legal Contract Analysis Report',
    signatureBlock: 'Enter signature or lower text',
    includeCharts: true,
<<<<<<< HEAD
    retentionPeriod: '12 Months',
    autoDeleteFiles: true,
    exportBeforeDeletion: true,
=======

    // Data Retention Policy
    retentionPeriod: '12 Months',
    autoDeleteFiles: true,
    exportBeforeDeletion: true,

    // Notifications
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
    emailNotifications: true,
    processingComplete: true,
    weeklyDigest: true,
    securityAlerts: true,
<<<<<<< HEAD
    theme: theme,
=======

    // Interface Preferences
    theme: 'System',
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
    contextView: false,
    showConfidenceScores: true,
    highlightAmbiguousText: true,
  });

  const handleInputChange = (field: keyof SettingsState, value: any) => {
<<<<<<< HEAD
    if (field === 'theme') {
      setTheme(value);
    }
=======
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
    setSettings(prev => ({
      ...prev,
      [field]: value
    }));
  };

<<<<<<< HEAD
  /*
  const handleReset = () => {
    const defaultTheme = 'system';
    setTheme(defaultTheme);
    
=======
  const handleReset = () => {
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
    setSettings({
      defaultModel: 'Ensemble Model',
      explanationLanguage: 'Standard',
      confidenceThreshold: 70,
      enableModelComparison: true,
      defaultFormat: 'PDF Report',
      templateStyle: 'Professional',
      reportHeader: 'Legal Contract Analysis Report',
      signatureBlock: 'Enter signature or lower text',
      includeCharts: true,
      retentionPeriod: '12 Months',
      autoDeleteFiles: true,
      exportBeforeDeletion: true,
      emailNotifications: true,
      processingComplete: true,
      weeklyDigest: true,
      securityAlerts: true,
<<<<<<< HEAD
      theme: defaultTheme,
=======
      theme: 'System',
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
      contextView: false,
      showConfidenceScores: true,
      highlightAmbiguousText: true,
    });
  };

  const handleSave = () => {
    console.log('Saving settings:', settings);
    alert('Settings saved successfully!');
  };

  const ToggleSwitch = ({ 
    checked, 
    onChange, 
    disabled = false 
  }: { 
    checked: boolean; 
    onChange: (checked: boolean) => void;
    disabled?: boolean;
  }) => {
    return (
      <label className={`toggle-switch ${disabled ? 'disabled' : ''}`}>
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          disabled={disabled}
          className="toggle-input"
        />
        <span className="toggle-slider"></span>
      </label>
    );
  };
<<<<<<< HEAD
  */

  return (
    <div className="settings-page">
=======

  return (
    <div className="settings-page">
      {/* Page Header */}
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
      <div className="page-header">
        <div className="header-content">
          <div className="header-text">
            <h1>Settings</h1>
<<<<<<< HEAD
            <p>Configure application preferences</p>
          </div>
          {/*
=======
            <p>Configure models, reports, data retention, and application preferences</p>
          </div>
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
          <div className="header-actions">
            <button className="btn-secondary" onClick={handleReset}>
              Reset to Defaults
            </button>
            <button className="btn-primary" onClick={handleSave}>
              Save Changes
            </button>
          </div>
<<<<<<< HEAD
          */}
=======
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
        </div>
      </div>

      <div className="settings-content">
<<<<<<< HEAD
        {/*
=======
        {/* Model Settings */}
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
        <div className="settings-section">
          <div className="section-header">
            <div className="section-icon">🧠</div>
            <div className="section-title">
              <h2>Model Settings</h2>
              <p>Configure AI models and analysis preferences</p>
            </div>
          </div>

          <div className="settings-grid">
            <div className="settings-row">
              <div className="setting-item">
                <label className="setting-label">Default Model</label>
                <select 
                  value={settings.defaultModel}
                  onChange={(e) => handleInputChange('defaultModel', e.target.value)}
                  className="setting-input"
                >
                  <option value="Ensemble Model">Ensemble Model</option>
                  <option value="Neural Network">Neural Network</option>
                  <option value="Rule-Based">Rule-Based</option>
                  <option value="Hybrid">Hybrid Model</option>
                </select>
                <div className="setting-description">Best overall accuracy</div>
              </div>

              <div className="setting-item">
                <label className="setting-label">Explanation Language Level</label>
                <select 
                  value={settings.explanationLanguage}
                  onChange={(e) => handleInputChange('explanationLanguage', e.target.value)}
                  className="setting-input"
                >
                  <option value="Simple">Simple</option>
                  <option value="Standard">Standard</option>
                  <option value="Technical">Technical</option>
                  <option value="Legal">Legal Terminology</option>
                </select>
              </div>
            </div>

            <div className="setting-item">
              <label className="setting-label">Confidence Threshold ({settings.confidenceThreshold}%)</label>
              <input
                type="range"
                min="50"
                max="95"
                value={settings.confidenceThreshold}
                onChange={(e) => handleInputChange('confidenceThreshold', parseInt(e.target.value))}
                className="slider-input"
              />
              <div className="setting-description">
                Minimum confidence required to classify a sentence as ambiguous
              </div>
            </div>

            <div className="toggle-item">
              <div className="toggle-content">
                <div className="toggle-text">
                  <span className="toggle-label">Enable model comparison features</span>
                </div>
                <ToggleSwitch
                  checked={settings.enableModelComparison}
                  onChange={(checked) => handleInputChange('enableModelComparison', checked)}
                />
              </div>
            </div>
          </div>
        </div>

<<<<<<< HEAD
=======
        {/* Report Templates */}
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
        <div className="settings-section">
          <div className="section-header">
            <h2>Report Templates</h2>
            <p>Customize report formats and branding</p>
          </div>

          <div className="settings-grid">
            <div className="settings-row">
              <div className="setting-item">
                <label className="setting-label">Default Format</label>
                <select 
                  value={settings.defaultFormat}
                  onChange={(e) => handleInputChange('defaultFormat', e.target.value)}
                  className="setting-input"
                >
                  <option value="PDF Report">PDF Report</option>
                  <option value="Excel Spreadsheet">Excel Spreadsheet</option>
                  <option value="HTML Report">HTML Report</option>
                  <option value="Plain Text">Plain Text</option>
                </select>
              </div>

              <div className="setting-item">
                <label className="setting-label">Template Style</label>
                <select 
                  value={settings.templateStyle}
                  onChange={(e) => handleInputChange('templateStyle', e.target.value)}
                  className="setting-input"
                >
                  <option value="Professional">Professional</option>
                  <option value="Minimal">Minimal</option>
                  <option value="Corporate">Corporate</option>
                  <option value="Legal">Legal Format</option>
                </select>
              </div>
            </div>

            <div className="setting-item">
              <label className="setting-label">Report Header</label>
              <input
                type="text"
                value={settings.reportHeader}
                onChange={(e) => handleInputChange('reportHeader', e.target.value)}
                className="setting-input"
                placeholder="Enter report header text"
              />
            </div>

            <div className="setting-item">
              <label className="setting-label">Signature Block</label>
              <textarea
                value={settings.signatureBlock}
                onChange={(e) => handleInputChange('signatureBlock', e.target.value)}
                className="setting-input textarea"
                placeholder="Enter signature or footer text"
                rows={3}
              />
            </div>

            <div className="toggle-item">
              <div className="toggle-content">
                <div className="toggle-text">
                  <span className="toggle-label">Include charts and visualizations by default</span>
                </div>
                <ToggleSwitch
                  checked={settings.includeCharts}
                  onChange={(checked) => handleInputChange('includeCharts', checked)}
                />
              </div>
            </div>
          </div>
        </div>

<<<<<<< HEAD
=======
        {/* Data Retention Policy */}
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
        <div className="settings-section">
          <div className="section-header">
            <div className="section-icon">📊</div>
            <div className="section-title">
              <h2>Data Retention Policy</h2>
              <p>Configure how long analysis data is stored</p>
            </div>
          </div>

          <div className="settings-grid">
            <div className="setting-item">
              <label className="setting-label">Retention Period</label>
              <select 
                value={settings.retentionPeriod}
                onChange={(e) => handleInputChange('retentionPeriod', e.target.value)}
                className="setting-input"
              >
                <option value="3 Months">3 Months</option>
                <option value="6 Months">6 Months</option>
                <option value="12 Months">12 Months</option>
                <option value="24 Months">24 Months</option>
                <option value="Indefinite">Indefinite</option>
              </select>
            </div>

            <div className="toggle-item">
              <div className="toggle-content">
                <div className="toggle-text">
                  <span className="toggle-label">Automatically delete files after retention period</span>
                </div>
                <ToggleSwitch
                  checked={settings.autoDeleteFiles}
                  onChange={(checked) => handleInputChange('autoDeleteFiles', checked)}
                />
              </div>
            </div>

            <div className="toggle-item">
              <div className="toggle-content">
                <div className="toggle-text">
                  <span className="toggle-label">Export reports before automatic deletion</span>
                </div>
                <ToggleSwitch
                  checked={settings.exportBeforeDeletion}
                  onChange={(checked) => handleInputChange('exportBeforeDeletion', checked)}
                />
              </div>
            </div>
          </div>

          <div className="settings-note">
            Data retention policies help ensure compliance with privacy regulations. Consult your legal team before modifying these settings.
          </div>
        </div>

<<<<<<< HEAD
=======
        {/* Notifications */}
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
        <div className="settings-section">
          <div className="section-header">
            <div className="section-icon">📊</div>
            <div className="section-title">
              <h2>Notifications</h2>
              <p>Configure email alerts and notifications</p>
            </div>
          </div>

          <div className="settings-grid">
            <div className="toggle-item">
              <div className="toggle-content">
                <div className="toggle-text">
                  <span className="toggle-label">Email Notifications</span>
                  <div className="toggle-description">Receive notifications via email</div>
                </div>
                <ToggleSwitch
                  checked={settings.emailNotifications}
                  onChange={(checked) => handleInputChange('emailNotifications', checked)}
                />
              </div>
            </div>

            <div className="notification-subitems">
              <div className="toggle-item subitem">
                <div className="toggle-content">
                  <div className="toggle-text">
                    <span className="toggle-label">Processing Complete</span>
                    <div className="toggle-description">When document analysis finishes</div>
                  </div>
                  <ToggleSwitch
                    checked={settings.processingComplete}
                    onChange={(checked) => handleInputChange('processingComplete', checked)}
                    disabled={!settings.emailNotifications}
                  />
                </div>
              </div>

              <div className="toggle-item subitem">
                <div className="toggle-content">
                  <div className="toggle-text">
                    <span className="toggle-label">Weekly Digest</span>
                    <div className="toggle-description">Summary of weekly activity</div>
                  </div>
                  <ToggleSwitch
                    checked={settings.weeklyDigest}
                    onChange={(checked) => handleInputChange('weeklyDigest', checked)}
                    disabled={!settings.emailNotifications}
                  />
                </div>
              </div>

              <div className="toggle-item subitem">
                <div className="toggle-content">
                  <div className="toggle-text">
                    <span className="toggle-label">Security Alerts</span>
                    <div className="toggle-description">Important security notifications</div>
                  </div>
                  <ToggleSwitch
                    checked={settings.securityAlerts}
                    onChange={(checked) => handleInputChange('securityAlerts', checked)}
                    disabled={!settings.emailNotifications}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
<<<<<<< HEAD
        */}

=======

        {/* Interface Preferences */}
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
        <div className="settings-section">
          <div className="section-header">
            <div className="section-icon">📊</div>
            <div className="section-title">
              <h2>Interface Preferences</h2>
              <p>Customize the application appearance and behavior</p>
            </div>
          </div>

          <div className="settings-grid">
            <div className="setting-item">
              <label className="setting-label">Theme</label>
              <select 
<<<<<<< HEAD
                value={theme}
                onChange={(e) => handleInputChange('theme', e.target.value)}
                className="setting-input"
              >
                <option value="system">System</option>
                <option value="light">Light</option>
                <option value="dark">Dark</option>
                <option value="gray">Gray</option>
              </select>
            </div>

            {/*
=======
                value={settings.theme}
                onChange={(e) => handleInputChange('theme', e.target.value)}
                className="setting-input"
              >
                <option value="System">System</option>
                <option value="Light">Light</option>
                <option value="Dark">Dark</option>
                <option value="Auto">Auto</option>
              </select>
            </div>

>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
            <div className="toggle-item">
              <div className="toggle-content">
                <div className="toggle-text">
                  <span className="toggle-label">Context View</span>
                  <div className="toggle-description">Use smaller spacing and condensed layouts</div>
                </div>
                <ToggleSwitch
                  checked={settings.contextView}
                  onChange={(checked) => handleInputChange('contextView', checked)}
                />
              </div>
            </div>

            <div className="toggle-item">
              <div className="toggle-content">
                <div className="toggle-text">
                  <span className="toggle-label">Show Confidence Scores</span>
                  <div className="toggle-description">Display confidence percentages in tables</div>
                </div>
                <ToggleSwitch
                  checked={settings.showConfidenceScores}
                  onChange={(checked) => handleInputChange('showConfidenceScores', checked)}
                />
              </div>
            </div>

            <div className="toggle-item">
              <div className="toggle-content">
                <div className="toggle-text">
                  <span className="toggle-label">Highlight Ambiguous Text</span>
                  <div className="toggle-description">Visually highlight ambiguous sentences in documents</div>
                </div>
                <ToggleSwitch
                  checked={settings.highlightAmbiguousText}
                  onChange={(checked) => handleInputChange('highlightAmbiguousText', checked)}
                />
              </div>
            </div>
<<<<<<< HEAD
            */}
=======
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;