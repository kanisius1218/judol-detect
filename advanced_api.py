"""
Advanced API for Spam Detection with Professional Features
Includes caching, rate limiting, monitoring, and analytics
"""

import os
import json
import joblib
import logging
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from functools import wraps
from collections import defaultdict, deque
import threading

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
import redis
import numpy as np

# Monitoring and metrics
import psutil
import prometheus_client
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Enable CORS
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://localhost:5173"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Configure caching
cache_config = {
    'CACHE_TYPE': 'redis' if os.environ.get('REDIS_URL') else 'simple',
    'CACHE_REDIS_URL': os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    'CACHE_DEFAULT_TIMEOUT': 300,
    'CACHE_KEY_PREFIX': 'spam_detector_'
}
app.config.update(cache_config)
cache = Cache(app)

# Configure rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["1000 per hour", "100 per minute"],
    storage_uri=os.environ.get('REDIS_URL', 'memory://'),
)

# Prometheus metrics
prediction_counter = Counter('spam_predictions_total', 'Total number of predictions', ['result'])
prediction_duration = Histogram('spam_prediction_duration_seconds', 'Prediction duration')
model_accuracy_gauge = Gauge('spam_model_accuracy', 'Current model accuracy')
active_requests_gauge = Gauge('spam_active_requests', 'Number of active requests')
cache_hit_counter = Counter('spam_cache_hits_total', 'Total cache hits')
cache_miss_counter = Counter('spam_cache_misses_total', 'Total cache misses')
error_counter = Counter('spam_errors_total', 'Total errors', ['error_type'])


class ModelManager:
    """
    Manages ML models with hot-reloading and versioning.
    """
    
    def __init__(self):
        self.models = {}
        self.vectorizers = {}
        self.current_version = None
        self.load_lock = threading.Lock()
        self.performance_stats = defaultdict(lambda: {
            'predictions': 0,
            'correct': 0,
            'accuracy': 0.0,
            'avg_latency': 0.0,
            'latencies': deque(maxlen=100)
        })
        
        self._load_models()
    
    def _load_models(self):
        """Load all available models."""
        with self.load_lock:
            try:
                base_dir = Path(__file__).parent
                model_dir = base_dir / "ml_models"
                
                # Load ensemble model (primary)
                ensemble_path = model_dir / "advanced_spam_detector_ensemble_latest.joblib"
                vectorizer_path = model_dir / "advanced_spam_detector_vectorizers_latest.joblib"
                
                if ensemble_path.exists() and vectorizer_path.exists():
                    self.models['ensemble'] = joblib.load(ensemble_path)
                    self.vectorizers['ensemble'] = joblib.load(vectorizer_path)
                    self.current_version = 'ensemble'
                    logger.info("Ensemble model loaded successfully")
                else:
                    # Fallback to basic model
                    basic_model_path = model_dir / "spam_detector_latest.joblib"
                    basic_vectorizer_path = model_dir / "spam_detector_vectorizer_latest.joblib"
                    
                    if basic_model_path.exists() and basic_vectorizer_path.exists():
                        self.models['basic'] = joblib.load(basic_model_path)
                        self.vectorizers['basic'] = joblib.load(basic_vectorizer_path)
                        self.current_version = 'basic'
                        logger.info("Basic model loaded successfully")
                    else:
                        logger.error("No models found!")
                        
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
        self.lock = threading.Lock()
    
    def log_request(self, ip: str, text: str, result: str, latency: float):
        """Log request for analytics."""
        with self.lock:
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
        with self.lock:
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
                'avg_latency_ms': round(avg_latency, 2),
                'avg_text_length': round(avg_text_length, 1),
                'unique_users': len(self.user_stats),
                'recent_requests': recent_requests,
                'hourly_stats': dict(list(self.hourly_stats.items())[-24:])
            }


# Initialize managers
model_manager = ModelManager()
analytics = RequestAnalytics()


def measure_performance(f):
    """Decorator to measure endpoint performance."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        active_requests_gauge.inc()
        start_time = time.time()
        
        try:
            result = f(*args, **kwargs)
            duration = time.time() - start_time
            prediction_duration.observe(duration)
            return result
        finally:
            active_requests_gauge.dec()
    
    return decorated_function


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        # Check model availability
        model_status = 'healthy' if model_manager.current_version else 'unhealthy'
        
        # Check system resources
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        health_status = {
            'status': model_status,
            'timestamp': datetime.now().isoformat(),
            'model_version': model_manager.current_version,
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_mb': memory.available / (1024 * 1024)
            }
        }
        
        status_code = 200 if model_status == 'healthy' else 503
        return jsonify(health_status), status_code
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/predict', methods=['POST'])
@limiter.limit("10 per minute")
@measure_performance
def predict():
    """
    Enhanced prediction endpoint with caching and monitoring.
    """
    try:
        # Validate request
        data = request.get_json()
        if not data or 'text' not in data:
            error_counter.labels(error_type='invalid_input').inc()
            return jsonify({'error': 'Invalid input: JSON with "text" field required'}), 400
        
        text = data['text']
        if not isinstance(text, str) or not text.strip():
            error_counter.labels(error_type='empty_text').inc()
            return jsonify({'error': 'Text must be a non-empty string'}), 400
        
        # Check cache
        cache_key = f"prediction_{hashlib.md5(text.encode()).hexdigest()}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            cache_hit_counter.inc()
            cached_result['cached'] = True
            return jsonify(cached_result)
        
        cache_miss_counter.inc()
        
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
            ip=request.remote_addr,
            text=text,
            result=result['prediction'],
            latency=latency
        )
        
        # Update metrics
        prediction_counter.labels(result=result['prediction']).inc()
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        error_counter.labels(error_type='prediction_error').inc()
        return jsonify({'error': 'Prediction failed', 'message': str(e)}), 500


@app.route('/api/batch', methods=['POST'])
@limiter.limit("5 per minute")
@measure_performance
def batch_predict():
    """
    Batch prediction endpoint for multiple texts.
    """
    try:
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
@limiter.limit("10 per minute")
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
@limiter.limit("20 per minute")
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


@app.route('/api/reload-models', methods=['POST'])
@limiter.limit("1 per minute")
def reload_models():
    """
    Reload models from disk (admin endpoint).
    """
    try:
        # In production, add authentication here
        auth_header = request.headers.get('Authorization')
        if auth_header != f"Bearer {os.environ.get('ADMIN_TOKEN', 'admin-token')}":
            return jsonify({'error': 'Unauthorized'}), 401
        
        model_manager._load_models()
        
        return jsonify({
            'status': 'success',
            'message': 'Models reloaded',
            'current_model': model_manager.current_version
        })
        
    except Exception as e:
        logger.error(f"Model reload error: {e}")
        return jsonify({'error': 'Failed to reload models', 'message': str(e)}), 500


@app.route('/metrics')
def metrics():
    """
    Prometheus metrics endpoint.
    """
    return Response(generate_latest(), mimetype='text/plain')


@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded."""
    return jsonify({
        'error': 'Rate limit exceeded',
        'message': str(e.description)
    }), 429


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
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"""
    ╔══════════════════════════════════════════════════════╗
    ║     ADVANCED SPAM DETECTION API                      ║
    ║     Starting on http://localhost:{port}              ║
    ║     Metrics: http://localhost:{port}/metrics         ║
    ║     Health: http://localhost:{port}/api/health       ║
    ╚══════════════════════════════════════════════════════╝
    """)
    
    app.run(host='0.0.0.0', port=port, debug=debug)
