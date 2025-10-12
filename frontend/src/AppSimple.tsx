import React, { useState } from 'react';
import { FiSend, FiYoutube, FiTrash2, FiShield } from 'react-icons/fi';
import './AppSimple.css';
import api from './services/api';
import { DetectionResult } from './types';

function AppSimple() {
  const [text, setText] = useState('');
  const [result, setResult] = useState<DetectionResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [mode, setMode] = useState<'detect' | 'youtube'>('detect');

  const handleDetect = async () => {
    if (!text.trim()) return;
    
    setIsLoading(true);
    try {
      const response = await api.detectMessage(text);
      setResult(response);
    } catch (error) {
      setResult({
        is_spam: false,
        confidence: 0,
        label: 'Error',
        error: 'Detection failed'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleDetect();
    }
  };

  return (
    <div className="app-simple">
      {/* Minimal Header */}
      <header className="header-simple">
        <h1>Spam Detector</h1>
        <div className="mode-toggle">
          <button 
            className={mode === 'detect' ? 'active' : ''}
            onClick={() => setMode('detect')}
          >
            <FiShield /> Detect
          </button>
          <button 
            className={mode === 'youtube' ? 'active' : ''}
            onClick={() => setMode('youtube')}
          >
            <FiYoutube /> YouTube
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-simple">
        {mode === 'detect' ? (
          <>
            {/* Input Area */}
            <div className="input-area">
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Paste message here..."
                className="text-input"
                rows={6}
              />
              <button 
                onClick={handleDetect}
                disabled={!text.trim() || isLoading}
                className="detect-btn"
              >
                {isLoading ? (
                  <div className="spinner" />
                ) : (
                  <><FiSend /> Check</>
                )}
              </button>
            </div>

            {/* Result */}
            {result && !isLoading && (
              <div className={`result-simple ${result.is_spam ? 'spam' : 'clean'}`}>
                <div className="result-icon">
                  {result.is_spam ? '⚠️' : '✅'}
                </div>
                <div className="result-text">
                  <strong>{result.is_spam ? 'SPAM' : 'CLEAN'}</strong>
                  <span>{Math.round(result.confidence * 100)}% confidence</span>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="youtube-section">
            <div className="youtube-card">
              <FiYoutube size={48} />
              <h2>YouTube Comment Cleaner</h2>
              <p>Automatically remove spam comments from your YouTube channel</p>
              
              <div className="youtube-features">
                <div className="feature">
                  <FiShield />
                  <span>Auto-detect judol/gambling spam</span>
                </div>
                <div className="feature">
                  <FiTrash2 />
                  <span>Delete spam comments automatically</span>
                </div>
              </div>

              <div className="youtube-instructions">
                <h3>Setup Instructions:</h3>
                <ol>
                  <li>Run <code>python youtube_spam_cleaner.py</code></li>
                  <li>Authenticate with your YouTube account</li>
                  <li>Choose automatic or manual cleanup</li>
                  <li>Schedule regular cleanups (optional)</li>
                </ol>
              </div>

              <div className="youtube-stats">
                <div className="stat">
                  <span className="stat-value">95%</span>
                  <span className="stat-label">Accuracy</span>
                </div>
                <div className="stat">
                  <span className="stat-value">24/7</span>
                  <span className="stat-label">Protection</span>
                </div>
                <div className="stat">
                  <span className="stat-value">Auto</span>
                  <span className="stat-label">Cleanup</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default AppSimple;
