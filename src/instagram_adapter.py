#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instagram Adapter - Auto-Moderasi Spam Comments
Menggunakan Instagram Graph API (Facebook)
"""

import logging
import requests
import time
from typing import List, Dict, Optional
from datetime import datetime

from core_detector import SpamDetector, DetectionResult
from database import DatabaseManager

logger = logging.getLogger(__name__)


class InstagramAdapter:
    """
    Adapter untuk Instagram platform menggunakan Graph API.
    
    Features:
    - Monitor comments di posts
    - Auto-delete spam comments
    - Support untuk media comments
    - Rate limiting handling
    
    Requirements:
    - Instagram Business/Creator account
    - Facebook Page connected
    - Access token with permissions:
      - instagram_basic
      - instagram_manage_comments
      - pages_read_engagement
    """
    
    def __init__(
        self,
        access_token: str,
        instagram_user_id: str,
        detector: SpamDetector,
        database: DatabaseManager
    ):
        """
        Initialize Instagram adapter.
        
        Args:
            access_token: Facebook Graph API access token
            instagram_user_id: Instagram Business Account ID
            detector: SpamDetector instance
            database: DatabaseManager instance
        """
        self.access_token = access_token
        self.instagram_user_id = instagram_user_id
        self.detector = detector
        self.database = database
        
        # API configuration
        self.api_version = 'v18.0'
        self.base_url = f'https://graph.facebook.com/{self.api_version}'
        
        # Rate limiting
        self.rate_limit_remaining = 200  # Instagram: 200 calls/hour
        self.rate_limit_reset = None
        
        # Statistics
        self.stats = {
            'comments_checked': 0,
            'spam_detected': 0,
            'spam_deleted': 0,
            'errors': 0,
            'rate_limited': 0
        }
        
        logger.info("Instagram API client initialized")
    
    # ========================================================================
    # API HELPERS
    # ========================================================================
    
    def _make_request(
        self,
        endpoint: str,
        method: str = 'GET',
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Make API request dengan error handling dan rate limiting.
        
        Args:
            endpoint: API endpoint
            method: HTTP method (GET, POST, DELETE)
            params: Query parameters
            data: Request body data
            
        Returns:
            Dict: Response data atau None jika error
        """
        url = f"{self.base_url}/{endpoint}"
        
        # Add access token to params
        if params is None:
            params = {}
        params['access_token'] = self.access_token
        
        try:
            if method == 'GET':
                response = requests.get(url, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, params=params, json=data, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, params=params, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # Check rate limiting
            if 'X-App-Usage' in response.headers:
                usage = eval(response.headers['X-App-Usage'])
                self.rate_limit_remaining = 200 - usage.get('call_count', 0)
            
            # Handle rate limit
            if response.status_code == 429:
                logger.warning("Rate limit exceeded, waiting...")
                self.stats['rate_limited'] += 1
                time.sleep(3600)  # Wait 1 hour
                return self._make_request(endpoint, method, params, data)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request error: {e}")
            self.stats['errors'] += 1
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            self.stats['errors'] += 1
            return None
    
    # ========================================================================
    # MEDIA & COMMENTS
    # ========================================================================
    
    def get_recent_media(self, limit: int = 10) -> List[Dict]:
        """
        Ambil recent media (posts) dari account.
        
        Args:
            limit: Maximum jumlah media
            
        Returns:
            List of media dicts
        """
        try:
            response = self._make_request(
                f"{self.instagram_user_id}/media",
                params={
                    'fields': 'id,caption,media_type,media_url,permalink,timestamp',
                    'limit': limit
                }
            )
            
            if response and 'data' in response:
                media_list = response['data']
                logger.info(f"Retrieved {len(media_list)} media items")
                return media_list
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting media: {e}")
            return []
    
    def get_media_comments(
        self,
        media_id: str,
        limit: int = 100
    ) -> List[Dict]:
        """
        Ambil comments dari media tertentu.
        
        Args:
            media_id: Instagram media ID
            limit: Maximum jumlah comments
            
        Returns:
            List of comment dicts
        """
        try:
            comments = []
            after = None
            
            while len(comments) < limit:
                params = {
                    'fields': 'id,text,username,timestamp,like_count,from',
                    'limit': min(50, limit - len(comments))
                }
                
                if after:
                    params['after'] = after
                
                response = self._make_request(
                    f"{media_id}/comments",
                    params=params
                )
                
                if not response or 'data' not in response:
                    break
                
                comments.extend(response['data'])
                
                # Check if there are more pages
                if 'paging' in response and 'next' in response['paging']:
                    cursors = response['paging'].get('cursors', {})
                    after = cursors.get('after')
                    if not after:
                        break
                else:
                    break
            
            logger.info(f"Retrieved {len(comments)} comments from media {media_id}")
            return comments
            
        except Exception as e:
            logger.error(f"Error getting comments: {e}")
            return []
    
    def get_all_recent_comments(self, max_media: int = 10) -> List[Dict]:
        """
        Ambil semua recent comments dari recent media.
        
        Args:
            max_media: Maximum media to check
            
        Returns:
            List of comment dicts with media info
        """
        all_comments = []
        
        # Get recent media
        media_list = self.get_recent_media(limit=max_media)
        
        for media in media_list:
            comments = self.get_media_comments(media['id'])
            
            # Add media info to each comment
            for comment in comments:
                comment['media_id'] = media['id']
                comment['media_url'] = media.get('permalink', '')
                all_comments.append(comment)
            
            # Rate limiting: sleep between requests
            time.sleep(0.5)
        
        logger.info(f"Retrieved {len(all_comments)} total comments from {len(media_list)} media")
        return all_comments
    
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
        self.database.update_comment_count('instagram')
        
        # Get author info
        author_id = comment.get('from', {}).get('id', 'unknown')
        author_username = comment.get('username', 'unknown')
        
        # Check whitelist
        if self.database.is_whitelisted('instagram', author_id):
            logger.debug(f"Skipping whitelisted user: {author_username}")
            return None
        
        # Detect spam
        result = self.detector.detect(
            text=comment.get('text', ''),
            author=author_username
        )
        
        if result.is_spam:
            self.stats['spam_detected'] += 1
            
            logger.warning(
                f"SPAM DETECTED on Instagram!\n"
                f"  Media: {comment.get('media_id', 'unknown')}\n"
                f"  Author: {author_username}\n"
                f"  Confidence: {result.confidence}%\n"
                f"  Text: {comment.get('text', '')[:100]}..."
            )
            
            # Log to database
            self.database.log_spam(
                platform='instagram',
                content_id=comment.get('media_id', 'unknown'),
                content_url=comment.get('media_url', ''),
                comment_id=comment['id'],
                author_id=author_id,
                author_name=author_username,
                comment_text=comment.get('text', ''),
                detected_keywords=result.detected_keywords,
                detected_patterns=result.detected_patterns,
                confidence_score=result.confidence
            )
            
            # Delete comment
            if not dry_run:
                if self.delete_comment(comment['id']):
                    self.stats['spam_deleted'] += 1
                    logger.info(f"✅ Spam comment deleted: {comment['id']}")
                else:
                    logger.error(f"❌ Failed to delete comment: {comment['id']}")
            else:
                logger.info(f"[DRY RUN] Would delete comment: {comment['id']}")
            
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
            response = self._make_request(
                comment_id,
                method='DELETE'
            )
            
            if response and response.get('success'):
                logger.info(f"Comment deleted: {comment_id}")
                return True
            else:
                logger.error(f"Failed to delete comment: {comment_id}")
                return False
            
        except Exception as e:
            logger.error(f"Error deleting comment: {e}")
            return False
    
    # ========================================================================
    # BATCH PROCESSING
    # ========================================================================
    
    def moderate_media(
        self,
        media_id: str,
        max_comments: int = 100,
        dry_run: bool = False
    ) -> Dict:
        """
        Moderate semua comments di media tertentu.
        
        Args:
            media_id: Instagram media ID
            max_comments: Maximum comments to check
            dry_run: Testing mode (tidak delete)
            
        Returns:
            Dict: Statistics hasil moderasi
        """
        logger.info(f"Starting moderation for media: {media_id}")
        
        # Get comments
        comments = self.get_media_comments(media_id, max_comments)
        
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
            time.sleep(0.2)
        
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
    
    def moderate_account(
        self,
        max_media: int = 10,
        max_comments_per_media: int = 50,
        dry_run: bool = False
    ) -> Dict:
        """
        Moderate semua comments di recent media.
        
        Args:
            max_media: Maximum media to check
            max_comments_per_media: Maximum comments per media
            dry_run: Testing mode
            
        Returns:
            Dict: Statistics hasil moderasi
        """
        logger.info(f"Starting account moderation")
        
        total_checked = 0
        total_spam = 0
        total_deleted = 0
        
        # Get recent media
        media_list = self.get_recent_media(limit=max_media)
        
        if not media_list:
            logger.info("No media found")
            return {'checked': 0, 'spam_found': 0, 'deleted': 0}
        
        # Moderate each media
        for media in media_list:
            logger.info(f"Checking media: {media['id']}")
            
            result = self.moderate_media(
                media['id'],
                max_comments=max_comments_per_media,
                dry_run=dry_run
            )
            
            total_checked += result['checked']
            total_spam += result['spam_found']
            total_deleted += result['deleted']
            
            # Rate limiting between media
            time.sleep(1)
        
        result_stats = {
            'media_checked': len(media_list),
            'comments_checked': total_checked,
            'spam_found': total_spam,
            'deleted': total_deleted
        }
        
        logger.info(
            f"Account moderation completed: {result_stats['media_checked']} media, "
            f"{result_stats['comments_checked']} comments checked, "
            f"{result_stats['spam_found']} spam found, "
            f"{result_stats['deleted']} deleted"
        )
        
        return result_stats
    
    # ========================================================================
    # UTILITIES
    # ========================================================================
    
    def verify_token(self) -> bool:
        """
        Verify access token validity.
        
        Returns:
            bool: True jika token valid
        """
        try:
            response = self._make_request(
                'me',
                params={'fields': 'id,name'}
            )
            
            if response and 'id' in response:
                logger.info(f"Token valid for: {response.get('name', 'Unknown')}")
                return True
            else:
                logger.error("Invalid access token")
                return False
                
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return False
    
    def get_account_info(self) -> Optional[Dict]:
        """
        Get Instagram account information.
        
        Returns:
            Dict: Account info atau None
        """
        try:
            response = self._make_request(
                self.instagram_user_id,
                params={'fields': 'id,username,name,profile_picture_url,followers_count,follows_count,media_count'}
            )
            
            if response:
                logger.info(f"Account: @{response.get('username', 'unknown')}")
                return response
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None
    
    def get_stats(self) -> Dict:
        """Get adapter statistics."""
        stats = self.stats.copy()
        stats['rate_limit_remaining'] = self.rate_limit_remaining
        return stats
    
    def reset_stats(self) -> None:
        """Reset statistics."""
        self.stats = {
            'comments_checked': 0,
            'spam_detected': 0,
            'spam_deleted': 0,
            'errors': 0,
            'rate_limited': 0
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
    print("Instagram Adapter Test")
    print("=" * 70)
    print()
    print("⚠️  IMPORTANT:")
    print("1. Dapatkan Instagram Access Token dari Facebook Graph API")
    print("2. Perlu Instagram Business/Creator account")
    print("3. Connect ke Facebook Page")
    print()
    print("API Setup Guide:")
    print("- Go to: https://developers.facebook.com/")
    print("- Create app")
    print("- Add Instagram product")
    print("- Get access token with permissions:")
    print("  - instagram_basic")
    print("  - instagram_manage_comments")
    print("  - pages_read_engagement")
    print()
    print("=" * 70)
