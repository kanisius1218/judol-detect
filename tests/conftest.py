"""Pytest configuration and shared fixtures."""

import pytest
import os
from typing import Generator
from unittest.mock import Mock, patch
import redis
import fakeredis

# Set test environment
os.environ['FLASK_ENV'] = 'testing'
os.environ['DATABASE_URL'] = 'postgresql://testuser:testpass@localhost:5432/testdb'
os.environ['REDIS_URL'] = 'redis://localhost:6379/1'


@pytest.fixture(scope='session')
def app():
    """Create Flask application for testing."""
    from app import create_app
    
    app = create_app('testing')
    app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'RATELIMIT_ENABLED': False,  # Disable rate limiting in tests
    })
    
    yield app


@pytest.fixture(scope='function')
def client(app):
    """Create Flask test client."""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """Create Flask CLI test runner."""
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def app_context(app):
    """Create Flask application context."""
    with app.app_context():
        yield


@pytest.fixture(scope='function')
def request_context(app):
    """Create Flask request context."""
    with app.test_request_context():
        yield


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope='function')
def db_session(app):
    """Create database session for testing."""
    from src.database import db, init_db
    
    with app.app_context():
        # Create tables
        init_db()
        
        yield db.session
        
        # Cleanup
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def clean_db(db_session):
    """Clean database before test."""
    # Clear all tables
    for table in reversed(db_session.metadata.sorted_tables):
        db_session.execute(table.delete())
    db_session.commit()
    
    yield db_session


# ============================================================================
# REDIS FIXTURES
# ============================================================================

@pytest.fixture(scope='function')
def redis_client():
    """Create fake Redis client for testing."""
    fake_redis = fakeredis.FakeRedis(decode_responses=True)
    
    yield fake_redis
    
    # Cleanup
    fake_redis.flushall()


@pytest.fixture(scope='function')
def mock_redis(redis_client):
    """Mock Redis in application."""
    with patch('redis.Redis', return_value=redis_client):
        yield redis_client


# ============================================================================
# AUTHENTICATION FIXTURES
# ============================================================================

@pytest.fixture(scope='function')
def api_key(app, redis_client):
    """Create valid API key for testing."""
    from src.security.auth import APIKeyManager
    
    manager = APIKeyManager(redis_client)
    api_key = manager.create_api_key(
        user_id='test_user',
        name='Test Key',
        rate_limit=10000
    )
    
    return api_key


@pytest.fixture(scope='function')
def auth_headers(api_key):
    """Create authentication headers."""
    return {'X-API-Key': api_key}


# ============================================================================
# MODEL FIXTURES
# ============================================================================

@pytest.fixture(scope='function')
def mock_model():
    """Create mock ML model."""
    mock = Mock()
    mock.predict.return_value = 0.85  # Mock confidence score
    mock.predict_proba.return_value = [[0.15, 0.85]]
    
    return mock


@pytest.fixture(scope='function')
def spam_detector(mock_model):
    """Create spam detector with mock model."""
    from src.core_detector import SpamDetector
    
    detector = SpamDetector()
    detector.model = mock_model
    
    return detector


# ============================================================================
# DATA FIXTURES
# ============================================================================

@pytest.fixture
def spam_text():
    """Sample spam text."""
    return "SLOT GACOR MAXWIN! 🎰💰 Daftar sekarang di link.slot.gacor"


@pytest.fixture
def ham_text():
    """Sample ham (legitimate) text."""
    return "Hello, how are you today? Hope you're doing well!"


@pytest.fixture
def batch_texts():
    """Batch of mixed spam and ham texts."""
    return [
        "SLOT GACOR MAXWIN!",
        "Hello friend",
        "Togel online terpercaya",
        "Nice video!",
        "🎰🎰🎰 JACKPOT",
        "Thanks for sharing"
    ]


# ============================================================================
# FACTORY FIXTURES
# ============================================================================

@pytest.fixture
def spam_log_factory(db_session):
    """Factory for creating spam log entries."""
    def create_spam_log(**kwargs):
        from src.models import SpamLog
        
        defaults = {
            'platform': 'youtube',
            'content_id': 'test_video_123',
            'comment_id': 'comment_456',
            'author_id': 'user_789',
            'comment_text': 'SLOT GACOR',
            'confidence_score': 75.5,
            'detected_keywords': ['slot', 'gacor']
        }
        defaults.update(kwargs)
        
        spam_log = SpamLog(**defaults)
        db_session.add(spam_log)
        db_session.commit()
        
        return spam_log
    
    return create_spam_log


# ============================================================================
# MOCK EXTERNAL APIS
# ============================================================================

@pytest.fixture
def mock_youtube_api():
    """Mock YouTube API responses."""
    with patch('googleapiclient.discovery.build') as mock_build:
        mock_service = Mock()
        mock_build.return_value = mock_service
        
        # Mock comments list
        mock_service.commentThreads().list().execute.return_value = {
            'items': [
                {
                    'id': 'comment_1',
                    'snippet': {
                        'topLevelComment': {
                            'id': 'comment_1',
                            'snippet': {
                                'textDisplay': 'SLOT GACOR',
                                'authorDisplayName': 'Spammer',
                                'authorChannelId': {'value': 'UC123'}
                            }
                        }
                    }
                }
            ]
        }
        
        yield mock_service


@pytest.fixture
def mock_instagram_api():
    """Mock Instagram Graph API responses."""
    import responses
    
    responses.add(
        responses.GET,
        'https://graph.instagram.com/v12.0/me/media',
        json={'data': [{'id': 'media_123'}]},
        status=200
    )
    
    responses.add(
        responses.GET,
        'https://graph.instagram.com/v12.0/media_123/comments',
        json={
            'data': [
                {
                    'id': 'comment_1',
                    'text': 'SLOT GACOR',
                    'username': 'spammer'
                }
            ]
        },
        status=200
    )
    
    yield responses


# ============================================================================
# UTILITY FIXTURES
# ============================================================================

@pytest.fixture
def capture_logs():
    """Capture log messages for testing."""
    from src.logging_config import get_logger
    import logging
    from io import StringIO
    
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.DEBUG)
    
    logger = get_logger('test')
    logger.addHandler(handler)
    
    yield log_stream
    
    logger.removeHandler(handler)


@pytest.fixture
def freezer():
    """Freeze time for testing."""
    from freezegun import freeze_time
    
    with freeze_time('2024-01-01 12:00:00') as frozen_time:
        yield frozen_time


# ============================================================================
# PERFORMANCE FIXTURES
# ============================================================================

@pytest.fixture
def performance_timer():
    """Timer for performance tests."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        @property
        def duration(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()


# ============================================================================
# CLEANUP
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """Cleanup temporary files after tests."""
    yield
    
    # Clean up temp test databases
    import glob
    for db_file in glob.glob('test_*.db'):
        try:
            os.remove(db_file)
        except:
            pass
