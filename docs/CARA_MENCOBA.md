# 🧪 Cara Mencoba Bot - Panduan Lengkap

Panduan step-by-step untuk mencoba bot spam moderator ini.

## 🎯 3 Cara Mencoba

### 1️⃣ Test Tanpa API (Paling Mudah) ⭐ RECOMMENDED

Test detection engine dan database tanpa perlu API keys.

**Waktu:** 2 menit

```bash
# Cara 1: Jalankan batch file (Windows)
TEST_BOT.bat

# Cara 2: Jalankan manual
python test_all.py
```

**Output yang diharapkan:**
```
✅ Core Detection Engine: WORKING
✅ Database System: WORKING
✅ YouTube Adapter: STRUCTURE OK
✅ Configuration Files: PRESENT
```

**Apa yang di-test:**
- ✅ Detection engine dengan 5 test cases
- ✅ Database operations (log, whitelist, stats)
- ✅ File structure
- ✅ Module imports

---

### 2️⃣ Test Detection Engine Saja

Test hanya detection engine dengan berbagai contoh spam.

**Waktu:** 1 menit

```bash
python core_detector.py
```

**Output:**
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
----------------------------------------------------------------------
```

**Apa yang di-test:**
- ✅ Keyword detection
- ✅ Pattern recognition
- ✅ Confidence scoring
- ✅ Typo detection

---

### 3️⃣ Test Dengan YouTube API (Production Test)

Test dengan real YouTube data - **PERLU API KEY**.

**Waktu:** 15 menit (termasuk setup API)

#### Step 1: Get YouTube API Key (10 menit)

1. **Buka Google Cloud Console**
   - URL: https://console.cloud.google.com/
   - Login dengan Google account

2. **Create Project**
   - Click "Select a project" → "New Project"
   - Project name: "Spam Moderator"
   - Click "Create"

3. **Enable YouTube Data API v3**
   - Sidebar: APIs & Services → Library
   - Search: "YouTube Data API v3"
   - Click → Enable

4. **Create API Key**
   - APIs & Services → Credentials
   - Create Credentials → API Key
   - Copy API key (format: AIzaSy...)

5. **Get Channel ID**
   - Dari URL channel: `youtube.com/channel/UC_xxxxx`
   - Atau dari YouTube Studio → Settings → Channel → Advanced

#### Step 2: Configure (2 menit)

```bash
# Copy config template
copy config.example.env .env

# Edit .env
notepad .env
```

Isi dengan:
```env
YOUTUBE_ENABLED=true
YOUTUBE_API_KEY=AIzaSy_YOUR_API_KEY_HERE
YOUTUBE_CHANNEL_ID=UC_YOUR_CHANNEL_ID_HERE
CONFIDENCE_THRESHOLD=40
DRY_RUN=true
```

**PENTING:** Set `DRY_RUN=true` untuk testing!

#### Step 3: Test YouTube Adapter (3 menit)

Buat file `test_youtube.py`:

```python
from core_detector import SpamDetector
from database import DatabaseManager
from youtube_adapter import YouTubeAdapter
import os
from dotenv import load_dotenv

# Load config
load_dotenv()

# Initialize
detector = SpamDetector(confidence_threshold=40)
database = DatabaseManager()
youtube = YouTubeAdapter(
    api_key=os.getenv('YOUTUBE_API_KEY'),
    detector=detector,
    database=database,
    channel_id=os.getenv('YOUTUBE_CHANNEL_ID')
)

# Test: Get recent comments from channel
print("Getting recent comments...")
comments = youtube.get_channel_comments(max_results=10)

print(f"\nFound {len(comments)} comments")

# Test: Check for spam (dry run - won't delete)
print("\nChecking for spam...")
for comment in comments:
    result = youtube.check_and_delete_spam(comment, dry_run=True)
    if result:
        print(f"\n🚨 SPAM DETECTED:")
        print(f"   Author: {comment['author_name']}")
        print(f"   Text: {comment['text'][:100]}...")
        print(f"   Confidence: {result.confidence}%")

# Show stats
print(f"\nStats: {youtube.get_stats()}")
```

Jalankan:
```bash
python test_youtube.py
```

**Output yang diharapkan:**
```
Getting recent comments...
Found 10 comments

Checking for spam...

🚨 SPAM DETECTED:
   Author: SpammerUser
   Text: SLOT GACOR MAXWIN! Daftar sekarang...
   Confidence: 85%

