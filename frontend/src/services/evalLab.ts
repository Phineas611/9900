import { API_BASE_URL } from './api'

export type EvalConfig = {
  judges: { id: string; label: string }[];
  default_rubrics: string[];
};

export type EvalUploadResponse = {
  job_id: string;
  columns_detected: Record<string, string>;
  preview_rows: Record<string, any>[];
};

export type EvalRunRequest = {
  job_id: string;
  judges?: string[];
  rubrics?: Record<string, boolean>;
  custom_metrics?: string[];
};

export type EvalJobStatus = {
  job_id: string;
<<<<<<< HEAD
  status: string;
  total: number;
  progress: number;
=======
  total: number;
  finished: number;
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
  started_at?: string;
  finished_at?: string;
  judges: string[];
  rubrics: string[];
  custom_metrics: string[];
  metrics_summary: Record<string, number>;
};

export type JudgeAssessment = {
  judge_id: string;
  class_ok?: boolean;
  rationale_ok_by_rubric: Record<string, boolean>;
  custom_ok: Record<string, boolean>;
};

export type EvalRecordOut = {
  id: string;
  sentence: string;
  gold_class?: 'Ambiguous' | 'Unambiguous';
  pred_class: 'Ambiguous' | 'Unambiguous';
  rationale: string;
  judges: JudgeAssessment[];
  consensus: { class_ok_ratio?: number; rationale_pass_ratio?: number };
};

export type EvalRecordsPage = {
  page: number;
  page_size: number;
  total: number;
  items: EvalRecordOut[];
};

export async function getConfig(): Promise<EvalConfig> {
<<<<<<< HEAD
  const res = await fetch(`${API_BASE_URL}/eval-lab/config`);
=======
  const res = await fetch(`${API_BASE_URL}/config`);
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
  if (!res.ok) throw new Error('Failed to fetch config');
  return res.json();
}

export async function uploadFile(file: File): Promise<EvalUploadResponse> {
  const fd = new FormData();
  fd.append('file', file);
<<<<<<< HEAD
  const res = await fetch(`${API_BASE_URL}/eval-lab/upload`, { method: 'POST', body: fd });
=======
  const res = await fetch(`${API_BASE_URL}/upload`, { method: 'POST', body: fd });
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
  if (!res.ok) throw new Error('Upload failed');
  return res.json();
}

export async function runEval(body: EvalRunRequest): Promise<{ job_id: string; total: number; started_at?: string }> {
<<<<<<< HEAD
  const res = await fetch(`${API_BASE_URL}/eval-lab/run`, {
=======
  const res = await fetch(`${API_BASE_URL}/run`, {
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error('Run failed');
  return res.json();
}

export async function getJobStatus(jobId: string): Promise<EvalJobStatus> {
<<<<<<< HEAD
  const res = await fetch(`${API_BASE_URL}/eval-lab/jobs/${jobId}/state`);
=======
  const res = await fetch(`${API_BASE_URL}/jobs/${jobId}`);
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
  if (!res.ok) throw new Error('Status fetch failed');
  return res.json();
}

export async function listRecords(
  jobId: string,
  page = 1,
  pageSize = 12,
  judgeFilter?: string[]
): Promise<EvalRecordsPage> {
  const qp = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
    ...(judgeFilter && judgeFilter.length ? { judges: judgeFilter.join(',') } : {}),
  });
<<<<<<< HEAD
  const res = await fetch(`${API_BASE_URL}/eval-lab/jobs/${jobId}/records?${qp.toString()}`);
=======
  const res = await fetch(`${API_BASE_URL}/jobs/${jobId}/records?${qp.toString()}`);
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
  if (!res.ok) throw new Error('Records fetch failed');
  return res.json();
}

export function exportCsvUrl(jobId: string): string {
<<<<<<< HEAD
  return `${API_BASE_URL}/eval-lab/jobs/${jobId}/export.csv`;
}

export function exportXlsxUrl(jobId: string): string {
  return `${API_BASE_URL}/eval-lab/jobs/${jobId}/export.xlsx`;
=======
  return `${API_BASE_URL}/jobs/${jobId}/export.csv`;
}

export function exportXlsxUrl(jobId: string): string {
  return `${API_BASE_URL}/jobs/${jobId}/export.xlsx`;
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
}