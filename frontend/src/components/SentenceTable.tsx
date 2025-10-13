import { useMemo, useState } from 'react';
import type { SentenceItem } from '../services/api';

type Props = {
    data: SentenceItem[];
    onClassify: (items: SentenceItem[]) => Promise<void>;
    onExplainBatch: (items: SentenceItem[]) => Promise<void>;
};

export default function SentenceTable({ data, onClassify, onExplainBatch }: Props) {
    const [selected, setSelected] = useState<Record<string, boolean>>({});

    const selectedItems = useMemo(
        () => data.filter(d => selected[d.sentenceId]),
        [data, selected]
    );

    const toggleAll = (checked: boolean) => {
        const next: Record<string, boolean> = {};
        if (checked) data.forEach(d => (next[d.sentenceId] = true));
        setSelected(next);
    };

    return (
        <div className="space-y-3">
            <div className="flex gap-2">
                <button
                    disabled={selectedItems.length === 0}
                    onClick={() => onClassify(selectedItems)}
                    className="px-3 py-1 rounded bg-black text-white disabled:opacity-50"
                >
                    Classify Selected
                </button>
                <button
                    disabled={selectedItems.length === 0}
                    onClick={() => onExplainBatch(selectedItems)}
                    className="px-3 py-1 rounded bg-black text-white disabled:opacity-50"
                >
                    Generate Explanation (Batch)
                </button>
                <div className="text-sm text-gray-500">
                    Selected {selectedItems.length} / Total {data.length}
                </div>
            </div>

            <table className="w-full border text-sm">
                <thead>
                    <tr className="bg-gray-100">
                        <th className="p-2 text-left">
                            <input type="checkbox" onChange={e => toggleAll(e.target.checked)} />
                        </th>
                        <th className="p-2 text-left">Document</th>
                        <th className="p-2 text-left">Page</th>
                        <th className="p-2 text-left" style={{ width: '50%' }}>Sentence</th>
                        <th className="p-2 text-left">Label</th>
                        <th className="p-2 text-left">Explanation</th>
                    </tr>
                </thead>
                <tbody>
                    {data.map(row => (
                        <tr key={row.sentenceId} className="border-t align-top">
                            <td className="p-2">
                                <input
                                    type="checkbox"
                                    checked={!!selected[row.sentenceId]}
                                    onChange={e =>
                                        setSelected(s => ({ ...s, [row.sentenceId]: e.target.checked }))
                                    }
                                />
                            </td>
                            <td className="p-2">{row.docName}</td>
                            <td className="p-2">{row.page ?? '-'}</td>
                            <td className="p-2" title={row.text} style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                {row.text}
                            </td>
                            <td className="p-2">
                                {row.label ? `${row.label} (${row.score?.toFixed?.(2) ?? '-'})` : '-'}
                            </td>
                            <td className="p-2" title={row.rationale} style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                {row.rationale ?? '-'}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
