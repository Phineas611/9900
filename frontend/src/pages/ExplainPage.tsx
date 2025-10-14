import ExplainChat from '../components/ExplainChat';

export default function ExplainPage() {
    return (
        <div className="space-y-4 p-4">
            <h2 className="text-lg font-semibold">PROJ6-3 · Plain-English Explanation</h2>
            <p className="text-sm text-gray-600">
                Enter a contract sentence to get its ambiguity classification and plain-English explanation.
            </p>
            <ExplainChat />
        </div>
    );
}
