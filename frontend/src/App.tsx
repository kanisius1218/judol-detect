import React, { useState, useEffect } from 'react';
import { Toaster, toast } from 'react-hot-toast';
import { FiActivity, FiAlertTriangle, FiCheckCircle, FiBarChart2 } from 'react-icons/fi';
import './App.css';

// Import components
import MessageInput from './components/MessageInput';
import ResultDisplay from './components/ResultDisplay';
import StatsCard from './components/StatsCard';
import HistoryList from './components/HistoryList';
import BatchDetection from './components/BatchDetection';

// Import services and types
import api from './services/api';
import { 
  DetectionResult, 
  HistoryItem, 
  StatsResponse,
  BatchDetectionResponse 
} from './types';

function App() {
  const [activeTab, setActiveTab] = useState<'single' | 'batch' | 'history'>('single');
  const [currentResult, setCurrentResult] = useState<DetectionResult | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(true);

  // Load initial data
  useEffect(() => {
    checkConnection();
    loadHistory();
    loadStats();
    
    // Set up periodic refresh
    const interval = setInterval(() => {
      loadStats();
    }, 30000); // Refresh stats every 30 seconds

    return () => clearInterval(interval);
  }, []);

  const checkConnection = async () => {
    try {
      const connected = await api.healthCheck();
      setIsConnected(connected);
      if (!connected) {
        toast.error('Cannot connect to server. Please ensure the backend is running.');
      }
    } catch (error) {
      setIsConnected(false);
    }
  };

  const loadHistory = async () => {
    try {
      const response = await api.getHistory();
      setHistory(response.history);
    } catch (error) {
      console.error('Failed to load history:', error);
    }
  };

  const loadStats = async () => {
    try {
      const response = await api.getStats();
      setStats(response);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const handleDetect = async (text: string) => {
    setIsLoading(true);
    try {
      const result = await api.detectMessage(text);
      setCurrentResult(result);
      
      // Refresh history and stats
      await Promise.all([loadHistory(), loadStats()]);
      
      // Show toast notification
      if (result.is_spam) {
        toast.error('⚠️ Spam detected!', {
          duration: 3000,
          style: {
            background: '#000',
            color: '#fff',
            border: '2px solid #dc3545'
          }
        });
      } else {
        toast.success('✓ Message is legitimate', {
          duration: 3000,
          style: {
            background: '#000',
            color: '#fff',
            border: '2px solid #28a745'
          }
        });
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Detection failed';
      setCurrentResult({
        is_spam: false,
        confidence: 0,
        label: 'Error',
        error: errorMessage
      });
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleBatchDetect = async (texts: string[]): Promise<DetectionResult[]> => {
    setIsLoading(true);
    try {
      const response = await api.detectBatch(texts);
      await Promise.all([loadHistory(), loadStats()]);
      return response.results;
    } catch (error) {
      toast.error('Batch detection failed');
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearHistory = async () => {
    try {
      await api.clearHistory();
      setHistory([]);
      setStats({
        total_checks: 0,
        spam_count: 0,
        ham_count: 0,
        spam_rate: 0
      });
      toast.success('History cleared successfully');
    } catch (error) {
      toast.error('Failed to clear history');
    }
  };

  return (
    <div className="App">
      <Toaster position="top-right" />
      
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <div className="header-title">
            <h1>Spam Detection System</h1>
            <p>Advanced ML-powered message classification</p>
          </div>
          <div className="header-status">
            <span className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
              <FiActivity size={16} />
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
      </header>

      {/* Stats Dashboard */}
      {stats && (
        <div className="stats-dashboard">
          <StatsCard
            title="Total Checks"
            value={stats.total_checks}
            icon={<FiBarChart2 size={24} />}
            color="primary"
          />
          <StatsCard
            title="Spam Detected"
            value={stats.spam_count}
            icon={<FiAlertTriangle size={24} />}
            color="danger"
          />
          <StatsCard
            title="Legitimate"
            value={stats.ham_count}
            icon={<FiCheckCircle size={24} />}
            color="success"
          />
          <StatsCard
            title="Spam Rate"
            value={`${stats.spam_rate}%`}
            icon={<FiActivity size={24} />}
            color="warning"
          />
        </div>
      )}

      {/* Tab Navigation */}
      <div className="tab-navigation">
        <button
          className={`tab-button ${activeTab === 'single' ? 'active' : ''}`}
          onClick={() => setActiveTab('single')}
        >
          Single Detection
        </button>
        <button
          className={`tab-button ${activeTab === 'batch' ? 'active' : ''}`}
          onClick={() => setActiveTab('batch')}
        >
          Batch Processing
        </button>
        <button
          className={`tab-button ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          History
        </button>
      </div>

      {/* Main Content */}
      <main className="main-content">
        {activeTab === 'single' && (
          <div className="single-detection">
            <div className="detection-input">
              <MessageInput onDetect={handleDetect} isLoading={isLoading} />
            </div>
            <div className="detection-result">
              <ResultDisplay result={currentResult} isLoading={isLoading} />
            </div>
          </div>
        )}

        {activeTab === 'batch' && (
          <BatchDetection onBatchDetect={handleBatchDetect} isLoading={isLoading} />
        )}

        {activeTab === 'history' && (
          <HistoryList history={history} onClear={handleClearHistory} />
        )}
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <p>© 2024 Spam Detection System • Powered by Advanced ML</p>
      </footer>
    </div>
  );
}

export default App;