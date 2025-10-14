import { useEffect, useState } from 'react';
import SentenceTable from '../components/SentenceTable';

import type { SentenceItem } from '../services/api';
import { mock /*, classify, explainBatch, getExtractedSentences */ } from '../services/api';

export default function ExtractAndClassifyPage() {
    const [rows, setRows] = useState<SentenceItem[]>([]);
    const [loading, setLoading] = useState(false);
    const model = 'modelA';

    // Boot with mock sentences; later replace with getExtractedSentences(jobId)
    useEffect(() => {
        setRows(mock.sampleSentences());
    }, []);

    async function handleClassify(items: SentenceItem[]) {
        setLoading(true);
        try {
            // const res = await classify(items, model);
            const res = await mock.classify(items, model);
            const map = new Map(res.map(r => [r.sentenceId, r]));
            setRows(prev => prev.map(p => map.get(p.sentenceId) ?? p));
        } finally {
            setLoading(false);
        }
    }

    async function handleExplainBatch(items: SentenceItem[]) {
        setLoading(true);
        try {
            // const res = await explainBatch(items, model);
            const res = await mock.explainBatch(items, model);
            const map = new Map(res.map((r: SentenceItem) => [r.sentenceId, r]));
            setRows(prev => prev.map(p => map.get(p.sentenceId) ?? p));
        } finally {
            setLoading(false);
        }
    }

    function exportCSV() {
        const header = ['docName', 'page', 'sentence', 'label', 'score', 'rationale'];
        const lines = rows.map(r =>
            [r.docName, r.page ?? '', JSON.stringify(r.text), r.label ?? '', r.score ?? '', JSON.stringify(r.rationale ?? '')]
                .join(',')
        );
        const csv = [header.join(','), ...lines].join('\n');
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = 'classification_results.csv'; a.click();
        URL.revokeObjectURL(url);
    }

    const amb = rows.filter(r => r.label === 'ambiguous').length;
    const clr = rows.filter(r => r.label === 'clear').length;

    return (
        <div className="space-y-4 p-4">
            <h2 className="text-lg font-semibold">PROJ6-2 · Sentence Extraction & Classification</h2>

            <div className="flex gap-4">
                <div className="p-3 border rounded bg-white">
                    <div className="text-sm text-gray-600">Ambiguous</div>
                    <div className="text-2xl font-bold">{amb}</div>
                </div>
                <div className="p-3 border rounded bg-white">
                    <div className="text-sm text-gray-600">Clear</div>
                    <div className="text-2xl font-bold">{clr}</div>
                </div>
                <div className="p-3 border rounded bg-white">
                    <div className="text-sm text-gray-600">Total</div>
                    <div className="text-2xl font-bold">{rows.length}</div>
                </div>
                <div className="ml-auto">
                    <button onClick={exportCSV} className="px-3 py-2 rounded bg-black text-white">
                        Export CSV
                    </button>
                </div>
            </div>

            {loading && <div className="text-sm text-gray-500">Processing…</div>}

            <SentenceTable
                data={rows}
                onClassify={handleClassify}
                onExplainBatch={handleExplainBatch}
            />
        </div>
    );
}
