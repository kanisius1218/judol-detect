#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube Adapter - Auto-Moderasi Spam Comments
Menggunakan YouTube Data API v3
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
import time

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from core_detector import SpamDetector, DetectionResult
from database import DatabaseManager

logger = logging.getLogger(__name__)


class YouTubeAdapter:
    """
    Adapter untuk YouTube platform.
    
    Features:
    - Monitor comments di video/channel
    - Auto-delete spam comments
    - Support untuk video comments dan replies
    - Rate limiting handling
    """
    
    def __init__(
        self,
        api_key: str,
        detector: SpamDetector,
        database: DatabaseManager,
        channel_id: Optional[str] = None
    ):
        """
        Initialize YouTube adapter.
        
        Args:
            api_key: YouTube Data API key
            detector: SpamDetector instance
            database: DatabaseManager instance
            channel_id: Your channel ID (optional, untuk filter)
        """
        self.api_key = api_key
        self.detector = detector
        self.database = database
        self.channel_id = channel_id
        
        # Build YouTube API client
        try:
            self.youtube = build('youtube', 'v3', developerKey=api_key)
            logger.info("YouTube API client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize YouTube API: {e}")
            raise
        
        # Statistics
        self.stats = {
            'comments_checked': 0,
            'spam_detected': 0,
            'spam_deleted': 0,
            'errors': 0
        }
    
    # ========================================================================
    # COMMENT MONITORING
    # ========================================================================
    
    def get_video_comments(
        self,
        video_id: str,
        max_results: int = 100
    ) -> List[Dict]:
        """
        Ambil comments dari video tertentu.
        
        Args:
            video_id: YouTube video ID
            max_results: Maximum jumlah comments
            
        Returns:
            List of comment dicts
        """
        try:
            comments = []
            request = self.youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=min(max_results, 100),
                textFormat='plainText',
                order='time'  # Newest first
            )
            
            while request and len(comments) < max_results:
                response = request.execute()
                
                for item in response['items']:
                    snippet = item['snippet']['topLevelComment']['snippet']
                    comments.append({
                        'comment_id': item['snippet']['topLevelComment']['id'],
                        'video_id': video_id,
                        'author_id': snippet['authorChannelId']['value'] if 'authorChannelId' in snippet else 'unknown',
                        'author_name': snippet['authorDisplayName'],
                        'text': snippet['textDisplay'],
                        'published_at': snippet['publishedAt'],
                        'like_count': snippet['likeCount']
                    })
                
                # Check if there are more pages
                if 'nextPageToken' in response and len(comments) < max_results:
                    request = self.youtube.commentThreads().list(
                        part='snippet',
                        videoId=video_id,
                        maxResults=min(max_results - len(comments), 100),
                        textFormat='plainText',
                        order='time',
                        pageToken=response['nextPageToken']
                    )
                else:
                    request = None
            
            logger.info(f"Retrieved {len(comments)} comments from video {video_id}")
            return comments
            
        except HttpError as e:
            logger.error(f"HTTP error getting comments: {e}")
            self.stats['errors'] += 1
            return []
        except Exception as e:
            logger.error(f"Error getting comments: {e}")
            self.stats['errors'] += 1
            return []
    
    def get_channel_comments(
        self,
        channel_id: Optional[str] = None,
        max_results: int = 100
    ) -> List[Dict]:
        """
        Ambil comments dari semua video di channel.
        
        Args:
            channel_id: Channel ID (None = use self.channel_id)
            max_results: Maximum jumlah comments
            
        Returns:
            List of comment dicts
        """
        channel_id = channel_id or self.channel_id
        
        if not channel_id:
            logger.error("Channel ID not provided")
            return []
        
        try:
            comments = []
            request = self.youtube.commentThreads().list(
                part='snippet',
                allThreadsRelatedToChannelId=channel_id,
                maxResults=min(max_results, 100),
                textFormat='plainText',
                order='time'
            )
            
            while request and len(comments) < max_results:
                response = request.execute()
                
                for item in response['items']:
                    snippet = item['snippet']['topLevelComment']['snippet']
                    comments.append({
                        'comment_id': item['snippet']['topLevelComment']['id'],
                        'video_id': snippet['videoId'],
                        'author_id': snippet['authorChannelId']['value'] if 'authorChannelId' in snippet else 'unknown',
                        'author_name': snippet['authorDisplayName'],
                        'text': snippet['textDisplay'],
                        'published_at': snippet['publishedAt'],
                        'like_count': snippet['likeCount']
                    })
                
                if 'nextPageToken' in response and len(comments) < max_results:
                    request = self.youtube.commentThreads().list(
                        part='snippet',
                        allThreadsRelatedToChannelId=channel_id,
                        maxResults=min(max_results - len(comments), 100),
                        textFormat='plainText',
                        order='time',
                        pageToken=response['nextPageToken']
                    )
                else:
                    request = None
            
            logger.info(f"Retrieved {len(comments)} comments from channel")
            return comments
            
        except HttpError as e:
            logger.error(f"HTTP error getting channel comments: {e}")
            self.stats['errors'] += 1
            return []
        except Exception as e:
            logger.error(f"Error getting channel comments: {e}")
            self.stats['errors'] += 1
            return []
    
    # ========================================================================
    # SPAM DETECTION & DELETION
    # ========================================================================
    
    def check_and_delete_spam(
        self,
        comment: Dict,
        dry_run: bool = False
    ) -> Optional[DetectionResult]:
        """
        Check comment untuk spam dan delete jika terdeteksi.
        
        Args:
            comment: Comment dict
            dry_run: Jika True, tidak akan delete (testing mode)
            
        Returns:
            DetectionResult jika spam, None jika bukan spam
        """
        self.stats['comments_checked'] += 1
        self.database.update_comment_count('youtube')
        
        # Check whitelist
        if self.database.is_whitelisted('youtube', comment['author_id']):
            logger.debug(f"Skipping whitelisted user: {comment['author_name']}")
            return None
        
        # Detect spam
        result = self.detector.detect(
            text=comment['text'],
            author=comment['author_name']
        )
        
        if result.is_spam:
            self.stats['spam_detected'] += 1
            
            logger.warning(
                f"SPAM DETECTED on YouTube!\n"
                f"  Video: {comment['video_id']}\n"
                f"  Author: {comment['author_name']}\n"
                f"  Confidence: {result.confidence}%\n"
                f"  Text: {comment['text'][:100]}..."
            )
            
            # Log to database
            self.database.log_spam(
                platform='youtube',
                content_id=comment['video_id'],
                content_url=f"https://youtube.com/watch?v={comment['video_id']}",
                comment_id=comment['comment_id'],
                author_id=comment['author_id'],
                author_name=comment['author_name'],
                comment_text=comment['text'],
                detected_keywords=result.detected_keywords,
                detected_patterns=result.detected_patterns,
                confidence_score=result.confidence
            )
            
            # Delete comment
            if not dry_run:
                if self.delete_comment(comment['comment_id']):
                    self.stats['spam_deleted'] += 1
                    logger.info(f"✅ Spam comment deleted: {comment['comment_id']}")
                else:
                    logger.error(f"❌ Failed to delete comment: {comment['comment_id']}")
            else:
                logger.info(f"[DRY RUN] Would delete comment: {comment['comment_id']}")
            
            return result
        
        return None
    
    def delete_comment(self, comment_id: str) -> bool:
        """
        Delete comment by ID.
        
        Args:
            comment_id: Comment ID
            
        Returns:
            bool: True jika berhasil
        """
        try:
            self.youtube.comments().delete(id=comment_id).execute()
            logger.info(f"Comment deleted: {comment_id}")
            return True
            
        except HttpError as e:
            if e.resp.status == 403:
                logger.error(f"Permission denied to delete comment: {e}")
            elif e.resp.status == 404:
                logger.error(f"Comment not found: {e}")
            else:
                logger.error(f"HTTP error deleting comment: {e}")
            return False
            
        except Exception as e:
            logger.error(f"Error deleting comment: {e}")
            return False
    
    # ========================================================================
    # BATCH PROCESSING
    # ========================================================================
    
    def moderate_video(
        self,
        video_id: str,
        max_comments: int = 100,
        dry_run: bool = False
    ) -> Dict:
        """
        Moderate semua comments di video tertentu.
        
        Args:
            video_id: YouTube video ID
            max_comments: Maximum comments to check
            dry_run: Testing mode (tidak delete)
            
        Returns:
            Dict: Statistics hasil moderasi
        """
        logger.info(f"Starting moderation for video: {video_id}")
        
        # Get comments
        comments = self.get_video_comments(video_id, max_comments)
        
        if not comments:
            logger.info("No comments found")
            return {'checked': 0, 'spam_found': 0, 'deleted': 0}
        
        # Check each comment
        spam_found = 0
        for comment in comments:
            result = self.check_and_delete_spam(comment, dry_run=dry_run)
            if result:
                spam_found += 1
            
            # Rate limiting: sleep between requests
            time.sleep(0.1)
        
        result_stats = {
            'checked': len(comments),
            'spam_found': spam_found,
            'deleted': spam_found if not dry_run else 0
        }
        
        logger.info(
            f"Moderation completed: {result_stats['checked']} checked, "
            f"{result_stats['spam_found']} spam found, "
            f"{result_stats['deleted']} deleted"
        )
        
        return result_stats
    
    def moderate_channel(
        self,
        channel_id: Optional[str] = None,
        max_comments: int = 100,
        dry_run: bool = False
    ) -> Dict:
        """
        Moderate semua comments di channel.
        
        Args:
            channel_id: Channel ID (None = use self.channel_id)
            max_comments: Maximum comments to check
            dry_run: Testing mode
            
        Returns:
            Dict: Statistics hasil moderasi
        """
        logger.info(f"Starting channel moderation")
        
        # Get comments
        comments = self.get_channel_comments(channel_id, max_comments)
        
        if not comments:
            logger.info("No comments found")
            return {'checked': 0, 'spam_found': 0, 'deleted': 0}
        
        # Check each comment
        spam_found = 0
        for comment in comments:
            result = self.check_and_delete_spam(comment, dry_run=dry_run)
            if result:
                spam_found += 1
            
            time.sleep(0.1)
        
        result_stats = {
            'checked': len(comments),
            'spam_found': spam_found,
            'deleted': spam_found if not dry_run else 0
        }
        
        logger.info(
            f"Channel moderation completed: {result_stats['checked']} checked, "
            f"{result_stats['spam_found']} spam found, "
            f"{result_stats['deleted']} deleted"
        )
        
        return result_stats
    
    # ========================================================================
    # UTILITIES
    # ========================================================================
    
    def get_stats(self) -> Dict:
        """Get adapter statistics."""
        return self.stats.copy()
    
    def reset_stats(self) -> None:
        """Reset statistics."""
        self.stats = {
            'comments_checked': 0,
            'spam_detected': 0,
            'spam_deleted': 0,
            'errors': 0
        }


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 70)
    print("YouTube Adapter Test")
    print("=" * 70)
    print()
    print("⚠️  IMPORTANT:")
    print("1. Dapatkan YouTube Data API key dari Google Cloud Console")
    print("2. Enable YouTube Data API v3")
    print("3. Set API key di bawah")
    print()
    print("API Setup Guide:")
    print("- Go to: https://console.cloud.google.com/")
    print("- Create new project")
    print("- Enable YouTube Data API v3")
    print("- Create credentials (API key)")
    print("- Copy API key")
    print()
    print("=" * 70)
