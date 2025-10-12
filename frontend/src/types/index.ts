// API Response Types
export interface DetectionResult {
  is_spam: boolean;
  confidence: number;
  label: 'Spam' | 'Ham' | 'Error';
  timestamp?: string;
  error?: string;
  text?: string;
}

export interface BatchDetectionResponse {
  results: DetectionResult[];
  total: number;
  timestamp: string;
}

export interface HistoryItem {
  timestamp: string;
  text: string;
  result: string;
  confidence: number;
}

export interface HistoryResponse {
  history: HistoryItem[];
  total: number;
}

export interface StatsResponse {
  total_checks: number;
  spam_count: number;
  ham_count: number;
  spam_rate: number;
}

// Component Props Types
export interface MessageInputProps {
  onDetect: (text: string) => void;
  isLoading: boolean;
}

export interface ResultDisplayProps {
  result: DetectionResult | null;
  isLoading: boolean;
}

export interface StatsCardProps {
  title: string;
  value: number | string;
  icon?: React.ReactNode;
  color?: 'primary' | 'success' | 'danger' | 'warning';
}

export interface HistoryListProps {
  history: HistoryItem[];
  onClear: () => void;
}

// Application State Types
export interface AppState {
  currentResult: DetectionResult | null;
  history: HistoryItem[];
  stats: StatsResponse | null;
  isLoading: boolean;
  error: string | null;
  batchMode: boolean;
  batchTexts: string[];
  batchResults: DetectionResult[];
}

// Form Types
export interface MessageFormData {
  text: string;
  characterCount: number;
}

export interface BatchFormData {
  texts: string[];
}
