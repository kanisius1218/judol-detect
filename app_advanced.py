"""
Advanced Message Detection System with Google Auth and Social Media Analysis
"""

import os
import json
import re
import hashlib
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from functools import wraps
import sqlite3
import requests
from urllib.parse import urlparse, parse_qs

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from authlib.integrations.flask_client import OAuth
import joblib
import numpy as np

# Configure Flask
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Enable CORS
CORS(app)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Configure OAuth
oauth = OAuth(app)

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', 'your-client-id')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', 'your-client-secret')

google = oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# Database setup
def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect('detection_system.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  google_id TEXT UNIQUE,
                  email TEXT UNIQUE,
                  name TEXT,
                  picture TEXT,
                  created_at TIMESTAMP,
                  is_admin BOOLEAN DEFAULT 0)''')
    
    # Detection history table
    c.execute('''CREATE TABLE IF NOT EXISTS detections
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  text TEXT,
                  category TEXT,
                  confidence REAL,
                  source TEXT,
                  timestamp TIMESTAMP,
                  deleted BOOLEAN DEFAULT 0,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    # Social media analysis table
    c.execute('''CREATE TABLE IF NOT EXISTS social_media_analysis
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  platform TEXT,
                  url TEXT,
                  total_comments INTEGER,
                  spam_comments INTEGER,
                  judi_comments INTEGER,
                  analysis_date TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    # Spam accounts research table
    c.execute('''CREATE TABLE IF NOT EXISTS spam_accounts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  platform TEXT,
                  username TEXT,
                  spam_count INTEGER,
                  judi_count INTEGER,
                  first_seen TIMESTAMP,
                  last_seen TIMESTAMP,
                  patterns TEXT,
                  risk_score REAL)''')
    
    # Categories table
    c.execute('''CREATE TABLE IF NOT EXISTS categories
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT UNIQUE,
                  keywords TEXT,
                  patterns TEXT,
                  created_at TIMESTAMP)''')
    
    # Insert default categories
    categories = [
        ('spam', 'promo,discount,click here,limited offer', '(http|https)://[^\s]+'),
        ('not_spam', 'thank you,regards,sincerely', None),
        ('judi_online', 'slot,togel,casino,jackpot,maxwin,gacor,scatter,bonus,deposit,withdraw', 'slot\s*\d+|togel\s*\d+|maxwin')
    ]
    
    for cat in categories:
        c.execute("INSERT OR IGNORE INTO categories (name, keywords, patterns, created_at) VALUES (?, ?, ?, ?)",
                  (cat[0], cat[1], cat[2], datetime.now()))
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

class User(UserMixin):
    def __init__(self, user_id, email, name, picture, is_admin=False):
        self.id = user_id
        self.email = email
        self.name = name
        self.picture = picture
        self.is_admin = is_admin

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('detection_system.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user_data = c.fetchone()
    conn.close()
    
    if user_data:
        return User(user_data[0], user_data[2], user_data[3], user_data[4], user_data[5])
    return None

class AdvancedDetector:
    def __init__(self):
        self.model = None
        self.vectorizer = None
        self.categories = self.load_categories()
        self.load_model()
    
    def load_categories(self):
        """Load categories from database"""
        conn = sqlite3.connect('detection_system.db')
        c = conn.cursor()
        c.execute("SELECT name, keywords, patterns FROM categories")
        categories = {}
        for row in c.fetchall():
            categories[row[0]] = {
                'keywords': row[1].split(',') if row[1] else [],
                'patterns': row[2]
            }
        conn.close()
        return categories
    
    def load_model(self):
        """Load ML model"""
        try:
            base_dir = Path(__file__).parent
            model_dir = base_dir / "ml_models"
            
            ensemble_path = model_dir / "advanced_spam_detector_ensemble_latest.joblib"
            vectorizer_path = model_dir / "advanced_spam_detector_vectorizers_latest.joblib"
            
            if ensemble_path.exists() and vectorizer_path.exists():
                self.model = joblib.load(ensemble_path)
                self.vectorizer = joblib.load(vectorizer_path)
            else:
                # Fallback to basic model
                basic_model_path = model_dir / "spam_detector_latest.joblib"
                basic_vectorizer_path = model_dir / "spam_detector_vectorizer_latest.joblib"
                
                if basic_model_path.exists() and basic_vectorizer_path.exists():
                    self.model = joblib.load(basic_model_path)
                    self.vectorizer = joblib.load(basic_vectorizer_path)
        except Exception as e:
            print(f"Error loading model: {e}")
    
    def detect_category(self, text):
        """Detect message category with enhanced classification"""
        text_lower = text.lower()
        
        # Check for judi online patterns
        judi_keywords = self.categories.get('judi_online', {}).get('keywords', [])
        judi_pattern = self.categories.get('judi_online', {}).get('patterns', '')
        
        judi_score = sum(1 for keyword in judi_keywords if keyword in text_lower)
        if judi_pattern and re.search(judi_pattern, text_lower):
            judi_score += 2
        
        if judi_score >= 2:
            return {
                'category': 'judi_online',
                'confidence': min(0.95, 0.7 + judi_score * 0.05),
                'characteristics': self.extract_characteristics(text, 'judi_online')
            }
        
        # Use ML model for spam detection
        if self.model and self.vectorizer:
            try:
                if isinstance(self.vectorizer, dict) and 'feature_union' in self.vectorizer:
                    features = self.vectorizer['feature_union'].transform([text])
                else:
                    features = self.vectorizer.transform([text])
                
                prediction = self.model.predict(features)[0]
                probability = self.model.predict_proba(features)[0] if hasattr(self.model, 'predict_proba') else [0.5, 0.5]
                
                category = 'spam' if prediction == 1 else 'not_spam'
                return {
                    'category': category,
                    'confidence': float(probability[1] if category == 'spam' else probability[0]),
                    'characteristics': self.extract_characteristics(text, category)
                }
            except:
                pass
        
        # Fallback to keyword-based detection
        spam_keywords = self.categories.get('spam', {}).get('keywords', [])
        spam_score = sum(1 for keyword in spam_keywords if keyword in text_lower)
        
        if spam_score >= 2:
            return {
                'category': 'spam',
                'confidence': min(0.85, 0.6 + spam_score * 0.05),
                'characteristics': self.extract_characteristics(text, 'spam')
            }
        
        return {
            'category': 'not_spam',
            'confidence': 0.75,
            'characteristics': self.extract_characteristics(text, 'not_spam')
        }
    
    def extract_characteristics(self, text, category):
        """Extract characteristics of the message"""
        chars = {
            'length': len(text),
            'word_count': len(text.split()),
            'url_count': len(re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)),
            'number_count': len(re.findall(r'\d+', text)),
            'uppercase_ratio': sum(1 for c in text if c.isupper()) / max(len(text), 1),
            'special_chars': sum(1 for c in text if not c.isalnum() and not c.isspace()) / max(len(text), 1),
            'category_keywords': []
        }
        
        # Find matching keywords
        if category in self.categories:
            keywords = self.categories[category].get('keywords', [])
            chars['category_keywords'] = [kw for kw in keywords if kw in text.lower()]
        
        return chars

class SocialMediaAnalyzer:
    """Analyze comments from social media platforms"""
    
    def __init__(self, detector):
        self.detector = detector
        self.platforms = {
            'instagram': self.analyze_instagram,
            'twitter': self.analyze_twitter,
            'youtube': self.analyze_youtube,
            'tiktok': self.analyze_tiktok
        }
    
    def extract_platform(self, url):
        """Extract platform from URL"""
        domain = urlparse(url).netloc.lower()
        
        if 'instagram.com' in domain or 'instagr.am' in domain:
            return 'instagram'
        elif 'twitter.com' in domain or 'x.com' in domain:
            return 'twitter'
        elif 'youtube.com' in domain or 'youtu.be' in domain:
            return 'youtube'
        elif 'tiktok.com' in domain:
            return 'tiktok'
        return None
    
    def analyze_url(self, url, user_id=None):
        """Analyze comments from social media URL"""
        platform = self.extract_platform(url)
        
        if not platform:
            return {'error': 'Unsupported platform'}
        
        # Call platform-specific analyzer
        analyzer = self.platforms.get(platform)
        if analyzer:
            results = analyzer(url)
            
            # Save to database if user is logged in
            if user_id:
                self.save_analysis(user_id, platform, url, results)
            
            return results
        
        return {'error': 'Platform analyzer not implemented'}
    
    def analyze_instagram(self, url):
        """Analyze Instagram post comments"""
        # This would require Instagram API access
        # For demo, return mock data
        return self.mock_analysis('instagram', url)
    
    def analyze_twitter(self, url):
        """Analyze Twitter/X post replies"""
        # This would require Twitter API access
        return self.mock_analysis('twitter', url)
    
    def analyze_youtube(self, url):
        """Analyze YouTube video comments"""
        # This would require YouTube API access
        return self.mock_analysis('youtube', url)
    
    def analyze_tiktok(self, url):
        """Analyze TikTok video comments"""
        # This would require TikTok API access
        return self.mock_analysis('tiktok', url)
    
    def mock_analysis(self, platform, url):
        """Generate mock analysis data for demo"""
        import random
        
        # Generate mock comments
        mock_comments = [
            "Great content! Check out my profile for more",
            "SLOT GACOR HARI INI! MAXWIN GUARANTEED!",
            "Thanks for sharing this information",
            "Togel online terpercaya, bonus 100%",
            "This is really helpful, thank you!",
            "PROMO CASINO ONLINE, JACKPOT MILLIONS",
            "I learned something new today",
            "Daftar sekarang dapat bonus deposit 50%",
            "Amazing video, keep it up!",
            "Link slot terbaru ada di bio saya"
        ]
        
        total_comments = random.randint(50, 500)
        sample_size = min(10, total_comments)
        sampled_comments = random.sample(mock_comments, sample_size)
        
        # Analyze each comment
        analysis_results = []
        spam_count = 0
        judi_count = 0
        spam_accounts = {}
        
        for comment in sampled_comments:
            result = self.detector.detect_category(comment)
            analysis_results.append({
                'text': comment[:100],
                'category': result['category'],
                'confidence': result['confidence']
            })
            
            if result['category'] == 'spam':
                spam_count += 1
                username = f"user_{random.randint(1000, 9999)}"
                spam_accounts[username] = spam_accounts.get(username, 0) + 1
            elif result['category'] == 'judi_online':
                judi_count += 1
                username = f"judi_user_{random.randint(100, 999)}"
                spam_accounts[username] = spam_accounts.get(username, 0) + 1
        
        return {
            'platform': platform,
            'url': url,
            'total_comments': total_comments,
            'analyzed_comments': sample_size,
            'spam_comments': spam_count,
            'judi_comments': judi_count,
            'spam_percentage': round((spam_count + judi_count) / sample_size * 100, 1),
            'sample_results': analysis_results,
            'top_spam_accounts': dict(sorted(spam_accounts.items(), key=lambda x: x[1], reverse=True)[:5]),
            'analysis_date': datetime.now().isoformat()
        }
    
    def save_analysis(self, user_id, platform, url, results):
        """Save analysis results to database"""
        conn = sqlite3.connect('detection_system.db')
        c = conn.cursor()
        
        c.execute("""INSERT INTO social_media_analysis 
                     (user_id, platform, url, total_comments, spam_comments, judi_comments, analysis_date)
                     VALUES (?, ?, ?, ?, ?, ?, ?)""",
                  (user_id, platform, url, 
                   results.get('total_comments', 0),
                   results.get('spam_comments', 0),
                   results.get('judi_comments', 0),
                   datetime.now()))
        
        # Save spam accounts
        for username, count in results.get('top_spam_accounts', {}).items():
            c.execute("""INSERT OR REPLACE INTO spam_accounts 
                         (platform, username, spam_count, judi_count, first_seen, last_seen, risk_score)
                         VALUES (?, ?, ?, ?, ?, ?, ?)""",
                      (platform, username, 
                       count if 'spam' in username else 0,
                       count if 'judi' in username else 0,
                       datetime.now(), datetime.now(),
                       min(1.0, count * 0.2)))
        
        conn.commit()
        conn.close()

class SpamAccountResearcher:
    """Research and analyze spam accounts"""
    
    def __init__(self):
        pass
    
    def research_account(self, platform, username):
        """Research a specific spam account"""
        conn = sqlite3.connect('detection_system.db')
        c = conn.cursor()
        
        # Get account data
        c.execute("""SELECT * FROM spam_accounts WHERE platform = ? AND username = ?""",
                  (platform, username))
        account_data = c.fetchone()
        
        if not account_data:
            conn.close()
            return {'error': 'Account not found'}
        
        # Get related detections
        c.execute("""SELECT COUNT(*) as total, 
                            SUM(CASE WHEN category = 'spam' THEN 1 ELSE 0 END) as spam,
                            SUM(CASE WHEN category = 'judi_online' THEN 1 ELSE 0 END) as judi
                     FROM detections WHERE text LIKE ?""",
                  (f'%{username}%',))
        stats = c.fetchone()
        
        conn.close()
        
        return {
            'platform': account_data[1],
            'username': account_data[2],
            'spam_count': account_data[3],
            'judi_count': account_data[4],
            'first_seen': account_data[5],
            'last_seen': account_data[6],
            'patterns': json.loads(account_data[7]) if account_data[7] else [],
            'risk_score': account_data[8],
            'total_detections': stats[0] if stats else 0,
            'characteristics': self.analyze_patterns(username, platform)
        }
    
    def analyze_patterns(self, username, platform):
        """Analyze patterns in spam account behavior"""
        patterns = {
            'username_patterns': [],
            'posting_times': [],
            'common_keywords': [],
            'risk_indicators': []
        }
        
        # Check username patterns
        if re.search(r'\d{3,}', username):
            patterns['username_patterns'].append('Contains multiple digits')
            patterns['risk_indicators'].append('Auto-generated username')
        
        if 'slot' in username.lower() or 'judi' in username.lower() or 'togel' in username.lower():
            patterns['username_patterns'].append('Contains gambling keywords')
            patterns['risk_indicators'].append('Gambling-related account')
        
        # Platform-specific patterns
        if platform == 'instagram':
            patterns['common_keywords'] = ['link in bio', 'check profile', 'DM for info']
        elif platform == 'youtube':
            patterns['common_keywords'] = ['check my channel', 'subscribe', 'click link']
        
        return patterns
    
    def get_top_spam_accounts(self, limit=10):
        """Get top spam accounts across all platforms"""
        conn = sqlite3.connect('detection_system.db')
        c = conn.cursor()
        
        c.execute("""SELECT platform, username, spam_count + judi_count as total, risk_score
                     FROM spam_accounts
                     ORDER BY total DESC, risk_score DESC
                     LIMIT ?""", (limit,))
        
        accounts = []
        for row in c.fetchall():
            accounts.append({
                'platform': row[0],
                'username': row[1],
                'total_spam': row[2],
                'risk_score': row[3]
            })
        
        conn.close()
        return accounts

# Initialize components
detector = AdvancedDetector()
social_analyzer = SocialMediaAnalyzer(detector)
account_researcher = SpamAccountResearcher()

# Routes
@app.route('/')
def index():
    """Main page"""
    return render_template('index_advanced.html')

@app.route('/login')
def login():
    """Login page"""
    redirect_uri = url_for('auth_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/callback')
def auth_callback():
    """Google OAuth callback"""
    try:
        token = google.authorize_access_token()
        user_info = token.get('userinfo')
        
        if user_info:
            # Save or update user in database
            conn = sqlite3.connect('detection_system.db')
            c = conn.cursor()
            
            c.execute("SELECT id FROM users WHERE google_id = ?", (user_info['sub'],))
            existing_user = c.fetchone()
            
            if existing_user:
                user_id = existing_user[0]
                # Update user info
                c.execute("""UPDATE users SET email = ?, name = ?, picture = ? 
                            WHERE id = ?""",
                          (user_info['email'], user_info['name'], 
                           user_info.get('picture'), user_id))
            else:
                # Create new user
                c.execute("""INSERT INTO users (google_id, email, name, picture, created_at)
                            VALUES (?, ?, ?, ?, ?)""",
                          (user_info['sub'], user_info['email'], user_info['name'],
                           user_info.get('picture'), datetime.now()))
                user_id = c.lastrowid
            
            conn.commit()
            
            # Get user data
            c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            user_data = c.fetchone()
            conn.close()
            
            # Login user
            user = User(user_data[0], user_data[2], user_data[3], user_data[4], user_data[5])
            login_user(user)
            
            return redirect(url_for('index'))
    except Exception as e:
        print(f"Auth error: {e}")
        return redirect(url_for('index'))
    
    return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    """Logout"""
    logout_user()
    return redirect(url_for('index'))

@app.route('/api/detect', methods=['POST'])
def detect_message():
    """Enhanced detection with categorization"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text.strip():
            return jsonify({'error': 'Empty text'}), 400
        
        # Detect category
        result = detector.detect_category(text)
        
        # Save to database if user is logged in
        if current_user.is_authenticated:
            conn = sqlite3.connect('detection_system.db')
            c = conn.cursor()
            c.execute("""INSERT INTO detections (user_id, text, category, confidence, timestamp)
                        VALUES (?, ?, ?, ?, ?)""",
                      (current_user.id, text[:500], result['category'], 
                       result['confidence'], datetime.now()))
            conn.commit()
            conn.close()
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze-url', methods=['POST'])
def analyze_social_media():
    """Analyze social media URL for spam comments"""
    try:
        data = request.get_json()
        url = data.get('url', '')
        
        if not url:
            return jsonify({'error': 'No URL provided'}), 400
        
        user_id = current_user.id if current_user.is_authenticated else None
        results = social_analyzer.analyze_url(url, user_id)
        
        return jsonify(results)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete-spam', methods=['POST'])
@login_required
def delete_spam():
    """Automatically delete detected spam (for authenticated users)"""
    try:
        data = request.get_json()
        category = data.get('category', 'spam')
        
        conn = sqlite3.connect('detection_system.db')
        c = conn.cursor()
        
        # Mark as deleted (soft delete)
        c.execute("""UPDATE detections SET deleted = 1 
                    WHERE user_id = ? AND category IN (?, 'judi_online')""",
                  (current_user.id, category))
        
        deleted_count = c.rowcount
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'deleted_count': deleted_count,
            'message': f'Deleted {deleted_count} spam messages'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/research-account', methods=['POST'])
def research_account():
    """Research spam account"""
    try:
        data = request.get_json()
        platform = data.get('platform', '')
        username = data.get('username', '')
        
        if not platform or not username:
            return jsonify({'error': 'Platform and username required'}), 400
        
        results = account_researcher.research_account(platform, username)
        return jsonify(results)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/top-spammers', methods=['GET'])
def get_top_spammers():
    """Get top spam accounts"""
    try:
        limit = request.args.get('limit', 10, type=int)
        accounts = account_researcher.get_top_spam_accounts(limit)
        return jsonify({'accounts': accounts})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user-stats', methods=['GET'])
@login_required
def get_user_stats():
    """Get user statistics"""
    try:
        conn = sqlite3.connect('detection_system.db')
        c = conn.cursor()
        
        # Get user's detection stats
        c.execute("""SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN category = 'spam' THEN 1 ELSE 0 END) as spam,
                        SUM(CASE WHEN category = 'judi_online' THEN 1 ELSE 0 END) as judi,
                        SUM(CASE WHEN deleted = 1 THEN 1 ELSE 0 END) as deleted
                     FROM detections WHERE user_id = ?""",
                  (current_user.id,))
        stats = c.fetchone()
        
        # Get recent analyses
        c.execute("""SELECT platform, url, spam_comments, judi_comments, analysis_date
                     FROM social_media_analysis 
                     WHERE user_id = ?
                     ORDER BY analysis_date DESC
                     LIMIT 5""",
                  (current_user.id,))
        recent_analyses = []
        for row in c.fetchall():
            recent_analyses.append({
                'platform': row[0],
                'url': row[1],
                'spam_comments': row[2],
                'judi_comments': row[3],
                'date': row[4]
            })
        
        conn.close()
        
        return jsonify({
            'total_detections': stats[0] if stats else 0,
            'spam_count': stats[1] if stats else 0,
            'judi_count': stats[2] if stats else 0,
            'deleted_count': stats[3] if stats else 0,
            'recent_analyses': recent_analyses
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)
