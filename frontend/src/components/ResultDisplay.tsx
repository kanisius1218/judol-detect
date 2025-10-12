import React from 'react';
import { FiCheckCircle, FiAlertTriangle, FiCopy } from 'react-icons/fi';
import { ResultDisplayProps } from '../types';
import toast from 'react-hot-toast';

const ResultDisplay: React.FC<ResultDisplayProps> = ({ result, isLoading }) => {
  if (isLoading) {
    return (
      <div className="result-container loading">
        <div className="loader"></div>
        <p>Analyzing message...</p>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="result-container empty">
        <p>No results yet. Enter a message to detect spam.</p>
      </div>
    );
  }

  if (result.error) {
    return (
      <div className="result-container error">
        <FiAlertTriangle size={24} />
        <h3>Error</h3>
        <p>{result.error}</p>
      </div>
    );
  }

  const confidencePercent = Math.round(result.confidence * 100);
  const isSpam = result.is_spam;

  const copyResult = () => {
    const textToCopy = `Detection: ${result.label}\nConfidence: ${confidencePercent}%\nTimestamp: ${result.timestamp || new Date().toISOString()}`;
    navigator.clipboard.writeText(textToCopy);
    toast.success('Result copied to clipboard!');
  };

  return (
    <div className={`result-container ${isSpam ? 'spam' : 'ham'}`}>
      <div className="result-header">
        <div className="result-icon">
          {isSpam ? (
            <FiAlertTriangle size={32} color="#dc3545" />
          ) : (
            <FiCheckCircle size={32} color="#28a745" />
          )}
        </div>
        <div className="result-label">
          <h2>{result.label}</h2>
          <p className="result-subtitle">
            {isSpam ? 'This message appears to be spam' : 'This message appears to be legitimate'}
          </p>
        </div>
      </div>

      <div className="confidence-section">
        <div className="confidence-label">
          <span>Confidence</span>
          <span className="confidence-value">{confidencePercent}%</span>
        </div>
        <div className="confidence-bar">
          <div 
            className="confidence-fill"
            style={{ width: `${confidencePercent}%` }}
          />
        </div>
      </div>

      <div className="result-actions">
        <button onClick={copyResult} className="btn-copy">
          <FiCopy size={16} />
          Copy Result
        </button>
      </div>

      {result.timestamp && (
        <div className="result-timestamp">
          Detected at: {new Date(result.timestamp).toLocaleString()}
        </div>
      )}
    </div>
  );
};

export default ResultDisplay;