Stats: {'comments_checked': 10, 'spam_detected': 1, 'spam_deleted': 0, 'errors': 0}
```

---

## 📊 Memahami Output

### Detection Result

```python
DetectionResult(
    is_spam=True,              # Apakah spam?
    confidence=75,             # Confidence score (0-100)
    detected_keywords=[...],   # Keywords yang terdeteksi
    detected_patterns=[...],   # Patterns yang terdeteksi
    reason='...',              # Alasan deteksi
    score=75                   # Raw score
)
```

### Confidence Levels

- **0-30%**: Bukan spam (safe)
- **30-40%**: Borderline (perlu review)
- **40-60%**: Likely spam (moderate confidence)
- **60-80%**: Very likely spam (high confidence)
- **80-100%**: Definitely spam (very high confidence)

---

## 🎨 Customize Detection

### Test dengan Custom Keywords

Edit `core_detector.py`:

```python
# Tambah keywords baru
PLATFORM_NAMES = [
    'olxtoto', 'rajabandot', 'kingslot',
    'platform_baru_anda'  # Tambah di sini
]
```

Test lagi:
```bash
python core_detector.py
```

### Test dengan Custom Threshold

```python
# Lebih sensitif
detector = SpamDetector(confidence_threshold=30)

# Lebih konservatif
detector = SpamDetector(confidence_threshold=50)
```

---

## 🔍 Debugging

### Lihat Logs Detail

Edit file test, tambahkan logging:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,  # Change to DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Check Database

```bash
python database.py
```

Atau gunakan SQLite browser:
- Download: https://sqlitebrowser.org/
- Open: `spam_moderator.db`
- Browse tables: spam_logs, whitelist, stats

### Manual Test Detection

```python
from core_detector import SpamDetector

detector = SpamDetector(confidence_threshold=40)

# Test dengan text Anda sendiri
text = "MASUKKAN TEXT YANG MAU DI-TEST DI SINI"
result = detector.detect(text)

print(f"Is Spam: {result.is_spam}")
print(f"Confidence: {result.confidence}%")
print(f"Keywords: {result.detected_keywords}")
print(f"Patterns: {result.detected_patterns}")
print(f"Reason: {result.reason}")
```

---

## ⚠️ Troubleshooting

### Error: "Module not found"

```bash
pip install -r requirements.txt
```

### Error: "API key invalid"

- Check API key di Google Cloud Console
- Pastikan YouTube Data API v3 enabled
- Copy-paste API key dengan benar (no spaces)

### Error: "Permission denied"

- Pastikan Anda owner/manager channel
- Check API key restrictions di Google Cloud Console

### Tidak ada spam terdeteksi

**Kemungkinan:**
1. Threshold terlalu tinggi → Lower threshold
2. Keywords tidak match → Add custom keywords
3. Memang tidak ada spam → Good!

**Test dengan spam sample:**
```python
spam_samples = [
    "SLOT GACOR MAXWIN! 🎰💰",
    "Togel online terpercaya! WA: 08123456789",
    "Daftar sekarang di https://slotgacor.com"
]

for text in spam_samples:
    result = detector.detect(text)
    print(f"{text}: {result.is_spam} ({result.confidence}%)")
```

---

## 📈 Next Steps

### Setelah Test Berhasil

1. **Review Results**
   - Check false positives
   - Check false negatives
   - Adjust threshold

2. **Customize**
   - Add custom keywords
   - Adjust scoring weights
   - Configure platforms

3. **Production Run**
   - Set `DRY_RUN=false`
   - Monitor closely
   - Backup database

4. **Automate**
   - Setup scheduled runs
   - Monitor statistics
   - Regular maintenance

---

## 📚 Resources

### Documentation
- **README.md**: Full documentation
- **QUICKSTART.md**: Quick setup guide
- **PROJECT_SUMMARY.md**: Project overview

### Code Files
- **core_detector.py**: Detection engine
- **database.py**: Database manager
- **youtube_adapter.py**: YouTube integration
- **test_all.py**: Comprehensive tests

### Configuration
- **config.example.env**: Config template
- **.env**: Your config (create this)
- **requirements.txt**: Dependencies

---

## 🎯 Test Checklist

### Basic Tests ✅
- [ ] Run `test_all.py` successfully
- [ ] All components working
- [ ] No errors

### Detection Tests ✅
- [ ] Run `core_detector.py`
- [ ] Spam detected correctly
- [ ] Non-spam passed correctly
- [ ] Confidence scores reasonable

### Database Tests ✅
- [ ] Database created
- [ ] Spam logged
- [ ] Whitelist working
- [ ] Stats retrieved

### YouTube Tests (Optional) ✅
- [ ] API key obtained
- [ ] Config file created
- [ ] Comments retrieved
- [ ] Spam detection working
- [ ] Dry run successful

### Production Ready ✅
- [ ] False positives checked
- [ ] Threshold adjusted
- [ ] Keywords customized
- [ ] Ready to deploy

---

## 💡 Tips

### 1. Start Small
Test dengan 1-2 video dulu sebelum full channel

### 2. Use Dry Run
Selalu test dengan `DRY_RUN=true` dulu

### 3. Monitor Closely
Check hasil detection untuk beberapa hari pertama

### 4. Backup Database
```bash
copy spam_moderator.db backup\
```

### 5. Regular Updates
Update keywords sesuai spam trends

---

## 🎉 Selamat Mencoba!

Jika ada pertanyaan atau masalah:
1. Check Troubleshooting section
2. Review documentation
3. Check logs
4. Test dengan dry run

**Good luck!** 🚀

---

**Version:** 1.0.0  
**Last Updated:** 2025-10-07
