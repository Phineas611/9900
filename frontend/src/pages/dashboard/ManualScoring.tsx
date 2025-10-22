import { useState } from 'react';
import './ManualScoring.css';

interface ScoringCriteria {
  clarity: number;
  correctness: number;
  completeness: number;
  relevance: number;
}

const ManualScoring = () => {
  const [scores, setScores] = useState<ScoringCriteria>({
    clarity: 5,
    correctness: 5,
    completeness: 5,
    relevance: 5
  });
  const [additionalComments, setAdditionalComments] = useState('');

  // Calculate overall score
  const calculateOverallScore = (criteria: ScoringCriteria): number => {
    const total = criteria.clarity + criteria.correctness + criteria.completeness + criteria.relevance;
    return total / 4;
  };

  const overallScore = calculateOverallScore(scores);

  // Handle score change
  const handleScoreChange = (criteria: keyof ScoringCriteria, value: number) => {
    setScores(prev => ({
      ...prev,
      [criteria]: value
    }));
  };

  // Handle reset scores
  const handleResetScores = () => {
    setScores({
      clarity: 5,
      correctness: 5,
      completeness: 5,
      relevance: 5
    });
    setAdditionalComments('');
  };

  // Handle save assessment
  const handleSaveAssessment = () => {
    // Simulate save functionality
    const assessmentData = {
      scores,
      overallScore,
      additionalComments,
      timestamp: new Date().toISOString()
    };
    console.log('Saving assessment:', assessmentData);
    alert('Assessment saved successfully!');
  };

  // Get score label and color
  const getScoreInfo = (score: number) => {
    if (score >= 8) return { label: 'Excellent', color: '#38a169' };
    if (score >= 6) return { label: 'Good', color: '#3182ce' };
    if (score >= 4) return { label: 'Fair', color: '#d69e2e' };
    return { label: 'Poor', color: '#e53e3e' };
  };

  return (
    <div className="manual-scoring">
      {/* Header */}
      <div className="scoring-header">
        <h1>Manual Quality Assessment</h1>
        <p>Score the explanation quality based on defined criteria</p>
      </div>

      <div className="scoring-content">
        {/* Original Sentence Section */}
        <div className="section-card">
          <h3>Original Sentence</h3>
          <div className="content-box">
            <p className="sentence-text">
              The party shall be responsible for any damages that may arise from the use of this software, 
              unless such damages are determined to be caused by factors beyond their reasonable control.
            </p>
          </div>
        </div>

        {/* AI Explanation Section */}
        <div className="section-card">
          <h3>AI-Generated Explanation</h3>
          <div className="content-box">
            <p className="explanation-text">
              This sentence contains ambiguous terms. "Reasonable control" can be interpreted differently 
              depending on context and circumstances. The phrase lacks specific definition and could lead 
              to disputes over liability determination.
            </p>
          </div>
        </div>

        {/* Quality Assessment Section */}
        <div className="section-card">
          <h3>Quality Assessment</h3>
          <p className="section-subtitle">Rate each aspect of the explanation on a scale of 1-10:</p>

          <div className="scoring-criteria">
            {/* Clarity */}
            <div className="criterion-row">
              <div className="criterion-header">
                <span className="criterion-name">Clarity</span>
                <span className="score-display">
                  {scores.clarity}/10 
                  <span className="score-label" style={{ color: getScoreInfo(scores.clarity).color }}>
                    ({getScoreInfo(scores.clarity).label})
                  </span>
                </span>
              </div>
              <p className="criterion-description">How easy is it to understand the explanation?</p>
              <div className="slider-container">
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={scores.clarity}
                  onChange={(e) => handleScoreChange('clarity', parseInt(e.target.value))}
                  className="score-slider"
                />
                <div className="slider-labels">
                  <span>1 - Poor</span>
                  <span>10 - Excellent</span>
                </div>
              </div>
            </div>

            {/* Correctness */}
            <div className="criterion-row">
              <div className="criterion-header">
                <span className="criterion-name">Correctness</span>
                <span className="score-display">
                  {scores.correctness}/10 
                  <span className="score-label" style={{ color: getScoreInfo(scores.correctness).color }}>
                    ({getScoreInfo(scores.correctness).label})
                  </span>
                </span>
              </div>
              <p className="criterion-description">Is the explanation legally and factually accurate?</p>
              <div className="slider-container">
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={scores.correctness}
                  onChange={(e) => handleScoreChange('correctness', parseInt(e.target.value))}
                  className="score-slider"
                />
                <div className="slider-labels">
                  <span>1 - Poor</span>
                  <span>10 - Excellent</span>
                </div>
              </div>
            </div>

            {/* Completeness */}
            <div className="criterion-row">
              <div className="criterion-header">
                <span className="criterion-name">Completeness</span>
                <span className="score-display">
                  {scores.completeness}/10 
                  <span className="score-label" style={{ color: getScoreInfo(scores.completeness).color }}>
                    ({getScoreInfo(scores.completeness).label})
                  </span>
                </span>
              </div>
              <p className="criterion-description">Does the explanation cover all important aspects?</p>
              <div className="slider-container">
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={scores.completeness}
                  onChange={(e) => handleScoreChange('completeness', parseInt(e.target.value))}
                  className="score-slider"
                />
                <div className="slider-labels">
                  <span>1 - Poor</span>
                  <span>10 - Excellent</span>
                </div>
              </div>
            </div>

            {/* Relevance */}
            <div className="criterion-row">
              <div className="criterion-header">
                <span className="criterion-name">Relevance</span>
                <span className="score-display">
                  {scores.relevance}/10 
                  <span className="score-label" style={{ color: getScoreInfo(scores.relevance).color }}>
                    ({getScoreInfo(scores.relevance).label})
                  </span>
                </span>
              </div>
              <p className="criterion-description">How relevant is the explanation to the ambiguity?</p>
              <div className="slider-container">
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={scores.relevance}
                  onChange={(e) => handleScoreChange('relevance', parseInt(e.target.value))}
                  className="score-slider"
                />
                <div className="slider-labels">
                  <span>1 - Poor</span>
                  <span>10 - Excellent</span>
                </div>
              </div>
            </div>
          </div>

          {/* Overall Score */}
          <div className="overall-score">
            <div className="overall-score-header">
              <span className="overall-label">Overall Score</span>
              <span className="overall-value">
                {overallScore.toFixed(1)}/10
                <span className="overall-label-detail">(Average: {overallScore.toFixed(1)}/10)</span>
              </span>
            </div>
            <div className="score-breakdown">
              <div className="breakdown-item">
                <span>Clarity: {scores.clarity}/10</span>
              </div>
              <div className="breakdown-item">
                <span>Correctness: {scores.correctness}/10</span>
              </div>
              <div className="breakdown-item">
                <span>Completeness: {scores.completeness}/10</span>
              </div>
              <div className="breakdown-item">
                <span>Relevance: {scores.relevance}/10</span>
              </div>
            </div>
          </div>
        </div>

        {/* Additional Comments Section */}
        <div className="section-card">
          <h3>Additional Comments</h3>
          <p className="section-subtitle">Provide specific feedback or observations</p>
          <div className="comments-container">
            <textarea
              value={additionalComments}
              onChange={(e) => setAdditionalComments(e.target.value)}
              placeholder="Enter your detailed feedback, suggestions for improvement, or specific observations about this explanation..."
              className="comments-textarea"
              rows={6}
            />
          </div>
        </div>

        {/* Action Buttons */}
        <div className="actions-section">
          <button onClick={handleResetScores} className="reset-button">
            Reset Scores
          </button>
          <button onClick={handleSaveAssessment} className="save-button">
            Save Assessment
          </button>
        </div>
      </div>
    </div>
  );
};

export default ManualScoring;