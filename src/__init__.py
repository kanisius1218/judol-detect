"""
Multi-Platform Spam Moderator
Auto-moderasi spam judi online untuk YouTube, Instagram, dan TikTok
"""

__version__ = "2.0.0"
__author__ = "AI Assistant"

from .core_detector import SpamDetector, DetectionResult
from .database import DatabaseManager
from .youtube_adapter import YouTubeAdapter
from .instagram_adapter import InstagramAdapter
from .analytics import AnalyticsEngine

__all__ = [
    'SpamDetector',
    'DetectionResult',
    'DatabaseManager',
    'YouTubeAdapter',
    'InstagramAdapter',
    'AnalyticsEngine'
]
