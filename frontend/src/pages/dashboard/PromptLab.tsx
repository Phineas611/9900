import React, { useEffect, useMemo, useState, useRef } from "react";
import { useSearchParams } from 'react-router-dom';
import { API_BASE_URL } from '../../services/api'

import {
  getModels,
  switchModel,
  getPrompts,
  explainOne,
  explainBatch,
  explainFile,
  type ExplainResult,
  type ModelsResponse,
} from "../../services/promptLab";
import "./PromptLab.css";

export default function PromptLab() {
  const [searchParams] = useSearchParams();
  const contract_id = searchParams.get('id'); 
  const [contractId2, setContractId2] = useState<number | "">("");
  useEffect(() => {
    if (contract_id) {
      setContractId2(Number(contract_id));
    }
  }, [contract_id]);

  // Models / prompts
  const [models, setModels] = useState<ModelsResponse | null>(null);
  const [currentModel, setCurrentModel] = useState<string | null>(null);
  const [prompts, setPrompts] = useState<string[]>([]);
  const [promptId, setPromptId] = useState<string>("amb-basic");
  const [useCustomPrompt, setUseCustomPrompt] = useState(false);
  const [customPrompt, setCustomPrompt] = useState("");

  // Single sentence
  const [singleSentence, setSingleSentence] = useState("");
  const [singleResult, setSingleResult] = useState<ExplainResult | null>(null);
  const [contractId, setContractId] = useState<number | "">("");

  // Batch
  const [batchSentencesText, setBatchSentencesText] = useState("");
  const [batchResults, setBatchResults] = useState<ExplainResult[]>([]);

  // File
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [outFmt, setOutFmt] = useState<"csv" | "xlsx">("csv");
  const [isDragOver, setIsDragOver] = useState(false);
  const [taskStatus, setTaskStatus] = useState<{
    task_id: string;
    status: string;
    message: string;
    progress: {
      current: number,
      total: number
    }
  } | null>(null);
  const [statusInterval, setStatusInterval] = useState<ReturnType<typeof setInterval> | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const handleRemoveFile = (e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    setUploadFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    // Clear any existing task status when removing file
    setTaskStatus(null);
    if (statusInterval) {
      clearInterval(statusInterval);
      setStatusInterval(null);
    }
  };

  // Drag and drop handlers
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
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];
      if (file.name.endsWith('.csv') || file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
        setUploadFile(file);
        // Clear previous task status when new file is selected
        setTaskStatus(null);
        if (statusInterval) {
          clearInterval(statusInterval);
          setStatusInterval(null);
        }
      } else {
        alert('Please upload only CSV or Excel files.');
      }
    }
  };

  async function loadModels() {
    const m = await getModels();
    setModels(m);
    setCurrentModel(m.current?.id || null);
  }

  async function doSwitchModel(id: string) {
    await switchModel(id);
    await loadModels();
  }

  async function loadPrompts() {
    const p = await getPrompts();
    setPrompts(p.prompts || []);
  }

  useEffect(() => {
    loadModels().catch(() => {});
    loadPrompts().catch(() => {});
  }, []);

  // Cleanup interval on unmount
  useEffect(() => {
    return () => {
      if (statusInterval) {
        clearInterval(statusInterval);
      }
    };
  }, [statusInterval]);

  // Single explain
  async function onExplainOne() {
    const payload = {
      sentence: singleSentence,
      prompt_id: effectivePromptId,
      custom_prompt: effectiveCustomPrompt,
      contract_id: effectiveContractId,
    };
    const res = await explainOne(payload);
    setSingleResult(res);
  }

  // Batch explain (one per line)
  async function onExplainBatch() {
    const list = batchSentencesText
      .split("\n")
      .map((s) => s.trim())
      .filter(Boolean);
    const res = await explainBatch(list, effectivePromptId, effectiveCustomPrompt, effectiveContractId);
    setBatchResults(res);
  }

  // Check task status
  async function checkTaskStatus(taskId: string) {
    try {
      const res = await fetch(`${API_BASE_URL}/promptlab/explain/file/status/${taskId}`, {
        method: "GET",
        credentials: "include",
      });
      
      if (!res.ok) {
        throw new Error(`Status check failed: ${res.status}`);
      }
      
      const statusData = await res.json();
      setTaskStatus(statusData);
      
      // If task is completed, stop polling
      if (statusData.status === 'completed' || statusData.status === 'failed') {
        if (statusInterval) {
          clearInterval(statusInterval);
          setStatusInterval(null);
        }
      }
      
      return statusData;
    } catch (error) {
      console.error('Error checking task status:', error);
      setTaskStatus(prev => prev ? {
        ...prev,
        status: 'error',
        message: `Failed to check status: ${error instanceof Error ? error.message : 'Unknown error'}`
      } : null);
      
      if (statusInterval) {
        clearInterval(statusInterval);
        setStatusInterval(null);
      }
    }
  }

  // Download result file
  async function onDownloadResult(taskId: string) {
    try {
      const res = await fetch(`${API_BASE_URL}/promptlab/explain/file/result/${taskId}`, {
        method: "GET",
        credentials: "include",
      });
      
      if (!res.ok) {
        throw new Error(`Download failed: ${res.status}`);
      }
      
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = outFmt === "xlsx" ? "promptlab_results.xlsx" : "promptlab_results.csv";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading result:', error);
      alert(`Download failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  // File upload (CSV/XLSX)
  async function onExplainFile() {
    if (!uploadFile) return;
    
    try {
      // Clear previous status
      setTaskStatus(null);

      const result = await explainFile(uploadFile, {
        prompt_id: effectivePromptId,
        custom_prompt: effectiveCustomPrompt,
        contract_id: contractId2 || undefined,
        out: outFmt,
      });
      
      // Parse the response and start polling
      const taskData = JSON.parse(result);
      setTaskStatus(taskData);
      
      // Start polling for status updates
      const interval = setInterval(() => {
        checkTaskStatus(taskData.task_id);
      }, 2000); // Check every 2 seconds
      
      setStatusInterval(interval);
      
    } catch (error) {
      console.error('Error processing file:', error);
      setTaskStatus({
        task_id: 'error',
        status: 'error',
        message: `Processing failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        progress: {current: 0, total: 0}
      });
    }
  }

  // Effective prompt selection
  const effectivePromptId = useMemo(
    () => (useCustomPrompt ? undefined : promptId),
    [useCustomPrompt, promptId]
  );
  const effectiveCustomPrompt = useMemo(
    () => (useCustomPrompt ? customPrompt : undefined),
    [useCustomPrompt, customPrompt]
  );
  const effectiveContractId = useMemo(
    () => (contractId === "" ? undefined : Number(contractId)),
    [contractId]
  );

  return (
    <div className="prompt-lab">
      <div className="page-header">
        <h1>Prompt Lab</h1>
        <p>Test and evaluate different prompts for contract analysis</p>
      </div>

      {/* Models & prompts */}
      <section className="config-panel">
        <h3>Models & Prompts</h3>
        <div className="config-section">
          <label className="config-label">Current Model</label>
          <select
            className="config-select"
            value={currentModel || ""}
            onChange={(e) => {
              setCurrentModel(e.target.value);
              doSwitchModel(e.target.value);
            }}
          >
            {(models?.available || []).map((m) => (
              <option key={m.id} value={m.id}>
                {m.name} ({m.id})
              </option>
            ))}
          </select>
          <span className="model-info">HuggingFace: {models?.current?.hf_name || "N/A"}</span>
        </div>

        <div className="config-section">
          <label className="config-label">Prompt Template</label>
          <select
            className="config-select"
            disabled={useCustomPrompt}
            value={promptId}
            onChange={(e) => setPromptId(e.target.value)}
          >
            {prompts.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={useCustomPrompt}
              onChange={(e) => setUseCustomPrompt(e.target.checked)}
            />
            Use Custom Prompt
          </label>
        </div>

        {useCustomPrompt && (
          <div className="custom-prompt-section">
            <label className="config-label">Custom Prompt</label>
            <textarea
              className="custom-prompt-input"
              placeholder="Write your custom prompt template here..."
              rows={4}
              value={customPrompt}
              onChange={(e) => setCustomPrompt(e.target.value)}
            />
          </div>
        )}
      </section>

      {/* Single sentence */}
      <section className="single-panel">
        <h3>Single Sentence Analysis</h3>
        <textarea
          className="sentence-input"
          rows={3}
          placeholder="Paste one contract sentence for analysis..."
          value={singleSentence}
          onChange={(e) => setSingleSentence(e.target.value)}
        />
        <div className="action-row">
          <label className="action-label">Contract ID</label>
          <input
            className="contract-input"
            placeholder="Optional"
            value={contractId}
            onChange={(e) => setContractId(e.target.value === "" ? "" : Number(e.target.value))}
          />
          <button className="action-btn primary" onClick={onExplainOne}>
            Explain Sentence
          </button>
        </div>

        {singleResult && (
          <div className="result-card">
            <div className="result-field">
              <span className="field-label">Label:</span>
              <span className="field-value">{singleResult.label}</span>
            </div>
            <div className="result-field">
              <span className="field-label">Model:</span>
              <span className="field-value">{singleResult.model_id}</span>
            </div>
            <div className="result-field full-width">
              <span className="field-label">Rationale:</span>
              <div className="rationale-text">{singleResult.rationale}</div>
            </div>
          </div>
        )}
      </section>

      {/* Batch (textarea) */}
      <section className="batch-panel">
        <h3>Batch Analysis</h3>
        <p className="panel-description">Enter multiple sentences, one per line</p>
        <textarea
          className="batch-input"
          rows={6}
          placeholder="Enter one sentence per line for batch analysis..."
          value={batchSentencesText}
          onChange={(e) => setBatchSentencesText(e.target.value)}
        />
        <button className="action-btn primary" onClick={onExplainBatch}>
          Analyze Batch
        </button>

        {batchResults.length > 0 && (
          <div className="batch-results">
            <h4>Analysis Results ({batchResults.length} sentences)</h4>
            <div className="results-list">
              {batchResults.map((r, i) => (
                <div key={i} className="batch-result-item">
                  <span className={`result-label ${r.label?.toLowerCase()}`}>
                    {r.label}
                  </span>
                  <span className="result-sentence">{r.sentence}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>

      {/* File upload */}
      <section className="file-panel">
        <h3>File Upload Analysis</h3>
        <div style={{marginBottom: '12px'}}>
          <label className="action-label" style={{marginRight: '12px'}}>Contract ID</label>
          <input
            className="contract-input"
            placeholder="Optional"
            value={contractId2}
            onChange={(e) => setContractId2(e.target.value === "" ? "" : Number(e.target.value))}
          />
        </div>
        <p className="panel-description">Upload CSV or Excel files for analysis</p>
        
        <div className="file-upload-area">
          <input
            type="file"
            accept=".csv,.xlsx,.xls"
            onChange={(e) => {
              setUploadFile(e.target.files?.[0] || null);
              // Clear previous task status when new file is selected
              setTaskStatus(null);
              if (statusInterval) {
                clearInterval(statusInterval);
                setStatusInterval(null);
              }
            }}
            className="file-input"
            id="file-upload"
            ref={fileInputRef}
          />
          <label 
            htmlFor="file-upload" 
            className={`file-drop-zone ${isDragOver ? 'drag-over' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <div className="file-drop-content">
              <div className="file-icon">📁</div>
              <div className="file-text">
                <div className="file-title">Choose a file or drag it here</div>
                <div className="file-subtitle">Supports CSV, XLSX files</div>
              </div>
            </div>
            {uploadFile && (
              <div className="file-preview">
                <div className="file-preview-icon">
                  {uploadFile.name.endsWith('.csv') ? '📄' : '📑'}
                </div>
                <div className="file-preview-info">
                  <div className="file-name">{uploadFile.name}</div>
                  <div className="file-size">
                    {(uploadFile.size / 1024 / 1024).toFixed(2)} MB
                  </div>
                </div>
                <button 
                  type="button"
                  className="file-remove"
                  onClick={handleRemoveFile}
                >
                  X
                </button>
              </div>
            )}
          </label>
        </div>

        {/* Task Status Display */}
        {taskStatus && uploadFile && (
          <div className="task-status-card">
            <div className="task-status-header">
              <span className="task-id">Task ID: {taskStatus.task_id}</span>
              <span className={`task-status-badge ${taskStatus.status}`}>
                {taskStatus.status === 'pending' ? taskStatus.status : `${taskStatus.status} - ${taskStatus.progress?.current || 0}/${taskStatus.progress?.total || 0}`}
              </span>
            </div>
            <div className="task-status-message">{taskStatus.message}</div>
            {taskStatus.status === 'completed' && (
              <button
                className="action-btn primary download-btn"
                onClick={() => onDownloadResult(taskStatus.task_id)}
              >
                <span className="btn-icon">⬇️</span>
                Download Results
              </button>
            )}
          </div>
        )}

        <div className="file-options">
          <div className="format-selector">
            <label className="format-label">Output Format:</label>
            <div className="radio-group">
              <label className="radio-option">
                <input 
                  type="radio" 
                  checked={outFmt === "csv"} 
                  onChange={() => setOutFmt("csv")}
                />
                <span className="radio-custom"></span>
                CSV
              </label>
              <label className="radio-option">
                <input 
                  type="radio" 
                  checked={outFmt === "xlsx"} 
                  onChange={() => setOutFmt("xlsx")} 
                />
                <span className="radio-custom"></span>
                Excel
              </label>
            </div>
          </div>

          <div className="file-action-buttons">
            <button
              className="action-btn primary large"
              onClick={onExplainFile}
              disabled={!uploadFile || (taskStatus?.status === 'pending' || taskStatus?.status === 'processing')}
            >
              <span className="btn-icon">⚡</span>
              {taskStatus && (taskStatus.status === 'pending' || taskStatus.status === 'processing') ? 'Processing...' : 'Process File'}
            </button>
          </div>
        </div>

        <div className="file-info">
          <div className="info-header">File Requirements:</div>
          <ul className="info-list">
            <li>Accepted headers: <code>sentence</code>, <code>text</code>, or <code>clause</code></li>
            <li>Maximum file size: 50MB</li>
            <li>Output columns: <code>id,sentence,label,rationale,model_id,contract_id,sentence_id</code></li>
          </ul>
        </div>
      </section>
    </div>
  );
};