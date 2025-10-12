"""
Configuration file for the Message Detection System Web Application
"""

import os

class Config:
    """Base configuration"""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    # Server Configuration
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    
    # Session Configuration
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    
    # Model Configuration
    MODEL_PATH = 'ml_models'
    USE_ENSEMBLE = True
    FALLBACK_TO_BASIC = True
    MOCK_PREDICTIONS = True  # Use mock if no model available
    
    # API Rate Limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_DEFAULT = "100 per hour"
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'memory://')
    
    # Cache Configuration
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # UI Configuration
    MAX_MESSAGE_LENGTH = 5000
    MAX_BATCH_SIZE = 50
    HISTORY_SIZE = 10
    
    # Features Toggle
    ENABLE_BATCH_PROCESSING = True
    ENABLE_HISTORY = True
    ENABLE_STATISTICS = True
    ENABLE_FEEDBACK = False
    
    # Theme Configuration
    THEME = 'black-white'  # Options: 'black-white', 'dark', 'light'
    
    # Security
    CORS_ENABLED = True
    CORS_ORIGINS = ['http://localhost:3000', 'http://localhost:5173']
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'app.log'
    LOG_TO_FILE = False

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Use Redis for caching in production
    CACHE_TYPE = 'redis' if os.environ.get('REDIS_URL') else 'simple'
    CACHE_REDIS_URL = os.environ.get('REDIS_URL')
    
    # Stricter rate limiting in production
    RATELIMIT_DEFAULT = "50 per hour"

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    
    # Disable rate limiting for tests
    RATELIMIT_ENABLED = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
