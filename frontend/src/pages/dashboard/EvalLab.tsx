import { useEffect, useMemo, useState } from 'react';
import {
  getConfig,
  uploadFile,
  runEval,
  getJobStatus,
  listRecords,
  exportCsvUrl,
  exportXlsxUrl,
  type EvalConfig,
  type EvalUploadResponse,
  type EvalJobStatus,
  type EvalRecordsPage,
} from '../../services/evalLab';
import './EvalLab.css';

const RUBRIC_KEYS = [
  'grammar',
  'word_choice',
  'cohesion',
  'conciseness',
  'completeness',
  'correctness',
  'clarity',
] as const;

export default function EvalLab() {
  const [config, setConfig] = useState<EvalConfig | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [upload, setUpload] = useState<EvalUploadResponse | null>(null);
  const [jobId, setJobId] = useState<string>('');
  const [status, setStatus] = useState<EvalJobStatus | null>(null);
  const [polling, setPolling] = useState<boolean>(false);
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(10);
  const [records, setRecords] = useState<EvalRecordsPage | null>(null);
  const [selectedJudges, setSelectedJudges] = useState<string[]>([]);
  const [rubrics, setRubrics] = useState<Record<string, boolean>>({});
  const [error, setError] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  useEffect(() => {
    getConfig()
      .then((cfg) => {
        setConfig(cfg);
        const initial = Object.fromEntries(
          (cfg.default_rubrics?.length ? cfg.default_rubrics : RUBRIC_KEYS).map((k) => [k, true])
        );
        setRubrics(initial);
        setSelectedJudges(cfg.judges.map((j) => j.id));
      })
      .catch((e) => setError(String(e)));
  }, []);

  const onUpload = async () => {
    if (!file) return;
    setError(null);
    setIsUploading(true);
    try {
      const res = await uploadFile(file);
      setUpload(res);
      setJobId(res.job_id);
    } catch (e) {
      setError(String(e));
    } finally {
      setIsUploading(false);
    }
  };

  const onRun = async () => {
    if (!jobId) return;
    setError(null);
    try {
      const judges = selectedJudges.length ? selectedJudges : config?.judges.map((j) => j.id) || [];
      setPolling(true);
      await runEval({ job_id: jobId, judges, rubrics });
      startPolling(jobId);
    } catch (e) {
      setError(String(e));
    }
  };

  const startPolling = (jid: string) => {
    const timer = setInterval(async () => {
      try {
        const s = await getJobStatus(jid);
        setStatus(s);
        if (s.status === 'DONE' || s.status === 'FAILED') {
          clearInterval(timer);
          setPolling(false);
        }
      } catch (e) {
        clearInterval(timer);
        setPolling(false);
        setError(String(e));
      }
    }, 1200);
  };

  useEffect(() => {
    if (!jobId) return;
    listRecords(jobId, page, pageSize, selectedJudges)
      .then((r) => setRecords(r))
      .catch(() => {});
  }, [jobId, status?.progress, page, pageSize, selectedJudges]);

  const progress = useMemo(() => {
    if (!status || !status.total) return 0;
    return Math.min(100, Math.round((status.progress / (status.total || 1)) * 100));
  }, [status]);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && (droppedFile.name.endsWith('.csv') || droppedFile.name.endsWith('.xlsx'))) {
      setFile(droppedFile);
    }
  };

  const isRunButtonDisabled = !jobId || polling || status?.status === 'DONE';
  const isUploadButtonDisabled = !file || isUploading;

  const mapJudgeIdToDisplayName = (id: string): string => {
    const mapping: Record<string, string> = {
      'judge-mini-a': 'judge-a-llama-3.1-8b-instant',
      'judge-mini-b': 'judge-b-prometheus-7b-v2.0',
      'judge-mini-c': 'judge-c-llama-3.3-70b-versatile',
      'groq/llama-3.1-8b-instant': 'judge-a-llama-3.1-8b-instant',
      'hf/prometheus-7b-v2.0': 'judge-b-prometheus-7b-v2.0',
      'groq/llama-3.3-70b-versatile': 'judge-c-llama-3.3-70b-versatile'
    };
    return mapping[id] || id;
  };

  return (
    <div className="eval-lab">
      <h2>Evaluation Lab</h2>
      {error && <div className="error-message">Error: {error}</div>}

      <section className="config-panel">
        <h3>Configuration</h3>
        <div className="config-section">
          <strong>Judges:</strong>
          <div className="judges-list">
            {config?.judges.map((j) => (
              <label key={j.id} className="judge-item">
                <input
                  type="checkbox"
                  checked={selectedJudges.includes(j.id)}
                  onChange={(e) => {
                    setSelectedJudges((prev) =>
                      e.target.checked ? [...prev, j.id] : prev.filter((x) => x !== j.id)
                    );
                  }}
                />
                {mapJudgeIdToDisplayName(j.label)}
              </label>
            ))}
          </div>
        </div>

        <div className="config-section">
          <strong>Rubrics:</strong>
          <div className="rubrics-list">
            {RUBRIC_KEYS.map((k) => (
              <label key={k} className="rubric-item">
                <input
                  type="checkbox"
                  checked={!!rubrics[k]}
                  onChange={(e) => setRubrics({ ...rubrics, [k]: e.target.checked })}
                />
                {k}
              </label>
            ))}
          </div>
        </div>
      </section>

      <section className="upload-panel">
        <h3>Upload & Run</h3>
        <div className="upload-controls">
          <div className="file-upload-area">
            <input 
              type="file" 
              accept=".csv,.xlsx" 
              onChange={(e) => setFile(e.target.files?.[0] || null)} 
              className="file-input"
              id="file-upload"
            />
            <label 
              htmlFor="file-upload" 
              className={`file-upload-label ${isDragOver ? 'drag-over' : ''}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <div className="upload-icon">📁</div>
              <div className="upload-text">
                <div className="upload-title">Choose File</div>
                <div className="upload-subtitle">or drag and drop files here</div>
              </div>
              <div className="file-types">CSV, XLSX up to 10MB</div>
            </label>
            {file && (
              <div className="selected-file">
                <span className="file-name">{file.name}</span>
                <span className="file-size">({(file.size / 1024 / 1024).toFixed(2)} MB)</span>
              </div>
            )}
          </div>
          <button 
            onClick={onUpload} 
            disabled={isUploadButtonDisabled} 
            className="upload-btn"
          >
            {isUploading ? 'Uploading...' : 'Upload'}
          </button>
        </div>
        {upload && (
          <div className="upload-info">
            <div className="job-id">Job ID: {upload.job_id}</div>
            <button 
              onClick={onRun} 
              disabled={isRunButtonDisabled}
              className="run-btn"
            >
              {polling ? 'Evaluating...' : status?.status === 'DONE' ? 'Evaluation Complete' : 'Start Evaluation'}
            </button>
          </div>
        )}
      </section>

      <section className="status-panel">
        <h3>Status & Summary</h3>
        {status ? (
          <div className="status-content">
            <div className="status-header">
              <div className="status-badge status-badge-running">
                {status.status === 'RUNNING' && 'Running'}
                {status.status === 'DONE' && 'Completed'}
                {status.status === 'FAILED' && 'Failed'}
                {status.status === 'PROCESSING' && 'Processing'}
              </div>
            </div>
            <div className="status-details">
              <div className="status-row">
                <span className="status-label">Start Time:  {new Date(status.started_at!).toLocaleString()}</span>
                {/*<span className="status-value">{new Date(status.started_at!).toLocaleString()}</span>*/}
              </div>
              {status.finished_at && (
                <div className="status-row">
                  <span className="status-label">Finish Time:  {new Date(status.finished_at).toLocaleString()}</span>
                  {/*<span className="status-value">{new Date(status.finished_at).toLocaleString()}</span>*/}
                </div>
              )}
              <div className="status-row">
                <span className="status-label">Progress:  {status.progress} / {status.total || 1} ({progress}%)</span>
                {/*<span className="status-value">{status.progress} / {status.total || 1} ({progress}%)</span>*/}
              </div>
            </div>
            <div className="progress-section">
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${progress}%` }} />
              </div>
            </div>
            {status.metrics_summary && Object.keys(status.metrics_summary).length > 0 && (
              <div className="metrics-summary">
                <strong>Summary:</strong>
                <div className="metrics-grid">
                  {Object.entries(status.metrics_summary).map(([k, v]) => (
                    <div key={k} className="metric-item">
                      {k}: {typeof v === 'number' ? v.toFixed(3) : String(v)}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="status-placeholder">No evaluation running or loading...</div>
        )}
      </section>

      <section className="records-panel">
        <h3>Records & Export</h3>
        {jobId ? (
          <div className="records-content">
            <div className="export-buttons">
              <button onClick={() => window.open(exportCsvUrl(jobId), '_blank')} className="export-btn">
                Export CSV
              </button>
              <button onClick={() => window.open(exportXlsxUrl(jobId), '_blank')} className="export-btn">
                Export XLSX
              </button>
            </div>
            {records ? (
              <div>
                <div className="records-count">Total: {records.total} records</div>
                <ul className="records-list">
                  {records.items.map((it) => (
                    <li key={it.id} className="record-item">
                      <div className="sentence-text">{it.sentence}</div>
                      <div className="record-meta">
                        Prediction: {it.pred_class}; Consensus:
                        {typeof it.consensus?.class_ok_ratio === 'number' && (
                          <> class_ok_ratio={it.consensus.class_ok_ratio.toFixed(2)}</>
                        )}
                        {typeof it.consensus?.rationale_pass_ratio === 'number' && (
                          <>， rationale_pass_ratio={it.consensus.rationale_pass_ratio.toFixed(2)}</>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
                <div className="pagination">
                  <button disabled={page <= 1} onClick={() => setPage((p) => Math.max(1, p - 1))}>
                    Previous
                  </button>
                  <span>Page {page}</span>
                  <button onClick={() => setPage((p) => p + 1)}>Next</button>
                  <select value={pageSize} onChange={(e) => setPageSize(Number(e.target.value))}>
                    {[10, 20, 50].map((s) => (
                      <option key={s} value={s}>{s} per page</option>
                    ))}
                  </select>
                </div>
              </div>
            ) : (
              <div>No records available</div>
            )}
          </div>
        ) : (
          <div>Please upload and run evaluation first</div>
        )}
      </section>
    </div>
  );
}