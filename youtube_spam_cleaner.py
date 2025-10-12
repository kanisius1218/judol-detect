"""
YouTube Spam Comment Auto-Deletion System
Automatically detects and removes spam/judol comments from YouTube channel
"""

import os
import json
import time
import pickle
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
import googleapiclient.discovery
import googleapiclient.errors
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import pandas as pd
import joblib
from pathlib import Path

class YouTubeSpamCleaner:
    """YouTube API integration for spam comment management"""
    
    def __init__(self, credentials_file: str = "client_secret.json"):
        self.credentials_file = credentials_file
        self.youtube = None
        self.model = None
        self.vectorizer = None
        self.scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
        
        # Initialize API
        self.authenticate()
        
        # Load spam detection model
        self.load_model()
        
    def authenticate(self):
        """Authenticate with YouTube API"""
        creds = None
        token_file = "token.pickle"
        
        # Load existing token
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.scopes)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        # Build YouTube API client
        self.youtube = googleapiclient.discovery.build(
            "youtube", "v3", credentials=creds)
        
        print("✓ YouTube API authenticated successfully")
    
    def load_model(self):
        """Load the spam detection model"""
        try:
            model_path = Path("ml_models/advanced_spam_detector_ensemble_latest.joblib")
            vectorizer_path = Path("ml_models/advanced_spam_detector_vectorizers_latest.joblib")
            
            if model_path.exists() and vectorizer_path.exists():
                self.model = joblib.load(model_path)
                self.vectorizer = joblib.load(vectorizer_path)
                print("✓ Spam detection model loaded")
            else:
                print("⚠ Model not found, using keyword-based detection")
        except Exception as e:
            print(f"⚠ Error loading model: {e}")
    
    def get_channel_id(self) -> str:
        """Get authenticated user's channel ID"""
        try:
            request = self.youtube.channels().list(
                part="id",
                mine=True
            )
            response = request.execute()
            
            if response['items']:
                return response['items'][0]['id']
            return None
        except Exception as e:
            print(f"Error getting channel ID: {e}")
            return None
    
    def get_recent_videos(self, max_results: int = 10) -> List[Dict]:
        """Get recent videos from channel"""
        channel_id = self.get_channel_id()
        if not channel_id:
            return []
        
        try:
            request = self.youtube.search().list(
                part="id,snippet",
                channelId=channel_id,
                maxResults=max_results,
                order="date",
                type="video"
            )
            response = request.execute()
            
            videos = []
            for item in response['items']:
                videos.append({
                    'video_id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'published_at': item['snippet']['publishedAt']
                })
            
            return videos
        except Exception as e:
            print(f"Error getting videos: {e}")
            return []
    
    def get_video_comments(self, video_id: str, max_results: int = 100) -> List[Dict]:
        """Get comments from a video"""
        comments = []
        
        try:
            request = self.youtube.commentThreads().list(
                part="snippet,replies",
                videoId=video_id,
                maxResults=max_results,
                textFormat="plainText"
            )
            
            while request:
                response = request.execute()
                
                for item in response['items']:
                    comment = item['snippet']['topLevelComment']['snippet']
                    comments.append({
                        'comment_id': item['id'],
                        'video_id': video_id,
                        'author': comment['authorDisplayName'],
                        'text': comment['textDisplay'],
                        'published_at': comment['publishedAt'],
                        'like_count': comment['likeCount']
                    })
                    
                    # Get replies if any
                    if 'replies' in item:
                        for reply in item['replies']['comments']:
                            reply_snippet = reply['snippet']
                            comments.append({
                                'comment_id': reply['id'],
                                'video_id': video_id,
                                'author': reply_snippet['authorDisplayName'],
                                'text': reply_snippet['textDisplay'],
                                'published_at': reply_snippet['publishedAt'],
                                'like_count': reply_snippet['likeCount'],
                                'is_reply': True
                            })
                
                # Get next page
                request = self.youtube.commentThreads().list_next(request, response) if 'nextPageToken' in response else None
            
            return comments
        except Exception as e:
            print(f"Error getting comments for video {video_id}: {e}")
            return []
    
    def is_spam_comment(self, text: str) -> Tuple[bool, float]:
        """Check if comment is spam using model or keywords"""
        
        # Use model if available
        if self.model and self.vectorizer:
            try:
                if isinstance(self.vectorizer, dict) and 'feature_union' in self.vectorizer:
                    features = self.vectorizer['feature_union'].transform([text])
                else:
                    features = self.vectorizer.transform([text])
                
                prediction = self.model.predict(features)[0]
                probability = self.model.predict_proba(features)[0]
                
                return bool(prediction == 1), float(probability[1])
            except:
                pass
        
        # Fallback to keyword detection
        text_lower = text.lower()
        
        # Spam keywords for Indonesian judol/gambling
        spam_keywords = [
            # Gambling
            'slot', 'togel', 'poker', 'casino', 'jackpot', 'maxwin', 'gacor',
            'scatter', 'bonus', 'deposit', 'withdraw', 'wd', 'jp', 'jepe',
            'bandar', 'agen', 'situs', 'daftar', 'register', 'promo',
            # Adult content
            'bokep', 'porn', 'sex', 'nude', 'hot', 'sexy', 'panas', 'bugil',
            # Scams
            'cuan', 'profit', 'income', 'investasi', 'trading', 'forex',
            # Links
            'wa.me', 'bit.ly', 't.me', 'telegram', 'whatsapp',
            'klik link', 'join grup', 'hub admin'
        ]
        
        # Count keyword matches
        keyword_count = sum(1 for keyword in spam_keywords if keyword in text_lower)
        
        # Calculate spam score
        spam_score = min(keyword_count * 0.3, 1.0)
        
        # Check for suspicious patterns
        if any(pattern in text_lower for pattern in ['http://', 'https://', 'www.', '.com', '.net']):
            spam_score += 0.3
        
        if len(text) < 10 or text.count(' ') < 2:  # Very short or no spaces
            spam_score += 0.2
        
        if text.isupper():  # All caps
            spam_score += 0.1
        
        return spam_score > 0.5, spam_score
    
    def delete_comment(self, comment_id: str) -> bool:
        """Delete a comment by ID"""
        try:
            request = self.youtube.comments().delete(id=comment_id)
            request.execute()
            return True
        except Exception as e:
            print(f"Error deleting comment {comment_id}: {e}")
            return False
    
    def moderate_comment(self, comment_id: str) -> bool:
        """Mark comment as spam (held for review)"""
        try:
            request = self.youtube.comments().markAsSpam(id=comment_id)
            request.execute()
            return True
        except Exception as e:
            print(f"Error moderating comment {comment_id}: {e}")
            return False
    
    def clean_video_comments(self, video_id: str, auto_delete: bool = False, 
                           threshold: float = 0.7) -> Dict:
        """Clean spam comments from a video"""
        print(f"\n🔍 Scanning video: {video_id}")
        
        comments = self.get_video_comments(video_id)
        print(f"Found {len(comments)} comments")
        
        results = {
            'total_comments': len(comments),
            'spam_detected': 0,
            'deleted': 0,
            'moderated': 0,
            'spam_comments': []
        }
        
        for comment in comments:
            is_spam, confidence = self.is_spam_comment(comment['text'])
            
            if is_spam and confidence >= threshold:
                results['spam_detected'] += 1
                
                spam_info = {
                    'author': comment['author'],
                    'text': comment['text'][:100] + '...' if len(comment['text']) > 100 else comment['text'],
                    'confidence': confidence,
                    'action': None
                }
                
                if auto_delete:
                    # Delete if very high confidence
                    if confidence >= 0.9:
                        if self.delete_comment(comment['comment_id']):
                            results['deleted'] += 1
                            spam_info['action'] = 'deleted'
                            print(f"  ❌ Deleted spam from {comment['author']}: {spam_info['text']}")
                    # Moderate if medium-high confidence
                    elif confidence >= threshold:
                        if self.moderate_comment(comment['comment_id']):
                            results['moderated'] += 1
                            spam_info['action'] = 'moderated'
                            print(f"  ⚠️ Moderated spam from {comment['author']}: {spam_info['text']}")
                else:
                    print(f"  🚨 Spam detected from {comment['author']} (confidence: {confidence:.2f})")
                
                results['spam_comments'].append(spam_info)
        
        return results
    
    def clean_channel(self, auto_delete: bool = False, max_videos: int = 10) -> Dict:
        """Clean spam from entire channel"""
        print("\n🧹 Starting channel cleanup...")
        
        videos = self.get_recent_videos(max_videos)
        print(f"Processing {len(videos)} recent videos")
        
        channel_results = {
            'videos_processed': len(videos),
            'total_comments': 0,
            'total_spam': 0,
            'total_deleted': 0,
            'total_moderated': 0,
            'video_results': []
        }
        
        for video in videos:
            print(f"\n📹 Processing: {video['title']}")
            
            video_results = self.clean_video_comments(
                video['video_id'], 
                auto_delete=auto_delete
            )
            
            video_results['video_title'] = video['title']
            channel_results['video_results'].append(video_results)
            
            # Update totals
            channel_results['total_comments'] += video_results['total_comments']
            channel_results['total_spam'] += video_results['spam_detected']
            channel_results['total_deleted'] += video_results['deleted']
            channel_results['total_moderated'] += video_results['moderated']
            
            # Rate limiting
            time.sleep(1)
        
        return channel_results
    
    def generate_report(self, results: Dict) -> str:
        """Generate cleanup report"""
        report = []
        report.append("\n" + "="*50)
        report.append("📊 YOUTUBE SPAM CLEANUP REPORT")
        report.append("="*50)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        report.append("📈 SUMMARY:")
        report.append(f"  • Videos processed: {results['videos_processed']}")
        report.append(f"  • Total comments: {results['total_comments']}")
        report.append(f"  • Spam detected: {results['total_spam']}")
        report.append(f"  • Comments deleted: {results['total_deleted']}")
        report.append(f"  • Comments moderated: {results['total_moderated']}")
        
        if results['total_comments'] > 0:
            spam_rate = (results['total_spam'] / results['total_comments']) * 100
            report.append(f"  • Spam rate: {spam_rate:.1f}%")
        
        report.append("")
        report.append("📹 VIDEO DETAILS:")
        
        for video_result in results['video_results']:
            report.append(f"\n  {video_result['video_title']}")
            report.append(f"    Comments: {video_result['total_comments']}")
            report.append(f"    Spam: {video_result['spam_detected']}")
            
            if video_result['spam_comments']:
                report.append("    Top spam comments:")
                for spam in video_result['spam_comments'][:3]:
                    report.append(f"      - {spam['author']}: {spam['text'][:50]}...")
        
        report.append("\n" + "="*50)
        
        return "\n".join(report)
    
    def schedule_cleanup(self, interval_hours: int = 24, auto_delete: bool = False):
        """Schedule automatic cleanup"""
        print(f"⏰ Scheduled cleanup every {interval_hours} hours")
        print("Press Ctrl+C to stop")
        
        while True:
            try:
                # Run cleanup
                results = self.clean_channel(auto_delete=auto_delete)
                
                # Generate and print report
                report = self.generate_report(results)
                print(report)
                
                # Save report
                report_file = f"reports/youtube_cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                os.makedirs("reports", exist_ok=True)
                with open(report_file, 'w', encoding='utf-8') as f:
                    f.write(report)
                
                print(f"\n💾 Report saved to {report_file}")
                print(f"\n😴 Sleeping for {interval_hours} hours...")
                
                # Sleep
                time.sleep(interval_hours * 3600)
                
            except KeyboardInterrupt:
                print("\n👋 Cleanup scheduler stopped")
                break
            except Exception as e:
                print(f"\n❌ Error during cleanup: {e}")
                print(f"Retrying in {interval_hours} hours...")
                time.sleep(interval_hours * 3600)


