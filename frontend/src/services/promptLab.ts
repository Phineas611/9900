import { API_BASE_URL } from './api'

export type ExplainOneRequest = {
  sentence: string;
  prompt_id?: string | null;
  custom_prompt?: string | null;
  contract_id?: number | null;
};

export type ExplainResult = {
  sentence: string;
  label: string;
  rationale: string;
  model_id: string;
  contract_id?: number | null;
  sentence_id?: number | null;
};

export type ModelInfo = { id: string; name: string; hf_name: string; task: string };
export type ModelsResponse = { available: ModelInfo[]; current: ModelInfo };

export async function login(username: string, password: string) {
  const res = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) throw new Error(`Login failed: ${res.status}`);
  return res.json();
}

export async function getModels(): Promise<ModelsResponse> {
  const res = await fetch(`${API_BASE_URL}/promptlab/models`, {
    method: "GET",
    credentials: "include",
  });
  if (!res.ok) throw new Error(`getModels failed: ${res.status}`);
  return res.json();
}

export async function switchModel(model_id: string) {
  const res = await fetch(`${API_BASE_URL}/promptlab/models/switch`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model_id }),
  });
  if (!res.ok) throw new Error(`switchModel failed: ${res.status}`);
  return res.json();
}

export async function getPrompts(): Promise<{ prompts: string[] }> {
  const res = await fetch(`${API_BASE_URL}/promptlab/prompts`, {
    method: "GET",
    credentials: "include",
  });
  if (!res.ok) throw new Error(`getPrompts failed: ${res.status}`);
  return res.json();
}

export async function explainOne(payload: ExplainOneRequest): Promise<ExplainResult> {
  const res = await fetch(`${API_BASE_URL}/promptlab/explain/one`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`explainOne failed: ${res.status} ${detail}`);
  }
  return res.json();
}

export async function explainBatch(
  sentences: string[],
  prompt_id?: string,
  custom_prompt?: string,
  contract_id?: number
) {
  const res = await fetch(`${API_BASE_URL}/promptlab/explain/batch`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sentences, prompt_id, custom_prompt, contract_id }),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`explainBatch failed: ${res.status} ${detail}`);
  }
  return res.json();
}

// Upload CSV/XLSX and download CSV/XLSX with fixed header
export async function explainFile(
  file: File,
  opts: { prompt_id?: string; custom_prompt?: string; contract_id?: number; out?: "csv" | "xlsx" }
) {
  const form = new FormData();
  form.append("file", file);
  const params = new URLSearchParams();
  if (opts.prompt_id) params.set("prompt_id", opts.prompt_id);
  if (opts.custom_prompt) params.set("custom_prompt", opts.custom_prompt);
  if (typeof opts.contract_id === "number") params.set("contract_id", String(opts.contract_id));
  params.set("out", opts.out || "csv");

  const res = await fetch(`${API_BASE_URL}/promptlab/explain/file?${params.toString()}`, {
    method: "POST",
    credentials: "include",
    body: form,
  });

  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`explainFile failed: ${res.status} ${detail}`);
  }
  return await res.text();
}
