#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Manager - Multi-Platform
Mengelola database untuk logging spam dari semua platform
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SpamLog:
    """Data class untuk spam log entry."""
    id: Optional[int]
    platform: str  # 'youtube', 'tiktok', 'instagram'
    content_id: str  # video_id, post_id, dll
    content_url: str
    comment_id: str
    author_id: str
    author_name: str
    comment_text: str
    detected_keywords: str
    detected_patterns: str
    confidence_score: int
    timestamp: datetime


class DatabaseManager:
    """
    Mengelola semua operasi database untuk multi-platform bot.
    
    Handles:
    - Inisialisasi database dan tabel
    - Logging spam yang terdeteksi
    - Manajemen whitelist
    - Pengambilan statistik per platform
    - Export data
    """
    
    def __init__(self, db_file: str = "spam_moderator.db"):
        """
        Initialize database manager.
        
        Args:
            db_file: Path ke file database SQLite
        """
        self.db_file = db_file
        self.init_database()
        logger.info(f"DatabaseManager initialized: {db_file}")
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Membuat koneksi ke database.
        
        Returns:
            sqlite3.Connection: Objek koneksi database
        """
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self) -> None:
        """
        Inisialisasi database dan membuat tabel jika belum ada.
        
        Creates:
        - spam_logs: Log semua spam yang terdeteksi dari semua platform
        - whitelist: Daftar user yang di-whitelist per platform
        - stats: Statistik harian per platform
        - platform_config: Konfigurasi per platform
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Tabel spam_logs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS spam_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    content_id TEXT NOT NULL,
                    content_url TEXT,
                    comment_id TEXT NOT NULL,
                    author_id TEXT NOT NULL,
                    author_name TEXT,
                    comment_text TEXT NOT NULL,
                    detected_keywords TEXT,
                    detected_patterns TEXT,
                    confidence_score INTEGER NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabel whitelist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS whitelist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    author_id TEXT NOT NULL,
                    author_name TEXT,
                    added_by TEXT,
                    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(platform, author_id)
                )
            ''')
            
            # Tabel stats
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    platform TEXT NOT NULL,
                    total_comments INTEGER DEFAULT 0,
                    spam_detected INTEGER DEFAULT 0,
                    spam_deleted INTEGER DEFAULT 0,
                    UNIQUE(date, platform)
                )
            ''')
            
            # Tabel platform_config
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS platform_config (
                    platform TEXT PRIMARY KEY,
                    enabled BOOLEAN DEFAULT 1,
                    api_key TEXT,
                    api_secret TEXT,
                    confidence_threshold INTEGER DEFAULT 40,
                    last_check DATETIME,
                    total_processed INTEGER DEFAULT 0
                )
            ''')
            
            # Indexes untuk performa
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_spam_logs_platform 
                ON spam_logs(platform)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_spam_logs_timestamp 
                ON spam_logs(timestamp)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_spam_logs_author 
                ON spam_logs(author_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_whitelist_platform_author 
                ON whitelist(platform, author_id)
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    # ========================================================================
    # SPAM LOGGING
    # ========================================================================
    
    def log_spam(
        self,
        platform: str,
        content_id: str,
        content_url: str,
        comment_id: str,
        author_id: str,
        author_name: str,
        comment_text: str,
        detected_keywords: List[str],
        detected_patterns: List[str],
        confidence_score: int
    ) -> bool:
        """
        Log spam yang terdeteksi ke database.
        
        Args:
            platform: Platform name ('youtube', 'tiktok', 'instagram')
            content_id: ID konten (video_id, post_id, dll)
            content_url: URL konten
            comment_id: ID comment
            author_id: ID author
            author_name: Nama author
            comment_text: Isi comment
            detected_keywords: List keywords yang terdeteksi
            detected_patterns: List patterns yang terdeteksi
            confidence_score: Confidence score (0-100)
            
        Returns:
            bool: True jika berhasil, False jika gagal
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Insert spam log
            cursor.execute('''
                INSERT INTO spam_logs 
                (platform, content_id, content_url, comment_id, author_id, 
                 author_name, comment_text, detected_keywords, detected_patterns, 
                 confidence_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                platform,
                content_id,
                content_url,
                comment_id,
                author_id,
                author_name,
                comment_text,
                ','.join(detected_keywords),
                ','.join(detected_patterns),
                confidence_score
            ))
            
            # Update stats
            today = datetime.now().date()
            cursor.execute('''
                INSERT INTO stats (date, platform, total_comments, spam_detected, spam_deleted)
                VALUES (?, ?, 1, 1, 1)
                ON CONFLICT(date, platform) DO UPDATE SET
                    spam_detected = spam_detected + 1,
                    spam_deleted = spam_deleted + 1
            ''', (today, platform))
            
            conn.commit()
            conn.close()
            
            logger.info(
                f"Spam logged: platform={platform}, author={author_name}, "
                f"confidence={confidence_score}%"
            )
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error logging spam: {e}")
            return False
    
    def update_comment_count(self, platform: str) -> None:
        """
        Update jumlah comment yang dicek hari ini untuk platform tertentu.
        
        Args:
            platform: Platform name
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            today = datetime.now().date()
            cursor.execute('''
                INSERT INTO stats (date, platform, total_comments)
                VALUES (?, ?, 1)
                ON CONFLICT(date, platform) DO UPDATE SET
                    total_comments = total_comments + 1
            ''', (today, platform))
            
            conn.commit()
            conn.close()
            
        except sqlite3.Error as e:
            logger.error(f"Error updating comment count: {e}")
    
    # ========================================================================
    # WHITELIST MANAGEMENT
    # ========================================================================
    
    def is_whitelisted(self, platform: str, author_id: str) -> bool:
        """
        Cek apakah user ada di whitelist untuk platform tertentu.
        
        Args:
            platform: Platform name
            author_id: Author ID
            
        Returns:
            bool: True jika whitelisted, False jika tidak
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT id FROM whitelist WHERE platform = ? AND author_id = ?',
                (platform, author_id)
            )
            result = cursor.fetchone()
            
            conn.close()
            return result is not None
            
        except sqlite3.Error as e:
            logger.error(f"Error checking whitelist: {e}")
            return False
    
    def add_to_whitelist(
        self,
        platform: str,
        author_id: str,
        author_name: str,
        added_by: str = "system"
    ) -> bool:
        """
        Tambahkan user ke whitelist untuk platform tertentu.
        
        Args:
            platform: Platform name
            author_id: Author ID yang akan di-whitelist
            author_name: Nama author
            added_by: Siapa yang menambahkan
            
        Returns:
            bool: True jika berhasil, False jika gagal atau sudah ada
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO whitelist (platform, author_id, author_name, added_by)
                VALUES (?, ?, ?, ?)
            ''', (platform, author_id, author_name, added_by))
            
            rows_affected = cursor.rowcount
            conn.commit()
            conn.close()
            
            if rows_affected > 0:
                logger.info(f"User {author_name} added to whitelist on {platform}")
                return True
            else:
                logger.info(f"User {author_name} already in whitelist on {platform}")
                return False
            
        except sqlite3.Error as e:
            logger.error(f"Error adding to whitelist: {e}")
            return False
    
    def remove_from_whitelist(self, platform: str, author_id: str) -> bool:
        """
        Hapus user dari whitelist.
        
        Args:
            platform: Platform name
            author_id: Author ID
            
        Returns:
            bool: True jika berhasil, False jika gagal
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'DELETE FROM whitelist WHERE platform = ? AND author_id = ?',
                (platform, author_id)
            )
            
            rows_affected = cursor.rowcount
            conn.commit()
            conn.close()
            
            return rows_affected > 0
            
        except sqlite3.Error as e:
            logger.error(f"Error removing from whitelist: {e}")
            return False
    
    # ========================================================================
    # STATISTICS
    # ========================================================================
    
    def get_stats(
        self,
        platform: Optional[str] = None,
        days: int = 7
    ) -> Dict:
        """
        Ambil statistik untuk periode tertentu.
        
        Args:
            platform: Platform name (None = all platforms)
            days: Jumlah hari ke belakang
            
        Returns:
            Dict: Statistik dengan keys: total_comments, spam_detected, 
                  spam_deleted, unique_spammers, affected_contents
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            start_date = datetime.now().date() - timedelta(days=days)
            
            # Build query based on platform filter
            platform_filter = ""
            params = [start_date]
            
            if platform:
                platform_filter = "AND platform = ?"
                params.append(platform)
            
            # Total comments, spam detected, spam deleted
            cursor.execute(f'''
                SELECT 
                    COALESCE(SUM(total_comments), 0) as total_comments,
                    COALESCE(SUM(spam_detected), 0) as spam_detected,
                    COALESCE(SUM(spam_deleted), 0) as spam_deleted
                FROM stats
                WHERE date >= ? {platform_filter}
            ''', params)
            
            stats_row = cursor.fetchone()
            
            # Unique spammers
            cursor.execute(f'''
                SELECT COUNT(DISTINCT author_id) as unique_spammers
                FROM spam_logs
                WHERE DATE(timestamp) >= ? {platform_filter}
            ''', params)
            
            spammers_row = cursor.fetchone()
            
            # Affected contents
            cursor.execute(f'''
                SELECT COUNT(DISTINCT content_id) as affected_contents
                FROM spam_logs
                WHERE DATE(timestamp) >= ? {platform_filter}
            ''', params)
            
            contents_row = cursor.fetchone()
            
            conn.close()
            
            return {
                'total_comments': stats_row['total_comments'],
                'spam_detected': stats_row['spam_detected'],
                'spam_deleted': stats_row['spam_deleted'],
                'unique_spammers': spammers_row['unique_spammers'],
                'affected_contents': contents_row['affected_contents']
            }
            
        except sqlite3.Error as e:
            logger.error(f"Error getting stats: {e}")
            return {
                'total_comments': 0,
                'spam_detected': 0,
                'spam_deleted': 0,
                'unique_spammers': 0,
                'affected_contents': 0
            }
    
    def get_platform_stats(self, days: int = 7) -> Dict[str, Dict]:
        """
        Get statistics per platform.
        
        Args:
            days: Jumlah hari ke belakang
            
        Returns:
            Dict: Stats per platform
        """
        platforms = ['youtube', 'tiktok', 'instagram']
        result = {}
        
        for platform in platforms:
            result[platform] = self.get_stats(platform=platform, days=days)
        
        return result
    
    def get_top_spammers(
        self,
        platform: Optional[str] = None,
        limit: int = 10,
        days: int = 30
    ) -> List[Tuple[str, str, int]]:
        """
        Get top spammers.
        
        Args:
            platform: Platform name (None = all platforms)
            limit: Jumlah hasil
            days: Periode dalam hari
            
        Returns:
            List of tuples: (author_id, author_name, spam_count)
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            start_date = datetime.now().date() - timedelta(days=days)
            
            platform_filter = ""
            params = [start_date, limit]
            
            if platform:
                platform_filter = "AND platform = ?"
                params = [start_date, platform, limit]
            
            cursor.execute(f'''
                SELECT author_id, author_name, COUNT(*) as spam_count
                FROM spam_logs
                WHERE DATE(timestamp) >= ? {platform_filter}
                GROUP BY author_id
                ORDER BY spam_count DESC
                LIMIT ?
            ''', params)
            
            results = cursor.fetchall()
            conn.close()
            
            return [(row['author_id'], row['author_name'], row['spam_count']) 
                    for row in results]
            
        except sqlite3.Error as e:
            logger.error(f"Error getting top spammers: {e}")
            return []
    
    # ========================================================================
    # PLATFORM CONFIG
    # ========================================================================
    
    def save_platform_config(
        self,
        platform: str,
        enabled: bool = True,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        confidence_threshold: int = 40
    ) -> bool:
        """
        Save platform configuration.
        
        Args:
            platform: Platform name
            enabled: Apakah platform enabled
            api_key: API key
            api_secret: API secret
            confidence_threshold: Confidence threshold
            
        Returns:
            bool: True jika berhasil
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO platform_config 
                (platform, enabled, api_key, api_secret, confidence_threshold)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(platform) DO UPDATE SET
                    enabled = excluded.enabled,
                    api_key = excluded.api_key,
                    api_secret = excluded.api_secret,
                    confidence_threshold = excluded.confidence_threshold
            ''', (platform, enabled, api_key, api_secret, confidence_threshold))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Platform config saved: {platform}")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error saving platform config: {e}")
            return False
    
    def get_platform_config(self, platform: str) -> Optional[Dict]:
        """
        Get platform configuration.
        
        Args:
            platform: Platform name
            
        Returns:
            Dict: Configuration atau None jika tidak ada
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT * FROM platform_config WHERE platform = ?',
                (platform,)
            )
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return dict(row)
            return None
            
        except sqlite3.Error as e:
            logger.error(f"Error getting platform config: {e}")
            return None
    
    # ========================================================================
    # EXPORT
    # ========================================================================
    
    def export_spam_logs_csv(
        self,
        filename: str,
        platform: Optional[str] = None,
        days: int = 30
    ) -> bool:
        """
        Export spam logs ke CSV file.
        
        Args:
            filename: Output filename
            platform: Platform filter (None = all)
            days: Periode dalam hari
            
        Returns:
            bool: True jika berhasil
        """
        try:
            import csv
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            start_date = datetime.now().date() - timedelta(days=days)
            
            platform_filter = ""
            params = [start_date]
            
            if platform:
                platform_filter = "AND platform = ?"
                params.append(platform)
            
            cursor.execute(f'''
                SELECT * FROM spam_logs
                WHERE DATE(timestamp) >= ? {platform_filter}
                ORDER BY timestamp DESC
            ''', params)
            
            rows = cursor.fetchall()
            
            if rows:
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([desc[0] for desc in cursor.description])
                    writer.writerows(rows)
                
                logger.info(f"Exported {len(rows)} logs to {filename}")
                conn.close()
                return True
            else:
                logger.info("No logs to export")
                conn.close()
                return False
            
        except Exception as e:
            logger.error(f"Error exporting logs: {e}")
            return False


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test database
    db = DatabaseManager("test_spam_moderator.db")
    
    # Test logging spam
    db.log_spam(
        platform='youtube',
        content_id='test_video_123',
        content_url='https://youtube.com/watch?v=test123',
        comment_id='comment_456',
        author_id='user_789',
        author_name='TestSpammer',
        comment_text='SLOT GACOR MAXWIN!',
        detected_keywords=['slot', 'gacor', 'maxwin'],
        detected_patterns=['aggressive_caps'],
        confidence_score=75
    )
    
    # Test whitelist
    db.add_to_whitelist('youtube', 'user_999', 'TrustedUser')
    print(f"Is whitelisted: {db.is_whitelisted('youtube', 'user_999')}")
    
    # Test stats
    stats = db.get_stats(platform='youtube', days=7)
    print(f"Stats: {stats}")
    
    print("\n✅ Database test completed!")
