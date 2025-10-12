#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-Platform Spam Moderator - Main Orchestrator
Unified bot runner dengan scheduling dan monitoring
"""

import os
import sys
import logging
import schedule
import time
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

from .core_detector import SpamDetector
from .database import DatabaseManager
from .youtube_adapter import YouTubeAdapter
from .instagram_adapter import InstagramAdapter

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/spam_moderator.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class SpamModeratorBot:
    """
    Main orchestrator untuk multi-platform spam moderation.
    
    Features:
    - Unified interface untuk semua platforms
    - Scheduled checking
    - Statistics tracking
    - Error handling dan recovery
    - Configuration management
    """
    
    def __init__(self, config_file: str = '.env'):
        """
        Initialize bot dengan configuration.
        
        Args:
            config_file: Path ke .env file
        """
        logger.info("=" * 70)
        logger.info("MULTI-PLATFORM SPAM MODERATOR")
        logger.info("=" * 70)

        # Setup Jinja2
        self.jinja_env = Environment(loader=FileSystemLoader('templates'))
        
        # Load configuration
        load_dotenv(config_file)
        self.config = self._load_config()
        
        # Initialize core components
        self.detector = SpamDetector(
            confidence_threshold=self.config['confidence_threshold']
        )
        self.database = DatabaseManager(
            db_file=self.config['database_file']
        )
        
        # Initialize platform adapters
        self.adapters = {}
        self._init_adapters()
        
        # Statistics
        self.run_count = 0
        self.last_run = None
        
        logger.info("Bot initialized successfully")
        logger.info(f"Enabled platforms: {list(self.adapters.keys())}")
        logger.info(f"Confidence threshold: {self.config['confidence_threshold']}%")
        logger.info(f"Dry run mode: {self.config['dry_run']}")
        logger.info("=" * 70)
    
    def _load_config(self) -> Dict:
        """
        Load configuration dari environment variables.
        
        Returns:
            Dict: Configuration
        """
        config = {
            # General
            'confidence_threshold': int(os.getenv('CONFIDENCE_THRESHOLD', '40')),
            'dry_run': os.getenv('DRY_RUN', 'false').lower() == 'true',
            'check_interval': int(os.getenv('CHECK_INTERVAL_MINUTES', '5')),
            'database_file': os.getenv('DATABASE_FILE', 'spam_moderator.db'),
            
            # YouTube
            'youtube_enabled': os.getenv('YOUTUBE_ENABLED', 'false').lower() == 'true',
            'youtube_client_secret_file': os.getenv('YOUTUBE_CLIENT_SECRET_FILE', 'client_secret.json'),
            
            # Instagram
            'instagram_enabled': os.getenv('INSTAGRAM_ENABLED', 'false').lower() == 'true',
            'instagram_access_token': os.getenv('INSTAGRAM_ACCESS_TOKEN'),
            'instagram_user_id': os.getenv('INSTAGRAM_USER_ID'),
        }
        
        return config
    
    def _init_adapters(self) -> None:
        """Initialize platform adapters berdasarkan configuration."""
        
        # YouTube
        if self.config['youtube_enabled']:
            if self.config['youtube_client_secret_file']:
                try:
                    self.adapters['youtube'] = YouTubeAdapter(
                        client_secret_file=self.config['youtube_client_secret_file'],
                        detector=self.detector,
                        database=self.database
                    )
                    logger.info("YouTube adapter initialized")
                except Exception as e:
                    logger.error(f"Failed to initialize YouTube adapter: {e}")
            else:
                logger.warning("YouTube enabled but client secret file path is missing in .env")
        
        # Instagram
        if self.config['instagram_enabled']:
            if self.config['instagram_access_token'] and self.config['instagram_user_id']:
                try:
                    self.adapters['instagram'] = InstagramAdapter(
                        access_token=self.config['instagram_access_token'],
                        instagram_user_id=self.config['instagram_user_id'],
                        detector=self.detector,
                        database=self.database
                    )
                    logger.info("✅ Instagram adapter initialized")
                except Exception as e:
                    logger.error(f"❌ Failed to initialize Instagram adapter: {e}")
            else:
                logger.warning("⚠️  Instagram enabled but access token/user ID missing")
        
        if not self.adapters:
            logger.warning("⚠️  No platform adapters initialized!")
    
    # ========================================================================
    # MODERATION TASKS
    # ========================================================================
    
    def moderate_youtube(self) -> Dict:
        """
        Run YouTube moderation task.
        
        Returns:
            Dict: Moderation results
        """
        if 'youtube' not in self.adapters:
            return {'status': 'disabled'}
        
        logger.info("🎥 Starting YouTube moderation...")
        
        try:
            adapter = self.adapters['youtube']
            
            # Moderate channel comments
            result = adapter.moderate_channel(
                max_comments=100,
                dry_run=self.config['dry_run']
            )
            
            logger.info(
                f"✅ YouTube moderation completed: "
                f"{result['checked']} checked, {result['spam_found']} spam found"
            )
            
            return {
                'status': 'success',
                'platform': 'youtube',
                **result
            }
            
        except Exception as e:
            logger.error(f"❌ YouTube moderation error: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def moderate_instagram(self) -> Dict:
        """
        Run Instagram moderation task.
        
        Returns:
            Dict: Moderation results
        """
        if 'instagram' not in self.adapters:
            return {'status': 'disabled'}
        
        logger.info("📸 Starting Instagram moderation...")
        
        try:
            adapter = self.adapters['instagram']
            
            # Moderate account comments
            result = adapter.moderate_account(
                max_media=10,
                max_comments_per_media=50,
                dry_run=self.config['dry_run']
            )
            
            logger.info(
                f"✅ Instagram moderation completed: "
                f"{result['comments_checked']} checked, {result['spam_found']} spam found"
            )
            
            return {
                'status': 'success',
                'platform': 'instagram',
                **result
            }
            
        except Exception as e:
            logger.error(f"❌ Instagram moderation error: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def moderate_all(self) -> List[Dict]:
        """
        Run moderation untuk semua enabled platforms.
        
        Returns:
            List[Dict]: Results dari semua platforms
        """
        self.run_count += 1
        self.last_run = datetime.now()
        
        logger.info("=" * 70)
        logger.info(f"MODERATION RUN #{self.run_count}")
        logger.info(f"Time: {self.last_run.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Dry run: {self.config['dry_run']}")
        logger.info("=" * 70)
        
        results = []
        
        # YouTube
        if 'youtube' in self.adapters:
            result = self.moderate_youtube()
            results.append(result)
        
        # Instagram
        if 'instagram' in self.adapters:
            result = self.moderate_instagram()
            results.append(result)
        
        # Summary
        self._print_summary(results)
        
        return results
    
    def _print_summary(self, results: List[Dict]) -> None:
        """Print summary dari moderation run."""
        logger.info("=" * 70)
        logger.info("MODERATION SUMMARY")
        logger.info("=" * 70)
        
        total_checked = 0
        total_spam = 0
        total_deleted = 0
        
        for result in results:
            if result['status'] == 'success':
                platform = result.get('platform', 'unknown')
                checked = result.get('checked', result.get('comments_checked', 0))
                spam = result.get('spam_found', 0)
                deleted = result.get('deleted', 0)
                
                total_checked += checked
                total_spam += spam
                total_deleted += deleted
                
                logger.info(
                    f"  {platform.upper()}: "
                    f"{checked} checked, {spam} spam, {deleted} deleted"
                )
        
        # Generate HTML report
        summary_data = {
            'results': [],
            'total_checked': total_checked,
            'total_spam': total_spam,
            'total_deleted': total_deleted
        }
        for result in results:
            if result['status'] == 'success':
                summary_data['results'].append({
                    'platform': result.get('platform', 'unknown'),
                    'checked': result.get('checked', result.get('comments_checked', 0)),
                    'spam': result.get('spam_found', 0),
                    'deleted': result.get('deleted', 0)
                })
        
        self.generate_html_report(
            template_name='report_template.html',
            title='Moderation Summary',
            data={'summary': summary_data}
        )

    def generate_html_report(self, template_name: str, title: str, data: Dict) -> None:
        """
        Generate an HTML report from a template.

        Args:
            template_name: The name of the template file.
            title: The title of the report.
            data: The data to render in the template.
        """
        try:
            template = self.jinja_env.get_template(template_name)
            
            # Render the template
            output = template.render(
                title=title,
                generated_on=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                **data
            )
            
            # Save the report
            report_path = os.path.join('reports', f"{title.lower().replace(' ', '_')}.html")
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(output)
            
            logger.info(f"HTML report generated: {report_path}")
            
        except Exception as e:
            logger.error(f"Failed to generate HTML report: {e}")
    
    # ========================================================================
    # STATISTICS & MONITORING
    # ========================================================================
    
    def get_statistics(self, days: int = 7) -> Dict:
        """
        Get comprehensive statistics.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dict: Statistics
        """
        # Database stats
        db_stats = self.database.get_platform_stats(days=days)
        
        # Adapter stats
        adapter_stats = {}
        for platform, adapter in self.adapters.items():
            adapter_stats[platform] = adapter.get_stats()
        
        # Bot stats
        bot_stats = {
            'run_count': self.run_count,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'enabled_platforms': list(self.adapters.keys()),
            'dry_run': self.config['dry_run']
        }
        
        return {
            'bot': bot_stats,
            'database': db_stats,
            'adapters': adapter_stats
        }
    
    def print_statistics(self, days: int = 7) -> None:
        """Print formatted statistics."""
        stats = self.get_statistics(days=days)
        
        # Generate HTML report
        self.generate_html_report(
            template_name='report_template.html',
            title=f'Statistics Report ({days} Days)',
            data={'stats': stats, 'days': days}
        )

        print("\n" + "=" * 70)
        print(f"STATISTICS ({days} DAYS)")
        print("=" * 70)
        
        # Bot stats
        print("\n📊 Bot Status:")
        print(f"  Run count: {stats['bot']['run_count']}")
        print(f"  Last run: {stats['bot']['last_run']}")
        print(f"  Enabled platforms: {', '.join(stats['bot']['enabled_platforms'])}")
        print(f"  Dry run mode: {stats['bot']['dry_run']}")
        
        # Database stats
        print("\n💾 Database Stats:")
        for platform, data in stats['database'].items():
            print(f"\n  {platform.upper()}:")
            print(f"    Total comments: {data['total_comments']}")
            print(f"    Spam detected: {data['spam_detected']}")
            print(f"    Spam deleted: {data['spam_deleted']}")
            print(f"    Unique spammers: {data['unique_spammers']}")
            print(f"    Affected contents: {data['affected_contents']}")
        
        # Adapter stats
        print("\n🔧 Adapter Stats:")
        for platform, data in stats['adapters'].items():
            print(f"\n  {platform.upper()}:")
            for key, value in data.items():
                print(f"    {key}: {value}")
        
        print("\n" + "=" * 70)
    
    # ========================================================================
    # SCHEDULING
    # ========================================================================
    
    def schedule_tasks(self) -> None:
        """Setup scheduled tasks."""
        interval = self.config['check_interval']
        
        logger.info(f"⏰ Scheduling moderation every {interval} minutes")
        
        schedule.every(interval).minutes.do(self.moderate_all)
        
        # Daily statistics
        schedule.every().day.at("00:00").do(
            lambda: self.print_statistics(days=1)
        )
    
    def run_scheduled(self) -> None:
        """
        Run bot dengan scheduled tasks.
        
        This will run indefinitely until interrupted.
        """
        logger.info("🚀 Starting scheduled moderation...")
        logger.info(f"⏰ Check interval: {self.config['check_interval']} minutes")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 70)
        
        # Setup schedule
        self.schedule_tasks()
        
        # Run first moderation immediately
        self.moderate_all()
        
        # Run scheduled tasks
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("\n👋 Bot stopped by user")
            self.print_statistics()
    
    def run_once(self) -> None:
        """Run moderation once and exit."""
        logger.info("🚀 Running one-time moderation...")
        self.moderate_all()
        self.print_statistics()
    
    # ========================================================================
    # CLI INTERFACE
    # ========================================================================
    
    def interactive_menu(self) -> None:
        """Interactive CLI menu."""
        while True:
            print("\n" + "=" * 70)
            print("MULTI-PLATFORM SPAM MODERATOR - MENU")
            print("=" * 70)
            print("\n1. Run moderation once")
            print("2. Run scheduled moderation")
            print("3. View statistics")
            print("4. Test detection")
            print("5. Configuration")
            print("6. Exit")
            print()
            
            choice = input("Select option (1-6): ").strip()
            
            if choice == '1':
                self.run_once()
            elif choice == '2':
                self.run_scheduled()
            elif choice == '3':
                days = input("Days to look back (default 7): ").strip()
                days = int(days) if days.isdigit() else 7
                self.print_statistics(days=days)
            elif choice == '4':
                self._test_detection_interactive()
            elif choice == '5':
                self._show_configuration()
            elif choice == '6':
                print("\n👋 Goodbye!")
                break
            else:
                print("\n❌ Invalid option")
    
    def _test_detection_interactive(self) -> None:
        """Interactive detection testing."""
        print("\n" + "=" * 70)
        print("TEST DETECTION")
        print("=" * 70)
        print("Enter text to test (or 'back' to return):")
        
        while True:
            text = input("\n> ").strip()
            
            if text.lower() == 'back':
                break
            
            if not text:
                continue
            
            result = self.detector.detect(text)
            
            print(f"\n{'🚨 SPAM' if result.is_spam else '✅ NOT SPAM'}")
            print(f"Confidence: {result.confidence}%")
            print(f"Keywords: {result.detected_keywords}")
            print(f"Patterns: {result.detected_patterns}")
            print(f"Reason: {result.reason}")
    
    def _show_configuration(self) -> None:
        """Show current configuration."""
        print("\n" + "=" * 70)
        print("CONFIGURATION")
        print("=" * 70)
        
        print(f"\nConfidence threshold: {self.config['confidence_threshold']}%")
        print(f"Dry run mode: {self.config['dry_run']}")
        print(f"Check interval: {self.config['check_interval']} minutes")
        print(f"Database file: {self.config['database_file']}")
        
        print(f"\nYouTube: {'✅ Enabled' if self.config['youtube_enabled'] else '❌ Disabled'}")
        if self.config['youtube_enabled']:
            print(f"  API key: {'✅ Set' if self.config['youtube_api_key'] else '❌ Not set'}")
            print(f"  Channel ID: {'✅ Set' if self.config['youtube_channel_id'] else '❌ Not set'}")
        
        print(f"\nInstagram: {'✅ Enabled' if self.config['instagram_enabled'] else '❌ Disabled'}")
        if self.config['instagram_enabled']:
            print(f"  Access token: {'✅ Set' if self.config['instagram_access_token'] else '❌ Not set'}")
            print(f"  User ID: {'✅ Set' if self.config['instagram_user_id'] else '❌ Not set'}")
        
        print("\n" + "=" * 70)


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Multi-Platform Spam Moderator'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run moderation once and exit'
    )
    parser.add_argument(
        '--scheduled',
        action='store_true',
        help='Run scheduled moderation'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show statistics and exit'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Days for statistics (default: 7)'
    )
    parser.add_argument(
        '--config',
        default='.env',
        help='Path to config file (default: .env)'
    )
    
    args = parser.parse_args()
    
    # Initialize bot
    try:
        bot = SpamModeratorBot(config_file=args.config)
    except Exception as e:
        logger.error(f"Failed to initialize bot: {e}")
        sys.exit(1)
    
    # Run based on arguments
    if args.once:
        bot.run_once()
    elif args.scheduled:
        bot.run_scheduled()
    elif args.stats:
        bot.print_statistics(days=args.days)
    else:
        # Interactive menu
        bot.interactive_menu()


if __name__ == "__main__":
    main()
