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
    try {
      const res = await uploadFile(file);
      setUpload(res);
      setJobId(res.job_id);
    } catch (e) {
      setError(String(e));
    }
  };

  const onRun = async () => {
    if (!jobId) return;
    setError(null);
    try {
      const judges = selectedJudges.length ? selectedJudges : config?.judges.map((j) => j.id) || [];
      await runEval({ job_id: jobId, judges, rubrics });
      setPolling(true);
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
        if (s.total > 0 && s.finished >= s.total) {
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
  }, [jobId, status?.finished, page, pageSize, selectedJudges]);

  const progress = useMemo(() => {
    if (!status || !status.total) return 0;
    return Math.min(100, Math.round((status.finished / status.total) * 100));
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

  return (
    <div className="eval-lab">
      <h2>Evaluation Lab</h2>
      {error && <div className="error-message">Error: {error}</div>}

      {/* Config panel */}
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
                {j.label}
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

      {/* Upload panel */}
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
          <button onClick={onUpload} disabled={!file} className="upload-btn">
            Upload
          </button>
        </div>
        {upload && (
          <div className="upload-info">
            <div className="job-id">Job ID: {upload.job_id}</div>
            <button onClick={onRun} disabled={!jobId || polling} className="run-btn">
              {polling ? 'Evaluating...' : 'Start Evaluation'}
            </button>
          </div>
        )}
      </section>

      {/* Status panel */}
      <section className="status-panel">
        <h3>Status & Summary</h3>
        {status ? (
          <div className="status-content">
            <div className="progress-info">
              Progress: {status.finished} / {status.total} ({progress}%)
            </div>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progress}%` }} />
            </div>
            <div className="metrics-summary">
              <strong>Summary:</strong>
              <div className="metrics-grid">
                {Object.entries(status.metrics_summary || {}).map(([k, v]) => (
                  <div key={k} className="metric-item">
                    {k}: {typeof v === 'number' ? v.toFixed(3) : String(v)}
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div>No evaluation running or loading...</div>
        )}
      </section>

      {/* Records panel */}
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