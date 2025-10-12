"""
Flask Web Application for Message Detection System
Simple black and white design
"""

import os
import json
import joblib
import logging
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-2024')

# Enable CORS
CORS(app)

class MessageDetector:
    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.load_model()
    
    def load_model(self):
        """Load the spam detection model"""
        try:
            base_dir = Path(__file__).parent
            model_dir = base_dir / "ml_models"
            
            # Try to load ensemble model first
            ensemble_path = model_dir / "advanced_spam_detector_ensemble_latest.joblib"
            vectorizer_path = model_dir / "advanced_spam_detector_vectorizers_latest.joblib"
            
            if ensemble_path.exists() and vectorizer_path.exists():
                self.model = joblib.load(ensemble_path)
                self.vectorizer = joblib.load(vectorizer_path)
                logger.info("Ensemble model loaded successfully")
            else:
                # Fallback to basic model
                basic_model_path = model_dir / "spam_detector_latest.joblib"
                basic_vectorizer_path = model_dir / "spam_detector_vectorizer_latest.joblib"
                
                if basic_model_path.exists() and basic_vectorizer_path.exists():
                    self.model = joblib.load(basic_model_path)
                    self.vectorizer = joblib.load(basic_vectorizer_path)
                    logger.info("Basic model loaded successfully")
                else:
                    logger.warning("No models found - using mock predictions")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
    
    def predict(self, text):
        """Make prediction on text"""
        try:
            if self.model is None or self.vectorizer is None:
                # Mock prediction if no model
                import random
                is_spam = random.random() > 0.7
                return {
                    'is_spam': is_spam,
                    'confidence': random.uniform(0.6, 0.95),
                    'label': 'Spam' if is_spam else 'Ham'
                }
            
            # Transform text
            if isinstance(self.vectorizer, dict) and 'feature_union' in self.vectorizer:
                features = self.vectorizer['feature_union'].transform([text])
            else:
                features = self.vectorizer.transform([text])
            
            # Make prediction
            prediction = self.model.predict(features)[0]
            probability = self.model.predict_proba(features)[0] if hasattr(self.model, 'predict_proba') else [0.5, 0.5]
            
            return {
                'is_spam': bool(prediction == 1),
                'confidence': float(probability[1]),
                'label': 'Spam' if prediction == 1 else 'Ham'
            }
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return {
                'is_spam': False,
                'confidence': 0.0,
                'label': 'Error',
                'error': str(e)
            }

# Initialize detector
detector = MessageDetector()

# Store history in session
def get_history():
    if 'history' not in session:
        session['history'] = []
    return session['history']

def add_to_history(text, result):
    history = get_history()
    history.append({
        'timestamp': datetime.now().isoformat(),
        'text': text[:100] + '...' if len(text) > 100 else text,
        'result': result['label'],
        'confidence': result['confidence']
    })
    # Keep only last 10 items
    session['history'] = history[-10:]

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/detect', methods=['POST'])
def detect_message():
    """API endpoint for message detection"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'No text provided'}), 400
        
        text = data['text']
        if not text.strip():
            return jsonify({'error': 'Empty text'}), 400
        
        # Make prediction
        result = detector.predict(text)
        
        # Add to history
        add_to_history(text, result)
        
        # Add timestamp
        result['timestamp'] = datetime.now().isoformat()
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Detection error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/batch', methods=['POST'])
def batch_detect():
    """Batch detection endpoint"""
    try:
        data = request.get_json()
        if not data or 'texts' not in data:
            return jsonify({'error': 'No texts provided'}), 400
        
        texts = data['texts']
        if not isinstance(texts, list):
            return jsonify({'error': 'Texts must be a list'}), 400
        
        results = []
        for text in texts[:50]:  # Limit to 50 texts
            if text and text.strip():
                result = detector.predict(text)
                result['text'] = text[:50] + '...' if len(text) > 50 else text
                results.append(result)
        
        return jsonify({
            'results': results,
            'total': len(results),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Batch detection error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_detection_history():
    """Get detection history"""
    try:
        history = get_history()
        return jsonify({
            'history': history,
            'total': len(history)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear-history', methods=['POST'])
def clear_history():
    """Clear detection history"""
    try:
        session['history'] = []
        return jsonify({'status': 'success', 'message': 'History cleared'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get statistics"""
    try:
        history = get_history()
        if not history:
            return jsonify({
                'total_checks': 0,
                'spam_count': 0,
                'ham_count': 0,
                'spam_rate': 0
            })
        
        spam_count = sum(1 for h in history if h['result'] == 'Spam')
        ham_count = sum(1 for h in history if h['result'] == 'Ham')
        
        return jsonify({
            'total_checks': len(history),
            'spam_count': spam_count,
            'ham_count': ham_count,
            'spam_rate': round(spam_count / len(history) * 100, 1) if history else 0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
