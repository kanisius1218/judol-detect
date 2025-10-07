#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Analytics Module
Comprehensive analytics dan reporting untuk spam moderation
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import Counter
import json

from database import DatabaseManager

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    """
    Advanced analytics engine untuk spam moderation.
    
    Features:
    - Trend analysis
    - Top spammers tracking
    - Keyword frequency analysis
    - Platform comparison
    - Time-based patterns
    - Export reports
    """
    
    def __init__(self, database: DatabaseManager):
        """
        Initialize analytics engine.
        
        Args:
            database: DatabaseManager instance
        """
        self.database = database
        logger.info("Analytics engine initialized")
    
    # ========================================================================
    # TREND ANALYSIS
    # ========================================================================
    
    def get_spam_trend(
        self,
        platform: Optional[str] = None,
        days: int = 30
    ) -> List[Dict]:
        """
        Get spam trend over time.
        
        Args:
            platform: Platform filter (None = all)
            days: Number of days
            
        Returns:
            List of daily stats
        """
        try:
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            start_date = datetime.now().date() - timedelta(days=days)
            
            platform_filter = ""
            params = [start_date]
            
            if platform:
                platform_filter = "AND platform = ?"
                params.append(platform)
            
            cursor.execute(f'''
                SELECT 
                    date,
                    platform,
                    total_comments,
                    spam_detected,
                    spam_deleted,
                    CAST(spam_detected AS FLOAT) / NULLIF(total_comments, 0) * 100 as spam_rate
                FROM stats
                WHERE date >= ? {platform_filter}
                ORDER BY date ASC
            ''', params)
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'date': row['date'],
                    'platform': row['platform'],
                    'total_comments': row['total_comments'],
                    'spam_detected': row['spam_detected'],
                    'spam_deleted': row['spam_deleted'],
                    'spam_rate': round(row['spam_rate'] or 0, 2)
                })
            
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"Error getting spam trend: {e}")
            return []
    
    def get_hourly_pattern(
        self,
        platform: Optional[str] = None,
        days: int = 7
    ) -> Dict[int, int]:
        """
        Analyze spam patterns by hour of day.
        
        Args:
            platform: Platform filter
            days: Number of days to analyze
            
        Returns:
            Dict: {hour: spam_count}
        """
        try:
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            start_date = datetime.now().date() - timedelta(days=days)
            
            platform_filter = ""
            params = [start_date]
            
            if platform:
                platform_filter = "AND platform = ?"
                params.append(platform)
            
            cursor.execute(f'''
                SELECT 
                    CAST(strftime('%H', timestamp) AS INTEGER) as hour,
                    COUNT(*) as count
                FROM spam_logs
                WHERE DATE(timestamp) >= ? {platform_filter}
                GROUP BY hour
                ORDER BY hour
            ''', params)
            
            hourly_data = {hour: 0 for hour in range(24)}
            
            for row in cursor.fetchall():
                hourly_data[row['hour']] = row['count']
            
            conn.close()
            return hourly_data
            
        except Exception as e:
            logger.error(f"Error getting hourly pattern: {e}")
            return {}
    
    # ========================================================================
    # TOP LISTS
    # ========================================================================
    
    def get_top_spammers(
        self,
        platform: Optional[str] = None,
        limit: int = 20,
        days: int = 30
    ) -> List[Dict]:
        """
        Get top spammers dengan detail.
        
        Args:
            platform: Platform filter
            limit: Number of results
            days: Period in days
            
        Returns:
            List of spammer dicts
        """
        try:
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            start_date = datetime.now().date() - timedelta(days=days)
            
            platform_filter = ""
            params = [start_date, limit]
            
            if platform:
                platform_filter = "AND platform = ?"
                params = [start_date, platform, limit]
            
            cursor.execute(f'''
                SELECT 
                    author_id,
                    author_name,
                    platform,
                    COUNT(*) as spam_count,
                    AVG(confidence_score) as avg_confidence,
                    MIN(timestamp) as first_seen,
                    MAX(timestamp) as last_seen
                FROM spam_logs
                WHERE DATE(timestamp) >= ? {platform_filter}
                GROUP BY author_id, platform
                ORDER BY spam_count DESC
                LIMIT ?
            ''', params)
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'author_id': row['author_id'],
                    'author_name': row['author_name'],
                    'platform': row['platform'],
                    'spam_count': row['spam_count'],
                    'avg_confidence': round(row['avg_confidence'], 1),
                    'first_seen': row['first_seen'],
                    'last_seen': row['last_seen']
                })
            
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"Error getting top spammers: {e}")
            return []
    
    def get_top_keywords(
        self,
        platform: Optional[str] = None,
        limit: int = 20,
        days: int = 30
    ) -> List[Tuple[str, int]]:
        """
        Get most frequently detected keywords.
        
        Args:
            platform: Platform filter
            limit: Number of results
            days: Period in days
            
        Returns:
            List of (keyword, count) tuples
        """
        try:
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            start_date = datetime.now().date() - timedelta(days=days)
            
            platform_filter = ""
            params = [start_date]
            
            if platform:
                platform_filter = "AND platform = ?"
                params.append(platform)
            
            cursor.execute(f'''
                SELECT detected_keywords
                FROM spam_logs
                WHERE DATE(timestamp) >= ? {platform_filter}
                AND detected_keywords IS NOT NULL
            ''', params)
            
            # Count keywords
            keyword_counter = Counter()
            
            for row in cursor.fetchall():
                keywords = row['detected_keywords'].split(',')
                for keyword in keywords:
                    keyword = keyword.strip()
                    if keyword:
                        keyword_counter[keyword] += 1
            
            conn.close()
            
            return keyword_counter.most_common(limit)
            
        except Exception as e:
            logger.error(f"Error getting top keywords: {e}")
            return []
    
    def get_top_patterns(
        self,
        platform: Optional[str] = None,
        limit: int = 10,
        days: int = 30
    ) -> List[Tuple[str, int]]:
        """
        Get most frequently detected patterns.
        
        Args:
            platform: Platform filter
            limit: Number of results
            days: Period in days
            
        Returns:
            List of (pattern, count) tuples
        """
        try:
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            start_date = datetime.now().date() - timedelta(days=days)
            
            platform_filter = ""
            params = [start_date]
            
            if platform:
                platform_filter = "AND platform = ?"
                params.append(platform)
            
            cursor.execute(f'''
                SELECT detected_patterns
                FROM spam_logs
                WHERE DATE(timestamp) >= ? {platform_filter}
                AND detected_patterns IS NOT NULL
            ''', params)
            
            # Count patterns
            pattern_counter = Counter()
            
            for row in cursor.fetchall():
                patterns = row['detected_patterns'].split(',')
                for pattern in patterns:
                    pattern = pattern.strip()
                    if pattern:
                        pattern_counter[pattern] += 1
            
            conn.close()
            
            return pattern_counter.most_common(limit)
            
        except Exception as e:
            logger.error(f"Error getting top patterns: {e}")
            return []
    
    # ========================================================================
    # PLATFORM COMPARISON
    # ========================================================================
    
    def compare_platforms(self, days: int = 30) -> Dict:
        """
        Compare performance across platforms.
        
        Args:
            days: Period in days
            
        Returns:
            Dict: Comparison data
        """
        platforms = ['youtube', 'instagram', 'tiktok']
        comparison = {}
        
        for platform in platforms:
            stats = self.database.get_stats(platform=platform, days=days)
            
            if stats['total_comments'] > 0:
                spam_rate = (stats['spam_detected'] / stats['total_comments']) * 100
                success_rate = (stats['spam_deleted'] / stats['spam_detected'] * 100) if stats['spam_detected'] > 0 else 0
            else:
                spam_rate = 0
                success_rate = 0
            
            comparison[platform] = {
                **stats,
                'spam_rate': round(spam_rate, 2),
                'success_rate': round(success_rate, 2)
            }
        
        return comparison
    
    # ========================================================================
    # REPORTS
    # ========================================================================
    
    def generate_daily_report(self, date: Optional[str] = None) -> Dict:
        """
        Generate comprehensive daily report.
        
        Args:
            date: Date string (YYYY-MM-DD), None = today
            
        Returns:
            Dict: Daily report
        """
        if date is None:
            date = datetime.now().date()
        else:
            date = datetime.strptime(date, '%Y-%m-%d').date()
        
        report = {
            'date': str(date),
            'generated_at': datetime.now().isoformat(),
            'platforms': {}
        }
        
        # Per-platform stats
        for platform in ['youtube', 'instagram']:
            stats = self.database.get_stats(platform=platform, days=1)
            
            if stats['total_comments'] > 0:
                report['platforms'][platform] = {
                    'total_comments': stats['total_comments'],
                    'spam_detected': stats['spam_detected'],
                    'spam_deleted': stats['spam_deleted'],
                    'spam_rate': round((stats['spam_detected'] / stats['total_comments']) * 100, 2),
                    'unique_spammers': stats['unique_spammers'],
                    'affected_contents': stats['affected_contents']
                }
        
        # Top spammers
        report['top_spammers'] = self.get_top_spammers(limit=10, days=1)
        
        # Top keywords
        report['top_keywords'] = dict(self.get_top_keywords(limit=10, days=1))
        
        return report
    
    def generate_weekly_report(self) -> Dict:
        """
        Generate comprehensive weekly report.
        
        Returns:
            Dict: Weekly report
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
        
        report = {
            'period': f"{start_date} to {end_date}",
            'generated_at': datetime.now().isoformat(),
            'summary': {},
            'platforms': {},
            'trends': {},
            'top_lists': {}
        }
        
        # Overall summary
        total_stats = self.database.get_stats(days=7)
        report['summary'] = total_stats
        
        # Platform comparison
        report['platforms'] = self.compare_platforms(days=7)
        
        # Trends
        report['trends'] = {
            'spam_trend': self.get_spam_trend(days=7),
            'hourly_pattern': self.get_hourly_pattern(days=7)
        }
        
        # Top lists
        report['top_lists'] = {
            'spammers': self.get_top_spammers(limit=20, days=7),
            'keywords': dict(self.get_top_keywords(limit=20, days=7)),
            'patterns': dict(self.get_top_patterns(limit=10, days=7))
        }
        
        return report
    
    # ========================================================================
    # EXPORT
    # ========================================================================
    
    def export_report_json(self, report: Dict, filename: str) -> bool:
        """
        Export report to JSON file.
        
        Args:
            report: Report dict
            filename: Output filename
            
        Returns:
            bool: True if successful
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Report exported to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting report: {e}")
            return False
    
    def export_report_text(self, report: Dict, filename: str) -> bool:
        """
        Export report to readable text file.
        
        Args:
            report: Report dict
            filename: Output filename
            
        Returns:
            bool: True if successful
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=" * 70 + "\n")
                f.write("SPAM MODERATION REPORT\n")
                f.write("=" * 70 + "\n\n")
                
                if 'date' in report:
                    f.write(f"Date: {report['date']}\n")
                elif 'period' in report:
                    f.write(f"Period: {report['period']}\n")
                
                f.write(f"Generated: {report['generated_at']}\n")
                f.write("\n" + "=" * 70 + "\n\n")
                
                # Summary
                if 'summary' in report:
                    f.write("SUMMARY\n")
                    f.write("-" * 70 + "\n")
                    for key, value in report['summary'].items():
                        f.write(f"{key}: {value}\n")
                    f.write("\n")
                
                # Platforms
                if 'platforms' in report:
                    f.write("PLATFORMS\n")
                    f.write("-" * 70 + "\n")
                    for platform, data in report['platforms'].items():
                        f.write(f"\n{platform.upper()}:\n")
                        for key, value in data.items():
                            f.write(f"  {key}: {value}\n")
                    f.write("\n")
                
                # Top spammers
                if 'top_spammers' in report:
                    f.write("TOP SPAMMERS\n")
                    f.write("-" * 70 + "\n")
                    for i, spammer in enumerate(report['top_spammers'][:10], 1):
                        f.write(f"{i}. {spammer['author_name']} ({spammer['platform']}): {spammer['spam_count']} spam\n")
                    f.write("\n")
                
                # Top keywords
                if 'top_keywords' in report:
                    f.write("TOP KEYWORDS\n")
                    f.write("-" * 70 + "\n")
                    for i, (keyword, count) in enumerate(list(report['top_keywords'].items())[:10], 1):
                        f.write(f"{i}. {keyword}: {count}\n")
                    f.write("\n")
                
                f.write("=" * 70 + "\n")
            
            logger.info(f"Report exported to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting report: {e}")
            return False


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """CLI interface for analytics."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Spam Moderation Analytics')
    parser.add_argument('--daily', action='store_true', help='Generate daily report')
    parser.add_argument('--weekly', action='store_true', help='Generate weekly report')
    parser.add_argument('--output', default='report', help='Output filename (without extension)')
    parser.add_argument('--format', choices=['json', 'text', 'both'], default='both', help='Output format')
    
    args = parser.parse_args()
    
    # Initialize
    db = DatabaseManager()
    analytics = AnalyticsEngine(db)
    
    # Generate report
    if args.daily:
        report = analytics.generate_daily_report()
        report_type = 'daily'
    elif args.weekly:
        report = analytics.generate_weekly_report()
        report_type = 'weekly'
    else:
        print("Please specify --daily or --weekly")
        return
    
    # Export
    if args.format in ['json', 'both']:
        filename = f"{args.output}_{report_type}.json"
        analytics.export_report_json(report, filename)
        print(f"✅ JSON report saved: {filename}")
    
    if args.format in ['text', 'both']:
        filename = f"{args.output}_{report_type}.txt"
        analytics.export_report_text(report, filename)
        print(f"✅ Text report saved: {filename}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
