import React from 'react';
import { FiTrash2, FiAlertTriangle, FiCheckCircle } from 'react-icons/fi';
import { HistoryListProps } from '../types';

const HistoryList: React.FC<HistoryListProps> = ({ history, onClear }) => {
  if (history.length === 0) {
    return (
      <div className="history-container empty">
        <p>No detection history yet.</p>
      </div>
    );
  }

  return (
    <div className="history-container">
      <div className="history-header">
        <h3>Recent Detections</h3>
        <button onClick={onClear} className="btn-clear-history">
          <FiTrash2 size={16} />
          Clear All
        </button>
      </div>
      
      <div className="history-list">
        {history.map((item, index) => (
          <div key={index} className={`history-item ${item.result.toLowerCase()}`}>
            <div className="history-icon">
              {item.result === 'Spam' ? (
                <FiAlertTriangle size={18} color="#dc3545" />
              ) : (
                <FiCheckCircle size={18} color="#28a745" />
              )}
            </div>
            
            <div className="history-content">
              <div className="history-text">{item.text}</div>
              <div className="history-meta">
                <span className="history-result">{item.result}</span>
                <span className="history-confidence">
                  {Math.round(item.confidence * 100)}% confidence
                </span>
                <span className="history-time">
                  {new Date(item.timestamp).toLocaleTimeString()}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default HistoryList;
