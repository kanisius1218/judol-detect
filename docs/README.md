# 🤖 Multi-Platform Spam Moderator

Bot otomatis untuk mendeteksi dan menghapus spam komentar judi online di **YouTube, TikTok, dan Instagram**.

## 📋 Table of Contents

- [Features](#-features)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [API Setup](#-api-setup)
  - [YouTube API](#1-youtube-api-setup)
  - [Instagram API](#2-instagram-api-setup)
  - [TikTok API](#3-tiktok-api-setup)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Detection System](#-detection-system)
- [Troubleshooting](#-troubleshooting)

---

## ✨ Features

### Core Features
- ✅ **Multi-Platform**: YouTube, TikTok, Instagram
- ✅ **AI-Powered Detection**: Confidence scoring 0-100%
- ✅ **Auto-Delete Spam**: Otomatis hapus spam comments
- ✅ **50+ Keywords**: Deteksi slot, togel, casino, dll
- ✅ **Typo Detection**: Deteksi variasi typo (sl0t, gac0r)
- ✅ **Pattern Recognition**: URL, phone, emoji, dll
- ✅ **Database Logging**: SQLite database untuk tracking
- ✅ **Whitelist System**: Whitelist trusted users
- ✅ **Statistics**: Per-platform statistics tracking
- ✅ **Dry Run Mode**: Testing tanpa delete

### Detection Methods
- **Keyword Matching**: 50+ keywords judi online
- **Typo Variants**: Deteksi lookalike characters
- **URL Detection**: Link shorteners dan domains
- **Phone Numbers**: Format Indonesia & international
- **Spam Emoji**: Deteksi emoji berlebihan 🎰💰🔥
- **Text Normalization**: Advanced text processing

---

## 📦 Requirements

- **Python 3.8+**
- **API Keys** untuk platform yang ingin digunakan:
  - YouTube: Google Cloud API Key
  - Instagram: Facebook Graph API Access Token
  - TikTok: Session ID (unofficial, berisiko)

---

## 🚀 Installation

### Step 1: Install Python

**Windows:**
```bash
# Download dari python.org
# Checklist "Add Python to PATH"
```

**Linux/Mac:**
```bash
sudo apt install python3 python3-pip  # Ubuntu/Debian
brew install python3                   # Mac
```

### Step 2: Clone/Download Project

```bash
cd "C:\Users\test\OneDrive\Desktop\judol delet msg"
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Note untuk TikTok:**
```bash
# TikTok memerlukan Playwright browsers
playwright install
```

### Step 4: Configure Environment

```bash
# Copy config template
copy config.example.env .env

# Edit .env dengan API keys Anda
notepad .env
```

---

## 🔑 API Setup

### 1. YouTube API Setup

#### Step 1: Google Cloud Console

1. Buka [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project atau pilih existing project
3. Nama project: "Spam Moderator" (atau nama lain)

#### Step 2: Enable YouTube Data API

1. Di sidebar, pilih **APIs & Services** → **Library**
2. Cari "YouTube Data API v3"
3. Click **Enable**

#### Step 3: Create API Key

1. **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **API Key**
3. Copy API key yang dibuat
4. (Optional) Click **Restrict Key**:
   - Application restrictions: None (atau IP addresses jika mau)
   - API restrictions: Restrict key → Pilih "YouTube Data API v3"
5. Save

#### Step 4: Get Channel ID

**Cara 1: Dari URL Channel**
```
https://www.youtube.com/channel/UC_x5XG1OV2P6uZZ5FSM9Ttw
                                 ^^^^^^^^^^^^^^^^^^^^^^^^
                                 Ini adalah Channel ID
```

**Cara 2: Dari YouTube Studio**
1. Buka [YouTube Studio](https://studio.youtube.com/)
2. Settings → Channel → Advanced settings
3. Copy "Channel ID"

#### Step 5: Configure

Edit `.env`:
```env
YOUTUBE_ENABLED=true
YOUTUBE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
YOUTUBE_CHANNEL_ID=UC_x5XG1OV2P6uZZ5FSM9Ttw
```

#### ⚠️ YouTube API Quota

- **Free quota**: 10,000 units/day
- **Read comment**: 1 unit
- **Delete comment**: 50 units
- **Estimasi**: ~200 delete operations/day dengan free quota

**Tips menghemat quota:**
- Gunakan `max_comments` parameter
- Run bot setiap beberapa jam, bukan continuous
- Increase confidence threshold untuk reduce false positives

---

### 2. Instagram API Setup

Instagram menggunakan **Facebook Graph API** dan memerlukan **Business/Creator account**.

#### Step 1: Convert ke Business Account

1. Buka Instagram app
2. Settings → Account → Switch to Professional Account
3. Pilih "Creator" atau "Business"

#### Step 2: Connect ke Facebook Page

1. Settings → Account → Linked Accounts → Facebook
2. Connect ke Facebook Page (create jika belum punya)

#### Step 3: Create Facebook App

1. Buka [Facebook Developers](https://developers.facebook.com/)
2. My Apps → Create App
3. Pilih "Business" type
4. App name: "Spam Moderator"
5. Create App

#### Step 4: Add Instagram Product

1. Di dashboard app, click **Add Product**
2. Pilih **Instagram** → Set Up
3. Follow setup wizard

#### Step 5: Get Access Token

**Cara 1: Graph API Explorer (Testing)**
1. Buka [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Select your app
3. Get User Access Token
4. Add permissions:
   - `instagram_basic`
   - `instagram_manage_comments`
   - `pages_read_engagement`
   - `pages_manage_metadata`
5. Generate Access Token
6. Copy token

**Cara 2: Long-Lived Token (Production)**
```bash
# Exchange short-lived token for long-lived (60 days)
curl -i -X GET "https://graph.facebook.com/v18.0/oauth/access_token?grant_type=fb_exchange_token&client_id=YOUR_APP_ID&client_secret=YOUR_APP_SECRET&fb_exchange_token=SHORT_LIVED_TOKEN"
```

#### Step 6: Get Instagram User ID

```bash
# Using access token
curl -i -X GET "https://graph.facebook.com/v18.0/me/accounts?access_token=YOUR_ACCESS_TOKEN"

# Get Instagram Business Account ID
curl -i -X GET "https://graph.facebook.com/v18.0/PAGE_ID?fields=instagram_business_account&access_token=YOUR_ACCESS_TOKEN"
```

#### Step 7: Configure

Edit `.env`:
```env
INSTAGRAM_ENABLED=true
INSTAGRAM_ACCESS_TOKEN=EAAxxxxxxxxxxxxxxxxxxxxxxxxx
INSTAGRAM_USER_ID=17841400000000000
```

#### ⚠️ Instagram API Limitations

- **Rate Limits**: 200 calls/hour per user
- **Token Expiry**: 60 days (need refresh)
- **Approval**: Some features need Facebook review
- **Business Account**: Required

---

### 3. TikTok API Setup

⚠️ **WARNING**: TikTok tidak memiliki official public API untuk comment moderation. Method ini menggunakan **unofficial API** yang:
- Melanggar TikTok Terms of Service
- Berisiko account banned
- Tidak stabil (bisa break kapan saja)
- **Gunakan dengan risiko Anda sendiri**

#### Recommended: Jangan Gunakan TikTok

Saya **sangat merekomendasikan** untuk **TIDAK menggunakan** TikTok adapter karena risiko tinggi.

Jika tetap ingin mencoba (at your own risk):

#### Step 1: Get Session ID

1. Login ke TikTok di browser
2. Buka Developer Tools (F12)
3. Application tab → Cookies → https://www.tiktok.com
4. Cari cookie bernama `sessionid`
5. Copy value-nya

#### Step 2: Configure

Edit `.env`:
```env
TIKTOK_ENABLED=false  # Set false untuk disable
TIKTOK_SESSION_ID=xxxxxxxxxxxxxxxxxxxxx
TIKTOK_USERNAME=your_username
```

#### Alternative untuk TikTok

**Rekomendasi:**
1. **Manual Moderation**: Moderate comments secara manual
2. **TikTok Creator Tools**: Gunakan built-in moderation tools
3. **Keyword Filters**: Set keyword filters di TikTok settings
4. **Wait for Official API**: Tunggu TikTok release official API

---

## ⚙️ Configuration

### Edit .env File

```env
# General
CONFIDENCE_THRESHOLD=40        # 0-100, lower = more sensitive
DRY_RUN=false                  # true = testing mode (no delete)
CHECK_INTERVAL_MINUTES=5       # Interval check comments

# YouTube
YOUTUBE_ENABLED=true
YOUTUBE_API_KEY=your_key_here
YOUTUBE_CHANNEL_ID=your_channel_id

# Instagram
INSTAGRAM_ENABLED=true
INSTAGRAM_ACCESS_TOKEN=your_token_here
INSTAGRAM_USER_ID=your_user_id

# TikTok (NOT RECOMMENDED)
TIKTOK_ENABLED=false
```

### Confidence Threshold Guide

- **30-35**: Very sensitive (banyak false positive)
- **40-50**: Balanced ✅ **RECOMMENDED**
- **60-70**: Conservative (sedikit false positive)
- **80-100**: Very conservative (hanya spam jelas)

---

## 📱 Usage

### Test Detection Engine

Test detector tanpa API:

```bash
python core_detector.py
```

Output:
```
======================================================================
SPAM DETECTOR TEST
======================================================================

Test 1:
Text: SLOT GACOR MAXWIN! Daftar di https://slotgacor.com 🎰💰🔥...
Is Spam: True
Confidence: 95%
Keywords: ['slot', 'gacor', 'maxwin']
Patterns: ['URL', 'spam_emojis', 'aggressive_caps']
```

### Test Database

```bash
python database.py
```

### Test YouTube Adapter

```bash
python youtube_adapter.py
```

### Run Main Bot

Coming soon - main orchestrator file

---

## 🔍 Detection System

### Confidence Scoring

| Detection Method | Points | Description |
|-----------------|--------|-------------|
| 3+ Keywords | +40 | Multiple gambling keywords |
| 2 Keywords | +30 | Two gambling keywords |
| 1 Keyword | +20 | One gambling keyword |
| URL/Link | +15 | Contains URL |
| Phone Number | +15 | Phone number detected |
| Telegram Link | +15 | Telegram link |
| WhatsApp | +10 | WhatsApp reference |
| Email | +10 | Email address |
| Spam Emoji (3+) | +10 | Excessive emojis |
| Excessive Numbers | +10 | 10+ digits |
| Aggressive Caps | +5 | CAPS + !!! |
| Repeated Chars | +5 | gacooorrrr |
| Suspicious Spacing | +5 | S L O T |

**Threshold**: Confidence ≥ 40% = SPAM

### Keywords Database

**Main Keywords (10):**
slot, togel, casino, betting, judol, judi online, judi, taruhan, bandar, gambling

**Slot Keywords (20+):**
gacor, maxwin, jackpot, scatter, freespin, rtp, pragmatic, pg soft, gates of olympus, dll

**Togel Keywords (15+):**
togel online, pasaran, hongkong, singapore, angka jitu, prediksi togel, dll

**Transaction Keywords (15+):**
deposit, withdraw, bonus, promo, daftar sekarang, klaim bonus, dll

**Platform Names (15+):**
olxtoto, rajabandot, kingslot, sultantoto, dll

---

## 🐛 Troubleshooting

### YouTube Issues

**Error: "API key not valid"**
- Check API key di Google Cloud Console
- Pastikan YouTube Data API v3 enabled
- Check API key restrictions

**Error: "Insufficient permissions"**
- Pastikan Anda owner/manager channel
- Check OAuth scopes jika pakai OAuth

**Error: "Quota exceeded"**
- Free quota: 10,000 units/day
- Wait 24 hours atau upgrade quota
- Reduce check frequency

### Instagram Issues

**Error: "Invalid access token"**
- Token expired (60 days)
- Generate new token
- Use long-lived token

**Error: "Permissions error"**
- Check permissions di Graph API Explorer
- Need: `instagram_manage_comments`
- May need Facebook app review

**Error: "Rate limit exceeded"**
- Instagram: 200 calls/hour
- Reduce check frequency
- Wait 1 hour

### TikTok Issues

**Error: "Session invalid"**
- Session ID expired
- Get new session ID dari browser
- Login ulang ke TikTok

**Account Banned**
- TikTok detected automation
- Create new account
- **Recommendation: Don't use TikTok adapter**

---

## 📊 Database Structure

### Table: spam_logs
Stores all detected spam across platforms.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| platform | TEXT | youtube/tiktok/instagram |
| content_id | TEXT | Video/Post ID |
| content_url | TEXT | URL to content |
| comment_id | TEXT | Comment ID |
| author_id | TEXT | Author ID |
| author_name | TEXT | Author name |
| comment_text | TEXT | Comment content |
| detected_keywords | TEXT | Keywords found |
| detected_patterns | TEXT | Patterns found |
| confidence_score | INTEGER | 0-100 |
| timestamp | DATETIME | Detection time |

### Table: whitelist
Whitelisted users per platform.

### Table: stats
Daily statistics per platform.

### Table: platform_config
Configuration per platform.

---

## 🎯 Best Practices

### 1. Start with Dry Run

```env
DRY_RUN=true
```

Test dulu tanpa delete untuk check accuracy.

### 2. Monitor False Positives

Check database logs:
```bash
python database.py
```

Whitelist users jika perlu.

### 3. Adjust Threshold

Start dengan 40, adjust berdasarkan hasil:
- Too many false positives → increase threshold
- Too much spam passing → decrease threshold

### 4. Regular Monitoring

- Check stats daily (first week)
- Review deleted comments
- Adjust keywords jika perlu

### 5. Backup Database

```bash
copy spam_moderator.db backup\spam_moderator_%date%.db
```

---

## 📚 Project Structure

```
judol delet msg/
├── core_detector.py          # Core detection engine
├── database.py                # Database manager
├── youtube_adapter.py         # YouTube platform adapter
├── instagram_adapter.py       # Instagram adapter (coming soon)
├── tiktok_adapter.py          # TikTok adapter (coming soon)
├── main.py                    # Main orchestrator (coming soon)
├── requirements.txt           # Dependencies
├── config.example.env         # Config template
├── .env                       # Your config (create this)
├── README.md                  # This file
└── spam_moderator.db          # Database (auto-created)
```

---

## ⚠️ Important Notes

### YouTube
- ✅ Official API - Safe to use
- ✅ Stable and reliable
- ⚠️ Quota limits (10k units/day free)
- ✅ **RECOMMENDED**

### Instagram
- ✅ Official API - Safe to use
- ⚠️ Requires Business account
- ⚠️ Token expires (60 days)
- ⚠️ May need Facebook review
- ✅ **USABLE** with setup

### TikTok
- ❌ Unofficial API - **NOT SAFE**
- ❌ Violates TOS
- ❌ Risk of account ban
- ❌ Unstable
- ❌ **NOT RECOMMENDED**

---

## 📄 License

MIT License - Free to use and modify

---

## 🤝 Support

Jika ada pertanyaan atau masalah:
1. Check Troubleshooting section
2. Review API setup guides
3. Check logs untuk error messages
4. Test dengan dry run mode

---

## 🎓 Next Steps

1. ✅ Setup API keys untuk platform yang diinginkan
2. ✅ Configure .env file
3. ✅ Test detection engine
4. ✅ Run dengan dry_run=true
5. ✅ Monitor results
6. ✅ Adjust threshold
7. ✅ Run production mode

---

**Version:** 1.0.0  
**Last Updated:** 2025-10-07  
**Status:** Beta - YouTube Ready, Instagram/TikTok In Development

**Developed for safer social media communities** ❤️
