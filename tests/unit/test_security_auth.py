"""Unit tests for authentication module."""

import pytest
from unittest.mock import Mock, patch
import redis

from src.security.auth import APIKeyManager, require_api_key
from src.exceptions import AuthenticationError, AuthorizationError


class TestAPIKeyManager:
    """Tests for APIKeyManager class."""
    
    def test_create_api_key(self, redis_client):
        """Test API key creation."""
        manager = APIKeyManager(redis_client)
        
        api_key = manager.create_api_key(
            user_id='test_user',
            name='Test Key',
            rate_limit=1000
        )
        
        # Verify key format
        assert api_key.startswith('sk_')
        assert len(api_key) > 40
        
        # Verify metadata stored
        metadata = manager.verify_api_key(api_key)
        assert metadata is not None
        assert metadata['user_id'] == 'test_user'
        assert metadata['name'] == 'Test Key'
        assert int(metadata['rate_limit']) == 1000
    
    def test_verify_valid_api_key(self, redis_client):
        """Test verifying valid API key."""
        manager = APIKeyManager(redis_client)
        api_key = manager.create_api_key('test_user', 'Test')
        
        metadata = manager.verify_api_key(api_key)
        
        assert metadata is not None
        assert metadata['user_id'] == 'test_user'
        assert int(metadata['total_requests']) == 1  # Incremented on verify
    
    def test_verify_invalid_api_key(self, redis_client):
        """Test verifying invalid API key."""
        manager = APIKeyManager(redis_client)
        
        metadata = manager.verify_api_key('invalid_key')
        
        assert metadata is None
    
    def test_verify_malformed_api_key(self, redis_client):
        """Test verifying malformed API key."""
        manager = APIKeyManager(redis_client)
        
        metadata = manager.verify_api_key('sk_invalid')
        
        assert metadata is None
    
    def test_check_rate_limit_first_request(self, redis_client):
        """Test rate limit check for first request."""
        manager = APIKeyManager(redis_client)
        api_key = manager.create_api_key('test_user', 'Test', rate_limit=10)
        
        is_allowed = manager.check_rate_limit(api_key)
        
        assert is_allowed is True
    
    def test_check_rate_limit_within_limit(self, redis_client):
        """Test rate limit check within limit."""
        manager = APIKeyManager(redis_client)
        api_key = manager.create_api_key('test_user', 'Test', rate_limit=10)
        
        # Make 5 requests
        for _ in range(5):
            manager.check_rate_limit(api_key)
        
        is_allowed = manager.check_rate_limit(api_key)
        assert is_allowed is True
    
    def test_check_rate_limit_exceeded(self, redis_client):
        """Test rate limit exceeded."""
        manager = APIKeyManager(redis_client)
        api_key = manager.create_api_key('test_user', 'Test', rate_limit=5)
        
        # Exhaust rate limit
        for _ in range(5):
            manager.check_rate_limit(api_key)
        
        # Next request should fail
        is_allowed = manager.check_rate_limit(api_key)
        assert is_allowed is False
    
    def test_revoke_api_key(self, redis_client):
        """Test API key revocation."""
        manager = APIKeyManager(redis_client)
        api_key = manager.create_api_key('test_user', 'Test')
        
        # Revoke key
        revoked = manager.revoke_api_key(api_key)
        assert revoked is True
        
        # Verify key is invalid
        metadata = manager.verify_api_key(api_key)
        assert metadata is None
    
    def test_revoke_nonexistent_key(self, redis_client):
        """Test revoking non-existent key."""
        manager = APIKeyManager(redis_client)
        
        revoked = manager.revoke_api_key('sk_nonexistent')
        assert revoked is False


class TestRequireAPIKeyDecorator:
    """Tests for require_api_key decorator."""
    
    def test_missing_api_key(self, client):
        """Test request without API key."""
        from flask import Flask, jsonify
        from src.security.auth import require_api_key
        
        app = Flask(__name__)
        
        @app.route('/test')
        @require_api_key
        def test_endpoint():
            return jsonify({'message': 'success'})
        
        with app.test_client() as client:
            response = client.get('/test')
            
            assert response.status_code == 401
            data = response.get_json()
            assert 'error' in data
    
    def test_valid_api_key(self, client, api_key, redis_client):
        """Test request with valid API key."""
        from flask import Flask, jsonify, request
        from src.security.auth import require_api_key
        
        app = Flask(__name__)
        app.extensions['redis'] = redis_client
        
        @app.route('/test')
        @require_api_key
        def test_endpoint():
            return jsonify({
                'message': 'success',
                'user_id': request.user_id
            })
        
        with app.test_client() as test_client:
            response = test_client.get(
                '/test',
                headers={'X-API-Key': api_key}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['message'] == 'success'
            assert data['user_id'] == 'test_user'
    
    def test_invalid_api_key(self, client, redis_client):
        """Test request with invalid API key."""
        from flask import Flask, jsonify
        from src.security.auth import require_api_key
        
        app = Flask(__name__)
        app.extensions['redis'] = redis_client
        
        @app.route('/test')
        @require_api_key
        def test_endpoint():
            return jsonify({'message': 'success'})
        
        with app.test_client() as test_client:
            response = test_client.get(
                '/test',
                headers={'X-API-Key': 'sk_invalid'}
            )
            
            assert response.status_code == 401


@pytest.mark.integration
class TestAPIKeyIntegration:
    """Integration tests for API key system."""
    
    def test_api_key_lifecycle(self, redis_client):
        """Test complete API key lifecycle."""
        manager = APIKeyManager(redis_client)
        
        # Create key
        api_key = manager.create_api_key('user123', 'Production Key', 100)
        assert api_key.startswith('sk_')
        
        # Verify key works
        metadata = manager.verify_api_key(api_key)
        assert metadata['user_id'] == 'user123'
        
        # Check rate limit
        assert manager.check_rate_limit(api_key) is True
        
        # Use key multiple times
        for _ in range(10):
            manager.verify_api_key(api_key)
        
        # Check total requests incremented
        metadata = manager.verify_api_key(api_key)
        assert int(metadata['total_requests']) >= 11
        
        # Revoke key
        assert manager.revoke_api_key(api_key) is True
        
        # Verify key no longer works
        assert manager.verify_api_key(api_key) is None
