"""
Enhanced API for Spam Detection - Simplified Version
Works without Redis and complex dependencies
"""

import os
import json
import joblib
import logging
import hashlib
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from functools import wraps
from collections import defaultdict, deque
import numpy as np

from flask import Flask, request, jsonify, Response
from flask_cors import CORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'

# Enable CORS
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://localhost:5173", "*"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Simple in-memory cache
class SimpleCache:
    def __init__(self, max_size=1000):
        self.cache = {}
        self.max_size = max_size
        
    def get(self, key):
        return self.cache.get(key)
    
    def set(self, key, value, timeout=300):
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest = next(iter(self.cache))
            del self.cache[oldest]
        self.cache[key] = value
    
    def clear(self):
        self.cache.clear()

cache = SimpleCache()

# Simple rate limiter
class SimpleRateLimiter:
    def __init__(self):
        self.requests = defaultdict(lambda: deque(maxlen=100))
    
    def is_allowed(self, ip, max_requests=10, window=60):
        now = time.time()
        request_times = self.requests[ip]
        
        # Remove old requests
        while request_times and request_times[0] < now - window:
            request_times.popleft()
        
        if len(request_times) >= max_requests:
            return False
        
        request_times.append(now)
        return True

rate_limiter = SimpleRateLimiter()


class ModelManager:
    """
    Manages ML models with versioning.
    """
    
    def __init__(self):
        self.models = {}
        self.vectorizers = {}
        self.current_version = None
        self.performance_stats = defaultdict(lambda: {
            'predictions': 0,
            'avg_latency': 0.0,
            'latencies': deque(maxlen=100)
        })
        
        self._load_models()
    
    def _load_models(self):
        """Load all available models."""
        try:
            base_dir = Path(__file__).parent
            model_dir = base_dir / "ml_models"
            
            # Try to load ensemble model first
            ensemble_path = model_dir / "advanced_spam_detector_ensemble_latest.joblib"
            vectorizer_path = model_dir / "advanced_spam_detector_vectorizers_latest.joblib"
            
            if ensemble_path.exists() and vectorizer_path.exists():
                self.models['ensemble'] = joblib.load(ensemble_path)
                self.vectorizers['ensemble'] = joblib.load(vectorizer_path)
                self.current_version = 'ensemble'
                logger.info("Ensemble model loaded successfully")
            
            # Also load basic model as fallback
            basic_model_path = model_dir / "spam_detector_latest.joblib"
            basic_vectorizer_path = model_dir / "spam_detector_vectorizer_latest.joblib"
            
            if basic_model_path.exists() and basic_vectorizer_path.exists():
                self.models['basic'] = joblib.load(basic_model_path)
                self.vectorizers['basic'] = joblib.load(basic_vectorizer_path)
                if not self.current_version:
                    self.current_version = 'basic'
                logger.info("Basic model loaded successfully")
                
        except Exception as e:
            logger.error(f"Error loading models: {e}")
    
    def predict(self, text: str, model_version: Optional[str] = None) -> Dict[str, Any]:
        """Make prediction with specified model version."""
        start_time = time.time()
        
        version = model_version or self.current_version
        if not version or version not in self.models:
            raise ValueError(f"Model version {version} not available")
        
        model = self.models[version]
        vectorizer = self.vectorizers[version]
        
        # Transform text
        if version == 'ensemble':
            # Use feature union for ensemble
            features = vectorizer['feature_union'].transform([text])
        else:
            # Use basic vectorizer
            features = vectorizer.transform([text])
        
        # Make prediction
        prediction = model.predict(features)[0]
        probability = model.predict_proba(features)[0] if hasattr(model, 'predict_proba') else None
        
        # Calculate latency
        latency = time.time() - start_time
        
        # Update stats
        self.performance_stats[version]['predictions'] += 1
        self.performance_stats[version]['latencies'].append(latency)
        self.performance_stats[version]['avg_latency'] = np.mean(
            self.performance_stats[version]['latencies']
        )
        
        result = {
            'prediction': 'spam' if prediction == 1 else 'ham',
            'confidence': float(probability[1]) if probability is not None else None,
            'model_version': version,
            'latency_ms': round(latency * 1000, 2)
        }
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Get model performance statistics."""
        return dict(self.performance_stats)


class RequestAnalytics:
    """
    Analytics and monitoring for API requests.
    """
    
    def __init__(self):
        self.request_history = deque(maxlen=10000)
        self.hourly_stats = defaultdict(lambda: {'total': 0, 'spam': 0, 'ham': 0})
        self.user_stats = defaultdict(lambda: {'requests': 0, 'last_seen': None})
    
    def log_request(self, ip: str, text: str, result: str, latency: float):
        """Log request for analytics."""
        timestamp = datetime.now()
        
        # Add to history
        self.request_history.append({
            'timestamp': timestamp.isoformat(),
            'ip': ip,
            'text_length': len(text),
            'result': result,
            'latency': latency
        })
        
        # Update hourly stats
        hour_key = timestamp.strftime('%Y-%m-%d %H:00')
        self.hourly_stats[hour_key]['total'] += 1
        self.hourly_stats[hour_key][result] += 1
        
        # Update user stats
        self.user_stats[ip]['requests'] += 1
        self.user_stats[ip]['last_seen'] = timestamp
    
    def get_analytics(self) -> Dict[str, Any]:
        """Get analytics summary."""
        recent_requests = list(self.request_history)[-100:]
        
        # Calculate metrics
        total_requests = len(self.request_history)
        if total_requests > 0:
            spam_rate = sum(1 for r in self.request_history if r['result'] == 'spam') / total_requests
            avg_latency = np.mean([r['latency'] for r in self.request_history])
            avg_text_length = np.mean([r['text_length'] for r in self.request_history])
        else:
            spam_rate = 0
            avg_latency = 0
            avg_text_length = 0
        
        return {
            'total_requests': total_requests,
            'spam_rate': round(spam_rate, 3),
            'avg_latency_ms': round(avg_latency * 1000, 2),
            'avg_text_length': round(avg_text_length, 1),
            'unique_users': len(self.user_stats),
            'recent_requests': recent_requests,
            'hourly_stats': dict(list(self.hourly_stats.items())[-24:])
        }


# Initialize managers
model_manager = ModelManager()
analytics = RequestAnalytics()


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        model_status = 'healthy' if model_manager.current_version else 'unhealthy'
        
        health_status = {
            'status': model_status,
            'timestamp': datetime.now().isoformat(),
            'model_version': model_manager.current_version,
            'available_models': list(model_manager.models.keys())
        }
        
        status_code = 200 if model_status == 'healthy' else 503
        return jsonify(health_status), status_code
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/predict', methods=['POST'])
def predict():
    """
    Enhanced prediction endpoint with caching.
    """
    try:
        # Simple rate limiting
        ip = request.remote_addr
        if not rate_limiter.is_allowed(ip, max_requests=10, window=60):
            return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429
        
        # Validate request
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'Invalid input: JSON with "text" field required'}), 400
        
        text = data['text']
        if not isinstance(text, str) or not text.strip():
            return jsonify({'error': 'Text must be a non-empty string'}), 400
        
        # Check cache
        cache_key = f"prediction_{hashlib.md5(text.encode()).hexdigest()}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            cached_result['cached'] = True
            return jsonify(cached_result)
        
        # Make prediction
        start_time = time.time()
        result = model_manager.predict(text, data.get('model_version'))
        latency = time.time() - start_time
        
        # Add metadata
        result['cached'] = False
        result['timestamp'] = datetime.now().isoformat()
        
        # Cache result
        cache.set(cache_key, result, timeout=300)
        
        # Log analytics
        analytics.log_request(
            ip=ip,
            text=text,
            result=result['prediction'],
            latency=latency
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return jsonify({'error': 'Prediction failed', 'message': str(e)}), 500


@app.route('/api/batch', methods=['POST'])
def batch_predict():
    """
    Batch prediction endpoint for multiple texts.
    """
    try:
        # Rate limiting
        ip = request.remote_addr
        if not rate_limiter.is_allowed(ip, max_requests=5, window=60):
            return jsonify({'error': 'Rate limit exceeded'}), 429
        
        data = request.get_json()
        if not data or 'texts' not in data:
            return jsonify({'error': 'Invalid input: JSON with "texts" array required'}), 400
        
        texts = data['texts']
        if not isinstance(texts, list) or len(texts) == 0:
            return jsonify({'error': 'Texts must be a non-empty array'}), 400
        
        if len(texts) > 100:
            return jsonify({'error': 'Maximum 100 texts per batch'}), 400
        
        # Process batch
        results = []
        for text in texts:
            if isinstance(text, str) and text.strip():
                try:
                    result = model_manager.predict(text)
                    results.append(result)
                except Exception as e:
                    results.append({'error': str(e)})
            else:
                results.append({'error': 'Invalid text'})
        
        return jsonify({
            'results': results,
            'total': len(results),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        return jsonify({'error': 'Batch prediction failed', 'message': str(e)}), 500


@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """
    Get analytics and statistics.
    """
    try:
        stats = analytics.get_analytics()
        model_stats = model_manager.get_stats()
        
        return jsonify({
            'request_analytics': stats,
            'model_performance': model_stats,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        return jsonify({'error': 'Failed to get analytics', 'message': str(e)}), 500


@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """
    Submit feedback for predictions to improve the model.
    """
    try:
        data = request.get_json()
        required_fields = ['text', 'predicted_label', 'correct_label']
        
        if not all(field in data for field in required_fields):
            return jsonify({'error': f'Required fields: {required_fields}'}), 400
        
        # Store feedback (in production, save to database)
        feedback_dir = Path('feedback')
        feedback_dir.mkdir(exist_ok=True)
        
        feedback_file = feedback_dir / f"feedback_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        with open(feedback_file, 'a') as f:
            feedback_entry = {
                'timestamp': datetime.now().isoformat(),
                'text': data['text'],
                'predicted_label': data['predicted_label'],
                'correct_label': data['correct_label'],
                'ip': request.remote_addr,
                'user_comment': data.get('comment', '')
            }
            f.write(json.dumps(feedback_entry) + '\n')
        
        return jsonify({
            'status': 'success',
            'message': 'Feedback received. Thank you for helping improve our model!'
        })
        
    except Exception as e:
        logger.error(f"Feedback error: {e}")
        return jsonify({'error': 'Failed to submit feedback', 'message': str(e)}), 500


@app.route('/api/models', methods=['GET'])
def list_models():
    """
    List available model versions.
    """
    try:
        models = list(model_manager.models.keys())
        current = model_manager.current_version
        
        return jsonify({
            'available_models': models,
            'current_model': current,
            'model_stats': model_manager.get_stats()
        })
        
    except Exception as e:
        logger.error(f"Model listing error: {e}")
        return jsonify({'error': 'Failed to list models', 'message': str(e)}), 500


@app.route('/api/clear-cache', methods=['POST'])
def clear_cache():
    """
    Clear the prediction cache.
    """
    try:
        cache.clear()
        return jsonify({'status': 'success', 'message': 'Cache cleared'})
    except Exception as e:
        logger.error(f"Cache clear error: {e}")
        return jsonify({'error': 'Failed to clear cache', 'message': str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500


if __name__ == '__main__':
    # Run the Flask app
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    print(f"""
    ╔══════════════════════════════════════════════════════╗
    ║     ENHANCED SPAM DETECTION API                      ║
    ║     Starting on http://localhost:{port}              ║
    ║     Health: http://localhost:{port}/api/health       ║
    ║     Models: {', '.join(model_manager.models.keys()) if model_manager.models else 'No models loaded'}
    ╚══════════════════════════════════════════════════════╝
    """)
    
    app.run(host='0.0.0.0', port=port, debug=debug)
