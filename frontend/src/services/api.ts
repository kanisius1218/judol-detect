import axios, { AxiosInstance } from 'axios';
import {
  DetectionResult,
  BatchDetectionResponse,
  HistoryResponse,
  StatsResponse
} from '../types';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5000',
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 10000,
    });

    // Request interceptor
    this.api.interceptors.request.use(
      (config) => {
        // Add any auth headers if needed
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response) {
          // Server responded with error
          throw new Error(error.response.data.error || 'Server error occurred');
        } else if (error.request) {
          // Request made but no response
          throw new Error('No response from server. Please check your connection.');
        } else {
          // Request setup error
          throw new Error('Request failed. Please try again.');
        }
      }
    );
  }

  // Single message detection
  async detectMessage(text: string): Promise<DetectionResult> {
    const response = await this.api.post<DetectionResult>('/api/detect', { text });
    return response.data;
  }

  // Batch message detection
  async detectBatch(texts: string[]): Promise<BatchDetectionResponse> {
    const response = await this.api.post<BatchDetectionResponse>('/api/batch', { texts });
    return response.data;
  }

  // Get detection history
  async getHistory(): Promise<HistoryResponse> {
    const response = await this.api.get<HistoryResponse>('/api/history');
    return response.data;
  }

  // Clear history
  async clearHistory(): Promise<{ status: string; message: string }> {
    const response = await this.api.post('/api/clear-history');
    return response.data;
  }

  // Get statistics
  async getStats(): Promise<StatsResponse> {
    const response = await this.api.get<StatsResponse>('/api/stats');
    return response.data;
  }

  // Health check
  async healthCheck(): Promise<boolean> {
    try {
      await this.api.get('/');
      return true;
    } catch {
      return false;
    }
  }
}

export default new ApiService();