def main():
    """Main function with CLI interface"""
    print("\n🎯 YouTube Spam Comment Cleaner")
    print("================================")
    
    # Initialize cleaner
    cleaner = YouTubeSpamCleaner()
    
    while True:
        print("\n📋 Options:")
        print("1. Scan channel for spam (no deletion)")
        print("2. Clean channel (auto-delete spam)")
        print("3. Schedule automatic cleanup")
        print("4. Clean specific video")
        print("5. Exit")
        
        choice = input("\nSelect option (1-5): ")
        
        if choice == '1':
            results = cleaner.clean_channel(auto_delete=False)
            report = cleaner.generate_report(results)
            print(report)
            
        elif choice == '2':
            confirm = input("⚠️  This will DELETE spam comments. Continue? (y/n): ")
            if confirm.lower() == 'y':
                results = cleaner.clean_channel(auto_delete=True)
                report = cleaner.generate_report(results)
                print(report)
            
        elif choice == '3':
            hours = int(input("Enter cleanup interval (hours): "))
            auto_delete = input("Enable auto-deletion? (y/n): ").lower() == 'y'
            cleaner.schedule_cleanup(hours, auto_delete)
            
        elif choice == '4':
            video_id = input("Enter video ID: ")
            auto_delete = input("Enable auto-deletion? (y/n): ").lower() == 'y'
            results = cleaner.clean_video_comments(video_id, auto_delete)
            print(f"\n✅ Processed {results['total_comments']} comments")
            print(f"   Spam detected: {results['spam_detected']}")
            
        elif choice == '5':
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid option")


if __name__ == "__main__":
    main()
