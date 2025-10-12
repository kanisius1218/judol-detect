import React, { useState } from 'react';
import { FiUpload, FiDownload, FiFileText } from 'react-icons/fi';
import { DetectionResult } from '../types';
import toast from 'react-hot-toast';

interface BatchDetectionProps {
  onBatchDetect: (texts: string[]) => Promise<DetectionResult[]>;
  isLoading: boolean;
}

const BatchDetection: React.FC<BatchDetectionProps> = ({ onBatchDetect, isLoading }) => {
  const [batchText, setBatchText] = useState('');
  const [results, setResults] = useState<DetectionResult[]>([]);
  const [showResults, setShowResults] = useState(false);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        const text = event.target?.result as string;
        setBatchText(text);
        toast.success('File loaded successfully!');
      };
      reader.readAsText(file);
    }
  };

  const handleBatchSubmit = async () => {
    const texts = batchText
      .split('\n')
      .map(line => line.trim())
      .filter(line => line.length > 0);

    if (texts.length === 0) {
      toast.error('Please enter at least one message');
      return;
    }

    if (texts.length > 50) {
      toast.error('Maximum 50 messages allowed at once');
      return;
    }

    try {
      const batchResults = await onBatchDetect(texts);
      setResults(batchResults);
      setShowResults(true);
      toast.success(`Analyzed ${batchResults.length} messages`);
    } catch (error) {
      toast.error('Batch detection failed');
    }
  };

  const downloadResults = () => {
    const csv = [
      'Message,Result,Confidence',
      ...results.map(r => `"${r.text}","${r.label}","${Math.round(r.confidence * 100)}%"`)
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `spam-detection-results-${Date.now()}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
    toast.success('Results downloaded!');
  };

  return (
    <div className="batch-container">
      <div className="batch-input">
        <div className="batch-header">
          <h3>Batch Detection</h3>
          <p>Enter multiple messages (one per line) or upload a text file</p>
        </div>

        <div className="batch-actions">
          <label className="btn-upload">
            <FiUpload size={18} />
            Upload File
            <input
              type="file"
              accept=".txt,.csv"
              onChange={handleFileUpload}
              style={{ display: 'none' }}
            />
          </label>
        </div>

        <textarea
          value={batchText}
          onChange={(e) => setBatchText(e.target.value)}
          placeholder="Enter messages here, one per line..."
          className="batch-textarea"
          rows={10}
          disabled={isLoading}
        />

        <div className="batch-footer">
          <span className="batch-count">
            {batchText.split('\n').filter(line => line.trim()).length} messages
          </span>
          <button
            onClick={handleBatchSubmit}
            className="btn-batch-detect"
            disabled={isLoading || !batchText.trim()}
          >
            <FiFileText size={18} />
            {isLoading ? 'Processing...' : 'Detect All'}
          </button>
        </div>
      </div>

      {showResults && results.length > 0 && (
        <div className="batch-results">
          <div className="batch-results-header">
            <h3>Results</h3>
            <button onClick={downloadResults} className="btn-download">
              <FiDownload size={18} />
              Download CSV
            </button>
          </div>

          <div className="batch-results-summary">
            <div className="summary-item">
              <span>Total:</span>
              <strong>{results.length}</strong>
            </div>
            <div className="summary-item spam">
              <span>Spam:</span>
              <strong>{results.filter(r => r.is_spam).length}</strong>
            </div>
            <div className="summary-item ham">
              <span>Ham:</span>
              <strong>{results.filter(r => !r.is_spam).length}</strong>
            </div>
          </div>

          <div className="batch-results-list">
            {results.map((result, index) => (
              <div key={index} className={`batch-result-item ${result.is_spam ? 'spam' : 'ham'}`}>
                <span className="result-index">#{index + 1}</span>
                <span className="result-text">{result.text}</span>
                <span className={`result-label ${result.is_spam ? 'spam' : 'ham'}`}>
                  {result.label}
                </span>
                <span className="result-confidence">
                  {Math.round(result.confidence * 100)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default BatchDetection;
