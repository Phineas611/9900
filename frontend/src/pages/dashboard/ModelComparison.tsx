import { useState } from 'react';
import './ModelComparison.css';

// Types
interface ModelData {
  id: string;
  name: string;
  classification: string;
  confidence: number;
  qualityScore: number;
  explanation: string;
  reasoningPoints: string[];
  processingTime: string;
}

interface ComparisonData {
  originalSentence: string;
  models: ModelData[];
}

const ModelComparison = () => {
  const [selectedModelA, setSelectedModelA] = useState<string>('legal-specialist');
  const [selectedModelB, setSelectedModelB] = useState<string>('ensemble');

  // Mock data
  const comparisonData: ComparisonData = {
    originalSentence: 'The party shall be responsible for any damages that may arise from the use of this software, unless such damages are determined to be caused by factors beyond their reasonable control.',
    models: [
      {
        id: 'ensemble',
        name: 'Ensemble Model',
        classification: 'Ambiguous',
        confidence: 85.0,
        qualityScore: 8.5,
        explanation: 'This sentence contains subjective terms like "reasonable control" which can be interpreted differently depending on context and circumstances.',
        reasoningPoints: [
          'Phrase "reasonable control" lacks specific definition',
          'Term "factors beyond" is vague and context-dependent',
          'Liability determination criteria are not clearly specified'
        ],
        processingTime: '1.20ms'
      },
      {
        id: 'legal-specialist',
        name: 'Legal Specialist',
        classification: 'Ambiguous',
        confidence: 92.0,
        qualityScore: 9.2,
        explanation: 'The language used introduces ambiguity through undefined terms and subjective qualifiers that could lead to disputes.',
        reasoningPoints: [
          'Undefined standard for "reasonable control"',
          'Subjective interpretation of causation required',
          'No clear guidelines for determining liability scope'
        ],
        processingTime: '2.00ms'
      },
      {
        id: 'general-ai',
        name: 'General AI',
        classification: 'Ambiguous',
        confidence: 78.0,
        qualityScore: 7.8,
        explanation: 'The sentence includes subjective language that may require further clarification for precise interpretation.',
        reasoningPoints: [
          'Ambiguous phrasing around responsibility',
          'Unclear scope of damages coverage',
          'Vague exception criteria'
        ],
        processingTime: '0.95ms'
      },
      {
        id: 'contract-expert',
        name: 'Contract Expert',
        classification: 'Ambiguous',
        confidence: 88.0,
        qualityScore: 8.8,
        explanation: 'The contractual language employs subjective standards that could lead to varying interpretations in dispute resolution.',
        reasoningPoints: [
          'Subjective "reasonable control" standard',
          'Ambiguous causation requirements',
          'Unclear burden of proof allocation'
        ],
        processingTime: '1.50ms'
      }
    ]
  };

  const handlePreferModel = (modelId: string) => {
    // In a real application, this would send feedback to the backend
    const modelName = comparisonData.models.find(m => m.id === modelId)?.name;
    alert(`Preference recorded for ${modelName}`);
  };

  const displayedModelA = comparisonData.models.find(model => model.id === selectedModelA);
  const displayedModelB = comparisonData.models.find(model => model.id === selectedModelB);

  return (
    <div className="model-comparison">
      {/* Page Header */}
      <div className="page-header">
        <h1>Model Comparison</h1>
        <p>Compare explanations from different AI models</p>
      </div>

      {/* Original Sentence Card */}
      <div className="sentence-card">
        <h2>Original Sentence</h2>
        <div className="sentence-content">
          <p>{comparisonData.originalSentence}</p>
        </div>
      </div>

      {/* Model Selection */}
      <div className="selection-card">
        <h3>Model Selection</h3>
        <p>Choose two models to compare their analysis</p>
        
        <div className="model-selection-grid">
          <div className="model-select-group">
            <label className="select-label">Model A</label>
            <select 
              value={selectedModelA}
              onChange={(e) => setSelectedModelA(e.target.value)}
              className="model-select"
            >
              {comparisonData.models.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.name}
                </option>
              ))}
            </select>
          </div>

          <div className="model-select-group">
            <label className="select-label">Model B</label>
            <select 
              value={selectedModelB}
              onChange={(e) => setSelectedModelB(e.target.value)}
              className="model-select"
            >
              {comparisonData.models.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Model Comparisons */}
      <div className="comparison-grid">
        {/* Model A Card */}
        {displayedModelA && (
          <div className="model-card">
            <div className="model-header">
              <h3>{displayedModelA.name}</h3>
            </div>

            {/* Classification Table */}
            <div className="classification-table">
              <table>
                <tbody>
                  <tr>
                    <td className="label">Classification</td>
                    <td className="value">{displayedModelA.classification}</td>
                  </tr>
                  <tr>
                    <td className="label">Confidence</td>
                    <td className="value">{displayedModelA.confidence}%</td>
                  </tr>
                  <tr>
                    <td className="label">Quality Score</td>
                    <td className="value">{displayedModelA.qualityScore}/10</td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Explanation */}
            <div className="explanation-section">
              <h4>Explanation</h4>
              <p>{displayedModelA.explanation}</p>
            </div>

            {/* Key Reasoning Points */}
            <div className="reasoning-section">
              <h4>Key Reasoning Points</h4>
              <ul>
                {displayedModelA.reasoningPoints.map((point, index) => (
                  <li key={index}>{point}</li>
                ))}
              </ul>
            </div>

            {/* Footer */}
            <div className="model-footer">
              <div className="processing-time">
                Processed in {displayedModelA.processingTime}
              </div>
              <button 
                className="prefer-btn"
                onClick={() => handlePreferModel(displayedModelA.id)}
              >
                Prefer This
              </button>
            </div>
          </div>
        )}

        {/* Model B Card */}
        {displayedModelB && (
          <div className="model-card">
            <div className="model-header">
              <h3>{displayedModelB.name}</h3>
            </div>

            {/* Classification Table */}
            <div className="classification-table">
              <table>
                <tbody>
                  <tr>
                    <td className="label">Classification</td>
                    <td className="value">{displayedModelB.classification}</td>
                  </tr>
                  <tr>
                    <td className="label">Confidence</td>
                    <td className="value">{displayedModelB.confidence}%</td>
                  </tr>
                  <tr>
                    <td className="label">Quality Score</td>
                    <td className="value">{displayedModelB.qualityScore}/10</td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Explanation */}
            <div className="explanation-section">
              <h4>Explanation</h4>
              <p>{displayedModelB.explanation}</p>
            </div>

            {/* Key Reasoning Points */}
            <div className="reasoning-section">
              <h4>Key Reasoning Points</h4>
              <ul>
                {displayedModelB.reasoningPoints.map((point, index) => (
                  <li key={index}>{point}</li>
                ))}
              </ul>
            </div>

            {/* Footer */}
            <div className="model-footer">
              <div className="processing-time">
                Processed in {displayedModelB.processingTime}
              </div>
              <button 
                className="prefer-btn"
                onClick={() => handlePreferModel(displayedModelB.id)}
              >
                Prefer This
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Comparison Summary */}
      <div className="summary-card">
        <h3>Comparison Summary</h3>
        <div className="summary-content">
          <div className="agreement-indicator">
            <span className="agreement-dot"></span>
            <span>Models show good agreement</span>
          </div>
          
          <div className="summary-points">
            <div className="summary-point">
              <strong>Common Findings:</strong>
              <ul>
                <li>Both models identified "reasonable control" as ambiguous</li>
                <li>Agreement on subjective nature of liability determination</li>
                <li>Similar confidence in classification</li>
              </ul>
            </div>
            
            <div className="summary-point">
              <strong>Key Differences:</strong>
              <ul>
                <li>Legal Specialist provided higher confidence score</li>
                <li>Ensemble Model processed faster</li>
                <li>Slight variation in explanation depth</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ModelComparison;