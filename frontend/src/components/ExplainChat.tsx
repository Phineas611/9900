import { useState } from 'react';
import { explainOne, mock } from '../services/api';

export default function ExplainChat() {
    const [input, setInput] = useState('');
    const [msgs, setMsgs] = useState<{ role: 'user' | 'model'; text: string }[]>([]);
    const [loading, setLoading] = useState(false);
    const model = 'modelA'; // TODO: replace with a dropdown later

    async function onSend() {
        if (!input.trim()) return;
        const text = input.trim();
        setMsgs(m => [...m, { role: 'user', text }]);
        setInput('');
        setLoading(true);
        try {
            // Use mock while backend is not ready:
            const res = await mock.explainOne(text, model);
            // Switch to real API later:
            // const res = await explainOne(text, model);
            const pretty = `Label: ${res.label}\nScore: ${res.score}\nWhy: ${res.rationale}`;
            setMsgs(m => [...m, { role: 'model', text: pretty }]);
        } catch (e: any) {
            setMsgs(m => [...m, { role: 'model', text: `Error: ${e.message || e}` }]);
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="space-y-3">
            <div className="border rounded p-3 h-64 overflow-auto bg-gray-50">
                {msgs.map((m, i) => (
                    <div key={i} className={m.role === 'user' ? 'text-right' : 'text-left'}>
                        <div className={`inline-block px-3 py-2 my-1 rounded ${m.role === 'user' ? 'bg-black text-white' : 'bg-white border'}`}>
                            <pre className="whitespace-pre-wrap">{m.text}</pre>
                        </div>
                    </div>
                ))}
                {loading && <div className="text-sm text-gray-500">Thinking…</div>}
            </div>
            <div className="flex gap-2">
                <input
                    className="flex-1 border rounded px-3"
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    placeholder="Enter a contract sentence..."
                />
                <button onClick={onSend} className="px-3 py-1 rounded bg-black text-white">Send</button>
            </div>
        </div>
    );
}
