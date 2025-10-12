"""
Comprehensive tests for Advanced Spam Detection API
"""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import the app
import sys
sys.path.append(str(Path(__file__).parent.parent))
from advanced_api import app, model_manager, analytics


@pytest.fixture
def client():
    """Create test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_model():
    """Create mock model."""
    model = Mock()
    model.predict.return_value = [1]  # Spam
    model.predict_proba.return_value = [[0.2, 0.8]]
    return model


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check_success(self, client):
        """Test successful health check."""
        response = client.get('/api/health')
        assert response.status_code in [200, 503]
        data = json.loads(response.data)
        assert 'status' in data
        assert 'timestamp' in data
        assert 'system' in data
    
    def test_health_check_includes_system_metrics(self, client):
        """Test health check includes system metrics."""
        response = client.get('/api/health')
        data = json.loads(response.data)
        
        if 'system' in data:
            assert 'cpu_percent' in data['system']
            assert 'memory_percent' in data['system']
            assert 'memory_available_mb' in data['system']


class TestPredictionEndpoint:
    """Test prediction endpoint."""
    
    def test_predict_valid_input(self, client):
        """Test prediction with valid input."""
        # Mock the model manager
        with patch.object(model_manager, 'predict') as mock_predict:
            mock_predict.return_value = {
                'prediction': 'spam',
                'confidence': 0.85,
                'model_version': 'test',
                'latency_ms': 10.5
            }
            
            response = client.post('/api/predict',
                                  json={'text': 'Win free money now!'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['prediction'] == 'spam'
            assert 'confidence' in data
            assert 'timestamp' in data
    
    def test_predict_empty_text(self, client):
        """Test prediction with empty text."""
        response = client.post('/api/predict',
                              json={'text': ''})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_predict_missing_text(self, client):
        """Test prediction with missing text field."""
        response = client.post('/api/predict',
                              json={'message': 'test'})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_predict_invalid_json(self, client):
        """Test prediction with invalid JSON."""
        response = client.post('/api/predict',
                              data='invalid json',
                              content_type='application/json')
        
        assert response.status_code == 400
    
    @patch('advanced_api.cache')
    def test_predict_with_caching(self, mock_cache, client):
        """Test prediction caching."""
        # First request - cache miss
        mock_cache.get.return_value = None
        
        with patch.object(model_manager, 'predict') as mock_predict:
            mock_predict.return_value = {
                'prediction': 'ham',
                'confidence': 0.95,
                'model_version': 'test',
                'latency_ms': 5.0
            }
            
            response = client.post('/api/predict',
                                  json={'text': 'Hello world'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['cached'] == False
            mock_cache.set.assert_called_once()
        
        # Second request - cache hit
        mock_cache.get.return_value = {
            'prediction': 'ham',
            'confidence': 0.95,
            'cached': True
        }
        
        response = client.post('/api/predict',
                              json={'text': 'Hello world'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['cached'] == True


class TestBatchEndpoint:
    """Test batch prediction endpoint."""
    
    def test_batch_predict_valid(self, client):
        """Test batch prediction with valid input."""
        with patch.object(model_manager, 'predict') as mock_predict:
            mock_predict.side_effect = [
                {'prediction': 'spam', 'confidence': 0.9},
                {'prediction': 'ham', 'confidence': 0.8}
            ]
            
            response = client.post('/api/batch',
                                  json={'texts': ['Spam text', 'Ham text']})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'results' in data
            assert len(data['results']) == 2
            assert data['total'] == 2
    
    def test_batch_predict_empty_array(self, client):
        """Test batch prediction with empty array."""
        response = client.post('/api/batch',
                              json={'texts': []})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_batch_predict_too_many_texts(self, client):
        """Test batch prediction with too many texts."""
        texts = ['text'] * 101  # Exceeds limit of 100
        response = client.post('/api/batch',
                              json={'texts': texts})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Maximum' in data['error']


class TestAnalyticsEndpoint:
    """Test analytics endpoint."""
    
    def test_get_analytics(self, client):
        """Test getting analytics."""
        response = client.get('/api/analytics')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'request_analytics' in data
        assert 'model_performance' in data
        assert 'timestamp' in data


class TestFeedbackEndpoint:
    """Test feedback endpoint."""
    
    def test_submit_feedback_valid(self, client):
        """Test submitting valid feedback."""
        feedback = {
            'text': 'Test message',
            'predicted_label': 'spam',
            'correct_label': 'ham',
            'comment': 'False positive'
        }
        
        response = client.post('/api/feedback', json=feedback)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
    
    def test_submit_feedback_missing_fields(self, client):
        """Test submitting feedback with missing fields."""
        feedback = {
            'text': 'Test message',
            'predicted_label': 'spam'
            # Missing correct_label
        }
        
        response = client.post('/api/feedback', json=feedback)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data


class TestModelEndpoints:
    """Test model management endpoints."""
    
    def test_list_models(self, client):
        """Test listing available models."""
        response = client.get('/api/models')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'available_models' in data
        assert 'current_model' in data
        assert 'model_stats' in data
    
    def test_reload_models_unauthorized(self, client):
        """Test reloading models without authorization."""
        response = client.post('/api/reload-models')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Unauthorized' in data['error']
    
    def test_reload_models_authorized(self, client):
        """Test reloading models with authorization."""
        with patch.object(model_manager, '_load_models') as mock_load:
            response = client.post('/api/reload-models',
                                 headers={'Authorization': 'Bearer admin-token'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'success'
            mock_load.assert_called_once()


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_rate_limit_exceeded(self, client):
        """Test rate limit enforcement."""
        # Make many requests quickly
        for _ in range(11):  # Exceeds 10 per minute limit
            response = client.post('/api/predict',
                                  json={'text': 'test'})
        
        # Last request should be rate limited
        assert response.status_code == 429
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Rate limit' in data['error']


class TestModelManager:
    """Test ModelManager class."""
    
    def test_model_manager_initialization(self):
        """Test ModelManager initialization."""
        manager = model_manager
        assert manager is not None
        assert hasattr(manager, 'models')
        assert hasattr(manager, 'vectorizers')
        assert hasattr(manager, 'performance_stats')
    
    def test_model_manager_predict(self):
        """Test ModelManager prediction."""
        manager = model_manager
        
        # Mock model and vectorizer
        mock_model = Mock()
        mock_model.predict.return_value = [0]  # Ham
        mock_model.predict_proba.return_value = [[0.9, 0.1]]
        
        mock_vectorizer = Mock()
        mock_vectorizer.transform.return_value = [[0, 1, 0]]
        
        manager.models['test'] = mock_model
        manager.vectorizers['test'] = mock_vectorizer
        manager.current_version = 'test'
        
        result = manager.predict('Test message', 'test')
        
        assert result['prediction'] == 'ham'
        assert result['confidence'] == 0.1
        assert result['model_version'] == 'test'
        assert 'latency_ms' in result


class TestRequestAnalytics:
    """Test RequestAnalytics class."""
    
    def test_analytics_initialization(self):
        """Test RequestAnalytics initialization."""
        analytics_obj = analytics
        assert analytics_obj is not None
        assert hasattr(analytics_obj, 'request_history')
        assert hasattr(analytics_obj, 'hourly_stats')
        assert hasattr(analytics_obj, 'user_stats')
    
    def test_log_request(self):
        """Test logging requests."""
        analytics_obj = analytics
        
        analytics_obj.log_request(
            ip='127.0.0.1',
            text='Test message',
            result='spam',
            latency=0.05
        )
        
        # Check that request was logged
        assert len(analytics_obj.request_history) > 0
        last_request = analytics_obj.request_history[-1]
        assert last_request['ip'] == '127.0.0.1'
        assert last_request['result'] == 'spam'
    
    def test_get_analytics_summary(self):
        """Test getting analytics summary."""
        analytics_obj = analytics
        
        summary = analytics_obj.get_analytics()
        
        assert 'total_requests' in summary
        assert 'spam_rate' in summary
        assert 'avg_latency_ms' in summary
        assert 'unique_users' in summary
        assert 'recent_requests' in summary
        assert 'hourly_stats' in summary


class TestErrorHandling:
    """Test error handling."""
    
    def test_internal_server_error(self, client):
        """Test internal server error handling."""
        with patch.object(model_manager, 'predict') as mock_predict:
            mock_predict.side_effect = Exception('Model error')
            
            response = client.post('/api/predict',
                                  json={'text': 'Test'})
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
