// frontend/src/services/api.ts

/** ============================
 *  Shared Types
 *  ============================ */
export type Label = 'ambiguous' | 'clear';

export type SentenceItem = {
    docId: string;
    docName: string;
    page?: number;
    sentenceId: string;
    text: string;
    label?: Label;      // filled after classification
    score?: number;     // confidence (0~1)
    rationale?: string; // plain-English explanation
};

export type ClassifyRequest = { sentences: SentenceItem[]; model: string };
export type ClassifyResponse = SentenceItem[];

export type ExplainOneRequest = { text: string; model: string; prompt?: string };
export type ExplainOneResponse = {
    label: Label;
    rationale: string;
    score?: number;
    model?: string;
};

export type ExplainBatchRequest = { items: SentenceItem[]; model: string };
export type ExplainBatchResponse = SentenceItem[];

/** ============================
 *  Backend Base URL
 *  - .env: VITE_API_URL=http://localhost:8000/api
 *  - fallback: '/api' (via dev proxy)
 *  ============================ */
export const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'https://legalcontractanalyzer-backend.onrender.com/api';

/** Guard: throw on non-2xx and parse JSON as T */
async function ok<T>(res: Response): Promise<T> {
    if (!res.ok) {
        const text = await res.text().catch(() => '');
        throw new Error(`HTTP ${res.status} ${res.statusText} - ${text}`);
    }
    return (await res.json()) as T;
}

/** ============================
 *  PROJ6-2 — Extraction & Classification
 *  ============================ */
export async function getExtractedSentences(jobId: string): Promise<SentenceItem[]> {
    const res = await fetch(`${API_BASE_URL}/extract/${encodeURIComponent(jobId)}`);
    const data = await ok<{ sentences: SentenceItem[] }>(res);
    return data.sentences;
}

export async function classify(sentences: SentenceItem[], model: string) {
    const res = await fetch(`${API_BASE_URL}/classify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sentences, model } as ClassifyRequest),
    });
    return ok<ClassifyResponse>(res);
}

/** ============================
 *  PROJ6-3 — Plain-English Explanations
 *  ============================ */
export async function explainOne(text: string, model: string, prompt?: string) {
    const res = await fetch(`${API_BASE_URL}/explain`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, model, prompt } as ExplainOneRequest),
    });
    return ok<ExplainOneResponse>(res);
}

export async function explainBatch(items: SentenceItem[], model: string) {
    const res = await fetch(`${API_BASE_URL}/explain/batch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items, model } as ExplainBatchRequest),
    });
    return ok<ExplainBatchResponse>(res);
}

/** ============================
 *  Mock helpers (use when backend is not ready)
 *  ============================ */
export const mock = {
    sampleSentences(): SentenceItem[] {
        return Array.from({ length: 12 }).map((_, i) => ({
            docId: 'docA',
            docName: 'Contract_A.pdf',
            page: 1 + Math.floor(i / 3),
            sentenceId: `s${i + 1}`,
            text: `This is sample sentence ${i + 1} which may or may not be ambiguous.`,
        }));
    },

    async classify(items: SentenceItem[], _model: string): Promise<ClassifyResponse> {
        return items.map((it, idx) => ({
            ...it,
            label: idx % 2 === 0 ? 'ambiguous' : 'clear',
            score: 0.65 + (idx % 3) * 0.1,
        }));
    },

    async explainOne(text: string, model: string): Promise<ExplainOneResponse> {
        console.log(text);
        return {
            label: 'ambiguous',
            rationale:
                'The phrase “reasonable efforts” is subjective and lacks measurable criteria, which invites multiple interpretations.',
            score: 0.78,
            model,
        };
        // replace with `return await explainOne(text, model)` once backend is ready
    },

    async explainBatch(items: SentenceItem[], _model: string): Promise<ExplainBatchResponse> {
        return items.map((it) => ({
            ...it,
            rationale:
                'Ambiguity arises from undefined or subjective terms (e.g., “reasonable”, “timely”). Consider specifying objective thresholds.',
        }));
    },
};
