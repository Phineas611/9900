import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import './UploadPage.css';

const UploadPage = () => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  
  // API base URL
  const API_BASE_URL = '/api';

  // Handle drag events
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  // Handle file drop
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const files = Array.from(e.dataTransfer.files);
      handleFiles(files);
    }
  };

  // Handle file selection
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const files = Array.from(e.target.files);
      handleFiles(files);
    }
  };

  // Validate and process files
  const handleFiles = (files: File[]) => {
    const validFiles: File[] = [];
    const errors: string[] = [];

    files.forEach(file => {
      // Check file type
      const validTypes = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain'
      ];
      const fileExtension = file.name.split('.').pop()?.toLowerCase();

      if (!validTypes.includes(file.type) && !['pdf', 'docx', 'txt'].includes(fileExtension || '')) {
        errors.push(`${file.name}: Invalid file type. Only PDF, DOCX, and TXT files are allowed.`);
        return;
      }

      // Check file size (10MB)
      if (file.size > 10 * 1024 * 1024) {
        errors.push(`${file.name}: File size exceeds 10MB limit.`);
        return;
      }

      validFiles.push(file);
    });

    if (errors.length > 0) {
      setError(errors.join('\n'));
    } else {
      setError(null);
    }

    if (validFiles.length > 0) {
      setSelectedFiles(prev => [...prev, ...validFiles]);
    }
  };

  // Process file upload
  const handleUpload = async () => {
    if (selectedFiles.length === 0) return;

    setUploading(true);
    setError(null);

    try {
      // Upload files sequentially
      for (const file of selectedFiles) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE_URL}/uploads/`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
          body: formData,
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ message: 'Upload failed' }));
          throw new Error(errorData.message || `Upload failed for ${file.name}`);
        }

        const result = await response.json();
        console.log('Upload successful:', result);
      }

      // Upload completed successfully
      setSelectedFiles([]);
      setShowSuccessModal(true);
    } catch (err) {
      console.error('Upload error:', err);
      setError(err instanceof Error ? err.message : 'File upload failed');
    } finally {
      setUploading(false);
    }
  };

  // Remove file from selection
  const removeFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
    setError(null);
  };

  // Clear all selected files
  const clearAllFiles = () => {
    setSelectedFiles([]);
    setError(null);
  };

  // Trigger file input click
  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  const handleModalClose = () => {
    setShowSuccessModal(false);
    navigate('/dashboard_main');
  };

  return (
    <div className="upload-page">
      <div className="upload-container">
        {/* Page Header */}
        <div className="upload-page-header">
          <h1>Upload Contract</h1>
          <p>Upload legal documents for ambiguity analysis and plain-English explanations</p>
        </div>

        {/* Upload Section */}
        <div className="upload-section">
          <h2>Document Upload</h2>
          <p className="upload-description">
            Drag and drop files or click to browse. Supports PDF, DOCX, and TXT files up to 10MB.
          </p>

          {/* Drop Zone */}
          <div
            className={`drop-zone ${dragActive ? 'drag-active' : ''} ${selectedFiles.length > 0 ? 'has-files' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={triggerFileInput}
          >
            <div className="drop-zone-content">
              <div className="upload-icon">📁</div>
              <h3>Drag and drop your files here</h3>
              <p>or</p>
              <button
                type="button"
                className="browse-btn"
                /* onClick={(e) => e.stopPropagation()} */
              >
                Browse Files
              </button>
            </div>

            {/* Hidden File Input */}
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.docx,.txt,.doc"
              onChange={handleFileSelect}
              className="file-input"
            />
          </div>

          {/* File Type Info */}
          <div className="file-types">
            <span className="file-type-tag">PDF</span>
            <span className="file-type-tag">DOCX</span>
            <span className="file-type-tag">TXT</span>
            <span className="file-type-tag">Max 10MB</span>
          </div>

          {/* Error Message */}
          {error && (
            <div className="error-message">
              <strong>Upload Error:</strong>
              <pre>{error}</pre>
            </div>
          )}

          {/* Selected Files List */}
          {selectedFiles.length > 0 && (
            <div className="selected-files">
              <div className="files-header">
                <h4>Selected Files ({selectedFiles.length})</h4>
                <button
                  className="clear-all-btn"
                  onClick={clearAllFiles}
                  disabled={uploading}
                >
                  Clear All
                </button>
              </div>
              <div className="file-list">
                {selectedFiles.map((file, index) => (
                  <div key={index} className="file-item">
                    <div className="file-info">
                      <span className="file-icon">
                        {file.type.includes('pdf') ? '📄' :
                          file.type.includes('word') || file.name.includes('.docx') ? '📝' : '📃'}
                      </span>
                      <div className="file-details">
                        <div className="file-name">{file.name}</div>
                        <div className="file-size">
                          {(file.size / (1024 * 1024)).toFixed(2)} MB
                        </div>
                      </div>
                    </div>
                    <button
                      className="remove-btn"
                      onClick={() => removeFile(index)}
                      disabled={uploading}
                      title="Remove file"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="action-buttons">
            <button
              className="cancel-btn"
              onClick={() => navigate(-1)}
              disabled={uploading}
            >
              Cancel
            </button>
            <button
              className="upload-btn"
              onClick={handleUpload}
              disabled={selectedFiles.length === 0 || uploading}
            >
              {uploading ? 'Uploading...' : `Upload ${selectedFiles.length} File${selectedFiles.length !== 1 ? 's' : ''}`}
            </button>
          </div>
        </div>
      </div>

      {/* Success Modal */}
      {showSuccessModal && (
        <div className="modal fade show" style={{ display: 'block', backgroundColor: 'rgba(0,0,0,0.5)' }} tabIndex={-1}>
          <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">Upload Successful</h5>
              </div>
              <div className="modal-body">
                <div className="text-center">
                  <div className="mb-3" style={{ fontSize: '2rem' }}>Successfully uploaded</div>
                  <p>Your files have been uploaded successfully!</p>
                  <p className="text-muted">You will be redirected to the dashboard.</p>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-success" onClick={handleModalClose}>Go to Dashboard</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UploadPage;