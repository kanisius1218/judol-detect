"""
Flask Web Application for Spam Moderator Dashboard
Modern, professional web interface
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import DatabaseManager
from ml_models.ml_detector import MLSpamDetector

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
CORS(app)

# Initialize components
db = DatabaseManager()
ml_detector = MLSpamDetector()


# ============================================================================
# ROUTES - Pages
# ============================================================================

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')


@app.route('/analytics')
def analytics():
    """Analytics page."""
    return render_template('analytics.html')


@app.route('/live-monitor')
def live_monitor():
    """Live monitoring page."""
    return render_template('live_monitor.html')


@app.route('/settings')
def settings():
    """Settings page."""
    return render_template('settings.html')


@app.route('/test')
def test():
    """Test detector page."""
    return render_template('test.html')


# ============================================================================
# API ROUTES - Dashboard Data
# ============================================================================

@app.route('/api/dashboard/stats')
def api_dashboard_stats():
    """Get dashboard statistics."""
    try:
        # Get stats for different time periods
        stats_today = db.get_platform_stats(days=1)
        stats_week = db.get_platform_stats(days=7)
        stats_month = db.get_platform_stats(days=30)
        
        # Calculate totals
        total_today = sum(platform['spam_detected'] for platform in stats_today.values())
        total_week = sum(platform['spam_detected'] for platform in stats_week.values())
        total_month = sum(platform['spam_detected'] for platform in stats_month.values())
        
        return jsonify({
            'success': True,
            'data': {
                'today': {
                    'total_spam': total_today,
                    'platforms': stats_today
                },
                'week': {
                    'total_spam': total_week,
                    'platforms': stats_week
                },
                'month': {
                    'total_spam': total_month,
                    'platforms': stats_month
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/dashboard/recent')
def api_dashboard_recent():
    """Get recent spam detections."""
    try:
        limit = request.args.get('limit', 20, type=int)
        
        # Get recent spam from database
        recent_spam = db.get_recent_spam(limit=limit)
        
        return jsonify({
            'success': True,
            'data': recent_spam
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/dashboard/chart-data')
def api_chart_data():
    """Get data for charts."""
    try:
        days = request.args.get('days', 7, type=int)
        
        # Get daily spam counts
        daily_data = db.get_daily_spam_count(days=days)
        
        # Get platform distribution
        platform_data = db.get_platform_stats(days=days)
        
        # Get hourly patterns
        hourly_data = db.get_hourly_patterns(days=days)
        
        return jsonify({
            'success': True,
            'data': {
                'daily': daily_data,
                'platforms': platform_data,
                'hourly': hourly_data
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# API ROUTES - ML Detector
# ============================================================================

@app.route('/api/detect', methods=['POST'])
def api_detect():
    """Detect if text is spam using ML model."""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({
                'success': False,
                'error': 'No text provided'
            }), 400
        
        # Predict using ML model
        result = ml_detector.predict(text)
        
        return jsonify({
            'success': True,
            'data': {
                'text': result.text,
                'is_spam': result.is_spam,
                'confidence': result.confidence,
                'spam_probability': result.spam_probability,
                'ham_probability': result.ham_probability,
                'model_name': result.model_name
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/detect/batch', methods=['POST'])
def api_detect_batch():
    """Detect multiple texts."""
    try:
        data = request.get_json()
        texts = data.get('texts', [])
        
        if not texts:
            return jsonify({
                'success': False,
                'error': 'No texts provided'
            }), 400
        
        # Predict batch
        results = ml_detector.predict_batch(texts)
        
        return jsonify({
            'success': True,
            'data': [
                {
                    'text': r.text,
                    'is_spam': r.is_spam,
                    'confidence': r.confidence,
                    'spam_probability': r.spam_probability,
                    'ham_probability': r.ham_probability,
                    'model_name': r.model_name
                }
                for r in results
            ]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/model/info')
def api_model_info():
    """Get ML model information."""
    try:
        info = ml_detector.get_model_info()
        
        # Add feature importance if available
        importance = ml_detector.get_feature_importance(top_n=20)
        if importance:
            info['top_features'] = importance
        
        return jsonify({
            'success': True,
            'data': info
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# API ROUTES - Analytics
# ============================================================================

@app.route('/api/analytics/trends')
def api_analytics_trends():
    """Get spam trends over time."""
    try:
        days = request.args.get('days', 30, type=int)
        
        # Get daily trends
        trends = db.get_spam_trends(days=days)
        
        return jsonify({
            'success': True,
            'data': trends
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analytics/top-spammers')
def api_top_spammers():
    """Get top spammers."""
    try:
        limit = request.args.get('limit', 10, type=int)
        days = request.args.get('days', 7, type=int)
        
        spammers = db.get_top_spammers(limit=limit, days=days)
        
        return jsonify({
            'success': True,
            'data': spammers
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analytics/keywords')
def api_analytics_keywords():
    """Get keyword frequency."""
    try:
        limit = request.args.get('limit', 20, type=int)
        days = request.args.get('days', 7, type=int)
        
        keywords = db.get_keyword_frequency(limit=limit, days=days)
        
        return jsonify({
            'success': True,
            'data': keywords
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# API ROUTES - System
# ============================================================================

@app.route('/api/system/status')
def api_system_status():
    """Get system status."""
    try:
        return jsonify({
            'success': True,
            'data': {
                'status': 'running',
                'timestamp': datetime.now().isoformat(),
                'ml_model_loaded': ml_detector.model is not None,
                'database_connected': True,
                'version': '3.0.0'
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/system/health')
def api_system_health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """404 error handler."""
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': 'Endpoint not found'
        }), 404
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """500 error handler."""
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500
    return render_template('500.html'), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    # Development server
    print("=" * 70)
    print("SPAM MODERATOR WEB DASHBOARD")
    print("=" * 70)
    print("Starting development server...")
    print("Dashboard: http://localhost:5000")
    print("=" * 70)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
